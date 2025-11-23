/**
 * Workflow Graph Component
 * Visualizes execution as a DAG using ReactFlow
 */

import React, { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Execution } from './types';
import './WorkflowGraph.css';

interface Props {
  execution: Execution;
}

const WorkflowGraph: React.FC<Props> = ({ execution }) => {
  // Convert execution steps to ReactFlow nodes
  const nodes: Node[] = useMemo(() => {
    const nodeList: Node[] = [];

    // Start node
    nodeList.push({
      id: 'start',
      type: 'input',
      data: { label: 'Start' },
      position: { x: 250, y: 50 },
      style: {
        background: '#00d4ff',
        color: '#0a0e17',
        border: 'none',
        borderRadius: '8px',
        fontWeight: 600,
      },
    });

    // Step nodes
    execution.steps.forEach((step, idx) => {
      let background = '#1e2530';
      let borderColor = '#2d3748';

      if (step.status === 'running') {
        background = 'rgba(0, 212, 255, 0.2)';
        borderColor = '#00d4ff';
      } else if (step.status === 'completed') {
        background = 'rgba(16, 185, 129, 0.2)';
        borderColor = '#10b981';
      } else if (step.status === 'failed') {
        background = 'rgba(239, 68, 68, 0.2)';
        borderColor = '#ef4444';
      }

      nodeList.push({
        id: step.step_id,
        data: {
          label: (
            <div className="custom-node">
              <div className="node-number">{step.step_number}</div>
              <div className="node-name">{step.name}</div>
              <div className={`node-status status-${step.status}`}>
                {step.status}
              </div>
              {step.agent_decisions.length > 0 && (
                <div className="node-meta">
                  🤖 {step.agent_decisions.length} decisions
                </div>
              )}
              {step.screenshots.length > 0 && (
                <div className="node-meta">
                  📸 {step.screenshots.length} screenshots
                </div>
              )}
            </div>
          ),
        },
        position: { x: 250, y: 150 + idx * 200 },
        style: {
          background,
          border: `2px solid ${borderColor}`,
          borderRadius: '12px',
          padding: '12px',
          width: 220,
          color: '#e0e6ed',
        },
      });
    });

    // End node
    const endY = 150 + execution.steps.length * 200;
    const endStatus = execution.status;
    let endBackground = '#7c3aed';

    if (endStatus === 'completed') {
      endBackground = '#10b981';
    } else if (endStatus === 'failed') {
      endBackground = '#ef4444';
    }

    nodeList.push({
      id: 'end',
      type: 'output',
      data: { label: execution.status.toUpperCase() },
      position: { x: 250, y: endY },
      style: {
        background: endBackground,
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontWeight: 600,
      },
    });

    return nodeList;
  }, [execution]);

  // Convert execution flow to ReactFlow edges
  const edges: Edge[] = useMemo(() => {
    const edgeList: Edge[] = [];

    // Start to first step
    if (execution.steps.length > 0) {
      edgeList.push({
        id: 'start-to-first',
        source: 'start',
        target: execution.steps[0].step_id,
        animated: execution.steps[0].status === 'running',
        style: { stroke: '#00d4ff', strokeWidth: 2 },
      });
    }

    // Step to step edges
    for (let i = 0; i < execution.steps.length - 1; i++) {
      const current = execution.steps[i];
      const next = execution.steps[i + 1];

      edgeList.push({
        id: `${current.step_id}-to-${next.step_id}`,
        source: current.step_id,
        target: next.step_id,
        animated: next.status === 'running',
        style: {
          stroke: current.status === 'completed' ? '#10b981' :
                  current.status === 'failed' ? '#ef4444' :
                  '#2d3748',
          strokeWidth: 2,
        },
      });
    }

    // Last step to end
    if (execution.steps.length > 0) {
      const lastStep = execution.steps[execution.steps.length - 1];
      edgeList.push({
        id: 'last-to-end',
        source: lastStep.step_id,
        target: 'end',
        animated: execution.status === 'running',
        style: {
          stroke: execution.status === 'completed' ? '#10b981' :
                  execution.status === 'failed' ? '#ef4444' :
                  '#2d3748',
          strokeWidth: 2,
        },
      });
    }

    return edgeList;
  }, [execution]);

  return (
    <div className="workflow-graph">
      <div className="graph-header">
        <h2>{execution.workflow_name}</h2>
        <div className="graph-legend">
          <div className="legend-item">
            <span className="legend-dot status-running"></span>
            <span>Running</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot status-completed"></span>
            <span>Completed</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot status-failed"></span>
            <span>Failed</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot status-queued"></span>
            <span>Queued</span>
          </div>
        </div>
      </div>

      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.1}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
          attributionPosition="bottom-right"
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={16}
            size={1}
            color="#2d3748"
          />
          <Controls
            style={{
              background: '#1e2530',
              border: '1px solid #2d3748',
              borderRadius: '8px',
            }}
          />
          <MiniMap
            nodeColor={(node) => {
              if (node.id === 'start' || node.id === 'end') return '#00d4ff';
              const step = execution.steps.find(s => s.step_id === node.id);
              if (!step) return '#1e2530';
              if (step.status === 'running') return '#00d4ff';
              if (step.status === 'completed') return '#10b981';
              if (step.status === 'failed') return '#ef4444';
              return '#1e2530';
            }}
            style={{
              background: '#0a0e17',
              border: '1px solid #2d3748',
              borderRadius: '8px',
            }}
            maskColor="rgba(10, 14, 23, 0.8)"
          />
        </ReactFlow>
      </div>
    </div>
  );
};

export default WorkflowGraph;
