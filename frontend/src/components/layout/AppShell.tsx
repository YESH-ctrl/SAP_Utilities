import React, { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

interface AppShellProps {
  children: (props: { isDevMode: boolean }) => React.ReactNode;
  title: string;
  subtitle?: string;
}

export const AppShell: React.FC<AppShellProps> = ({ children, title, subtitle }) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('sap_theme') === 'dark';
  });

  const [isDevMode, setIsDevMode] = useState<boolean>(() => {
    return localStorage.getItem('sap_dev_mode') === 'true';
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('sap_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('sap_theme', 'light');
    }
  }, [isDarkMode]);

  useEffect(() => {
    localStorage.setItem('sap_dev_mode', String(isDevMode));
  }, [isDevMode]);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans overflow-hidden">
      {/* Fixed Left Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Topbar
          title={title}
          subtitle={subtitle}
          isDarkMode={isDarkMode}
          onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
          isDevMode={isDevMode}
          onToggleDevMode={() => setIsDevMode(!isDevMode)}
        />

        <main className="flex-1 overflow-hidden relative">
          {children({ isDevMode })}
        </main>
      </div>
    </div>
  );
};
