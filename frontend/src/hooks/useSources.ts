import { useQuery } from '@tanstack/react-query';
import { fetchSourcesList, fetchSourceDetails } from '../services/sourcesApi';

export function useSources() {
  return useQuery({
    queryKey: ['sourcesList'],
    queryFn: fetchSourcesList,
    staleTime: 1000 * 60 * 10,
  });
}

export function useSourceDetail(sourceId: string | null) {
  return useQuery({
    queryKey: ['sourceDetail', sourceId],
    queryFn: () => (sourceId ? fetchSourceDetails(sourceId) : Promise.reject('No source ID')),
    enabled: !!sourceId,
  });
}
