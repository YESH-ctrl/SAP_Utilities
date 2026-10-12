import React from 'react';
import { BookOpen } from 'lucide-react';
import { Citation as CitationType } from '../../types/chat';

interface CitationProps {
  citation: CitationType;
  index: number;
  onClick: (citation: CitationType) => void;
}

export const CitationBadge: React.FC<CitationProps> = ({ citation, index, onClick }) => {
  return (
    <button
      onClick={() => onClick(citation)}
      className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded bg-sap-blue/10 dark:bg-sap-blue/20 text-sap-blue dark:text-sap-accent border border-sap-blue/30 hover:bg-sap-blue hover:text-white dark:hover:bg-sap-blue transition-all duration-150 font-mono text-[11px] font-semibold cursor-pointer align-baseline"
      title={`${citation.title || 'SAP Help Citation'} - ${citation.section || ''}`}
    >
      <BookOpen className="w-2.5 h-2.5" />
      <span>[{index + 1}]</span>
    </button>
  );
};
