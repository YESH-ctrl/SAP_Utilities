"""
Unit tests for the SAP Utilities Semantic Chunking Engine.
"""

import pathlib
import pytest
from sap_rag.chunking.tokenizer import SemanticTokenizer
from sap_rag.chunking.normalizer import TextNormalizer
from sap_rag.chunking.structural_parser import StructuralParser, BlockType
from sap_rag.chunking.semantic_chunker import SemanticChunker
from sap_rag.chunking.breadcrumb import BreadcrumbBuilder
from sap_rag.chunking.validators import ChunkValidator

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"

@pytest.fixture
def tokenizer():
    return SemanticTokenizer.get_instance()

@pytest.fixture
def chunker(tokenizer):
    return SemanticChunker(tokenizer=tokenizer)

def test_text_normalizer_markdown_table():
    fixture_path = FIXTURES_DIR / "fixture_table.md"
    content = fixture_path.read_text(encoding="utf-8")
    
    normalized = TextNormalizer.normalize_section_content(content)
    assert "TABLE:" in normalized
    assert "Field Name: Contract Account" in normalized or "Contract Account" in normalized
    assert "VKONT" in normalized

def test_procedure_preservation():
    fixture_path = FIXTURES_DIR / "fixture_procedure.md"
    content = fixture_path.read_text(encoding="utf-8")
    
    blocks = StructuralParser.parse_section(content)
    proc_blocks = [b for b in blocks if b.block_type == BlockType.PROCEDURE]
    assert len(proc_blocks) >= 1
    assert "1. Choose Utilities Industry" in proc_blocks[0].content
    assert "5. Save the generated" in proc_blocks[0].content

def test_note_preservation():
    fixture_path = FIXTURES_DIR / "fixture_procedure.md"
    content = fixture_path.read_text(encoding="utf-8")
    
    blocks = StructuralParser.parse_section(content)
    note_blocks = [b for b in blocks if b.block_type == BlockType.NOTE]
    assert len(note_blocks) >= 1
    assert "NOTE:" in note_blocks[0].content

def test_small_section_kept_intact(chunker):
    doc_info = {
        "id": 101,
        "title": "SAP Utilities Billing Procedure",
        "url": "https://help.sap.com/utilities/billing",
        "canonical_url": "https://help.sap.com/utilities/billing",
        "source_pdf": "SAP_Utilities_Billing.pdf",
        "root_document_id": 1,
        "parent_id": None,
        "depth": 1
    }
    section = {
        "id": 501,
        "heading": "Prerequisites",
        "content": "Before running automatic billing, ensure meter readings are validated and open items are cleared."
    }
    breadcrumb = "SAP Utilities > Billing > Prerequisites"
    
    chunks = chunker.chunk_section(doc_info, section, breadcrumb)
    assert len(chunks) == 1
    chk = chunks[0]
    assert chk["section_id"] == 501
    assert chk["chunk_index"] == 0
    assert "[DOCUMENT]" in chk["content"]
    assert "[PATH]" in chk["content"]
    assert "[SECTION]" in chk["content"]
    assert chk["token_count"] > 0
    assert len(chk["content_hash"]) == 64

def test_large_section_splitting_and_overlap(chunker):
    fixture_path = FIXTURES_DIR / "fixture_large_section.md"
    content = fixture_path.read_text(encoding="utf-8")
    
    doc_info = {
        "id": 102,
        "title": "Meter Reading Estimation",
        "url": "https://help.sap.com/utilities/estimation",
        "canonical_url": "https://help.sap.com/utilities/estimation",
        "source_pdf": "SAP_Utilities_Meter_Reading.pdf",
        "root_document_id": 1,
        "parent_id": 100,
        "depth": 2
    }
    section = {
        "id": 502,
        "heading": "Automatic Estimation Procedure",
        "content": content
    }
    breadcrumb = "SAP Utilities > Meter Reading > Automatic Estimation Procedure"
    
    chunks = chunker.chunk_section(doc_info, section, breadcrumb)
    assert len(chunks) >= 1
    
    # Check validator on generated chunks
    is_valid, errors = ChunkValidator.validate_chunks(chunks)
    assert is_valid, f"Validation failed: {errors}"

def test_deterministic_chunking(chunker):
    doc_info = {
        "id": 103,
        "title": "Deterministic Test",
        "url": "https://help.sap.com/test",
        "canonical_url": "https://help.sap.com/test",
        "source_pdf": "Test.pdf",
        "root_document_id": 1,
        "parent_id": None,
        "depth": 1
    }
    section = {
        "id": 503,
        "heading": "Deterministic Heading",
        "content": "1. Step A\n2. Step B\n3. Step C\n\nTABLE: Data\nField A: Val A"
    }
    breadcrumb = "Test > Deterministic Heading"
    
    run1 = chunker.chunk_section(doc_info, section, breadcrumb)
    run2 = chunker.chunk_section(doc_info, section, breadcrumb)
    
    assert len(run1) == len(run2)
    assert run1[0]["content_hash"] == run2[0]["content_hash"]
    assert run1[0]["content"] == run2[0]["content"]

def test_breadcrumb_builder():
    builder = BreadcrumbBuilder()
    builder.load_documents_map([
        {"id": 1, "parent_id": None, "title": "Root Doc", "source_title": "SAP Utilities Source"},
        {"id": 2, "parent_id": 1, "title": "Child Doc", "source_title": "SAP Utilities Source"},
        {"id": 3, "parent_id": 2, "title": "Grandchild Doc", "source_title": "SAP Utilities Source"}
    ])
    
    bc = builder.build_breadcrumb(3, section_title="Creating Item")
    assert bc == "SAP Utilities Source > Root Doc > Child Doc > Grandchild Doc > Creating Item"
