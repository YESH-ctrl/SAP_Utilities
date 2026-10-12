import React, { useState } from 'react';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  Bot,
  Database,
  ShieldCheck,
  ChevronUp,
  ChevronDown,
  List,
  Radio,
  Sparkles,
  GitFork,
  Feather
} from 'lucide-react';
import { WorkflowEvent } from '../../types/workflow';

interface EventTimelineProps {
  events: WorkflowEvent[];
  onSelectNode: (nodeId: string) => void;
  selectedNodeId?: string | null;
}

export const EventTimeline: React.FC<EventTimelineProps> = ({
  events,
  onSelectNode,
  selectedNodeId,
}) => {
  const [filter, setFilter] = useState<'all' | 'agents' | 'retrieval' | 'validation' | 'errors'>('all');
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [showHeartbeats, setShowHeartbeats] = useState<boolean>(false);

  // Check if live heartbeat/SSE is active (any event in last 60s or heartbeat received)
  const hasRecentHeartbeat = events.some(
    (e) => e.event_type === 'heartbeat' || e.summary.toLowerCase() === 'heartbeat'
  );

  // Filter out heartbeats from default visible timeline
  const meaningfulEvents = events.filter((evt) => {
    const isHb = evt.event_type === 'heartbeat' || evt.summary.toLowerCase() === 'heartbeat';
    if (!showHeartbeats && isHb) return false;
    return true;
  });

  const filteredEvents = meaningfulEvents.filter((evt) => {
    if (filter === 'all') return true;
    if (filter === 'agents') {
      return (
        evt.node_type === 'specialist' ||
        evt.node_type === 'planner' ||
        evt.node_type === 'synthesis' ||
        Boolean(evt.agent_role)
      );
    }
    if (filter === 'retrieval') {
      return (
        evt.node_type === 'retrieval' ||
        evt.node_type === 'encoder' ||
        evt.node_type === 'context_builder'
      );
    }
    if (filter === 'validation') {
      return (
        evt.node_type === 'validator' ||
        evt.node_type === 'auditor' ||
        evt.event_type === 'validation_updated'
      );
    }
    if (filter === 'errors') {
      return (
        evt.event_type === 'node_blocked' ||
        evt.event_type === 'node_failed' ||
        evt.event_type === 'run_failed' ||
        Boolean(evt.error)
      );
    }
    return true;
  });

  const getEventIcon = (evt: WorkflowEvent) => {
    if (evt.event_type === 'node_blocked') {
      return <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    }
    if (evt.event_type === 'node_failed' || evt.event_type === 'run_failed') {
      return <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
    }
    if (evt.event_type === 'node_succeeded' || evt.event_type === 'run_completed') {
      return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    }
    if (evt.node_type === 'planner') {
      return <Sparkles className="w-3.5 h-3.5 text-sap-gold shrink-0" />;
    }
    if (evt.node_type === 'retrieval' || evt.node_type === 'encoder') {
      return <Database className="w-3.5 h-3.5 text-teal-400 shrink-0" />;
    }
    if (evt.node_type === 'specialist') {
      return <Bot className="w-3.5 h-3.5 text-purple-400 shrink-0" />;
    }
    if (evt.node_type === 'auditor' || evt.node_type === 'validator') {
      return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    }
    if (evt.node_type === 'decision') {
      return <GitFork className="w-3.5 h-3.5 text-orange-400 shrink-0" />;
    }
    if (evt.node_type === 'synthesis') {
      return <Feather className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    }
    return <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts.slice(11, 19);
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-950 flex flex-col transition-all z-20">
      {/* Bar Header */}
      <div className="px-4 py-2 flex items-center justify-between border-b border-slate-800/80 bg-slate-900/70 text-xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 font-bold text-slate-200 hover:text-white transition-colors"
          >
            <List className="w-3.5 h-3.5 text-sap-blue" />
            Execution Timeline ({meaningfulEvents.length})
            {isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
            )}
          </button>

          {/* Transport Health Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-[10px] font-mono text-slate-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Live Stream Active</span>
          </div>

          {/* Functional Filters */}
          {isExpanded && (
            <div className="hidden sm:flex items-center gap-1">
              {(['all', 'agents', 'retrieval', 'validation', 'errors'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-2.5 py-0.5 rounded text-[10px] font-mono capitalize transition-colors ${
                    filter === f
                      ? 'bg-sap-blue text-white font-semibold shadow-sm shadow-sap-blue/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right side diagnostics toggle & latest counter */}
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <button
            onClick={() => setShowHeartbeats(!showHeartbeats)}
            className={`px-2 py-0.5 rounded border transition-colors ${
              showHeartbeats
                ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:text-slate-300'
            }`}
            title="Toggle routine heartbeat pings in timeline"
          >
            Diagnostics {showHeartbeats ? '(Heartbeats On)' : '(Filtered)'}
          </button>

          {meaningfulEvents.length > 0 && (
            <span className="text-slate-400 hidden sm:inline">
              Latest: #{meaningfulEvents[meaningfulEvents.length - 1].sequence}
            </span>
          )}
        </div>
      </div>

      {/* Expanded Timeline Items */}
      {isExpanded && (
        <div className="max-h-44 overflow-y-auto divide-y divide-slate-800/40 font-mono text-[11px]">
          {filteredEvents.length === 0 ? (
            <div className="p-4 text-center text-slate-400 text-xs">
              No events found for filter "{filter}".
            </div>
          ) : (
            filteredEvents.map((evt) => {
              const isSelected = selectedNodeId && evt.node_id === selectedNodeId;
              return (
                <div
                  key={evt.event_id || `${evt.sequence}-${evt.event_type}`}
                  onClick={() => evt.node_id && onSelectNode(evt.node_id)}
                  className={`px-4 py-2 flex items-center gap-3 hover:bg-slate-900/80 transition-colors cursor-pointer ${
                    isSelected ? 'bg-slate-900 border-l-2 border-sap-blue' : ''
                  }`}
                >
                  <span className="text-slate-400 w-8 text-right shrink-0">
                    #{evt.sequence}
                  </span>

                  <div>{getEventIcon(evt)}</div>

                  <div className="flex-1 truncate flex items-center gap-2">
                    <span className="text-slate-200 truncate">{evt.summary}</span>
                    {typeof evt.duration_ms === 'number' && evt.duration_ms > 0 && (
                      <span className="text-[10px] text-slate-400 shrink-0">
                        ({Math.round(evt.duration_ms)}ms)
                      </span>
                    )}
                  </div>

                  {evt.node_id && (
                    <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/60 shrink-0 hidden sm:inline">
                      {evt.node_id}
                    </span>
                  )}

                  <span className="text-[10px] text-slate-400 shrink-0">
                    {formatTimestamp(evt.timestamp)}
                  </span>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
