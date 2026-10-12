export interface Source {
  id: string;
  source_id?: string;
  document_id?: string;
  chunk_id?: string;
  title: string;
  document_name?: string;
  section_title?: string;
  content: string;
  score?: number;
  retrieval_method?: string;
  category?: string;
  url?: string;
  highlights?: string[];
}

export interface Citation {
  id: string;
  sourceId?: string;
  documentId?: string;
  chunkId?: string;
  title?: string;
  section?: string;
  excerpt?: string;
  url?: string;
}

export interface RetrievalMetadata {
  request_id?: string;
  query?: string;
  timestamp?: string;
  latency_ms?: number;
  dense_latency_ms?: number;
  lexical_latency_ms?: number;
  rrf_latency_ms?: number;
  llm_latency_ms?: number;
  candidate_count?: number;
  recovered_count?: number;
  model?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
  citations?: Citation[];
  metadata?: RetrievalMetadata;
  feedback?: 'like' | 'dislike' | null;
}

export interface ChatRequest {
  query: string;
  conversation_id?: string;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  citations?: Citation[];
  sources?: Source[];
  metadata?: RetrievalMetadata;
}
