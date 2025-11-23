# UI-TARS Embedded Components for Open-WebUI

This directory contains the **embedded** React components for UI-TARS Desktop integration within Open-WebUI, as specified in the ChiliHead OpsManager v2.1 PRD.

## Architecture Overview

UI-TARS is **NOT** a standalone application. It is embedded as tabs and components **inside Open-WebUI**, providing:

- **Real-time visual debugging** of Dolphin workflow executions
- **Email processing dashboard** with agent outputs
- **Task management** interface
- **Analytics and performance metrics**

## Components

### 1. UITARSDebugPanel (`components/UITARSDebugPanel.tsx`)

The main debugging interface embedded in Open-WebUI's Debug tab.

**Features:**
- Connects to Dolphin WebSocket for real-time execution updates
- Shows execution timeline with task status
- Displays visual checkpoints with screenshots
- Agent decision viewer
- Performance metrics per checkpoint
- Execution replay capability

**Usage:**
```tsx
import { UITARSDebugPanel } from '@chilihead/openwebui-components';

<UITARSDebugPanel
  executionId="optional-execution-id"
  autoRefresh={true}
/>
```

### 2. EmailDashboard (`components/EmailDashboard.tsx`)

Email processing dashboard showing all processed emails and their agent outputs.

**Features:**
- List of processed emails with status
- Agent output viewer (Triage, Vision, Deadline, Context)
- Actions taken display
- Confidence scoring
- Filter by status

**Usage:**
```tsx
import { EmailDashboard } from '@chilihead/openwebui-components';

<EmailDashboard autoRefresh={true} />
```

### 3. TaskManager (`components/TaskManager.tsx`)

Task management interface for tasks created from email processing.

**Features:**
- Task list with priority and status
- Task detail viewer
- Status updates
- Due date tracking with overdue alerts
- Link back to originating email

**Usage:**
```tsx
import { TaskManager } from '@chilihead/openwebui-components';

<TaskManager />
```

### 4. Analytics (`components/Analytics.tsx`)

System performance and agent metrics dashboard.

**Features:**
- System health monitoring (Dolphin, AUBS, Ollama, Qdrant)
- Processing statistics (total emails, success rate, avg time)
- Agent performance metrics per agent type
- Time range filtering (24h, 7d, 30d)

**Usage:**
```tsx
import { Analytics } from '@chilihead/openwebui-components';

<Analytics />
```

## Integration with Open-WebUI

### Configuration (`config/openwebui-config.yaml`)

The configuration file defines:

1. **Custom Tabs**
   - Email Dashboard (`/emails`)
   - Task Manager (`/tasks`)
   - UI-TARS Debug (`/debug`)
   - Analytics (`/analytics`)

2. **Service Integrations**
   - Dolphin Scheduler (API + WebSocket)
   - AUBS Business Logic Layer
   - Ollama LLM Runtime
   - Redis, PostgreSQL, Qdrant

3. **API Endpoints**
   - Email operations
   - Task CRUD
   - Dolphin execution queries
   - UI-TARS checkpoint retrieval

4. **WebSocket Channels**
   - `dolphin_updates` - Real-time execution updates
   - `email_notifications` - New email alerts

### WebSocket Hook (`hooks/useDolphinWebSocket.ts`)

Custom React hook for connecting to Dolphin's WebSocket:

```tsx
const { isConnected, lastMessage, send } = useDolphinWebSocket({
  url: 'ws://dolphin:12345/ws',
  onExecutionUpdate: (execution) => {
    // Handle execution updates
  },
  onCheckpoint: (checkpoint) => {
    // Handle UI-TARS checkpoints
  },
});
```

## Types (`types/index.ts`)

TypeScript types for all data structures:

- `DolphinExecution` - Dolphin DAG execution
- `DolphinTask` - Individual task in DAG
- `UITARSCheckpoint` - Visual checkpoint with screenshot
- `UITARSSession` - Complete debugging session
- `EmailProcessed` - Processed email with agent outputs
- `Action` - Action taken by system
- `AgentMetrics` - Performance metrics per agent
- `SystemHealth` - System component health status

## Installation

```bash
cd openwebui
npm install
```

## Development

```bash
npm run dev
```

## Building for Production

```bash
npm run build
```

## Integration Steps

To integrate these components into Open-WebUI:

1. **Copy components to Open-WebUI project:**
   ```bash
   cp -r openwebui/components/* /path/to/open-webui/components/
   cp -r openwebui/types/* /path/to/open-webui/types/
   cp -r openwebui/hooks/* /path/to/open-webui/hooks/
   ```

2. **Update Open-WebUI routing** to include new tabs:
   ```tsx
   import { UITARSDebugPanel, EmailDashboard, TaskManager, Analytics } from '@/components';

   const routes = [
     { path: '/emails', component: EmailDashboard },
     { path: '/tasks', component: TaskManager },
     { path: '/debug', component: UITARSDebugPanel },
     { path: '/analytics', component: Analytics },
   ];
   ```

3. **Configure environment variables:**
   ```env
   DOLPHIN_API_URL=http://dolphin:12345/api
   DOLPHIN_WS_URL=ws://dolphin:12345/ws
   AUBS_API_URL=http://aubs:5000/api
   ```

4. **Update API proxy** in `next.config.js`:
   ```js
   rewrites: async () => [
     { source: '/api/dolphin/:path*', destination: 'http://dolphin:12345/api/:path*' },
     { source: '/api/emails/:path*', destination: 'http://aubs:5000/api/emails/:path*' },
     { source: '/api/tasks/:path*', destination: 'http://aubs:5000/api/tasks/:path*' },
     { source: '/api/uitars/:path*', destination: 'http://dolphin:12345/api/uitars/:path*' },
   ]
   ```

## Connection to Dolphin

The components connect to Dolphin in two ways:

1. **REST API** for queries:
   - `GET /api/dolphin/executions` - List executions
   - `GET /api/dolphin/executions/:id` - Get execution details
   - `GET /api/dolphin/workers` - List workers

2. **WebSocket** for real-time updates:
   - Execution status changes
   - Task completion events
   - UI-TARS checkpoints
   - Performance metrics

## Visual Debugging Flow

```
Email Arrives
    ↓
AUBS Creates Dolphin DAG
    ↓
Dolphin Schedules Tasks → Workers Execute
    ↓
Each Agent Creates UI-TARS Checkpoints
    ↓
Checkpoints Stream to UITARSDebugPanel (WebSocket)
    ↓
User Sees Real-Time Execution Timeline
    ↓
Click Checkpoint → View Screenshot + Data
```

## Dependencies

- **React 18+** - Component framework
- **TypeScript 5+** - Type safety
- **Tailwind CSS** - Styling
- **WebSocket API** - Real-time updates

## License

MIT

## Related Documentation

- [PRD v2.1](../draftprd.md) - Full product requirements
- [Dolphin Documentation](https://dolphinscheduler.apache.org)
- [Open-WebUI](https://github.com/open-webui/open-webui)
