# Component Integration Guide

How to integrate ohhhmail components into Open-WebUI or any React application.

## Quick Start

### 1. Basic Integration

```tsx
import React from 'react';
import {
  Dashboard,
  CalendarView,
  AgentMonitor,
  Settings,
  EmailDashboard,
  TaskManager,
} from '@/ohhhmail/openwebui/components';

function App() {
  return (
    <div className="h-screen flex flex-col">
      <Dashboard className="flex-1" />
    </div>
  );
}
```

### 2. Tabbed Layout

```tsx
import React, { useState } from 'react';
import {
  Dashboard,
  CalendarView,
  AgentMonitor,
  Settings,
  EmailDashboard,
  TaskManager,
} from '@/ohhhmail/openwebui/components';

function OhhhmailInterface() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { key: 'dashboard', label: 'Dashboard', icon: '📊' },
    { key: 'emails', label: 'Emails', icon: '📧' },
    { key: 'calendar', label: 'Calendar', icon: '📅' },
    { key: 'tasks', label: 'Tasks', icon: '✓' },
    { key: 'agents', label: 'Agents', icon: '🤖' },
    { key: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Tab Navigation */}
      <div className="bg-white border-b shadow">
        <div className="flex gap-1 px-4">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-6 py-3 font-medium transition ${
                activeTab === tab.key
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'emails' && <EmailDashboard />}
        {activeTab === 'calendar' && <CalendarView />}
        {activeTab === 'tasks' && <TaskManager />}
        {activeTab === 'agents' && <AgentMonitor />}
        {activeTab === 'settings' && <Settings />}
      </div>
    </div>
  );
}

export default OhhhmailInterface;
```

### 3. Split View Layout

```tsx
import React, { useState } from 'react';
import {
  Dashboard,
  AgentMonitor,
  EmailDashboard,
} from '@/ohhhmail/openwebui/components';

function SplitViewLayout() {
  return (
    <div className="h-screen flex">
      {/* Left Panel - Dashboard */}
      <div className="w-1/3 border-r">
        <Dashboard />
      </div>

      {/* Right Panel - Emails and Agents */}
      <div className="flex-1 flex flex-col">
        <div className="h-1/2 border-b">
          <EmailDashboard />
        </div>
        <div className="flex-1">
          <AgentMonitor />
        </div>
      </div>
    </div>
  );
}

export default SplitViewLayout;
```

### 4. Responsive Layout

```tsx
import React, { useState } from 'react';
import {
  Dashboard,
  CalendarView,
  AgentMonitor,
  Settings,
} from '@/ohhhmail/openwebui/components';

function ResponsiveLayout() {
  const [activeView, setActiveView] = useState('dashboard');

  return (
    <div className="h-screen flex flex-col">
      {/* Mobile Navigation */}
      <div className="md:hidden bg-white border-b p-2">
        <select
          value={activeView}
          onChange={(e) => setActiveView(e.target.value)}
          className="w-full px-4 py-2 border rounded"
        >
          <option value="dashboard">Dashboard</option>
          <option value="calendar">Calendar</option>
          <option value="agents">Agents</option>
          <option value="settings">Settings</option>
        </select>
      </div>

      {/* Desktop Layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Sidebar (desktop only) */}
        <div className="hidden md:block w-64 bg-white border-r">
          <div className="p-4">
            <h2 className="text-xl font-bold mb-4">ohhhmail</h2>
            <nav className="space-y-2">
              {[
                { key: 'dashboard', label: 'Dashboard', icon: '📊' },
                { key: 'calendar', label: 'Calendar', icon: '📅' },
                { key: 'agents', label: 'Agents', icon: '🤖' },
                { key: 'settings', label: 'Settings', icon: '⚙️' },
              ].map(item => (
                <button
                  key={item.key}
                  onClick={() => setActiveView(item.key)}
                  className={`w-full text-left px-4 py-2 rounded transition ${
                    activeView === item.key
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {activeView === 'dashboard' && <Dashboard />}
          {activeView === 'calendar' && <CalendarView />}
          {activeView === 'agents' && <AgentMonitor />}
          {activeView === 'settings' && <Settings />}
        </div>
      </div>
    </div>
  );
}

export default ResponsiveLayout;
```

## Open-WebUI Specific Integration

### Embedding as Plugin

```tsx
// open-webui-plugin.tsx
import React from 'react';
import { Dashboard, AgentMonitor } from '@/ohhhmail/openwebui/components';

export const OhhhmailPlugin = {
  name: 'ohhhmail',
  version: '1.0.0',
  description: 'AI-powered email processing system',

  // Main view
  component: () => <Dashboard />,

  // Settings view
  settings: () => <Settings />,

  // Navigation items
  navigation: [
    { path: '/ohhhmail', label: 'Email Dashboard', icon: '📧' },
    { path: '/ohhhmail/calendar', label: 'Calendar', icon: '📅' },
    { path: '/ohhhmail/agents', label: 'Agents', icon: '🤖' },
  ],
};
```

### WebSocket Connection Configuration

```tsx
import { useDolphinWebSocket } from '@/ohhhmail/openwebui/hooks/useDolphinWebSocket';

function MyComponent() {
  // Configure WebSocket connection
  const { isConnected, lastMessage, send } = useDolphinWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000/ws',
    reconnectInterval: 5000,
    onExecutionUpdate: (execution) => {
      console.log('Execution update:', execution);
      // Handle execution update
    },
    onCheckpoint: (checkpoint) => {
      console.log('Checkpoint:', checkpoint);
      // Handle checkpoint
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      // Handle error
    },
  });

  return (
    <div>
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
    </div>
  );
}
```

## Environment Configuration

### .env file

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=ws://localhost:5000/ws

# Feature Flags
NEXT_PUBLIC_ENABLE_CALENDAR=true
NEXT_PUBLIC_ENABLE_AGENTS=true
NEXT_PUBLIC_ENABLE_SETTINGS=true
```

### Runtime Configuration

```tsx
// config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000/ws',
  features: {
    calendar: process.env.NEXT_PUBLIC_ENABLE_CALENDAR === 'true',
    agents: process.env.NEXT_PUBLIC_ENABLE_AGENTS === 'true',
    settings: process.env.NEXT_PUBLIC_ENABLE_SETTINGS === 'true',
  },
};
```

## Custom Themes

### Dark Mode Support

```tsx
import React from 'react';
import { Dashboard } from '@/ohhhmail/openwebui/components';

function ThemedDashboard() {
  const [darkMode, setDarkMode] = React.useState(false);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="bg-white dark:bg-gray-900 min-h-screen">
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Toggle {darkMode ? 'Light' : 'Dark'} Mode
        </button>
        <Dashboard />
      </div>
    </div>
  );
}
```

## API Proxy Configuration

If using a proxy for API requests:

```tsx
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
      {
        source: '/ws',
        destination: 'ws://localhost:5000/ws',
      },
    ];
  },
};
```

## Error Handling

```tsx
import React from 'react';
import { Dashboard } from '@/ohhhmail/openwebui/components';

function ErrorBoundary({ children }: { children: React.ReactNode }) {
  const [hasError, setHasError] = React.useState(false);

  if (hasError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Something went wrong
          </h2>
          <button
            onClick={() => setHasError(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
```

## Performance Optimization

### Lazy Loading Components

```tsx
import React, { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('@/ohhhmail/openwebui/components').then(m => ({ default: m.Dashboard })));
const CalendarView = lazy(() => import('@/ohhhmail/openwebui/components').then(m => ({ default: m.CalendarView })));
const AgentMonitor = lazy(() => import('@/ohhhmail/openwebui/components').then(m => ({ default: m.AgentMonitor })));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

## Testing

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import { Dashboard } from '@/ohhhmail/openwebui/components';

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('ohhhmail Dashboard')).toBeInTheDocument();
  });

  it('shows connection status', () => {
    render(<Dashboard />);
    expect(screen.getByText(/Connected|Disconnected/)).toBeInTheDocument();
  });
});
```

## Deployment Checklist

- [ ] Configure API URL environment variables
- [ ] Configure WebSocket URL
- [ ] Test WebSocket connection
- [ ] Verify CORS settings
- [ ] Test all components load correctly
- [ ] Verify responsive design
- [ ] Test error handling
- [ ] Configure authentication if needed
- [ ] Set up monitoring/logging
- [ ] Test with production API

## Support

For issues or questions:
1. Check component README files
2. Review API endpoint documentation
3. Verify WebSocket connection
4. Check browser console for errors
5. Ensure AUBS backend is running
