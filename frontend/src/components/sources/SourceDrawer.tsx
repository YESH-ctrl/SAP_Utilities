import React, { useState } from 'react';
import { X, ExternalLink, BookOpen, Layers, Hash, Award, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Source } from '../../types/chat';

interface SourceDrawerProps {
  source: Source | null;
  isOpen: boolean;
  onClose: () => void;
}

function cleanUnicode(str: string): string {
  if (!str) return '';
  return str.replace(/[\uE000-\uF8FF\uFFF0-\uFFFF]/g, '').trim();
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ source, isOpen, onClose }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isOpen || !source) return null;

  const hasScore = typeof source.score === 'number' && !isNaN(source.score);

  // Clean raw content by parsing header tags ([DOCUMENT], [PATH], [SECTION], [CONTENT])
  const rawContent = source.content || '';
  let parsedPath = '';
  let parsedSection = cleanUnicode(source.section_title || '');
  let cleanBody = rawContent;

  if (rawContent.includes('[CONTENT]')) {
    const parts = rawContent.split('[CONTENT]');
    const headerPart = parts[0];
    cleanBody = parts.slice(1).join('[CONTENT]').trim();

    const pathMatch = headerPart.match(/\[PATH\]\s*\n([^\n]+)/);
    if (pathMatch) {
      parsedPath = cleanUnicode(pathMatch[1]);
    }

    const sectionMatch = headerPart.match(/\[SECTION\]\s*\n([^\n]+)/);
    if (sectionMatch && !parsedSection) {
      parsedSection = cleanUnicode(sectionMatch[1]);
    }
  }

  const cleanTitle = cleanUnicode(source.title || source.document_name || '');
  const cleanDocName = cleanUnicode(source.document_name || source.title || '');
  const fullBodyText = cleanUnicode(cleanBody);

  const PREVIEW_CHAR_LIMIT = 350;
  const isLongContent = fullBodyText.length > PREVIEW_CHAR_LIMIT;

  let displayText = fullBodyText;
  if (isLongContent && !isExpanded) {
    const truncated = fullBodyText.slice(0, PREVIEW_CHAR_LIMIT);
    const lastSpace = truncated.lastIndexOf(' ');
    const boundaryCut = lastSpace > 200 ? truncated.slice(0, lastSpace) : truncated;
    displayText = boundaryCut.replace(/[ ,;\-:–—]+$/, '') + '...';
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end transition-opacity animate-fade-in">
      <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-slate-800 animate-slide-left">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-sap-blue dark:text-sap-accent">
              SAP Documentation Source Details
            </span>
            <h2 className="text-base font-bold text-sap-navy dark:text-slate-100 line-clamp-1 mt-0.5">
              {cleanTitle}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-2 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-sap-blue"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Document & Hierarchy Card */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-2.5 text-xs">
            <div className="flex justify-between items-start gap-4">
              <span className="text-slate-500 dark:text-slate-400 font-medium shrink-0">Document Title:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200 text-right break-words">
                {cleanDocName}
              </span>
            </div>

            {parsedPath && (
              <div className="flex justify-between items-start gap-4 border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
                <span className="text-slate-500 dark:text-slate-400 font-medium shrink-0">Path:</span>
                <span className="font-mono text-[11px] text-slate-700 dark:text-slate-300 text-right break-words">
                  {parsedPath}
                </span>
              </div>
            )}

            {parsedSection && (
              <div className="flex justify-between items-center border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Section:</span>
                <span className="font-semibold text-sap-blue dark:text-sap-accent text-right">
                  {parsedSection}
                </span>
              </div>
            )}

            {source.category && (
              <div className="flex justify-between items-center border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
                <span className="text-slate-500 dark:text-slate-400 font-medium">Category:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300 bg-slate-200 dark:bg-slate-700 px-2 py-0.5 rounded text-[11px]">
                  {source.category}
                </span>
              </div>
            )}
          </div>

          {/* Relevant Excerpt */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-sap-blue dark:text-sap-accent" />
                Retrieved Documentation Excerpt
              </h3>

              {isLongContent && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  aria-expanded={isExpanded}
                  className="text-xs font-semibold text-sap-blue dark:text-sap-accent hover:underline flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-sap-blue/40 rounded px-1.5 py-0.5"
                >
                  <span>{isExpanded ? 'Collapse excerpt' : 'Show full excerpt'}</span>
                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>

            <div className="p-4 rounded-xl bg-slate-100/70 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm leading-relaxed text-slate-800 dark:text-slate-200 font-normal whitespace-pre-wrap break-words max-h-96 overflow-y-auto">
              {displayText}
            </div>
          </div>

          {/* Retrieval Metadata Metrics Grid */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
              <Award className="w-4 h-4 text-sap-blue dark:text-sap-accent" />
              Engine Metadata
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <span className="text-slate-400 text-[11px] block">Retrieval Method</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono mt-0.5 block">
                  {source.retrieval_method || 'Dense + RRF'}
                </span>
              </div>

              {hasScore && (
                <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                  <span className="text-slate-400 text-[11px] block">Relevance Score</span>
                  <span className="font-bold font-mono text-sap-blue dark:text-sap-accent mt-0.5 block">
                    {(source.score! * (source.score! <= 1 ? 100 : 1)).toFixed(2)}%
                  </span>
                </div>
              )}

              {source.source_id && (
                <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                  <span className="text-slate-400 text-[11px] block">Source ID</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300 mt-0.5 block truncate">
                    #{source.source_id}
                  </span>
                </div>
              )}

              {source.chunk_id && (
                <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                  <span className="text-slate-400 text-[11px] block">Chunk ID</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300 mt-0.5 block truncate">
                    #{source.chunk_id}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* External Link */}
          {source.url && (
            <div className="pt-2">
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-3 px-4 rounded-xl bg-sap-blue text-white hover:bg-sap-accent font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-sap-blue"
              >
                <span>Open in SAP Help Portal</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

