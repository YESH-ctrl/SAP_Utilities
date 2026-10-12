"""
Unit tests for GeminiService & LLM Generation Integration (V5.5.1 Layer).
Uses unittest.mock to test all edge cases without requiring external network calls.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from google.genai.errors import APIError
except ImportError:
    APIError = Exception

from sap_rag.llm.gemini_service import (
    GeminiService,
    GROUNDING_SYSTEM_PROMPT,
    NO_CONTEXT_FALLBACK,
    ERROR_FALLBACK
)
from sap_rag.llm.service import LLMService
from sap_rag.retrieval.schemas import CandidateResultSchema, SourceCitationSchema

@pytest.fixture
def mock_candidates():
    return [
        CandidateResultSchema(
            chunk_id=1,
            document_id=2691,
            section_id=10,
            source_id=29,
            title="Reconnection Entry",
            url="https://help.sap.com/doc/2691",
            breadcrumb="IS-U > Disconnection/Reconnection > Reconnection Entry",
            content="To perform a reconnection entry, execute transaction EC30 in SAP IS-U.",
            score=0.95,
            retrieval_method="hybrid_rrf"
        ),
        CandidateResultSchema(
            chunk_id=2,
            document_id=2685,
            section_id=12,
            source_id=29,
            title="Disconnection/Reconnection of a Utilities Installation",
            url="https://help.sap.com/doc/2685",
            breadcrumb="IS-U > Customer Service > Disconnection/Reconnection",
            content="Disconnection and reconnection of utility installations require an order object.",
            score=0.88,
            retrieval_method="hybrid_rrf"
        )
    ]

# 1. Successful generation
@pytest.mark.asyncio
async def test_01_successful_generation(mock_candidates):
    service = GeminiService(api_key="fake-test-key")

    mock_resp = MagicMock()
    mock_resp.text = "To perform a reconnection in SAP Utilities, use transaction EC30."

    service._client = MagicMock()
    service._client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    ans, meta = await service.generate_answer(
        question="How do I perform the reconnection?",
        retrieved_context=mock_candidates
    )

    assert "EC30" in ans
    assert meta["status"] == "success"
    assert meta["chunks_used"] == 2
    assert meta["generation_ms"] >= 0

# 2. Missing API key
@pytest.mark.asyncio
async def test_02_missing_api_key(mock_candidates):
    service = GeminiService(api_key="")
    assert not service.is_configured()

    ans, meta = await service.generate_answer(
        question="How do I perform reconnection?",
        retrieved_context=mock_candidates
    )

    assert ans == ERROR_FALLBACK
    assert meta["status"] == "unconfigured"

# 3. Invalid API key / Auth error
@pytest.mark.asyncio
async def test_03_invalid_api_key(mock_candidates):
    service = GeminiService(api_key="invalid-key")
    service._client = MagicMock()

    api_err = APIError(401, "Invalid API key", None)
    service._client.aio.models.generate_content = AsyncMock(side_effect=api_err)

    ans, meta = await service.generate_answer(
        question="How do I perform reconnection?",
        retrieved_context=mock_candidates
    )

    assert ans == ERROR_FALLBACK
    assert meta["status"] == "api_error"

# 4. Gemini timeout
@pytest.mark.asyncio
async def test_04_gemini_timeout(mock_candidates):
    service = GeminiService(api_key="fake-key")
    service._client = MagicMock()

    service._client.aio.models.generate_content = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))

    ans, meta = await service.generate_answer(
        question="How do I perform reconnection?",
        retrieved_context=mock_candidates
    )

    assert ans == ERROR_FALLBACK
    assert meta["status"] == "error"

# 5. Gemini API failure
@pytest.mark.asyncio
async def test_05_gemini_api_failure(mock_candidates):
    service = GeminiService(api_key="fake-key")
    service._client = MagicMock()

    service._client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("Internal Server Error 500"))

    ans, meta = await service.generate_answer(
        question="How do I perform reconnection?",
        retrieved_context=mock_candidates
    )

    assert ans == ERROR_FALLBACK
    assert meta["status"] == "error"

# 6. Empty response / Safety block
@pytest.mark.asyncio
async def test_06_empty_response(mock_candidates):
    service = GeminiService(api_key="fake-key")
    service._client = MagicMock()

    mock_resp = MagicMock()
    mock_resp.text = ""
    service._client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    ans, meta = await service.generate_answer(
        question="How do I perform reconnection?",
        retrieved_context=mock_candidates
    )

    assert ans == ERROR_FALLBACK
    assert meta["status"] in ("empty_response", "error", "api_error")

# 7. Retrieved context passed correctly to Gemini
@pytest.mark.asyncio
async def test_07_retrieved_context_passed_correctly(mock_candidates):
    service = GeminiService(api_key="fake-key")
    service._client = MagicMock()

    mock_generate = AsyncMock(return_value=MagicMock(text="Grounded answer"))
    service._client.aio.models.generate_content = mock_generate

    await service.generate_answer(
        question="What is EC30?",
        retrieved_context=mock_candidates
    )

    assert mock_generate.called
    kwargs = mock_generate.call_args.kwargs
    contents = kwargs["contents"]

    assert "Reconnection Entry" in contents
    assert "execute transaction EC30" in contents
    assert "Disconnection/Reconnection of a Utilities Installation" in contents
    assert kwargs["config"].system_instruction == GROUNDING_SYSTEM_PROMPT

# 8. Conversation history passed correctly
@pytest.mark.asyncio
async def test_08_conversation_history_passed_correctly(mock_candidates):
    service = GeminiService(api_key="fake-key")
    service._client = MagicMock()

    mock_generate = AsyncMock(return_value=MagicMock(text="Answer with history"))
    service._client.aio.models.generate_content = mock_generate

    history = [
        {"role": "user", "content": "What is reconnection?"},
        {"role": "assistant", "content": "Reconnection is restoring service after disconnection."}
    ]

    await service.generate_answer(
        question="What are the prerequisites?",
        retrieved_context=mock_candidates,
        conversation_history=history
    )

    contents = mock_generate.call_args.kwargs["contents"]
    assert "PREVIOUS CONVERSATION:" in contents
    assert "What is reconnection?" in contents
    assert "restoring service" in contents

# 9. Context truncation / Context budget
@pytest.mark.asyncio
async def test_09_context_truncation(mock_candidates):
    service = GeminiService(api_key="fake-key", max_context_chunks=1, max_context_chars=100)

    formatted, count = service.format_grounding_context(mock_candidates)
    assert count == 1
    assert "Reconnection Entry" in formatted
    assert "Disconnection/Reconnection of a Utilities Installation" not in formatted

# 10. No retrieval -> no hallucinated answer
@pytest.mark.asyncio
async def test_10_no_retrieval_no_hallucination():
    service = GeminiService(api_key="fake-key")

    ans, meta = await service.generate_answer(
        question="What is transaction XYZ?",
        retrieved_context=[]
    )

    assert ans == NO_CONTEXT_FALLBACK
    assert meta["status"] == "no_context"

# 11. Source metadata remains retrieval-owned
def test_11_source_metadata_retrieval_owned(mock_candidates):
    from sap_rag.chat.service import ChatService
    chat_svc = ChatService()

    sources = chat_svc.extract_unique_sources(mock_candidates)
    assert len(sources) == 2
    assert sources[0].rank == 1
    assert sources[0].document_id == 2691
    assert sources[0].title == "Reconnection Entry"
    assert sources[1].rank == 2
    assert sources[1].document_id == 2685

# 12. API Response Schema
@pytest.mark.asyncio
async def test_12_api_response_schema():
    from sap_rag.retrieval.schemas import ChatResponse, ChatMessageSchema, SourceCitationSchema
    resp = ChatResponse(
        conversation_id="conv-123",
        message=ChatMessageSchema(role="assistant", content="Answer"),
        sources=[SourceCitationSchema(title="Title", document_id=1, url="http://example.com")],
        metadata={
            "retrieval_version": "5.5.1",
            "retrieval_latency_ms": 10.0,
            "generation_latency_ms": 20.0,
            "total_latency_ms": 30.0
        }
    )
    assert resp.conversation_id == "conv-123"
    assert resp.metadata["retrieval_version"] == "5.5.1"
