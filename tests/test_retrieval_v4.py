"""
Unit tests for V4 Production Hardened Retrieval Engine components.
"""

import pytest
from sap_rag.retrieval.models import ProcessedQuery, RetrievalCandidate
from sap_rag.retrieval.query_processor import QueryProcessor
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.relevance_scorer import SAPRelevanceScorer
from sap_rag.retrieval.confidence_evaluator import ConfidenceEvaluator
from sap_rag.retrieval.reranker import FastFeatureReranker

def test_v4_query_processor_acronyms_and_entities():
    q_text = "What is point of delivery POD role in FI-CA?"
    pq = QueryProcessor.process(q_text)

    assert pq.original_query == q_text
    assert "pod" in [t.lower() for t in pq.technical_terms] or "point of delivery" in [t.lower() for t in pq.technical_terms]
    assert "point of delivery pod" in pq.expanded_query.lower()
    assert pq.intent in ["overview", "definition", "general"]

def test_v4_rrf_fusion_missing_channel_neutrality():
    cand1 = RetrievalCandidate(chunk_id=101, document_id=1, dense_score=0.85, lexical_score=0.0)
    cand2 = RetrievalCandidate(chunk_id=102, document_id=2, dense_score=0.0, lexical_score=0.90)

    fused = HybridRetriever.fuse_rrf([cand1], [cand2], k=60, dense_weight=0.5, lexical_weight=0.5)

    assert len(fused) == 2
    assert fused[0].hybrid_score > 0.0
    assert fused[1].hybrid_score > 0.0
    # Candidate 2 (lexical rank 1) must be protected
    assert cand2.is_protected == True

def test_v4_relevance_scorer_feature_breakdown():
    cand = RetrievalCandidate(chunk_id=201, document_id=5, title="Clearing Variant Configuration", breadcrumb="FI-CA > Clearing", content="How clearing control works in FI-CA")
    pq = ProcessedQuery(original_query="clearing control in fi-ca", normalized_query="clearing control in fi-ca", technical_terms=["clearing control", "fi-ca"], keywords=["clearing", "control"], domain="clearing", intent="procedure")

    scored = SAPRelevanceScorer.score_candidates([cand], pq)
    top_c = scored[0]

    assert "title_match" in top_c.feature_breakdown
    assert "relevance_score" in top_c.feature_breakdown
    assert top_c.relevance_score > 0.0

def test_v4_confidence_evaluator():
    cand1 = RetrievalCandidate(chunk_id=301, document_id=10, title="Installment Plan Overview", relevance_score=0.8, hybrid_score=0.015, title_score=1.0, domain_match_score=1.0, is_protected=True)
    cand2 = RetrievalCandidate(chunk_id=302, document_id=11, relevance_score=0.4, hybrid_score=0.008)

    pq = ProcessedQuery(original_query="installment plan", normalized_query="installment plan", technical_terms=["installment plan"])

    conf, ans, conf_num = ConfidenceEvaluator.evaluate([cand1, cand2], pq)

    assert conf == "HIGH"
    assert ans == "ANSWERABLE"
    assert conf_num > 0.0

def test_v4_protected_reranker_safety():
    cand = RetrievalCandidate(chunk_id=401, document_id=15, title="Point of Delivery POD", content="POD master data", pre_rerank_score=0.85, is_protected=True)
    pq = ProcessedQuery(original_query="POD", normalized_query="pod", keywords=["pod"])

    reranker = FastFeatureReranker()
    reranked = reranker.rerank(pq, [cand], top_k=5)

    assert reranked[0].rerank_score >= 0.85
