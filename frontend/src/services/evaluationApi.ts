import { apiClient } from './api';
import { EvaluationReport } from '../types/evaluation';

export async function fetchEvaluationReport(): Promise<EvaluationReport> {
  return apiClient<EvaluationReport>('/api/v1/evaluation');
}
