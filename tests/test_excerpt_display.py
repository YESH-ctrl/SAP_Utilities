"""
Unit and Integration Tests for Retrieved Documentation Excerpt Display and Schema Integrity (V5.5.1).
"""

import pytest
from sap_rag.retrieval.schemas import CandidateResultSchema, SourceCitationSchema
from sap_rag.chat.service import ChatService

def test_source_citation_schema_includes_full_content():
    """Verify SourceCitationSchema carries full content alongside excerpt preview."""
    full_text = "[DOCUMENT]\nReconnection Order Generation\n\n[PATH]\nUtilities > Move-In\n\n[SECTION]\nReconnection\n\n[CONTENT]\nThis is the complete text of the retrieved document chunk explaining reconnection order generation in detail."
    
    cand = CandidateResultSchema(
        chunk_id=7140,
        document_id=10,
        source_id=10,
        title="Reconnection Order Generation",
        url="https://help.sap.com/utilities",
        breadcrumb="Utilities > Move-In",
        content=full_text,
        score=0.95,
        retrieval_method="RRF + H1"
    )

    chat_service = ChatService()
    sources = chat_service.extract_unique_sources([cand])

    assert len(sources) == 1
    src = sources[0]
    
    # Content must equal the full chunk text
    assert src.content == full_text
    
    # Excerpt should contain clean body text without raw header prefix
    assert "This is the complete text" in src.excerpt
    assert "[DOCUMENT]" not in src.excerpt

def test_long_excerpt_clean_preview():
    """Verify long text gets a clean preview excerpt while preserving full content."""
    long_body = "word " * 100  # 500 chars
    full_text = f"[DOCUMENT]\nTest Doc\n\n[SECTION]\nGeneral\n\n[CONTENT]\n{long_body}"

    cand = CandidateResultSchema(
        chunk_id=999,
        document_id=50,
        source_id=50,
        title="Test Doc",
        url="https://help.sap.com",
        breadcrumb="Test",
        content=full_text,
        score=0.88,
        retrieval_method="Dense"
    )

    chat_service = ChatService()
    sources = chat_service.extract_unique_sources([cand])
    src = sources[0]

    assert len(src.content) == len(full_text)
    assert src.excerpt.endswith("...")
    assert len(src.excerpt) <= 300

def test_word_boundary_truncation():
    """Verify preview truncation ends cleanly at word boundaries and does not slice mid-word."""
    chat_service = ChatService()
    text = "The process of contacting a customer for this purpose is called notification and must be documented carefully."
    smart = chat_service.build_smart_excerpt(text, max_chars=60)
    
    assert smart.endswith("...")
    assert smart.endswith("purpose is...") or smart.endswith("customer...") or smart.endswith("notification...")
    # Ensure no sliced word like 'is cal...' or 'notificationa...'
    assert not smart.endswith("cal...")
    assert not smart.endswith("an...")

def test_unicode_artifact_cleaning():
    """Verify Private Use Area Unicode characters (e.g. U+E088 glyphs) are stripped cleanly."""
    chat_service = ChatService()
    dirty_path = "Disconnection/Reconnection > Integration\ue088 > Reconnection Order"
    clean_path = chat_service.clean_unicode_artifacts(dirty_path)
    
    assert clean_path == "Disconnection/Reconnection > Integration > Reconnection Order"
    assert "\ue088" not in clean_path

