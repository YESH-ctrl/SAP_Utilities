import { useState, useCallback } from 'react';
import { executeSearch } from '../services/searchApi';
import { SearchRequest, SearchResponse } from '../types/search';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performSearch = useCallback(async (searchQuery?: string, customTopK?: number) => {
    const q = searchQuery !== undefined ? searchQuery : query;
    const k = customTopK || topK;

    if (!q.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await executeSearch({ query: q, top_k: k });
      setResults(response);
    } catch (err: any) {
      setError(err?.message || 'Failed to perform search in SAP documentation.');
    } finally {
      setIsLoading(false);
    }
  }, [query, topK]);

  return {
    query,
    setQuery,
    topK,
    setTopK,
    results,
    isLoading,
    error,
    performSearch,
  };
}
