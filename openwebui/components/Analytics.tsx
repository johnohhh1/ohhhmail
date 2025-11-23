/**
 * Analytics Dashboard Component - Embedded in Open-WebUI
 * Shows system performance metrics and agent statistics
 */

import React, { useState, useEffect } from 'react';
import type { AgentMetrics, SystemHealth } from '../types';

interface AnalyticsProps {
  className?: string;
}

interface ProcessingStats {
  total_emails: number;
  emails_today: number;
  emails_this_week: number;
  avg_processing_time_ms: number;
  success_rate: number;
  pending_count: number;
  failed_count: number;
}

export const Analytics: React.FC<AnalyticsProps> = ({ className = '' }) => {
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [processingStats, setProcessingStats] = useState<ProcessingStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  const fetchAnalytics = async () => {
    try {
      const [metricsRes, healthRes, statsRes] = await Promise.all([
        fetch(`/api/analytics/agents?range=${timeRange}`),
        fetch('/api/system/health'),
        fetch(`/api/analytics/processing?range=${timeRange}`),
      ]);

      const metrics = await metricsRes.json();
      const health = await healthRes.json();
      const stats = await statsRes.json();

      setAgentMetrics(metrics.agents || []);
      setSystemHealth(health);
      setProcessingStats(stats);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [timeRange]);

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'down':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}min`;
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 0.95) return 'text-green-600';
    if (rate >= 0.8) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={`analytics-dashboard ${className}`}>
      {/* Header */}
      <div className="p-4 bg-gray-800 text-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Analytics Dashboard</h2>
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 bg-gray-700 rounded text-sm"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button
              onClick={fetchAnalytics}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 overflow-y-auto">
        {isLoading ? (
          <div className="text-center text-gray-500">Loading analytics...</div>
        ) : (
          <>
            {/* System Health Overview */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">System Health</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {systemHealth && (
                  <>
                    <div className="bg-white rounded-lg shadow p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Dolphin Scheduler</span>
                        <div
                          className={`w-3 h-3 rounded-full ${getHealthColor(
                            systemHealth.dolphin_status
                          )}`}
                        />
                      </div>
                      <div className="mt-2 text-2xl font-bold">{systemHealth.dolphin_workers}</div>
                      <div className="text-xs text-gray-500">Active Workers</div>
                      <div className="text-sm text-gray-700 mt-1">
                        {systemHealth.dolphin_active_tasks} active tasks
                      </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">AUBS</span>
                        <div
                          className={`w-3 h-3 rounded-full ${getHealthColor(
                            systemHealth.aubs_status
                          )}`}
                        />
                      </div>
                      <div className="mt-2 text-lg font-semibold capitalize">
                        {systemHealth.aubs_status}
                      </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Ollama</span>
                        <div
                          className={`w-3 h-3 rounded-full ${getHealthColor(
                            systemHealth.ollama_status
                          )}`}
                        />
                      </div>
                      <div className="mt-2 text-2xl font-bold">
                        {systemHealth.ollama_models.length}
                      </div>
                      <div className="text-xs text-gray-500">Models Loaded</div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Vector Store</span>
                        <div
                          className={`w-3 h-3 rounded-full ${getHealthColor(
                            systemHealth.qdrant_status
                          )}`}
                        />
                      </div>
                      <div className="mt-2 text-lg font-semibold capitalize">
                        {systemHealth.qdrant_status}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Processing Statistics */}
            {processingStats && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Processing Statistics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-600 mb-1">Total Emails</div>
                    <div className="text-3xl font-bold text-blue-600">
                      {processingStats.total_emails}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Today: {processingStats.emails_today}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-600 mb-1">Success Rate</div>
                    <div
                      className={`text-3xl font-bold ${getSuccessRateColor(
                        processingStats.success_rate
                      )}`}
                    >
                      {(processingStats.success_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Failed: {processingStats.failed_count}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-600 mb-1">Avg Processing Time</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {formatDuration(processingStats.avg_processing_time_ms)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Per email</div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-600 mb-1">Pending</div>
                    <div className="text-3xl font-bold text-yellow-600">
                      {processingStats.pending_count}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Waiting to process</div>
                  </div>
                </div>
              </div>
            )}

            {/* Agent Performance Metrics */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">Agent Performance</h3>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Agent
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Executions
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Success Rate
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Avg Duration
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Avg Confidence
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                        Last Run
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {agentMetrics.map((agent) => (
                      <tr key={agent.agent_type} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className="font-medium capitalize">{agent.agent_type}</span>
                        </td>
                        <td className="px-4 py-3">{agent.total_executions}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden max-w-[100px]">
                              <div
                                className={`h-full ${
                                  agent.success_count / agent.total_executions >= 0.9
                                    ? 'bg-green-500'
                                    : agent.success_count / agent.total_executions >= 0.7
                                    ? 'bg-yellow-500'
                                    : 'bg-red-500'
                                }`}
                                style={{
                                  width: `${
                                    (agent.success_count / agent.total_executions) * 100
                                  }%`,
                                }}
                              />
                            </div>
                            <span className="text-sm">
                              {((agent.success_count / agent.total_executions) * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">{formatDuration(agent.avg_duration_ms)}</td>
                        <td className="px-4 py-3">
                          {agent.avg_confidence
                            ? (agent.avg_confidence * 100).toFixed(1) + '%'
                            : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {agent.last_execution
                            ? new Date(agent.last_execution).toLocaleString()
                            : 'Never'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Processing Timeline Chart Placeholder */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-semibold mb-4">Processing Timeline</h3>
              <div className="h-64 flex items-center justify-center text-gray-400">
                [Chart visualization would go here - integrate with charting library like
                Recharts or Chart.js]
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
