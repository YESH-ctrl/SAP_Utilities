import React, { useEffect, useState } from 'react';
import { X, History, Clock, ArrowRight, Loader2, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { listAgenticRuns } from '../../services/agenticApi';
import { RunSnapshot } from '../../types/workflow';

interface RunHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRun: (run: RunSnapshot) => void;
  currentRunId?: string;
}

export const RunHistoryModal: React.FC<RunHistoryModalProps> = ({
  isOpen,
  onClose,
  onSelectRun,
  currentRunId
}) => {
  const [runs, setRuns] = useState<RunSnapshot[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    setError(null);
    listAgenticRuns(25)
      .then((data) => setRuns(data))
      .catch((err) => setError(err?.message || 'Failed to load execution history.'))
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  const renderStatus = (status: string) => {
    switch (status) {
      case 'succeeded':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> SUCCEEDED
          </span>
        );
      case 'partial':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-amber-400">
            <AlertTriangle className="w-3 h-3" /> PARTIAL
          </span>
        );
      case 'evidence_only':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-amber-400">
            <AlertTriangle className="w-3 h-3" /> EVIDENCE ONLY
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-rose-400">
            <XCircle className="w-3 h-3" /> FAILED
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-slate-400">
            <Clock className="w-3 h-3" /> {status.toUpperCase()}
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-sap-blue" />
            <h3 className="text-sm font-bold text-slate-100">Workflow Execution History</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-sap-blue" />
              <span className="text-xs">Loading execution runs...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs text-center">
              {error}
            </div>
          ) : runs.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No previous runs recorded. Submit a query to initiate a live workflow run.
            </div>
          ) : (
            runs.map((r) => {
              const isCurrent = r.run_id === currentRunId;
              return (
                <div
                  key={r.run_id}
                  onClick={() => {
                    onSelectRun(r);
                    onClose();
                  }}
                  className={`p-3 rounded-xl bg-slate-950 border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    isCurrent
                      ? 'border-sap-blue bg-slate-900/60 shadow-sm shadow-sap-blue/20'
                      : 'border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/40'
                  }`}
                >
                  <div className="truncate flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-mono text-slate-400 font-semibold">
                        {r.run_id}
                      </span>
                      {renderStatus(r.status)}
                      {r.total_duration_ms && (
                        <span className="text-[10px] font-mono text-slate-500">
                          {Math.round(r.total_duration_ms)}ms
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-200 line-clamp-1 font-medium">
                      "{r.query}"
                    </p>
                    <span className="text-[10px] text-slate-500 mt-1 block">
                      {new Date(r.started_at).toLocaleString()}
                    </span>
                  </div>

                  <button
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-sap-blue text-slate-300 hover:text-white transition-colors shrink-0"
                    title="Load run into canvas"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
