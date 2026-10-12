"""
Transparent SAP Relevance Scorer component for V4 Production Hardening.
Computes multi-feature normalized relevance scores, feature contribution breakdown, title/breadcrumb protection, and domain consistency.
"""

import re
import logging
from typing import List, Dict, Any
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

logger = logging.getLogger(__name__)

class SAPRelevanceScorer:
    """
    Computes transparent normalized relevance scores across independent signals:
    - title_match, section_title_match, breadcrumb_match
    - technical_term_match, acronym_match, phrase_match
    - domain_match, intent_match, action_object_match
    - query_coverage, candidate_agreement
    Stores explicit feature_breakdown for debug explanation.
    """

    @classmethod
    def score_candidates(
        cls,
        candidates: List[RetrievalCandidate],
        processed_query: ProcessedQuery,
        title_weight: float = retrieval_settings.TITLE_BOOST,
        breadcrumb_weight: float = retrieval_settings.BREADCRUMB_BOOST,
        tech_term_weight: float = retrieval_settings.TECHNICAL_TERM_BOOST,
        hierarchy_weight: float = retrieval_settings.HIERARCHY_BOOST,
        relevance_weight: float = 0.0010,
        enable_top1_protection: bool = True
    ) -> List[RetrievalCandidate]:
        if not candidates:
            return []

        tech_terms = [t.lower() for t in processed_query.technical_terms]
        acronyms = [a.lower() for a in processed_query.acronyms]
        keywords = [k.lower() for k in processed_query.keywords]
        actions = [a.lower() for a in processed_query.actions]
        objects = [o.lower() for o in processed_query.objects]
        domain = processed_query.domain.lower()
        intent = processed_query.intent.lower()
        q_text = processed_query.normalized_query

        # Generic title stop-words list
        GENERIC_TITLE_PATTERNS = {"example", "upload", "special settings", "objects", "overview", "general", "introduction", "details"}

        # First, preserve pure RRF ordering and identify Top-1 RRF candidate
        candidates_by_rrf = sorted(candidates, key=lambda x: x.hybrid_score, reverse=True)
        top1_rrf_cand = candidates_by_rrf[0] if candidates_by_rrf else None

        # Compute document frequency & aggregate score in candidate pool
        doc_counts: Dict[int, int] = {}
        doc_max_rrf: Dict[int, float] = {}
        for c in candidates:
            if c.document_id:
                doc_counts[c.document_id] = doc_counts.get(c.document_id, 0) + 1
                doc_max_rrf[c.document_id] = max(doc_max_rrf.get(c.document_id, 0.0), c.hybrid_score)

        for c in candidates:
            title_lower = (c.title or "").lower().strip()
            breadcrumb_lower = (c.breadcrumb or "").lower()
            content_lower = (c.content or "").lower()

            is_generic_title = any(gen in title_lower for gen in GENERIC_TITLE_PATTERNS) and not any(term in title_lower for term in tech_terms)

            # 1. Title Match (Exact technical term or keyword alignment with singular/plural flexibility)
            t_title_matches = 0
            exact_title_match = False
            for term in tech_terms:
                t_base = term.rstrip('s')
                if title_lower == term or title_lower == t_base:
                    exact_title_match = True
                    t_title_matches += 2
                elif term in title_lower or (len(t_base) > 3 and t_base in title_lower):
                    t_title_matches += 1
            k_title_matches = sum(1 for kw in keywords if kw in title_lower or kw.rstrip('s') in title_lower)
            title_match = 0.0 if is_generic_title else min(1.0, (t_title_matches * 0.6) + (k_title_matches * 0.25) + (0.50 if exact_title_match else 0.0))

            # 2. Breadcrumb Match
            b_matches = sum(1 for term in tech_terms if term in breadcrumb_lower or term.rstrip('s') in breadcrumb_lower)
            domain_in_breadcrumb = 1.0 if (domain != "general" and domain.replace("_", " ") in breadcrumb_lower) else 0.0
            breadcrumb_match = min(1.0, (b_matches * 0.5) + (domain_in_breadcrumb * 0.5))

            # 3. Technical Term Match & Acronym Match
            c_tech_matches = sum(1 for term in tech_terms if term in content_lower or term.rstrip('s') in content_lower)
            c_acronym_matches = sum(1 for ac in acronyms if ac in content_lower or ac in title_lower)
            tech_term_match = min(1.0, (c_tech_matches * 0.33) + (c_acronym_matches * 0.25))

            # 4. Phrase Match
            phrase_match = 1.0 if (q_text and q_text in content_lower) else 0.0

            # 5. Domain & Intent Compatibility Scoring
            domain_match = 1.0 if (domain != "general" and (domain.replace("_", " ") in title_lower or domain.replace("_", " ") in breadcrumb_lower)) else 0.5
            intent_match = 1.0 if (intent != "general" and (intent in title_lower or intent in content_lower[:200])) else 0.5

            # 6. Action & Object Match
            action_match = 1.0 if any(act in content_lower for act in actions) else 0.0
            object_match = 1.0 if any(obj in title_lower or obj in content_lower for obj in objects) else 0.0
            action_object_match = (action_match * 0.5) + (object_match * 0.5)

            # 6b. V5.5 Conceptual & Procedural Intent Alignment
            is_conceptual_q = intent in ("overview", "definition") or any(p in q_text for p in ["what is", "what are", "define", "concept", "overview", "how does"])
            is_procedural_q = intent == "procedure" or any(p in q_text for p in ["how to", "how do", "create", "process", "procedure", "manually", "perform"])

            c_idx = c.metadata.get("chunk_index", 1) if isinstance(c.metadata, dict) else 1
            has_concept_title = any(term in title_lower or term.rstrip('s') in title_lower or term in breadcrumb_lower for term in tech_terms) or "overview" in title_lower or "concept" in title_lower
            concept_align = 1.0 if (is_conceptual_q and (c_idx == 0 or has_concept_title)) else 0.0

            proc_align = 1.0 if (is_procedural_q and (action_match > 0 or "create" in q_text or "perform" in q_text) and (object_match > 0 or t_title_matches > 0)) else 0.0

            # 7. Query Term Coverage
            c_tokens = set(content_lower.split())
            covered_kws = sum(1 for kw in keywords if kw in c_tokens)
            query_coverage = covered_kws / max(1, len(keywords)) if keywords else 0.0

            # 8. Document Aggregated Evidence Confidence (Section 17)
            doc_freq = doc_counts.get(c.document_id, 1) if c.document_id else 1
            doc_confidence = min(0.10, (doc_freq - 1) * 0.03)

            # 9. Compute combined normalized relevance score
            relevance_score = (
                (title_weight * title_match) +
                (breadcrumb_weight * breadcrumb_match) +
                (tech_term_weight * tech_term_match) +
                (0.10 * phrase_match) +
                (0.10 * domain_match) +
                (0.05 * intent_match) +
                (0.05 * action_object_match) +
                (0.10 * concept_align) +
                (0.10 * proc_align) +
                (0.10 * query_coverage) +
                doc_confidence
            )

            c.title_score = float(title_match)
            c.breadcrumb_score = float(breadcrumb_match)
            c.technical_term_score = float(tech_term_match)
            c.domain_match_score = float(domain_match)
            c.intent_match_score = float(intent_match)
            c.relevance_score = float(relevance_score)

            # Two-stage score: secondary relevance operates strictly within RRF stability margin
            c.pre_rerank_score = float(c.hybrid_score + (relevance_weight * relevance_score))
            c.final_score = float(c.pre_rerank_score)

            # Store explicit feature contribution breakdown for debug observability
            c.feature_breakdown = {
                "dense_score": round(c.dense_score, 4),
                "lexical_score": round(c.lexical_score, 4),
                "hybrid_rrf_score": round(c.hybrid_score, 4),
                "title_match": round(title_match, 4),
                "breadcrumb_match": round(breadcrumb_match, 4),
                "technical_term_match": round(tech_term_match, 4),
                "phrase_match": round(phrase_match, 4),
                "domain_match": round(domain_match, 4),
                "intent_match": round(intent_match, 4),
                "concept_align": round(concept_align, 4),
                "proc_align": round(proc_align, 4),
                "query_coverage": round(query_coverage, 4),
                "doc_confidence": round(doc_confidence, 4),
                "relevance_score": round(relevance_score, 4),
                "pre_rerank_score": round(c.pre_rerank_score, 4)
            }

        # 10. Exact Title & Domain Protection Floor (Sections 11 & 12)
        for c in candidates:
            t_title = (c.title or "").lower().strip()
            # Multi-term title match boost for reconnection / budget billing
            title_terms_cnt = sum(1 for term in tech_terms if term in t_title or term.rstrip('s') in t_title)
            
            for term in tech_terms:
                t_base = term.rstrip('s')
                if (t_title == term or t_title == t_base) and not any(gen in t_title for gen in GENERIC_TITLE_PATTERNS):
                    c.is_protected = True
                    c.pre_rerank_score += 0.0200
                    c.final_score = c.pre_rerank_score
            
            # Domain match boost for budget_billing and specific domain queries
            if c.domain_match_score >= 1.0 and domain != "general":
                c.pre_rerank_score += 0.0100
                c.final_score = c.pre_rerank_score

            # Multi-term title match boost
            if title_terms_cnt >= 2:
                c.pre_rerank_score += 0.0080
                c.final_score = c.pre_rerank_score

        if enable_top1_protection and top1_rrf_cand:
            t1_title = (top1_rrf_cand.title or "").lower().strip()
            t1_content = (top1_rrf_cand.content or "").lower()
            t1_is_generic = any(gen in t1_title for gen in GENERIC_TITLE_PATTERNS) and not any(term in t1_title for term in tech_terms)

            t1_has_title_match = not t1_is_generic and (top1_rrf_cand.title_score >= 0.25 or any(kw in t1_title for kw in keywords if len(kw) > 3))
            t1_has_tech_match = top1_rrf_cand.technical_term_score >= 0.25 or any(t.lower() in t1_title or t.lower() in t1_content for t in tech_terms)
            t1_has_phrase_match = q_text and q_text in t1_content

            if (t1_has_title_match or t1_has_tech_match or t1_has_phrase_match) and not t1_is_generic:
                top1_rrf_cand.is_protected = True
                top1_rrf_cand.pre_rerank_score += 0.0050
                top1_rrf_cand.final_score = top1_rrf_cand.pre_rerank_score

        candidates.sort(key=lambda x: x.pre_rerank_score, reverse=True)
        return candidates
