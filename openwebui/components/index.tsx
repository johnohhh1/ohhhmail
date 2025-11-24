/**
 * UI-TARS Component Exports
 * Main entry point for Open-WebUI integration
 */

export { UITARSDebugPanel } from './UITARSDebugPanel';
export { EmailDashboard } from './EmailDashboard';
export { TaskManager } from './TaskManager';
export { Analytics } from './Analytics';
export { Dashboard } from './Dashboard';
export { CalendarView } from './CalendarView';
export { AgentMonitor } from './AgentMonitor';
export { Settings } from './Settings';
export { ChatWithAUBS } from './ChatWithAUBS';

// Re-export types
export type {
  DolphinTask,
  DolphinExecution,
  UITARSCheckpoint,
  UITARSSession,
  EmailProcessed,
  Action,
  AgentMetrics,
  SystemHealth,
  DolphinWebSocketMessage,
} from '../types';

// Re-export hooks
export { useDolphinWebSocket } from '../hooks/useDolphinWebSocket';
