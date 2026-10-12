import React from 'react';
import { Search, SlidersHorizontal, Loader2 } from 'lucide-react';

interface SearchBarProps {
  query: string;
  onChangeQuery: (q: string) => void;
  topK: number;
  onChangeTopK: (k: number) => void;
  onSearch: () => void;
  isLoading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  query,
  onChangeQuery,
  topK,
  onChangeTopK,
  onSearch,
  isLoading,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => onChangeQuery(e.target.value)}
            placeholder="Search SAP Utilities documentation (e.g., premise, reconnection, budget billing)..."
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-sap-blue focus:ring-1 focus:ring-sap-blue"
          />
        </div>

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="px-5 py-2.5 rounded-lg bg-sap-blue text-white hover:bg-sap-accent disabled:opacity-40 font-semibold text-sm flex items-center gap-2 transition-all shadow-xs shrink-0"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          <span>Search</span>
        </button>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
            <SlidersHorizontal className="w-3.5 h-3.5 text-sap-blue" />
            <span>Search Parameters</span>
          </span>

          <div className="flex items-center gap-2">
            <label htmlFor="topKSelect" className="text-[11px]">Top K Results:</label>
            <select
              id="topKSelect"
              value={topK}
              onChange={(e) => onChangeTopK(Number(e.target.value))}
              className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-0.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        <span className="font-mono text-[11px] text-slate-400">
          Engine: Hybrid (Dense Vector + BM25 Lexical + RRF)
        </span>
      </div>
    </form>
  );
};
