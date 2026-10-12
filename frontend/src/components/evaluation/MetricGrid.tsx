import React from 'react';
import { Target, Award, Clock, Activity, Zap, CheckCircle2 } from 'lucide-react';
import { BenchmarkMetrics } from '../../types/evaluation';

interface MetricGridProps {
  metrics: BenchmarkMetrics;
}

export const MetricGrid: React.FC<MetricGridProps> = ({ metrics }) => {
  const formatPercent = (val?: number) => (val !== undefined ? `${(val * 100).toFixed(2)}%` : 'N/A');
  const formatMs = (val?: number) => (val !== undefined ? `${Math.round(val)} ms` : 'N/A');

  const metricCards = [
    { title: 'Source Recall @5', value: formatPercent(metrics.recall_at_5), icon: Target, category: 'Accuracy' },
    { title: 'Source Recall @10', value: formatPercent(metrics.recall_at_10), icon: Target, category: 'Accuracy' },
    { title: 'Source Recall @20', value: formatPercent(metrics.recall_at_20), icon: Target, category: 'Accuracy' },
    { title: 'Document Recall @10', value: formatPercent(metrics.doc_recall_at_10), icon: CheckCircle2, category: 'Coverage' },
    { title: 'MRR (Mean Reciprocal Rank)', value: formatPercent(metrics.mrr), icon: Award, category: 'Ranking' },
    { title: 'NDCG @10', value: formatPercent(metrics.ndcg_at_10), icon: Award, category: 'Ranking' },
    { title: 'P50 Latency (Median)', value: formatMs(metrics.p50_latency_ms), icon: Clock, category: 'Performance' },
    { title: 'P95 Latency (Tail)', value: formatMs(metrics.p95_latency_ms), icon: Clock, category: 'Performance' },
    { title: 'P99 Latency (Max)', value: formatMs(metrics.p99_latency_ms), icon: Activity, category: 'Performance' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {metricCards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold font-mono uppercase tracking-wider text-slate-400">
                  {card.category}
                </span>
                <Icon className="w-4 h-4 text-sap-blue dark:text-sap-accent" />
              </div>
              <h4 className="text-xs font-medium text-slate-600 dark:text-slate-400">
                {card.title}
              </h4>
            </div>

            <div className="mt-3">
              <div className="text-2xl font-bold font-mono text-sap-navy dark:text-slate-100 tracking-tight">
                {card.value}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
