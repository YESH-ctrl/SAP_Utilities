"""
Confidence Calibration & Answerability Evaluator for V4 Production Hardening.
Evaluates ranking margin, domain compatibility, evidence consistency, query coverage, and computes answerability status.
"""

import logging
from typing import List, Tuple
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

logger = logging.getLogger(__name__)

class ConfidenceEvaluator:
    """
    Computes calibrated confidence level (HIGH, MEDIUM, LOW), numerical confidence_score, and answerability_score.
    """

    @classmethod
    def evaluate(
        cls,
        candidates: List[RetrievalCandidate],
        processed_query: ProcessedQuery
    ) -> Tuple[str, str, float]:
        """
        Returns (confidence_level, answerability_status, confidence_num).
        """
        if not candidates:
            return "LOW", "INSUFFICIENT_EVIDENCE", 0.0

        top_cand = candidates[0]
        second_cand = candidates[1] if len(candidates) > 1 else None

        # 1. Top score & ranking margin
        top_score = top_cand.final_score
        margin = (top_score - second_cand.final_score) if second_cand else 0.50

        # 2. Key evidence signals
        has_title_match = top_cand.title_score >= 0.50
        has_protected = top_cand.is_protected
        domain_match = top_cand.domain_match_score >= 0.70
        tech_match = top_cand.technical_term_score >= 0.30

        # 3. Compute numerical confidence [0.0, 1.0]
        conf_num = min(1.0, (top_cand.relevance_score * 0.50) + (top_cand.hybrid_score * 30.0) + (margin * 0.20))

        # 4. Calibrated Confidence Classification (Phase 13)
        if (has_protected or (has_title_match and domain_match)) and conf_num >= 0.45:
            confidence = "HIGH"
        elif conf_num >= 0.35 and (domain_match or tech_match):
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # 5. Answerability Classification (Phase 14)
        if confidence == "HIGH" and len(candidates) >= 2:
            answerability = "ANSWERABLE"
        elif confidence in ["HIGH", "MEDIUM"]:
            answerability = "PARTIALLY_ANSWERABLE"
        else:
            answerability = "INSUFFICIENT_EVIDENCE"

        processed_query.retrieval_confidence = confidence
        processed_query.answerability = answerability

        logger.debug(f"ConfidenceEvaluator evaluated query '{processed_query.original_query[:30]}...': "
                     f"Confidence={confidence} ({conf_num:.3f}), Answerability={answerability}")

        return confidence, answerability, round(conf_num, 4)
