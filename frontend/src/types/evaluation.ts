export interface BenchmarkMetrics {
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  recall_at_10: number;
  recall_at_20: number;
  doc_recall_at_10: number;
  mrr: number;
  ndcg_at_10: number;
  mean_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
}

export interface EvaluationQueryItem {
  query_id: string;
  query: string;
  category: string;
  expected_source_id: string;
  expected_source_title?: string;
  retrieved_source_id?: string;
  retrieved_source_title?: string;
  status: 'HEALTHY' | 'RANKING_MISS' | 'TRUE_CANDIDATE_MISS' | 'RECOVERED_CANDIDATE_MISS';
  rank?: number;
  latency_ms: number;
  diagnostic?: string;
  candidate_rank?: number;
}

export interface EvaluationReport {
  version: string;
  timestamp: string;
  total_queries: number;
  metrics: BenchmarkMetrics;
  issue_counts: {
    healthy: number;
    ranking_miss: number;
    true_candidate_miss: number;
    recovered_candidate_miss: number;
  };
  queries: EvaluationQueryItem[];
}
