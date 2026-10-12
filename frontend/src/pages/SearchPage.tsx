import React from 'react';
import { useSearch } from '../hooks/useSearch';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResultCard } from '../components/search/SearchResultCard';
import { Search, Layers, FileText } from 'lucide-react';

export const SearchPage: React.FC = () => {
  const { query, setQuery, topK, setTopK, results, isLoading, error, performSearch } = useSearch();

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
      {/* Search Bar */}
      <SearchBar
        query={query}
        onChangeQuery={setQuery}
        topK={topK}
        onChangeTopK={setTopK}
        onSearch={() => performSearch()}
        isLoading={isLoading}
      />

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs font-semibold">
          ⚠️ {error}
        </div>
      )}

      {/* Empty State */}
      {!results && !isLoading && (
        <div className="py-20 text-center text-slate-400">
          <Search className="w-12 h-12 mx-auto mb-3 stroke-1 text-slate-300 dark:text-slate-700" />
          <h3 className="text-sm font-bold text-slate-600 dark:text-slate-400">
            Search SAP Utilities Documentation
          </h3>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 max-w-sm mx-auto">
            Type keywords such as "premise", "disconnection", "FI-CA", or "dunning" to perform vector search across SAP Help Portal.
          </p>
        </div>
      )}

      {/* Results Header & Grid */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 pb-3">
            <span>
              Found <strong className="text-slate-800 dark:text-slate-200">{results.total_results}</strong> relevant document snippets for "{results.query}"
            </span>
            <span className="font-mono text-[11px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
              Latency: {results.latency_ms} ms
            </span>
          </div>

          <div className="space-y-4">
            {results.results.map((item, idx) => (
              <SearchResultCard key={item.id || idx} result={item} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
