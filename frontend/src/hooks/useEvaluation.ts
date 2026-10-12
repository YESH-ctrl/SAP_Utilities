import { useQuery } from '@tanstack/react-query';
import { fetchEvaluationReport } from '../services/evaluationApi';

export function useEvaluation() {
  return useQuery({
    queryKey: ['evaluationReport'],
    queryFn: fetchEvaluationReport,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
  });
}
