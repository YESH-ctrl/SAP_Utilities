import React from 'react';
import { useEvaluation } from '../hooks/useEvaluation';
import { MetricGrid } from '../components/evaluation/MetricGrid';
import { QueryEvaluationTable } from '../components/evaluation/QueryEvaluationTable';
import { FailureAnalysis } from '../components/evaluation/FailureAnalysis';
import { BarChart3, Loader2, RefreshCw } from 'lucide-react';

export const EvaluationPage: React.FC = () => {
  const { data: report, isLoading, isError, error, refetch } = useEvaluation();

  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-sap-blue mb-2" />
        <p className="text-xs font-medium">Loading V5.5 retrieval benchmark metrics...</p>
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="h-full p-8 max-w-xl mx-auto flex flex-col items-center justify-center text-center">
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs space-y-3">
          <p className="font-bold">Failed to load benchmark evaluation data.</p>
          <p className="text-[11px] font-mono">{(error as any)?.message || 'Evaluation API unavailable.'}</p>
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-rose-600 text-white rounded-md font-semibold text-xs inline-flex items-center gap-1 hover:bg-rose-700"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-8 max-w-7xl mx-auto">
      {/* Overview Header */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-sap-navy dark:text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-sap-blue" />
            <span>SAP Utilities Retrieval Engine Benchmark ({report.version})</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Standardized benchmark evaluation across {report.total_queries} golden test queries.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          Evaluated: {new Date(report.timestamp).toLocaleDateString()}
        </div>
      </div>

      {/* Primary Benchmark Metric Cards */}
      <MetricGrid metrics={report.metrics} />

      {/* Failure Diagnostics Analysis */}
      <FailureAnalysis queries={report.queries} />

      {/* Benchmark Query Table */}
      <QueryEvaluationTable queries={report.queries} />
    </div>
  );
};
