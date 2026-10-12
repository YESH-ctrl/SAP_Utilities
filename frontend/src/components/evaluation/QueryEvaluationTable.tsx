import React, { useState } from 'react';
import { Search, CheckCircle, AlertTriangle, XCircle, RefreshCw, Filter } from 'lucide-react';
import { EvaluationQueryItem } from '../../types/evaluation';

interface QueryEvaluationTableProps {
  queries: EvaluationQueryItem[];
}

export const QueryEvaluationTable: React.FC<QueryEvaluationTableProps> = ({ queries }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filtered = queries.filter((q) => {
    const matchSearch =
      q.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.query_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (q.expected_source_title && q.expected_source_title.toLowerCase().includes(searchTerm.toLowerCase()));

    if (!matchSearch) return false;
    if (statusFilter !== 'ALL' && q.status !== statusFilter) return false;
    return true;
  });

  const getStatusBadge = (status: EvaluationQueryItem['status']) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-0.5 rounded border border-emerald-200">
            <CheckCircle className="w-3 h-3" /> Healthy
          </span>
        );
      case 'RANKING_MISS':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2.5 py-0.5 rounded border border-amber-200">
            <AlertTriangle className="w-3 h-3" /> Ranking Miss
          </span>
        );
      case 'TRUE_CANDIDATE_MISS':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-2.5 py-0.5 rounded border border-rose-200">
            <XCircle className="w-3 h-3" /> Candidate Miss
          </span>
        );
      case 'RECOVERED_CANDIDATE_MISS':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-2.5 py-0.5 rounded border border-indigo-200">
            <RefreshCw className="w-3 h-3" /> Recovered Miss
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-sap-navy dark:text-slate-100">
            Benchmark Query Dataset ({filtered.length} queries)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Evaluated against SAP Utilities V5.5 golden test set.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search benchmark question..."
              className="pl-8 pr-3 py-1.5 text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:border-sap-blue"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="HEALTHY">Healthy</option>
            <option value="RANKING_MISS">Ranking Miss</option>
            <option value="TRUE_CANDIDATE_MISS">Candidate Miss</option>
            <option value="RECOVERED_CANDIDATE_MISS">Recovered Miss</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="py-3 px-4 w-20">ID</th>
              <th className="py-3 px-4">Benchmark Question</th>
              <th className="py-3 px-4">Expected Source</th>
              <th className="py-3 px-4">Retrieved Top Result</th>
              <th className="py-3 px-4 w-32">Status</th>
              <th className="py-3 px-4 w-24 text-right">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                  No benchmark queries match the current filter.
                </td>
              </tr>
            ) : (
              filtered.map((q) => (
                <tr key={q.query_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="py-3 px-4 font-mono font-bold text-slate-500 text-[11px]">
                    {q.query_id}
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate">
                    {q.query}
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-mono text-[11px] max-w-xs truncate">
                    {q.expected_source_title || q.expected_source_id}
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-mono text-[11px] max-w-xs truncate">
                    {q.retrieved_source_title || q.retrieved_source_id || '—'}
                  </td>
                  <td className="py-3 px-4">{getStatusBadge(q.status)}</td>
                  <td className="py-3 px-4 font-mono text-right text-slate-600 dark:text-slate-400">
                    {q.latency_ms} ms
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
