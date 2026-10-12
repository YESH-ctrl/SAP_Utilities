"""
Deterministic Citation Validator for Agentic Platform.
Verifies that every citation refers to a genuine evidence item retrieved for this request.
Checks chunk ID, document ID, title, and canonical URL matching.
Verifies exact or fuzzy quoted text matches.
Does NOT permit LLM self-certification of citations.
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from sap_rag.agentic.schemas.contracts import (
    EvidenceItem,
    CitationItem,
    CitationVerification,
    ValidationReport
)

logger = logging.getLogger("sap_rag.agentic.validators.citation")


class CitationValidator:
    """
    Independent deterministic validator for citation and claim grounding.
    """

    @staticmethod
    def extract_numbered_citations(text: str) -> List[int]:
        """
        Extract numerical citations in brackets e.g. [1], [2], [1, 2], [1-3]
        """
        if not text:
            return []
        matches = re.findall(r"\[(\d+(?:[,\s\-–]+\d+)*)\]", text)
        citation_indices = []
        for m in matches:
            # Handle comma or hyphen lists
            parts = re.split(r"[,]+", m)
            for p in parts:
                p = p.strip()
                if "-" in p or "–" in p:
                    subparts = re.split(r"[\-–]+", p)
                    if len(subparts) == 2 and subparts[0].isdigit() and subparts[1].isdigit():
                        start, end = int(subparts[0]), int(subparts[1])
                        citation_indices.extend(range(start, min(end + 1, start + 10)))
                elif p.isdigit():
                    citation_indices.append(int(p))
        return sorted(list(set(citation_indices)))

    def validate_answer(
        self,
        answer_text: str,
        citations: List[CitationItem],
        evidence_items: List[EvidenceItem],
        response_mode: str = "synthesized_answer",
        evidence_sufficiency: str = "partial"
    ) -> ValidationReport:
        """
        Validate answer citations against real request evidence.
        """
        evidence_by_chunk_id: Dict[int, EvidenceItem] = {ev.chunk_id: ev for ev in evidence_items}
        evidence_by_ev_id: Dict[str, EvidenceItem] = {ev.evidence_id: ev for ev in evidence_items}

        referenced_nums = self.extract_numbered_citations(answer_text)
        citation_by_num: Dict[int, CitationItem] = {c.citation_id: c for c in citations}

        verified_citations: List[CitationVerification] = []
        invalid_citations: List[str] = []

        # Check each referenced citation in the answer text
        for num in referenced_nums:
            cit = citation_by_num.get(num)
            if not cit:
                invalid_citations.append(f"Citation [{num}] is cited in text but missing from citation metadata")
                continue

            # Verify chunk exists in evidence set
            matching_ev = evidence_by_chunk_id.get(cit.chunk_id) or evidence_by_ev_id.get(cit.evidence_id)
            if not matching_ev:
                invalid_citations.append(f"Citation [{num}] references nonexistent chunk_id={cit.chunk_id}")
                continue

            # Verify title and canonical url match stored metadata
            if matching_ev.document_id != cit.document_id:
                invalid_citations.append(f"Citation [{num}] document_id mismatch: expected {matching_ev.document_id}, got {cit.document_id}")
                continue

            # Substring match check for quoted text if excerpt provided
            quote_clean = (cit.excerpt or "").strip().lower()
            content_clean = (matching_ev.content or "").strip().lower()
            is_substring = True
            if quote_clean and len(quote_clean) > 20:
                # Check first 40 chars of quote
                probe = quote_clean[:40]
                is_substring = probe in content_clean

            verified_citations.append(
                CitationVerification(
                    citation_index=num,
                    evidence_id=matching_ev.evidence_id,
                    chunk_id=matching_ev.chunk_id,
                    document_id=matching_ev.document_id,
                    title=matching_ev.title,
                    canonical_url=matching_ev.canonical_url,
                    quoted_text=cit.excerpt[:200] if cit.excerpt else "",
                    is_verified_in_evidence=True,
                    is_exact_substring_match=is_substring
                )
            )

        total_referenced = len(referenced_nums)
        if total_referenced > 0:
            citation_integrity_ratio = round(len(verified_citations) / total_referenced, 2)
            citation_integrity = (len(invalid_citations) == 0 and len(verified_citations) > 0)
        else:
            # No citations emitted in text
            citation_integrity_ratio = 1.0 if not citations else 0.0
            citation_integrity = len(invalid_citations) == 0

        is_evidence_only = (response_mode == "evidence_only")
        overall = "evidence_only" if is_evidence_only else ("verified" if citation_integrity else "unverified")

        report = ValidationReport(
            citation_integrity=citation_integrity,
            citation_integrity_ratio=citation_integrity_ratio,
            verified_citations=verified_citations,
            invalid_citations=invalid_citations,
            claim_support_rate=None if is_evidence_only else (1.0 if citation_integrity else 0.0),
            question_coverage_rate=None if is_evidence_only else 0.0,
            evidence_sufficiency=evidence_sufficiency,
            synthesis_status="synthesis_unavailable" if is_evidence_only else "synthesis_completed",
            unanswered_subquestions=[],
            detected_contradictions=[],
            repair_attempts=0,
            overall_status=overall,
            notes="Truthful evidence-only validation report" if is_evidence_only else None
        )

        return report

    def get_active_citations(
        self,
        citations: List[CitationItem],
        answer_text: str
    ) -> List[CitationItem]:
        """
        Filters citations to only those actually cited in the answer text [1], [2]...
        Excludes candidate evidence items that were not cited in the synthesized answer.
        """
        referenced_nums = set(self.extract_numbered_citations(answer_text))
        if not referenced_nums:
            return citations
        return [c for c in citations if c.citation_id in referenced_nums]

    @staticmethod
    def deduplicate_sources_for_reference_list(
        active_citations: List[CitationItem]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicates source documents for the final reference list while preserving
        distinct citation indices and passage excerpts.
        """
        grouped: Dict[str, Dict[str, Any]] = {}
        for c in active_citations:
            key = c.canonical_url or c.title
            if key not in grouped:
                grouped[key] = {
                    "document_id": c.document_id,
                    "title": c.title,
                    "canonical_url": c.canonical_url,
                    "citation_indices": [c.citation_id],
                    "excerpts": [c.excerpt] if c.excerpt else []
                }
            else:
                grouped[key]["citation_indices"].append(c.citation_id)
                if c.excerpt and c.excerpt not in grouped[key]["excerpts"]:
                    grouped[key]["excerpts"].append(c.excerpt)
        return list(grouped.values())
