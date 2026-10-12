import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  MessageSquareText,
  Search,
  BarChart3,
  GitMerge,
  Activity,
  Database,
  Server,
  Zap,
  Sparkles,
  Network,
} from 'lucide-react';
import { useHealth } from '../../hooks/useHealth';
import { useAgenticWorkflow } from '../../context/AgenticWorkflowContext';

export const Sidebar: React.FC = () => {
  const { data: health } = useHealth();
  const { isExecuting } = useAgenticWorkflow();

  const isBackendOk = health?.status === 'healthy' || health?.status === 'degraded';
  const isDbOk = health?.services?.database?.status === 'healthy';

  const navItems = [
    { to: '/chat', label: 'AI Assistant', icon: MessageSquareText },
    { to: '/agentic', label: 'Agentic Intelligence', icon: Sparkles },
    { to: '/workflow-canvas', label: 'Live Execution Canvas', icon: Network, isLive: isExecuting },
    { to: '/search', label: 'Documentation Search', icon: Search },
    { to: '/retrieval', label: 'Retrieval Inspector', icon: GitMerge },
    { to: '/evaluation', label: 'Evaluation Metrics', icon: BarChart3 },
    { to: '/health', label: 'System Health', icon: Activity },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-sap-navy text-white flex flex-col h-screen border-r border-slate-700/50 shadow-xl select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-700/60 flex items-center gap-3">
        <div className="w-9 h-9 rounded-md bg-sap-blue flex items-center justify-center shadow-md font-bold text-white tracking-wider">
          SAP
        </div>
        <div>
          <h1 className="font-semibold text-sm tracking-wide text-slate-100">
            SAP Utilities AI
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">v5.5.1 RAG Engine</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-sap-blue text-white shadow-sm font-semibold'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span className="flex-1">{item.label}</span>
              {item.isLive && (
                <span className="flex h-2 w-2 relative" title="Live Agent Execution Active">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-700/60 bg-slate-900/60 text-xs space-y-2.5">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
          Engine Status
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-slate-300 text-[11px]">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            Backend:
          </span>
          <span className="flex items-center gap-1.5 font-medium text-[11px]">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendOk ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className={isBackendOk ? 'text-emerald-400' : 'text-rose-400'}>
              {isBackendOk ? 'Connected' : 'Offline'}
            </span>
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-slate-300 text-[11px]">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            Database:
          </span>
          <span className="flex items-center gap-1.5 font-medium text-[11px]">
            <span
              className={`w-2 h-2 rounded-full ${
                isDbOk ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span className={isDbOk ? 'text-emerald-400' : 'text-amber-400'}>
              {isDbOk ? 'Healthy' : 'Unknown'}
            </span>
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-slate-300 text-[11px]">
            <Zap className="w-3.5 h-3.5 text-slate-400" />
            Retrieval:
          </span>
          <span className="text-[10px] font-mono text-slate-300 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
            Dense + RRF + H1
          </span>
        </div>
      </div>
    </aside>
  );
};
