import React from 'react';
import { Sun, Moon, Code, ShieldCheck } from 'lucide-react';

interface TopbarProps {
  title: string;
  subtitle?: string;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
  isDevMode: boolean;
  onToggleDevMode: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  title,
  subtitle,
  isDarkMode,
  onToggleDarkMode,
  isDevMode,
  onToggleDevMode,
}) => {
  return (
    <header className="h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shadow-xs sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-bold text-sap-navy dark:text-slate-100 tracking-tight flex items-center gap-2">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Developer Mode Toggle */}
        <button
          onClick={onToggleDevMode}
          className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md border transition-all ${
            isDevMode
              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/40 shadow-xs'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
          title="Toggle developer diagnostic metadata"
        >
          <Code className="w-3.5 h-3.5" />
          <span>Dev Mode {isDevMode ? 'ON' : 'OFF'}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleDarkMode}
          className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 transition-colors"
          aria-label="Toggle theme"
        >
          {isDarkMode ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-600" />
          )}
        </button>

        {/* SAP Utilities Badge */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-sap-blue dark:text-sap-accent bg-sap-blue/10 dark:bg-sap-blue/20 px-3 py-1 rounded-md font-semibold border border-sap-blue/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SAP Utilities Engine</span>
        </div>
      </div>
    </header>
  );
};
