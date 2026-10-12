"""
Maximal Marginal Relevance (MMR) component for result diversity and redundancy elimination.
"""

import math
import logging
from typing import List, Set
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate

logger = logging.getLogger(__name__)

def _calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Fast character/token Jaccard similarity for redundancy check between two document chunks.
    """
    if not text1 or not text2:
        return 0.0
    words1: Set[str] = set(text1.lower().split())
    words2: Set[str] = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

class MMRSelector:
    """
    Maximal Marginal Relevance (MMR) selection engine balancing relevance and information diversity.
    """

    @classmethod
    def select(
        cls,
        candidates: List[RetrievalCandidate],
        top_k: int = retrieval_settings.FINAL_TOP_K,
        mmr_lambda: float = retrieval_settings.MMR_LAMBDA,
        enabled: bool = retrieval_settings.MMR_ENABLED
    ) -> List[RetrievalCandidate]:
        """
        Select top_k candidates from candidate pool using MMR greedy selection.
        """
        if not candidates:
            return []

        if not enabled or len(candidates) <= top_k:
            return candidates[:top_k]

        unselected = list(candidates)
        selected: List[RetrievalCandidate] = []

        while len(selected) < top_k and unselected:
            best_cand = None
            best_mmr_score = -float("inf")

            for cand in unselected:
                norm_rel = cand.final_score

                # Calculate max similarity with any already selected candidate
                if selected:
                    max_sim = max(_calculate_text_similarity(cand.content, s.content) for s in selected)
                else:
                    max_sim = 0.0

                mmr_score = (mmr_lambda * norm_rel) - ((1.0 - mmr_lambda) * max_sim)

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_cand = cand

            if best_cand:
                selected.append(best_cand)
                unselected.remove(best_cand)
            else:
                break

        logger.debug(f"MMRSelector selected {len(selected)} diverse candidates from {len(candidates)} pool.")
        return selected
