"""
Metadata-aware scoring component boosting candidates based on document title, breadcrumb hierarchy, technical terminology, and document-level relevance aggregation.
"""

import logging
from typing import List, Dict
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

logger = logging.getLogger(__name__)

class MetadataScorer:
    """
    Applies metadata-aware scoring, domain relevance boosts, and document-level confidence to hybrid candidate results.
    """

    @classmethod
    def score_candidates(
        cls,
        candidates: List[RetrievalCandidate],
        processed_query: ProcessedQuery,
        title_weight: float = retrieval_settings.TITLE_BOOST,
        breadcrumb_weight: float = retrieval_settings.BREADCRUMB_BOOST,
        tech_term_weight: float = retrieval_settings.TECHNICAL_TERM_BOOST,
        hierarchy_weight: float = retrieval_settings.HIERARCHY_BOOST
    ) -> List[RetrievalCandidate]:
        """
        Evaluate metadata signals and calculate pre_rerank_score.
        """
        if not candidates:
            return []

        tech_terms = [t.lower() for t in processed_query.technical_terms]
        keywords = [k.lower() for k in processed_query.keywords]
        domain = processed_query.domain.lower()

        # Document frequency calculation for document-level confidence (Phase 5)
        doc_counts: Dict[int, int] = {}
        for c in candidates:
            if c.document_id:
                doc_counts[c.document_id] = doc_counts.get(c.document_id, 0) + 1

        for c in candidates:
            title_lower = (c.title or "").lower()
            breadcrumb_lower = (c.breadcrumb or "").lower()
            content_lower = (c.content or "").lower()

            # 1. Title score: exact technical term matches in title (weighted heavily)
            t_title_matches = sum(1 for term in tech_terms if term in title_lower)
            k_title_matches = sum(1 for kw in keywords if kw in title_lower)
            c.title_score = min(1.0, (t_title_matches * 0.6) + (k_title_matches * 0.25))

            # 2. Breadcrumb score: matching terms or domain in breadcrumb hierarchy
            b_matches = sum(1 for term in tech_terms if term in breadcrumb_lower)
            domain_in_breadcrumb = 1.0 if (domain != "general" and domain.replace("_", " ") in breadcrumb_lower) else 0.0
            c.breadcrumb_score = min(1.0, (b_matches * 0.5) + (domain_in_breadcrumb * 0.5))

            # 3. Technical term score: exact presence of multi-word SAP terms in content
            c_matches = sum(1 for term in tech_terms if term in content_lower)
            c.technical_term_score = min(1.0, c_matches * 0.33)

            # 4. Hierarchy score: preference for structured sections and root documents
            c.hierarchy_score = 1.0 if (c.section_id is not None or "overview" in title_lower) else 0.5

            # 5. Document-level confidence score (Phase 5)
            doc_freq = doc_counts.get(c.document_id, 1) if c.document_id else 1
            doc_confidence = min(0.10, (doc_freq - 1) * 0.03)

            # 6. Combined pre-rerank score
            meta_component = (
                (title_weight * c.title_score) +
                (breadcrumb_weight * c.breadcrumb_score) +
                (tech_term_weight * c.technical_term_score) +
                (hierarchy_weight * c.hierarchy_score) +
                doc_confidence
            )
            c.pre_rerank_score = c.hybrid_score + meta_component
            c.final_score = c.pre_rerank_score

        # Sort candidates by pre_rerank_score descending
        candidates.sort(key=lambda x: x.pre_rerank_score, reverse=True)
        return candidates
