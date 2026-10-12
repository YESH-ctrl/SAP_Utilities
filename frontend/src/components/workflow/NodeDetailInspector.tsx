import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  X,
  Clock,
  Layers,
  Database,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Info,
  ShieldAlert,
  ArrowRight,
  GitBranch,
  Wrench,
  FileText,
  CornerDownRight,
  MessageSquare,
  Copy,
  Check,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { WorkflowNode, NodeStatus } from '../../types/workflow';

interface NodeDetailInspectorProps {
  node: WorkflowNode | null;
  onClose: () => void;
  onSelectEvidence?: (chunkId: number) => void;
}

export const NodeDetailInspector: React.FC<NodeDetailInspectorProps> = ({
  node,
  onClose,
  onSelectEvidence,
}) => {
  const navigate = useNavigate();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Section collapse states
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    overview: true,
    input: true,
    execution: true,
    output: true,
    handoff: true,
  });

  // Always scroll to top when node changes
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [node?.node_id]);

  if (!node) return null;

  const toggleSection = (key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCopyDiagnostics = () => {
    const diagnosticPayload = {
      node_id: node.node_id,
      label: node.label,
      node_type: node.node_type,
      status: node.status,
      duration_ms: node.duration_ms,
      started_at: node.started_at,
      completed_at: node.completed_at,
      mechanism: node.mechanism,
      selection_reason: node.selection_reason,
      tools_called: node.tools_called,
      predecessor_node_id: node.predecessor_node_id,
      successor_node_id: node.successor_node_id,
      handoff_summary: node.handoff_summary,
      evidence_refs: node.evidence_refs,
      metrics: node.metrics,
      error_summary: node.error_summary,
    };
    navigator.clipboard.writeText(JSON.stringify(diagnosticPayload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderStatusBadge = (status: NodeStatus) => {
    switch (status) {
      case 'succeeded':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            SUCCEEDED
          </span>
        );
      case 'running':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse">
            RUNNING
          </span>
        );
      case 'blocked':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            QUOTA BLOCKED
          </span>
        );
      case 'skipped':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700/50">
            SKIPPED
          </span>
        );
      case 'failed':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            FAILED
          </span>
        );
      case 'evidence_only':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            EVIDENCE ONLY
          </span>
        );
      case 'queued':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">
            QUEUED
          </span>
        );
    }
  };

  const isSkipped = node.status === 'skipped';
  const isBlocked = node.status === 'blocked';
  const isOutputNode = node.node_id === 'node_output';

  return (
    <div className="w-80 sm:w-96 md:w-[400px] bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl z-30 shrink-0 select-none">
      {/* Sticky Header */}
      <div className="p-3.5 border-b border-slate-800 flex items-start justify-between bg-slate-950/90 shrink-0">
        <div className="flex-1 pr-2">
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            <span className="text-[10px] font-mono text-slate-400 uppercase px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/60">
              {node.node_type}
            </span>
            {renderStatusBadge(node.status)}
            {node.phase && (
              <span className="text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/60 border border-slate-700/40">
                Phase {node.phase}
              </span>
            )}
          </div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            {node.label}
          </h3>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleCopyDiagnostics}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy Diagnostic Data"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title="Close Inspector"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Independently Scrollable Body */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-3.5 space-y-3.5 text-xs">
        {/* 1. AGENT OVERVIEW */}
        <section className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden">
          <button
            onClick={() => toggleSection('overview')}
            className="w-full px-3 py-2 flex items-center justify-between text-left font-bold text-slate-300 hover:text-white bg-slate-900/60 border-b border-slate-800/60 text-[11px]"
          >
            <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-400">
              <Info className="w-3.5 h-3.5 text-sap-blue" /> 1. Agent Overview & Responsibility
            </span>
            {openSections.overview ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {openSections.overview && (
            <div className="p-3 space-y-2.5">
              <p className="text-slate-300 leading-relaxed font-sans">{node.description}</p>

              {node.selection_reason && (
                <div className="pt-2 border-t border-slate-800/60">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-0.5">
                    Why selected for query:
                  </span>
                  <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                    {node.selection_reason}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-[11px] font-mono">
                <div>
                  <span className="text-slate-400 text-[10px] block">Role:</span>
                  <span className="text-amber-300 capitalize">
                    {node.mechanism?.replace(/_/g, ' ') || 'Deterministic Service'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Duration:</span>
                  <span className="text-slate-200">
                    {node.duration_ms ? `${Math.round(node.duration_ms)} ms` : 'In progress...'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* 2. INPUT RECEIVED */}
        <section className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden">
          <button
            onClick={() => toggleSection('input')}
            className="w-full px-3 py-2 flex items-center justify-between text-left font-bold text-slate-300 hover:text-white bg-slate-900/60 border-b border-slate-800/60 text-[11px]"
          >
            <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-400">
              <Layers className="w-3.5 h-3.5 text-cyan-400" /> 2. Input Received & Predecessor
            </span>
            {openSections.input ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {openSections.input && (
            <div className="p-3 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-mono text-[10px]">Source Stage:</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-indigo-300 text-[10px]">
                  {node.predecessor_node_id || 'Initial Input'}
                </span>
              </div>

              {node.input_summary && (
                <div className="p-2 rounded bg-slate-900/90 border border-slate-800/60 font-mono text-[11px] text-slate-300">
                  {node.input_summary}
                </div>
              )}
            </div>
          )}
        </section>

        {/* 3. EXECUTION SUMMARY & TOOLS */}
        <section className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden">
          <button
            onClick={() => toggleSection('execution')}
            className="w-full px-3 py-2 flex items-center justify-between text-left font-bold text-slate-300 hover:text-white bg-slate-900/60 border-b border-slate-800/60 text-[11px]"
          >
            <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-400">
              <Wrench className="w-3.5 h-3.5 text-teal-400" /> 3. Execution Summary & Tools
            </span>
            {openSections.execution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {openSections.execution && (
            <div className="p-3 space-y-2.5">
              {node.tools_called && node.tools_called.length > 0 && (
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                    Tools & Services Executed:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {node.tools_called.map((tool, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-950/70 border border-teal-500/40 text-teal-300"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {node.summary && (
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                    Observable Work:
                  </span>
                  <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                    {node.summary}
                  </p>
                </div>
              )}

              {node.error_summary && (
                <div className="p-2 rounded bg-rose-950/40 border border-rose-500/40 text-rose-300 font-mono text-[10px]">
                  {node.error_summary}
                </div>
              )}
            </div>
          )}
        </section>

        {/* 4. STRUCTURED OUTPUT & EVIDENCE ARTIFACTS */}
        <section className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden">
          <button
            onClick={() => toggleSection('output')}
            className="w-full px-3 py-2 flex items-center justify-between text-left font-bold text-slate-300 hover:text-white bg-slate-900/60 border-b border-slate-800/60 text-[11px]"
          >
            <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> 4. Structured Output & Artifact
            </span>
            {openSections.output ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {openSections.output && (
            <div className="p-3 space-y-2.5">
              {/* Skipped State Explanation */}
              {isSkipped && (
                <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-400 font-bold font-mono">
                    <CornerDownRight className="w-3.5 h-3.5" />
                    Stage Deliberately Skipped
                  </div>
                  <p className="text-slate-400 leading-relaxed font-sans">
                    This specialist was not assigned by the Query Planner because the query intent did not require its domain analysis. No intermediate output artifact was expected.
                  </p>
                </div>
              )}

              {/* Blocked State Explanation */}
              {isBlocked && (
                <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/50 text-[11px] space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-300 font-bold font-mono">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Stage Blocked by Provider
                  </div>
                  <p className="text-amber-200/80 leading-relaxed font-sans">
                    {node.error_summary || 'Capacity constraint encountered during model execution.'}
                  </p>
                </div>
              )}

              {/* Final Answer Separation Guard: No complete answer in canvas */}
              {isOutputNode ? (
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold font-mono text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Response Envelope Successfully Assembled
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    The final synthesized answer is exclusively presented in the Agentic Intelligence chatbot.
                  </p>
                  <button
                    onClick={() => navigate('/agentic')}
                    className="w-full py-2 px-3 rounded-lg bg-sap-blue hover:bg-sap-blue-hover text-white font-medium text-xs flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-sap-blue/20"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    View Final Answer in Chatbot →
                  </button>
                </div>
              ) : (
                !isSkipped &&
                !isBlocked && (
                  <>
                    {node.output_summary ? (
                      <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800/80 font-mono text-[11px] text-slate-200 leading-relaxed">
                        {node.output_summary}
                      </div>
                    ) : (
                      <div className="p-2 text-slate-400 italic text-[11px]">
                        Stage has not yet produced an output artifact.
                      </div>
                    )}
                  </>
                )
              )}

              {/* Evidence Refs list */}
              {node.evidence_refs && node.evidence_refs.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">
                    Referenced Documentation Chunks ({node.evidence_refs.length}):
                  </span>
                  <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1 font-mono text-[10px]">
                    {node.evidence_refs.map((ev: any, idx: number) => {
                      const docId = ev.document_id || ev.doc_id;
                      const title = ev.title || `Passage #${ev.chunk_id || idx + 1}`;
                      return (
                        <div
                          key={idx}
                          className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between gap-1 hover:border-slate-700"
                        >
                          <span className="truncate text-slate-300">
                            [{idx + 1}] {title}
                          </span>
                          {ev.canonical_url && (
                            <a
                              href={ev.canonical_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sap-blue hover:underline shrink-0 p-0.5"
                              title="Open SAP Help Document"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Metrics */}
              {node.metrics && Object.keys(node.metrics).length > 0 && (
                <div className="pt-2 border-t border-slate-800/60">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                    Measured Metrics:
                  </span>
                  <div className="grid grid-cols-2 gap-1.5 font-mono text-[10px]">
                    {Object.entries(node.metrics).map(([k, v]) => (
                      <div key={k} className="p-1 rounded bg-slate-900 border border-slate-800/60">
                        <span className="text-slate-400 block truncate">{k}</span>
                        <span className="text-slate-200 font-bold truncate">
                          {typeof v === 'number' ? v.toFixed(3) : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* 5. HANDOFF & COORDINATION */}
        <section className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden">
          <button
            onClick={() => toggleSection('handoff')}
            className="w-full px-3 py-2 flex items-center justify-between text-left font-bold text-slate-300 hover:text-white bg-slate-900/60 border-b border-slate-800/60 text-[11px]"
          >
            <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-400">
              <GitBranch className="w-3.5 h-3.5 text-purple-400" /> 5. Handoff & Coordination
            </span>
            {openSections.handoff ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {openSections.handoff && (
            <div className="p-3 space-y-2.5">
              <div className="flex items-center justify-between text-[11px] font-mono bg-slate-900 p-2 rounded border border-slate-800">
                <span className="text-slate-400">
                  From: <strong className="text-slate-200">{node.predecessor_node_id || 'Start'}</strong>
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-400">
                  To: <strong className="text-slate-200">{node.successor_node_id || 'End'}</strong>
                </span>
              </div>

              {node.handoff_summary && (
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                    Handoff Payload Contract:
                  </span>
                  <p className="text-[11px] text-slate-300 font-sans leading-relaxed p-2 rounded bg-slate-900 border border-slate-800/60">
                    {node.handoff_summary}
                  </p>
                </div>
              )}

              <div className="text-[10px] font-mono text-slate-400 pt-1 space-y-0.5 border-t border-slate-800/60">
                <div>Node ID: <code className="text-slate-400">{node.node_id}</code></div>
                {node.started_at && <div>Started: <span className="text-slate-400">{node.started_at}</span></div>}
                {node.completed_at && <div>Completed: <span className="text-slate-400">{node.completed_at}</span></div>}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
