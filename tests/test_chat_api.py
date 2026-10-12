"""
API & Chat integration tests for SAP Utilities RAG Pipeline (Release V5.5.1 Integration Layer).
Uses FastAPI TestClient to test endpoints without requiring external network calls.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app
from sap_rag.retrieval.schemas import CandidateResultSchema
from sap_rag.chat.service import ConversationStore, ChatService
from sap_rag.llm.service import LLMService, NO_CONTEXT_FALLBACK

client = TestClient(app)

@pytest.fixture
def mock_candidate():
    return CandidateResultSchema(
        chunk_id=101,
        document_id=12,
        section_id=3,
        source_id=1,
        title="Reconnection in SAP Utilities",
        url="https://help.sap.com/utilities/reconnection",
        breadcrumb="IS-U > Customer Service > Reconnection",
        content="To perform a reconnection in SAP Utilities, open transaction EC30 or process the reconnection order.",
        score=0.92,
        retrieval_method="hybrid_rrf",
        scores_breakdown={"dense_rank": 1, "lexical_rank": 2}
    )

def test_01_health_endpoint():
    """Test GET /api/v1/retrieval/health endpoint."""
    with patch("sap_rag.api.retrieval_router.DatabasePool.acquire") as mock_acquire:
        mock_conn = AsyncMock()
        mock_conn.fetchval.side_effect = [6689, 6689]
        mock_acquire.return_value.__aenter__.return_value = mock_conn

        response = client.get("/api/v1/retrieval/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_chunks"] == 6689
        assert data["database_vectors"] == 6689

def test_02_retrieval_query_endpoint(mock_candidate):
    """Test POST /api/v1/retrieval/query endpoint."""
    with patch("sap_rag.api.retrieval_router.DatabasePool.acquire") as mock_acquire, \
         patch("sap_rag.api.retrieval_router.pipeline_instance.execute") as mock_execute:

        mock_conn = AsyncMock()
        mock_acquire.return_value.__aenter__.return_value = mock_conn

        from sap_rag.retrieval.retrieval_pipeline import RetrievalMetrics
        metrics = RetrievalMetrics(total_latency_ms=120.0, candidate_count=1)

        # Mock candidate object using MagicMock for synchronous method calls
        from unittest.mock import MagicMock
        mock_candidate_obj = MagicMock()
        mock_candidate_obj.chunk_id = mock_candidate.chunk_id
        mock_candidate_obj.document_id = mock_candidate.document_id
        mock_candidate_obj.section_id = mock_candidate.section_id
        mock_candidate_obj.source_id = mock_candidate.source_id
        mock_candidate_obj.title = mock_candidate.title
        mock_candidate_obj.url = mock_candidate.url
        mock_candidate_obj.breadcrumb = mock_candidate.breadcrumb
        mock_candidate_obj.content = mock_candidate.content
        mock_candidate_obj.final_score = mock_candidate.score
        mock_candidate_obj.retrieval_method = mock_candidate.retrieval_method
        mock_candidate_obj.to_summary_dict.return_value = {
            "scores_breakdown": mock_candidate.scores_breakdown
        }

        from sap_rag.retrieval.models import ProcessedQuery
        mock_execute.return_value = ([mock_candidate_obj], "Context string", ProcessedQuery(original_query="reconnection", cleaned_query="reconnection", normalized_query="reconnection"), metrics)

        payload = {"query": "How do I perform a reconnection?", "top_k": 5}
        response = client.post("/api/v1/retrieval/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "How do I perform a reconnection?"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Reconnection in SAP Utilities"

def test_03_invalid_and_empty_queries():
    """Test error handling for empty or whitespace queries."""
    res1 = client.post("/api/v1/retrieval/query", json={"query": ""})
    assert res1.status_code in (400, 422)

    res2 = client.post("/api/v1/chat", json={"message": "   "})
    assert res2.status_code in (400, 422)

def test_04_chat_endpoint_grounded_answer(mock_candidate):
    """Test POST /api/v1/chat endpoint with grounded answer generation."""
    with patch("sap_rag.api.chat_router.DatabasePool.acquire") as mock_acquire, \
         patch.object(ChatService, "process_chat") as mock_process:

        mock_conn = AsyncMock()
        mock_acquire.return_value.__aenter__.return_value = mock_conn

        from sap_rag.retrieval.schemas import ChatResponse, ChatMessageSchema, SourceCitationSchema
        mock_process.return_value = ChatResponse(
            conversation_id="conv-12345",
            message=ChatMessageSchema(role="assistant", content="To perform reconnection, use EC30."),
            sources=[
                SourceCitationSchema(
                    title=mock_candidate.title,
                    document_id=mock_candidate.document_id,
                    source_id=mock_candidate.source_id,
                    url=mock_candidate.url,
                    excerpt=mock_candidate.content,
                    score=mock_candidate.score
                )
            ],
            metadata={"retrieval_version": "5.5.1", "total_latency_ms": 150.0}
        )

        payload = {"message": "How do I perform a reconnection?"}
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv-12345"
        assert "EC30" in data["message"]["content"]
        assert len(data["sources"]) == 1
        assert data["sources"][0]["title"] == "Reconnection in SAP Utilities"

def test_05_conversation_history_truncation():
    """Test ConversationStore bounds message history size."""
    store = ConversationStore(max_messages=4)
    conv_id = "test-conv"

    for i in range(10):
        store.add_message(conv_id, "user", f"Question {i}")
        store.add_message(conv_id, "assistant", f"Answer {i}")

    history = store.get_history(conv_id)
    assert len(history) == 4
    assert history[0]["content"] == "Question 8"
    assert history[-1]["content"] == "Answer 9"

def test_06_no_context_fallback():
    """Test LLM service fallback when context is insufficient."""
    llm = LLMService()

    # Empty candidate list
    ans = llm._generate_synthesizer("random query", [])
    assert ans == NO_CONTEXT_FALLBACK

def test_07_cors_headers():
    """Test CORS headers configuration."""
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"

def test_08_openapi_documentation():
    """Test OpenAPI schema availability."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/api/v1/retrieval/query" in schema["paths"]
    assert "/api/v1/chat" in schema["paths"]
    assert "/api/v1/retrieval/health" in schema["paths"]
