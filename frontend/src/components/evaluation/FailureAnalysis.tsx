import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, XCircle, RefreshCw, ChevronDown, ChevronUp, Wrench } from 'lucide-react';
import { EvaluationQueryItem } from '../../types/evaluation';

interface FailureAnalysisProps {
  queries: EvaluationQueryItem[];
}

export const FailureAnalysis: React.FC<FailureAnalysisProps> = ({ queries }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const rankingMisses = queries.filter((q) => q.status === 'RANKING_MISS');
  const candidateMisses = queries.filter((q) => q.status === 'TRUE_CANDIDATE_MISS');
  const recoveredMisses = queries.filter((q) => q.status === 'RECOVERED_CANDIDATE_MISS');

  const failedQueries = [...rankingMisses, ...candidateMisses, ...recoveredMisses];

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
      <div>
        <h3 className="text-sm font-bold text-sap-navy dark:text-slate-100 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-amber-500" />
          <span>Retrieval Issues & Failure Analysis</span>
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Detailed diagnostic breakdown of benchmark queries that did not retrieve expected golden source at Rank 1.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-800 dark:text-amber-300">
              Ranking Misses
            </span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-900 dark:text-amber-100 mt-2">
            {rankingMisses.length}
          </div>
          <p className="text-[11px] text-amber-700 dark:text-amber-400 mt-1">
            Golden source was generated in top-K but ranked below top result.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-800 dark:text-rose-300">
              Candidate Misses
            </span>
            <XCircle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-900 dark:text-rose-100 mt-2">
            {candidateMisses.length}
          </div>
          <p className="text-[11px] text-rose-700 dark:text-rose-400 mt-1">
            Golden source was never retrieved in initial vector/lexical candidate pool.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-indigo-200 dark:border-indigo-900/40 bg-indigo-50/50 dark:bg-indigo-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-indigo-800 dark:text-indigo-300">
              Recovered Misses
            </span>
            <RefreshCw className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-indigo-900 dark:text-indigo-100 mt-2">
            {recoveredMisses.length}
          </div>
          <p className="text-[11px] text-indigo-700 dark:text-indigo-400 mt-1">
            H1 hierarchy recovery retrieved document, but answer ranking missed.
          </p>
        </div>
      </div>

      {/* Failed Queries List */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Issue Diagnostics List ({failedQueries.length} items)
        </h4>

        {failedQueries.length === 0 ? (
          <div className="p-6 text-center text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200">
            ✓ Excellent! 100% of benchmark queries retrieved top golden sources.
          </div>
        ) : (
          failedQueries.map((item) => {
            const isExpanded = expandedId === item.query_id;
            return (
              <div
                key={item.query_id}
                className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-slate-50/50 dark:bg-slate-800/30"
              >
                <div
                  onClick={() => setExpandedId(isExpanded ? null : item.query_id)}
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-slate-400">
                      {item.query_id}
                    </span>
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                      "{item.query}"
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-semibold text-amber-600 dark:text-amber-400">
                      {item.status}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="p-5 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <span className="text-slate-400 text-[11px] block">Expected Golden Source</span>
                        <div className="font-mono font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">
                          {item.expected_source_title || item.expected_source_id}
                        </div>
                      </div>

                      <div>
                        <span className="text-slate-400 text-[11px] block">Actual Top Retrieved Result</span>
                        <div className="font-mono font-semibold text-rose-600 dark:text-rose-400 mt-0.5">
                          {item.retrieved_source_title || item.retrieved_source_id || 'None'}
                        </div>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-300 flex items-start gap-2">
                      <Wrench className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold block mb-0.5">Engine Diagnostic:</span>
                        <p className="text-[11px] leading-relaxed">
                          {item.diagnostic ||
                            (item.status === 'RANKING_MISS'
                              ? `Source was generated at Candidate Rank #${item.candidate_rank || 4}, but RRF dense weights gave precedence to alternative document.`
                              : `Source embeddings did not meet top-50 vector distance threshold for this specific vocabulary query.`)}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
