"""
Live Workflow Run Manager and Event Dispatcher for SAP Utilities Agentic Platform.
Manages in-memory run snapshots, graph layout, event emission, SSE fan-out, and cancellation.
Strictly isolated from legacy RAG.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, AsyncGenerator, Any

from sap_rag.agentic.schemas.workflow_events import (
    WorkflowNode,
    WorkflowEdge,
    WorkflowEvent,
    WorkflowEventType,
    NodeStatus,
    NodeType,
    RunSnapshot
)
from sap_rag.agentic.schemas.contracts import (
    FinalAgenticResponse,
    ResponseMode,
    AnswerStatus,
    StageExecutionStatus,
    ExecutionMechanism
)

logger = logging.getLogger("sap_rag.agentic.orchestration.run_manager")


class WorkflowRunManager:
    """
    Singleton / shared run manager for workflow execution observability.
    Thread-safe and async-safe across coroutines.
    """
    _instance: Optional["WorkflowRunManager"] = None

    def __init__(self):
        self._runs: Dict[str, RunSnapshot] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._sequences: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "WorkflowRunManager":
        if cls._instance is None:
            cls._instance = WorkflowRunManager()
        return cls._instance

    def _next_sequence(self, run_id: str) -> int:
        seq = self._sequences.get(run_id, 0) + 1
        self._sequences[run_id] = seq
        return seq

    def build_initial_graph(self, run_id: str, query: str) -> tuple[List[WorkflowNode], List[WorkflowEdge]]:
        """
        Build canonical directed graph layout for the SAP Utilities query.
        Nodes are laid out horizontally from left to right with specialist lanes vertically stacked.
        """
        nodes = [
            WorkflowNode(
                node_id="node_request",
                node_type=NodeType.REQUEST,
                label="Request Accepted",
                description="Input sanitized, budget & quota constraints initialized",
                status=NodeStatus.SUCCEEDED,
                position={"x": 60.0, "y": 80.0},
                phase=1,
                phase_title="PHASE 1 — REQUEST & PLANNING",
                mechanism="deterministic_guardrail",
                predecessor_node_id=None,
                successor_node_id="node_planner",
                selection_reason="Entry point for all user queries. Enforces untrusted input sanitization and execution budget guardrails.",
                tools_called=["SecurityGuardrails.sanitize_untrusted_text", "ExecutionBudgetController"],
                handoff_summary="Passes sanitized query text and execution budget deadline (90s) to Query Planner.",
                input_summary=f"Query: {query[:120]}",
                output_summary="Request ID generated, safety checks passed"
            ),
            WorkflowNode(
                node_id="node_planner",
                node_type=NodeType.PLANNER,
                label="Query Planner",
                description="Deconstructs query into intent, SAP entities, and subquestions",
                status=NodeStatus.QUEUED,
                position={"x": 60.0, "y": 220.0},
                phase=1,
                phase_title="PHASE 1 — REQUEST & PLANNING",
                agent_role="query_planner",
                mechanism="llm_reasoning",
                predecessor_node_id="node_request",
                successor_node_id="node_encoder",
                selection_reason="Deconstructs complex query into SAP domain intent and required specialist agent lane assignments.",
                tools_called=["CrewAI Query Planner Agent"],
                handoff_summary="Passes structured QueryPlan with subquestions and specialist routing plan to Query Encoder.",
                input_summary="Original user query and SAP domain context"
            ),
            WorkflowNode(
                node_id="node_encoder",
                node_type=NodeType.ENCODER,
                label="Query Encoder",
                description="Encodes subqueries via BAAI/bge-small-en-v1.5 (384-dim, normalized)",
                status=NodeStatus.PENDING,
                position={"x": 60.0, "y": 360.0},
                phase=1,
                phase_title="PHASE 1 — REQUEST & PLANNING",
                mechanism="deterministic_embedding",
                predecessor_node_id="node_planner",
                successor_node_id="node_retrieval",
                selection_reason="Deterministic vector transformation: encodes subqueries into 384-dimensional dense vectors.",
                tools_called=["BAAI/bge-small-en-v1.5 Dense Embedding Model"],
                handoff_summary="Passes normalized dense vector embeddings to Semantic Discovery for vector search.",
                input_summary="Subquery strings"
            ),
            WorkflowNode(
                node_id="node_retrieval",
                node_type=NodeType.RETRIEVAL,
                label="Semantic Discovery",
                description="Executes pgvector <=> cosine distance search against stored embeddings",
                status=NodeStatus.PENDING,
                position={"x": 420.0, "y": 150.0},
                phase=2,
                phase_title="PHASE 2 — KNOWLEDGE DISCOVERY",
                mechanism="deterministic_pgvector",
                predecessor_node_id="node_encoder",
                successor_node_id="node_context",
                selection_reason="Direct database vector search against pre-computed pgvector documentation chunk embeddings.",
                tools_called=["SemanticRetrievalService.search (pgvector cosine distance)"],
                handoff_summary="Passes candidate chunks with similarity scores and document IDs to Context Builder.",
                input_summary="Dense vectors & keyword parameters"
            ),
            WorkflowNode(
                node_id="node_context",
                node_type=NodeType.CONTEXT_BUILDER,
                label="Context Builder",
                description="Stable-ID deduplication, clean excerpts & graph expansion",
                status=NodeStatus.PENDING,
                position={"x": 420.0, "y": 290.0},
                phase=2,
                phase_title="PHASE 2 — KNOWLEDGE DISCOVERY",
                mechanism="deterministic_assembly",
                predecessor_node_id="node_retrieval",
                successor_node_id="Specialist Lanes",
                selection_reason="Deterministic assembly: deduplicates chunks, cleans body text, and expands section hierarchy.",
                tools_called=["EvidenceContextBuilder", "GraphTraversalService.expand_evidence_graph"],
                handoff_summary="Dispatches deduplicated, clean evidence packages to parallel specialist agent lanes.",
                input_summary="Raw vector candidates"
            ),
            # Phase 3: Specialist Lanes (vertically parallel at x=780)
            WorkflowNode(
                node_id="node_proc_analyst",
                node_type=NodeType.SPECIALIST,
                label="Procedure Analyst",
                description="Extracts transaction codes (EC53E, CRM_UI), preconditions, and steps",
                status=NodeStatus.PENDING,
                position={"x": 780.0, "y": 40.0},
                phase=3,
                phase_title="PHASE 3 — SPECIALIST AGENTS",
                agent_role="procedure_analyst",
                mechanism="llm_reasoning",
                predecessor_node_id="node_context",
                successor_node_id="node_ledger",
                selection_reason="Activated when query requires step-by-step procedural actions, transaction codes, and preconditions.",
                tools_called=["CrewAI Procedure Analyst Agent"],
                handoff_summary="Submits atomic procedural claims, transaction codes, and prerequisite warnings to Evidence Ledger."
            ),
            WorkflowNode(
                node_id="node_conf_analyst",
                node_type=NodeType.SPECIALIST,
                label="Configuration Analyst",
                description="Extracts SPRO customizing paths, tables, and system parameters",
                status=NodeStatus.PENDING,
                position={"x": 780.0, "y": 175.0},
                phase=3,
                phase_title="PHASE 3 — SPECIALIST AGENTS",
                agent_role="configuration_analyst",
                mechanism="llm_reasoning",
                predecessor_node_id="node_context",
                successor_node_id="node_ledger",
                selection_reason="Activated when query requires SPRO customizing paths, database tables, or system configuration.",
                tools_called=["CrewAI Configuration Analyst Agent"],
                handoff_summary="Submits customizing paths and table parameters to Evidence Ledger."
            ),
            WorkflowNode(
                node_id="node_rel_analyst",
                node_type=NodeType.SPECIALIST,
                label="Relationship Analyst",
                description="Traces dependencies across BP, Contract Account, and Installations",
                status=NodeStatus.PENDING,
                position={"x": 780.0, "y": 310.0},
                phase=3,
                phase_title="PHASE 3 — SPECIALIST AGENTS",
                agent_role="relationship_analyst",
                mechanism="llm_reasoning",
                predecessor_node_id="node_context",
                successor_node_id="node_ledger",
                selection_reason="Activated when query involves entity relationships across Business Partner, Contract Account, and Technical Objects.",
                tools_called=["CrewAI Relationship Analyst Agent"],
                handoff_summary="Submits entity relationships and dependency mappings to Evidence Ledger."
            ),
            WorkflowNode(
                node_id="node_ts_analyst",
                node_type=NodeType.SPECIALIST,
                label="Troubleshooting Analyst",
                description="Extracts diagnostic steps, error codes, and exception procedures",
                status=NodeStatus.PENDING,
                position={"x": 780.0, "y": 445.0},
                phase=3,
                phase_title="PHASE 3 — SPECIALIST AGENTS",
                agent_role="troubleshooting_analyst",
                mechanism="llm_reasoning",
                predecessor_node_id="node_context",
                successor_node_id="node_ledger",
                selection_reason="Activated when query involves error codes, exception handling, or diagnostic recovery.",
                tools_called=["CrewAI Troubleshooting Analyst Agent"],
                handoff_summary="Submits diagnostic steps and error resolution procedures to Evidence Ledger."
            ),
            # Phase 4: Evidence Reconciliation (x=1140)
            WorkflowNode(
                node_id="node_ledger",
                node_type=NodeType.AGGREGATOR,
                label="Evidence Ledger",
                description="Deterministic aggregation, claim-to-evidence links, and conflict tracking",
                status=NodeStatus.PENDING,
                position={"x": 1140.0, "y": 80.0},
                phase=4,
                phase_title="PHASE 4 — EVIDENCE RECONCILIATION",
                mechanism="deterministic_ledger",
                predecessor_node_id="Specialist Lanes",
                successor_node_id="node_auditor",
                selection_reason="Deterministic aggregation: links atomic claims to evidence IDs and tracks contradictions across agents.",
                tools_called=["EvidenceLedger.aggregate_findings"],
                handoff_summary="Passes normalized claim-evidence matrix to Evidence Auditor.",
                input_summary="Specialist findings & evidence items"
            ),
            WorkflowNode(
                node_id="node_auditor",
                node_type=NodeType.AUDITOR,
                label="Evidence Auditor",
                description="Assesses evidence sufficiency (SUFFICIENT / PARTIAL / INSUFFICIENT) and gaps",
                status=NodeStatus.PENDING,
                position={"x": 1140.0, "y": 220.0},
                phase=4,
                phase_title="PHASE 4 — EVIDENCE RECONCILIATION",
                mechanism="deterministic_audit",
                predecessor_node_id="node_ledger",
                successor_node_id="node_gap_decision",
                selection_reason="Deterministic audit of claim grounding against retrieved text and evaluation of subquestion coverage.",
                tools_called=["EvidenceAuditor", "ContradictionChecker"],
                handoff_summary="Passes sufficiency rating (SUFFICIENT / PARTIAL / INSUFFICIENT) and gap list to Gap Routing Decision.",
                input_summary="Aggregated claims & vector similarities"
            ),
            WorkflowNode(
                node_id="node_gap_decision",
                node_type=NodeType.DECISION,
                label="Gap Routing Decision",
                description="Determines whether to proceed to synthesis or re-investigate gaps",
                status=NodeStatus.PENDING,
                position={"x": 1140.0, "y": 360.0},
                phase=4,
                phase_title="PHASE 4 — EVIDENCE RECONCILIATION",
                mechanism="deterministic_routing",
                predecessor_node_id="node_auditor",
                successor_node_id="node_synthesizer",
                selection_reason="Deterministic routing: routes to Answer Synthesizer if sufficient, or triggers bounded investigation loop if gaps found.",
                tools_called=["DeterministicRoutingGate"],
                handoff_summary="Routes approved evidence package to Answer Synthesizer.",
                input_summary="Audited sufficiency & unresolved subquestion list"
            ),
            # Phase 5: Synthesis and Validation (x=1500)
            WorkflowNode(
                node_id="node_synthesizer",
                node_type=NodeType.SYNTHESIS,
                label="Answer Synthesizer",
                description="Synthesizes structured procedural answer or switches to verified evidence-only mode",
                status=NodeStatus.PENDING,
                position={"x": 1500.0, "y": 80.0},
                phase=5,
                phase_title="PHASE 5 — SYNTHESIS & VALIDATION",
                agent_role="answer_synthesizer",
                mechanism="llm_reasoning",
                predecessor_node_id="node_gap_decision",
                successor_node_id="node_validators",
                selection_reason="Synthesizes final answer strictly using approved evidence items and specialist claims (grounded synthesis).",
                tools_called=["CrewAI Answer Synthesizer Agent"],
                handoff_summary="Passes draft synthesized answer with citation markers [1] to Deterministic Validation.",
                input_summary="Audited evidence passages & structured findings"
            ),
            WorkflowNode(
                node_id="node_validators",
                node_type=NodeType.VALIDATOR,
                label="Deterministic Validation",
                description="Validates citation integrity, subquestion coverage, and server invariants",
                status=NodeStatus.PENDING,
                position={"x": 1500.0, "y": 220.0},
                phase=5,
                phase_title="PHASE 5 — SYNTHESIS & VALIDATION",
                mechanism="deterministic_validator",
                predecessor_node_id="node_synthesizer",
                successor_node_id="node_output",
                selection_reason="Deterministic validation: verifies exact quotation match against chunks and checks coverage rate.",
                tools_called=["CitationValidator", "AnswerCoverageValidator"],
                handoff_summary="Passes verified citations and validation report to Final Response Assembly.",
                input_summary="Draft answer, bracket citations, planned subquestions"
            ),
            WorkflowNode(
                node_id="node_output",
                node_type=NodeType.OUTPUT,
                label="Final Response Assembly",
                description="Produces typed FinalAgenticResponse payload",
                status=NodeStatus.PENDING,
                position={"x": 1500.0, "y": 360.0},
                phase=5,
                phase_title="PHASE 5 — SYNTHESIS & VALIDATION",
                mechanism="deterministic_assembly",
                predecessor_node_id="node_validators",
                successor_node_id=None,
                selection_reason="Final envelope packaging: bundles answers, citations, token diagnostics, latency, and audit report.",
                tools_called=["ResponseAssembler"],
                handoff_summary="Delivers final response payload to Agentic Intelligence chatbot.",
                input_summary="Validated output & audit telemetry"
            )
        ]

        edges = [
            WorkflowEdge(edge_id="e_req_plan", source_node_id="node_request", target_node_id="node_planner", label="Proceed"),
            WorkflowEdge(edge_id="e_plan_enc", source_node_id="node_planner", target_node_id="node_encoder", label="Subqueries"),
            WorkflowEdge(edge_id="e_enc_ret", source_node_id="node_encoder", target_node_id="node_retrieval", label="Vectors"),
            WorkflowEdge(edge_id="e_ret_ctx", source_node_id="node_retrieval", target_node_id="node_context", label="Raw Hits"),
            WorkflowEdge(edge_id="e_ctx_proc", source_node_id="node_context", target_node_id="node_proc_analyst", label="Procedural"),
            WorkflowEdge(edge_id="e_ctx_conf", source_node_id="node_context", target_node_id="node_conf_analyst", label="Config"),
            WorkflowEdge(edge_id="e_ctx_rel", source_node_id="node_context", target_node_id="node_rel_analyst", label="Relationship"),
            WorkflowEdge(edge_id="e_ctx_ts", source_node_id="node_context", target_node_id="node_ts_analyst", label="Troubleshoot"),
            WorkflowEdge(edge_id="e_proc_ledg", source_node_id="node_proc_analyst", target_node_id="node_ledger", label="Findings"),
            WorkflowEdge(edge_id="e_conf_ledg", source_node_id="node_conf_analyst", target_node_id="node_ledger", label="Findings"),
            WorkflowEdge(edge_id="e_rel_ledg", source_node_id="node_rel_analyst", target_node_id="node_ledger", label="Findings"),
            WorkflowEdge(edge_id="e_ts_ledg", source_node_id="node_ts_analyst", target_node_id="node_ledger", label="Findings"),
            WorkflowEdge(edge_id="e_ledg_aud", source_node_id="node_ledger", target_node_id="node_auditor", label="Claims"),
            WorkflowEdge(edge_id="e_aud_gap", source_node_id="node_auditor", target_node_id="node_gap_decision", label="Sufficiency"),
            WorkflowEdge(edge_id="e_gap_syn", source_node_id="node_gap_decision", target_node_id="node_synthesizer", label="Proceed"),
            WorkflowEdge(edge_id="e_syn_val", source_node_id="node_synthesizer", target_node_id="node_validators", label="Draft"),
            WorkflowEdge(edge_id="e_val_out", source_node_id="node_validators", target_node_id="node_output", label="Verified")
        ]

        return nodes, edges

    def create_run(
        self,
        query: str = "",
        run_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> RunSnapshot:
        """Create a new run snapshot and initialize graph state."""
        rid = run_id or kwargs.get("run_id") or f"run-{uuid.uuid4().hex[:10]}"
        q_text = query or kwargs.get("query", "")
        uid = user_id or kwargs.get("user_id")
        nodes, edges = self.build_initial_graph(rid, q_text)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Initial request accepted event
        init_evt = WorkflowEvent(
            run_id=rid,
            sequence=1,
            event_type=WorkflowEventType.RUN_STARTED,
            node_id="node_request",
            status=NodeStatus.SUCCEEDED,
            timestamp=now_iso,
            summary="Workflow run initiated and request accepted"
        )
        self._sequences[rid] = 1

        snapshot = RunSnapshot(
            run_id=rid,
            query=q_text,
            user_id=uid,
            status=NodeStatus.QUEUED,
            current_stage="request_accepted",
            started_at=now_iso,
            nodes=nodes,
            edges=edges,
            events=[init_evt]
        )
        self._runs[rid] = snapshot
        self._subscribers[rid] = []
        return snapshot

    def get_run(self, run_id: str) -> Optional[RunSnapshot]:
        return self._runs.get(run_id)

    def get_snapshot(self, run_id: str) -> Optional[RunSnapshot]:
        return self.get_run(run_id)

    def list_runs(self, limit: int = 20) -> List[RunSnapshot]:
        runs = list(self._runs.values())
        runs.sort(key=lambda r: r.started_at, reverse=True)
        return runs[:limit]

    def apply_event(self, event: WorkflowEvent) -> Optional[RunSnapshot]:
        """
        Record event in run snapshot, update node/edge states, and dispatch to all active subscribers.
        Returns the updated RunSnapshot.
        """
        rid = event.run_id
        snapshot = self._runs.get(rid)
        if not snapshot:
            logger.warning(f"Attempted to apply event for unknown run_id: {rid}")
            return None

        # Assign sequence number if not set
        if not event.sequence:
            event.sequence = self._next_sequence(rid)

        snapshot.events.append(event)

        # Update node status and properties
        if event.node_id:
            for node in snapshot.nodes:
                if node.node_id == event.node_id:
                    if event.status:
                        node.status = event.status
                    if event.duration_ms is not None:
                        node.duration_ms = event.duration_ms
                    if event.input_summary:
                        node.input_summary = event.input_summary
                    if event.output_summary:
                        node.output_summary = event.output_summary
                    if event.summary:
                        node.summary = event.summary
                    if event.predecessor_node_id:
                        node.predecessor_node_id = event.predecessor_node_id
                    if event.successor_node_id:
                        node.successor_node_id = event.successor_node_id
                    if event.selection_reason:
                        node.selection_reason = event.selection_reason
                    if event.tools_called:
                        node.tools_called = event.tools_called
                    if event.handoff_summary:
                        node.handoff_summary = event.handoff_summary

                    if event.evidence_refs:
                        node.evidence_refs = event.evidence_refs
                    if event.metrics:
                        node.metrics.update(event.metrics)
                    if event.error:
                        node.error_summary = event.error if isinstance(event.error, str) else event.error.get("message")
                    if event.event_type == WorkflowEventType.NODE_STARTED:
                        node.started_at = event.timestamp
                        node.status = NodeStatus.RUNNING
                    elif event.event_type in (
                        WorkflowEventType.NODE_SUCCEEDED,
                        WorkflowEventType.NODE_PARTIAL,
                        WorkflowEventType.NODE_FAILED,
                        WorkflowEventType.NODE_BLOCKED,
                        WorkflowEventType.NODE_SKIPPED
                    ):
                        node.completed_at = event.timestamp
                    break

            # Handle dynamic gap investigation loop edge
            if event.node_id == "node_gap_decision" and event.round and event.round > 0:
                loop_edge_id = f"edge-loop-gap-{event.round}"
                existing_edge = next((e for e in snapshot.edges if e.edge_id == loop_edge_id), None)
                if not existing_edge:
                    snapshot.edges.append(
                        WorkflowEdge(
                            edge_id=loop_edge_id,
                            source_node_id="node_gap_decision",
                            target_node_id="node_retrieval",
                            label=f"Evidence Gap (Loop Round {event.round})",
                            status="active",
                            animated=True,
                            condition=f"Investigation Round {event.round}"
                        )
                    )

            # Update edges: animate active edges into running nodes
            for edge in snapshot.edges:
                if edge.target_node_id == event.node_id:
                    if event.event_type == WorkflowEventType.NODE_STARTED:
                        edge.status = "active"
                        edge.animated = True
                    elif event.event_type in (
                        WorkflowEventType.NODE_SUCCEEDED,
                        WorkflowEventType.NODE_PARTIAL
                    ):
                        edge.status = "completed"
                        edge.animated = False
                    elif event.event_type in (
                        WorkflowEventType.NODE_BLOCKED,
                        WorkflowEventType.NODE_FAILED
                    ):
                        edge.status = "blocked"
                        edge.animated = False

        if event.summary and event.event_type != WorkflowEventType.HEARTBEAT and event.summary.lower() != "heartbeat":
            snapshot.current_stage = event.summary[:60]

        # Handle terminal events with truthful outcome determination
        if event.event_type == WorkflowEventType.RUN_COMPLETED:
            synth_node = next((n for n in snapshot.nodes if n.node_id == "node_synthesizer"), None)
            retrieval_node = next((n for n in snapshot.nodes if n.node_id == "node_retrieval"), None)

            if event.status in (NodeStatus.PARTIAL, "partial"):
                snapshot.status = NodeStatus.PARTIAL.value
            elif event.status in (NodeStatus.EVIDENCE_ONLY, "evidence_only"):
                snapshot.status = NodeStatus.EVIDENCE_ONLY.value
            elif synth_node and synth_node.status in (NodeStatus.BLOCKED, NodeStatus.FAILED, "blocked", "failed"):
                # Synthesis blocked (e.g. quota limit) or failed
                if retrieval_node and retrieval_node.status == NodeStatus.SUCCEEDED:
                    snapshot.status = NodeStatus.EVIDENCE_ONLY.value
                else:
                    snapshot.status = NodeStatus.FAILED.value
            elif any(n.status in (NodeStatus.FAILED, "failed") for n in snapshot.nodes if n.node_id in ("node_request", "node_retrieval")):
                snapshot.status = NodeStatus.FAILED.value
            elif any(n.status in (NodeStatus.BLOCKED, "blocked") for n in snapshot.nodes):
                snapshot.status = NodeStatus.PARTIAL.value
            else:
                snapshot.status = NodeStatus.SUCCEEDED.value

            snapshot.completed_at = event.timestamp
            if event.duration_ms:
                snapshot.total_duration_ms = event.duration_ms
        elif event.event_type == WorkflowEventType.RUN_FAILED:
            snapshot.status = NodeStatus.FAILED.value
            snapshot.completed_at = event.timestamp
            snapshot.error_message = event.summary
        elif event.event_type == WorkflowEventType.RUN_CANCELLED:
            snapshot.status = NodeStatus.CANCELLED.value
            snapshot.completed_at = event.timestamp
            snapshot.error_message = "Workflow run cancelled by user or deadline"

        # Dispatch to active SSE subscriber queues
        queues = self._subscribers.get(rid, [])
        for q in list(queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Subscriber queue full for run {rid}")

        return snapshot

    async def emit_event(self, event: WorkflowEvent):
        """Async wrapper for apply_event."""
        return self.apply_event(event)

    async def subscribe(self, run_id: str, last_sequence: int = 0) -> AsyncGenerator[Dict[str, Any], None]:
        """
        SSE generator for live event streaming (dictionary format for FastAPI sse-starlette).
        Replays existing events since `last_sequence`, then yields live events as they occur.
        """
        snapshot = self._runs.get(run_id)
        if not snapshot:
            yield {"event": "error", "data": f'{{"error": "Run {run_id} not found"}}'}
            return

        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(q)

        try:
            # 1. Replay missed events
            for evt in snapshot.events:
                if evt.sequence > last_sequence:
                    yield {
                        "id": str(evt.sequence),
                        "event": evt.event_type.value,
                        "data": evt.model_dump_json()
                    }

            # 2. Yield live events
            while True:
                try:
                    evt: WorkflowEvent = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield {
                        "id": str(evt.sequence),
                        "event": evt.event_type.value,
                        "data": evt.model_dump_json()
                    }
                    if evt.event_type in (
                        WorkflowEventType.RUN_COMPLETED,
                        WorkflowEventType.RUN_FAILED,
                        WorkflowEventType.RUN_CANCELLED
                    ):
                        break
                except asyncio.TimeoutError:
                    # Emit periodic heartbeat to keep SSE connection alive
                    hb = WorkflowEvent(
                        run_id=run_id,
                        sequence=self._next_sequence(run_id),
                        event_type=WorkflowEventType.HEARTBEAT,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        summary="heartbeat"
                    )
                    yield {
                        "id": str(hb.sequence),
                        "event": "heartbeat",
                        "data": hb.model_dump_json()
                    }
                    # If run has finished while idling, exit
                    if snapshot.status in ("succeeded", "partial", "failed", "cancelled"):
                        break
        finally:
            if run_id in self._subscribers and q in self._subscribers[run_id]:
                self._subscribers[run_id].remove(q)

    async def event_generator(
        self,
        run_id: str,
        last_sequence: int = 0,
        heartbeat_interval: float = 15.0
    ) -> AsyncGenerator[str, None]:
        """
        SSE generator yielding raw SSE formatted strings (data: {...}\n\n).
        """
        async for item in self.subscribe(run_id=run_id, last_sequence=last_sequence):
            yield f"data: {item['data']}\n\n"

    def cancel_run(self, run_id: str) -> Optional[RunSnapshot]:
        """Cancel an in-progress workflow run."""
        task = self._tasks.get(run_id)
        snapshot = self._runs.get(run_id)
        if not snapshot:
            return None

        if task and not task.done():
            task.cancel()

        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot.status = NodeStatus.CANCELLED
        snapshot.completed_at = now_iso
        snapshot.error_message = "Run cancelled by user request"

        # Mark all pending/running nodes as cancelled
        for node in snapshot.nodes:
            if node.status in (NodeStatus.PENDING, NodeStatus.QUEUED, NodeStatus.RUNNING):
                node.status = NodeStatus.CANCELLED
                node.summary = f"{node.label}: User cancelled"

        evt = WorkflowEvent(
            run_id=run_id,
            sequence=self._next_sequence(run_id),
            event_type=WorkflowEventType.RUN_CANCELLED,
            node_id="node_request",
            status=NodeStatus.CANCELLED,
            timestamp=now_iso,
            summary="Workflow run cancelled by user request"
        )
        self.apply_event(evt)
        return snapshot

    def register_task(self, run_id: str, task: asyncio.Task):
        self._tasks[run_id] = task


# Module-level singleton instance and helper exports
workflow_run_manager = WorkflowRunManager.get_instance()

def build_canonical_graph(run_id: str, query: str):
    return workflow_run_manager.build_initial_graph(run_id, query)

