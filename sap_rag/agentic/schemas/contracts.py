"""
Typed Pydantic Contracts for Independent Agentic Knowledge Intelligence Platform.
Defines strict data schemas for planning, retrieval, specialist analysis,
evidence ledger, deterministic validation, and final synthesized response.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class QueryIntent(str, Enum):
    PROCEDURAL = "procedural"
    CONFIGURATION = "configuration"
    CONCEPTUAL = "conceptual"
    RELATIONSHIP = "relationship"
    TROUBLESHOOTING = "troubleshooting"
    CONFLICT_OR_AMBIGUOUS = "conflict_or_ambiguous"
    GENERAL = "general"


class AnswerFormat(str, Enum):
    ORDERED_STEPS = "ordered_steps"
    STRUCTURED_GUIDE = "structured_guide"
    SPECIFICATION_TABLE = "specification_table"
    DIAGNOSTIC_FLOW = "diagnostic_flow"
    DIRECT_EXPLANATION = "direct_explanation"


class OperationCategory(str, Enum):
    REVERSE_NEW_CONTRACT = "reverse_new_contract"
    REVERSE_END_OF_CONTRACT = "reverse_end_of_contract"
    RECONNECT_INSTALLATION = "reconnect_installation"
    CANCEL_CONTRACT_CHANGE = "cancel_contract_change"
    AMBIGUOUS_REVERSAL_RECONNECTION = "ambiguous_reversal_reconnection"
    GENERAL_PROCEDURAL = "general_procedural"


class SubQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(..., description="Unique subquery identifier e.g. SQ-1")
    question: str = Field(..., description="Targeted subquestion text")
    target_intent: QueryIntent = Field(default=QueryIntent.GENERAL)
    expected_evidence_type: str = Field(default="procedure", description="Type of evidence sought")
    specialist_role: str = Field(default="procedure_analyst", description="Target specialist role")


class QueryPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    original_query: str = Field(..., description="User's original unmodified question")
    intent: QueryIntent = Field(default=QueryIntent.GENERAL, description="Primary detected intent")
    operation_category: OperationCategory = Field(default=OperationCategory.GENERAL_PROCEDURAL, description="Classified SAP operation")
    candidate_operations: List[OperationCategory] = Field(default_factory=list, description="Plausible candidate interpretations")
    disambiguation_reasoning: Optional[str] = Field(default=None, description="Explanation for operation selection or candidate ambiguity")
    requires_clarification: bool = Field(default=False, description="True if materially distinct operations remain plausible without sufficient distinguishing context")
    entities: List[str] = Field(default_factory=list, description="Extracted SAP entities or business objects")
    constraints: List[str] = Field(default_factory=list, description="User constraints e.g. On-Premise, S/4HANA")
    subquestions: List[SubQuestion] = Field(default_factory=list, description="Bounded set of subquestions")
    required_evidence_types: List[str] = Field(default_factory=list, description="Required evidence categories")
    answer_format: AnswerFormat = Field(default=AnswerFormat.ORDERED_STEPS, description="Desired answer structure")
    clarification_flag: bool = Field(default=False, description="True if query is critically ambiguous")
    clarification_reason: Optional[str] = Field(default=None, description="Explanation if clarification is flagged")


class EvidenceItem(BaseModel):
    """
    Direct source-linked evidence hit from pgvector retrieval or graph expansion.
    Preserves exact stable chunk IDs, character offsets, and source metadata.
    """
    model_config = ConfigDict(extra="ignore")
    evidence_id: str = Field(..., description="Unique request-scoped evidence ID e.g. EV-101")
    chunk_id: int = Field(..., description="Stable chunk ID from database")
    document_id: int = Field(..., description="Document ID from database")
    section_id: Optional[int] = Field(default=None, description="Section ID from database")
    source_id: Optional[int] = Field(default=None, description="Source PDF ID from database")
    title: str = Field(..., description="Document or section title")
    canonical_url: str = Field(..., description="Authoritative SAP Help Portal URL")
    section_heading: Optional[str] = Field(default=None, description="Heading of the section")
    section_path: Optional[str] = Field(default=None, description="Breadcrumb or hierarchy path")
    content: str = Field(..., description="Full stored text passage (immutable read-only preservation)")
    clean_body: Optional[str] = Field(default=None, description="Clean body text stripped of metadata tags like [DOCUMENT] or [CONTENT]")
    clean_excerpt: Optional[str] = Field(default=None, description="Safely excerpted sentence-bounded passage without mid-word or structural cuts")
    char_offset_start: int = Field(default=0, description="Start character offset in full chunk")
    char_offset_end: int = Field(default=0, description="End character offset in full chunk")
    is_excerpted: bool = Field(default=False, description="True if passage was excerpted due to size")
    token_count: int = Field(default=0, description="Token count of the passage")
    cosine_distance: float = Field(..., description="Direct pgvector cosine distance (0.0 to 2.0)")
    similarity_score: float = Field(..., description="Derived cosine similarity (1.0 - distance)")
    subquery_id: Optional[str] = Field(default=None, description="Subquestion ID that discovered this hit")
    discovery_method: str = Field(default="vector_direct", description="vector_direct, graph_edge, or parent_context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional verified metadata")


class StageExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED_BY_PROVIDER_QUOTA = "blocked_by_provider_quota"


class ExecutionMechanism(str, Enum):
    LLM_REASONING = "llm_reasoning"
    DETERMINISTIC_RETRIEVAL = "deterministic_retrieval"
    DETERMINISTIC_ASSEMBLY = "deterministic_assembly"
    HEURISTIC_FALLBACK = "heuristic_fallback"
    BYPASSED = "bypassed"


class ResponseMode(str, Enum):
    SYNTHESIZED_ANSWER = "synthesized_answer"
    EVIDENCE_ONLY = "evidence_only"


class AnswerStatus(str, Enum):
    SYNTHESIS_COMPLETED = "synthesis_completed"
    SYNTHESIS_UNAVAILABLE = "synthesis_unavailable"
    SYNTHESIS_DEGRADED = "synthesis_degraded"


class EvidenceSufficiency(str, Enum):
    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ClaimSupportStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ClaimCategory(str, Enum):
    OPERATION_IDENTIFICATION = "operation_identification"
    PRECONDITIONS = "preconditions"
    TRANSACTION_CODES = "transaction_codes"
    ORDERED_STEPS = "ordered_steps"
    EXPECTED_RESULTS = "expected_results"
    VERIFICATION_PROCEDURES = "verification_procedures"
    EXCEPTIONS_AND_LIMITATIONS = "exceptions_and_limitations"
    GENERAL = "general"


class ClaimRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_id: str = Field(..., description="Unique claim identifier e.g. CL-1")
    claim_text: str = Field(..., description="Atomic claim asserted by an analyst or synthesized answer")
    claim_category: str = Field(default="general", description="operation_identification, preconditions, transaction_codes, ordered_steps, expected_results, verification_procedures, exceptions_and_limitations")
    support_status: ClaimSupportStatus = Field(default=ClaimSupportStatus.SUPPORTED)
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="List of evidence_ids supporting this claim")
    contradictory_evidence_ids: List[str] = Field(default_factory=list, description="List of evidence_ids contradicting this claim")
    qualification: Optional[str] = Field(default=None, description="Caveat, assumption, or uncertainty note")
    is_service_state_equated: bool = Field(default=False, description="Flag indicating if claim improperly equates commercial contract state with physical service state")


class SubQuestionCoverageStatus(str, Enum):
    ANSWERED = "answered"
    PARTIALLY_ANSWERED = "partially_answered"
    NOT_FOUND = "not_found"
    NEEDS_CLARIFICATION = "needs_clarification"


class SubQuestionCoverage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    subquestion_id: str = Field(..., description="Subquestion ID e.g. SQ-1")
    question: str = Field(..., description="Subquestion text")
    status: SubQuestionCoverageStatus = Field(default=SubQuestionCoverageStatus.ANSWERED, description="Coverage status")
    explanation: Optional[str] = Field(default=None, description="Detailed coverage assessment or reason if ungrounded")


class AgentFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str = Field(..., description="Specialist agent role name")
    subquestion_id: str = Field(..., description="Subquestion assigned to this agent")
    atomic_claims: List[ClaimRecord] = Field(default_factory=list, description="Extracted atomic claims")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="All supporting evidence IDs")
    conflicting_evidence_ids: List[str] = Field(default_factory=list, description="Conflicting evidence IDs observed")
    unknowns_or_gaps: List[str] = Field(default_factory=list, description="Unresolved elements for this subquestion")
    execution_status: str = Field(default="completed", description="succeeded, partial, failed, skipped, blocked_by_provider_quota")
    error_message: Optional[str] = Field(default=None)


class CitationVerification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    citation_index: int = Field(...)
    evidence_id: str = Field(...)
    chunk_id: int = Field(...)
    document_id: int = Field(...)
    title: str = Field(...)
    canonical_url: str = Field(...)
    quoted_text: str = Field(...)
    is_verified_in_evidence: bool = Field(default=True)
    is_exact_substring_match: bool = Field(default=True)


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    citation_integrity: bool = Field(default=True, description="True if every citation references a real retrieved evidence item")
    citation_integrity_ratio: float = Field(default=1.0, description="Fraction of emitted citations resolving to valid evidence (0.0 - 1.0)")
    verified_citations: List[CitationVerification] = Field(default_factory=list)
    invalid_citations: List[str] = Field(default_factory=list, description="Any ungrounded or fabricated citations")
    claim_support_rate: Optional[float] = Field(default=None, description="Ratio of verified supported claims; None in evidence_only mode")
    question_coverage_rate: Optional[float] = Field(default=None, description="Ratio of subquestions addressed; None in evidence_only mode")
    evidence_sufficiency: str = Field(default="partial", description="sufficient, partial, or insufficient")
    synthesis_status: str = Field(default="synthesis_completed", description="synthesis_completed, synthesis_unavailable, synthesis_degraded")
    unanswered_subquestions: List[str] = Field(default_factory=list, description="Subquestions with insufficient corpus evidence")
    subquestion_coverage_details: List[SubQuestionCoverage] = Field(default_factory=list, description="Coverage breakdown for every subquestion")
    detected_contradictions: List[str] = Field(default_factory=list, description="Contradictions noted in documentation")
    repair_attempts: int = Field(default=0, description="Number of bounded repair attempts executed (max 1)")
    overall_status: str = Field(default="verified", description="verified, qualified, unverified, or evidence_only")
    notes: Optional[str] = Field(default=None)

    def validate_invariants(self, response_mode: Union[str, ResponseMode]) -> None:
        """
        Enforce server-side consistency invariants.
        Rejects internally contradictory validation states.
        """
        mode_val = response_mode.value if hasattr(response_mode, "value") else str(response_mode)
        if mode_val == ResponseMode.EVIDENCE_ONLY.value:
            if self.claim_support_rate is not None:
                raise ValueError("claim_support_rate must be None in evidence_only mode (no claims synthesized)")
            if self.question_coverage_rate is not None:
                raise ValueError("question_coverage_rate must be None in evidence_only mode (no answer synthesized)")
            if self.overall_status not in ("evidence_only", "qualified", "unverified"):
                raise ValueError(f"overall_status cannot be '{self.overall_status}' in evidence_only mode")
        elif mode_val == ResponseMode.SYNTHESIZED_ANSWER.value:
            if self.claim_support_rate is None:
                raise ValueError("claim_support_rate must be a float in synthesized_answer mode")
            if self.unanswered_subquestions and self.question_coverage_rate is not None and self.question_coverage_rate >= 1.0:
                raise ValueError("question_coverage_rate cannot be 1.0 when unanswered subquestions exist")
            if self.claim_support_rate is not None and (self.claim_support_rate < 0.0 or self.claim_support_rate > 1.0):
                raise ValueError(f"claim_support_rate out of bounds: {self.claim_support_rate}")


class StageStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stage_name: str = Field(...)
    status: str = Field(..., description="succeeded, partial, failed, skipped, blocked_by_provider_quota")
    mechanism: str = Field(default="deterministic_assembly", description="llm_reasoning, deterministic_retrieval, deterministic_assembly, heuristic_fallback, bypassed")
    latency_ms: float = Field(default=0.0)
    details: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


class RetrievalDiagnostics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    total_candidates_retrieved: int = Field(default=0)
    unique_chunks_used: int = Field(default=0)
    graph_expanded_count: int = Field(default=0)
    min_cosine_distance: float = Field(default=0.0)
    max_cosine_distance: float = Field(default=0.0)
    vector_search_latency_ms: float = Field(default=0.0)
    graph_traversal_latency_ms: float = Field(default=0.0)
    context_tokens_used: int = Field(default=0)
    context_budget_limit: int = Field(default=8192)


class CitationItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    citation_id: int = Field(..., description="Numbered reference index e.g. [1]")
    evidence_id: str = Field(..., description="Reference to EvidenceItem")
    chunk_id: int = Field(...)
    document_id: int = Field(...)
    title: str = Field(...)
    canonical_url: str = Field(...)
    section_heading: Optional[str] = Field(default=None)
    excerpt: str = Field(...)
    cosine_distance: float = Field(...)
    similarity_score: float = Field(...)


class FinalAgenticResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    request_id: str = Field(..., description="Unique request identifier")
    original_query: str = Field(...)
    answer: str = Field(..., description="Synthesized, grounded, single coherent answer, or formatted evidence-only guide")
    citations: List[CitationItem] = Field(default_factory=list, description="Numbered clickable citations")
    evidence_payload: List[EvidenceItem] = Field(default_factory=list, description="Full audited evidence items")
    agent_stage_summary: List[StageStatus] = Field(default_factory=list, description="Completed/failed stages with explicit status and mechanism")
    retrieval_diagnostics: RetrievalDiagnostics = Field(default_factory=RetrievalDiagnostics)
    validation_report: ValidationReport = Field(...)
    execution_status: str = Field(default="success", description="success, partial, error")
    response_mode: str = Field(default="synthesized_answer", description="synthesized_answer or evidence_only")
    answer_status: str = Field(default="synthesis_completed", description="synthesis_completed, synthesis_unavailable, synthesis_degraded")
    evidence_sufficiency: str = Field(default="partial", description="sufficient, partial, insufficient")
    unresolved_gaps: List[str] = Field(default_factory=list)
    total_latency_ms: float = Field(default=0.0)
    token_usage: Dict[str, int] = Field(default_factory=dict)


class AgenticChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str = Field(..., description="User question on SAP Utilities")
    conversation_id: Optional[str] = Field(default=None)
    max_investigation_rounds: int = Field(default=2, ge=1, le=3)
    allow_graph_expansion: bool = Field(default=True)
    timeout_seconds: float = Field(default=55.0, ge=5.0, le=120.0)
