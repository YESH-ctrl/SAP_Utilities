import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, ThumbsUp, ThumbsDown, RotateCcw, Clock, Layers, Sparkles, User } from 'lucide-react';
import { ChatMessage as ChatMessageType, Source } from '../../types/chat';
import { CitationBadge } from './Citation';

interface ChatMessageProps {
  message: ChatMessageType;
  isDevMode: boolean;
  onOpenSource: (source: Source) => void;
  onRegenerate?: (query: string) => void;
}

export const ChatMessageComponent: React.FC<ChatMessageProps> = ({
  message,
  isDevMode,
  onOpenSource,
  onRegenerate,
}) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end my-3 px-4">
        <div className="flex items-start gap-2 max-w-xl">
          <div className="bg-sap-blue text-white px-4 py-2.5 rounded-2xl rounded-tr-none shadow-sm text-sm font-medium leading-relaxed">
            {message.content}
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200 shrink-0">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start my-4 px-4">
      <div className="flex items-start gap-3 max-w-3xl w-full">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-sap-navy text-white flex items-center justify-center shrink-0 shadow-sm border border-slate-700">
          <Sparkles className="w-4 h-4 text-sap-accent" />
        </div>

        {/* Message Container */}
        <div className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-none p-5 shadow-xs">
          {/* Header metadata */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 dark:border-slate-800 text-xs">
            <span className="font-semibold text-sap-navy dark:text-slate-200 flex items-center gap-1.5">
              <span>SAP Utilities AI Assistant</span>
              <span className="text-[10px] font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                Grounded
              </span>
            </span>
            <span className="text-slate-600 dark:text-slate-400 text-[11px] font-mono">
              {message.timestamp}
            </span>
          </div>

          {/* Markdown Content */}
          <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed text-slate-800 dark:text-slate-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Inline Citations Reference Bar if available */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1">
                <span>Citations & References:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {message.citations.map((citation, idx) => (
                  <CitationBadge
                    key={citation.id || idx}
                    citation={citation}
                    index={idx}
                    onClick={() => {
                      const matchedSource = (message.sources || []).find(
                        (s) => s.id === citation.sourceId || s.title === citation.title
                      ) || {
                        id: citation.sourceId || `src_${idx}`,
                        source_id: citation.sourceId || `${idx}`,
                        title: citation.title || 'SAP Documentation',
                        document_name: 'SAP Help Portal',
                        section_title: citation.section,
                        content: citation.excerpt || '',
                        url: citation.url,
                      };
                      onOpenSource(matchedSource);
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Dev Mode Diagnostics Banner */}
          {isDevMode && message.metadata && (
            <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs font-mono text-amber-900 dark:text-amber-300 space-y-1">
              <div className="font-bold flex items-center justify-between">
                <span>[DEV METADATA] Request ID: {message.metadata.request_id}</span>
                <span className="flex items-center gap-1 text-[11px]">
                  <Clock className="w-3 h-3" /> Total: {message.metadata.latency_ms}ms
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
                <div>Dense: {message.metadata.dense_latency_ms ?? 'N/A'} ms</div>
                <div>Lexical: {message.metadata.lexical_latency_ms ?? 'N/A'} ms</div>
                <div>RRF: {message.metadata.rrf_latency_ms ?? 'N/A'} ms</div>
                <div>LLM: {message.metadata.llm_latency_ms ?? 'N/A'} ms</div>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-amber-500/20 text-[10px]">
                <span>Candidates: {message.metadata.candidate_count}</span>
                <span>Recovered H1: {message.metadata.recovered_count}</span>
                <span>Model: {message.metadata.model || 'gemini-2.5-flash'}</span>
              </div>
            </div>
          )}

          {/* Action Toolbar */}
          <div className="mt-4 pt-2 flex items-center justify-between text-slate-400 border-t border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1 text-xs"
                title="Copy response"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="text-[11px]">{copied ? 'Copied' : 'Copy'}</span>
              </button>

              {onRegenerate && (
                <button
                  onClick={() => onRegenerate(message.content)}
                  className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1 text-xs"
                  title="Regenerate answer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span className="text-[11px]">Regenerate</span>
                </button>
              )}
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
                className={`p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ${
                  feedback === 'up' ? 'text-emerald-500 font-bold' : 'text-slate-400'
                }`}
                title="Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
                className={`p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ${
                  feedback === 'down' ? 'text-rose-500 font-bold' : 'text-slate-400'
                }`}
                title="Not helpful"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
