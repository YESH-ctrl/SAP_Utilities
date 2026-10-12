import { apiClient } from './api';
import { ChatRequest, ChatResponse, Source } from '../types/chat';

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const backendResponse = await apiClient<any>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: request.query,
      query: request.query,
      top_k: request.top_k || 5,
      conversation_id: request.conversation_id,
    }),
  });

  // Normalize sources from backend if needed
  const normalizedSources: Source[] = (backendResponse.sources || []).map((s: any, idx: number) => ({
    id: s.id || s.source_id || `source_${idx + 1}`,
    source_id: s.source_id || s.id || `${idx + 1}`,
    document_id: s.document_id || '',
    chunk_id: s.chunk_id || '',
    title: s.title || s.document_name || 'SAP Utilities Documentation',
    document_name: s.document_name || s.title || 'SAP Help Portal',
    section_title: s.section_title || s.section || '',
    content: s.content || s.text || s.excerpt || '',
    score: typeof s.score === 'number' ? s.score : (s.final_score ?? s.rrf_score),
    retrieval_method: s.retrieval_method || s.method || 'RRF + H1',
    category: s.category || 'SAP Utilities',
    url: s.url || s.help_url,
    highlights: s.highlights || [],
  }));

  // Create explicit citations list from sources if available
  const citations = normalizedSources.map((s, index) => ({
    id: `citation_${index + 1}`,
    sourceId: s.id,
    documentId: s.document_id,
    chunkId: s.chunk_id,
    title: s.title,
    section: s.section_title,
    excerpt: s.content.slice(0, 150) + '...',
    url: s.url,
  }));

  const answerText = typeof backendResponse.message === 'object' && backendResponse.message?.content
    ? backendResponse.message.content
    : (typeof backendResponse.message === 'string' ? backendResponse.message : (backendResponse.answer || 'No response generated.'));

  return {
    answer: answerText,
    citations,
    sources: normalizedSources,
    metadata: {
      request_id: backendResponse.metadata?.request_id || `req_${Date.now()}`,
      query: request.query,
      timestamp: new Date().toISOString(),
      latency_ms: backendResponse.duration_ms || backendResponse.metadata?.latency_ms || 0,
      dense_latency_ms: backendResponse.metadata?.dense_latency_ms,
      lexical_latency_ms: backendResponse.metadata?.lexical_latency_ms,
      rrf_latency_ms: backendResponse.metadata?.rrf_latency_ms,
      llm_latency_ms: backendResponse.metadata?.llm_latency_ms,
      candidate_count: backendResponse.metadata?.candidate_count || normalizedSources.length,
      recovered_count: backendResponse.metadata?.recovered_count || 0,
      model: backendResponse.metadata?.model || 'gemini-2.5-flash',
    },
  };
}
