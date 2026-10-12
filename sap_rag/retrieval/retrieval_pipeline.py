"""
Production-grade Retrieval Pipeline Orchestrator V5 unifying SAP term normalization, candidate-presence-aware RRF fusion, transparent relevance scoring, reranking safety, calibrated confidence, answerability check, concurrent retrieval, and adaptive routing with hard recovery budgets.
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import asyncpg

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import ProcessedQuery, RetrievalCandidate
from sap_rag.retrieval.metrics import RetrievalMetrics
from sap_rag.retrieval.query_processor import QueryProcessor
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.relevance_scorer import SAPRelevanceScorer
from sap_rag.retrieval.confidence_evaluator import ConfidenceEvaluator
from sap_rag.retrieval.reranker import RetrievalReranker
from sap_rag.retrieval.hierarchy_expander import HierarchyExpander
from sap_rag.retrieval.mmr import MMRSelector
from sap_rag.retrieval.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

class RetrievalPipeline:
    """
    Main orchestrator for the SAP Utilities Retrieval Engine V5 Production Optimization.
    """

    def __init__(self, dense_retriever: Optional[DenseRetriever] = None, reranker: Optional[RetrievalReranker] = None):
        self.dense_retriever = dense_retriever or DenseRetriever()
        self.lexical_retriever = LexicalRetriever()
        self.reranker = reranker or RetrievalReranker()

    async def execute(
        self,
        conn: asyncpg.Connection,
        query: str,
        top_k: int = retrieval_settings.FINAL_TOP_K,
        dense_candidate_k: int = retrieval_settings.DENSE_TOP_K,
        lexical_candidate_k: int = retrieval_settings.LEXICAL_TOP_K,
        rerank: bool = retrieval_settings.RERANK_ENABLED,
        include_neighbors: bool = retrieval_settings.HIERARCHY_ENABLED,
        source_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None,
        dense_weight: Optional[float] = None,
        lexical_weight: Optional[float] = None,
        mmr_lambda: Optional[float] = None,
        adaptive_routing: bool = True,
        config_name: str = "V5_FINAL",
        recovery_budget_ms: float = 250.0,
        relevance_weight: float = 0.0010,
        enable_top1_protection: bool = True,
        max_per_doc: int = 5,
        adaptive_candidate_depth: bool = False,
        hierarchy_recovery_mode: str = "H0"
    ) -> Tuple[List[RetrievalCandidate], str, ProcessedQuery, RetrievalMetrics]:
        """
        Execute modular retrieval pipeline V5 with concurrent search & bounded recovery budget.
        
        Supported config_name modes:
        - "V3_RRF": Baseline candidate-presence-aware RRF fusion without heavy second-stage reranking/recovery.
        - "V5_RRF": Baseline RRF + lightweight SAP relevance scoring.
        - "V5_TITLE": V5_RRF + title/technical-term floor protection.
        - "V5_DOMAIN": V5_TITLE + domain/intent scoring adjustment.
        - "V5_RERANK": V5_DOMAIN + selective reranker when confidence is MEDIUM/LOW.
        - "V5_RECOVERY": V5_RERANK + bounded selective recovery (<=250ms budget) when confidence is LOW.
        - "V5_FINAL": Full adaptive production pipeline (Fast Path for HIGH confidence, Standard Path for MEDIUM, Recovery for LOW).
        """
        pipeline_start = time.time()
        metrics = RetrievalMetrics()

        # 1. Query Processing & Normalization
        processed_query = QueryProcessor.process(query)

        # 2 & 3. Concurrent Dense Vector Search & Lexical FTS Search (Phase 22)
        t0 = time.time()
        use_expanded_flag = False
        if DatabasePool._pool is not None:
            async with DatabasePool.acquire() as conn_lex:
                dense_task = self.dense_retriever.search(
                    conn,
                    query=processed_query.original_query,
                    top_k=dense_candidate_k,
                    source_ids=source_ids,
                    document_ids=document_ids
                )
                lexical_task = self.lexical_retriever.search(
                    conn_lex,
                    processed_query=processed_query,
                    top_k=lexical_candidate_k,
                    source_ids=source_ids,
                    document_ids=document_ids,
                    use_expanded=use_expanded_flag
                )
                dense_cands, lexical_cands = await asyncio.gather(dense_task, lexical_task)
        else:
            dense_cands = await self.dense_retriever.search(
                conn,
                query=processed_query.original_query,
                top_k=dense_candidate_k,
                source_ids=source_ids,
                document_ids=document_ids
            )
            lexical_cands = await self.lexical_retriever.search(
                conn,
                processed_query=processed_query,
                top_k=lexical_candidate_k,
                source_ids=source_ids,
                document_ids=document_ids,
                use_expanded=use_expanded_flag
            )
        
        search_ms = (time.time() - t0) * 1000.0
        metrics.dense_search_ms = search_ms / 2.0  # Approx parallel time
        metrics.lexical_search_ms = search_ms / 2.0
        metrics.dense_candidates_count = len(dense_cands)
        metrics.lexical_candidates_count = len(lexical_cands)

        # 4. Candidate-Presence-Aware RRF Fusion
        t0 = time.time()
        dw = dense_weight if dense_weight is not None else retrieval_settings.DENSE_WEIGHT
        lw = lexical_weight if lexical_weight is not None else retrieval_settings.LEXICAL_WEIGHT
        fused_cands = HybridRetriever.fuse(
            dense_candidates=dense_cands,
            lexical_candidates=lexical_cands,
            dense_weight=dw,
            lexical_weight=lw
        )
        metrics.fusion_ms = (time.time() - t0) * 1000.0
        metrics.merged_candidates_count = len(fused_cands)

        # Handle V3_RRF pure baseline path
        if config_name == "V3_RRF":
            final_cands = fused_cands[:top_k]
            context_str = ContextBuilder.build_context(final_cands)
            metrics.total_retrieval_ms = (time.time() - pipeline_start) * 1000.0
            metrics.final_results_count = len(final_cands)
            processed_query.retrieval_confidence = "HIGH" if len(final_cands) >= top_k else "MEDIUM"
            processed_query.answerability = "ANSWERABLE" if len(final_cands) > 0 else "INSUFFICIENT_EVIDENCE"
            return final_cands, context_str, processed_query, metrics

        # 5. Transparent SAP Relevance Scoring
        t0 = time.time()
        apply_title_prot = enable_top1_protection and config_name in ("V5_TITLE", "V5_DOMAIN", "V5_RERANK", "V5_RECOVERY", "V5_FINAL", "V5_2_BEST", "V5_FINAL_C")

        scored_cands = SAPRelevanceScorer.score_candidates(
            candidates=fused_cands,
            processed_query=processed_query,
            relevance_weight=relevance_weight,
            enable_top1_protection=apply_title_prot
        )

        if not apply_title_prot:
            # Strip title floor protection if testing basic RRF configurations
            for c in scored_cands:
                c.is_protected = False

        metrics.metadata_scoring_ms = (time.time() - t0) * 1000.0

        # 6. Confidence Calibration & Answerability Evaluation
        confidence, answerability, conf_score = ConfidenceEvaluator.evaluate(scored_cands, processed_query)

        # 7. Selective Recovery Path with Hard Latency Budget (Phases 10, 11 & 12)
        allow_recovery = config_name in ("V5_RECOVERY", "V5_FINAL")
        if allow_recovery and (confidence == "LOW" or (retrieval_settings.V55_Q50_RECOVERY_ENABLED and confidence != "HIGH")):
            elapsed_so_far_ms = (time.time() - pipeline_start) * 1000.0
            rem_budget_sec = max(0.05, (recovery_budget_ms - elapsed_so_far_ms) / 1000.0)
            
            logger.info(
                f"Low retrieval confidence for query '{query[:30]}...'; "
                f"triggering selective recovery path with {rem_budget_sec*1000:.1f}ms budget."
            )
            t_rec = time.time()
            try:
                fallback_task = self.lexical_retriever.search(
                    conn,
                    processed_query=processed_query,
                    top_k=lexical_candidate_k,
                    source_ids=source_ids,
                    document_ids=document_ids,
                    use_expanded=True
                )
                fallback_lexical = await asyncio.wait_for(fallback_task, timeout=rem_budget_sec)
                
                if fallback_lexical:
                    fused_cands = HybridRetriever.fuse(
                        dense_candidates=dense_cands,
                        lexical_candidates=fallback_lexical,
                        dense_weight=dw,
                        lexical_weight=lw
                    )
                    scored_cands = SAPRelevanceScorer.score_candidates(
                        fused_cands,
                        processed_query,
                        relevance_weight=relevance_weight,
                        enable_top1_protection=apply_title_prot
                    )
                    confidence, answerability, conf_score = ConfidenceEvaluator.evaluate(scored_cands, processed_query)
            except asyncio.TimeoutError:
                logger.warning(f"Selective recovery search timed out after {rem_budget_sec*1000:.1f}ms; using initial candidate set.")
            finally:
                metrics.recovery_ms = (time.time() - t_rec) * 1000.0

        # 7b. Hierarchy-Aware Candidate Recovery (Experiment C: H1 / H2)
        if hierarchy_recovery_mode in ("H1", "H2") and scored_cands:
            scored_cands = await HierarchyExpander.expand_parent_source(
                conn,
                candidates=scored_cands,
                max_additions=5 if hierarchy_recovery_mode == "H1" else 8
            )

        # Quick return for V5_RRF, V5_TITLE, V5_DOMAIN configurations
        if config_name in ("V5_RRF", "V5_TITLE", "V5_DOMAIN"):
            final_cands = self._apply_document_diversification(scored_cands, top_k=top_k, max_per_doc=max_per_doc)
            context_str = ContextBuilder.build_context(final_cands)
            metrics.total_retrieval_ms = (time.time() - pipeline_start) * 1000.0
            metrics.final_results_count = len(final_cands)
            return final_cands, context_str, processed_query, metrics

        # 8. Adaptive Fast Path Router (Phase 15 & 26)
        if adaptive_routing and confidence == "HIGH" and len(scored_cands) >= top_k:
            final_cands = self._apply_document_diversification(scored_cands, top_k=top_k, max_per_doc=max_per_doc)
            t0 = time.time()
            context_str = ContextBuilder.build_context(final_cands)
            metrics.context_building_ms = (time.time() - t0) * 1000.0
            metrics.total_retrieval_ms = (time.time() - pipeline_start) * 1000.0
            metrics.final_results_count = len(final_cands)

            logger.info(f"RetrievalPipeline V5 FAST PATH completed in {metrics.total_retrieval_ms:.1f}ms for query '{query[:30]}...'")
            return final_cands, context_str, processed_query, metrics

        # STANDARD PATH: Selective Reranker & Hierarchy Expansion
        t0 = time.time()
        should_rerank = rerank and config_name in ("V5_RERANK", "V5_RECOVERY", "V5_FINAL")
        rerank_target_k = min(len(scored_cands), max(top_k * 2, 15))
        
        if should_rerank:
            reranked_cands = self.reranker.rerank(
                processed_query=processed_query,
                candidates=scored_cands,
                top_k=rerank_target_k,
                enabled=True
            )
        else:
            reranked_cands = list(scored_cands[:rerank_target_k])

        metrics.reranking_ms = (time.time() - t0) * 1000.0
        metrics.reranked_candidates_count = len(reranked_cands)

        # Controlled Hierarchy Expansion
        t0 = time.time()
        if include_neighbors and confidence != "HIGH":
            expanded_cands = await HierarchyExpander.expand(
                conn,
                candidates=reranked_cands,
                window=retrieval_settings.NEIGHBOR_WINDOW,
                enabled=include_neighbors
            )
        else:
            expanded_cands = list(reranked_cands)
        metrics.hierarchy_expansion_ms = (time.time() - t0) * 1000.0
        metrics.expanded_candidates_count = len(expanded_cands)

        # Controlled Document Diversification & MMR
        t0 = time.time()
        diversified_cands = self._apply_document_diversification(expanded_cands, top_k=max(top_k * 2, 12), max_per_doc=max_per_doc)
        
        lambda_val = mmr_lambda if mmr_lambda is not None else retrieval_settings.MMR_LAMBDA
        final_cands = MMRSelector.select(
            candidates=diversified_cands,
            top_k=top_k,
            mmr_lambda=lambda_val,
            enabled=retrieval_settings.MMR_ENABLED
        )
        metrics.mmr_ms = (time.time() - t0) * 1000.0
        metrics.final_results_count = len(final_cands)

        # Context Building
        t0 = time.time()
        context_str = ContextBuilder.build_context(final_cands)
        metrics.context_building_ms = (time.time() - t0) * 1000.0
        metrics.total_retrieval_ms = (time.time() - pipeline_start) * 1000.0

        logger.info(
            f"RetrievalPipeline V5 STANDARD PATH completed in {metrics.total_retrieval_ms:.1f}ms: "
            f"dense={metrics.dense_candidates_count}, lexical={metrics.lexical_candidates_count}, "
            f"final={metrics.final_results_count} chunks."
        )

        return final_cands, context_str, processed_query, metrics

    def _apply_document_diversification(self, candidates: List[RetrievalCandidate], top_k: int, max_per_doc: int = 3) -> List[RetrievalCandidate]:
        """
        Document-aware candidate selection ensuring a single document does not monopolize all slots.
        """
        if not candidates:
            return []

        doc_counts: Dict[int, int] = {}
        diversified: List[RetrievalCandidate] = []

        for cand in candidates:
            doc_id = cand.document_id
            curr_cnt = doc_counts.get(doc_id, 0)

            if curr_cnt < max_per_doc or cand.is_protected:
                diversified.append(cand)
                doc_counts[doc_id] = curr_cnt + 1

            if len(diversified) >= top_k:
                break

        return diversified[:top_k]

