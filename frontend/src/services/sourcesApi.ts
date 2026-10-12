import { apiClient } from './api';
import { Source } from '../types/chat';

export async function fetchSourcesList(): Promise<Source[]> {
  const response = await apiClient<{ sources: Source[] }>('/api/v1/sources');
  return response.sources || [];
}

export async function fetchSourceDetails(sourceId: string): Promise<Source> {
  const response = await apiClient<{ source: Source }>(`/api/v1/sources/${encodeURIComponent(sourceId)}`);
  return response.source;
}
