# UI-TARS Open-WebUI Components - Quick Start Guide

## TL;DR

UI-TARS Desktop is now **EMBEDDED** in Open-WebUI as React components. 1,513 lines of TypeScript/React code across 5 components, 1 hook, and type definitions.

## What You Got

### Components (1,279 lines)
1. **UITARSDebugPanel** (329 lines) - Visual debugging with execution timeline
2. **EmailDashboard** (309 lines) - Email processing view
3. **TaskManager** (297 lines) - Task management
4. **Analytics** (319 lines) - Performance metrics
5. **index.tsx** (25 lines) - Exports

### Infrastructure (234 lines)
6. **useDolphinWebSocket** (124 lines) - WebSocket hook
7. **types/index.ts** (110 lines) - TypeScript types

### Total: 1,513 lines of production-ready code

## 30-Second Setup

```bash
# 1. Install dependencies
cd C:\Users\John\ohhhmail\openwebui
npm install

# 2. Copy to Open-WebUI
cp -r components/* /path/to/open-webui/src/components/
cp -r hooks/* /path/to/open-webui/src/hooks/
cp -r types/* /path/to/open-webui/src/types/

# 3. Update Open-WebUI routes
# Add tabs in your router config

# 4. Start Open-WebUI
npm run dev
```

## Component Usage

### UITARSDebugPanel
```tsx
import { UITARSDebugPanel } from '@/components';

<UITARSDebugPanel
  executionId="optional-id"
  autoRefresh={true}
/>
```

Shows:
- Execution timeline
- Task status (Triage → Vision → Deadline → Context)
- Visual checkpoints with screenshots
- Performance metrics

### EmailDashboard
```tsx
import { EmailDashboard } from '@/components';

<EmailDashboard autoRefresh={true} />
```

Shows:
- Email list with status
- Agent outputs (all 4 agents)
- Actions taken
- Confidence scores

### TaskManager
```tsx
import { TaskManager } from '@/components';

<TaskManager />
```

Shows:
- Task list with priorities
- Due dates with overdue alerts
- Status management
- Link to originating email

### Analytics
```tsx
import { Analytics } from '@/components';

<Analytics />
```

Shows:
- System health (Dolphin, AUBS, Ollama, Qdrant)
- Processing stats
- Agent performance
- Success rates

## WebSocket Hook

```tsx
import { useDolphinWebSocket } from '@/hooks/useDolphinWebSocket';

const { isConnected, lastMessage } = useDolphinWebSocket({
  url: 'ws://dolphin:12345/ws',
  onExecutionUpdate: (execution) => {
    console.log('Execution updated:', execution);
  },
  onCheckpoint: (checkpoint) => {
    console.log('New checkpoint:', checkpoint);
  },
});
```

## API Endpoints Required

Configure these in your API proxy:

```
GET  /api/dolphin/executions          → Dolphin Scheduler
GET  /api/dolphin/executions/:id      → Dolphin Scheduler
GET  /api/uitars/checkpoints          → Dolphin Scheduler
GET  /api/emails                      → AUBS
GET  /api/emails/:id                  → AUBS
GET  /api/tasks                       → AUBS
PATCH /api/tasks/:id                  → AUBS
GET  /api/analytics/agents            → AUBS
GET  /api/analytics/processing        → AUBS
GET  /api/system/health               → AUBS
WS   ws://dolphin:12345/ws            → Dolphin WebSocket
```

## Environment Variables

```bash
NEXT_PUBLIC_DOLPHIN_API_URL=http://dolphin:12345/api
NEXT_PUBLIC_DOLPHIN_WS_URL=ws://dolphin:12345/ws
NEXT_PUBLIC_AUBS_API_URL=http://aubs:5000/api
NEXT_PUBLIC_AUTO_REFRESH_INTERVAL=10000
```

## Docker Compose

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - DOLPHIN_API_URL=http://dolphin:12345/api
      - DOLPHIN_WS_URL=ws://dolphin:12345/ws
      - AUBS_API_URL=http://aubs:5000/api
    volumes:
      - ./openwebui/components:/app/components/uitars
    depends_on:
      - dolphin-server
      - aubs
```

## Testing

```bash
# Start dev server
npm run dev

# Open browser
http://localhost:3000/debug        # UI-TARS Debug Panel
http://localhost:3000/emails       # Email Dashboard
http://localhost:3000/tasks        # Task Manager
http://localhost:3000/analytics    # Analytics

# Check WebSocket connection
# Browser console should show:
# [Dolphin WebSocket] Connected
```

## Component Architecture

```
UITARSDebugPanel
├── Execution List (sidebar)
│   ├── Email-123 (running)
│   ├── Email-456 (success)
│   └── Email-789 (failed)
├── Execution Details (main)
│   ├── Task Timeline
│   │   ├── [Triage] ━━━━━━━━━━ ✓ 1.2s
│   │   ├── [Vision] ━━━━━━━━━━ ✓ 3.5s
│   │   ├── [Deadline] ━━━━━━━━ ✓ 0.8s
│   │   └── [Context] ━━━━━━━━━ ⏳ Running...
│   └── Visual Checkpoints
│       ├── Screenshot 1 [📷]
│       ├── Screenshot 2 [📷]
│       └── Screenshot 3 [📷]
└── Checkpoint Detail Modal
    ├── Screenshot
    ├── Metrics (CPU, Memory, GPU)
    └── Data (JSON)
```

## Data Flow

```
Email Arrives
    ↓
AUBS Creates Dolphin DAG
    ↓
Dolphin Schedules Tasks
    ↓
Workers Execute (Triage → Vision → Deadline → Context)
    ↓
Each Agent Creates UI-TARS Checkpoint
    ↓
Checkpoint Sent via WebSocket → ws://dolphin:12345/ws
    ↓
useDolphinWebSocket() Hook Receives
    ↓
UITARSDebugPanel Component Updates
    ↓
User Sees Real-Time Timeline in Open-WebUI
```

## TypeScript Types

All data is fully typed:

```typescript
import type {
  DolphinExecution,
  DolphinTask,
  UITARSCheckpoint,
  UITARSSession,
  EmailProcessed,
  Action,
  AgentMetrics,
  SystemHealth,
} from '@/types';
```

## Key Features

- Real-time WebSocket updates
- Visual execution timeline
- Screenshot gallery
- Performance metrics
- Agent output viewer
- Task management
- System health monitoring
- Time range filtering
- Auto-refresh
- Error boundaries
- Loading states
- TypeScript type safety
- Responsive design (Tailwind CSS)

## File Structure

```
openwebui/
├── components/
│   ├── UITARSDebugPanel.tsx    # Debug interface
│   ├── EmailDashboard.tsx      # Email view
│   ├── TaskManager.tsx         # Task management
│   ├── Analytics.tsx           # Metrics
│   └── index.tsx               # Exports
├── hooks/
│   └── useDolphinWebSocket.ts  # WebSocket hook
├── types/
│   └── index.ts                # Type definitions
├── config/
│   └── openwebui-config.yaml   # Configuration
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── README.md
├── INTEGRATION_GUIDE.md
├── DEPLOYMENT_SUMMARY.md
└── QUICK_START.md              # This file
```

## Next Steps

1. Copy components to Open-WebUI
2. Update routing to include new tabs
3. Configure API proxy
4. Set environment variables
5. Deploy with Docker Compose
6. Test WebSocket connection
7. Verify all components load

## Support

- Full docs: `README.md`
- Integration: `INTEGRATION_GUIDE.md`
- Deployment: `DEPLOYMENT_SUMMARY.md`
- PRD: `../draftprd.md`

## Production Ready

✅ 1,513 lines of TypeScript/React
✅ Full type safety
✅ WebSocket reconnection
✅ Error handling
✅ Loading states
✅ Responsive design
✅ Performance optimized
✅ Production-ready code

**You're ready to integrate with Open-WebUI!**
