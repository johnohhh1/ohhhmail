'use client';

import { useState, useEffect } from 'react';

interface EmailProcessed {
  email_id: string;
  subject: string;
  from: string;
  status: string;
  confidence_score?: number;
  agent_outputs: {
    triage?: any;
    deadline?: any;
    vision?: any;
    context?: any;
  };
  actions_taken: Array<{
    action_id: string;
    type: string;
    timestamp: string;
  }>;
}

export default function EmailClient() {
  const [showAgentView, setShowAgentView] = useState(false);
  const [recentEmails, setRecentEmails] = useState<EmailProcessed[]>([]);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);

  const fetchRecentProcessedEmails = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/emails/recent?limit=10');
      const data = await response.json();
      setRecentEmails(data.emails || []);
    } catch (error) {
      console.error('Failed to fetch recent emails:', error);
    }
  };

  useEffect(() => {
    if (showAgentView) {
      fetchRecentProcessedEmails();
      const interval = setInterval(fetchRecentProcessedEmails, 30000);
      return () => clearInterval(interval);
    }
  }, [showAgentView]);

  const selectedEmail = recentEmails.find((e) => e.email_id === selectedEmailId);

  return (
    <div className="flex h-full bg-gray-100">
      {/* Main Email Client - SnappyMail */}
      <div className={`flex-1 flex flex-col bg-white ${showAgentView ? 'border-r border-gray-200' : ''}`}>
        {/* Header */}
        <div className="px-4 py-3 bg-gray-800 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">📧 Email Client</h2>
            <span className="text-sm text-gray-400">SnappyMail</span>
          </div>
          <button
            onClick={() => setShowAgentView(!showAgentView)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              showAgentView
                ? 'bg-purple-600 hover:bg-purple-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {showAgentView ? '🤖 Hide' : '🤖 Show'} Agent View
          </button>
        </div>

        {/* SnappyMail iframe */}
        <div className="flex-1 relative">
          <iframe
            src="http://localhost:8888"
            className="absolute inset-0 w-full h-full border-0"
            title="SnappyMail Email Client"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-downloads"
          />
        </div>
      </div>

      {/* Agent Processing View - Collapsible Sidebar */}
      {showAgentView && (
        <div className="w-96 bg-white flex flex-col border-l border-gray-200">
          {/* Agent View Header */}
          <div className="px-4 py-3 bg-purple-50 border-b border-purple-200">
            <h3 className="font-semibold text-purple-900 flex items-center gap-2">
              <span>🤖</span>
              <span>AI Processing View</span>
            </h3>
            <p className="text-xs text-purple-700 mt-1">
              Real-time agent analysis and actions
            </p>
          </div>

          {/* Recently Processed Emails */}
          <div className="flex-1 overflow-y-auto">
            {recentEmails.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <div className="text-4xl mb-2">🔄</div>
                <div className="text-sm">No processed emails yet</div>
              </div>
            ) : (
              <div>
                {recentEmails.map((email) => (
                  <button
                    key={email.email_id}
                    onClick={() => setSelectedEmailId(email.email_id)}
                    className={`w-full p-3 text-left border-b border-gray-100 hover:bg-purple-50 transition ${
                      selectedEmailId === email.email_id
                        ? 'bg-purple-100 border-l-4 border-l-purple-600'
                        : 'border-l-4 border-l-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <div className="text-sm font-medium text-gray-900 truncate flex-1">
                        {email.subject}
                      </div>
                      <div
                        className={`w-2 h-2 rounded-full ml-2 ${
                          email.status === 'completed'
                            ? 'bg-green-500'
                            : email.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-yellow-500 animate-pulse'
                        }`}
                      />
                    </div>
                    <div className="text-xs text-gray-600 truncate mb-1">{email.from}</div>
                    {email.confidence_score !== undefined && (
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
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
                        <span className="text-xs text-gray-500">
                          {(email.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Selected Email Details */}
          {selectedEmail && (
            <div className="border-t border-gray-200 bg-gray-50 p-4 max-h-96 overflow-y-auto">
              <h4 className="font-semibold text-gray-900 mb-3 text-sm">
                AI Analysis Results
              </h4>

              {/* Agent outputs would be displayed here */}
              <div className="text-xs text-gray-600">
                Agent processing details for: {selectedEmail.subject}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
