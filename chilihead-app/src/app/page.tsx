'use client';

import { useState } from 'react';
import EmailClient from '@/components/EmailClient';
import AUBSChat from '@/components/AUBSChat';
import Settings from '@/components/Settings';

type Tab = 'email' | 'chat' | 'settings';

export default function ChiliHeadPlatform() {
  const [activeTab, setActiveTab] = useState<Tab>('email');

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-2xl">🌶️</div>
            <div>
              <h1 className="text-xl font-bold text-white">ChiliHead OpsManager</h1>
              <p className="text-sm text-gray-400">Restaurant Operations Platform v2.1</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-green-600 text-white text-xs font-semibold rounded-full">
              ● LIVE
            </span>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6">
        <div className="flex gap-1">
          <TabButton
            active={activeTab === 'email'}
            onClick={() => setActiveTab('email')}
            icon="📧"
            label="Email Client"
          />
          <TabButton
            active={activeTab === 'chat'}
            onClick={() => setActiveTab('chat')}
            icon="💬"
            label="AUBS Chat"
          />
          <TabButton
            active={activeTab === 'settings'}
            onClick={() => setActiveTab('settings')}
            icon="⚙️"
            label="Settings"
          />
        </div>
      </nav>

      {/* Content Area */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'email' && <EmailClient />}
        {activeTab === 'chat' && <AUBSChat />}
        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-3 font-medium text-sm transition-colors ${
        active
          ? 'bg-gray-900 text-white border-t-2 border-blue-500'
          : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
      }`}
    >
      <span className="mr-2">{icon}</span>
      {label}
    </button>
  );
}
