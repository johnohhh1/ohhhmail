/**
 * UI-TARS Debug Panel - Embedded in Open-WebUI
 * Shows execution timeline, agent decisions, and screenshots
 */

import React, { useState, useEffect } from 'react';
import { useDolphinWebSocket } from '../hooks/useDolphinWebSocket';
import type { DolphinExecution, UITARSSession, UITARSCheckpoint } from '../types';

interface UITARSDebugPanelProps {
  executionId?: string;
  autoRefresh?: boolean;
  className?: string;
}

export const UITARSDebugPanel: React.FC<UITARSDebugPanelProps> = ({
  executionId,
  autoRefresh = true,
  className = '',
}) => {
  const [selectedExecution, setSelectedExecution] = useState<DolphinExecution | null>(null);
  const [executions, setExecutions] = useState<DolphinExecution[]>([]);
  const [checkpoints, setCheckpoints] = useState<UITARSCheckpoint[]>([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<UITARSCheckpoint | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Connect to Dolphin WebSocket for real-time updates
  const { isConnected, lastMessage } = useDolphinWebSocket({
    onExecutionUpdate: (execution) => {
      setExecutions((prev) => {
        const index = prev.findIndex((e) => e.execution_id === execution.execution_id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = execution;
          return updated;
        }
        return [execution, ...prev];
      });

      if (execution.execution_id === selectedExecution?.execution_id) {
        setSelectedExecution(execution);
      }
    },
    onCheckpoint: (checkpoint) => {
      setCheckpoints((prev) => [...prev, checkpoint]);
    },
  });

  // Fetch executions from API
  const fetchExecutions = async () => {
    try {
      const response = await fetch('/api/dolphin/executions?limit=50');
      const data = await response.json();
      setExecutions(data.executions || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
      setIsLoading(false);
    }
  };

  // Fetch checkpoints for selected execution
  const fetchCheckpoints = async (execId: string) => {
    try {
      const response = await fetch(`/api/uitars/checkpoints?execution_id=${execId}`);
      const data = await response.json();
      setCheckpoints(data.checkpoints || []);
    } catch (error) {
      console.error('Failed to fetch checkpoints:', error);
    }
  };

  useEffect(() => {
    fetchExecutions();
    const interval = autoRefresh ? setInterval(fetchExecutions, 5000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  useEffect(() => {
    if (executionId) {
      const execution = executions.find((e) => e.execution_id === executionId);
      if (execution) {
        setSelectedExecution(execution);
        fetchCheckpoints(executionId);
      }
    }
  }, [executionId, executions]);

  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'running':
        return 'bg-blue-500 animate-pulse';
      case 'pending':
        return 'bg-gray-400';
      default:
        return 'bg-gray-300';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className={`ui-tars-debug-panel ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-800 text-white">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold">UI-TARS Debug Panel</h2>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-300">
            {isConnected ? 'Connected to Dolphin' : 'Disconnected'}
          </span>
        </div>
        <button
          onClick={fetchExecutions}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
        >
          Refresh
        </button>
      </div>

      <div className="flex h-full">
        {/* Execution List - Left Sidebar */}
        <div className="w-80 border-r border-gray-300 overflow-y-auto bg-gray-50">
          <div className="p-3 border-b border-gray-300">
            <h3 className="font-semibold text-gray-700">Recent Executions</h3>
          </div>
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading...</div>
          ) : (
            <div>
              {executions.map((execution) => (
                <button
                  key={execution.execution_id}
                  onClick={() => {
                    setSelectedExecution(execution);
                    fetchCheckpoints(execution.execution_id);
                  }}
                  className={`w-full p-3 text-left border-b border-gray-200 hover:bg-gray-100 transition ${
                    selectedExecution?.execution_id === execution.execution_id
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 truncate">
                      {execution.email_id.slice(0, 12)}...
                    </span>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        execution.status === 'success'
                          ? 'bg-green-100 text-green-700'
                          : execution.status === 'failed'
                          ? 'bg-red-100 text-red-700'
                          : execution.status === 'running'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {execution.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(execution.started_at).toLocaleString()}
                  </div>
                  {execution.total_duration_ms && (
                    <div className="text-xs text-gray-500">
                      Duration: {formatDuration(execution.total_duration_ms)}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          {selectedExecution ? (
            <div className="p-6">
              {/* Execution Details */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <h3 className="text-lg font-semibold mb-3">Execution Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-500">Execution ID:</span>
                    <div className="font-mono text-sm">{selectedExecution.execution_id}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Email ID:</span>
                    <div className="font-mono text-sm">{selectedExecution.email_id}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Status:</span>
                    <div className="font-semibold">{selectedExecution.status}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Duration:</span>
                    <div>{formatDuration(selectedExecution.total_duration_ms)}</div>
                  </div>
                </div>
              </div>

              {/* Task Timeline */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <h3 className="text-lg font-semibold mb-4">Task Timeline</h3>
                <div className="space-y-3">
                  {selectedExecution.tasks.map((task) => (
                    <div
                      key={task.task_id}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded"
                    >
                      <div className={`w-3 h-3 rounded-full ${getTaskStatusColor(task.status)}`} />
                      <div className="flex-1">
                        <div className="font-medium">{task.task_type}</div>
                        <div className="text-xs text-gray-500">
                          {task.start_time && (
                            <span>Started: {new Date(task.start_time).toLocaleTimeString()}</span>
                          )}
                          {task.duration_ms && <span> | {formatDuration(task.duration_ms)}</span>}
                        </div>
                        {task.error && (
                          <div className="text-xs text-red-600 mt-1">Error: {task.error}</div>
                        )}
                      </div>
                      {task.output && (
                        <button
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                          onClick={() => console.log(task.output)}
                        >
                          View Output
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Checkpoints */}
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-lg font-semibold mb-4">
                  Visual Checkpoints ({checkpoints.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {checkpoints.map((checkpoint) => (
                    <button
                      key={checkpoint.checkpoint_id}
                      onClick={() => setSelectedCheckpoint(checkpoint)}
                      className="text-left p-3 border border-gray-200 rounded hover:border-blue-500 hover:shadow transition"
                    >
                      <div className="font-medium text-sm mb-2">{checkpoint.checkpoint_name}</div>
                      <div className="text-xs text-gray-500 mb-2">
                        {new Date(checkpoint.timestamp).toLocaleString()}
                      </div>
                      {checkpoint.screenshot && (
                        <img
                          src={`data:image/png;base64,${checkpoint.screenshot}`}
                          alt={checkpoint.checkpoint_name}
                          className="w-full h-32 object-cover rounded"
                        />
                      )}
                      <div className="text-xs text-gray-600 mt-2">
                        CPU: {checkpoint.metrics.cpu_percent.toFixed(1)}% | Mem:{' '}
                        {checkpoint.metrics.memory_usage_mb.toFixed(0)}MB
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>

      {/* Checkpoint Detail Modal */}
      {selectedCheckpoint && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedCheckpoint(null)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-4xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold mb-4">{selectedCheckpoint.checkpoint_name}</h3>
            {selectedCheckpoint.screenshot && (
              <img
                src={`data:image/png;base64,${selectedCheckpoint.screenshot}`}
                alt={selectedCheckpoint.checkpoint_name}
                className="w-full mb-4 rounded"
              />
            )}
            <div className="mb-4">
              <h4 className="font-semibold mb-2">Metrics</h4>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                {JSON.stringify(selectedCheckpoint.metrics, null, 2)}
              </pre>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Data</h4>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto max-h-64">
                {JSON.stringify(selectedCheckpoint.data, null, 2)}
              </pre>
            </div>
            <button
              onClick={() => setSelectedCheckpoint(null)}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
