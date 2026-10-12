/**
 * ISOLATED MOCK ADAPTER
 * Used ONLY when VITE_USE_MOCK_DATA=true is explicitly set in environment or developer settings.
 * All mock data is clearly labeled with [MOCK] prefix.
 */
import { ChatResponse } from '../types/chat';
import { SearchResponse } from '../types/search';
import { EvaluationReport } from '../types/evaluation';
import { SystemHealthResponse } from '../types/health';

export const IS_MOCK_ENABLED = import.meta.env.VITE_USE_MOCK_DATA === 'true';

export async function getMockChatResponse(query: string): Promise<ChatResponse> {
  await new Promise((res) => setTimeout(res, 800));

  return {
    answer: `[MOCK ANSWER] In SAP Utilities, **${query}** involves core master data entities and business processes.\n\n### Key Concepts\n1. **Premise**: Spatial object representing a building or land segment.\n2. **Installation**: Logical grouping of devices/utility services.\n3. **Business Partner**: Customer or legal entity tied to account.`,
    citations: [
      {
        id: 'mock_cit_1',
        sourceId: 'src_101',
        documentId: 'doc_premise_01',
        title: '[MOCK] Master Data - Premise Overview',
        section: 'Section 4.1 Premises in SAP IS-U',
        excerpt: 'A premise represents a physical location where utility services are supplied.',
        url: 'https://help.sap.com/docs/SAP_UTILITIES/premise',
      },
    ],
    sources: [
      {
        id: 'src_101',
        source_id: '101',
        document_id: 'doc_premise_01',
        chunk_id: 'chk_992',
        title: '[MOCK] Master Data - Premise Overview',
        document_name: 'SAP Utilities Master Data Manual',
        section_title: 'Premise Structure & Relationships',
        content: 'A premise in SAP Utilities represents a spatial unit (e.g. apartment, office building) to which utility services are delivered.',
        score: 0.942,
        retrieval_method: 'Dense + RRF Fusion',
        category: 'Master Data',
        url: 'https://help.sap.com/docs/SAP_UTILITIES/premise',
      },
    ],
    metadata: {
      request_id: `mock_req_${Date.now()}`,
      query,
      timestamp: new Date().toISOString(),
      latency_ms: 450,
      dense_latency_ms: 85,
      lexical_latency_ms: 42,
      rrf_latency_ms: 12,
      llm_latency_ms: 310,
      candidate_count: 50,
      recovered_count: 1,
      model: 'mock-gemini-2.5-flash',
    },
  };
}
