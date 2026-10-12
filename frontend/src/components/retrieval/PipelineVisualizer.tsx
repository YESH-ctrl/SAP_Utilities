import React from 'react';
import { CheckCircle2, Clock, Layers, ArrowRight, Zap, Database, GitMerge, FileText } from 'lucide-react';
import { PipelineStageInfo, RetrievalInspectionData } from '../../types/retrieval';

interface PipelineVisualizerProps {
  data: RetrievalInspectionData | null;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ data }) => {
  const defaultStages: PipelineStageInfo[] = data?.stages || [
    { name: 'Query Processing', status: 'complete', latency_ms: 12, details: 'Normalized & Tokenized' },
    { name: 'Dense Vector Retrieval', status: 'complete', latency_ms: 85, candidates_count: 50, details: 'pgvector Cosine Similarity' },
    { name: 'Lexical BM25 Retrieval', status: 'complete', latency_ms: 42, candidates_count: 50, details: 'PostgreSQL Full-Text Search' },
    { name: 'RRF Fusion Stage', status: 'complete', latency_ms: 12, candidates_count: 50, details: 'k=60 Reciprocal Rank Fusion' },
    { name: 'H1 Hierarchy Recovery', status: 'complete', latency_ms: 18, recovered_count: 1, details: 'Parent Document Structural Anchor' },
    { name: 'Final Ranking & Context', status: 'complete', latency_ms: 5, candidates_count: data?.final_sources?.length || 5, details: 'Top RRF Selected' },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-sap-navy dark:text-slate-100 flex items-center gap-2">
            <GitMerge className="w-5 h-5 text-sap-blue" />
            <span>V5.5.1 RAG Retrieval Pipeline Execution</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Step-by-step query candidate generation, fusion, and structural recovery trace.
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-md text-slate-700 dark:text-slate-300 font-semibold border border-slate-200 dark:border-slate-700">
              Latency: {data.total_latency_ms} ms
            </span>
            <span className="bg-sap-blue/10 text-sap-blue dark:text-sap-accent px-3 py-1 rounded-md font-bold border border-sap-blue/20">
              Req ID: {data.request_id}
            </span>
          </div>
        )}
      </div>

      {/* Visual Workflow Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {defaultStages.map((stage, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 relative flex flex-col justify-between hover:border-sap-blue/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                  Stage 0{idx + 1}
                </span>
                <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>{stage.status}</span>
                </span>
              </div>

              <h4 className="text-xs font-bold text-sap-navy dark:text-slate-100 mb-1">
                {stage.name}
              </h4>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-3">
                {stage.details}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" />
                {stage.latency_ms !== undefined ? `${stage.latency_ms} ms` : 'Not available'}
              </span>

              {stage.candidates_count !== undefined && (
                <span className="text-sap-blue dark:text-sap-accent font-semibold">
                  Candidates: {stage.candidates_count}
                </span>
              )}

              {stage.recovered_count !== undefined && (
                <span className="text-amber-600 dark:text-amber-400 font-semibold">
                  Recovered H1: {stage.recovered_count}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
