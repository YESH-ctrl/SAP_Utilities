import React, { useState } from 'react';
import { ExternalLink, BookOpen, Layers, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { SearchResultItem } from '../../types/search';

interface SearchResultCardProps {
  result: SearchResultItem;
  rank: number;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({ result, rank }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasScore = typeof result.score === 'number' && !isNaN(result.score);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs hover:shadow-md transition-all">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-sap-blue/10 text-sap-blue dark:text-sap-accent font-mono text-xs font-bold flex items-center justify-center border border-sap-blue/20 shrink-0">
            {rank}
          </span>
          <h3 className="text-sm font-bold text-sap-navy dark:text-slate-100 hover:text-sap-blue transition-colors">
            {result.title || result.document_name}
          </h3>
        </div>

        {hasScore && (
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-md text-xs font-mono shrink-0">
            <span className="text-slate-400">Score:</span>
            <span className="font-bold text-sap-blue dark:text-sap-accent">
              {(result.score! * (result.score! <= 1 ? 100 : 1)).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {result.section_title && (
        <p className="text-xs text-sap-blue dark:text-sap-accent font-medium mb-3 flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5" />
          <span>{result.section_title}</span>
        </p>
      )}

      <div className={`text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-normal ${isExpanded ? '' : 'line-clamp-3'}`}>
        "{result.content}"
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-mono text-[11px] text-slate-500">
            <FileText className="w-3 h-3 text-slate-400" />
            {result.document_name}
          </span>
          <span className="font-mono text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-400">
            {result.retrieval_method || 'Dense + Lexical + RRF'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-sap-blue flex items-center gap-1"
          >
            <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {result.url && (
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold text-sap-blue dark:text-sap-accent hover:underline flex items-center gap-1 ml-2"
            >
              <span>SAP Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
