import React, { useMemo, useCallback, useEffect, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  BackgroundVariant,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomWorkflowNode } from './CustomWorkflowNode';
import { PhaseGroupNode } from './PhaseGroupNode';
import { WorkflowNode as WorkflowNodeModel, WorkflowEdge as WorkflowEdgeModel } from '../../types/workflow';

const nodeTypes = {
  custom: CustomWorkflowNode,
  phaseGroup: PhaseGroupNode,
};

// 5 Visual Phase Container Swimlanes (n8n-style)
const PHASE_CONTAINERS = [
  {
    id: 'phase-1-group',
    type: 'phaseGroup',
    position: { x: 35, y: 20 },
    data: {
      phaseNumber: 1,
      phaseTitle: 'PHASE 1 — REQUEST & PLANNING',
      phaseSubtitle: 'Sanitization • Decomposition • Dense Encoding',
      width: 320,
      height: 480,
    },
    selectable: false,
    draggable: false,
    zIndex: -1,
  },
  {
    id: 'phase-2-group',
    type: 'phaseGroup',
    position: { x: 395, y: 20 },
    data: {
      phaseNumber: 2,
      phaseTitle: 'PHASE 2 — KNOWLEDGE DISCOVERY',
      phaseSubtitle: 'pgvector <=> Cosine Discovery • Context Expansion',
      width: 320,
      height: 480,
    },
    selectable: false,
    draggable: false,
    zIndex: -1,
  },
  {
    id: 'phase-3-group',
    type: 'phaseGroup',
    position: { x: 755, y: 20 },
    data: {
      phaseNumber: 3,
      phaseTitle: 'PHASE 3 — SPECIALIST AGENTS',
      phaseSubtitle: 'Parallel Analysis (Procedure • Config • Rel • Troubleshoot)',
      width: 320,
      height: 565,
    },
    selectable: false,
    draggable: false,
    zIndex: -1,
  },
  {
    id: 'phase-4-group',
    type: 'phaseGroup',
    position: { x: 1115, y: 20 },
    data: {
      phaseNumber: 4,
      phaseTitle: 'PHASE 4 — EVIDENCE RECONCILIATION',
      phaseSubtitle: 'Ledger Aggregation • Sufficiency Audit • Gap Routing',
      width: 320,
      height: 480,
    },
    selectable: false,
    draggable: false,
    zIndex: -1,
  },
  {
    id: 'phase-5-group',
    type: 'phaseGroup',
    position: { x: 1475, y: 20 },
    data: {
      phaseNumber: 5,
      phaseTitle: 'PHASE 5 — SYNTHESIS & VALIDATION',
      phaseSubtitle: 'Grounded Synthesis • Citation Verification • Assembly',
      width: 320,
      height: 480,
    },
    selectable: false,
    draggable: false,
    zIndex: -1,
  },
];

interface WorkflowCanvasProps {
  nodes: WorkflowNodeModel[];
  edges: WorkflowEdgeModel[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  showMiniMap?: boolean;
  runId?: string;
}

const WorkflowCanvasInner: React.FC<WorkflowCanvasProps> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  showMiniMap = true,
  runId,
}) => {
  const { fitView } = useReactFlow();
  const prevRunIdRef = useRef<string | undefined>(undefined);

  // Map models to React Flow nodes with phase background containers
  const flowNodes: Node[] = useMemo(() => {
    const customNodes: Node[] = nodes.map((n) => ({
      id: n.node_id,
      type: 'custom',
      position: n.position || { x: 0, y: 0 },
      data: { ...n },
      selected: n.node_id === selectedNodeId,
      zIndex: 10,
    }));

    return [...PHASE_CONTAINERS, ...customNodes];
  }, [nodes, selectedNodeId]);

  // Determine directional handle connections
  const getHandles = (sourceId: string, targetId: string) => {
    // Vertical intra-phase connections (top -> bottom)
    if (
      (sourceId === 'node_request' && targetId === 'node_planner') ||
      (sourceId === 'node_planner' && targetId === 'node_encoder') ||
      (sourceId === 'node_retrieval' && targetId === 'node_context') ||
      (sourceId === 'node_ledger' && targetId === 'node_auditor') ||
      (sourceId === 'node_auditor' && targetId === 'node_gap_decision') ||
      (sourceId === 'node_synthesizer' && targetId === 'node_validators') ||
      (sourceId === 'node_validators' && targetId === 'node_output')
    ) {
      return { sourceHandle: 'bottom', targetHandle: 'top' };
    }

    // Gap investigation loop back to retrieval
    if (sourceId === 'node_gap_decision' && targetId === 'node_retrieval') {
      return { sourceHandle: 'bottom', targetHandle: 'bottom' };
    }

    // All horizontal inter-phase connections (right -> left)
    return { sourceHandle: 'right', targetHandle: 'left' };
  };

  // Map models to React Flow edges with smooth styling and handles
  const flowEdges: Edge[] = useMemo(() => {
    return edges.map((e) => {
      let strokeColor = '#334155'; // default slate-700
      let strokeWidth = 1.5;

      if (e.status === 'active' || e.animated) {
        strokeColor = '#06b6d4'; // cyan
        strokeWidth = 2.5;
      } else if (e.status === 'completed') {
        strokeColor = '#10b981'; // emerald
        strokeWidth = 2.0;
      } else if (e.status === 'blocked') {
        strokeColor = '#f59e0b'; // amber
        strokeWidth = 2.0;
      }

      const handles = getHandles(e.source_node_id, e.target_node_id);

      return {
        id: e.edge_id,
        source: e.source_node_id,
        target: e.target_node_id,
        sourceHandle: handles.sourceHandle,
        targetHandle: handles.targetHandle,
        type: e.edge_id.includes('loop') ? 'smoothstep' : 'default',
        animated: e.animated || e.status === 'active',
        label: e.label,
        labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace', fontWeight: 600 },
        labelBgStyle: { fill: '#090d16', fillOpacity: 0.9, stroke: '#1e293b', strokeWidth: 1 },
        labelBgPadding: [6, 3] as [number, number],
        labelBgBorderRadius: 4,
        style: {
          stroke: strokeColor,
          strokeWidth,
        },
      };
    });
  }, [edges]);

  // Fit view once on run change or initial load, without resetting on every SSE event
  useEffect(() => {
    if (runId && runId !== prevRunIdRef.current) {
      prevRunIdRef.current = runId;
      setTimeout(() => {
        fitView({ padding: 0.12, duration: 400 });
      }, 100);
    }
  }, [runId, fitView]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.type === 'custom') {
        onSelectNode(node.id);
      }
    },
    [onSelectNode]
  );

  const handlePaneClick = useCallback(() => {
    onSelectNode(null);
  }, [onSelectNode]);

  return (
    <div className="w-full h-full bg-slate-950 relative overflow-hidden select-none">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        minZoom={0.2}
        maxZoom={1.8}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          color="#1e293b"
          gap={24}
          size={1}
          variant={BackgroundVariant.Dots}
        />
        <Controls
          className="!bg-slate-900 !border !border-slate-800 !text-slate-300 shadow-xl [&>button]:!border-slate-800 [&>button]:!bg-slate-900 [&>button:hover]:!bg-slate-800 [&>button]:!fill-slate-300"
          showInteractive={false}
        />
        {showMiniMap && (
          <MiniMap
            className="!bg-slate-900/90 !border !border-slate-800 rounded-xl overflow-hidden shadow-2xl backdrop-blur-sm"
            nodeColor={(n) => {
              if (n.type === 'phaseGroup') return 'rgba(30, 41, 59, 0.3)';
              const data = n.data as any;
              if (data?.status === 'running') return '#06b6d4';
              if (data?.status === 'succeeded') return '#10b981';
              if (data?.status === 'blocked') return '#f59e0b';
              if (data?.status === 'failed') return '#f43f5e';
              if (data?.status === 'skipped') return '#334155';
              return '#475569';
            }}
            maskColor="rgba(15, 23, 42, 0.75)"
          />
        )}
      </ReactFlow>
    </div>
  );
};

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
};
