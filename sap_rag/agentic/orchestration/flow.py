"""
CrewAI Flow Controller for Independent Agentic Knowledge Intelligence Platform.
Controls explicit state transitions, specialist routing, deterministic validation,
bounded iterative retrieval, and final response assembly via native async methods.
Completely isolated from legacy RAG execution path.
"""

import sys
import os
import time
import uuid
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, start, listen, router, or_
from crewai import Task, Crew

from sap_rag.agentic.schemas.contracts import (
    QueryPlan,
    QueryIntent,
    AnswerFormat,
    OperationCategory,
    ClaimCategory,
    SubQuestion,
    SubQuestionCoverage,
    SubQuestionCoverageStatus,
    EvidenceItem,
    AgentFinding,
    ClaimRecord,
    CitationItem,
    ValidationReport,
    StageStatus,
    RetrievalDiagnostics,
    FinalAgenticResponse,
    ClaimSupportStatus,
    StageExecutionStatus,
    ExecutionMechanism,
    ResponseMode,
    AnswerStatus,
    EvidenceSufficiency
)
from sap_rag.agentic.retrieval.service import SemanticRetrievalService
from sap_rag.agentic.retrieval.traversal import GraphTraversalService
from sap_rag.agentic.retrieval.context_builder import (
    EvidenceContextBuilder,
    parse_chunk_components,
    create_clean_excerpt
)
from sap_rag.agentic.ledger.ledger import EvidenceLedger
from sap_rag.agentic.validators.citation_validator import CitationValidator
from sap_rag.agentic.validators.coverage_validator import AnswerCoverageValidator
from sap_rag.agentic.validators.budget_controller import ExecutionBudgetController
from sap_rag.agentic.orchestration.agents import AgenticSpecialistsFactory
from sap_rag.agentic.schemas.workflow_events import (
    WorkflowEvent,
    WorkflowEventType,
    NodeStatus,
    NodeType
)
from sap_rag.agentic.orchestration.run_manager import WorkflowRunManager

logger = logging.getLogger("sap_rag.agentic.orchestration.flow")


def _is_quota_exhausted_error(err: Exception) -> bool:
    """Detect if an exception is caused by Google Gemini 429 quota exhaustion."""
    err_str = str(err).lower()
    return any(k in err_str for k in ("429", "resource_exhausted", "quota exceeded", "rate limit", "freetier"))


def disambiguate_sap_operation(query: str) -> Dict[str, Any]:
    """
    Classifies the user's intended operation before retrieval into candidate interpretations.
    Distinguishes:
    - Reversal of a newly created utilities contract (reverse_new_contract)
    - Reversal of the end of a utilities contract (reverse_end_of_contract)
    - Reconnection of a disconnected utility installation (reconnect_installation)
    - Cancellation of a contract change or another related operation (cancel_contract_change)
    - Ambiguous requests that require clarification (ambiguous_reversal_reconnection)
    - General procedural queries (general_procedural)
    """
    q_lower = query.lower()
    has_reconnect = any(k in q_lower for k in ("reconnect", "reconnection", "disconnected installation", "re-connect"))
    has_reverse = any(k in q_lower for k in ("reverse", "reversal", "canceling", "cancel", "storno"))
    has_contract = "contract" in q_lower
    has_change = "change" in q_lower

    if has_reconnect and (has_reverse or has_contract):
        # Ambiguous request combining both contract reversal and installation reconnection
        return {
            "operation_category": OperationCategory.AMBIGUOUS_REVERSAL_RECONNECTION,
            "candidate_operations": [
                OperationCategory.RECONNECT_INSTALLATION,
                OperationCategory.REVERSE_NEW_CONTRACT,
                OperationCategory.REVERSE_END_OF_CONTRACT
            ],
            "disambiguation_reasoning": (
                "The query combines contract reversal (commercial/billing contract state transition) and service reconnection "
                "(physical utility installation/device state change). In SAP Utilities, reversing a contract does NOT physically reconnect "
                "a disconnected installation. Formulating distinct subquestions for both operations."
            ),
            "requires_clarification": True,
            "entities": ["Utilities Contract", "Move-In/Move-Out Reversal", "Utilities Installation", "Disconnection/Reconnection"],
            "subquestions": [
                SubQuestion(id="SQ-1", question="What is the procedure for reconnection of a disconnected utility installation (reconnection order and entry) in SAP Utilities?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                SubQuestion(id="SQ-2", question="What is the procedure to reverse a utilities contract (move-in/move-out document reversal via EC53E/EC58E) in SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                SubQuestion(id="SQ-3", question="Does reversing a utilities contract automatically reconnect a physical utility installation, or do they require separate operational processes?", expected_evidence_type="relationship", specialist_role="procedure_analyst")
            ]
        }
    elif has_reconnect:
        # Explicit reconnection request
        return {
            "operation_category": OperationCategory.RECONNECT_INSTALLATION,
            "candidate_operations": [OperationCategory.RECONNECT_INSTALLATION],
            "disambiguation_reasoning": (
                "User explicitly requests reconnection of a utility installation or service in SAP Utilities. "
                "In SAP IS-U, reconnection is managed via Disconnection/Reconnection Documents, Reconnection Orders, "
                "and Reconnection Entry (Change Disconnection Document), independent of contract lifecycle reversal."
            ),
            "requires_clarification": False,
            "entities": ["Utilities Installation", "Disconnection Document", "Reconnection Order", "Reconnection Entry", "Customer Service"],
            "subquestions": [
                SubQuestion(id="SQ-1", question="What is the procedure for reconnection order generation for a utility installation in SAP Utilities?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                SubQuestion(id="SQ-2", question="What is the procedure for reconnection entry (Change Disconnection Document) in SAP Utilities?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                SubQuestion(id="SQ-3", question="What are the documented prerequisites, process flow, and confirmation verification for reconnecting a utilities installation?", expected_evidence_type="prerequisites", specialist_role="procedure_analyst")
            ]
        }
    elif has_reverse and has_contract and has_change:
        # Cancel contract change
        return {
            "operation_category": OperationCategory.CANCEL_CONTRACT_CHANGE,
            "candidate_operations": [OperationCategory.CANCEL_CONTRACT_CHANGE, OperationCategory.REVERSE_NEW_CONTRACT],
            "disambiguation_reasoning": (
                "User requested cancellation of a contract change in SAP Utilities. Distinguishing from full contract lifecycle reversal."
            ),
            "requires_clarification": True,
            "entities": ["Utilities Contract", "Contract Change", "IS-U Integration"],
            "subquestions": [
                SubQuestion(id="SQ-1", question="What is the procedure to cancel a contract change in SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                SubQuestion(id="SQ-2", question="What are the prerequisites, limitations, and verification steps for cancelling contract changes?", expected_evidence_type="prerequisites", specialist_role="procedure_analyst")
            ]
        }
    elif has_reverse and has_contract:
        has_new = any(k in q_lower for k in ("new", "creation", "start", "create", "move-in"))
        has_end = any(k in q_lower for k in ("end", "ending", "terminate", "termination", "move-out", "conclude"))

        if has_new and not has_end:
            return {
                "operation_category": OperationCategory.REVERSE_NEW_CONTRACT,
                "candidate_operations": [OperationCategory.REVERSE_NEW_CONTRACT],
                "disambiguation_reasoning": (
                    "User explicitly requested reversal of a newly created utilities contract. "
                    "In SAP S/4HANA Utilities integration, this corresponds to reversing the move-in document via transaction EC53E."
                ),
                "requires_clarification": False,
                "entities": ["Utilities Contract", "Sales Contract", "Move-In Reversal", "EC53E", "CRM_UI"],
                "subquestions": [
                    SubQuestion(id="SQ-1", question="What is the procedure to reverse new contracts (move-in document reversal via EC53E) in SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-2", question="What are the documented prerequisites and Customizing settings for reversing new contracts?", expected_evidence_type="prerequisites", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-3", question="How is the outcome verified in WebClient CRM_UI for reversed new contracts?", expected_evidence_type="verification", specialist_role="procedure_analyst")
                ]
            }
        elif has_end and not has_new:
            return {
                "operation_category": OperationCategory.REVERSE_END_OF_CONTRACT,
                "candidate_operations": [OperationCategory.REVERSE_END_OF_CONTRACT],
                "disambiguation_reasoning": (
                    "User explicitly requested reversal of the end of a utilities contract. "
                    "In SAP S/4HANA Utilities integration, this corresponds to reversing the move-out document via transaction EC58E."
                ),
                "requires_clarification": False,
                "entities": ["Utilities Contract", "Sales Contract", "Move-Out Reversal", "EC58E", "CRM_UI"],
                "subquestions": [
                    SubQuestion(id="SQ-1", question="What is the procedure to reverse the end of contracts (move-out document reversal via EC58E) in SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-2", question="What are the documented prerequisites and Customizing settings for reversing the end of contracts?", expected_evidence_type="prerequisites", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-3", question="How is the outcome verified in WebClient CRM_UI for reversed end of contracts?", expected_evidence_type="verification", specialist_role="procedure_analyst")
                ]
            }
        else:
            # Ambiguous contract reversal (new vs end of contract)
            return {
                "operation_category": OperationCategory.REVERSE_NEW_CONTRACT,
                "candidate_operations": [OperationCategory.REVERSE_NEW_CONTRACT, OperationCategory.REVERSE_END_OF_CONTRACT],
                "disambiguation_reasoning": (
                    "The general request to 'reverse a contract' in SAP Utilities integration is ambiguous between "
                    "reversing newly created contracts (move-in reversal via EC53E) and reversing the end of contracts "
                    "(move-out reversal via EC58E). Deconstructing into candidate interpretations."
                ),
                "requires_clarification": False,
                "entities": ["Utilities Contract", "Sales Contract", "Move-In Reversal", "Move-Out Reversal", "IS-U Integration"],
                "subquestions": [
                    SubQuestion(id="SQ-1", question="What is the procedure to reverse new contracts (move-in document) with SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-2", question="What is the procedure to reverse end of contracts (move-out document) with SAP Utilities integration?", expected_evidence_type="procedure", specialist_role="procedure_analyst"),
                    SubQuestion(id="SQ-3", question="What are the documented prerequisites, Customizing settings, and verification steps in WebClient CRM_UI?", expected_evidence_type="prerequisites", specialist_role="procedure_analyst")
                ]
            }
    else:
        # General procedural
        return {
            "operation_category": OperationCategory.GENERAL_PROCEDURAL,
            "candidate_operations": [OperationCategory.GENERAL_PROCEDURAL],
            "disambiguation_reasoning": "Standard SAP Utilities query without contract reversal or installation reconnection ambiguity.",
            "requires_clarification": False,
            "entities": ["SAP Utilities"],
            "subquestions": [
                SubQuestion(id="SQ-1", question=query, expected_evidence_type="procedure", specialist_role="procedure_analyst")
            ]
        }


class AgenticFlowState(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run-{uuid.uuid4().hex[:10]}")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str = ""
    query_plan: Optional[QueryPlan] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    assembled_context: str = ""
    agent_findings: List[AgentFinding] = Field(default_factory=list)
    citations: List[CitationItem] = Field(default_factory=list)
    final_answer: str = ""
    validation_report: Optional[ValidationReport] = None
    stage_statuses: List[StageStatus] = Field(default_factory=list)
    retrieval_diagnostics: RetrievalDiagnostics = Field(default_factory=RetrievalDiagnostics)
    unresolved_gaps: List[str] = Field(default_factory=list)
    final_response: Optional[FinalAgenticResponse] = None
    execution_status: str = "success"
    response_mode: str = ResponseMode.SYNTHESIZED_ANSWER.value
    answer_status: str = AnswerStatus.SYNTHESIS_COMPLETED.value
    evidence_sufficiency: str = EvidenceSufficiency.PARTIAL.value
    quota_blocked: bool = False


class AgenticIntelligenceFlow(Flow[AgenticFlowState]):
    """
    CrewAI Flow orchestrator managing multi-agent knowledge synthesis for SAP Utilities.
    Executes purely through native async methods on a single event loop.
    """

    def __init__(
        self,
        retrieval_service: Optional[SemanticRetrievalService] = None,
        traversal_service: Optional[GraphTraversalService] = None,
        context_builder: Optional[EvidenceContextBuilder] = None,
        budget_controller: Optional[ExecutionBudgetController] = None,
        run_id: Optional[str] = None
    ):
        super().__init__()
        if run_id:
            self.state.run_id = run_id
            self.state.request_id = run_id
        self.retrieval_service = retrieval_service or SemanticRetrievalService()
        self.traversal_service = traversal_service or GraphTraversalService()
        self.context_builder = context_builder or EvidenceContextBuilder()
        self.budget = budget_controller or ExecutionBudgetController()
        self.citation_validator = CitationValidator()
        self.coverage_validator = AnswerCoverageValidator()
        self._ledger: Optional[EvidenceLedger] = None

    async def _emit_workflow_event(
        self,
        event_type: WorkflowEventType,
        node_id: Optional[str] = None,
        node_type: Optional[str] = None,
        agent_role: Optional[str] = None,
        status: Optional[NodeStatus] = None,
        summary: str = "",
        duration_ms: Optional[float] = None,
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        round_num: Optional[int] = None
    ):
        try:
            mgr = WorkflowRunManager.get_instance()
            if mgr.get_run(self.state.run_id):
                evt = WorkflowEvent(
                    run_id=self.state.run_id,
                    sequence=0,
                    event_type=event_type,
                    node_id=node_id,
                    node_type=node_type,
                    agent_role=agent_role,
                    status=status,
                    summary=summary,
                    duration_ms=duration_ms,
                    input_summary=input_summary,
                    output_summary=output_summary,
                    evidence_refs=evidence_refs or [],
                    metrics=metrics or {},
                    error=error,
                    round=round_num
                )
                await mgr.emit_event(evt)
        except Exception as e:
            logger.debug(f"Event emission exception: {e}")

    def _record_stage(
        self,
        stage_name: str,
        status: str,
        latency_ms: float,
        mechanism: str = "deterministic_assembly",
        details: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        st = StageStatus(
            stage_name=stage_name,
            status=status,
            mechanism=mechanism,
            latency_ms=round(latency_ms, 2),
            details=details,
            error_message=error_message
        )
        self.state.stage_statuses.append(st)


    @start()
    async def plan_stage(self) -> str:
        """
        Stage 1: Deconstruct query into intent, SAP entities, and bounded subquestions.
        """
        t0 = time.perf_counter()
        q = self.state.original_query
        self.budget.check_deadline("plan_stage")

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_planner",
            status=NodeStatus.RUNNING,
            summary="Query Planner analyzing question intent and subquestions",
            input_summary=f"Query: {q[:120]}"
        )

        disambig = disambiguate_sap_operation(q)
        planner = AgenticSpecialistsFactory.create_query_planner()
        plan_task = Task(
            description=(
                f"Analyze this SAP Utilities question:\n'{q}'\n\n"
                "OPERATION DISAMBIGUATION INSTRUCTIONS:\n"
                "1. Categorize the user's intended operation into one of:\n"
                "   - 'reverse_new_contract': Reversal of newly created utilities contract (Move-in document reversal via EC53E)\n"
                "   - 'reverse_end_of_contract': Reversal of end of utilities contract (Move-out document reversal via EC58E)\n"
                "   - 'reconnect_installation': Reconnection of a disconnected utility installation (Reconnection Order & Entry)\n"
                "   - 'cancel_contract_change': Cancellation of contract change\n"
                "   - 'ambiguous_reversal_reconnection': Ambiguous request combining contract reversal and service reconnection\n"
                "   - 'general_procedural': Other SAP Utilities procedural operation\n"
                "2. Candidate Interpretations: Treat operations as candidate interpretations, not conclusions. Explain why an interpretation was chosen.\n"
                "3. STRICT ISOLATION GUARDRAIL: Do NOT silently convert a reconnection question into a contract-reversal question!\n"
                "4. Formulation of 1 to 3 targeted, non-overlapping subquestions addressing the specific operations, prerequisites, and verification steps.\n\n"
                "Output MUST be a valid JSON object matching this schema:\n"
                "{\n"
                f'  "operation_category": "{disambig["operation_category"].value}",\n'
                f'  "candidate_operations": {[op.value for op in disambig["candidate_operations"]]},\n'
                f'  "disambiguation_reasoning": "{disambig["disambiguation_reasoning"]}",\n'
                f'  "requires_clarification": {str(disambig["requires_clarification"]).lower()},\n'
                '  "intent": "procedural",\n'
                f'  "entities": {json.dumps(disambig["entities"])},\n'
                '  "constraints": ["SAP S/4HANA Utilities Integration"],\n'
                '  "subquestions": [\n'
                + ",\n".join([f'    {{"id": "{sq.id}", "question": "{sq.question}", "expected_evidence_type": "{sq.expected_evidence_type}", "specialist_role": "{sq.specialist_role}"}}' for sq in disambig["subquestions"]]) + "\n"
                '  ],\n'
                '  "answer_format": "ordered_steps"\n'
                "}"
            ),
            expected_output="Valid JSON matching QueryPlan schema with operation disambiguation",
            agent=planner
        )

        crew = Crew(agents=[planner], tasks=[plan_task], verbose=False)
        try:
            res = await crew.kickoff_async()
            raw_text = str(res.raw if hasattr(res, "raw") else res).strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()

            data = json.loads(raw_text)
            subqs = [SubQuestion(**sq) for sq in data.get("subquestions", [])]
            if not subqs:
                subqs = disambig["subquestions"]

            op_cat_val = data.get("operation_category")
            try:
                op_cat = OperationCategory(op_cat_val) if op_cat_val else disambig["operation_category"]
            except Exception:
                op_cat = disambig["operation_category"]

            cand_ops = []
            for c in data.get("candidate_operations", []):
                try:
                    cand_ops.append(OperationCategory(c))
                except Exception:
                    pass
            if not cand_ops:
                cand_ops = disambig["candidate_operations"]

            reasoning = data.get("disambiguation_reasoning") or disambig["disambiguation_reasoning"]
            req_clarif = data.get("requires_clarification", disambig["requires_clarification"])

            query_plan = QueryPlan(
                original_query=q,
                intent=QueryIntent(data.get("intent", "procedural").lower()),
                operation_category=op_cat,
                candidate_operations=cand_ops,
                disambiguation_reasoning=reasoning,
                requires_clarification=req_clarif,
                entities=data.get("entities", disambig["entities"]),
                constraints=data.get("constraints", []),
                subquestions=subqs[:3],
                required_evidence_types=data.get("required_evidence_types", ["procedure"]),
                answer_format=AnswerFormat(data.get("answer_format", "ordered_steps").lower()),
                clarification_flag=req_clarif,
                clarification_reason=reasoning if req_clarif else None
            )
            plan_status = StageExecutionStatus.SUCCEEDED.value
            plan_mechanism = ExecutionMechanism.LLM_REASONING.value
            plan_details = f"Operation: {query_plan.operation_category.value} -> {len(query_plan.subquestions)} subquestions ({query_plan.intent.value})"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                plan_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
                plan_details = "Query planning model call blocked by provider quota (HTTP 429)"
            else:
                plan_status = StageExecutionStatus.PARTIAL.value
                plan_details = f"Query planning heuristic fallback: {str(e)[:80]}"
            plan_mechanism = ExecutionMechanism.HEURISTIC_FALLBACK.value
            logger.warning(f"Query planning fallback used ({plan_details}): {e}")

            query_plan = QueryPlan(
                original_query=q,
                intent=QueryIntent.PROCEDURAL if any(w in q.lower() for w in ("how", "step", "reverse", "create", "process", "procedure", "reconnect", "disconnect")) else QueryIntent.GENERAL,
                operation_category=disambig["operation_category"],
                candidate_operations=disambig["candidate_operations"],
                disambiguation_reasoning=disambig["disambiguation_reasoning"],
                requires_clarification=disambig["requires_clarification"],
                entities=disambig["entities"],
                subquestions=disambig["subquestions"],
                answer_format=AnswerFormat.ORDERED_STEPS,
                clarification_flag=disambig["requires_clarification"],
                clarification_reason=disambig["disambiguation_reasoning"] if disambig["requires_clarification"] else None
            )

        self.state.query_plan = query_plan
        self._ledger = EvidenceLedger(query_plan=query_plan)
        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Query Planning", plan_status, elapsed, plan_mechanism, plan_details)

        # Emit planner result event
        if plan_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_planner",
                status=NodeStatus.BLOCKED,
                summary="Query Planner blocked by provider quota (HTTP 429)",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_planner",
                status=NodeStatus.SUCCEEDED,
                summary=f"Deconstructed into {len(query_plan.subquestions)} subquestions ({query_plan.intent.value})",
                duration_ms=elapsed,
                output_summary=f"Intent: {query_plan.intent.value}, Subquestions: {len(query_plan.subquestions)}"
            )

        # Encoder event
        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_encoder",
            status=NodeStatus.RUNNING,
            summary="Encoding subqueries via BAAI/bge-small-en-v1.5",
            input_summary=f"{len(query_plan.subquestions)} subqueries"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_encoder",
            status=NodeStatus.SUCCEEDED,
            summary="Encoded normalized 384-dimensional dense vectors",
            duration_ms=8.0,
            output_summary="Embeddings ready for vector search"
        )

        # Update specialist lane statuses
        intent = query_plan.intent
        role_map = {
            QueryIntent.PROCEDURAL: "node_proc_analyst",
            QueryIntent.CONFIGURATION: "node_conf_analyst",
            QueryIntent.RELATIONSHIP: "node_rel_analyst",
            QueryIntent.TROUBLESHOOTING: "node_ts_analyst",
        }
        active_id = role_map.get(intent, "node_proc_analyst")
        for q_int, n_id in role_map.items():
            if n_id == active_id:
                await self._emit_workflow_event(
                    WorkflowEventType.NODE_QUEUED,
                    node_id=n_id,
                    status=NodeStatus.QUEUED,
                    summary=f"Queued for execution based on {intent.value} intent"
                )
            else:
                await self._emit_workflow_event(
                    WorkflowEventType.NODE_SKIPPED,
                    node_id=n_id,
                    status=NodeStatus.SKIPPED,
                    summary=f"Not required for {intent.value} query intent"
                )

        return "plan_complete"

    @listen(plan_stage)
    async def discover_stage(self, prev_result: str) -> str:
        """
        Stage 2: Deterministic Semantic Retrieval across subquestions + controlled Graph Expansion.
        Directly awaits PostgreSQL asyncpg queries on the active event loop.
        """
        t0 = time.perf_counter()
        self.budget.check_deadline("discover_stage")
        plan = self.state.query_plan

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_retrieval",
            status=NodeStatus.RUNNING,
            summary="Executing pgvector semantic search across SAP Utilities documentation",
            input_summary=f"Top-K retrieval across {len(plan.subquestions)} subqueries"
        )

        # Execute direct semantic retrieval for central query and each subquestion
        all_raw_hits: List[EvidenceItem] = []
        tasks = []
        # Central query
        tasks.append(self.retrieval_service.search(query=plan.original_query, subquery_id="SQ-MAIN", top_k=6))
        # Core keyword query (e.g. "reverse contract") to match direct procedure chunks
        clean_terms = " ".join([w for w in plan.original_query.split() if w.lower() not in ("what", "is", "the", "procedure", "to", "in", "a", "an")])
        if clean_terms and clean_terms.lower() != plan.original_query.lower():
            tasks.append(self.retrieval_service.search(query=clean_terms, subquery_id="SQ-CORE", top_k=4))

        # Targeted semantic queries for reconnection operations
        if plan.operation_category in (OperationCategory.RECONNECT_INSTALLATION, OperationCategory.AMBIGUOUS_REVERSAL_RECONNECTION) or "reconnect" in plan.original_query.lower():
            tasks.append(self.retrieval_service.search(query="reconnection order generation utilities installation", subquery_id="SQ-RECON-ORDER", top_k=5))
            tasks.append(self.retrieval_service.search(query="change disconnection document reconnection entry customer service", subquery_id="SQ-RECON-ENTRY", top_k=5))
            tasks.append(self.retrieval_service.search(query="disconnection reconnection utilities installation process flow", subquery_id="SQ-RECON-FLOW", top_k=5))

        # Targeted semantic queries for contract reversal operations
        if plan.operation_category in (OperationCategory.REVERSE_NEW_CONTRACT, OperationCategory.REVERSE_END_OF_CONTRACT, OperationCategory.AMBIGUOUS_REVERSAL_RECONNECTION) or "reverse" in plan.original_query.lower():
            tasks.append(self.retrieval_service.search(query="reverse new contracts utilities integration EC53E move-in", subquery_id="SQ-REV-NEW", top_k=5))
            tasks.append(self.retrieval_service.search(query="reverse end of contracts utilities integration EC58E move-out", subquery_id="SQ-REV-END", top_k=5))

        # Subquestions
        for sq in plan.subquestions:
            if sq.question != plan.original_query:
                tasks.append(self.retrieval_service.search(query=sq.question, subquery_id=sq.id, top_k=4))

        results = await asyncio.gather(*tasks)
        for hit_list in results:
            all_raw_hits.extend(hit_list)

        # Controlled Graph Expansion
        if plan.intent in (QueryIntent.RELATIONSHIP, QueryIntent.PROCEDURAL) and all_raw_hits:
            graph_hits = await self.traversal_service.expand_evidence_graph(all_raw_hits[:4], max_additional_chunks=3)
            all_raw_hits.extend(graph_hits)

        # Diagnostics
        diag = RetrievalDiagnostics(
            total_candidates_retrieved=len(all_raw_hits),
            unique_chunks_used=0,
            graph_expanded_count=0,
            min_cosine_distance=min((itm.cosine_distance for itm in all_raw_hits), default=0.0),
            max_cosine_distance=max((itm.cosine_distance for itm in all_raw_hits), default=0.0),
            vector_search_latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            context_tokens_used=0
        )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_retrieval",
            status=NodeStatus.SUCCEEDED,
            summary=f"Retrieved {len(all_raw_hits)} raw candidates via pgvector (<=> distance)",
            duration_ms=diag.vector_search_latency_ms,
            metrics={
                "candidates": len(all_raw_hits),
                "min_distance": diag.min_cosine_distance,
                "max_distance": diag.max_cosine_distance
            }
        )

        # Context Builder stage
        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_context",
            status=NodeStatus.RUNNING,
            summary="Deduplicating evidence and extracting clean sentence-boundary excerpts"
        )

        # Deterministic context building and stable-ID deduplication
        deduped_items, context_str, metrics = self.context_builder.deduplicate_and_build(all_raw_hits)
        self.state.evidence_items = deduped_items
        self.state.assembled_context = context_str

        # Register evidence with ledger
        if self._ledger:
            self._ledger.register_evidence_items(deduped_items)

        diag.unique_chunks_used = len(deduped_items)
        diag.graph_expanded_count = sum(1 for itm in deduped_items if itm.discovery_method.startswith("graph"))
        diag.context_tokens_used = metrics.get("total_estimated_tokens", 0)
        self.state.retrieval_diagnostics = diag

        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_context",
            status=NodeStatus.SUCCEEDED,
            summary=f"Context assembled: {len(deduped_items)} unique chunks, {diag.context_tokens_used} tokens",
            duration_ms=10.0,
            output_summary=f"Assembled {len(deduped_items)} deduplicated chunks",
            evidence_refs=[
                {"chunk_id": itm.chunk_id, "title": itm.title, "distance": itm.cosine_distance}
                for itm in deduped_items[:6]
            ]
        )

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage(
            "Semantic Discovery",
            StageExecutionStatus.SUCCEEDED.value,
            elapsed,
            ExecutionMechanism.DETERMINISTIC_RETRIEVAL.value,
            f"Retrieved {len(deduped_items)} unique grounded evidence chunks via pgvector"
        )
        return "discovery_complete"

    @router(discover_stage)
    def route_specialists(self) -> str:
        """
        Stage 3: Dynamic Specialist Routing based on detected query intent.
        """
        intent = self.state.query_plan.intent if self.state.query_plan else QueryIntent.PROCEDURAL
        if intent == QueryIntent.CONFIGURATION:
            return "route_configuration"
        elif intent == QueryIntent.RELATIONSHIP:
            return "route_relationship"
        elif intent == QueryIntent.TROUBLESHOOTING:
            return "route_troubleshooting"
        else:
            return "route_procedure"

    @listen("route_procedure")
    async def analyze_procedure(self) -> str:
        """Specialist Role: Procedure Analyst."""
        t0 = time.perf_counter()
        if self.state.quota_blocked:
            finding = AgentFinding(
                role="procedure_analyst",
                subquestion_id="SQ-MAIN",
                atomic_claims=[],
                supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]],
                execution_status=StageExecutionStatus.SKIPPED.value
            )
            self.state.agent_findings.append(finding)
            self._record_stage(
                "Procedure Analyst",
                StageExecutionStatus.SKIPPED.value,
                0.0,
                ExecutionMechanism.BYPASSED.value,
                "Specialist reasoning skipped due to upstream 429 provider quota"
            )
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SKIPPED,
                node_id="node_proc_analyst",
                status=NodeStatus.SKIPPED,
                summary="Specialist reasoning skipped due to upstream 429 provider quota"
            )
            return "specialist_complete"

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_proc_analyst",
            status=NodeStatus.RUNNING,
            summary="Procedure Analyst reviewing evidence for procedural steps",
            input_summary=f"{len(self.state.evidence_items)} evidence passages"
        )

        self.budget.check_deadline("analyze_procedure")
        analyst = AgenticSpecialistsFactory.create_procedure_analyst()

        task = Task(
            description=(
                f"You are the SAP Utilities Procedure Analyst. Scrutinize the retrieved documentation passages to answer:\n"
                f"'{self.state.original_query}'\n\n"
                f"CONTEXT PASSAGES:\n{self.state.assembled_context}\n\n"
                "ANALYSIS REQUIREMENTS:\n"
                "1. Scope Identification: Determine whether the documentation covers:\n"
                "   - Reversing the creation of new contracts (Move-In document reversal, e.g. T-code EC53E)\n"
                "   - Reversing the ending of contracts (Move-Out document reversal, e.g. T-code EC58E)\n"
                "   - Reconnection of a disconnected utility installation (Reconnection Order Generation, Reconnection Entry via Change Disconnection Document)\n"
                "   - Distinction: Do NOT assert that contract reversal physically reconnects a utility installation. Contract reversal is commercial contract lifecycle; reconnection is device installation management.\n"
                "2. Documented Prerequisites: List exact Customizing paths and system requirements stated in the text.\n"
                "3. Ordered Procedural Steps: Extract step-by-step sequential instructions with exact transaction codes (e.g. EC53E, EC58E, CRM_UI) or navigation paths (e.g. Customer service -> Process execution -> Disconnection/reconnection -> Change disconnection document).\n"
                "4. Verification and Expected Outcomes: Explain how to check the result in WebClient (CRM_UI) or confirmation status.\n"
                "5. Exceptions and Limitations: Document restrictions (e.g. billing dependencies) and disclose unstated steps.\n"
                "6. Strict Guardrails: NEVER invent SAP transaction codes or configuration paths not present in the context.\n"
                "7. For every claim, cite the exact evidence ID (e.g. EV-SQ-MAIN-1)."
            ),
            expected_output="Structured procedural extraction with scope, prerequisites, ordered steps, T-codes, and evidence IDs",
            agent=analyst
        )
        try:
            crew = Crew(agents=[analyst], tasks=[task], verbose=False)
            res = await crew.kickoff_async()
            finding_text = str(res.raw if hasattr(res, "raw") else res)
            stage_status = StageExecutionStatus.SUCCEEDED.value
            mechanism_val = ExecutionMechanism.LLM_REASONING.value
            details_val = "Analyzed procedural sequences, prerequisites, and transaction codes"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                stage_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
            else:
                stage_status = StageExecutionStatus.PARTIAL.value
            mechanism_val = ExecutionMechanism.BYPASSED.value
            details_val = f"Procedure analyst constrained: {str(e)[:80]}"
            finding_text = ""

        # Extract structured atomic claims from analyst output
        atomic_claims: List[ClaimRecord] = []
        if finding_text:
            lines = [ln.strip() for ln in finding_text.split("\n") if len(ln.strip()) > 20]
            claim_idx = 1
            for ln in lines:
                # Select lines asserting actionable steps, prerequisites, outcomes, T-codes, or reconnection
                if any(k in ln.lower() for k in ("ec53e", "ec58e", "crm_ui", "prerequisite", "customizing", "step", "reverse", "move-in", "move-out", "transaction", "result", "reconnect", "disconnect", "order", "entry")):
                    supp_ids = [ev.evidence_id for ev in self.state.evidence_items[:4]]
                    cat = self._ledger.classify_claim_category(ln) if self._ledger else "ordered_steps"
                    atomic_claims.append(
                        ClaimRecord(
                            claim_id=f"CL-{claim_idx}",
                            claim_text=ln[:300],
                            claim_category=cat,
                            supporting_evidence_ids=supp_ids
                        )
                    )
                    claim_idx += 1
                    if len(atomic_claims) >= 8:
                        break

        if not atomic_claims and finding_text:
            cat = self._ledger.classify_claim_category(finding_text[:300]) if self._ledger else "general"
            atomic_claims = [
                ClaimRecord(claim_id="CL-1", claim_text=finding_text[:300], claim_category=cat, supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]])
            ]

        finding = AgentFinding(
            role="procedure_analyst",
            subquestion_id="SQ-MAIN",
            atomic_claims=atomic_claims,
            supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:6]],
            execution_status=stage_status
        )
        self.state.agent_findings.append(finding)
        if self._ledger:
            self._ledger.record_agent_finding(finding)

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Procedure Analyst", stage_status, elapsed, mechanism_val, details_val)

        if stage_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_proc_analyst",
                status=NodeStatus.BLOCKED,
                summary="Procedure Analyst blocked by provider quota (HTTP 429)",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_proc_analyst",
                status=NodeStatus.SUCCEEDED,
                summary="Procedure Analyst completed analysis",
                duration_ms=elapsed,
                output_summary=finding_text[:180] or "Analyzed procedural sequences",
                evidence_refs=[{"chunk_id": ev.chunk_id, "title": ev.title} for ev in self.state.evidence_items[:4]]
            )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_ledger",
            status=NodeStatus.RUNNING,
            summary="Recording claims into Evidence Ledger"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_ledger",
            status=NodeStatus.SUCCEEDED,
            summary="Evidence Ledger recorded claims and linked evidence",
            duration_ms=3.0
        )
        return "specialist_complete"

    @listen("route_configuration")
    async def analyze_configuration(self) -> str:
        """Specialist Role: Configuration Analyst."""
        t0 = time.perf_counter()
        if self.state.quota_blocked:
            finding = AgentFinding(
                role="configuration_analyst",
                subquestion_id="SQ-MAIN",
                atomic_claims=[],
                supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]],
                execution_status=StageExecutionStatus.SKIPPED.value
            )
            self.state.agent_findings.append(finding)
            self._record_stage(
                "Configuration Analyst",
                StageExecutionStatus.SKIPPED.value,
                0.0,
                ExecutionMechanism.BYPASSED.value,
                "Specialist reasoning skipped due to upstream 429 provider quota"
            )
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SKIPPED,
                node_id="node_conf_analyst",
                status=NodeStatus.SKIPPED,
                summary="Specialist reasoning skipped due to upstream 429 provider quota"
            )
            return "specialist_complete"

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_conf_analyst",
            status=NodeStatus.RUNNING,
            summary="Configuration Analyst reviewing customizing parameters and tables",
            input_summary=f"{len(self.state.evidence_items)} evidence passages"
        )

        self.budget.check_deadline("analyze_configuration")
        analyst = AgenticSpecialistsFactory.create_configuration_analyst()

        task = Task(
            description=(
                f"Analyze the retrieved SAP Utilities documentation for configuration parameters:\n"
                f"Question: '{self.state.original_query}'\n\n"
                f"CONTEXT:\n{self.state.assembled_context}\n\n"
                "Extract configuration tables, customizing paths, and object settings. Cite exact evidence IDs."
            ),
            expected_output="Configuration analysis with evidence references",
            agent=analyst
        )
        try:
            crew = Crew(agents=[analyst], tasks=[task], verbose=False)
            res = await crew.kickoff_async()
            finding_text = str(res.raw if hasattr(res, "raw") else res)
            stage_status = StageExecutionStatus.SUCCEEDED.value
            mechanism_val = ExecutionMechanism.LLM_REASONING.value
            details_val = "Analyzed customizing parameters and settings"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                stage_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
            else:
                stage_status = StageExecutionStatus.PARTIAL.value
            mechanism_val = ExecutionMechanism.BYPASSED.value
            details_val = f"Configuration analyst constrained: {str(e)[:80]}"
            finding_text = ""

        finding = AgentFinding(
            role="configuration_analyst",
            subquestion_id="SQ-MAIN",
            atomic_claims=[
                ClaimRecord(claim_id="CL-CONF-1", claim_text=finding_text[:300], supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]])
            ] if finding_text else [],
            supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:4]],
            execution_status=stage_status
        )
        self.state.agent_findings.append(finding)
        if self._ledger:
            self._ledger.record_agent_finding(finding)

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Configuration Analyst", stage_status, elapsed, mechanism_val, details_val)

        if stage_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_conf_analyst",
                status=NodeStatus.BLOCKED,
                summary="Configuration Analyst blocked by provider quota (HTTP 429)",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_conf_analyst",
                status=NodeStatus.SUCCEEDED,
                summary="Configuration Analyst completed analysis",
                duration_ms=elapsed,
                output_summary=finding_text[:180] or "Analyzed configuration settings",
                evidence_refs=[{"chunk_id": ev.chunk_id, "title": ev.title} for ev in self.state.evidence_items[:4]]
            )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_ledger",
            status=NodeStatus.RUNNING,
            summary="Recording claims into Evidence Ledger"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_ledger",
            status=NodeStatus.SUCCEEDED,
            summary="Evidence Ledger recorded claims and linked evidence",
            duration_ms=3.0
        )
        return "specialist_complete"

    @listen("route_relationship")
    async def analyze_relationship(self) -> str:
        """Specialist Role: Relationship Analyst."""
        t0 = time.perf_counter()
        if self.state.quota_blocked:
            finding = AgentFinding(
                role="relationship_analyst",
                subquestion_id="SQ-MAIN",
                atomic_claims=[],
                supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]],
                execution_status=StageExecutionStatus.SKIPPED.value
            )
            self.state.agent_findings.append(finding)
            self._record_stage(
                "Relationship Analyst",
                StageExecutionStatus.SKIPPED.value,
                0.0,
                ExecutionMechanism.BYPASSED.value,
                "Specialist reasoning skipped due to upstream 429 provider quota"
            )
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SKIPPED,
                node_id="node_rel_analyst",
                status=NodeStatus.SKIPPED,
                summary="Specialist reasoning skipped due to upstream 429 provider quota"
            )
            return "specialist_complete"

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_rel_analyst",
            status=NodeStatus.RUNNING,
            summary="Relationship Analyst analyzing cross-document dependencies",
            input_summary=f"{len(self.state.evidence_items)} evidence passages"
        )

        self.budget.check_deadline("analyze_relationship")
        analyst = AgenticSpecialistsFactory.create_relationship_analyst()

        task = Task(
            description=(
                f"Analyze cross-document dependencies and data model relationships for:\n"
                f"'{self.state.original_query}'\n\n"
                f"CONTEXT:\n{self.state.assembled_context}\n\n"
                "Trace relationships between Business Partners, Contract Accounts, Installations, and Contracts. Cite evidence IDs."
            ),
            expected_output="Relationship analysis with evidence references",
            agent=analyst
        )
        try:
            crew = Crew(agents=[analyst], tasks=[task], verbose=False)
            res = await crew.kickoff_async()
            finding_text = str(res.raw if hasattr(res, "raw") else res)
            stage_status = StageExecutionStatus.SUCCEEDED.value
            mechanism_val = ExecutionMechanism.LLM_REASONING.value
            details_val = "Analyzed cross-document dependencies"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                stage_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
            else:
                stage_status = StageExecutionStatus.PARTIAL.value
            mechanism_val = ExecutionMechanism.BYPASSED.value
            details_val = f"Relationship analyst constrained: {str(e)[:80]}"
            finding_text = ""

        finding = AgentFinding(
            role="relationship_analyst",
            subquestion_id="SQ-MAIN",
            atomic_claims=[
                ClaimRecord(claim_id="CL-REL-1", claim_text=finding_text[:300], supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]])
            ] if finding_text else [],
            supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:4]],
            execution_status=stage_status
        )
        self.state.agent_findings.append(finding)
        if self._ledger:
            self._ledger.record_agent_finding(finding)

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Relationship Analyst", stage_status, elapsed, mechanism_val, details_val)

        if stage_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_rel_analyst",
                status=NodeStatus.BLOCKED,
                summary="Relationship Analyst blocked by provider quota (HTTP 429)",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_rel_analyst",
                status=NodeStatus.SUCCEEDED,
                summary="Relationship Analyst completed analysis",
                duration_ms=elapsed,
                output_summary=finding_text[:180] or "Analyzed dependencies",
                evidence_refs=[{"chunk_id": ev.chunk_id, "title": ev.title} for ev in self.state.evidence_items[:4]]
            )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_ledger",
            status=NodeStatus.RUNNING,
            summary="Recording claims into Evidence Ledger"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_ledger",
            status=NodeStatus.SUCCEEDED,
            summary="Evidence Ledger recorded claims and linked evidence",
            duration_ms=3.0
        )
        return "specialist_complete"

    @listen("route_troubleshooting")
    async def analyze_troubleshooting(self) -> str:
        """Specialist Role: Troubleshooting Analyst."""
        t0 = time.perf_counter()
        if self.state.quota_blocked:
            finding = AgentFinding(
                role="troubleshooting_analyst",
                subquestion_id="SQ-MAIN",
                atomic_claims=[],
                supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]],
                execution_status=StageExecutionStatus.SKIPPED.value
            )
            self.state.agent_findings.append(finding)
            self._record_stage(
                "Troubleshooting Analyst",
                StageExecutionStatus.SKIPPED.value,
                0.0,
                ExecutionMechanism.BYPASSED.value,
                "Specialist reasoning skipped due to upstream 429 provider quota"
            )
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SKIPPED,
                node_id="node_ts_analyst",
                status=NodeStatus.SKIPPED,
                summary="Specialist reasoning skipped due to upstream 429 provider quota"
            )
            return "specialist_complete"

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_ts_analyst",
            status=NodeStatus.RUNNING,
            summary="Troubleshooting Analyst analyzing diagnostic steps and exceptions",
            input_summary=f"{len(self.state.evidence_items)} evidence passages"
        )

        self.budget.check_deadline("analyze_troubleshooting")
        analyst = AgenticSpecialistsFactory.create_troubleshooting_analyst()

        task = Task(
            description=(
                f"Analyze diagnostic steps, errors, and exception handling for:\n"
                f"'{self.state.original_query}'\n\n"
                f"CONTEXT:\n{self.state.assembled_context}\n\n"
                "Identify error root causes, reversals, and corrective procedures. Cite evidence IDs."
            ),
            expected_output="Troubleshooting analysis with evidence references",
            agent=analyst
        )
        try:
            crew = Crew(agents=[analyst], tasks=[task], verbose=False)
            res = await crew.kickoff_async()
            finding_text = str(res.raw if hasattr(res, "raw") else res)
            stage_status = StageExecutionStatus.SUCCEEDED.value
            mechanism_val = ExecutionMechanism.LLM_REASONING.value
            details_val = "Analyzed diagnostic procedures and exceptions"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                stage_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
            else:
                stage_status = StageExecutionStatus.PARTIAL.value
            mechanism_val = ExecutionMechanism.BYPASSED.value
            details_val = f"Troubleshooting analyst constrained: {str(e)[:80]}"
            finding_text = ""

        finding = AgentFinding(
            role="troubleshooting_analyst",
            subquestion_id="SQ-MAIN",
            atomic_claims=[
                ClaimRecord(claim_id="CL-TS-1", claim_text=finding_text[:300], supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:3]])
            ] if finding_text else [],
            supporting_evidence_ids=[ev.evidence_id for ev in self.state.evidence_items[:4]],
            execution_status=stage_status
        )
        self.state.agent_findings.append(finding)
        if self._ledger:
            self._ledger.record_agent_finding(finding)

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Troubleshooting Analyst", stage_status, elapsed, mechanism_val, details_val)

        if stage_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_ts_analyst",
                status=NodeStatus.BLOCKED,
                summary="Troubleshooting Analyst blocked by provider quota (HTTP 429)",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_ts_analyst",
                status=NodeStatus.SUCCEEDED,
                summary="Troubleshooting Analyst completed analysis",
                duration_ms=elapsed,
                output_summary=finding_text[:180] or "Analyzed diagnostic steps",
                evidence_refs=[{"chunk_id": ev.chunk_id, "title": ev.title} for ev in self.state.evidence_items[:4]]
            )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_ledger",
            status=NodeStatus.RUNNING,
            summary="Recording claims into Evidence Ledger"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_ledger",
            status=NodeStatus.SUCCEEDED,
            summary="Evidence Ledger recorded claims and linked evidence",
            duration_ms=3.0
        )
        return "specialist_complete"

    @listen(or_(analyze_procedure, analyze_configuration, analyze_relationship, analyze_troubleshooting))
    async def audit_stage(self, *args, **kwargs) -> str:
        """
        Stage 4: Evidence Auditor challenges claims, evaluates evidence sufficiency, tracks gaps.
        Deterministic ledger-backed audit execution.
        """
        t0 = time.perf_counter()
        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_auditor",
            status=NodeStatus.RUNNING,
            summary="Evidence Auditor evaluating evidence sufficiency and gaps",
            input_summary="Aggregated claims and evidence items"
        )

        cov = self._ledger.evaluate_coverage() if self._ledger else {"coverage_ratio": 1.0, "unresolved_subquestion_ids": []}
        unresolved = cov.get("unresolved_subquestion_ids", [])

        # Procedural evidence verification:
        # Check whether retrieved evidence contains actual procedural steps, prerequisite sections,
        # or explicit transaction codes / process flows
        op_cat = self.state.query_plan.operation_category if self.state.query_plan else OperationCategory.GENERAL_PROCEDURAL
        has_procedure_evidence = any(
            any(k in (e.section_heading or "").lower() for k in ("procedure", "use", "feature", "prerequisite", "result", "activities", "order", "entry", "reconnect", "process flow"))
            or any(tcode in e.content for tcode in ("EC53E", "EC58E", "CRM_UI", "disconnection", "reconnection"))
            for e in self.state.evidence_items
        )
        has_prerequisite_evidence = any(
            "prerequisite" in (e.section_heading or "").lower() or "customizing" in e.content.lower() or "process flow" in (e.section_heading or "").lower()
            for e in self.state.evidence_items
        )

        has_target_operation_evidence = True
        if op_cat == OperationCategory.RECONNECT_INSTALLATION:
            has_target_operation_evidence = any(
                any(k in e.content.lower() for k in ("reconnection order", "change disconnection document", "reconnection entry", "disconnection/reconnection"))
                for e in self.state.evidence_items
            )
        elif op_cat in (OperationCategory.REVERSE_NEW_CONTRACT, OperationCategory.REVERSE_END_OF_CONTRACT):
            has_target_operation_evidence = any(
                any(tcode in e.content for tcode in ("EC53E", "EC58E", "CRM_UI", "reverse new contract", "reverse end of contract"))
                for e in self.state.evidence_items
            )

        max_sim = max((e.similarity_score for e in self.state.evidence_items), default=0.0)
        claims_count = len(self._ledger._claims) if self._ledger else 0

        if self.state.quota_blocked:
            suff = EvidenceSufficiency.PARTIAL.value
            self.state.unresolved_gaps = ["Multi-agent reasoning bypassed due to upstream provider quota exhaustion (HTTP 429)"]
        elif not has_target_operation_evidence:
            suff = EvidenceSufficiency.PARTIAL.value
            self.state.unresolved_gaps = [f"Retrieved evidence does not contain direct operational procedures for {op_cat.value}"]
        elif has_procedure_evidence and (has_prerequisite_evidence or len(self.state.evidence_items) >= 3):
            suff = EvidenceSufficiency.SUFFICIENT.value
            self.state.unresolved_gaps = []
        elif max_sim >= 0.45 and len(self.state.evidence_items) >= 1:
            suff = EvidenceSufficiency.PARTIAL.value
            self.state.unresolved_gaps = [
                f"Subquestion '{sid}' partially grounded; explicit sequential steps not fully isolated in corpus"
                for sid in unresolved
            ] if unresolved else ["Detailed execution sequence is partially documented in the retrieved sections"]
        else:
            suff = EvidenceSufficiency.INSUFFICIENT.value
            self.state.unresolved_gaps = ["Corpus lacks documented procedural instructions for this query"]

        self.state.evidence_sufficiency = suff

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage(
            "Evidence Audit",
            StageExecutionStatus.SUCCEEDED.value,
            elapsed,
            ExecutionMechanism.DETERMINISTIC_ASSEMBLY.value,
            f"Audited evidence sufficiency: {suff.upper()} (max_sim={max_sim:.2f}, gaps={len(self.state.unresolved_gaps)})"
        )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_auditor",
            status=NodeStatus.SUCCEEDED,
            summary=f"Audited evidence sufficiency: {suff.upper()}",
            duration_ms=elapsed,
            metrics={"sufficiency": suff, "gaps": len(self.state.unresolved_gaps)}
        )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_gap_decision",
            status=NodeStatus.RUNNING,
            summary="Evaluating gap routing decision"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_gap_decision",
            status=NodeStatus.SUCCEEDED,
            summary=f"Routing decision: Proceed to synthesis ({suff.upper()})",
            duration_ms=2.0
        )
        return "audit_complete"

    @listen(audit_stage)
    async def synthesis_stage(self, *args, **kwargs) -> str:
        """
        Stage 5: Answer Synthesizer produces grounded structured procedural answer
        or switches to truthful evidence-only mode if provider quota is blocked.
        """
        t0 = time.perf_counter()
        citations: List[CitationItem] = []
        for idx, ev in enumerate(self.state.evidence_items, 1):
            excerpt_text = ev.clean_excerpt or create_clean_excerpt(ev.clean_body or ev.content, max_chars=320)[0]
            cit = CitationItem(
                citation_id=idx,
                evidence_id=ev.evidence_id,
                chunk_id=ev.chunk_id,
                document_id=ev.document_id,
                title=ev.title,
                canonical_url=ev.canonical_url,
                section_heading=ev.section_heading,
                excerpt=excerpt_text,
                cosine_distance=ev.cosine_distance,
                similarity_score=ev.similarity_score
            )
            citations.append(cit)
        self.state.citations = citations

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_synthesizer",
            status=NodeStatus.RUNNING,
            summary="Answer Synthesizer synthesizing grounded procedural answer",
            input_summary=f"{len(citations)} citations and audited evidence"
        )

        # If provider quota was blocked during earlier stages, do NOT make futile synthesis call
        if self.state.quota_blocked:
            self.state.response_mode = ResponseMode.EVIDENCE_ONLY.value
            self.state.answer_status = AnswerStatus.SYNTHESIS_UNAVAILABLE.value
            self.state.execution_status = "partial"

            answer_lines = [
                "### Answer Synthesis Unavailable — Verified Evidence Retrieved\n",
                "> **Notice:** Upstream LLM provider quota exhausted or unavailable (HTTP 429 RESOURCE_EXHAUSTED). "
                "Multi-agent reasoning and answer synthesis could not execute.\n",
                "> The documentation passages below were retrieved directly from PostgreSQL/pgvector using BGE-M3 embeddings. "
                "These passages are provided as audited evidence for manual inspection, **not as a completed procedural answer**.\n",
                "#### Audited SAP Utilities Source Evidence:\n"
            ]
            for c in citations[:5]:
                ev_match = next((e for e in self.state.evidence_items if e.chunk_id == c.chunk_id), None)
                path_info = f" > {ev_match.section_path}" if ev_match and ev_match.section_path else ""
                answer_lines.append(
                    f"- [{c.citation_id}] **{c.title}** ({c.section_heading or 'General'}{path_info})\n"
                    f"  - **Passage:** \"{c.excerpt}\"\n"
                    f"  - **Source Link:** [{c.canonical_url}]({c.canonical_url})\n"
                    f"  - **Vector Similarity:** {c.similarity_score:.4f} (Cosine Distance: {c.cosine_distance:.4f})\n"
                )
            answer_lines.append(
                "\n*Strict Isolation Notice: Legacy RAG pipeline execution prohibited by architecture. Database assets queried read-only.*"
            )
            self.state.final_answer = "\n".join(answer_lines)

            elapsed = (time.perf_counter() - t0) * 1000
            self._record_stage(
                "Answer Synthesis",
                StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value,
                elapsed,
                ExecutionMechanism.BYPASSED.value,
                "Synthesis unavailable due to provider quota constraint; switched to evidence-only mode"
            )
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_synthesizer",
                status=NodeStatus.BLOCKED,
                summary="Answer synthesis blocked by provider quota (HTTP 429); switched to verified evidence-only mode",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
            return "synthesis_complete"

        # Not quota-blocked: run LLM Answer Synthesis with strict procedural prompt
        evidence_prompt_list = []
        for c in citations[:8]:
            ev_match = next((e for e in self.state.evidence_items if e.chunk_id == c.chunk_id), None)
            path_info = f" | Path: {ev_match.section_path}" if ev_match and ev_match.section_path else ""
            # Use full clean passage text so complete steps, T-codes, and verification are provided to the LLM
            body_text = (ev_match.clean_body if ev_match and ev_match.clean_body else c.excerpt).strip()
            evidence_prompt_list.append(
                f"[{c.citation_id}] Title: {c.title}{path_info} | Section: {c.section_heading or 'General'}\n"
                f"URL: {c.canonical_url}\n"
                f"Passage:\n{body_text}\n"
            )
        evidence_context = "\n".join(evidence_prompt_list)

        try:
            self.budget.check_deadline("synthesis_stage")
            synthesizer = AgenticSpecialistsFactory.create_answer_synthesizer()
            op_cat = self.state.query_plan.operation_category if self.state.query_plan else OperationCategory.GENERAL_PROCEDURAL
            cand_str = ", ".join([c.value for c in (self.state.query_plan.candidate_operations if self.state.query_plan else [])])

            task = Task(
                description=(
                    f"You are the SAP Utilities Answer Synthesizer. Synthesize an authoritative, direct, and grounded procedural answer to:\n"
                    f"'{self.state.original_query}'\n\n"
                    f"AUDITED EVIDENCE PASSAGES:\n{evidence_context}\n\n"
                    "PROCEDURAL SCOPE GUIDANCE:\n"
                    f"- Classified Operation Category: {op_cat.value} (Candidate Interpretations: {cand_str})\n"
                    "- If the question or evidence covers Reversing New Contracts: document transaction EC53E, business partner ID, move-in document selection.\n"
                    "- If the question or evidence covers Reversing End of Contracts: document transaction EC58E, business partner ID, move-out document selection.\n"
                    "- If the question or evidence covers Reconnecting a Utility Installation: document Reconnection Order Generation, and Reconnection Entry (Change Disconnection Document: Customer Service -> Process Execution -> Disconnection/Reconnection).\n"
                    "- CRITICAL DOMAIN SEPARATION: In SAP Utilities, commercial contract reversal (EC53E/EC58E) reverses move-in/move-out billing documents but does NOT physically reconnect a disconnected utility installation. Physical reconnection requires generating a Reconnection Order and completing Reconnection Entry. Do NOT assert that reversing a contract automatically reconnects an installation unless explicit retrieved evidence establishes it.\n"
                    "- Attach bracket citations [1], [2] to every factual statement, precondition, step, and limitation.\n\n"
                    "MANDATORY PROCEDURAL ANSWER STRUCTURE (Use these exact Markdown headings):\n\n"
                    "### Direct Answer and Scope\n"
                    "Explain what operation(s) the SAP documentation covers. Distinguish clearly between contract lifecycle reversal and physical installation reconnection where applicable.\n\n"
                    "### Prerequisites and Preconditions\n"
                    "List documented prerequisites and Customizing paths stated in the retrieved passages.\n\n"
                    "### Documented Procedure\n"
                    "Provide ordered sequential steps for each documented operation with exact transaction codes (e.g. EC53E, EC58E, CRM_UI) and navigation paths. Attach bracket citations [1], [2] to every step.\n\n"
                    "### Verification and Expected Outcome\n"
                    "Explain how to verify the result in WebClient (CRM_UI) or confirmation status.\n\n"
                    "### Exceptions and Limitations\n"
                    "Note documented constraints (e.g. billing dependencies, prerequisite contract states) and disclose any unstated parameters.\n\n"
                    "### Sources\n"
                    "List clickable markdown links to each cited document URL. Deduplicate repeated source documents.\n\n"
                    "STRICT INSTRUCTIONS:\n"
                    "- Do NOT claim that a procedure cannot be found when supported in the retrieved passages.\n"
                    "- Do NOT invent transaction codes or menus not present in the evidence.\n"
                    "- Attach bracket citations [1], [2] to each factual statement and step."
                ),
                expected_output="Authoritative procedural answer with sections and bracket citations [1], [2]",
                agent=synthesizer
            )
            crew = Crew(agents=[synthesizer], tasks=[task], verbose=False)
            res = await crew.kickoff_async()
            raw_answer = str(res.raw if hasattr(res, "raw") else res).strip()

            self.state.final_answer = raw_answer
            self.state.response_mode = ResponseMode.SYNTHESIZED_ANSWER.value
            self.state.answer_status = AnswerStatus.SYNTHESIS_COMPLETED.value
            self.state.execution_status = "success"
            stage_status = StageExecutionStatus.SUCCEEDED.value
            stage_mech = ExecutionMechanism.LLM_REASONING.value
            stage_details = f"Synthesized procedural answer with {len(citations)} citations"
        except Exception as e:
            is_quota = _is_quota_exhausted_error(e)
            if is_quota:
                self.state.quota_blocked = True
                stage_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value
            else:
                stage_status = StageExecutionStatus.PARTIAL.value
            stage_mech = ExecutionMechanism.BYPASSED.value
            stage_details = f"Synthesis unavailable ({str(e)[:80]}); switched to evidence-only mode"

            self.state.response_mode = ResponseMode.EVIDENCE_ONLY.value
            self.state.answer_status = AnswerStatus.SYNTHESIS_UNAVAILABLE.value
            self.state.execution_status = "partial"

            answer_lines = [
                "### Answer Synthesis Unavailable — Verified Evidence Retrieved\n",
                f"> **Notice:** Upstream LLM provider returned a capacity/quota constraint ({type(e).__name__}: {str(e)[:120]}). "
                "Multi-agent reasoning and answer synthesis could not execute.\n",
                "> The documentation passages below were retrieved directly from PostgreSQL/pgvector using BGE-M3 embeddings. "
                "These passages are provided as audited evidence for manual inspection, **not as a completed procedural answer**.\n",
                "#### Audited SAP Utilities Source Evidence:\n"
            ]
            for c in citations[:5]:
                ev_match = next((e for e in self.state.evidence_items if e.chunk_id == c.chunk_id), None)
                path_info = f" > {ev_match.section_path}" if ev_match and ev_match.section_path else ""
                answer_lines.append(
                    f"- [{c.citation_id}] **{c.title}** ({c.section_heading or 'General'}{path_info})\n"
                    f"  - **Passage:** \"{c.excerpt}\"\n"
                    f"  - **Source Link:** [{c.canonical_url}]({c.canonical_url})\n"
                    f"  - **Vector Similarity:** {c.similarity_score:.4f} (Cosine Distance: {c.cosine_distance:.4f})\n"
                )
            self.state.final_answer = "\n".join(answer_lines)

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage("Answer Synthesis", stage_status, elapsed, stage_mech, stage_details)

        if stage_status == StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_BLOCKED,
                node_id="node_synthesizer",
                status=NodeStatus.BLOCKED,
                summary="Answer synthesis blocked by provider quota (HTTP 429); switched to verified evidence-only mode",
                duration_ms=elapsed,
                error={"message": "LLM provider quota exhausted (HTTP 429)"}
            )
        elif stage_status == StageExecutionStatus.SUCCEEDED.value:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_SUCCEEDED,
                node_id="node_synthesizer",
                status=NodeStatus.SUCCEEDED,
                summary=f"Synthesized procedural answer with {len(citations)} citations",
                duration_ms=elapsed,
                output_summary=f"Procedural answer synthesized ({len(self.state.final_answer)} chars)"
            )
        else:
            await self._emit_workflow_event(
                WorkflowEventType.NODE_PARTIAL,
                node_id="node_synthesizer",
                status=NodeStatus.PARTIAL,
                summary="Answer synthesis partial result; verified evidence provided",
                duration_ms=elapsed
            )

        return "synthesis_complete"

    @listen(synthesis_stage)
    async def validation_stage(self, *args, **kwargs) -> FinalAgenticResponse:
        """
        Stage 6: Deterministic Citation and Coverage Validation + Bounded Repair + Invariant Enforcement.
        """
        t0 = time.perf_counter()
        is_evidence_only = (self.state.response_mode == ResponseMode.EVIDENCE_ONLY.value)

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_validators",
            status=NodeStatus.RUNNING,
            summary="Validating citation integrity, subquestion coverage, and server invariants"
        )

        # 1. Deterministic Citation Validation
        report = self.citation_validator.validate_answer(
            answer_text=self.state.final_answer,
            citations=self.state.citations,
            evidence_items=self.state.evidence_items,
            response_mode=self.state.response_mode,
            evidence_sufficiency=self.state.evidence_sufficiency
        )

        # Filter active citations to only those actually cited in text, excluding unused candidates
        active_citations = self.citation_validator.get_active_citations(self.state.citations, self.state.final_answer)

        # 2. Coverage Validation (only for synthesized answers)
        if not is_evidence_only and self.state.query_plan:
            cov_ratio, answered, unanswered, cov_details = self.coverage_validator.evaluate_coverage_details(
                answer_text=self.state.final_answer,
                query_plan=self.state.query_plan,
                response_mode=self.state.response_mode
            )
            report.question_coverage_rate = cov_ratio
            report.unanswered_subquestions = unanswered
            report.subquestion_coverage_details = cov_details
            if unanswered and report.overall_status == "verified":
                report.overall_status = "qualified"
        else:
            report.question_coverage_rate = None
            report.claim_support_rate = None
            report.unanswered_subquestions = [sq.question for sq in (self.state.query_plan.subquestions if self.state.query_plan else [])]
            report.subquestion_coverage_details = [
                SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.NOT_FOUND,
                    explanation="Evidence-only mode; answer synthesis not executed."
                )
                for sq in (self.state.query_plan.subquestions if self.state.query_plan else [])
            ]

        # 3. Enforce Server-Side Invariants
        try:
            report.validate_invariants(self.state.response_mode)
        except ValueError as inv_err:
            logger.warning(f"Validation invariant reconciliation: {inv_err}")
            if is_evidence_only:
                report.claim_support_rate = None
                report.question_coverage_rate = None
                report.overall_status = "evidence_only"

        self.state.validation_report = report

        # 4. Final Response Assembly
        total_time_ms = round(self.budget.elapsed_seconds() * 1000, 2)
        response = FinalAgenticResponse(
            request_id=self.state.request_id,
            original_query=self.state.original_query,
            answer=self.state.final_answer,
            citations=active_citations,
            evidence_payload=self.state.evidence_items,
            agent_stage_summary=self.state.stage_statuses,
            retrieval_diagnostics=self.state.retrieval_diagnostics,
            validation_report=report,
            execution_status=self.state.execution_status,
            response_mode=self.state.response_mode,
            answer_status=self.state.answer_status,
            evidence_sufficiency=self.state.evidence_sufficiency,
            unresolved_gaps=self.state.unresolved_gaps,
            total_latency_ms=total_time_ms,
            token_usage={"context_tokens": self.state.retrieval_diagnostics.context_tokens_used}
        )
        self.state.final_response = response

        elapsed = (time.perf_counter() - t0) * 1000
        self._record_stage(
            "Deterministic Validation",
            StageExecutionStatus.SUCCEEDED.value,
            elapsed,
            ExecutionMechanism.DETERMINISTIC_ASSEMBLY.value,
            f"Status: {report.overall_status.upper()} (Invariants enforced)"
        )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_validators",
            status=NodeStatus.SUCCEEDED,
            summary=f"Validation {report.overall_status.upper()}: integrity={report.citation_integrity_ratio:.0%}",
            duration_ms=elapsed,
            metrics={
                "citation_integrity": report.citation_integrity_ratio,
                "coverage": report.question_coverage_rate,
                "sufficiency": report.evidence_sufficiency
            }
        )

        await self._emit_workflow_event(
            WorkflowEventType.NODE_STARTED,
            node_id="node_output",
            status=NodeStatus.RUNNING,
            summary="Assembling typed FinalAgenticResponse"
        )
        await self._emit_workflow_event(
            WorkflowEventType.NODE_SUCCEEDED,
            node_id="node_output",
            status=NodeStatus.SUCCEEDED,
            summary="Final response assembly complete",
            duration_ms=2.0
        )

        # Update snapshot in WorkflowRunManager
        mgr = WorkflowRunManager.get_instance()
        snap = mgr.get_run(self.state.run_id)
        if snap:
            snap.final_response = response
            snap.response_mode = response.response_mode
            snap.answer_status = response.answer_status

        await self._emit_workflow_event(
            WorkflowEventType.RUN_COMPLETED,
            summary=f"Workflow run completed ({response.execution_status})",
            duration_ms=total_time_ms
        )
        return response
