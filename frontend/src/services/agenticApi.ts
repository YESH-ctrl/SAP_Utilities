import { apiClient } from './api';
import { API_BASE_URL } from '../lib/constants';
import { AgenticChatRequest, FinalAgenticResponse, EvidenceItem } from '../types/agentic';
import { RunSnapshot, WorkflowEvent } from '../types/workflow';

/**
 * Dedicated API Client for Independent Agentic Platform & Live Workflow Canvas.
 * Strictly communicates with /api/v2/agentic endpoints.
 * Never calls legacy /api/v1/ endpoints.
 */

export async function sendAgenticChat(request: AgenticChatRequest): Promise<FinalAgenticResponse> {
  return await apiClient<FinalAgenticResponse>('/api/v2/agentic/chat', {
    method: 'POST',
    body: JSON.stringify({
      query: request.query,
      conversation_id: request.conversation_id,
      max_investigation_rounds: request.max_investigation_rounds || 2,
      allow_graph_expansion: request.allow_graph_expansion !== false,
      timeout_seconds: request.timeout_seconds || 90.0,
    }),
  });
}

export async function createAgenticRun(request: AgenticChatRequest): Promise<RunSnapshot> {
  return await apiClient<RunSnapshot>('/api/v2/agentic/runs', {
    method: 'POST',
    body: JSON.stringify({
      query: request.query,
      conversation_id: request.conversation_id,
      max_investigation_rounds: request.max_investigation_rounds || 2,
      allow_graph_expansion: request.allow_graph_expansion !== false,
      timeout_seconds: request.timeout_seconds || 90.0,
    }),
  });
}

export async function getAgenticRun(runId: string): Promise<RunSnapshot> {
  return await apiClient<RunSnapshot>(`/api/v2/agentic/runs/${encodeURIComponent(runId)}`, {
    method: 'GET',
  });
}

export async function listAgenticRuns(limit: number = 20): Promise<RunSnapshot[]> {
  return await apiClient<RunSnapshot[]>(`/api/v2/agentic/runs?limit=${limit}`, {
    method: 'GET',
  });
}

export async function cancelAgenticRun(runId: string): Promise<any> {
  return await apiClient<any>(`/api/v2/agentic/runs/${encodeURIComponent(runId)}/cancel`, {
    method: 'POST',
  });
}

export function subscribeToRunEvents(
  runId: string,
  onEvent: (evt: WorkflowEvent) => void,
  onError?: (err: any) => void
): () => void {
  const url = `${API_BASE_URL}/api/v2/agentic/runs/${encodeURIComponent(runId)}/events`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error('Failed to parse SSE event data', e);
    }
  };

  const eventTypes = [
    'run_started',
    'node_created',
    'node_queued',
    'node_started',
    'node_progress',
    'node_succeeded',
    'node_partial',
    'node_failed',
    'node_blocked',
    'node_skipped',
    'edge_activated',
    'agent_finding',
    'evidence_added',
    'validation_updated',
    'retry_scheduled',
    'run_completed',
    'run_failed',
    'run_cancelled',
    'heartbeat',
  ];

  eventTypes.forEach((type) => {
    eventSource.addEventListener(type, (event: any) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
      } catch (e) {
        console.error(`Failed to parse SSE ${type} event data`, e);
      }
    });
  });

  eventSource.onerror = (err) => {
    if (onError) onError(err);
  };

  return () => {
    eventSource.close();
  };
}

export async function searchAgenticEvidence(query: string, topK: number = 8): Promise<EvidenceItem[]> {
  return await apiClient<EvidenceItem[]>(`/api/v2/agentic/search?query=${encodeURIComponent(query)}&top_k=${topK}`, {
    method: 'POST',
  });
}

export async function fetchAgenticHealth(): Promise<any> {
  return await apiClient<any>('/api/v2/agentic/health', {
    method: 'GET',
  });
}
