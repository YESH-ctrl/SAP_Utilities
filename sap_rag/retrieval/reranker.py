"""
Second-stage re-ranking component comparing (Query + Document Chunk) pairs with candidate rank protection safety.
Provides swappable reranker abstraction with robust local feature fallback.
"""

import math
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

logger = logging.getLogger(__name__)

class BaseReranker(ABC):
    """
    Abstract Base Class for retrieval rerankers.
    """
    @abstractmethod
    def rerank(self, processed_query: ProcessedQuery, candidates: List[RetrievalCandidate], top_k: int) -> List[RetrievalCandidate]:
        pass

class FastFeatureReranker(BaseReranker):
    """
    Production-grade, fast multi-feature reranker evaluating Query-Chunk interaction with Protected Candidate Safety (Phase 6).
    """

    def rerank(self, processed_query: ProcessedQuery, candidates: List[RetrievalCandidate], top_k: int) -> List[RetrievalCandidate]:
        if not candidates:
            return []

        q_text = processed_query.normalized_query
        q_tokens = set(processed_query.keywords)
        q_tech_terms = [t.lower() for t in processed_query.technical_terms]

        for cand in candidates:
            c_text = cand.content.lower()
            t_text = cand.title.lower()

            # 1. Exact phrase matching boost
            phrase_boost = 1.0 if (q_text and q_text in c_text) else 0.0

            # 2. Keyword overlap ratio (Jaccard-like)
            c_tokens = set(c_text.split())
            overlap = len(q_tokens.intersection(c_tokens))
            overlap_score = overlap / max(1, len(q_tokens)) if q_tokens else 0.0

            # 3. Technical term exact match count
            tech_match_count = sum(1 for term in q_tech_terms if term in c_text)
            tech_score = min(1.0, tech_match_count * 0.5)

            # 4. Title relevance alignment
            title_overlap = len(q_tokens.intersection(set(t_text.split())))
            title_align_score = title_overlap / max(1, len(q_tokens)) if q_tokens else 0.0

            # Compute combined rerank score using pre_rerank_score baseline with bounded rerank weight
            base_score = cand.pre_rerank_score
            interaction_boost = (
                (0.20 * overlap_score) +
                (0.15 * tech_score) +
                (0.10 * phrase_boost) +
                (0.05 * title_align_score)
            )

            rerank_weight = 0.0020
            calculated_rerank_score = float(base_score + (rerank_weight * interaction_boost))

            # Phase 6: Reranker Safety Protection
            # Protected candidates cannot be demoted below their pre_rerank_score baseline
            if cand.is_protected:
                cand.rerank_score = max(calculated_rerank_score, cand.pre_rerank_score + 0.01)
            else:
                cand.rerank_score = calculated_rerank_score

            cand.final_score = float(cand.rerank_score)
            cand.retrieval_method = "hybrid_reranked"

        candidates.sort(key=lambda x: x.rerank_score or 0.0, reverse=True)
        return candidates[:top_k]

class RetrievalReranker:
    """
    Facade for executing reranking with fallback protection.
    """
    def __init__(self, provider: Optional[BaseReranker] = None):
        self.provider = provider or FastFeatureReranker()

    def rerank(
        self,
        processed_query: ProcessedQuery,
        candidates: List[RetrievalCandidate],
        top_k: int = retrieval_settings.RERANK_TOP_K,
        enabled: bool = retrieval_settings.RERANK_ENABLED
    ) -> List[RetrievalCandidate]:
        """
        Rerank candidates if enabled. Gracefully fall back to pre_rerank_score on failure or if disabled.
        """
        if not candidates:
            return []

        if not enabled:
            logger.debug("Reranking is disabled; maintaining pre_rerank_score order.")
            return candidates[:top_k]

        try:
            reranked = self.provider.rerank(processed_query, candidates, top_k)
            logger.debug(f"Reranker successfully scored {len(reranked)} candidates.")
            return reranked
        except Exception as e:
            logger.warning(f"Reranker failed with error ({e}); falling back to pre_rerank_score ordering.")
            for c in candidates:
                c.rerank_score = None
                c.final_score = c.pre_rerank_score
            candidates.sort(key=lambda x: x.pre_rerank_score, reverse=True)
            return candidates[:top_k]
