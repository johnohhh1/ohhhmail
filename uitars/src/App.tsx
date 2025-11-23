/**
 * UI-TARS Main Application Component
 * Manages WebSocket connection and routes to main panel
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import UITARSPanel from './UITARSPanel';
import config, { log } from './config';
import { Execution, WSMessage, ConnectionState } from './types';
import './App.css';

const App: React.FC = () => {
  const [executions, setExecutions] = useState<Map<string, Execution>>(new Map());
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    connected: false,
    reconnecting: false,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WSMessage = JSON.parse(event.data);
      log.debug('Received message:', message);

      setExecutions(prev => {
        const next = new Map(prev);
        const execution = next.get(message.execution_id);

        switch (message.type) {
          case 'execution_started':
            next.set(message.execution_id, message.data as Execution);
            break;

          case 'execution_updated':
          case 'execution_completed':
            if (execution) {
              next.set(message.execution_id, { ...execution, ...message.data });
            }
            break;

          case 'step_started':
          case 'step_completed':
            if (execution) {
              const stepIndex = execution.steps.findIndex(
                s => s.step_id === message.data.step_id
              );
              if (stepIndex >= 0) {
                const updatedSteps = [...execution.steps];
                updatedSteps[stepIndex] = { ...updatedSteps[stepIndex], ...message.data };
                next.set(message.execution_id, { ...execution, steps: updatedSteps });
              } else {
                execution.steps.push(message.data);
                next.set(message.execution_id, { ...execution });
              }
            }
            break;

          case 'decision_made':
            if (execution) {
              const stepId = message.data.step_id;
              const stepIndex = execution.steps.findIndex(s => s.step_id === stepId);
              if (stepIndex >= 0) {
                const updatedSteps = [...execution.steps];
                updatedSteps[stepIndex].agent_decisions.push(message.data.decision);
                next.set(message.execution_id, { ...execution, steps: updatedSteps });
              }
            }
            break;

          case 'screenshot_captured':
            if (execution) {
              const stepId = message.data.step_id;
              const stepIndex = execution.steps.findIndex(s => s.step_id === stepId);
              if (stepIndex >= 0) {
                const updatedSteps = [...execution.steps];
                updatedSteps[stepIndex].screenshots.push(message.data.screenshot);
                next.set(message.execution_id, { ...execution, steps: updatedSteps });
              }
            }
            break;

          case 'log_entry':
            if (execution) {
              const stepId = message.data.step_id;
              const stepIndex = execution.steps.findIndex(s => s.step_id === stepId);
              if (stepIndex >= 0) {
                const updatedSteps = [...execution.steps];
                updatedSteps[stepIndex].logs.push(message.data.log);
                next.set(message.execution_id, { ...execution, steps: updatedSteps });
              }
            }
            break;

          case 'error':
            log.error('Execution error:', message.data);
            break;

          default:
            log.warn('Unknown message type:', message.type);
        }

        return next;
      });
    } catch (error) {
      log.error('Error parsing WebSocket message:', error);
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log.debug('WebSocket already connected');
      return;
    }

    try {
      log.info('Connecting to Dolphin WebSocket:', config.wsUrl);
      const ws = new WebSocket(config.wsUrl);

      ws.onopen = () => {
        log.info('WebSocket connected');
        setConnectionState({ connected: true, reconnecting: false });
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        log.error('WebSocket error:', error);
        setConnectionState(prev => ({
          ...prev,
          error: 'Connection error'
        }));
      };

      ws.onclose = () => {
        log.warn('WebSocket disconnected');
        setConnectionState({ connected: false, reconnecting: true });
        wsRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < config.wsMaxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          log.info(`Reconnecting in ${config.wsReconnectInterval}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, config.wsReconnectInterval);
        } else {
          log.error('Max reconnection attempts reached');
          setConnectionState({
            connected: false,
            reconnecting: false,
            error: 'Failed to reconnect to Dolphin service'
          });
        }
      };

      wsRef.current = ws;
    } catch (error) {
      log.error('Error creating WebSocket:', error);
      setConnectionState({
        connected: false,
        reconnecting: false,
        error: 'Failed to create connection'
      });
    }
  }, [handleMessage]);

  // Initialize connection on mount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Manual reconnect handler
  const handleReconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connect();
  }, [connect]);

  return (
    <div className="app">
      <UITARSPanel
        executions={Array.from(executions.values())}
        connectionState={connectionState}
        onReconnect={handleReconnect}
      />
    </div>
  );
};

export default App;
