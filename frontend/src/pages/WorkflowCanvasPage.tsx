import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Network,
  History,
  Maximize2,
  StopCircle,
  Copy,
  Check,
  Clock,
  Sparkles,
  MessageSquare,
  AlertTriangle,
  RotateCcw,
  SlidersHorizontal,
  ChevronDown
} from 'lucide-react';
import { useAgenticWorkflow } from '../context/AgenticWorkflowContext';
import { WorkflowCanvas } from '../components/workflow/WorkflowCanvas';
import { NodeDetailInspector } from '../components/workflow/NodeDetailInspector';
import { EventTimeline } from '../components/workflow/EventTimeline';
import { RunHistoryModal } from '../components/workflow/RunHistoryModal';
import { RunSnapshot } from '../types/workflow';

export const WorkflowCanvasPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    activeRun,
    selectedRun,
    selectRun,
    runsHistory,
    isExecuting,
    currentStage,
    cancelCurrentRun,
    refreshHistory
  } = useAgenticWorkflow();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [showMiniMap, setShowMiniMap] = useState<boolean>(true);

  // The run to display is selectedRun, falling back to activeRun
  const currentRun: RunSnapshot | null = selectedRun || activeRun;

  React.useEffect(() => {
    if (!currentRun) {
      refreshHistory();
    }
  }, [currentRun, refreshHistory]);

  const handleCopyRunId = () => {
    if (!currentRun) return;
    navigator.clipboard.writeText(currentRun.run_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const selectedNode = currentRun?.nodes.find((n) => n.node_id === selectedNodeId) || null;

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
      case 'evidence_only':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            EVIDENCE ONLY
          </span>
        );
      case 'blocked':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            QUOTA BLOCKED
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
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-700/60 text-slate-300 border border-slate-600/40 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
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
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      {/* Top Operations Header */}
      <div className="bg-slate-900 border-b border-slate-800 p-3 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0 shadow-md z-30">
        {/* Left: Run Selector & ID */}
        <div className="flex items-center gap-3 flex-wrap w-full sm:w-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-sap-blue/20 border border-sap-blue/40 flex items-center justify-center text-sap-blue">
              <Network className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Execution Run
              </span>
              {currentRun ? (
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-xs font-bold text-slate-200">
                    {currentRun.run_id}
                  </span>
                  <button
                    onClick={handleCopyRunId}
                    className="p-1 hover:text-white text-slate-400 transition-colors"
                    title="Copy Run ID"
                  >
                    {copied ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              ) : (
                <span className="text-xs text-slate-500 font-mono">No active run</span>
              )}
            </div>
          </div>

          {currentRun && renderStatusPill(currentRun.status)}

          {currentRun && (
            <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded-lg border border-slate-800">
              <Clock className="w-3 h-3 text-slate-500" />
              <span>
                {currentRun.total_duration_ms
                  ? `${(currentRun.total_duration_ms / 1000).toFixed(1)}s`
                  : 'Live'}
              </span>
            </div>
          )}

          {currentRun?.current_stage && (
            <span className="text-xs text-slate-400 truncate max-w-[200px] sm:max-w-xs">
              Stage: <span className="text-slate-200 font-medium">{currentRun.current_stage}</span>
            </span>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          {isExecuting && (
            <button
              onClick={cancelCurrentRun}
              className="px-2.5 py-1.5 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-300 hover:bg-rose-900/60 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Cancel Run
            </button>
          )}

          <button
            onClick={() => setIsHistoryOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <History className="w-3.5 h-3.5" />
            <span>Run History ({runsHistory.length})</span>
          </button>

          <button
            onClick={() => navigate('/agentic')}
            className="px-3 py-1.5 rounded-lg bg-sap-blue hover:bg-sap-accent text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm shadow-sap-blue/20"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chatbot Interface</span>
          </button>
        </div>
      </div>

      {/* Query Bar (Compact) */}
      {currentRun && (
        <div className="bg-slate-950/90 border-b border-slate-800/80 px-4 py-2 flex items-center justify-between text-xs text-slate-300">
          <div className="truncate flex-1 pr-4">
            <span className="text-slate-500 font-mono text-[10px] uppercase mr-2 font-bold">
              Target Query:
            </span>
            <span className="text-slate-200 font-medium">"{currentRun.query}"</span>
          </div>
          <span className="text-[10px] font-mono text-slate-500 shrink-0">
            {currentRun.nodes.length} Stages • {currentRun.edges.length} Edges
          </span>
        </div>
      )}

      {/* Main Canvas & Inspector Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {currentRun ? (
          <div className="flex-1 flex flex-col h-full relative">
            <WorkflowCanvas
              nodes={currentRun.nodes}
              edges={currentRun.edges}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
              showMiniMap={showMiniMap}
            />

            {/* Bottom Chronological Event Timeline */}
            <EventTimeline
              events={currentRun.events}
              onSelectNode={setSelectedNodeId}
              selectedNodeId={selectedNodeId}
            />
          </div>
        ) : (
          /* Empty Workspace State */
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center bg-slate-950 text-slate-500">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-4 shadow-xl">
              <Network className="w-8 h-8 text-sap-blue" />
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-1">
              Live Multi-Agent Execution Workspace
            </h3>
            <p className="text-xs max-w-md text-slate-400 mb-6 leading-relaxed">
              No workflow execution is currently selected. Ask a question in the Agentic Intelligence
              chatbot to stream real-time agent coordination, or choose a previous execution run from
              history.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/agentic')}
                className="px-4 py-2 bg-sap-blue hover:bg-sap-accent text-white font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-colors shadow-md shadow-sap-blue/20"
              >
                <MessageSquare className="w-4 h-4" />
                Go to Agentic Chatbot
              </button>
              {runsHistory.length > 0 && (
                <button
                  onClick={() => setIsHistoryOpen(true)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium text-xs rounded-xl flex items-center gap-1.5 border border-slate-800 transition-colors"
                >
                  <History className="w-4 h-4" />
                  Browse Run History
                </button>
              )}
            </div>
          </div>
        )}

        {/* Right 5-Section Node Inspector */}
        {selectedNode && (
          <NodeDetailInspector
            node={selectedNode}
            onClose={() => setSelectedNodeId(null)}
          />
        )}
      </div>

      {/* Run History Modal */}
      <RunHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        currentRunId={currentRun?.run_id || undefined}
        onSelectRun={(run) => {
          selectRun(run.run_id);
          setSelectedNodeId(null);
          setIsHistoryOpen(false);
        }}
      />
    </div>
  );
};
