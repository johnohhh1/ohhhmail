/**
 * Dashboard Component - Main overview for ohhhmail system
 * Shows email stats, agent performance, and recent activity
 */

import React, { useState, useEffect } from 'react';
import { useDolphinWebSocket } from '../hooks/useDolphinWebSocket';
import type { AgentMetrics, SystemHealth, EmailProcessed } from '../types';

interface DashboardProps {
  className?: string;
}

interface DashboardStats {
  total_emails: number;
  processed_today: number;
  pending_count: number;
  failed_count: number;
  avg_processing_time_ms: number;
  high_confidence_count: number;
}

export const Dashboard: React.FC<DashboardProps> = ({ className = '' }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [recentEmails, setRecentEmails] = useState<EmailProcessed[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected } = useDolphinWebSocket({
    url: 'ws://localhost:5000/ws',
    onExecutionUpdate: () => {
      // Refresh stats when new execution completes
      fetchDashboardData();
    },
  });

  const fetchDashboardData = async () => {
    try {
      const [statsRes, metricsRes, healthRes, emailsRes] = await Promise.all([
        fetch('http://localhost:5000/api/stats/dashboard'),
        fetch('http://localhost:5000/api/stats/agents'),
        fetch('http://localhost:5000/api/health'),
        fetch('http://localhost:5000/api/emails?limit=5&sort=recent'),
      ]);

      const statsData = await statsRes.json();
      const metricsData = await metricsRes.json();
      const healthData = await healthRes.json();
      const emailsData = await emailsRes.json();

      setStats(statsData);
      setAgentMetrics(metricsData.agents || []);
      setSystemHealth(healthData);
      setRecentEmails(emailsData.emails || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const getHealthStatusColor = (status?: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'down':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getSuccessRate = (metrics: AgentMetrics) => {
    const total = metrics.total_executions;
    if (total === 0) return 0;
    return ((metrics.success_count / total) * 100).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className={`dashboard ${className} flex items-center justify-center h-full`}>
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className={`dashboard ${className} p-6 bg-gray-100 overflow-y-auto`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">ohhhmail Dashboard</h1>
            <p className="text-gray-600 mt-1">AI-powered email processing system</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              onClick={fetchDashboardData}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Emails</p>
              <p className="text-3xl font-bold text-gray-800">{stats?.total_emails || 0}</p>
            </div>
            <div className="text-4xl">📧</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Processed Today</p>
              <p className="text-3xl font-bold text-blue-600">{stats?.processed_today || 0}</p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-3xl font-bold text-yellow-600">{stats?.pending_count || 0}</p>
            </div>
            <div className="text-4xl">⏳</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Process Time</p>
              <p className="text-3xl font-bold text-green-600">
                {stats?.avg_processing_time_ms ? `${(stats.avg_processing_time_ms / 1000).toFixed(1)}s` : 'N/A'}
              </p>
            </div>
            <div className="text-4xl">⚡</div>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">System Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.aubs_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">AUBS</p>
            <p className="text-xs text-gray-500">{systemHealth?.aubs_status || 'unknown'}</p>
          </div>
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.dolphin_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">Dolphin</p>
            <p className="text-xs text-gray-500">
              {systemHealth?.dolphin_workers || 0} workers
            </p>
          </div>
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.ollama_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">Ollama</p>
            <p className="text-xs text-gray-500">
              {systemHealth?.ollama_models?.length || 0} models
            </p>
          </div>
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.postgres_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">PostgreSQL</p>
            <p className="text-xs text-gray-500">{systemHealth?.postgres_status || 'unknown'}</p>
          </div>
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.redis_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">Redis</p>
            <p className="text-xs text-gray-500">{systemHealth?.redis_status || 'unknown'}</p>
          </div>
          <div className="flex flex-col items-center">
            <div className={`w-12 h-12 rounded-full ${getHealthStatusColor(systemHealth?.qdrant_status)} mb-2`} />
            <p className="text-sm font-medium text-gray-700">Qdrant</p>
            <p className="text-xs text-gray-500">{systemHealth?.qdrant_status || 'unknown'}</p>
          </div>
        </div>
      </div>

      {/* Agent Performance */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Agent Performance</h2>
        <div className="space-y-4">
          {agentMetrics.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No agent metrics available</p>
          ) : (
            agentMetrics.map((metrics) => (
              <div key={metrics.agent_type} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-800 capitalize">
                    {metrics.agent_type.replace('_', ' ')}
                  </h3>
                  <span className="text-sm font-medium text-green-600">
                    {getSuccessRate(metrics)}% success
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Executions</p>
                    <p className="font-semibold text-gray-800">{metrics.total_executions}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Success</p>
                    <p className="font-semibold text-green-600">{metrics.success_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Failed</p>
                    <p className="font-semibold text-red-600">{metrics.failure_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Avg Time</p>
                    <p className="font-semibold text-blue-600">
                      {(metrics.avg_duration_ms / 1000).toFixed(1)}s
                    </p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${getSuccessRate(metrics)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600">
                      Confidence: {(metrics.avg_confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {recentEmails.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No recent activity</p>
          ) : (
            recentEmails.map((email) => (
              <div
                key={email.email_id}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <div
                  className={`w-3 h-3 rounded-full ${
                    email.status === 'completed'
                      ? 'bg-green-500'
                      : email.status === 'failed'
                      ? 'bg-red-500'
                      : email.status === 'processing'
                      ? 'bg-blue-500 animate-pulse'
                      : 'bg-yellow-500'
                  }`}
                />
                <div className="flex-1">
                  <p className="font-medium text-gray-800 truncate">{email.subject}</p>
                  <p className="text-sm text-gray-600 truncate">{email.from}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {new Date(email.received_at).toLocaleTimeString()}
                  </p>
                  {email.confidence_score !== undefined && (
                    <p className="text-xs text-gray-500">
                      {(email.confidence_score * 100).toFixed(0)}% confidence
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
