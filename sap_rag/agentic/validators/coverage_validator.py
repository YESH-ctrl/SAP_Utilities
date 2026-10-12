"""
Deterministic Answer Coverage Validator for Agentic Platform.
Compares final synthesized answer against planned subquestions and required entities.
Detects unanswered subquestions and ensures transparent omission labeling.
Reports granular coverage for each subquestion: answered, partially_answered, not_found, needs_clarification.
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from sap_rag.agentic.schemas.contracts import (
    QueryPlan,
    SubQuestion,
    ResponseMode,
    SubQuestionCoverage,
    SubQuestionCoverageStatus
)

logger = logging.getLogger("sap_rag.agentic.validators.coverage")


class AnswerCoverageValidator:
    """
    Evaluates whether the final synthesized answer directly addresses the planned subquestions.
    Returns None in evidence-only mode or when no answer synthesis was executed.
    """

    def __init__(self):
        self.last_coverage_details: List[SubQuestionCoverage] = []

    def evaluate_coverage_details(
        self,
        answer_text: str,
        query_plan: QueryPlan,
        response_mode: str = "synthesized_answer"
    ) -> Tuple[Optional[float], List[str], List[str], List[SubQuestionCoverage]]:
        """
        Evaluate granular subquestion coverage:
        Reports each subquestion as answered, partially_answered, not_found, or needs_clarification.
        """
        if response_mode == ResponseMode.EVIDENCE_ONLY.value or "Answer Synthesis Unavailable" in answer_text:
            details = [
                SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.NOT_FOUND,
                    explanation="Answer synthesis unavailable; raw evidence passages presented without narrative synthesis."
                )
                for sq in query_plan.subquestions
            ]
            self.last_coverage_details = details
            return None, [], [sq.question for sq in query_plan.subquestions], details

        if not answer_text or not answer_text.strip():
            details = [
                SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.NOT_FOUND,
                    explanation="Final answer is empty."
                )
                for sq in query_plan.subquestions
            ]
            self.last_coverage_details = details
            return 0.0, [], [sq.question for sq in query_plan.subquestions], details

        if not query_plan.subquestions:
            details = [
                SubQuestionCoverage(
                    subquestion_id="SQ-MAIN",
                    question=query_plan.original_query,
                    status=SubQuestionCoverageStatus.ANSWERED,
                    explanation="Single question query addressed directly."
                )
            ]
            self.last_coverage_details = details
            return 1.0, [query_plan.original_query], [], details

        ans_lower = answer_text.lower()
        answered = []
        unanswered = []
        details: List[SubQuestionCoverage] = []

        stop_words = {
            "what", "when", "where", "which", "does", "have", "with", "from",
            "step", "steps", "explain", "about", "there", "these", "those",
            "the", "and", "for", "how", "can", "are"
        }

        for sq in query_plan.subquestions:
            q_clean = sq.question.lower()
            terms = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", q_clean) if w not in stop_words]

            # Critical Section 6 check:
            # "Do not mark a general reconnection question as fully answered merely because contract-reversal procedures have been retrieved."
            # "If the evidence supports only contract reversal, state that boundary and identify the reconnection question as unresolved."
            is_reconnection_subq = any(k in q_clean for k in ("reconnect", "reconnection", "disconnected installation"))
            answer_has_reconnection_procedure = any(k in ans_lower for k in ("reconnection order", "change disconnection document", "reconnection entry", "disconnection/reconnection"))

            if is_reconnection_subq and not answer_has_reconnection_procedure:
                if query_plan.requires_clarification or "clarif" in ans_lower:
                    st = SubQuestionCoverageStatus.NEEDS_CLARIFICATION
                    exp = "Reconnection question requires operational clarification; distinct from contract reversal."
                else:
                    st = SubQuestionCoverageStatus.NOT_FOUND
                    exp = "Reconnection procedure not substantiated in retrieved contract reversal documentation."
                unanswered.append(sq.question)
                details.append(SubQuestionCoverage(subquestion_id=sq.id, question=sq.question, status=st, explanation=exp))
                continue

            if not terms:
                answered.append(sq.question)
                details.append(SubQuestionCoverage(subquestion_id=sq.id, question=sq.question, status=SubQuestionCoverageStatus.ANSWERED, explanation="Question terms verified."))
                continue

            matches = sum(1 for t in terms if t in ans_lower)
            match_rate = matches / len(terms) if terms else 1.0

            is_gap_disclosed = (
                "does not specify" in ans_lower or
                "documentation gap" in ans_lower or
                "could not be verified" in ans_lower or
                "does not provide" in ans_lower or
                "not found" in ans_lower or
                "unresolved" in ans_lower
            )

            if match_rate >= 0.60 or sq.question.lower() in ans_lower:
                answered.append(sq.question)
                details.append(SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.ANSWERED,
                    explanation=f"Subquestion substantive terms addressed ({match_rate:.0%})."
                ))
            elif is_gap_disclosed and match_rate >= 0.35:
                answered.append(sq.question)
                details.append(SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.PARTIALLY_ANSWERED,
                    explanation=f"Subquestion partially addressed with transparent documentation gap disclosure."
                ))
            elif query_plan.requires_clarification:
                unanswered.append(sq.question)
                details.append(SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.NEEDS_CLARIFICATION,
                    explanation="Requires user clarification among distinct operational alternatives."
                ))
            else:
                unanswered.append(sq.question)
                details.append(SubQuestionCoverage(
                    subquestion_id=sq.id,
                    question=sq.question,
                    status=SubQuestionCoverageStatus.NOT_FOUND,
                    explanation="Substantive procedure or terms not found in synthesized answer."
                ))

        total = len(query_plan.subquestions)
        coverage_ratio = len(answered) / total if total > 0 else 1.0
        self.last_coverage_details = details

        return round(coverage_ratio, 2), answered, unanswered, details

    def evaluate_coverage(
        self,
        answer_text: str,
        query_plan: QueryPlan,
        response_mode: str = "synthesized_answer"
    ) -> Tuple[Optional[float], List[str], List[str]]:
        cov_ratio, answered, unanswered, _ = self.evaluate_coverage_details(
            answer_text=answer_text,
            query_plan=query_plan,
            response_mode=response_mode
        )
        return cov_ratio, answered, unanswered
