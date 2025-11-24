# ohhhmail Open-WebUI Components

Complete TypeScript React components for the ohhhmail AI email processing system, designed to be embedded in Open-WebUI.

## Components Overview

### 1. Dashboard.tsx
**Main overview component showing system status and activity**

Features:
- Real-time email processing statistics
- Agent performance metrics with success rates
- System health monitoring (AUBS, Dolphin, Ollama, PostgreSQL, Redis, Qdrant)
- Recent activity feed
- WebSocket integration for live updates
- Auto-refresh every 10 seconds

API Endpoints:
- `GET /api/stats/dashboard` - Get dashboard statistics
- `GET /api/stats/agents` - Get agent metrics
- `GET /api/health` - Get system health status
- `GET /api/emails?limit=5&sort=recent` - Get recent emails

Usage:
```tsx
import { Dashboard } from './components';

<Dashboard className="h-screen" />
```

### 2. CalendarView.tsx
**Calendar interface for events and deadlines extracted from emails**

Features:
- Month/week view toggle
- Event display with color coding by type (deadline, meeting, reminder, task)
- Priority indicators (urgent, high, medium, low)
- Event creation from emails
- Today highlighting
- Event detail modal
- Navigation controls

Event Types:
- Deadline (red)
- Meeting (blue)
- Reminder (yellow)
- Task (green)

API Endpoints:
- `GET /api/calendar/events?start={ISO}&end={ISO}` - Get events in date range

Usage:
```tsx
import { CalendarView } from './components';

<CalendarView className="h-screen" />
```

### 3. AgentMonitor.tsx
**Real-time agent status and management interface**

Features:
- Live agent status monitoring (idle, running, error)
- Enable/disable agents with toggle switches
- Model selection per agent (Ollama, OpenAI, Claude)
- Performance metrics per agent:
  - Total executions
  - Success rate
  - Average response time
  - Average confidence
- Current task display
- Test agent functionality
- Agent detail modal with full configuration

Supported Agents:
- Triage Agent (📋)
- Vision Agent (👁️)
- Deadline Agent (⏰)
- Context Agent (🧠)

API Endpoints:
- `GET /api/agents/status` - Get all agent statuses
- `GET /api/stats/agents` - Get agent performance metrics
- `POST /api/agents/{type}/toggle` - Enable/disable agent
- `POST /api/agents/{type}/model` - Change agent model
- `POST /api/agents/{type}/test` - Test agent

Usage:
```tsx
import { AgentMonitor } from './components';

<AgentMonitor className="h-screen" />
```

### 4. Settings.tsx
**System configuration and preferences**

Features:
- **Models Tab**: Configure AI models for each agent
  - Provider selection (Ollama, OpenAI, Anthropic)
  - Model selection from available models
  - API key configuration
  - Custom base URL support

- **Thresholds Tab**: Configure confidence thresholds
  - High confidence threshold (auto-process)
  - Medium confidence threshold (requires confirmation)
  - Low confidence threshold (manual review)
  - Auto-process threshold

- **Notifications Tab**: Configure notification preferences
  - Email notifications toggle
  - Slack notifications toggle
  - Webhook URL configuration
  - Notification triggers (high confidence, low confidence, errors)

- **Integrations Tab**: External service connections
  - Gmail integration with OAuth
  - Calendar sync
  - Task manager integration
  - n8n webhook URL

API Endpoints:
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Save settings
- `GET /api/models/available` - Get available models

Usage:
```tsx
import { Settings } from './components';

<Settings className="h-screen" />
```

## Existing Components

### 5. EmailDashboard.tsx
Email processing dashboard showing processed emails and agent outputs.

### 6. TaskManager.tsx
Task management interface for tasks created from emails.

### 7. Analytics.tsx
Analytics and insights dashboard.

### 8. UITARSDebugPanel.tsx
Debug panel for UI-TARS agent execution monitoring.

## Common Features

All components include:
- TypeScript type safety
- Responsive design with Tailwind CSS
- Real-time WebSocket updates where applicable
- Error handling
- Loading states
- Auto-refresh functionality
- Connection status indicators

## API Integration

All components connect to the AUBS API at `http://localhost:5000`. Key endpoints:

### Email & Processing
- `GET /api/emails` - List emails with filtering
- `GET /api/emails/{id}` - Get email details

### Agent Management
- `GET /api/agents/status` - Get agent statuses
- `POST /api/agents/{type}/toggle` - Enable/disable agent
- `POST /api/agents/{type}/model` - Change model

### Calendar
- `GET /api/calendar/events` - Get calendar events

### Statistics
- `GET /api/stats/dashboard` - Dashboard stats
- `GET /api/stats/agents` - Agent metrics

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

### Health
- `GET /api/health` - System health check

## WebSocket Integration

Components use `useDolphinWebSocket` hook for real-time updates:

```tsx
import { useDolphinWebSocket } from '../hooks/useDolphinWebSocket';

const { isConnected, lastMessage } = useDolphinWebSocket({
  url: 'ws://localhost:5000/ws',
  onExecutionUpdate: (execution) => {
    // Handle execution update
  },
  onCheckpoint: (checkpoint) => {
    // Handle checkpoint
  },
  onError: (error) => {
    // Handle error
  },
});
```

## Types

All TypeScript types are defined in `../types/index.ts`:

- `EmailProcessed` - Processed email data
- `Action` - Action taken on email
- `AgentMetrics` - Agent performance metrics
- `SystemHealth` - System health status
- `DolphinExecution` - Dolphin DAG execution
- `DolphinTask` - Individual task in DAG
- `UITARSCheckpoint` - UI-TARS checkpoint data

## Styling

Components use Tailwind CSS for styling with a consistent color scheme:

- Primary: Blue (#2563eb)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Error: Red (#ef4444)
- Gray scale for backgrounds and text

## Installation

Components are already part of the ohhhmail OpenWebUI integration. Import from:

```tsx
import {
  Dashboard,
  CalendarView,
  AgentMonitor,
  Settings,
  EmailDashboard,
  TaskManager,
  Analytics,
  UITARSDebugPanel,
} from '@/ohhhmail/openwebui/components';
```

## Development

To add new components:

1. Create component file in `components/` directory
2. Add TypeScript interface definitions
3. Connect to AUBS API endpoints
4. Add WebSocket integration if needed
5. Export from `index.tsx`

## Testing

Test components with the AUBS backend running:

```bash
# Start AUBS backend
cd ohhhmail/aubs
python app.py

# Components will connect to http://localhost:5000
```

## Contributing

When adding features:
- Maintain TypeScript type safety
- Follow existing component patterns
- Use Tailwind CSS for styling
- Include loading and error states
- Add proper API error handling
- Document new API endpoints
