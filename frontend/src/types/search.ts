import { Source } from './chat';

export interface SearchRequest {
  query: string;
  top_k?: number;
  use_rrf?: boolean;
  dense_weight?: number;
  lexical_weight?: number;
  enable_h1_recovery?: boolean;
  enable_semantic_recovery?: boolean;
  filters?: {
    category?: string;
    document_id?: string;
    min_score?: number;
  };
}

export interface SearchResultItem extends Source {
  retrieval_method?: string;
  category?: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  latency_ms: number;
  results: SearchResultItem[];
}
