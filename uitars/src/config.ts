/**
 * UI-TARS Configuration
 * Environment-aware configuration for connecting to Dolphin service
 */

interface Config {
  // WebSocket connection
  wsUrl: string;
  wsReconnectInterval: number;
  wsMaxReconnectAttempts: number;

  // API endpoints
  apiBaseUrl: string;

  // UI settings
  maxExecutionsDisplay: number;
  logRetentionMs: number;
  screenshotThumbnailSize: number;

  // Polling intervals (fallback if WS fails)
  pollInterval: number;

  // Feature flags
  enableDebugMode: boolean;
  enablePerformanceMonitoring: boolean;
}

const isDevelopment = process.env.NODE_ENV === 'development';

const config: Config = {
  // WebSocket - use environment variable or default
  wsUrl: process.env.REACT_APP_WS_URL ||
         (isDevelopment ? 'ws://localhost:8080/ws' : 'ws://dolphin-service:8080/ws'),

  wsReconnectInterval: parseInt(process.env.REACT_APP_WS_RECONNECT_INTERVAL || '3000', 10),
  wsMaxReconnectAttempts: parseInt(process.env.REACT_APP_WS_MAX_RECONNECT || '10', 10),

  // API
  apiBaseUrl: process.env.REACT_APP_API_URL ||
              (isDevelopment ? 'http://localhost:8080/api' : '/api'),

  // UI settings
  maxExecutionsDisplay: parseInt(process.env.REACT_APP_MAX_EXECUTIONS || '100', 10),
  logRetentionMs: parseInt(process.env.REACT_APP_LOG_RETENTION_MS || '3600000', 10), // 1 hour
  screenshotThumbnailSize: parseInt(process.env.REACT_APP_THUMBNAIL_SIZE || '200', 10),

  // Polling fallback
  pollInterval: parseInt(process.env.REACT_APP_POLL_INTERVAL || '5000', 10),

  // Feature flags
  enableDebugMode: process.env.REACT_APP_DEBUG === 'true' || isDevelopment,
  enablePerformanceMonitoring: process.env.REACT_APP_PERF_MONITORING === 'true',
};

// Logging helper
export const log = {
  debug: (...args: any[]) => {
    if (config.enableDebugMode) {
      console.log('[UI-TARS DEBUG]', ...args);
    }
  },
  info: (...args: any[]) => {
    console.info('[UI-TARS]', ...args);
  },
  warn: (...args: any[]) => {
    console.warn('[UI-TARS]', ...args);
  },
  error: (...args: any[]) => {
    console.error('[UI-TARS]', ...args);
  },
};

export default config;
