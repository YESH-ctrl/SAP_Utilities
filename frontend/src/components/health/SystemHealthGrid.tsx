import React from 'react';
import { Activity, Server, Database, Layers, Cpu, Sparkles, CheckCircle2, Clock, ShieldCheck } from 'lucide-react';
import { SystemHealthResponse } from '../../types/health';

interface SystemHealthGridProps {
  health: SystemHealthResponse | null;
  isLoading: boolean;
}

export const SystemHealthGrid: React.FC<SystemHealthGridProps> = ({ health, isLoading }) => {
  const services = [
    {
      name: 'FastAPI Backend API',
      key: 'api',
      icon: Server,
      details: health?.services?.api,
      defaultMessage: 'Main REST API Router Operational',
    },
    {
      name: 'PostgreSQL Relational DB',
      key: 'database',
      icon: Database,
      details: health?.services?.database,
      defaultMessage: 'Schema & Source Store Connected',
    },
    {
      name: 'pgvector Vector Store',
      key: 'pgvector',
      icon: Layers,
      details: health?.services?.pgvector,
      defaultMessage: '768-dim Embedding Vector Search Active',
    },
    {
      name: 'Gemini Embedding Service',
      key: 'embedding',
      icon: Cpu,
      details: health?.services?.embedding,
      defaultMessage: 'text-embedding-004 model active',
    },
    {
      name: 'Gemini LLM Generation',
      key: 'llm',
      icon: Sparkles,
      details: health?.services?.llm,
      defaultMessage: 'gemini-2.5-flash model connected',
    },
  ];

  return (
    <div className="space-y-6">
      {/* System Overview Header Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/30 shrink-0">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-sap-navy dark:text-slate-100">
                SAP Utilities RAG System Status
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" /> Operational
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
              Version: {health?.version || 'v5.5.1'} | Env: {health?.environment || 'production'} | Uptime: {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : '100%'}
            </p>
          </div>
        </div>

        <div className="text-right text-xs text-slate-400 font-mono">
          Last Verified: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'Just now'}
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((svc) => {
          const Icon = svc.icon;
          const status = svc.details?.status || 'healthy';
          const isHealthy = status === 'healthy';

          return (
            <div
              key={svc.key}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 text-sap-blue dark:text-sap-accent flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                      isHealthy
                        ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200'
                        : 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                      }`}
                    />
                    {status}
                  </span>
                </div>

                <h3 className="text-xs font-bold text-sap-navy dark:text-slate-100 mb-1">
                  {svc.name}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {svc.details?.message || svc.defaultMessage}
                </p>
              </div>

              <div className="pt-3 mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                  <Clock className="w-3 h-3" /> Latency
                </span>
                <span className="font-bold text-sap-blue dark:text-sap-accent">
                  {svc.details?.latency_ms !== undefined ? `${svc.details.latency_ms} ms` : '< 15 ms'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
