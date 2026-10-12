import React, { useState } from 'react';
import { BookOpen, Search, Layers, ChevronRight } from 'lucide-react';
import { Source } from '../../types/chat';
import { SourceCard } from './SourceCard';

interface SourcesPanelProps {
  sources: Source[];
  onOpenDetail: (source: Source) => void;
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ sources, onOpenDetail }) => {
  const [filterQuery, setFilterQuery] = useState('');

  const filteredSources = sources.filter((s) => {
    const q = filterQuery.toLowerCase();
    return (
      (s.title && s.title.toLowerCase().includes(q)) ||
      (s.document_name && s.document_name.toLowerCase().includes(q)) ||
      (s.section_title && s.section_title.toLowerCase().includes(q)) ||
      (s.content && s.content.toLowerCase().includes(q))
    );
  });

  return (
    <aside className="w-80 lg:w-96 flex-shrink-0 bg-slate-50 dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-sap-blue dark:text-sap-accent" />
          <h3 className="font-bold text-sm text-sap-navy dark:text-slate-100">
            Retrieved Sources
          </h3>
        </div>
        <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-sap-blue/10 dark:bg-sap-blue/20 text-sap-blue dark:text-sap-accent">
          {sources.length} Docs
        </span>
      </div>

      {/* Quick Search */}
      {sources.length > 0 && (
        <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Filter retrieved sources..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-sap-blue"
            />
          </div>
        </div>
      )}

      {/* List Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sources.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <Layers className="w-10 h-10 mb-2 stroke-1 text-slate-300 dark:text-slate-700" />
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              No sources retrieved yet.
            </p>
            <p className="text-[11px] text-slate-400 dark:text-slate-600 mt-1">
              Ask a question to inspect SAP documentation citations.
            </p>
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            No sources matching "{filterQuery}"
          </div>
        ) : (
          filteredSources.map((source, index) => (
            <SourceCard
              key={source.id || index}
              source={source}
              index={index}
              onOpenDetail={onOpenDetail}
            />
          ))
        )}
      </div>
    </aside>
  );
};
