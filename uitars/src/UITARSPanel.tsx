/**
 * UI-TARS Main Panel Component
 * Primary dashboard interface for monitoring agent executions
 */

import React, { useState, useMemo } from 'react';
import { Execution, ConnectionState, ExecutionStatus, UIState } from './types';
import ExecutionDetail from './ExecutionDetail';
import WorkflowGraph from './WorkflowGraph';
import { formatDistanceToNow } from 'date-fns';
import './UITARSPanel.css';

interface Props {
  executions: Execution[];
  connectionState: ConnectionState;
  onReconnect: () => void;
}

const UITARSPanel: React.FC<Props> = ({ executions, connectionState, onReconnect }) => {
  const [uiState, setUIState] = useState<UIState>({
    viewMode: 'timeline',
    filterStatus: undefined,
    searchQuery: '',
  });

  // Sort executions by start time (newest first)
  const sortedExecutions = useMemo(() => {
    return [...executions].sort((a, b) =>
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    );
  }, [executions]);

  // Filter executions based on UI state
  const filteredExecutions = useMemo(() => {
    let filtered = sortedExecutions;

    if (uiState.filterStatus && uiState.filterStatus.length > 0) {
      filtered = filtered.filter(e => uiState.filterStatus!.includes(e.status));
    }

    if (uiState.searchQuery) {
      const query = uiState.searchQuery.toLowerCase();
      filtered = filtered.filter(e =>
        e.workflow_name.toLowerCase().includes(query) ||
        e.execution_id.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [sortedExecutions, uiState.filterStatus, uiState.searchQuery]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = executions.length;
    const active = executions.filter(e => e.status === 'running').length;
    const completed = executions.filter(e => e.status === 'completed').length;
    const failed = executions.filter(e => e.status === 'failed').length;

    const completedExecutions = executions.filter(e => e.total_duration_ms);
    const avgDuration = completedExecutions.length > 0
      ? completedExecutions.reduce((sum, e) => sum + (e.total_duration_ms || 0), 0) / completedExecutions.length
      : 0;

    const successRate = total > 0 ? (completed / total) * 100 : 0;

    return { total, active, completed, failed, avgDuration, successRate };
  }, [executions]);

  // Selected execution
  const selectedExecution = useMemo(() => {
    return executions.find(e => e.execution_id === uiState.selectedExecution);
  }, [executions, uiState.selectedExecution]);

  // Status filter toggle
  const toggleStatusFilter = (status: ExecutionStatus) => {
    setUIState(prev => {
      const current = prev.filterStatus || [];
      const next = current.includes(status)
        ? current.filter(s => s !== status)
        : [...current, status];
      return { ...prev, filterStatus: next.length > 0 ? next : undefined };
    });
  };

  // Format duration
  const formatDuration = (ms?: number): string => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  return (
    <div className="uitars-panel">
      {/* Header */}
      <header className="panel-header">
        <div className="header-left">
          <h1 className="panel-title">
            <span className="title-icon">◉</span>
            UI-TARS
          </h1>
          <span className="subtitle">Agent Execution Monitor</span>
        </div>

        <div className="header-center">
          {/* Connection status */}
          <div className={`connection-status ${connectionState.connected ? 'connected' : 'disconnected'}`}>
            <span className="status-indicator"></span>
            <span className="status-text">
              {connectionState.connected ? 'Connected to Dolphin' :
               connectionState.reconnecting ? 'Reconnecting...' :
               'Disconnected'}
            </span>
            {!connectionState.connected && !connectionState.reconnecting && (
              <button className="btn-reconnect" onClick={onReconnect}>
                Reconnect
              </button>
            )}
          </div>
        </div>

        <div className="header-right">
          {/* Stats */}
          <div className="stats-summary">
            <div className="stat">
              <span className="stat-value">{stats.active}</span>
              <span className="stat-label">Active</span>
            </div>
            <div className="stat">
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat">
              <span className="stat-value">{stats.successRate.toFixed(0)}%</span>
              <span className="stat-label">Success</span>
            </div>
          </div>
        </div>
      </header>

      {/* Toolbar */}
      <div className="panel-toolbar">
        <div className="toolbar-left">
          {/* View mode switcher */}
          <div className="view-mode-switcher">
            <button
              className={`view-btn ${uiState.viewMode === 'timeline' ? 'active' : ''}`}
              onClick={() => setUIState(prev => ({ ...prev, viewMode: 'timeline' }))}
            >
              Timeline
            </button>
            <button
              className={`view-btn ${uiState.viewMode === 'graph' ? 'active' : ''}`}
              onClick={() => setUIState(prev => ({ ...prev, viewMode: 'graph' }))}
            >
              Graph
            </button>
            <button
              className={`view-btn ${uiState.viewMode === 'logs' ? 'active' : ''}`}
              onClick={() => setUIState(prev => ({ ...prev, viewMode: 'logs' }))}
            >
              Logs
            </button>
          </div>

          {/* Status filters */}
          <div className="status-filters">
            <button
              className={`filter-btn ${uiState.filterStatus?.includes('running') ? 'active status-running' : ''}`}
              onClick={() => toggleStatusFilter('running')}
            >
              Running
            </button>
            <button
              className={`filter-btn ${uiState.filterStatus?.includes('completed') ? 'active status-completed' : ''}`}
              onClick={() => toggleStatusFilter('completed')}
            >
              Completed
            </button>
            <button
              className={`filter-btn ${uiState.filterStatus?.includes('failed') ? 'active status-failed' : ''}`}
              onClick={() => toggleStatusFilter('failed')}
            >
              Failed
            </button>
          </div>
        </div>

        <div className="toolbar-right">
          {/* Search */}
          <input
            type="text"
            className="search-input"
            placeholder="Search executions..."
            value={uiState.searchQuery}
            onChange={(e) => setUIState(prev => ({ ...prev, searchQuery: e.target.value }))}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="panel-content">
        {/* Execution list */}
        <div className="execution-list">
          <div className="list-header">
            <h3>Executions ({filteredExecutions.length})</h3>
          </div>
          <div className="list-body">
            {filteredExecutions.length === 0 ? (
              <div className="empty-state">
                <p>No executions {uiState.filterStatus || uiState.searchQuery ? 'match your filters' : 'yet'}</p>
              </div>
            ) : (
              filteredExecutions.map(execution => (
                <div
                  key={execution.execution_id}
                  className={`execution-item ${execution.execution_id === uiState.selectedExecution ? 'selected' : ''} ${execution.status}`}
                  onClick={() => setUIState(prev => ({
                    ...prev,
                    selectedExecution: execution.execution_id
                  }))}
                >
                  <div className="item-header">
                    <span className={`status-badge status-${execution.status}`}>
                      {execution.status}
                    </span>
                    <span className="execution-time">
                      {formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })}
                    </span>
                  </div>
                  <div className="item-name">{execution.workflow_name}</div>
                  <div className="item-meta">
                    <span className="meta-item">
                      {execution.steps.length} steps
                    </span>
                    <span className="meta-item">
                      {formatDuration(execution.total_duration_ms)}
                    </span>
                  </div>
                  {execution.status === 'running' && (
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${(execution.steps.filter(s => s.status === 'completed').length / execution.steps.length) * 100}%`
                        }}
                      />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Detail view */}
        <div className="execution-detail-container">
          {selectedExecution ? (
            uiState.viewMode === 'graph' ? (
              <WorkflowGraph execution={selectedExecution} />
            ) : (
              <ExecutionDetail
                execution={selectedExecution}
                viewMode={uiState.viewMode}
              />
            )
          ) : (
            <div className="empty-detail">
              <p>Select an execution to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UITARSPanel;
