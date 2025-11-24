/**
 * Complete Example Application
 * Demonstrates how to use all ohhhmail components together
 */

import React, { useState } from 'react';
import {
  Dashboard,
  CalendarView,
  AgentMonitor,
  Settings,
  EmailDashboard,
  TaskManager,
  Analytics,
  UITARSDebugPanel,
} from './index';

type TabKey =
  | 'dashboard'
  | 'emails'
  | 'calendar'
  | 'tasks'
  | 'agents'
  | 'analytics'
  | 'debug'
  | 'settings';

interface Tab {
  key: TabKey;
  label: string;
  icon: string;
  component: React.ComponentType<any>;
  badge?: number;
}

export const OhhhmailApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const tabs: Tab[] = [
    {
      key: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      component: Dashboard,
    },
    {
      key: 'emails',
      label: 'Emails',
      icon: '📧',
      component: EmailDashboard,
    },
    {
      key: 'calendar',
      label: 'Calendar',
      icon: '📅',
      component: CalendarView,
    },
    {
      key: 'tasks',
      label: 'Tasks',
      icon: '✓',
      component: TaskManager,
    },
    {
      key: 'agents',
      label: 'Agents',
      icon: '🤖',
      component: AgentMonitor,
    },
    {
      key: 'analytics',
      label: 'Analytics',
      icon: '📈',
      component: Analytics,
    },
    {
      key: 'debug',
      label: 'Debug',
      icon: '🔧',
      component: UITARSDebugPanel,
    },
    {
      key: 'settings',
      label: 'Settings',
      icon: '⚙️',
      component: Settings,
    },
  ];

  const ActiveComponent = tabs.find(t => t.key === activeTab)?.component || Dashboard;

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Sidebar */}
      <div
        className={`bg-white border-r shadow-lg transition-all duration-300 ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b bg-blue-600 text-white">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-xl font-bold">ohhhmail</h1>
                <p className="text-xs text-blue-100">AI Email Processing</p>
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 hover:bg-blue-700 rounded transition"
              title={sidebarCollapsed ? 'Expand' : 'Collapse'}
            >
              {sidebarCollapsed ? '→' : '←'}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-2">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white shadow'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              title={sidebarCollapsed ? tab.label : undefined}
            >
              <span className="text-xl">{tab.icon}</span>
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1 text-left font-medium">{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                      {tab.badge}
                    </span>
                  )}
                </>
              )}
            </button>
          ))}
        </nav>

        {/* Footer */}
        {!sidebarCollapsed && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-gray-50">
            <div className="text-xs text-gray-600">
              <p className="font-semibold">System Status</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>All systems operational</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white border-b shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-800">
                {tabs.find(t => t.key === activeTab)?.label}
              </h2>
              <p className="text-sm text-gray-600">
                {activeTab === 'dashboard' && 'Overview of your email processing system'}
                {activeTab === 'emails' && 'View and manage processed emails'}
                {activeTab === 'calendar' && 'Events and deadlines from your emails'}
                {activeTab === 'tasks' && 'Tasks created from email processing'}
                {activeTab === 'agents' && 'Monitor and manage AI agents'}
                {activeTab === 'analytics' && 'Performance metrics and insights'}
                {activeTab === 'debug' && 'UI-TARS execution debugging'}
                {activeTab === 'settings' && 'Configure system preferences'}
              </p>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                onClick={() => window.location.reload()}
              >
                Refresh
              </button>
              <button
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
                onClick={() => setActiveTab('settings')}
              >
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Component Content */}
        <div className="flex-1 overflow-hidden">
          <ActiveComponent className="h-full" />
        </div>
      </div>
    </div>
  );
};

export default OhhhmailApp;

/**
 * Usage Example:
 *
 * import OhhhmailApp from '@/ohhhmail/openwebui/components/ExampleApp';
 *
 * function App() {
 *   return <OhhhmailApp />;
 * }
 */

/**
 * Mobile-Responsive Version:
 *
 * export const OhhhmailMobileApp: React.FC = () => {
 *   const [activeTab, setActiveTab] = useState<TabKey>('dashboard');
 *   const [menuOpen, setMenuOpen] = useState(false);
 *
 *   return (
 *     <div className="h-screen flex flex-col">
 *       {/* Mobile Header
 *       <div className="bg-blue-600 text-white p-4 md:hidden">
 *         <div className="flex items-center justify-between">
 *           <h1 className="text-xl font-bold">ohhhmail</h1>
 *           <button onClick={() => setMenuOpen(!menuOpen)}>
 *             Menu
 *           </button>
 *         </div>
 *       </div>
 *
 *       {/* Mobile Menu
 *       {menuOpen && (
 *         <div className="bg-white border-b p-2 md:hidden">
 *           {tabs.map(tab => (
 *             <button
 *               key={tab.key}
 *               onClick={() => {
 *                 setActiveTab(tab.key);
 *                 setMenuOpen(false);
 *               }}
 *               className="w-full text-left px-4 py-2"
 *             >
 *               {tab.icon} {tab.label}
 *             </button>
 *           ))}
 *         </div>
 *       )}
 *
 *       {/* Content
 *       <div className="flex-1 overflow-hidden">
 *         <ActiveComponent />
 *       </div>
 *
 *       {/* Bottom Navigation (Mobile)
 *       <div className="bg-white border-t p-2 flex justify-around md:hidden">
 *         {tabs.slice(0, 5).map(tab => (
 *           <button
 *             key={tab.key}
 *             onClick={() => setActiveTab(tab.key)}
 *             className={`flex flex-col items-center ${
 *               activeTab === tab.key ? 'text-blue-600' : 'text-gray-600'
 *             }`}
 *           >
 *             <span className="text-2xl">{tab.icon}</span>
 *             <span className="text-xs">{tab.label}</span>
 *           </button>
 *         ))}
 *       </div>
 *     </div>
 *   );
 * };
 */
