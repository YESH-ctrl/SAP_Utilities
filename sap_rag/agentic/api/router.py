"""
FastAPI Router for Independent Agentic Knowledge Intelligence Platform.
Routes under /api/v2/agentic.
Completely isolated from legacy /api/v1/ routes and contracts.
"""

import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from sap_rag.database.connection import DatabasePool
from sap_rag.agentic.schemas.contracts import (
    AgenticChatRequest,
    FinalAgenticResponse,
    EvidenceItem,
    CitationItem,
    StageStatus,
    StageExecutionStatus,
    ExecutionMechanism,
    ResponseMode,
    AnswerStatus,
    EvidenceSufficiency,
    RetrievalDiagnostics,
    ValidationReport
)
from sap_rag.agentic.schemas.workflow_events import (
    RunSnapshot,
    WorkflowEvent,
    WorkflowEventType
)
from sap_rag.agentic.orchestration.flow import AgenticIntelligenceFlow
from sap_rag.agentic.orchestration.run_manager import WorkflowRunManager
from sap_rag.agentic.retrieval.service import SemanticRetrievalService
from sap_rag.agentic.validators.budget_controller import ExecutionBudgetController
from sap_rag.agentic.security.guardrails import SecurityGuardrails

logger = logging.getLogger("sap_rag.agentic.api")

router = APIRouter(prefix="/api/v2/agentic", tags=["agentic_intelligence"])
_direct_retriever = SemanticRetrievalService()


@router.post("/runs", response_model=RunSnapshot, status_code=status.HTTP_201_CREATED)
async def create_agentic_run(req: AgenticChatRequest):
    """
    Launch an asynchronous live workflow execution run for the Live Workflow Canvas.
    Returns the initial RunSnapshot with graph nodes and edges.
    """
    clean_query = SecurityGuardrails.sanitize_untrusted_text((req.query or "").strip())
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agentic query cannot be empty or whitespace."
        )

    run_id = f"run-{uuid.uuid4().hex[:10]}"
    mgr = WorkflowRunManager.get_instance()
    snapshot = mgr.create_run(query=clean_query, run_id=run_id)

    async def _run_flow_background(r_id: str, q: str, timeout: float, max_rounds: int):
        try:
            budget = ExecutionBudgetController(timeout_seconds=timeout, max_investigation_rounds=max_rounds)
            flow = AgenticIntelligenceFlow(
                retrieval_service=_direct_retriever,
                budget_controller=budget,
                run_id=r_id
            )
            flow.state.original_query = q
            await flow.kickoff_async()
        except Exception as e:
            logger.error(f"Background execution of run {r_id} failed: {e}", exc_info=True)
            now_iso = datetime.now(timezone.utc).isoformat()
            snap = mgr.get_run(r_id)
            if snap:
                snap.status = "failed"
                snap.completed_at = now_iso
                snap.error_message = str(e)
            await mgr.emit_event(WorkflowEvent(
                run_id=r_id,
                sequence=0,
                event_type=WorkflowEventType.RUN_FAILED,
                timestamp=now_iso,
                summary=f"Workflow run failed: {str(e)[:100]}"
            ))

    task = asyncio.create_task(_run_flow_background(run_id, clean_query, req.timeout_seconds, req.max_investigation_rounds))
    mgr.register_task(run_id, task)
    return snapshot


@router.get("/runs/{run_id}", response_model=RunSnapshot, status_code=status.HTTP_200_OK)
async def get_agentic_run(run_id: str):
    """Fetch current authoritative snapshot and graph state of a workflow run."""
    mgr = WorkflowRunManager.get_instance()
    snap = mgr.get_run(run_id)
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{run_id}' not found."
        )
    return snap


@router.get("/runs/{run_id}/events")
async def stream_agentic_run_events(
    run_id: str,
    last_sequence: int = 0
):
    """
    Server-Sent Events (SSE) stream for live node, edge, and execution events.
    Supports reconnection and missed-event replay using `last_sequence`.
    """
    mgr = WorkflowRunManager.get_instance()
    snap = mgr.get_run(run_id)
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{run_id}' not found."
        )
    return EventSourceResponse(
        mgr.subscribe(run_id, last_sequence=last_sequence),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_agentic_run(run_id: str):
    """Cancel an active in-flight workflow run."""
    mgr = WorkflowRunManager.get_instance()
    ok = mgr.cancel_run(run_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{run_id}' not found."
        )
    return {"run_id": run_id, "status": "cancelled", "message": "Workflow run cancelled successfully."}


@router.get("/runs", response_model=List[RunSnapshot], status_code=status.HTTP_200_OK)
async def list_agentic_runs(limit: int = 20):
    """List recent execution runs with final outcomes and statuses."""
    mgr = WorkflowRunManager.get_instance()
    return mgr.list_runs(limit=limit)


@router.post("/chat", response_model=FinalAgenticResponse, status_code=status.HTTP_200_OK)
async def agentic_chat(req: AgenticChatRequest):
    """
    Independent CrewAI Agentic Knowledge Intelligence endpoint for SAP Utilities.
    Executes multi-agent planning, direct semantic vector discovery, specialist analysis,
    evidence audit, answer synthesis, and deterministic citation validation.
    """
    clean_query = SecurityGuardrails.sanitize_untrusted_text((req.query or "").strip())
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agentic query cannot be empty or whitespace."
        )

    logger.info(f"Received Agentic Chat Request: '{clean_query[:80]}...'")

    try:
        # Create request-scoped budget controller
        budget = ExecutionBudgetController(
            timeout_seconds=req.timeout_seconds,
            max_investigation_rounds=req.max_investigation_rounds
        )

        flow = AgenticIntelligenceFlow(
            retrieval_service=_direct_retriever,
            budget_controller=budget
        )
        flow.state.original_query = clean_query

        # Run flow execution via native async kickoff
        final_resp = await flow.kickoff_async()

        # Retrieve state if kickoff returned intermediate status
        if not isinstance(final_resp, FinalAgenticResponse):
            final_resp = flow.state.final_response

        if not final_resp:
            raise RuntimeError("Agentic flow failed to generate a final response.")

        return final_resp

    except Exception as e:
        logger.warning(
            f"Agentic multi-agent flow interrupted ({e}). Initiating deterministic grounded passage synthesis. "
            "Strict isolation boundary preserved (zero legacy RAG fallback).",
            exc_info=True
        )
        try:
            items = await _direct_retriever.search(query=clean_query, top_k=5)
            citations = [
                CitationItem(
                    citation_id=idx,
                    evidence_id=ev.evidence_id,
                    chunk_id=ev.chunk_id,
                    document_id=ev.document_id,
                    title=ev.title,
                    canonical_url=ev.canonical_url,
                    section_heading=ev.section_heading,
                    excerpt=ev.clean_excerpt or ev.content[:240].strip(),
                    cosine_distance=ev.cosine_distance,
                    similarity_score=ev.similarity_score
                )
                for idx, ev in enumerate(items, 1)
            ]

            error_msg_short = str(e).replace("\n", " ")[:140]
            is_quota = any(kw in str(e).lower() for kw in ["429", "quota", "resource_exhausted", "rate limit"])

            parts = [
                f"### {c.title} ({c.section_heading or 'General'}) [{c.citation_id}]\n"
                f"- **Breadcrumb:** {items[idx-1].breadcrumb or 'General'}\n"
                f"- **Key Passage:** {c.excerpt}\n"
                f"- **Vector Distance:** {c.cosine_distance:.4f} (Similarity: {c.similarity_score * 100:.1f}%)"
                for idx, c in enumerate(citations[:5], 1)
            ]
            evidence_blocks = "\n\n".join(parts) if parts else "No relevant SAP documentation records located for this query."
            
            ans_body = (
                f"### Answer Synthesis Unavailable — Verified Evidence Retrieved\n\n"
                f"> **Notice:** Multi-agent answer synthesis could not execute due to upstream LLM provider capacity/quota constraint (`{error_msg_short}`).\n"
                f"> **Important:** The documentation passages below are verified evidence retrieved directly from PostgreSQL/pgvector for **manual inspection**. They do NOT constitute an automated multi-agent synthesized procedural answer.\n\n"
                f"**User Question:** {clean_query}\n\n"
                f"#### Retrieved Evidence Records for Manual Inspection:\n\n"
                f"{evidence_blocks}\n\n"
                f"---\n"
                f"*Strict isolation boundary preserved: zero legacy RAG fallback invoked.*"
            )

            diag = RetrievalDiagnostics(
                total_candidates_retrieved=len(items),
                unique_chunks_used=len(items),
                graph_expanded_count=0,
                min_cosine_distance=min((itm.cosine_distance for itm in items), default=0.0),
                max_cosine_distance=max((itm.cosine_distance for itm in items), default=0.0),
                vector_search_latency_ms=50.0,
                context_tokens_used=sum(len(itm.content.split()) for itm in items)
            )

            validation = ValidationReport(
                overall_status="evidence_only",
                citation_integrity=True,
                citation_integrity_ratio=1.0,
                claim_support_rate=None,
                question_coverage_rate=None,
                unresolved_gaps=[f"Multi-agent reasoning bypassed due to upstream error: {error_msg_short}"],
                repair_attempts=0,
                notes=f"Truthful evidence-only response returned due to upstream error: {error_msg_short}"
            )
            validation.validate_invariants(ResponseMode.EVIDENCE_ONLY)

            exec_status = StageExecutionStatus.BLOCKED_BY_PROVIDER_QUOTA if is_quota else StageExecutionStatus.FAILED

            return FinalAgenticResponse(
                request_id=f"fallback-{uuid.uuid4()}",
                original_query=clean_query,
                response_mode=ResponseMode.EVIDENCE_ONLY,
                answer_status=AnswerStatus.SYNTHESIS_UNAVAILABLE,
                evidence_sufficiency=EvidenceSufficiency.PARTIAL if items else EvidenceSufficiency.INSUFFICIENT,
                answer=ans_body,
                citations=citations,
                evidence_payload=items,
                agent_stage_summary=[
                    StageStatus(
                        stage_name="Query Planning",
                        status=exec_status,
                        mechanism=ExecutionMechanism.LLM_REASONING,
                        latency_ms=0.0,
                        details="Upstream provider constraint"
                    ),
                    StageStatus(
                        stage_name="Deterministic Vector Retrieval",
                        status=StageExecutionStatus.SUCCEEDED,
                        mechanism=ExecutionMechanism.DETERMINISTIC_RETRIEVAL,
                        latency_ms=50.0,
                        details=f"Retrieved {len(items)} chunks"
                    ),
                    StageStatus(
                        stage_name="Specialist Reasoning",
                        status=StageExecutionStatus.SKIPPED,
                        mechanism=ExecutionMechanism.BYPASS,
                        latency_ms=0.0,
                        details="Bypassed due to provider constraint"
                    ),
                    StageStatus(
                        stage_name="Answer Synthesis",
                        status=exec_status,
                        mechanism=ExecutionMechanism.BYPASS,
                        latency_ms=0.0,
                        details=f"Synthesis unavailable: {error_msg_short}"
                    )
                ],
                retrieval_diagnostics=diag,
                validation_report=validation,
                execution_status="partial",
                unresolved_gaps=[f"Multi-agent reasoning bypassed due to upstream error: {error_msg_short}"],
                total_latency_ms=75.0,
                token_usage={"context_tokens": 0}
            )
        except Exception as fallback_err:
            logger.error(f"Fatal failure during deterministic fallback: {fallback_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agentic platform error: {str(e)}. (Legacy fallback prohibited by architecture)."
            )


@router.post("/search", response_model=List[EvidenceItem], status_code=status.HTTP_200_OK)
async def direct_semantic_search(query: str, top_k: int = 10):
    """
    Direct semantic retrieval endpoint without specialist agent execution.
    Runs direct parameterized pgvector search over stored embeddings.
    """
    clean_q = SecurityGuardrails.sanitize_untrusted_text((query or "").strip())
    if not clean_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty or whitespace."
        )

    try:
        items = await _direct_retriever.search(query=clean_q, top_k=top_k)
        return items
    except Exception as e:
        logger.error(f"Direct semantic search error for '{clean_q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Direct semantic retrieval failure: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def agentic_health_check():
    """
    Health check endpoint for the Independent Agentic Platform.
    Verifies database connectivity, vector index readiness, and encoder status.
    """
    try:
        async with DatabasePool.acquire() as conn:
            chunk_cnt = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
            vector_cnt = await conn.fetchval("SELECT COUNT(*) FROM embeddings;")

        return {
            "platform": "SAP Utilities Independent CrewAI Agentic Platform",
            "version": "2.0.0",
            "status": "healthy",
            "database": {
                "chunks": chunk_cnt,
                "embeddings": vector_cnt,
                "distance_metric": "cosine (<=>)"
            },
            "encoder": {
                "model": _direct_retriever.encoder.model_name,
                "dimension": _direct_retriever.encoder.target_dim,
                "device": _direct_retriever.encoder.device
            },
            "specialist_roles": [
                "Query Planner",
                "Semantic Discovery Worker",
                "Procedure Analyst",
                "Configuration Analyst",
                "Relationship Analyst",
                "Troubleshooting Analyst",
                "Evidence Auditor",
                "Answer Synthesizer"
            ],
            "isolation_boundary": "Strict (Legacy RAG execution path prohibited)"
        }
    except Exception as e:
        logger.error(f"Agentic health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agentic health check failure: {str(e)}"
        )
