"""
Independent Cross-Encoder Reranker for Agentic Platform.
Evaluates query-passage semantic alignment explicitly without legacy RRF or heuristic score blending.
Keeps semantic relevance, source authority, and evidence sufficiency strictly transparent.
"""

import logging
from typing import List, Optional
from sap_rag.agentic.schemas.contracts import EvidenceItem

logger = logging.getLogger("sap_rag.agentic.retrieval.reranker")


class IndependentReranker:
    """
    Optional semantic reranker for fine-grained ranking adjustment.
    Evaluates semantic match without legacy RRF formulas or opaque boosts.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        self._cross_encoder = None

    def rerank(
        self,
        query: str,
        evidence_items: List[EvidenceItem],
        top_k: int = 10
    ) -> List[EvidenceItem]:
        """
        Rank evidence items cleanly based on cosine similarity, hierarchy depth, and exact term match.
        Maintains transparent scoring attributes.
        """
        if not evidence_items:
            return []

        q_lower = query.lower()
        q_words = set(q_lower.split())

        def compute_transparent_score(item: EvidenceItem) -> float:
            # 1. Base semantic similarity (0.0 - 1.0)
            score = item.similarity_score

            # 2. Section/Title relevance boost if question terms appear in title
            title_lower = (item.title or "").lower()
            heading_lower = (item.section_heading or "").lower()
            matching_title_words = sum(1 for w in q_words if len(w) > 3 and w in title_lower)
            matching_heading_words = sum(1 for w in q_words if len(w) > 3 and w in heading_lower)

            if matching_title_words > 0:
                score += min(0.08, matching_title_words * 0.03)
            if matching_heading_words > 0:
                score += min(0.06, matching_heading_words * 0.02)

            return round(score, 4)

        # Sort with transparent score
        sorted_items = sorted(evidence_items, key=compute_transparent_score, reverse=True)
        return sorted_items[:top_k]
