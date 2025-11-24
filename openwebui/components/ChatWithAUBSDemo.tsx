/**
 * ChatWithAUBS Demo - Integration Examples
 *
 * This file shows different ways to integrate ChatWithAUBS into your application
 */

import React, { useState } from 'react';
import ChatWithAUBS from './ChatWithAUBS';

// ============================================================================
// Example 1: Full-Screen Chat Application
// ============================================================================

export const FullScreenChatApp: React.FC = () => {
  return (
    <div className="h-screen w-screen">
      <ChatWithAUBS
        apiBaseUrl="http://localhost:8000"
        enableWebSocket={true}
        enableQuickActions={true}
      />
    </div>
  );
};

// ============================================================================
// Example 2: Floating Chat Widget (Bottom-Right Corner)
// ============================================================================

export const FloatingChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Your main application content */}
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-4">OpsManager Dashboard</h1>
        <p className="text-gray-600">Your main content goes here...</p>
      </div>

      {/* Floating chat button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 text-white rounded-full shadow-2xl hover:bg-blue-700 transition flex items-center justify-center text-2xl z-50"
          title="Chat with AUBS"
        >
          💬
        </button>
      )}

      {/* Floating chat window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl z-50 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 bg-blue-600 text-white">
            <h3 className="font-bold">AUBS Assistant</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatWithAUBS
              apiBaseUrl="http://localhost:8000"
              enableQuickActions={true}
            />
          </div>
        </div>
      )}
    </>
  );
};

// ============================================================================
// Example 3: Modal Chat Dialog
// ============================================================================

export const ModalChatDialog: React.FC = () => {
  const [showModal, setShowModal] = useState(false);

  return (
    <div>
      {/* Trigger button */}
      <button
        onClick={() => setShowModal(true)}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        🤖 Ask AUBS
      </button>

      {/* Modal overlay */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col">
            {/* Modal header */}
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">
                  Chat with AUBS
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  AI Assistant with full operational awareness
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Chat content */}
            <div className="flex-1 overflow-hidden">
              <ChatWithAUBS
                apiBaseUrl="http://localhost:8000"
                enableWebSocket={true}
                enableQuickActions={true}
                onSessionChange={(sessionId) => {
                  console.log('Session:', sessionId);
                }}
                onMessageSent={(message) => {
                  console.log('Sent:', message);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Example 4: Sidebar Chat (Slide-in from Right)
// ============================================================================

export const SidebarChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex h-screen">
      {/* Main content */}
      <div className="flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            💬 Chat
          </button>
        </div>
        <p className="text-gray-600">Your main content here...</p>
      </div>

      {/* Sliding sidebar */}
      <div
        className={`fixed top-0 right-0 h-screen w-[500px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-xl font-bold">AUBS Assistant</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
          </div>
        </div>
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

// ============================================================================
// Example 5: Embedded Chat in Dashboard
// ============================================================================

export const EmbeddedChatDashboard: React.FC = () => {
  return (
    <div className="h-screen flex">
      {/* Left side - Dashboard content */}
      <div className="flex-1 p-8 bg-gray-50 overflow-y-auto">
        <h1 className="text-3xl font-bold mb-6">OpsManager Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          {/* Stats cards */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Emails Today</h3>
            <p className="text-4xl font-bold text-blue-600">24</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Active Tasks</h3>
            <p className="text-4xl font-bold text-green-600">12</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Pending Deadlines</h3>
            <p className="text-4xl font-bold text-orange-600">5</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
          <p className="text-gray-600">Your activity timeline...</p>
        </div>
      </div>

      {/* Right side - Embedded chat */}
      <div className="w-[450px] border-l shadow-lg">
        <ChatWithAUBS
          apiBaseUrl="http://localhost:8000"
          enableQuickActions={true}
        />
      </div>
    </div>
  );
};

// ============================================================================
// Example 6: Tab-Based Chat Interface
// ============================================================================

export const TabBasedChatInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'tasks'>(
    'dashboard'
  );

  return (
    <div className="h-screen flex flex-col">
      {/* Top navigation */}
      <div className="bg-white border-b shadow-sm">
        <div className="flex items-center gap-4 p-4">
          <h1 className="text-2xl font-bold mr-6">OpsManager</h1>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 rounded ${
              activeTab === 'dashboard'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-2 rounded ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            💬 Chat with AUBS
          </button>
          <button
            onClick={() => setActiveTab('tasks')}
            className={`px-4 py-2 rounded ${
              activeTab === 'tasks'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            ✓ Tasks
          </button>
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'dashboard' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
            <p className="text-gray-600">Your dashboard content...</p>
          </div>
        )}

        {activeTab === 'chat' && (
          <ChatWithAUBS
            apiBaseUrl="http://localhost:8000"
            enableWebSocket={true}
            enableQuickActions={true}
          />
        )}

        {activeTab === 'tasks' && (
          <div className="p-8">
            <h2 className="text-2xl font-bold mb-4">Tasks</h2>
            <p className="text-gray-600">Your tasks content...</p>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Example 7: Chat with Analytics Tracking
// ============================================================================

export const ChatWithAnalytics: React.FC = () => {
  const [chatMetrics, setChatMetrics] = useState({
    messagesCount: 0,
    sessionsCount: 0,
    avgResponseTime: 0,
  });

  const handleSessionChange = (sessionId: string) => {
    console.log('Session changed:', sessionId);
    setChatMetrics(prev => ({
      ...prev,
      sessionsCount: prev.sessionsCount + 1,
    }));

    // Send to analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'chat_session_created', {
        session_id: sessionId,
      });
    }
  };

  const handleMessageSent = (message: string) => {
    console.log('Message sent:', message);
    setChatMetrics(prev => ({
      ...prev,
      messagesCount: prev.messagesCount + 1,
    }));

    // Send to analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'chat_message_sent', {
        message_length: message.length,
      });
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Analytics bar */}
      <div className="bg-gray-100 border-b p-4">
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-gray-600">Messages: </span>
            <span className="font-bold">{chatMetrics.messagesCount}</span>
          </div>
          <div>
            <span className="text-gray-600">Sessions: </span>
            <span className="font-bold">{chatMetrics.sessionsCount}</span>
          </div>
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <ChatWithAUBS
          apiBaseUrl="http://localhost:8000"
          enableWebSocket={true}
          onSessionChange={handleSessionChange}
          onMessageSent={handleMessageSent}
        />
      </div>
    </div>
  );
};

// ============================================================================
// Example 8: Mobile-Responsive Chat
// ============================================================================

export const MobileResponsiveChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Desktop: sidebar */}
      <div className="hidden md:flex h-screen">
        <div className="flex-1 p-8">
          <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
          <p className="text-gray-600">Desktop view with sidebar...</p>
        </div>
        <div className="w-[400px] border-l">
          <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
        </div>
      </div>

      {/* Mobile: full screen overlay */}
      <div className="md:hidden">
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
          <button
            onClick={() => setIsOpen(true)}
            className="w-full py-3 bg-blue-600 text-white rounded-lg"
          >
            💬 Chat with AUBS
          </button>
        </div>

        {isOpen && (
          <div className="fixed inset-0 bg-white z-50">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-bold">Chat</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="h-[calc(100vh-64px)]">
              <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
            </div>
          </div>
        )}
      </div>
    </>
  );
};

// ============================================================================
// Export all examples
// ============================================================================

export default {
  FullScreenChatApp,
  FloatingChatWidget,
  ModalChatDialog,
  SidebarChat,
  EmbeddedChatDashboard,
  TabBasedChatInterface,
  ChatWithAnalytics,
  MobileResponsiveChat,
};

/**
 * Usage:
 *
 * import {
 *   FullScreenChatApp,
 *   FloatingChatWidget,
 *   ModalChatDialog,
 * } from './ChatWithAUBSDemo';
 *
 * // Use in your app
 * <FloatingChatWidget />
 */
