import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { ChatPage } from '../pages/ChatPage';
import { SearchPage } from '../pages/SearchPage';
import { RetrievalInspectorPage } from '../pages/RetrievalInspectorPage';
import { EvaluationPage } from '../pages/EvaluationPage';
import { HealthPage } from '../pages/HealthPage';
import { AgenticIntelligencePage } from '../pages/AgenticIntelligencePage';
import { WorkflowCanvasPage } from '../pages/WorkflowCanvasPage';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Navigate to="/chat" replace />}
        />

        <Route
          path="/chat"
          element={
            <AppShell
              title="SAP Utilities AI Assistant"
              subtitle="Grounded Q&A over SAP Help Portal documentation."
            >
              {({ isDevMode }) => <ChatPage isDevMode={isDevMode} />}
            </AppShell>
          }
        />

        <Route
          path="/agentic"
          element={
            <AppShell
              title="SAP Agentic Knowledge Intelligence"
              subtitle="Independent multi-agent investigation & grounded synthesis over SAP docs."
            >
              {() => <AgenticIntelligencePage />}
            </AppShell>
          }
        />

        <Route
          path="/workflow-canvas"
          element={
            <AppShell
              title="Live Multi-Agent Execution Canvas"
              subtitle="Real-time n8n-style agent orchestration observability & artifact inspection."
            >
              {() => <WorkflowCanvasPage />}
            </AppShell>
          }
        />

        <Route
          path="/search"
          element={
            <AppShell
              title="Documentation Search"
              subtitle="Semantic vector & lexical search across SAP Utilities docs."
            >
              {() => <SearchPage />}
            </AppShell>
          }
        />

        <Route
          path="/retrieval"
          element={
            <AppShell
              title="Retrieval Pipeline Inspector"
              subtitle="Inspect dense, lexical, RRF fusion, and H1 hierarchy recovery."
            >
              {() => <RetrievalInspectorPage />}
            </AppShell>
          }
        />

        <Route
          path="/evaluation"
          element={
            <AppShell
              title="Benchmark Evaluation Metrics"
              subtitle="V5.5 retrieval engine Recall, MRR, NDCG, and failure analysis."
            >
              {() => <EvaluationPage />}
            </AppShell>
          }
        />

        <Route
          path="/health"
          element={
            <AppShell
              title="System Health & Telemetry"
              subtitle="Monitor database connections, vector store, and API status."
            >
              {() => <HealthPage />}
            </AppShell>
          }
        />

        {/* 404 Fallback */}
        <Route
          path="*"
          element={
            <AppShell title="404 Not Found" subtitle="Page does not exist.">
              {() => (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
                  <h2 className="text-xl font-bold text-sap-navy dark:text-slate-100 mb-2">
                    Page Not Found
                  </h2>
                  <p className="text-xs mb-4">The requested route does not exist.</p>
                  <a
                    href="/chat"
                    className="px-4 py-2 bg-sap-blue text-white text-xs font-semibold rounded-lg hover:bg-sap-accent"
                  >
                    Return to AI Assistant
                  </a>
                </div>
              )}
            </AppShell>
          }
        />
      </Routes>
    </BrowserRouter>
  );
};
