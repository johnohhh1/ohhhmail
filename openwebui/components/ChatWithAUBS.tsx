/**
 * ChatWithAUBS Component
 * Full AI Operations Assistant with complete operational awareness
 *
 * Features:
 * - Real-time chat with AUBS AI assistant
 * - Streaming responses
 * - Complete operational context (emails, tasks, deadlines, agents)
 * - Conversation history
 * - Quick action suggestions
 * - WebSocket support for real-time updates
 * - Context-aware responses
 *
 * AUBS has access to:
 * - All processed emails
 * - Current tasks and deadlines
 * - Agent performance metrics
 * - System status and health
 * - 30-day historical context
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

// Types
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface ChatSession {
  id: string;
  started_at: string;
  last_activity: string;
  message_count: number;
  metadata?: Record<string, any>;
}

interface OperationalContext {
  statistics: {
    total_emails_processed: number;
    emails_today: number;
    active_executions: number;
    failed_executions: number;
    total_tasks_created: number;
    total_events_scheduled: number;
  };
  recent_activity: {
    emails_count: number;
    tasks_count: number;
    deadlines_count: number;
  };
  system_health: {
    dolphin_connected: boolean;
    nats_connected: boolean;
    active_sessions: number;
    total_messages: number;
  };
  high_risk_items_count: number;
}

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  prompt: string;
  category: 'tasks' | 'emails' | 'deadlines' | 'agents' | 'system';
}

interface ChatWithAUBSProps {
  apiBaseUrl?: string;
  wsBaseUrl?: string;
  enableWebSocket?: boolean;
  enableQuickActions?: boolean;
  enableVoice?: boolean;
  className?: string;
  onSessionChange?: (sessionId: string) => void;
  onMessageSent?: (message: string) => void;
}

export const ChatWithAUBS: React.FC<ChatWithAUBSProps> = ({
  apiBaseUrl = 'http://localhost:8000',
  wsBaseUrl = 'ws://localhost:8000',
  enableWebSocket = false,
  enableQuickActions = true,
  enableVoice = false,
  className = '',
  onSessionChange,
  onMessageSent,
}) => {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [context, setContext] = useState<OperationalContext | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Quick Actions
  const quickActions: QuickAction[] = [
    {
      id: 'urgent-today',
      label: "What's most urgent today?",
      icon: '🔥',
      prompt: "Show me the most urgent tasks and deadlines for today",
      category: 'tasks',
    },
    {
      id: 'all-deadlines',
      label: 'Show all deadlines',
      icon: '📅',
      prompt: "List all upcoming deadlines with their dates and priorities",
      category: 'deadlines',
    },
    {
      id: 'vision-extractions',
      label: 'Vision agent extractions',
      icon: '👁️',
      prompt: "What did the Vision agent extract from recent emails?",
      category: 'agents',
    },
    {
      id: 'failed-emails',
      label: 'Show failed emails',
      icon: '❌',
      prompt: "Show me all emails that failed to process and why",
      category: 'emails',
    },
    {
      id: 'create-task',
      label: 'Create a task',
      icon: '➕',
      prompt: "Help me create a new task",
      category: 'tasks',
    },
    {
      id: 'email-status',
      label: 'Email status',
      icon: '📧',
      prompt: "What's the processing status of recent emails?",
      category: 'emails',
    },
    {
      id: 'system-health',
      label: 'System status',
      icon: '🏥',
      prompt: "Give me a full system health report",
      category: 'system',
    },
    {
      id: 'agent-performance',
      label: 'Agent performance',
      icon: '🤖',
      prompt: "How are the AI agents performing?",
      category: 'agents',
    },
  ];

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize session
  useEffect(() => {
    createNewSession();
    loadOperationalContext();
    loadSessions();
  }, []);

  // WebSocket connection
  useEffect(() => {
    if (enableWebSocket && sessionId) {
      connectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [enableWebSocket, sessionId]);

  // Create new session
  const createNewSession = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/sessions`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const session = await response.json();
      setSessionId(session.id);
      onSessionChange?.(session.id);

      // Add welcome message
      const welcomeMessage: Message = {
        id: `system-${Date.now()}`,
        role: 'system',
        content: `Welcome to AUBS AI Assistant! I have complete operational awareness of your email processing system. Ask me anything about your emails, tasks, deadlines, or agent performance.`,
        timestamp: new Date().toISOString(),
      };
      setMessages([welcomeMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      console.error('Session creation error:', err);
    }
  };

  // Load operational context
  const loadOperationalContext = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/context`);

      if (!response.ok) {
        throw new Error('Failed to load context');
      }

      const contextData = await response.json();
      setContext(contextData);
    } catch (err) {
      console.error('Context loading error:', err);
    }
  };

  // Load sessions
  const loadSessions = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/chat/sessions?limit=20`);

      if (!response.ok) {
        throw new Error('Failed to load sessions');
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Sessions loading error:', err);
    }
  };

  // Load session history
  const loadSessionHistory = async (sessionIdToLoad: string) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/chat/history/${sessionIdToLoad}?limit=100`
      );

      if (!response.ok) {
        throw new Error('Failed to load history');
      }

      const data = await response.json();
      setMessages(data.messages || []);
      setSessionId(sessionIdToLoad);
      onSessionChange?.(sessionIdToLoad);
      setShowSessions(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
      console.error('History loading error:', err);
    }
  };

  // WebSocket connection
  const connectWebSocket = () => {
    if (!sessionId) return;

    try {
      const ws = new WebSocket(`${wsBaseUrl}/ws/chat/${sessionId}`);

      ws.onopen = () => {
        setWsConnected(true);
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'chunk':
            // Update the last assistant message with new content
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage?.role === 'assistant') {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: lastMessage.content + data.content,
                  },
                ];
              }
              return prev;
            });
            break;

          case 'complete':
            setIsStreaming(false);
            setIsLoading(false);
            break;

          case 'error':
            setError(data.message);
            setIsStreaming(false);
            setIsLoading(false);
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.log('WebSocket disconnected');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('WebSocket connection error:', err);
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setWsConnected(false);
    }
  };

  // Send message
  const sendMessage = async (messageText: string = inputMessage) => {
    if (!messageText.trim() || !sessionId) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);
    onMessageSent?.(messageText);

    // Use WebSocket if enabled and connected
    if (enableWebSocket && wsConnected && wsRef.current) {
      sendMessageViaWebSocket(messageText);
      return;
    }

    // Use HTTP streaming
    await sendMessageViaHTTP(messageText);
  };

  const sendMessageViaWebSocket = (messageText: string) => {
    if (!wsRef.current) return;

    wsRef.current.send(
      JSON.stringify({
        message: messageText,
      })
    );

    // Add empty assistant message for streaming
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, assistantMessage]);
    setIsStreaming(true);
  };

  const sendMessageViaHTTP = async (messageText: string) => {
    try {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Add empty assistant message for streaming
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsStreaming(true);

      // Read streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6);

            // Update the last assistant message
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage?.role === 'assistant') {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: lastMessage.content + content,
                  },
                ];
              }
              return prev;
            });
          }
        }
      }

      setIsStreaming(false);
      setIsLoading(false);

      // Reload context after message
      loadOperationalContext();
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Request aborted');
        return;
      }

      setError(err instanceof Error ? err.message : 'Failed to send message');
      setIsLoading(false);
      setIsStreaming(false);
      console.error('Send message error:', err);
    }
  };

  // Handle quick action click
  const handleQuickAction = (action: QuickAction) => {
    sendMessage(action.prompt);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Delete session
  const deleteSession = async (sessionIdToDelete: string) => {
    try {
      await fetch(`${apiBaseUrl}/api/chat/sessions/${sessionIdToDelete}`, {
        method: 'DELETE',
      });

      loadSessions();

      if (sessionIdToDelete === sessionId) {
        createNewSession();
      }
    } catch (err) {
      console.error('Session deletion error:', err);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Format date
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-3xl">
              🤖
            </div>
            <div>
              <h1 className="text-2xl font-bold">AUBS AI Assistant</h1>
              <p className="text-sm text-blue-100">
                Full operational awareness • Real-time insights
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Connection status */}
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs ${
                wsConnected
                  ? 'bg-green-500 bg-opacity-20 text-green-100'
                  : 'bg-gray-500 bg-opacity-20 text-gray-200'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  wsConnected ? 'bg-green-300 animate-pulse' : 'bg-gray-400'
                }`}
              />
              {wsConnected ? 'Connected' : 'HTTP Mode'}
            </div>

            {/* Context button */}
            <button
              onClick={() => setShowContext(!showContext)}
              className="px-4 py-2 bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition"
              title="System Context"
            >
              📊 Context
            </button>

            {/* Sessions button */}
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="px-4 py-2 bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition"
              title="Chat History"
            >
              💬 History
            </button>

            {/* New chat button */}
            <button
              onClick={createNewSession}
              className="px-4 py-2 bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition"
              title="New Chat"
            >
              ➕ New
            </button>
          </div>
        </div>

        {/* Context display */}
        {showContext && context && (
          <div className="mt-4 bg-white bg-opacity-10 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-blue-200 mb-1">Emails Today</p>
                <p className="text-2xl font-bold">{context.statistics.emails_today}</p>
              </div>
              <div>
                <p className="text-blue-200 mb-1">Total Tasks</p>
                <p className="text-2xl font-bold">{context.statistics.total_tasks_created}</p>
              </div>
              <div>
                <p className="text-blue-200 mb-1">Active Executions</p>
                <p className="text-2xl font-bold">{context.statistics.active_executions}</p>
              </div>
              <div>
                <p className="text-blue-200 mb-1">High Risk Items</p>
                <p className="text-2xl font-bold text-red-300">
                  {context.high_risk_items_count}
                </p>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-white border-opacity-20">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      context.system_health.dolphin_connected
                        ? 'bg-green-300'
                        : 'bg-red-300'
                    }`}
                  />
                  <span>Dolphin</span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      context.system_health.nats_connected ? 'bg-green-300' : 'bg-red-300'
                    }`}
                  />
                  <span>NATS</span>
                </div>
                <div className="ml-auto text-blue-200">
                  {context.system_health.active_sessions} active sessions •{' '}
                  {context.system_health.total_messages} messages
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sessions sidebar */}
      {showSessions && (
        <div className="bg-white border-b shadow-sm p-4 max-h-64 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">Recent Conversations</h3>
            <button
              onClick={() => setShowSessions(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2">
            {sessions.length === 0 ? (
              <p className="text-gray-500 text-sm">No previous conversations</p>
            ) : (
              sessions.map(session => (
                <div
                  key={session.id}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    session.id === sessionId
                      ? 'bg-blue-50 border-blue-300'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                  onClick={() => loadSessionHistory(session.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">
                        {formatDate(session.started_at)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {session.message_count} messages • Last active{' '}
                        {formatTimestamp(session.last_activity)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.id);
                      }}
                      className="ml-2 p-1 text-red-500 hover:text-red-700"
                      title="Delete session"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {enableQuickActions && messages.length <= 1 && (
        <div className="bg-white border-b p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Quick Actions
          </h3>
          <div className="flex flex-wrap gap-2">
            {quickActions.map(action => (
              <button
                key={action.id}
                onClick={() => handleQuickAction(action)}
                className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition"
                disabled={isLoading}
              >
                <span>{action.icon}</span>
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.role === 'system'
                  ? 'bg-gray-200 text-gray-700 w-full text-center'
                  : 'bg-white shadow-md text-gray-800'
              }`}
            >
              {/* Message header */}
              {message.role !== 'system' && (
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">
                    {message.role === 'user' ? '👤' : '🤖'}
                  </span>
                  <span className="text-xs opacity-70">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
              )}

              {/* Message content */}
              <div className="whitespace-pre-wrap break-words">
                {message.content}
                {isStreaming &&
                  message.id === messages[messages.length - 1]?.id && (
                    <span className="inline-block ml-1 animate-pulse">▊</span>
                  )}
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && !isStreaming && (
          <div className="flex justify-start">
            <div className="bg-white shadow-md rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200" />
                </div>
                <span className="text-sm text-gray-600">AUBS is thinking...</span>
              </div>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-800">
              <span>❌</span>
              <span className="font-medium">Error:</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-white border-t shadow-lg p-4">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask AUBS anything about your emails, tasks, deadlines, or agents..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading || !sessionId}
            />
          </div>

          <button
            onClick={() => sendMessage()}
            disabled={isLoading || !inputMessage.trim() || !sessionId}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-medium"
          >
            {isLoading ? '⏳' : '📤'} Send
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>💡 Try asking about urgent tasks or recent emails</span>
          </div>
          <div>
            {messages.length > 1 && (
              <span>{messages.length - 1} messages in this conversation</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatWithAUBS;

/**
 * Usage Example:
 *
 * import ChatWithAUBS from '@/components/ChatWithAUBS';
 *
 * function App() {
 *   return (
 *     <div className="h-screen">
 *       <ChatWithAUBS
 *         apiBaseUrl="http://localhost:8000"
 *         enableWebSocket={true}
 *         enableQuickActions={true}
 *         onSessionChange={(sessionId) => console.log('Session:', sessionId)}
 *         onMessageSent={(message) => console.log('Sent:', message)}
 *       />
 *     </div>
 *   );
 * }
 *
 * Example Questions for AUBS:
 * - "What's most urgent today?"
 * - "Show me all deadlines this week"
 * - "What did the Vision agent extract from recent emails?"
 * - "Create a task for the fire inspection follow-up"
 * - "What's the status of the email about menu pricing?"
 * - "Show me failed email processing attempts"
 * - "How are the AI agents performing?"
 * - "What tasks are overdue?"
 * - "Give me a daily summary"
 * - "What emails came in today?"
 */
