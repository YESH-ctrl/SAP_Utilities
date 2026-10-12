import React from 'react';
import { ExternalLink, BookOpen, Layers, CheckCircle2 } from 'lucide-react';
import { Source } from '../../types/chat';

interface SourceCardProps {
  source: Source;
  index: number;
  onOpenDetail: (source: Source) => void;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, index, onOpenDetail }) => {
  const hasScore = typeof source.score === 'number' && !isNaN(source.score);

  return (
    <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-sap-blue/50 dark:hover:border-sap-blue/50 shadow-xs hover:shadow-md transition-all group relative flex flex-col justify-between">
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-sap-blue/10 dark:bg-sap-blue/20 text-sap-blue dark:text-sap-accent border border-sap-blue/30">
            0{index + 1}
          </span>

          {source.category && (
            <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded truncate max-w-[140px]">
              {source.category}
            </span>
          )}
        </div>

        {/* Title */}
        <h4 className="text-xs font-bold text-sap-navy dark:text-slate-100 group-hover:text-sap-blue dark:group-hover:text-sap-accent transition-colors line-clamp-2 mb-1">
          {source.title || source.document_name || 'SAP Utilities Documentation'}
        </h4>

        {/* Section */}
        {source.section_title && (
          <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium mb-2 line-clamp-1 flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-sap-blue dark:text-sap-accent shrink-0" />
            <span>{source.section_title}</span>
          </p>
        )}

        {/* Excerpt */}
        <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed mb-3 font-normal">
          "{source.content}"
        </p>
      </div>

      {/* Footer Metadata */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
        {hasScore ? (
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Score:</span>
            <span className="font-mono font-bold text-sap-blue dark:text-sap-accent">
              {(source.score! * (source.score! <= 1 ? 100 : 1)).toFixed(1)}%
            </span>
          </div>
        ) : (
          <span className="text-slate-400 text-[10px] italic">Verified Source</span>
        )}

        <button
          onClick={() => onOpenDetail(source)}
          className="flex items-center gap-1 font-semibold text-sap-blue dark:text-sap-accent hover:underline text-[11px]"
        >
          <span>View Source</span>
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
