# UI-TARS Open-WebUI Integration Guide

This guide explains how to embed UI-TARS components into your Open-WebUI installation.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Open-WebUI Frontend                   │
│  ┌────────────┬──────────┬──────────┬──────────────┐   │
│  │  Email Tab │ Task Tab │ Debug    │ Analytics    │   │
│  │            │          │ Tab      │ Tab          │   │
│  │ ┌────────┐ │┌────────┐│┌────────┐│┌───────────┐│   │
│  │ │ Email  │ ││ Task   ││││ UITARs│││ Analytics ││   │
│  │ │Dashboard│││Manager │││ Debug ││││Dashboard  ││   │
│  │ └────────┘ │└────────┘│└────────┘│└───────────┘│   │
│  └────────────┴──────────┴──────────┴──────────────┘   │
│                         ▲                                │
│                         │ WebSocket + REST API           │
└─────────────────────────┼────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────────┐            ┌─────────────────────┐
│ Dolphin Scheduler │            │  AUBS Logic Layer   │
│  ┌─────────────┐  │            │  ┌──────────────┐  │
│  │ DAG Engine  │  │◄───────────┤  │ Orchestrator │  │
│  └─────────────┘  │            │  └──────────────┘  │
│  ┌─────────────┐  │            │  ┌──────────────┐  │
│  │   Workers   │  │            │  │ Action Router│  │
│  └─────────────┘  │            │  └──────────────┘  │
└───────────────────┘            └─────────────────────┘
        │                                   │
        └───────────────┬───────────────────┘
                        ▼
              ┌──────────────────┐
              │  Agent Workers   │
              │  ┌────┐  ┌────┐ │
              │  │Triage│Vision│ │
              │  ├────┤  ├────┤ │
              │  │Dead│  │Ctx │ │
              │  │line│  │    │ │
              │  └────┘  └────┘ │
              └──────────────────┘
```

## Component Integration

### 1. UITARSDebugPanel Integration

**Purpose:** Visual debugging of Dolphin executions with real-time updates

**Integration Location:** Add as a new tab in Open-WebUI

```tsx
// In Open-WebUI's main layout file (e.g., app/layout.tsx)
import { UITARSDebugPanel } from '@/components/UITARSDebugPanel';

// Add to navigation tabs
const tabs = [
  // ... existing tabs
  {
    id: 'debug',
    label: 'UI-TARS Debug',
    icon: BugReportIcon,
    component: <UITARSDebugPanel />,
  },
];
```

**Data Flow:**
```
Dolphin Worker Executes Task
        ↓
Creates Checkpoint (screenshot + data)
        ↓
Sends via WebSocket → ws://dolphin:12345/ws
        ↓
useDolphinWebSocket() receives update
        ↓
UITARSDebugPanel renders checkpoint
```

### 2. EmailDashboard Integration

**Purpose:** Show processed emails with agent analysis

```tsx
// In Open-WebUI router
import { EmailDashboard } from '@/components/EmailDashboard';

// Add route
{
  path: '/emails',
  element: <EmailDashboard />,
}
```

**API Requirements:**
- `GET /api/emails?status=all` - List emails
- `GET /api/emails/:id` - Get email details

### 3. TaskManager Integration

**Purpose:** Manage tasks created from email processing

```tsx
import { TaskManager } from '@/components/TaskManager';

// Add to tabs
{
  id: 'tasks',
  component: <TaskManager />,
}
```

**API Requirements:**
- `GET /api/tasks?status=all` - List tasks
- `PATCH /api/tasks/:id` - Update task status

### 4. Analytics Integration

**Purpose:** System health and performance metrics

```tsx
import { Analytics } from '@/components/Analytics';

{
  id: 'analytics',
  component: <Analytics />,
}
```

**API Requirements:**
- `GET /api/analytics/agents?range=24h` - Agent metrics
- `GET /api/system/health` - System status
- `GET /api/analytics/processing?range=24h` - Processing stats

## API Proxy Configuration

Add to `next.config.js`:

```js
module.exports = {
  async rewrites() {
    return [
      // Dolphin API
      {
        source: '/api/dolphin/:path*',
        destination: 'http://dolphin:12345/api/:path*',
      },
      // AUBS API
      {
        source: '/api/emails/:path*',
        destination: 'http://aubs:5000/api/emails/:path*',
      },
      {
        source: '/api/tasks/:path*',
        destination: 'http://aubs:5000/api/tasks/:path*',
      },
      // UI-TARS Checkpoints
      {
        source: '/api/uitars/:path*',
        destination: 'http://dolphin:12345/api/uitars/:path*',
      },
      // Analytics
      {
        source: '/api/analytics/:path*',
        destination: 'http://aubs:5000/api/analytics/:path*',
      },
      {
        source: '/api/system/:path*',
        destination: 'http://aubs:5000/api/system/:path*',
      },
    ];
  },
};
```

## WebSocket Configuration

### Server-Side WebSocket Proxy

If using Next.js API routes:

```ts
// pages/api/ws/dolphin.ts
import type { NextApiRequest } from 'next';
import { WebSocketServer } from 'ws';

export default function handler(req: NextApiRequest, res: any) {
  if (req.method === 'GET') {
    const wss = new WebSocketServer({ noServer: true });

    res.socket.server.on('upgrade', (request, socket, head) => {
      wss.handleUpgrade(request, socket, head, (ws) => {
        // Proxy to Dolphin WebSocket
        const dolphinWs = new WebSocket('ws://dolphin:12345/ws');

        dolphinWs.on('message', (data) => {
          ws.send(data);
        });

        ws.on('message', (data) => {
          dolphinWs.send(data);
        });
      });
    });
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};
```

### Client-Side Usage

The `useDolphinWebSocket` hook handles all WebSocket logic:

```tsx
import { useDolphinWebSocket } from '@/hooks/useDolphinWebSocket';

function MyComponent() {
  const { isConnected, lastMessage } = useDolphinWebSocket({
    url: '/api/ws/dolphin', // Proxied WebSocket
    onExecutionUpdate: (execution) => {
      console.log('Execution updated:', execution);
    },
  });

  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

## Environment Variables

Create `.env.local`:

```bash
# Dolphin Integration
NEXT_PUBLIC_DOLPHIN_API_URL=http://localhost:12345/api
NEXT_PUBLIC_DOLPHIN_WS_URL=ws://localhost:12345/ws

# AUBS Integration
NEXT_PUBLIC_AUBS_API_URL=http://localhost:5000/api

# Feature Flags
NEXT_PUBLIC_ENABLE_UITARS_DEBUG=true
NEXT_PUBLIC_ENABLE_SCREENSHOTS=true
NEXT_PUBLIC_AUTO_REFRESH_INTERVAL=10000
```

## Docker Deployment

Update `docker-compose.yml`:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DOLPHIN_API_URL=http://dolphin:12345/api
      - DOLPHIN_WS_URL=ws://dolphin:12345/ws
      - AUBS_API_URL=http://aubs:5000/api
    volumes:
      # Mount custom components
      - ./openwebui/components:/app/components/custom
      - ./openwebui/config:/app/config
    depends_on:
      - dolphin-server
      - aubs
      - ollama
    networks:
      - chilihead-network

  dolphin-server:
    # ... Dolphin configuration

  aubs:
    # ... AUBS configuration

networks:
  chilihead-network:
    driver: bridge
```

## Testing Integration

### 1. Test Component Loading

```bash
# Start Open-WebUI in development mode
cd /path/to/open-webui
npm run dev
```

Navigate to:
- `http://localhost:3000/emails` - Email Dashboard
- `http://localhost:3000/tasks` - Task Manager
- `http://localhost:3000/debug` - UI-TARS Debug Panel
- `http://localhost:3000/analytics` - Analytics

### 2. Test WebSocket Connection

Open browser console and check for:
```
[Dolphin WebSocket] Connected
```

### 3. Test API Endpoints

```bash
# Test email listing
curl http://localhost:3000/api/emails

# Test Dolphin executions
curl http://localhost:3000/api/dolphin/executions

# Test system health
curl http://localhost:3000/api/system/health
```

## Customization

### Theming

Update `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      'brand-primary': '#2196F3',
      'brand-secondary': '#FF9800',
    },
  },
}
```

### Component Props

All components accept a `className` prop for custom styling:

```tsx
<UITARSDebugPanel className="custom-debug-panel" />
```

### Custom Filters

Extend the components by passing custom filter functions:

```tsx
<EmailDashboard
  customFilter={(email) => email.status === 'completed'}
/>
```

## Troubleshooting

### WebSocket Not Connecting

1. Check Dolphin is running: `docker ps | grep dolphin`
2. Verify WebSocket URL in `.env.local`
3. Check browser console for errors
4. Ensure CORS is configured on Dolphin server

### Components Not Loading

1. Verify imports are correct
2. Check TypeScript errors: `npm run type-check`
3. Ensure dependencies are installed: `npm install`

### API 404 Errors

1. Check API proxy configuration in `next.config.js`
2. Verify backend services are running
3. Check network connectivity between containers

## Production Checklist

- [ ] All environment variables configured
- [ ] WebSocket proxy configured
- [ ] API endpoints secured (if needed)
- [ ] CORS configured on backend
- [ ] Components lazy-loaded for performance
- [ ] Error boundaries added
- [ ] Logging configured
- [ ] Performance monitoring enabled

## Support

For issues or questions:
1. Check the [main README](README.md)
2. Review the [PRD](../draftprd.md)
3. Check Dolphin logs: `docker logs dolphin-server`
4. Check AUBS logs: `docker logs aubs`
