import { Source } from './chat';

export interface PipelineStageInfo {
  name: string;
  status: 'complete' | 'in_progress' | 'failed' | 'skipped' | 'idle';
  latency_ms?: number;
  candidates_count?: number;
  recovered_count?: number;
  details?: string;
}

export interface CandidateItem {
  rank: number;
  source_id: string;
  title: string;
  document_name: string;
  section_title?: string;
  dense_score?: number;
  lexical_score?: number;
  rrf_score?: number;
  final_score?: number;
  retrieval_method: string;
  is_selected: boolean;
  content_preview?: string;
}

export interface RetrievalInspectionData {
  request_id: string;
  query: string;
  timestamp: string;
  total_latency_ms: number;
  stages: PipelineStageInfo[];
  candidates: CandidateItem[];
  final_sources: Source[];
  retrieval_config: {
    top_k: number;
    dense_weight: number;
    lexical_weight: number;
    rrf_k: number;
    h1_enabled: boolean;
    semantic_recovery_enabled: boolean;
  };
}
