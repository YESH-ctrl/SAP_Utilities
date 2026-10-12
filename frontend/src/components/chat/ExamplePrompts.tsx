import React from 'react';
import { HelpCircle, Sparkles } from 'lucide-react';

interface ExamplePromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

const EXAMPLE_PROMPTS = [
  "What is premise in SAP Utilities?",
  "How do I perform reconnection of a utility service?",
  "What is the purpose of budget billing?",
  "Explain the dunning process in SAP Utilities.",
];

export const ExamplePrompts: React.FC<ExamplePromptsProps> = ({ onSelectPrompt }) => {
  return (
    <div className="max-w-2xl mx-auto my-8 p-6 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm text-center">
      <div className="w-12 h-12 rounded-full bg-sap-blue/10 text-sap-blue dark:text-sap-accent flex items-center justify-center mx-auto mb-3">
        <Sparkles className="w-6 h-6" />
      </div>
      <h2 className="text-lg font-bold text-sap-navy dark:text-slate-100 mb-1">
        SAP Utilities AI Knowledge Base
      </h2>
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
        Ask technical questions grounded directly in SAP Help Portal documentation.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
        {EXAMPLE_PROMPTS.map((prompt, index) => (
          <button
            key={index}
            onClick={() => onSelectPrompt(prompt)}
            className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-sap-blue/50 dark:hover:border-sap-blue/50 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-sap-blue/5 dark:hover:bg-sap-blue/10 transition-all text-xs font-medium text-slate-700 dark:text-slate-300 flex items-start gap-2 group"
          >
            <HelpCircle className="w-4 h-4 text-sap-blue dark:text-sap-accent shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
