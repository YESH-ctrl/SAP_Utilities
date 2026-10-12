import { useQuery } from '@tanstack/react-query';
import { fetchSystemHealth } from '../services/healthApi';

export function useHealth(refetchInterval: number = 30000) {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval,
    retry: 1,
  });
}
