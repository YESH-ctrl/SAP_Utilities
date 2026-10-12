import React, { useState } from 'react';
import { Search, CheckCircle, XCircle, ArrowUpDown, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { CandidateItem } from '../../types/retrieval';

interface CandidateTableProps {
  candidates: CandidateItem[];
}

export const CandidateTable: React.FC<CandidateTableProps> = ({ candidates }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSelected, setFilterSelected] = useState<'all' | 'selected' | 'unselected'>('all');
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [sortField, setSortField] = useState<'rank' | 'score'>('rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const filtered = candidates
    .filter((item) => {
      const matchText =
        item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.section_title && item.section_title.toLowerCase().includes(searchTerm.toLowerCase()));

      if (!matchText) return false;

      if (filterSelected === 'selected') return item.is_selected;
      if (filterSelected === 'unselected') return !item.is_selected;
      return true;
    })
    .sort((a, b) => {
      const valA = sortField === 'rank' ? a.rank : a.final_score ?? a.rrf_score ?? 0;
      const valB = sortField === 'rank' ? b.rank : b.final_score ?? b.rrf_score ?? 0;

      if (sortOrder === 'asc') return valA > valB ? 1 : -1;
      return valA < valB ? 1 : -1;
    });

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
      {/* Table Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-sap-navy dark:text-slate-100">
            Candidate Generation Pool ({filtered.length} items)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Inspect candidates retrieved across Dense, Lexical, and RRF stages.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search candidate titles..."
              className="pl-8 pr-3 py-1.5 text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 focus:outline-none focus:border-sap-blue"
            />
          </div>

          <select
            value={filterSelected}
            onChange={(e) => setFilterSelected(e.target.value as any)}
            className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
          >
            <option value="all">All Candidates</option>
            <option value="selected">Selected for Context</option>
            <option value="unselected">Unselected</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="py-3 px-4 w-16">
                <button
                  onClick={() => {
                    setSortField('rank');
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center gap-1 hover:text-slate-800 dark:hover:text-slate-200"
                >
                  <span>Rank</span>
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="py-3 px-4">Title / Section</th>
              <th className="py-3 px-4">Document</th>
              <th className="py-3 px-4 w-24">
                <button
                  onClick={() => {
                    setSortField('score');
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center gap-1 hover:text-slate-800 dark:hover:text-slate-200"
                >
                  <span>Score</span>
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </th>
              <th className="py-3 px-4 w-32">Retrieval Method</th>
              <th className="py-3 px-4 w-24 text-center">Selected</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                  No candidates match the specified filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((c) => {
                const score = c.final_score ?? c.rrf_score ?? c.dense_score;
                const isExpanded = expandedRow === c.rank;

                return (
                  <React.Fragment key={c.rank}>
                    <tr
                      onClick={() => setExpandedRow(isExpanded ? null : c.rank)}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors ${
                        c.is_selected ? 'bg-sap-blue/5 dark:bg-sap-blue/10 font-medium' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-slate-700 dark:text-slate-300">
                        #{c.rank}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-800 dark:text-slate-200">
                          {c.title}
                        </div>
                        {c.section_title && (
                          <div className="text-[11px] text-slate-500 font-normal">
                            {c.section_title}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
                        {c.document_name}
                      </td>
                      <td className="py-3 px-4 font-mono text-sap-blue dark:text-sap-accent font-bold">
                        {score !== undefined ? (score <= 1 ? (score * 100).toFixed(1) + '%' : score.toFixed(3)) : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] font-mono text-slate-700 dark:text-slate-300">
                          {c.retrieval_method}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {c.is_selected ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200">
                            <CheckCircle className="w-3 h-3" /> Yes
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                            <XCircle className="w-3 h-3" /> No
                          </span>
                        )}
                      </td>
                    </tr>

                    {/* Expanded Preview Row */}
                    {isExpanded && c.content_preview && (
                      <tr className="bg-slate-50 dark:bg-slate-900/80">
                        <td colSpan={6} className="p-4 border-t border-b border-slate-200 dark:border-slate-800">
                          <div className="text-xs text-slate-700 dark:text-slate-300 font-normal leading-relaxed bg-white dark:bg-slate-800 p-3 rounded-md border border-slate-200 dark:border-slate-700">
                            <span className="font-semibold text-slate-500 block mb-1">Snippet Preview:</span>
                            "{c.content_preview}"
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
