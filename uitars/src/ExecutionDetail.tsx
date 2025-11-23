/**
 * Execution Detail Component
 * Shows timeline, screenshots, agent decisions, and logs
 */

import React, { useState, useMemo } from 'react';
import { Execution, ExecutionStep, Screenshot, AgentDecision, LogEntry } from './types';
import { format } from 'date-fns';
import './ExecutionDetail.css';

interface Props {
  execution: Execution;
  viewMode: 'timeline' | 'logs';
}

const ExecutionDetail: React.FC<Props> = ({ execution, viewMode }) => {
  const [selectedStep, setSelectedStep] = useState<string | undefined>(undefined);
  const [selectedScreenshot, setSelectedScreenshot] = useState<Screenshot | undefined>(undefined);
  const [logLevel, setLogLevel] = useState<'all' | 'error' | 'warning' | 'info'>('all');

  // Get selected step data
  const stepData = useMemo(() => {
    return execution.steps.find(s => s.step_id === selectedStep);
  }, [execution, selectedStep]);

  // Aggregate all logs
  const allLogs = useMemo(() => {
    const logs: (LogEntry & { step_name: string })[] = [];
    execution.steps.forEach(step => {
      step.logs.forEach(log => {
        logs.push({ ...log, step_name: step.name });
      });
    });
    return logs.sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [execution]);

  // Filter logs by level
  const filteredLogs = useMemo(() => {
    if (logLevel === 'all') return allLogs;
    return allLogs.filter(log => log.level === logLevel);
  }, [allLogs, logLevel]);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return format(new Date(timestamp), 'HH:mm:ss.SSS');
  };

  // Format duration
  const formatDuration = (ms?: number): string => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  if (viewMode === 'logs') {
    return (
      <div className="execution-detail logs-view">
        <div className="detail-header">
          <h2>{execution.workflow_name}</h2>
          <div className="log-controls">
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value as any)}
              className="log-level-select"
            >
              <option value="all">All Levels</option>
              <option value="error">Errors</option>
              <option value="warning">Warnings</option>
              <option value="info">Info</option>
            </select>
          </div>
        </div>

        <div className="logs-container">
          {filteredLogs.length === 0 ? (
            <div className="empty-logs">No logs available</div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className={`log-entry log-${log.level}`}>
                <span className="log-time">{formatTime(log.timestamp)}</span>
                <span className={`log-level level-${log.level}`}>{log.level.toUpperCase()}</span>
                <span className="log-step">[{log.step_name}]</span>
                <span className="log-message">{log.message}</span>
                {log.context && (
                  <pre className="log-context">{JSON.stringify(log.context, null, 2)}</pre>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="execution-detail timeline-view">
      {/* Header */}
      <div className="detail-header">
        <div>
          <h2>{execution.workflow_name}</h2>
          <div className="execution-meta">
            <span className={`status-badge status-${execution.status}`}>{execution.status}</span>
            <span className="meta-text">Started {format(new Date(execution.started_at), 'PPpp')}</span>
            {execution.total_duration_ms && (
              <span className="meta-text">Duration: {formatDuration(execution.total_duration_ms)}</span>
            )}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="timeline-container">
        <div className="timeline">
          {execution.steps.map((step, idx) => (
            <div
              key={step.step_id}
              className={`timeline-step ${step.step_id === selectedStep ? 'selected' : ''} status-${step.status}`}
              onClick={() => setSelectedStep(step.step_id)}
            >
              <div className="step-number">{step.step_number}</div>
              <div className="step-connector">
                <div className="connector-line"></div>
              </div>
              <div className="step-content">
                <div className="step-header">
                  <h4 className="step-name">{step.name}</h4>
                  <span className={`step-status status-${step.status}`}>{step.status}</span>
                </div>
                <div className="step-meta">
                  <span>{formatTime(step.started_at)}</span>
                  {step.duration_ms && <span>{formatDuration(step.duration_ms)}</span>}
                </div>
                {step.error && (
                  <div className="step-error">{step.error}</div>
                )}

                {/* Quick indicators */}
                <div className="step-indicators">
                  {step.agent_decisions.length > 0 && (
                    <span className="indicator" title={`${step.agent_decisions.length} decisions`}>
                      🤖 {step.agent_decisions.length}
                    </span>
                  )}
                  {step.screenshots.length > 0 && (
                    <span className="indicator" title={`${step.screenshots.length} screenshots`}>
                      📸 {step.screenshots.length}
                    </span>
                  )}
                  {step.logs.length > 0 && (
                    <span className="indicator" title={`${step.logs.length} logs`}>
                      📝 {step.logs.length}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Step Detail Panel */}
        {stepData && (
          <div className="step-detail-panel">
            <div className="panel-header">
              <h3>{stepData.name}</h3>
              <button
                className="close-btn"
                onClick={() => setSelectedStep(undefined)}
              >
                ×
              </button>
            </div>

            <div className="panel-content">
              {/* Agent Decisions */}
              {stepData.agent_decisions.length > 0 && (
                <section className="panel-section">
                  <h4 className="section-title">Agent Decisions</h4>
                  {stepData.agent_decisions.map((decision, idx) => (
                    <div key={idx} className="decision-card">
                      <div className="decision-header">
                        <span className="decision-agent">{decision.agent_id}</span>
                        <span className="decision-time">{formatTime(decision.timestamp)}</span>
                      </div>
                      <div className="decision-action">
                        <strong>Action:</strong> {decision.action}
                      </div>
                      {decision.tool_used && (
                        <div className="decision-tool">
                          <strong>Tool:</strong> <code>{decision.tool_used}</code>
                        </div>
                      )}
                      <div className="decision-reasoning">
                        <strong>Reasoning:</strong> {decision.reasoning}
                      </div>
                      <div className="decision-confidence">
                        <strong>Confidence:</strong>
                        <div className="confidence-bar">
                          <div
                            className="confidence-fill"
                            style={{ width: `${decision.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span>{(decision.confidence * 100).toFixed(0)}%</span>
                      </div>
                      {decision.parameters && (
                        <details className="decision-params">
                          <summary>Parameters</summary>
                          <pre>{JSON.stringify(decision.parameters, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  ))}
                </section>
              )}

              {/* Screenshots */}
              {stepData.screenshots.length > 0 && (
                <section className="panel-section">
                  <h4 className="section-title">Screenshots</h4>
                  <div className="screenshot-grid">
                    {stepData.screenshots.map((screenshot) => (
                      <div
                        key={screenshot.id}
                        className="screenshot-thumbnail"
                        onClick={() => setSelectedScreenshot(screenshot)}
                      >
                        <img
                          src={screenshot.thumbnail_url || screenshot.url}
                          alt={screenshot.description || 'Screenshot'}
                        />
                        <div className="screenshot-info">
                          <span className="screenshot-time">{formatTime(screenshot.timestamp)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Logs */}
              {stepData.logs.length > 0 && (
                <section className="panel-section">
                  <h4 className="section-title">Logs ({stepData.logs.length})</h4>
                  <div className="step-logs">
                    {stepData.logs.map((log, idx) => (
                      <div key={idx} className={`log-entry log-${log.level}`}>
                        <span className="log-time">{formatTime(log.timestamp)}</span>
                        <span className={`log-level level-${log.level}`}>{log.level}</span>
                        <span className="log-message">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Screenshot Modal */}
      {selectedScreenshot && (
        <div className="screenshot-modal" onClick={() => setSelectedScreenshot(undefined)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedScreenshot(undefined)}>
              ×
            </button>
            <img
              src={selectedScreenshot.url}
              alt={selectedScreenshot.description || 'Screenshot'}
            />
            {selectedScreenshot.description && (
              <p className="screenshot-description">{selectedScreenshot.description}</p>
            )}
            <div className="screenshot-metadata">
              <span>{formatTime(selectedScreenshot.timestamp)}</span>
              <span>{selectedScreenshot.width} × {selectedScreenshot.height}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionDetail;
