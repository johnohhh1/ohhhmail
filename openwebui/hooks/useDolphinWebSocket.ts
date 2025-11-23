/**
 * Hook for connecting to Dolphin WebSocket
 * Receives real-time execution updates
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import type { DolphinWebSocketMessage, DolphinExecution, UITARSCheckpoint } from '../types';

interface UseDolphinWebSocketOptions {
  url?: string;
  reconnectInterval?: number;
  onExecutionUpdate?: (execution: DolphinExecution) => void;
  onCheckpoint?: (checkpoint: UITARSCheckpoint) => void;
  onError?: (error: Error) => void;
}

export function useDolphinWebSocket(options: UseDolphinWebSocketOptions = {}) {
  const {
    url = 'ws://dolphin:12345/ws',
    reconnectInterval = 5000,
    onExecutionUpdate,
    onCheckpoint,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<DolphinWebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[Dolphin WebSocket] Connected');
        setIsConnected(true);

        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: DolphinWebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Route message to appropriate handler
          switch (message.type) {
            case 'execution_update':
              onExecutionUpdate?.(message.data as DolphinExecution);
              break;
            case 'checkpoint':
              onCheckpoint?.(message.data as UITARSCheckpoint);
              break;
            case 'error':
              onError?.(new Error(message.data.error));
              break;
          }
        } catch (err) {
          console.error('[Dolphin WebSocket] Failed to parse message:', err);
          onError?.(err as Error);
        }
      };

      ws.onerror = (error) => {
        console.error('[Dolphin WebSocket] Error:', error);
        onError?.(new Error('WebSocket error'));
      };

      ws.onclose = () => {
        console.log('[Dolphin WebSocket] Disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[Dolphin WebSocket] Attempting reconnect...');
          connect();
        }, reconnectInterval);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[Dolphin WebSocket] Connection failed:', err);
      onError?.(err as Error);
    }
  }, [url, reconnectInterval, onExecutionUpdate, onCheckpoint, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[Dolphin WebSocket] Cannot send message - not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    disconnect,
    reconnect: connect,
  };
}
