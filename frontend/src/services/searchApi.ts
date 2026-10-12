import { apiClient } from './api';
import { SearchRequest, SearchResponse, SearchResultItem } from '../types/search';

export async function executeSearch(request: SearchRequest): Promise<SearchResponse> {
  const startTime = performance.now();
  const rawResponse = await apiClient<any>('/api/v1/retrieval/query', {
    method: 'POST',
    body: JSON.stringify({
      query: request.query,
      top_k: request.top_k || 10,
      use_rrf: request.use_rrf ?? true,
      dense_weight: request.dense_weight,
      lexical_weight: request.lexical_weight,
    }),
  });

  const duration = Math.round(performance.now() - startTime);

  const results: SearchResultItem[] = (rawResponse.results || rawResponse.sources || []).map(
    (item: any, idx: number) => ({
      id: item.id || item.source_id || `search_res_${idx + 1}`,
      source_id: item.source_id || item.id || `${idx + 1}`,
      document_id: item.document_id || '',
      chunk_id: item.chunk_id || '',
      title: item.title || item.document_name || 'SAP Utilities Doc',
      document_name: item.document_name || item.title || 'SAP Help Portal',
      section_title: item.section_title || item.section || '',
      content: item.content || item.text || item.excerpt || '',
      score: typeof item.score === 'number' ? item.score : (item.final_score ?? item.rrf_score),
      retrieval_method: item.retrieval_method || item.method || 'Hybrid (Dense+Lexical)',
      category: item.category || 'SAP Utilities',
      url: item.url || item.help_url,
    })
  );

  return {
    query: request.query,
    total_results: rawResponse.total_results || results.length,
    latency_ms: rawResponse.latency_ms || duration,
    results,
  };
}
