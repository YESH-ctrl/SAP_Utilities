"""
Workflow Event and Graph Models for Live CrewAI Execution Canvas.
Strictly typed data schemas for nodes, edges, events, and run snapshots.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

from sap_rag.agentic.schemas.contracts import FinalAgenticResponse, ResponseMode, AnswerStatus


class WorkflowEventType(str, Enum):
    RUN_STARTED = "run_started"
    NODE_CREATED = "node_created"
    NODE_QUEUED = "node_queued"
    NODE_STARTED = "node_started"
    NODE_PROGRESS = "node_progress"
    NODE_SUCCEEDED = "node_succeeded"
    NODE_PARTIAL = "node_partial"
    NODE_FAILED = "node_failed"
    NODE_BLOCKED = "node_blocked"
    NODE_SKIPPED = "node_skipped"
    EDGE_ACTIVATED = "edge_activated"
    AGENT_FINDING = "agent_finding"
    EVIDENCE_ADDED = "evidence_added"
    VALIDATION_UPDATED = "validation_updated"
    RETRY_SCHEDULED = "retry_scheduled"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"
    HEARTBEAT = "heartbeat"


class NodeStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    EVIDENCE_ONLY = "evidence_only"
    WAITING = "waiting"


class NodeType(str, Enum):
    REQUEST = "request"
    PLANNER = "planner"
    ENCODER = "encoder"
    RETRIEVAL = "retrieval"
    CONTEXT_BUILDER = "context_builder"
    SPECIALIST = "specialist"
    AGGREGATOR = "aggregator"
    AUDITOR = "auditor"
    DECISION = "decision"
    SYNTHESIS = "synthesis"
    VALIDATOR = "validator"
    OUTPUT = "output"


class WorkflowNode(BaseModel):
    node_id: str
    node_type: NodeType
    label: str
    description: str
    status: NodeStatus = NodeStatus.PENDING
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    phase: Optional[int] = 1
    phase_title: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    agent_role: Optional[str] = None
    mechanism: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    summary: Optional[str] = None
    predecessor_node_id: Optional[str] = None
    successor_node_id: Optional[str] = None
    selection_reason: Optional[str] = None
    tools_called: List[str] = Field(default_factory=list)
    handoff_summary: Optional[str] = None
    evidence_refs: List[Any] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error_summary: Optional[str] = None
    round: Optional[int] = 1


class WorkflowEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None
    status: str = "pending"  # pending, active, completed, blocked
    condition: Optional[str] = None
    animated: bool = False

    @property
    def source(self) -> str:
        return self.source_node_id

    @property
    def target(self) -> str:
        return self.target_node_id


class WorkflowEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:10]}")
    run_id: str
    sequence: int = 0
    event_type: WorkflowEventType
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    agent_role: Optional[str] = None
    status: Optional[NodeStatus] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: Optional[float] = None
    summary: str
    predecessor_node_id: Optional[str] = None
    successor_node_id: Optional[str] = None
    selection_reason: Optional[str] = None
    tools_called: List[str] = Field(default_factory=list)
    handoff_summary: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    evidence_refs: List[Any] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Any] = None
    round: Optional[int] = None



class RunSnapshot(BaseModel):
    run_id: str
    query: str
    user_id: Optional[str] = None
    status: str = "queued"  # queued, running, succeeded, partial, failed, cancelled
    response_mode: str = ResponseMode.SYNTHESIZED_ANSWER.value
    answer_status: str = AnswerStatus.SYNTHESIS_COMPLETED.value
    current_stage: str = "Initializing"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: Optional[float] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    events: List[WorkflowEvent] = Field(default_factory=list)
    final_response: Optional[FinalAgenticResponse] = None
    error_message: Optional[str] = None

