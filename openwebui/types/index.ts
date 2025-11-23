/**
 * UI-TARS Embedded Component Types
 * For Open-WebUI Integration
 */

export interface DolphinTask {
  task_id: string;
  task_type: 'TRIAGE_TASK' | 'VISION_TASK' | 'DEADLINE_TASK' | 'CONTEXT_TASK';
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  start_time?: string;
  end_time?: string;
  duration_ms?: number;
  worker_id?: string;
  output?: any;
  error?: string;
  retries?: number;
}

export interface DolphinExecution {
  execution_id: string;
  dag_id: string;
  email_id: string;
  status: 'running' | 'success' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  tasks: DolphinTask[];
  total_duration_ms?: number;
}

export interface UITARSCheckpoint {
  checkpoint_id: string;
  timestamp: string;
  checkpoint_name: string;
  agent_type: string;
  data: any;
  screenshot?: string; // base64 encoded image
  metrics: {
    memory_usage_mb: number;
    cpu_percent: number;
    gpu_percent?: number;
    gpu_memory_mb?: number;
  };
}

export interface UITARSSession {
  session_id: string;
  execution_id: string;
  email_id: string;
  started_at: string;
  completed_at?: string;
  status: 'active' | 'completed' | 'failed';
  checkpoints: UITARSCheckpoint[];
  result?: any;
  error?: string;
}

export interface EmailProcessed {
  email_id: string;
  subject: string;
  from: string;
  received_at: string;
  processed_at?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  execution_id?: string;
  agent_outputs: {
    triage?: any;
    vision?: any;
    deadline?: any;
    context?: any;
  };
  actions_taken: Action[];
  confidence_score?: number;
}

export interface Action {
  action_id: string;
  type: 'task_created' | 'calendar_scheduled' | 'notification_sent' | 'human_review';
  timestamp: string;
  details: any;
  status: 'pending' | 'completed' | 'failed';
  result?: any;
}

export interface AgentMetrics {
  agent_type: string;
  total_executions: number;
  success_count: number;
  failure_count: number;
  avg_duration_ms: number;
  avg_confidence: number;
  last_execution?: string;
}

export interface SystemHealth {
  dolphin_status: 'healthy' | 'degraded' | 'down';
  dolphin_workers: number;
  dolphin_active_tasks: number;
  aubs_status: 'healthy' | 'degraded' | 'down';
  ollama_status: 'healthy' | 'degraded' | 'down';
  ollama_models: string[];
  redis_status: 'healthy' | 'degraded' | 'down';
  postgres_status: 'healthy' | 'degraded' | 'down';
  qdrant_status: 'healthy' | 'degraded' | 'down';
}

export interface DolphinWebSocketMessage {
  type: 'execution_update' | 'task_update' | 'checkpoint' | 'error';
  data: any;
  timestamp: string;
}
