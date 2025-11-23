/**
 * Email Dashboard Component - Embedded in Open-WebUI
 * Shows processed emails, agent outputs, and actions taken
 */

import React, { useState, useEffect } from 'react';
import type { EmailProcessed, Action } from '../types';

interface EmailDashboardProps {
  className?: string;
  autoRefresh?: boolean;
}

export const EmailDashboard: React.FC<EmailDashboardProps> = ({
  className = '',
  autoRefresh = true,
}) => {
  const [emails, setEmails] = useState<EmailProcessed[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailProcessed | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'processing' | 'completed' | 'failed'>(
    'all'
  );
  const [isLoading, setIsLoading] = useState(true);

  const fetchEmails = async () => {
    try {
      const response = await fetch(`/api/emails?status=${filter}`);
      const data = await response.json();
      setEmails(data.emails || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
    const interval = autoRefresh ? setInterval(fetchEmails, 10000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [filter, autoRefresh]);

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'vendor':
        return 'bg-blue-100 text-blue-700';
      case 'staff':
        return 'bg-purple-100 text-purple-700';
      case 'customer':
        return 'bg-green-100 text-green-700';
      case 'system':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'processing':
        return 'bg-blue-500 animate-pulse';
      case 'pending':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'task_created':
        return '✓';
      case 'calendar_scheduled':
        return '📅';
      case 'notification_sent':
        return '📱';
      case 'human_review':
        return '👤';
      default:
        return '•';
    }
  };

  return (
    <div className={`email-dashboard ${className}`}>
      {/* Header */}
      <div className="p-4 bg-gray-800 text-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Email Processing Dashboard</h2>
          <div className="flex items-center gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-2 bg-gray-700 rounded text-sm"
            >
              <option value="all">All Emails</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <button
              onClick={fetchEmails}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* Email List */}
        <div className="w-96 border-r border-gray-300 overflow-y-auto bg-gray-50">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading emails...</div>
          ) : emails.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No emails found</div>
          ) : (
            <div>
              {emails.map((email) => (
                <button
                  key={email.email_id}
                  onClick={() => setSelectedEmail(email)}
                  className={`w-full p-4 text-left border-b border-gray-200 hover:bg-gray-100 transition ${
                    selectedEmail?.email_id === email.email_id
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : ''
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-800 truncate">{email.subject}</div>
                      <div className="text-sm text-gray-600 truncate">{email.from}</div>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(email.status)}`} />
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-500">
                      {new Date(email.received_at).toLocaleString()}
                    </span>
                    {email.agent_outputs.triage?.category && (
                      <span
                        className={`px-2 py-1 rounded ${getCategoryColor(
                          email.agent_outputs.triage.category
                        )}`}
                      >
                        {email.agent_outputs.triage.category}
                      </span>
                    )}
                  </div>
                  {email.confidence_score !== undefined && (
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              email.confidence_score >= 0.9
                                ? 'bg-green-500'
                                : email.confidence_score >= 0.7
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${email.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-600">
                          {(email.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Email Details */}
        <div className="flex-1 overflow-y-auto">
          {selectedEmail ? (
            <div className="p-6">
              {/* Email Header */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <h3 className="text-xl font-bold mb-2">{selectedEmail.subject}</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">From:</span>{' '}
                    <span className="font-medium">{selectedEmail.from}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Received:</span>{' '}
                    {new Date(selectedEmail.received_at).toLocaleString()}
                  </div>
                  <div>
                    <span className="text-gray-500">Status:</span>{' '}
                    <span className="font-semibold">{selectedEmail.status}</span>
                  </div>
                  {selectedEmail.processed_at && (
                    <div>
                      <span className="text-gray-500">Processed:</span>{' '}
                      {new Date(selectedEmail.processed_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>

              {/* Agent Outputs */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <h4 className="text-lg font-semibold mb-4">Agent Analysis</h4>
                <div className="space-y-4">
                  {/* Triage Output */}
                  {selectedEmail.agent_outputs.triage && (
                    <div className="p-3 bg-blue-50 rounded">
                      <div className="font-semibold text-blue-900 mb-2">Triage Agent</div>
                      <pre className="text-sm bg-white p-2 rounded overflow-x-auto">
                        {JSON.stringify(selectedEmail.agent_outputs.triage, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Vision Output */}
                  {selectedEmail.agent_outputs.vision && (
                    <div className="p-3 bg-purple-50 rounded">
                      <div className="font-semibold text-purple-900 mb-2">Vision Agent</div>
                      <pre className="text-sm bg-white p-2 rounded overflow-x-auto">
                        {JSON.stringify(selectedEmail.agent_outputs.vision, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Deadline Output */}
                  {selectedEmail.agent_outputs.deadline && (
                    <div className="p-3 bg-yellow-50 rounded">
                      <div className="font-semibold text-yellow-900 mb-2">Deadline Scanner</div>
                      <pre className="text-sm bg-white p-2 rounded overflow-x-auto">
                        {JSON.stringify(selectedEmail.agent_outputs.deadline, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Context Output */}
                  {selectedEmail.agent_outputs.context && (
                    <div className="p-3 bg-green-50 rounded">
                      <div className="font-semibold text-green-900 mb-2">Context Agent</div>
                      <pre className="text-sm bg-white p-2 rounded overflow-x-auto max-h-64">
                        {JSON.stringify(selectedEmail.agent_outputs.context, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions Taken */}
              <div className="bg-white rounded-lg shadow p-4">
                <h4 className="text-lg font-semibold mb-4">
                  Actions Taken ({selectedEmail.actions_taken.length})
                </h4>
                {selectedEmail.actions_taken.length === 0 ? (
                  <div className="text-gray-500 text-sm">No actions taken yet</div>
                ) : (
                  <div className="space-y-3">
                    {selectedEmail.actions_taken.map((action) => (
                      <div key={action.action_id} className="p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{getActionIcon(action.type)}</span>
                          <span className="font-medium">{action.type.replace(/_/g, ' ')}</span>
                          <span
                            className={`ml-auto text-xs px-2 py-1 rounded ${
                              action.status === 'completed'
                                ? 'bg-green-100 text-green-700'
                                : action.status === 'failed'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {action.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          {new Date(action.timestamp).toLocaleString()}
                        </div>
                        {action.details && (
                          <pre className="text-xs bg-white p-2 rounded mt-2 overflow-x-auto">
                            {JSON.stringify(action.details, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select an email to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
