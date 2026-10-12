import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import {
  Sparkles,
  Cpu,
  Database,
  Layers,
  Bot,
  FileSpreadsheet,
  ShieldCheck,
  GitFork,
  Feather,
  CheckCircle2,
  Clock,
  Loader2,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  CornerDownRight,
  Slash,
  FileText
} from 'lucide-react';
import { WorkflowNode as WorkflowNodeModel, NodeStatus, NodeType } from '../../types/workflow';

interface CustomNodeData extends WorkflowNodeModel {
  isSelected?: boolean;
}

export const CustomWorkflowNode: React.FC<NodeProps> = ({ data, selected }) => {
  const node = data as unknown as CustomNodeData;

  const getNodeIcon = (type: NodeType) => {
    switch (type) {
      case 'request':
        return <CheckCircle2 className="w-4 h-4 text-sky-400" />;
      case 'planner':
        return <Sparkles className="w-4 h-4 text-sap-gold" />;
      case 'encoder':
        return <Cpu className="w-4 h-4 text-indigo-400" />;
      case 'retrieval':
        return <Database className="w-4 h-4 text-teal-400" />;
      case 'context_builder':
        return <Layers className="w-4 h-4 text-cyan-400" />;
      case 'specialist':
        return <Bot className="w-4 h-4 text-purple-400" />;
      case 'aggregator':
        return <FileSpreadsheet className="w-4 h-4 text-blue-400" />;
      case 'auditor':
        return <ShieldCheck className="w-4 h-4 text-amber-400" />;
      case 'decision':
        return <GitFork className="w-4 h-4 text-orange-400" />;
      case 'synthesis':
        return <Feather className="w-4 h-4 text-emerald-400" />;
      case 'validator':
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      case 'output':
        return <CheckCircle2 className="w-4 h-4 text-sky-400" />;
      default:
        return <Bot className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status: NodeStatus) => {
    switch (status) {
      case 'queued':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-sky-300 px-1.5 py-0.5 rounded bg-sky-950/70 border border-sky-500/40">
            <Clock className="w-2.5 h-2.5 text-sky-400" />
            QUEUED
          </span>
        );
      case 'running':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-cyan-300 px-2 py-0.5 rounded bg-cyan-950/90 border border-cyan-400/80 shadow-sm shadow-cyan-500/40 animate-pulse">
            <Loader2 className="w-2.5 h-2.5 text-cyan-400 animate-spin" />
            RUNNING
          </span>
        );
      case 'succeeded':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-emerald-300 px-1.5 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/40">
            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
            SUCCEEDED
          </span>
        );
      case 'partial':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-amber-300 px-1.5 py-0.5 rounded bg-amber-950/70 border border-amber-500/40">
            <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
            PARTIAL
          </span>
        );
      case 'evidence_only':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-amber-300 px-1.5 py-0.5 rounded bg-amber-950/70 border border-amber-500/50">
            <Layers className="w-2.5 h-2.5 text-amber-400" />
            EVIDENCE ONLY
          </span>
        );
      case 'blocked':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-amber-300 px-1.5 py-0.5 rounded bg-amber-950/90 border border-amber-500/70">
            <ShieldAlert className="w-2.5 h-2.5 text-amber-400" />
            QUOTA BLOCKED
          </span>
        );
      case 'skipped':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/50">
            <CornerDownRight className="w-2.5 h-2.5 text-slate-400" />
            SKIPPED
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-rose-300 px-1.5 py-0.5 rounded bg-rose-950/80 border border-rose-500/50">
            <XCircle className="w-2.5 h-2.5 text-rose-400" />
            FAILED
          </span>
        );
      case 'cancelled':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-rose-300 px-1.5 py-0.5 rounded bg-rose-950/60 border border-rose-500/40">
            <Slash className="w-2.5 h-2.5 text-rose-400" />
            CANCELLED
          </span>
        );
      case 'waiting':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/60 border border-slate-700/40">
            <Clock className="w-2.5 h-2.5 text-slate-500" />
            WAITING
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-800/60 border border-slate-700/30">
            <Clock className="w-2.5 h-2.5 text-slate-500" />
            QUEUED
          </span>
        );
    }
  };

  const getBorderColor = () => {
    if (selected) {
      return 'ring-2 ring-sap-blue border-sap-blue shadow-xl shadow-sap-blue/25';
    }
    if (node.status === 'running') {
      return 'border-cyan-400 shadow-lg shadow-cyan-500/20';
    }
    if (node.status === 'blocked') {
      return 'border-amber-500/80 bg-amber-950/20';
    }
    if (node.status === 'succeeded') {
      return 'border-slate-800 hover:border-emerald-500/60 bg-slate-900';
    }
    if (node.status === 'skipped') {
      return 'border-slate-800/70 opacity-60 bg-slate-950/70';
    }
    if (node.status === 'failed') {
      return 'border-rose-500/80 bg-rose-950/20';
    }
    return 'border-slate-800 hover:border-slate-700 bg-slate-900';
  };

  const formatDuration = (ms?: number) => {
    if (!ms || ms <= 0) return null;
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const evidenceCount = node.evidence_refs?.length || 0;
  const hasEvidence = evidenceCount > 0;
  const hasOutput = Boolean(node.output_summary);

  return (
    <div
      className={`relative w-[270px] min-h-[105px] rounded-xl p-3.5 border transition-all text-slate-200 text-left cursor-pointer flex flex-col justify-between ${getBorderColor()}`}
    >
      {/* 4 Connection Handles for Clean Directional Routing */}
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="!w-2.5 !h-2.5 !bg-slate-600 !border-2 !border-slate-900 hover:!bg-sap-blue"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="!w-2.5 !h-2.5 !bg-slate-600 !border-2 !border-slate-900 hover:!bg-sap-blue"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="!w-2.5 !h-2.5 !bg-slate-600 !border-2 !border-slate-900 hover:!bg-sap-blue"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="!w-2.5 !h-2.5 !bg-slate-600 !border-2 !border-slate-900 hover:!bg-sap-blue"
      />

      {/* Top Header Row */}
      <div className="flex items-center justify-between gap-1.5 mb-1.5">
        <div className="flex items-center gap-2 truncate">
          <div className="p-1 rounded-md bg-slate-800 border border-slate-700/60 shrink-0">
            {getNodeIcon(node.node_type)}
          </div>
          <span className="font-bold text-xs text-slate-100 truncate">
            {node.label}
          </span>
        </div>

        {/* Right Header Indicators: Duration + Evidence/Output badges */}
        <div className="flex items-center gap-1 shrink-0">
          {hasEvidence && (
            <span
              title={`${evidenceCount} evidence passages attached`}
              className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-teal-500/20 text-teal-300 border border-teal-500/40 flex items-center gap-0.5"
            >
              <Layers className="w-2.5 h-2.5" />
              {evidenceCount}
            </span>
          )}
          {hasOutput && !hasEvidence && (
            <span
              title="Structured output artifact available"
              className="p-0.5 rounded text-indigo-400"
            >
              <FileText className="w-3 h-3" />
            </span>
          )}
          {formatDuration(node.duration_ms) && (
            <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-700/40">
              {formatDuration(node.duration_ms)}
            </span>
          )}
        </div>
      </div>

      {/* Center Row: Clean One-line Responsibility */}
      <p className="text-[11px] text-slate-400 line-clamp-1 leading-snug mb-2 font-sans">
        {node.description}
      </p>

      {/* Bottom Footer Row: Execution Status & Mechanism Tag */}
      <div className="flex items-center justify-between gap-1 mt-auto pt-1.5 border-t border-slate-800/70">
        <div>{getStatusBadge(node.status)}</div>
        {node.mechanism && (
          <span className="text-[9px] font-mono text-slate-400 uppercase tracking-tight truncate max-w-[95px]">
            {node.mechanism.replace(/_/g, ' ')}
          </span>
        )}
      </div>
    </div>
  );
};
