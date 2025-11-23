/**
 * UI-TARS TypeScript Type Definitions
 * Matches Dolphin protocol schema
 */

// Execution Status
export type ExecutionStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

// Agent Decision Types
export interface AgentDecision {
  timestamp: string;
  agent_id: string;
  reasoning: string;
  action: string;
  confidence: number;
  tool_used?: string;
  parameters?: Record<string, any>;
}

// Screenshot/Visual Artifact
export interface Screenshot {
  id: string;
  timestamp: string;
  url: string;
  thumbnail_url?: string;
  width: number;
  height: number;
  description?: string;
}

// Execution Step
export interface ExecutionStep {
  step_id: string;
  step_number: number;
  name: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  agent_decisions: AgentDecision[];
  screenshots: Screenshot[];
  logs: LogEntry[];
  error?: string;
}

// Log Entry
export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  context?: Record<string, any>;
}

// Complete Execution Record
export interface Execution {
  execution_id: string;
  workflow_id: string;
  workflow_name: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  total_duration_ms?: number;
  steps: ExecutionStep[];
  metadata?: Record<string, any>;
}

// WebSocket Message Types
export type WSMessageType =
  | 'execution_started'
  | 'execution_updated'
  | 'execution_completed'
  | 'step_started'
  | 'step_completed'
  | 'decision_made'
  | 'screenshot_captured'
  | 'log_entry'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  timestamp: string;
  execution_id: string;
  data: any;
}

// Workflow Graph Node
export interface WorkflowNode {
  id: string;
  type: 'start' | 'agent' | 'decision' | 'action' | 'end';
  label: string;
  status?: ExecutionStatus;
  position?: { x: number; y: number };
  data?: Record<string, any>;
}

// Workflow Graph Edge
export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

// Workflow Graph
export interface WorkflowGraph {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

// Connection State
export interface ConnectionState {
  connected: boolean;
  reconnecting: boolean;
  error?: string;
  last_ping?: string;
}

// UI State
export interface UIState {
  selectedExecution?: string;
  selectedStep?: string;
  selectedScreenshot?: string;
  viewMode: 'timeline' | 'graph' | 'logs';
  filterStatus?: ExecutionStatus[];
  searchQuery?: string;
}

// Statistics
export interface ExecutionStats {
  total_executions: number;
  active_executions: number;
  completed_executions: number;
  failed_executions: number;
  avg_duration_ms: number;
  success_rate: number;
}
