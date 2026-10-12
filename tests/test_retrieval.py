"""
Unit and integration tests for SAP Utilities RAG Retrieval Engine components.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from sap_rag.retrieval.query_processor import QueryProcessor
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.metadata_scorer import MetadataScorer
from sap_rag.retrieval.reranker import FastFeatureReranker, RetrievalReranker
from sap_rag.retrieval.mmr import MMRSelector
from sap_rag.retrieval.context_builder import ContextBuilder

def test_query_processor_normal():
    pq = QueryProcessor.process("How do I create an installment plan?")
    assert pq.original_query == "How do I create an installment plan?"
    assert "installment" in pq.keywords or "plan" in pq.keywords
    assert "Installment Plan" in pq.technical_terms
    assert pq.intent == "procedure"
    assert pq.domain == "installment_plan"

def test_query_processor_empty():
    pq = QueryProcessor.process("")
    assert pq.original_query == ""
    assert pq.keywords == []
    assert pq.technical_terms == []

def test_query_processor_sap_terms():
    pq = QueryProcessor.process("FI-CA clearing control for incoming payments")
    assert "FI-CA" in pq.technical_terms or "FI CA" in pq.technical_terms
    assert "Clearing Control" in pq.technical_terms
    assert pq.domain == "clearing"

def test_hybrid_fusion():
    cand1 = RetrievalCandidate(
        chunk_id=1, document_id=10, title="Doc 1", content="Text 1", dense_score=0.95, lexical_score=0.10
    )
    cand2 = RetrievalCandidate(
        chunk_id=2, document_id=10, title="Doc 2", content="Text 2", dense_score=0.60, lexical_score=0.90
    )
    fused = HybridRetriever.fuse([cand1], [cand1, cand2], dense_weight=0.70, lexical_weight=0.30)
    assert len(fused) == 2
    assert fused[0].chunk_id in (1, 2)
    assert 0.0 <= fused[0].hybrid_score <= 1.0

def test_metadata_scorer():
    pq = ProcessedQuery(
        original_query="FI-CA Dunning",
        normalized_query="fi-ca dunning",
        keywords=["dunning"],
        technical_terms=["FI-CA", "Dunning"],
        intent="general",
        domain="dunning"
    )
    cand = RetrievalCandidate(
        chunk_id=1,
        document_id=10,
        title="FI-CA Dunning Overview",
        breadcrumb="Contract Accounts -> Dunning",
        content="FI-CA dunning procedures for overdue receivables",
        dense_score=0.90,
        lexical_score=0.80,
        hybrid_score=0.85
    )
    scored = MetadataScorer.score_candidates([cand], pq)
    assert len(scored) == 1
    assert scored[0].title_score > 0
    assert scored[0].breadcrumb_score > 0
    assert scored[0].pre_rerank_score >= 0.85

def test_reranker_feature_scoring():
    pq = ProcessedQuery(
        original_query="meter reading estimation",
        normalized_query="meter reading estimation",
        keywords=["meter", "reading", "estimation"],
        technical_terms=["Meter Reading", "Meter Reading Estimation"],
        intent="general",
        domain="meter_reading"
    )
    cand1 = RetrievalCandidate(
        chunk_id=1, document_id=5, title="Meter Reading Estimation", content="Meter reading estimation procedure details", dense_score=0.90
    )
    cand2 = RetrievalCandidate(
        chunk_id=2, document_id=5, title="Unrelated Document", content="General utilities overview", dense_score=0.50
    )
    reranker = RetrievalReranker()
    reranked = reranker.rerank(pq, [cand1, cand2], top_k=2, enabled=True)
    assert len(reranked) == 2
    assert reranked[0].chunk_id == 1
    assert reranked[0].rerank_score > reranked[1].rerank_score

def test_mmr_diversity():
    cand1 = RetrievalCandidate(
        chunk_id=1, document_id=1, title="Doc 1", content="Same exact text about installment plan", final_score=0.95
    )
    cand2 = RetrievalCandidate(
        chunk_id=2, document_id=1, title="Doc 2", content="Same exact text about installment plan", final_score=0.94
    )
    cand3 = RetrievalCandidate(
        chunk_id=3, document_id=2, title="Doc 3", content="Completely different text about billing meter reading", final_score=0.80
    )
    selected = MMRSelector.select([cand1, cand2, cand3], top_k=2, mmr_lambda=0.5, enabled=True)
    assert len(selected) == 2
    selected_ids = {c.chunk_id for c in selected}
    assert 1 in selected_ids
    assert 3 in selected_ids

def test_context_builder():
    cand = RetrievalCandidate(
        chunk_id=101,
        document_id=55,
        source_id=24,
        title="Creating Installment Plans",
        breadcrumb="Contract Accounts -> Installment Plans",
        url="https://help.sap.com/example",
        content="Step 1: Open transaction FPR1",
        final_score=0.92
    )
    context = ContextBuilder.build_context([cand])
    assert "Creating Installment Plans" in context
    assert "https://help.sap.com/example" in context
    assert "Step 1: Open transaction FPR1" in context

    prompt = ContextBuilder.build_rag_prompt("How to create installment plan?", [cand])
    assert "STRICT RAG CONSTRAINTS" in prompt
    assert "How to create installment plan?" in prompt
