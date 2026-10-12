"""
FastAPI router for SAP Utilities Retrieval Engine endpoints.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.schemas import RetrievalRequest, RetrievalResponse, CandidateResultSchema
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])
pipeline_instance = RetrievalPipeline()

@router.post("/search", response_model=RetrievalResponse, status_code=status.HTTP_200_OK)
@router.post("/query", response_model=RetrievalResponse, status_code=status.HTTP_200_OK)
async def search_documentation(req: RetrievalRequest):
    """
    Search SAP Utilities documentation chunks using Hybrid (pgvector Dense + PostgreSQL Lexical + Reranking) retrieval engine.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'query' cannot be empty or whitespace."
        )

    try:
        async with DatabasePool.acquire() as conn:
            candidates, context_str, processed_query, metrics = await pipeline_instance.execute(
                conn=conn,
                query=req.query,
                top_k=req.top_k,
                dense_candidate_k=req.dense_candidate_k,
                lexical_candidate_k=req.lexical_candidate_k,
                rerank=req.rerank,
                include_neighbors=req.include_neighbors,
                source_ids=req.source_ids,
                document_ids=req.document_ids,
                dense_weight=req.dense_weight,
                lexical_weight=req.lexical_weight,
                mmr_lambda=req.mmr_lambda
            )

            results_schema = []
            for c in candidates:
                summary = c.to_summary_dict()
                breakdown = summary.get("scores_breakdown") or summary.get("feature_breakdown") or {}
                results_schema.append(
                    CandidateResultSchema(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        section_id=c.section_id,
                        source_id=c.source_id,
                        title=c.title,
                        url=c.url,
                        breadcrumb=c.breadcrumb,
                        content=c.content,
                        score=round(c.final_score, 4),
                        retrieval_method=c.retrieval_method,
                        scores_breakdown=breakdown
                    )
                )

            return RetrievalResponse(
                query=req.query,
                processed_query=processed_query,
                results=results_schema,
                formatted_context=context_str,
                metadata=metrics.to_dict()
            )
    except Exception as e:
        logger.error(f"Error executing retrieval search query '{req.query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval engine failure: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def retrieval_health_check():
    """
    Health check endpoint for retrieval engine database connectivity and model readiness.
    """
    try:
        async with DatabasePool.acquire() as conn:
            chunk_cnt = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
            vector_cnt = await conn.fetchval("SELECT COUNT(*) FROM embeddings;")
        return {
            "status": "healthy",
            "database_chunks": chunk_cnt,
            "database_vectors": vector_cnt,
            "model": pipeline_instance.dense_retriever.model_key,
            "dimension": pipeline_instance.dense_retriever.service.target_dimension
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database or model service unavailable: {str(e)}"
        )
