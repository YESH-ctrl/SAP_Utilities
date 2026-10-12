import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import {
  createAgenticRun,
  getAgenticRun,
  listAgenticRuns,
  cancelAgenticRun,
  subscribeToRunEvents
} from '../services/agenticApi';
import { FinalAgenticResponse, EvidenceItem } from '../types/agentic';
import { RunSnapshot, WorkflowEvent, NodeStatus, WorkflowNode } from '../types/workflow';

export interface AgenticChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  runId?: string;
  isLoading?: boolean;
  loadingStage?: string;
  response?: FinalAgenticResponse;
  error?: string;
}

interface AgenticWorkflowContextType {
  // Chat state
  messages: AgenticChatMessage[];
  sendMessage: (query: string) => Promise<void>;
  clearChat: () => void;

  // Active run & observability state
  activeRunId: string | null;
  activeRun: RunSnapshot | null;
  selectedRun: RunSnapshot | null;
  runsHistory: RunSnapshot[];
  isExecuting: boolean;
  currentStage: string;
  error: string | null;
  selectRun: (runId: string) => Promise<void>;
  cancelCurrentRun: () => Promise<void>;
  refreshHistory: () => Promise<void>;

  // Evidence drawer state (for citation inspection in chatbot)
  selectedEvidence: EvidenceItem | null;
  isEvidenceDrawerOpen: boolean;
  openEvidenceDetail: (evidence: EvidenceItem) => void;
  closeEvidenceDrawer: () => void;
}

const AgenticWorkflowContext = createContext<AgenticWorkflowContextType | null>(null);

export const AgenticWorkflowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<AgenticChatMessage[]>(() => {
    const saved = localStorage.getItem('sap_agentic_chat_messages');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  });

  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<RunSnapshot | null>(null);
  const [selectedRun, setSelectedRun] = useState<RunSnapshot | null>(null);
  const [runsHistory, setRunsHistory] = useState<RunSnapshot[]>([]);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<string>('Ready');
  const [error, setError] = useState<string | null>(null);

  // Evidence detail drawer
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);

  // SSE subscription ref
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Persist chat messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('sap_agentic_chat_messages', JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to persist agentic chat messages', e);
    }
  }, [messages]);

  // Load initial run history on mount
  useEffect(() => {
    refreshHistory();
  }, []);

  const refreshHistory = async () => {
    try {
      const history = await listAgenticRuns(20);
      setRunsHistory(history);
      if (!selectedRun && history.length > 0) {
        try {
          const fullSnap = await getAgenticRun(history[0].run_id);
          setSelectedRun(fullSnap);
        } catch {
          setSelectedRun(history[0]);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch run history:', err);
    }
  };

  const handleIncomingEvent = (evt: WorkflowEvent) => {
    if (evt.summary) {
      setCurrentStage(evt.summary);
    }

    setActiveRun((prev) => {
      if (!prev) return prev;

      // Duplicate sequence check
      if (prev.events.some((e) => e.sequence === evt.sequence)) {
        return prev;
      }

      const updatedEvents = [...prev.events, evt];
      let updatedStatus = prev.status;
      let updatedStage = evt.summary || prev.current_stage;

      // Update nodes
      const updatedNodes = prev.nodes.map((node) => {
        if (node.node_id === evt.node_id) {
          return {
            ...node,
            status: evt.status || node.status,
            started_at: evt.event_type === 'node_started' ? evt.timestamp : node.started_at,
            completed_at: [
              'node_succeeded',
              'node_partial',
              'node_failed',
              'node_blocked',
              'node_skipped'
            ].includes(evt.event_type)
              ? evt.timestamp
              : node.completed_at,
            duration_ms: typeof evt.duration_ms === 'number' ? evt.duration_ms : node.duration_ms,
            input_summary: evt.input_summary || node.input_summary,
            output_summary: evt.output_summary || node.output_summary,
            summary: evt.summary || node.summary,
            evidence_refs: evt.evidence_refs || node.evidence_refs,
            metrics: { ...node.metrics, ...(evt.metrics || {}) },
            error_summary:
              typeof evt.error === 'string'
                ? evt.error
                : evt.error?.message || node.error_summary,
            predecessor_node_id: evt.predecessor_node_id || node.predecessor_node_id,
            successor_node_id: evt.successor_node_id || node.successor_node_id,
            tools_called:
              evt.tools_called && evt.tools_called.length > 0
                ? evt.tools_called
                : node.tools_called,
            handoff_summary: evt.handoff_summary || node.handoff_summary,
          };
        }
        return node;
      });

      // Update edges: animate active edge
      const updatedEdges = prev.edges.map((edge) => {
        if (edge.target_node_id === evt.node_id) {
          if (evt.event_type === 'node_started') {
            return { ...edge, status: 'active', animated: true };
          } else if (['node_succeeded', 'node_partial'].includes(evt.event_type)) {
            return { ...edge, status: 'completed', animated: false };
          } else if (['node_blocked', 'node_failed'].includes(evt.event_type)) {
            return { ...edge, status: 'blocked', animated: false };
          }
        }
        return edge;
      });

      // Terminal event check
      if (evt.event_type === 'run_completed') {
        updatedStatus = evt.status === 'partial' ? 'partial' : 'succeeded';
      } else if (evt.event_type === 'run_failed') {
        updatedStatus = 'failed';
      } else if (evt.event_type === 'run_cancelled') {
        updatedStatus = 'cancelled';
      }

      const updatedSnapshot: RunSnapshot = {
        ...prev,
        status: updatedStatus,
        current_stage: updatedStage,
        nodes: updatedNodes,
        edges: updatedEdges,
        events: updatedEvents,
      };

      // Keep selectedRun in sync if currently viewing active run
      setSelectedRun((cur) => (cur?.run_id === prev.run_id ? updatedSnapshot : cur));
      return updatedSnapshot;
    });

    // Update the chatbot's pending message loading stage
    setMessages((prevMsgs) =>
      prevMsgs.map((msg) =>
        msg.isLoading
          ? {
              ...msg,
              loadingStage: evt.summary || msg.loadingStage,
            }
          : msg
      )
    );
  };

  const finalizeRun = async (rId: string, assistantMsgId: string) => {
    setIsExecuting(false);
    try {
      const finalSnap = await getAgenticRun(rId);
      setActiveRun(finalSnap);
      setSelectedRun((cur) => (cur?.run_id === rId ? finalSnap : cur));

      // Append final snapshot to history list
      setRunsHistory((prev) => {
        const filtered = prev.filter((r) => r.run_id !== rId);
        return [finalSnap, ...filtered];
      });

      // Update chatbot assistant message with final answer and response object
      const answerContent =
        finalSnap.final_response?.answer ||
        (finalSnap.response_mode === 'evidence_only'
          ? 'Synthesis unavailable due to upstream provider quota limits (HTTP 429). Verified documentation evidence passages have been preserved below.'
          : finalSnap.status === 'failed'
          ? `Execution failed: ${finalSnap.error_message || 'Unknown error'}`
          : 'Workflow completed successfully.');

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: answerContent,
                isLoading: false,
                loadingStage: undefined,
                response: finalSnap.final_response,
                error: finalSnap.error_message,
              }
            : m
        )
      );
    } catch (err: any) {
      console.error('Failed to finalize run snapshot:', err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: 'Failed to retrieve final execution results.',
                isLoading: false,
                error: err?.message,
              }
            : m
        )
      );
    }
  };

  const sendMessage = async (queryText: string) => {
    const q = queryText.trim();
    if (!q || isExecuting) return;

    setError(null);
    setIsExecuting(true);
    setCurrentStage('Submitting query...');

    // 1. Add user message
    const userMsgId = `user-${Date.now()}`;
    const userMsg: AgenticChatMessage = {
      id: userMsgId,
      role: 'user',
      content: q,
      timestamp: new Date().toISOString(),
    };

    // 2. Add loading assistant message
    const assistantMsgId = `asst-${Date.now()}`;
    const assistantMsg: AgenticChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isLoading: true,
      loadingStage: 'Request Accepted — initializing query planner...',
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    // 3. Cancel any previous SSE listener
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }

    try {
      // 4. Create execution run in backend
      const initialSnapshot = await createAgenticRun({
        query: q,
        timeout_seconds: 90.0,
        max_investigation_rounds: 2,
        allow_graph_expansion: true,
      });

      const rId = initialSnapshot.run_id;
      setActiveRunId(rId);
      setActiveRun(initialSnapshot);
      setSelectedRun(initialSnapshot);

      // Attach runId to assistant message
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsgId ? { ...m, runId: rId } : m))
      );

      // 5. Connect SSE stream
      let isDone = false;
      const cleanup = subscribeToRunEvents(
        rId,
        (evt: WorkflowEvent) => {
          handleIncomingEvent(evt);
          if (
            ['run_completed', 'run_failed', 'run_cancelled'].includes(evt.event_type) &&
            !isDone
          ) {
            isDone = true;
            // Short delay to allow backend to persist final snapshot
            setTimeout(() => {
              finalizeRun(rId, assistantMsgId);
            }, 600);
          }
        },
        (sseErr) => {
          console.warn('SSE event stream warning:', sseErr);
          // If SSE disconnects or fails, poll final status once after short wait
          if (!isDone) {
            setTimeout(() => {
              finalizeRun(rId, assistantMsgId);
            }, 3000);
          }
        }
      );
      unsubscribeRef.current = cleanup;
    } catch (err: any) {
      console.error('Run creation failed:', err);
      setError(err?.message || 'Agentic platform execution failed.');
      setIsExecuting(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: `Execution request error: ${err?.message || 'Failed to start agentic workflow.'}`,
                isLoading: false,
                error: err?.message,
              }
            : m
        )
      );
    }
  };

  const selectRun = async (runId: string) => {
    try {
      const snap = await getAgenticRun(runId);
      setSelectedRun(snap);
    } catch (err) {
      console.error(`Failed to select run ${runId}:`, err);
    }
  };

  const cancelCurrentRun = async () => {
    if (!activeRunId) return;
    try {
      await cancelAgenticRun(activeRunId);
      setIsExecuting(false);
      setCurrentStage('Run Cancelled');
      const updated = await getAgenticRun(activeRunId);
      setActiveRun(updated);
      setSelectedRun(updated);
    } catch (err) {
      console.error('Failed to cancel run:', err);
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('sap_agentic_chat_messages');
  };

  const openEvidenceDetail = (evidence: EvidenceItem) => {
    setSelectedEvidence(evidence);
    setIsEvidenceDrawerOpen(true);
  };

  const closeEvidenceDrawer = () => {
    setIsEvidenceDrawerOpen(false);
    setSelectedEvidence(null);
  };

  return (
    <AgenticWorkflowContext.Provider
      value={{
        messages,
        sendMessage,
        clearChat,
        activeRunId,
        activeRun,
        selectedRun,
        runsHistory,
        isExecuting,
        currentStage,
        error,
        selectRun,
        cancelCurrentRun,
        refreshHistory,
        selectedEvidence,
        isEvidenceDrawerOpen,
        openEvidenceDetail,
        closeEvidenceDrawer,
      }}
    >
      {children}
    </AgenticWorkflowContext.Provider>
  );
};

export const useAgenticWorkflow = () => {
  const context = useContext(AgenticWorkflowContext);
  if (!context) {
    throw new Error('useAgenticWorkflow must be used within an AgenticWorkflowProvider');
  }
  return context;
};
