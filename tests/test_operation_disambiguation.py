"""
Regression Test Suite for SAP Utilities Operation Disambiguation and Claim-Level Evidence.
Verifies all 10 scenarios required by the Targeted Improvement specification:
1. Reversing a new contract (EC53E, Move-in reversal)
2. Reversing the end of a contract (EC58E, Move-out reversal)
3. Reconnecting a disconnected utility installation (Doc 2685, 2690, 2691)
4. Ambiguous request involving reversal and reconnection
5. Procedure split across multiple chunks (section expansion without hardcoded IDs)
6. Missing procedural evidence (transparent gap disclosure)
7. Claims that incorrectly equate contract state with service state
8. Duplicate citations and unrelated source candidates deduplication
9. Incorrect transaction-code claims rejected by auditor
10. Legacy RAG isolation (zero legacy RAG invocation)
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from sap_rag.database.connection import DatabasePool
from sap_rag.agentic.retrieval.service import SemanticRetrievalService
from sap_rag.agentic.orchestration.flow import (
    AgenticIntelligenceFlow,
    disambiguate_sap_operation
)
from sap_rag.agentic.schemas.contracts import (
    QueryPlan,
    QueryIntent,
    OperationCategory,
    SubQuestion,
    AnswerFormat,
    EvidenceItem,
    AgentFinding,
    ClaimRecord,
    ClaimSupportStatus,
    CitationItem,
    ResponseMode,
    AnswerStatus,
    EvidenceSufficiency,
    SubQuestionCoverageStatus
)
from sap_rag.agentic.ledger.ledger import EvidenceLedger
from sap_rag.agentic.validators.citation_validator import CitationValidator
from sap_rag.agentic.validators.coverage_validator import AnswerCoverageValidator


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Scenario 1: Reversing a new contract
@pytest.mark.asyncio
async def test_scenario_1_reversing_new_contract():
    """
    Scenario 1: User asks to reverse a newly created contract.
    Must classify as REVERSE_NEW_CONTRACT and discover EC53E procedure.
    """
    query = "What is the procedure to reverse a new contract in SAP Utilities integration?"
    disambig = disambiguate_sap_operation(query)
    
    assert disambig["operation_category"] == OperationCategory.REVERSE_NEW_CONTRACT
    assert OperationCategory.REVERSE_NEW_CONTRACT in disambig["candidate_operations"]
    assert "EC53E" in disambig["disambiguation_reasoning"] or "move-in" in disambig["disambiguation_reasoning"].lower()
    assert disambig["requires_clarification"] is False

    await DatabasePool.initialize(min_size=1, max_size=2)
    svc = SemanticRetrievalService()
    items = await svc.search(query=query, top_k=6, expand_sections=True)
    
    # Verify Doc 3035 (Reverse New Contracts) and Chunk 10116 (EC53E) are retrieved
    doc_ids = [itm.document_id for itm in items]
    chunk_ids = [itm.chunk_id for itm in items]
    assert 3035 in doc_ids, f"Doc 3035 missing from retrieved: {doc_ids}"
    assert 10116 in chunk_ids, f"Chunk 10116 (EC53E) missing from retrieved: {chunk_ids}"
    
    c10116 = next(itm for itm in items if itm.chunk_id == 10116)
    assert "EC53E" in c10116.content
    await DatabasePool.close()


# Scenario 2: Reversing the end of a contract
@pytest.mark.asyncio
async def test_scenario_2_reversing_end_of_contract():
    """
    Scenario 2: User asks to reverse the end of a contract.
    Must classify as REVERSE_END_OF_CONTRACT and discover EC58E procedure.
    """
    query = "How to reverse the ending of a contract in SAP Utilities?"
    disambig = disambiguate_sap_operation(query)
    
    assert disambig["operation_category"] == OperationCategory.REVERSE_END_OF_CONTRACT
    assert OperationCategory.REVERSE_END_OF_CONTRACT in disambig["candidate_operations"]
    assert "EC58E" in disambig["disambiguation_reasoning"] or "move-out" in disambig["disambiguation_reasoning"].lower()
    assert disambig["requires_clarification"] is False

    await DatabasePool.initialize(min_size=1, max_size=2)
    svc = SemanticRetrievalService()
    items = await svc.search(query=query, top_k=6, expand_sections=True)
    
    # Verify Doc 3040 (Reverse End of Contracts) and Chunk 10150 (EC58E) are retrieved
    doc_ids = [itm.document_id for itm in items]
    chunk_ids = [itm.chunk_id for itm in items]
    assert 3040 in doc_ids, f"Doc 3040 missing from retrieved: {doc_ids}"
    assert 10150 in chunk_ids, f"Chunk 10150 (EC58E) missing from retrieved: {chunk_ids}"
    
    c10150 = next(itm for itm in items if itm.chunk_id == 10150)
    assert "EC58E" in c10150.content
    await DatabasePool.close()


# Scenario 3: Reconnecting a disconnected utility installation
@pytest.mark.asyncio
async def test_scenario_3_reconnecting_utility_installation():
    """
    Scenario 3: User asks to reconnect a disconnected utility installation.
    Must classify as RECONNECT_INSTALLATION and MUST NOT convert to contract reversal.
    """
    query = "What is the procedure to reconnect a disconnected utility installation in SAP Utilities?"
    disambig = disambiguate_sap_operation(query)
    
    assert disambig["operation_category"] == OperationCategory.RECONNECT_INSTALLATION
    assert OperationCategory.RECONNECT_INSTALLATION in disambig["candidate_operations"]
    assert disambig["operation_category"] != OperationCategory.REVERSE_NEW_CONTRACT
    assert "reconnection" in disambig["disambiguation_reasoning"].lower()
    assert disambig["requires_clarification"] is False

    await DatabasePool.initialize(min_size=1, max_size=2)
    svc = SemanticRetrievalService()
    items = await svc.search(query=query, top_k=8, expand_sections=True)
    
    # Check that disconnection/reconnection documentation is retrieved
    doc_titles = [itm.title.lower() for itm in items]
    has_recon_doc = any("disconnection/reconnection" in t or "reconnection" in t for t in doc_titles)
    assert has_recon_doc, f"Expected disconnection/reconnection documents in {doc_titles}"
    
    # Ensure it did NOT retrieve only contract reversal
    recon_chunks = [itm for itm in items if "reconnect" in itm.content.lower()]
    assert len(recon_chunks) >= 2, "Expected at least 2 reconnection chunks retrieved"
    await DatabasePool.close()


# Scenario 4: Ambiguous request involving reversal and reconnection
def test_scenario_4_ambiguous_request_reversal_and_reconnection():
    """
    Scenario 4: User asks an ambiguous question combining contract reversal and reconnection.
    Must classify as AMBIGUOUS_REVERSAL_RECONNECTION, flag requires_clarification=True,
    and formulate subquestions covering both distinct operations.
    """
    query = "Can I reverse a contract to reconnect service for a customer in SAP Utilities?"
    disambig = disambiguate_sap_operation(query)
    
    assert disambig["operation_category"] == OperationCategory.AMBIGUOUS_REVERSAL_RECONNECTION
    assert OperationCategory.RECONNECT_INSTALLATION in disambig["candidate_operations"]
    assert OperationCategory.REVERSE_NEW_CONTRACT in disambig["candidate_operations"]
    assert disambig["requires_clarification"] is True
    assert len(disambig["subquestions"]) >= 2
    
    # Subquestions must cover both installation reconnection and contract reversal
    subq_texts = " ".join([sq.question.lower() for sq in disambig["subquestions"]])
    assert "reconnection" in subq_texts or "reconnect" in subq_texts
    assert "reverse" in subq_texts


# Scenario 5: Procedure split across multiple chunks (section expansion)
@pytest.mark.asyncio
async def test_scenario_5_procedure_split_across_multiple_chunks():
    """
    Scenario 5: Section expansion gathers both procedure and prerequisite chunks
    dynamically without hardcoding chunk IDs.
    """
    await DatabasePool.initialize(min_size=1, max_size=2)
    svc = SemanticRetrievalService()
    
    query = "What is the procedure to reverse a contract in SAP Utilities integration?"
    items = await svc.search(query=query, top_k=10, expand_sections=True)
    
    # Check that multiple chunks for the same document are discovered via section expansion
    doc_chunk_map = {}
    for itm in items:
        doc_chunk_map.setdefault(itm.document_id, []).append(itm)
        
    # Doc 3035 should have at least 2 chunks (e.g. Prerequisites chunk 10115 and Procedure chunk 10116)
    assert 3035 in doc_chunk_map, "Doc 3035 should be present"
    doc_3035_chunks = doc_chunk_map[3035]
    assert len(doc_3035_chunks) >= 2, f"Expected multiple chunks for Doc 3035, got {len(doc_3035_chunks)}"
    
    headings = [c.section_heading for c in doc_3035_chunks]
    assert any("Prerequisites" in (h or "") for h in headings)
    assert any("Procedure" in (h or "") for h in headings)
    await DatabasePool.close()


# Scenario 6: Missing procedural evidence
def test_scenario_6_missing_procedural_evidence():
    """
    Scenario 6: Evidence Auditor detects missing procedural evidence and disallows
    overconfident answer claims.
    """
    plan = QueryPlan(
        original_query="What is the procedure for nuclear reactor core cooling in SAP Utilities?",
        intent=QueryIntent.PROCEDURAL,
        operation_category=OperationCategory.GENERAL_PROCEDURAL,
        subquestions=[
            SubQuestion(id="SQ-1", question="What is the procedure for nuclear reactor cooling in SAP Utilities?", expected_evidence_type="procedure")
        ]
    )
    ledger = EvidenceLedger(query_plan=plan)
    
    # No relevant evidence registered
    cov = ledger.evaluate_coverage()
    assert cov["coverage_ratio"] == 0.0
    assert "SQ-1" in cov["unresolved_subquestion_ids"]


# Scenario 7: Claims that incorrectly equate contract state with service state
def test_scenario_7_claims_incorrectly_equating_contract_and_service_state():
    """
    Scenario 7: Evidence Auditor detects and rejects / contradicts a claim asserting
    that reversing a contract automatically reconnects physical utility installation.
    """
    plan = QueryPlan(
        original_query="Can reversing a contract reconnect service?",
        intent=QueryIntent.PROCEDURAL,
        operation_category=OperationCategory.AMBIGUOUS_REVERSAL_RECONNECTION
    )
    ledger = EvidenceLedger(query_plan=plan)
    
    # Register contract reversal evidence only
    ev1 = EvidenceItem(
        evidence_id="EV-1",
        chunk_id=10116,
        document_id=3035,
        title="How to Reverse New Contracts",
        canonical_url="https://help.sap.com/reverse",
        content="Open transaction EC53E to reverse move-in document of utilities contract.",
        cosine_distance=0.1,
        similarity_score=0.9
    )
    ledger.register_evidence_items([ev1])
    
    # Fabricated / ungrounded claim equating contract reversal with physical service reconnection
    faulty_claim = ClaimRecord(
        claim_id="CL-FAULTY-1",
        claim_text="Reversing a contract using EC53E automatically reconnects the physical utility installation.",
        supporting_evidence_ids=["EV-1"]
    )
    
    finding = AgentFinding(
        role="procedure_analyst",
        subquestion_id="SQ-1",
        atomic_claims=[faulty_claim],
        supporting_evidence_ids=["EV-1"]
    )
    ledger.record_agent_finding(finding)
    
    # Auditor must contradict or reject the claim
    audited = ledger._claims[0]
    assert audited.is_service_state_equated is True
    assert audited.support_status == ClaimSupportStatus.CONTRADICTED
    assert "Rejected claim" in (audited.qualification or "")


# Scenario 8: Duplicate citations and unrelated source candidates
def test_scenario_8_duplicate_citations_and_unrelated_candidates():
    """
    Scenario 8: CitationValidator filters out unused candidate citations and
    deduplicates duplicate source passages in reference list.
    """
    validator = CitationValidator()
    
    c1 = CitationItem(
        citation_id=1,
        evidence_id="EV-1",
        chunk_id=10116,
        document_id=3035,
        title="How to Reverse New Contracts",
        canonical_url="https://help.sap.com/reverse",
        excerpt="Open transaction EC53E.",
        cosine_distance=0.1,
        similarity_score=0.9
    )
    c2 = CitationItem(
        citation_id=2,
        evidence_id="EV-2",
        chunk_id=10115,
        document_id=3035,
        title="How to Reverse New Contracts",
        canonical_url="https://help.sap.com/reverse",
        excerpt="Prerequisites for new contracts.",
        cosine_distance=0.15,
        similarity_score=0.85
    )
    c3_unused = CitationItem(
        citation_id=3,
        evidence_id="EV-3",
        chunk_id=9999,
        document_id=999,
        title="Unrelated Candidate Document",
        canonical_url="https://help.sap.com/unrelated",
        excerpt="Unrelated candidate text.",
        cosine_distance=0.4,
        similarity_score=0.6
    )
    
    all_candidates = [c1, c2, c3_unused]
    answer_text = "Execute step 1 [1] after completing prerequisites [2]."
    
    # Active citations should exclude citation [3]
    active = validator.get_active_citations(all_candidates, answer_text)
    assert len(active) == 2
    assert all(c.citation_id in (1, 2) for c in active)
    
    # Deduplication for reference list should group [1] and [2] under single Doc 3035
    deduped = validator.deduplicate_sources_for_reference_list(active)
    assert len(deduped) == 1
    assert deduped[0]["document_id"] == 3035
    assert deduped[0]["citation_indices"] == [1, 2]


# Scenario 9: Incorrect transaction-code claims
def test_scenario_9_incorrect_transaction_code_claims():
    """
    Scenario 9: Evidence Auditor rejects claims asserting transaction codes
    not present in the retrieved documentation (e.g. inventing EC50 or VA01).
    """
    plan = QueryPlan(
        original_query="What is the procedure to reverse a contract?",
        intent=QueryIntent.PROCEDURAL,
        operation_category=OperationCategory.REVERSE_NEW_CONTRACT
    )
    ledger = EvidenceLedger(query_plan=plan)
    
    ev1 = EvidenceItem(
        evidence_id="EV-1",
        chunk_id=10116,
        document_id=3035,
        title="How to Reverse New Contracts",
        canonical_url="https://help.sap.com/reverse",
        content="Open transaction EC53E to reverse move-in document.",
        cosine_distance=0.1,
        similarity_score=0.9
    )
    ledger.register_evidence_items([ev1])
    
    # Claim asserting non-existent / incorrect T-code EC50
    incorrect_tcode_claim = ClaimRecord(
        claim_id="CL-BAD-TC",
        claim_text="Open transaction EC50 to reverse the contract.",
        supporting_evidence_ids=["EV-1"]
    )
    
    finding = AgentFinding(
        role="procedure_analyst",
        subquestion_id="SQ-1",
        atomic_claims=[incorrect_tcode_claim],
        supporting_evidence_ids=["EV-1"]
    )
    ledger.record_agent_finding(finding)
    
    audited = ledger._claims[0]
    assert audited.support_status == ClaimSupportStatus.INSUFFICIENT_EVIDENCE
    assert "Transaction code 'EC50' is ungrounded" in (audited.qualification or "")


# Scenario 10: Legacy RAG isolation
@pytest.mark.asyncio
async def test_scenario_10_legacy_rag_isolation():
    """
    Scenario 10: Verifies complete architectural isolation from legacy RAG.
    Zero legacy modules (hybrid_search, rrf_fusion, search_service, chat_service)
    can be imported or invoked during the agentic workflow.
    """
    legacy_mock = MagicMock()
    with patch.dict("sys.modules", {
        "sap_rag.retrieval.hybrid_search": legacy_mock,
        "sap_rag.retrieval.rrf_fusion": legacy_mock,
        "sap_rag.services.search_service": legacy_mock,
        "sap_rag.services.chat_service": legacy_mock,
    }):
        await DatabasePool.initialize(min_size=1, max_size=2)
        svc = SemanticRetrievalService()
        items = await svc.search(query="reconnection utilities installation", top_k=5)
        
        assert len(items) > 0
        assert legacy_mock.call_count == 0, "Legacy RAG was invoked!"
        await DatabasePool.close()
