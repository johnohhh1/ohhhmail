/**
 * Agent Monitor Component - Real-time agent status and management
 * Shows agent performance, model selection, and enable/disable controls
 */

import React, { useState, useEffect } from 'react';
import { useDolphinWebSocket } from '../hooks/useDolphinWebSocket';
import type { AgentMetrics } from '../types';

interface AgentStatus {
  agent_type: string;
  enabled: boolean;
  current_model: string;
  available_models: string[];
  status: 'idle' | 'running' | 'error';
  current_task_id?: string;
  last_execution?: string;
  avg_response_time_ms: number;
  error_rate: number;
}

interface AgentMonitorProps {
  className?: string;
}

export const AgentMonitor: React.FC<AgentMonitorProps> = ({ className = '' }) => {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [metrics, setMetrics] = useState<Record<string, AgentMetrics>>({});
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected, lastMessage } = useDolphinWebSocket({
    url: 'ws://localhost:5000/ws',
    onExecutionUpdate: () => {
      fetchAgentStatus();
    },
  });

  const fetchAgentStatus = async () => {
    try {
      const [statusRes, metricsRes] = await Promise.all([
        fetch('http://localhost:5000/api/agents/status'),
        fetch('http://localhost:5000/api/stats/agents'),
      ]);

      const statusData = await statusRes.json();
      const metricsData = await metricsRes.json();

      setAgents(statusData.agents || []);

      // Convert metrics array to object keyed by agent_type
      const metricsMap: Record<string, AgentMetrics> = {};
      (metricsData.agents || []).forEach((m: AgentMetrics) => {
        metricsMap[m.agent_type] = m;
      });
      setMetrics(metricsMap);

      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch agent status:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const toggleAgentEnabled = async (agentType: string, enabled: boolean) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentType}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      fetchAgentStatus();
    } catch (error) {
      console.error('Failed to toggle agent:', error);
    }
  };

  const changeAgentModel = async (agentType: string, model: string) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentType}/model`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model }),
      });
      fetchAgentStatus();
    } catch (error) {
      console.error('Failed to change model:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-500 animate-pulse';
      case 'idle':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'triage':
        return '📋';
      case 'vision':
        return '👁️';
      case 'deadline':
        return '⏰';
      case 'context':
        return '🧠';
      default:
        return '🤖';
    }
  };

  const getSuccessRate = (agentType: string) => {
    const metric = metrics[agentType];
    if (!metric || metric.total_executions === 0) return 0;
    return ((metric.success_count / metric.total_executions) * 100).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className={`agent-monitor ${className} flex items-center justify-center h-full`}>
        <div className="text-gray-500">Loading agent status...</div>
      </div>
    );
  }

  return (
    <div className={`agent-monitor ${className} h-full flex flex-col bg-gray-100`}>
      {/* Header */}
      <div className="p-4 bg-white shadow">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Agent Monitor</h2>
            <p className="text-sm text-gray-600 mt-1">
              Real-time agent status and configuration
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              onClick={fetchAgentStatus}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agents.map(agent => {
            const agentMetrics = metrics[agent.agent_type];
            const successRate = getSuccessRate(agent.agent_type);

            return (
              <div
                key={agent.agent_type}
                className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition"
              >
                {/* Agent Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="text-4xl">{getAgentIcon(agent.agent_type)}</div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-800 capitalize">
                        {agent.agent_type} Agent
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                        <span className="text-sm text-gray-600 capitalize">{agent.status}</span>
                      </div>
                    </div>
                  </div>
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agent.enabled}
                      onChange={(e) => toggleAgentEnabled(agent.agent_type, e.target.checked)}
                      className="w-12 h-6 appearance-none bg-gray-300 rounded-full relative cursor-pointer transition-colors checked:bg-green-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">
                      {agent.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>

                {/* Model Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Model
                  </label>
                  <select
                    value={agent.current_model}
                    onChange={(e) => changeAgentModel(agent.agent_type, e.target.value)}
                    disabled={!agent.enabled}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  >
                    {agent.available_models.map(model => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {agent.available_models.length} models available
                  </p>
                </div>

                {/* Performance Metrics */}
                {agentMetrics && (
                  <div className="border-t border-gray-200 pt-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">Performance Metrics</h4>
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div>
                        <p className="text-xs text-gray-500">Total Executions</p>
                        <p className="text-lg font-bold text-gray-800">{agentMetrics.total_executions}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Success Rate</p>
                        <p className="text-lg font-bold text-green-600">{successRate}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Avg Response Time</p>
                        <p className="text-lg font-bold text-blue-600">
                          {(agentMetrics.avg_duration_ms / 1000).toFixed(2)}s
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Avg Confidence</p>
                        <p className="text-lg font-bold text-purple-600">
                          {(agentMetrics.avg_confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>

                    {/* Success Rate Bar */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>Success</span>
                        <span>
                          {agentMetrics.success_count}/{agentMetrics.total_executions}
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500"
                          style={{ width: `${successRate}%` }}
                        />
                      </div>
                    </div>

                    {/* Error Rate */}
                    {agentMetrics.failure_count > 0 && (
                      <div className="bg-red-50 border border-red-200 rounded p-2">
                        <p className="text-xs text-red-800">
                          {agentMetrics.failure_count} failed executions (
                          {((agentMetrics.failure_count / agentMetrics.total_executions) * 100).toFixed(1)}
                          % error rate)
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Current Task */}
                {agent.status === 'running' && agent.current_task_id && (
                  <div className="mt-4 bg-blue-50 border border-blue-200 rounded p-3">
                    <p className="text-sm font-medium text-blue-900">Currently Processing</p>
                    <p className="text-xs text-blue-700 font-mono mt-1">{agent.current_task_id}</p>
                  </div>
                )}

                {/* Last Execution */}
                {agent.last_execution && (
                  <div className="mt-4 text-xs text-gray-500">
                    Last execution: {new Date(agent.last_execution).toLocaleString()}
                  </div>
                )}

                {/* Agent Actions */}
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => setSelectedAgent(agent.agent_type)}
                    className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => {
                      fetch(`http://localhost:5000/api/agents/${agent.agent_type}/test`, {
                        method: 'POST',
                      });
                    }}
                    disabled={!agent.enabled}
                    className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                  >
                    Test Agent
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* No Agents Message */}
        {agents.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <p className="text-xl">No agents configured</p>
            <p className="text-sm mt-2">Configure agents in the settings</p>
          </div>
        )}
      </div>

      {/* Agent Details Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-2xl font-bold text-gray-800 capitalize">
                {selectedAgent} Agent Details
              </h3>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded p-4">
                <h4 className="font-semibold text-gray-800 mb-2">Configuration</h4>
                <pre className="text-sm bg-white p-3 rounded overflow-x-auto">
                  {JSON.stringify(
                    agents.find(a => a.agent_type === selectedAgent),
                    null,
                    2
                  )}
                </pre>
              </div>
              {metrics[selectedAgent] && (
                <div className="bg-gray-50 rounded p-4">
                  <h4 className="font-semibold text-gray-800 mb-2">Metrics</h4>
                  <pre className="text-sm bg-white p-3 rounded overflow-x-auto">
                    {JSON.stringify(metrics[selectedAgent], null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
