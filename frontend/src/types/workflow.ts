import { FinalAgenticResponse } from './agentic';

export type NodeStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'partial'
  | 'failed'
  | 'blocked'
  | 'skipped'
  | 'cancelled'
  | 'evidence_only'
  | 'waiting';

export type NodeType =
  | 'request'
  | 'planner'
  | 'encoder'
  | 'retrieval'
  | 'context_builder'
  | 'specialist'
  | 'aggregator'
  | 'auditor'
  | 'decision'
  | 'synthesis'
  | 'validator'
  | 'output';

export type WorkflowEventType =
  | 'run_started'
  | 'node_created'
  | 'node_queued'
  | 'node_started'
  | 'node_progress'
  | 'node_succeeded'
  | 'node_partial'
  | 'node_failed'
  | 'node_blocked'
  | 'node_skipped'
  | 'edge_activated'
  | 'agent_finding'
  | 'evidence_added'
  | 'validation_updated'
  | 'retry_scheduled'
  | 'run_completed'
  | 'run_failed'
  | 'run_cancelled'
  | 'heartbeat';

export interface WorkflowNode {
  node_id: string;
  node_type: NodeType;
  label: string;
  description: string;
  status: NodeStatus;
  position: { x: number; y: number };
  phase?: number;
  phase_title?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  agent_role?: string;
  mechanism?: string;
  input_summary?: string;
  output_summary?: string;
  summary?: string;
  predecessor_node_id?: string | null;
  successor_node_id?: string | null;
  selection_reason?: string;
  tools_called?: string[];
  handoff_summary?: string;
  evidence_refs?: Array<any>;
  metrics?: Record<string, any>;
  error_summary?: string;
  round?: number;
}

export interface WorkflowEdge {
  edge_id: string;
  source_node_id: string;
  target_node_id: string;
  label?: string;
  status: string;
  condition?: string;
  animated?: boolean;
}

export interface WorkflowEvent {
  event_id: string;
  run_id: string;
  sequence: number;
  event_type: WorkflowEventType;
  node_id?: string;
  node_type?: string;
  agent_role?: string;
  status?: NodeStatus;
  timestamp: string;
  duration_ms?: number;
  summary: string;
  predecessor_node_id?: string | null;
  successor_node_id?: string | null;
  selection_reason?: string;
  tools_called?: string[];
  handoff_summary?: string;
  input_summary?: string;
  output_summary?: string;
  evidence_refs?: Array<any>;
  metrics?: Record<string, any>;
  error?: { message: string; [key: string]: any };
  round?: number;
}

export interface RunSnapshot {
  run_id: string;
  query: string;
  status: 'queued' | 'running' | 'succeeded' | 'partial' | 'failed' | 'cancelled';
  response_mode: string;
  answer_status: string;
  current_stage: string;
  started_at: string;
  completed_at?: string;
  total_duration_ms?: number;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  events: WorkflowEvent[];
  final_response?: FinalAgenticResponse;
  error_message?: string;
}
