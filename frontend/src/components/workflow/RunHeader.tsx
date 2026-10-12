import React, { useState, useEffect } from 'react';
import {
  Copy,
  Check,
  Clock,
  StopCircle,
  History,
  Maximize2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Sparkles
} from 'lucide-react';
import { RunSnapshot } from '../../types/workflow';

interface RunHeaderProps {
  run: RunSnapshot | null;
  onCancel?: () => void;
  onOpenHistory?: () => void;
  onFitView?: () => void;
}

export const RunHeader: React.FC<RunHeaderProps> = ({
  run,
  onCancel,
  onOpenHistory,
  onFitView
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [isQueryExpanded, setIsQueryExpanded] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    if (!run) return;
    if (run.status === 'running') {
      const startMs = new Date(run.started_at).getTime();
      const interval = setInterval(() => {
        setElapsedSeconds(Math.max(0, Math.floor((Date.now() - startMs) / 1000)));
      }, 500);
      return () => clearInterval(interval);
    } else if (run.total_duration_ms) {
      setElapsedSeconds(Math.floor(run.total_duration_ms / 1000));
    }
  }, [run?.status, run?.started_at, run?.total_duration_ms]);

  if (!run) return null;

  const handleCopyRunId = () => {
    navigator.clipboard.writeText(run.run_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderStatusPill = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-400/50 animate-pulse flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            RUNNING
          </span>
        );
      case 'succeeded':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            SUCCEEDED
          </span>
        );
      case 'partial':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            PARTIAL
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            FAILED
          </span>
        );
      case 'cancelled':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            CANCELLED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
            {status.toUpperCase()}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border-b border-slate-800 p-3 sm:px-4 flex flex-col gap-2 shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Run ID & Status */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1 bg-slate-950 px-2 py-1 rounded-lg border border-slate-800 text-xs font-mono text-slate-300">
            <span className="text-slate-500">RUN:</span>
            <span className="text-slate-200 font-semibold">{run.run_id}</span>
            <button
              onClick={handleCopyRunId}
              className="p-1 hover:text-white text-slate-400 transition-colors ml-1"
              title="Copy Run ID"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>

          {renderStatusPill(run.status)}

          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-950/60 px-2 py-1 rounded-lg border border-slate-800/80">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{elapsedSeconds}s</span>
          </div>

          <span className="text-xs text-slate-400 truncate max-w-[200px] sm:max-w-xs">
            Stage: <span className="text-slate-200 font-medium">{run.current_stage}</span>
          </span>
        </div>

        {/* Right: Controls & History */}
        <div className="flex items-center gap-2">
          {run.status === 'running' && onCancel && (
            <button
              onClick={onCancel}
              className="px-2.5 py-1 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-300 hover:bg-rose-900/60 text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Cancel Run
            </button>
          )}

          {onFitView && (
            <button
              onClick={onFitView}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1 transition-colors"
              title="Fit graph to view"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              Fit View
            </button>
          )}

          {onOpenHistory && (
            <button
              onClick={onOpenHistory}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <History className="w-3.5 h-3.5" />
              Run History
            </button>
          )}
        </div>
      </div>

      {/* Query Banner */}
      <div className="flex items-start justify-between gap-2 bg-slate-950/80 p-2 rounded-lg border border-slate-800/60 text-xs">
        <div className="truncate flex-1">
          <span className="text-slate-500 font-medium mr-2">Query:</span>
          <span className={`text-slate-200 ${isQueryExpanded ? '' : 'line-clamp-1'}`}>
            "{run.query}"
          </span>
        </div>
        {run.query.length > 80 && (
          <button
            onClick={() => setIsQueryExpanded(!isQueryExpanded)}
            className="text-slate-400 hover:text-white p-0.5"
          >
            {isQueryExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>
    </div>
  );
};
