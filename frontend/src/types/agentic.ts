export type StageExecutionStatus = 
  | 'pending'
  | 'running'
  | 'succeeded'
  | 'partial'
  | 'failed'
  | 'skipped'
  | 'blocked_by_provider_quota';

export type ExecutionMechanism =
  | 'llm_reasoning'
  | 'deterministic_retrieval'
  | 'deterministic_extraction'
  | 'rule_engine'
  | 'bypass'
  | 'test_stub';

export type ResponseMode =
  | 'synthesized_answer'
  | 'evidence_only'
  | 'error_state';

export type AnswerStatus =
  | 'synthesized_verified'
  | 'synthesized_qualified'
  | 'synthesis_unavailable'
  | 'synthesis_failed';

export type EvidenceSufficiency =
  | 'sufficient'
  | 'partial'
  | 'insufficient';

export interface CitationItem {
  citation_id: number;
  evidence_id: string;
  chunk_id: number;
  document_id: number;
  title: string;
  canonical_url: string;
  section_heading?: string;
  excerpt: string;
  cosine_distance: number;
  similarity_score: number;
}

export interface EvidenceItem {
  evidence_id: string;
  chunk_id: number;
  document_id: number;
  section_id?: number;
  source_id?: number;
  title: string;
  canonical_url: string;
  section_heading?: string;
  section_path?: string;
  breadcrumb?: string;
  clean_body?: string;
  clean_excerpt?: string;
  content: string;
  char_offset_start: number;
  char_offset_end: number;
  is_excerpted: boolean;
  token_count: number;
  cosine_distance: number;
  similarity_score: number;
  subquery_id?: string;
  discovery_method: string;
  metadata?: Record<string, any>;
}

export interface StageStatus {
  stage_name: string;
  status: StageExecutionStatus;
  mechanism?: ExecutionMechanism;
  latency_ms: number;
  details?: string;
  tokens_used?: number;
}

export interface CitationVerification {
  citation_index: number;
  evidence_id: string;
  chunk_id: number;
  document_id: number;
  title: string;
  canonical_url: string;
  quoted_text: string;
  is_verified_in_evidence: boolean;
  is_exact_substring_match: boolean;
}

export interface ValidationReport {
  citation_integrity: boolean;
  citation_integrity_ratio?: number | null;
  verified_citations: CitationVerification[];
  invalid_citations: string[];
  claim_support_rate?: number | null;
  question_coverage_rate?: number | null;
  unanswered_subquestions: string[];
  detected_contradictions: string[];
  repair_attempts: number;
  overall_status: 'verified' | 'qualified' | 'unverified' | 'evidence_only';
  notes?: string;
}

export interface RetrievalDiagnostics {
  total_candidates_retrieved: number;
  unique_chunks_used: number;
  graph_expanded_count: number;
  min_cosine_distance: number;
  max_cosine_distance: number;
  vector_search_latency_ms: number;
  graph_traversal_latency_ms: number;
  context_tokens_used: number;
  context_budget_limit: number;
}

export interface FinalAgenticResponse {
  request_id: string;
  original_query: string;
  response_mode: ResponseMode;
  answer_status: AnswerStatus;
  evidence_sufficiency: EvidenceSufficiency;
  answer: string;
  citations: CitationItem[];
  evidence_payload: EvidenceItem[];
  agent_stage_summary: StageStatus[];
  retrieval_diagnostics: RetrievalDiagnostics;
  validation_report: ValidationReport;
  execution_status: 'succeeded' | 'partial' | 'failed';
  unresolved_gaps: string[];
  total_latency_ms: number;
  token_usage?: Record<string, number>;
}

export interface AgenticChatRequest {
  query: string;
  conversation_id?: string;
  max_investigation_rounds?: number;
  allow_graph_expansion?: boolean;
  timeout_seconds?: number;
}
