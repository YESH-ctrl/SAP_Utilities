import React, { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Loader2, StopCircle } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (query: string) => void;
  onClearChat: () => void;
  isLoading: boolean;
  loadingStage?: string | null;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onClearChat,
  isLoading,
  loadingStage,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shadow-lg relative">
      {/* Loading Stage Indicator */}
      {isLoading && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-sap-navy text-white text-xs px-4 py-1.5 rounded-full shadow-md flex items-center gap-2 border border-slate-700 animate-fade-in">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-sap-accent" />
          <span className="font-medium tracking-wide">{loadingStage || 'Processing query...'}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-end gap-2">
        <div className="flex-1 relative bg-slate-50 dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700 focus-within:border-sap-blue dark:focus-within:border-sap-blue focus-within:ring-2 focus-within:ring-sap-blue/20 transition-all shadow-xs">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about SAP Utilities documentation..."
            disabled={isLoading}
            className="w-full py-3 pl-4 pr-12 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none resize-none max-h-44"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2.5 bottom-2.5 p-2 rounded-lg bg-sap-blue text-white disabled:opacity-40 disabled:hover:bg-sap-blue hover:bg-sap-accent transition-all shadow-xs"
            title="Send Message (Enter)"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Clear Chat Button */}
        <button
          type="button"
          onClick={onClearChat}
          disabled={isLoading}
          className="p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors shrink-0"
          title="Clear Conversation"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
