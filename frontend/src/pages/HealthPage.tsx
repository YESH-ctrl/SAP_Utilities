import React from 'react';
import { useHealth } from '../hooks/useHealth';
import { SystemHealthGrid } from '../components/health/SystemHealthGrid';
import { Loader2, RefreshCw } from 'lucide-react';

export const HealthPage: React.FC = () => {
  const { data: health, isLoading, isError, refetch } = useHealth();

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-sap-navy dark:text-slate-100">
            System Infrastructure & Microservices Health
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time telemetry and health monitoring for backend, pgvector, and LLM services.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      <SystemHealthGrid health={health || null} isLoading={isLoading} />
    </div>
  );
};
