# ChatWithAUBS Component

Full AI Operations Assistant with complete operational awareness of your email processing system.

## Overview

ChatWithAUBS is a comprehensive chat interface that connects to the AUBS (AI-powered Universal Business System) backend. The assistant has **real-time access** to all operational data including emails, tasks, deadlines, agent performance, and system health.

## Features

### Core Capabilities
- **Real-time Chat Interface**: Streaming responses for immediate feedback
- **Full Operational Awareness**: Access to all emails, tasks, deadlines, and agent data
- **Conversation History**: Persistent sessions with message history
- **Quick Actions**: Pre-defined prompts for common questions
- **Context Display**: Live system statistics and health metrics
- **Session Management**: Multiple conversation threads
- **WebSocket Support**: Real-time bi-directional communication (optional)
- **Error Handling**: Graceful error display and recovery

### What AUBS Knows

AUBS has complete operational context including:

1. **Email Processing**
   - Total emails processed (all time and today)
   - Recent emails with subjects, senders, status
   - Failed email processing attempts
   - Emails with attachments
   - Processing timestamps

2. **Tasks & Actions**
   - All tasks created from emails
   - Task priorities and due dates
   - Task status (pending, completed, etc.)
   - Task creation timestamps

3. **Deadlines & Events**
   - Upcoming deadlines extracted from emails
   - Deadline confidence scores
   - Associated email context
   - Calendar events scheduled

4. **Agent Performance**
   - Execution counts per agent type
   - Average execution times
   - Confidence scores
   - Model usage statistics

5. **System Health**
   - Dolphin server connection status
   - NATS message broker status
   - Active chat sessions
   - Total messages processed

6. **High-Risk Items**
   - Failed executions with error messages
   - High-priority tasks
   - Overdue deadlines
   - System anomalies

## Installation

```bash
# The component is already part of the openwebui package
import { ChatWithAUBS } from '@chilihead/openwebui-components';
```

## Usage

### Basic Usage

```tsx
import React from 'react';
import { ChatWithAUBS } from '@chilihead/openwebui-components';

function App() {
  return (
    <div className="h-screen">
      <ChatWithAUBS />
    </div>
  );
}
```

### Advanced Usage

```tsx
import React from 'react';
import { ChatWithAUBS } from '@chilihead/openwebui-components';

function App() {
  const handleSessionChange = (sessionId: string) => {
    console.log('Session changed:', sessionId);
    // Save to localStorage, analytics, etc.
  };

  const handleMessageSent = (message: string) => {
    console.log('Message sent:', message);
    // Track analytics, log messages, etc.
  };

  return (
    <div className="h-screen">
      <ChatWithAUBS
        apiBaseUrl="http://localhost:8000"
        wsBaseUrl="ws://localhost:8000"
        enableWebSocket={true}
        enableQuickActions={true}
        onSessionChange={handleSessionChange}
        onMessageSent={handleMessageSent}
        className="custom-chat-container"
      />
    </div>
  );
}
```

### Full-Screen Modal

```tsx
import React, { useState } from 'react';
import { ChatWithAUBS } from '@chilihead/openwebui-components';

function Dashboard() {
  const [showChat, setShowChat] = useState(false);

  return (
    <div>
      {/* Your dashboard content */}
      <button
        onClick={() => setShowChat(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-full shadow-lg"
      >
        💬 Chat with AUBS
      </button>

      {/* Chat modal */}
      {showChat && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-[80vh]">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-xl font-bold">Chat with AUBS</h2>
              <button
                onClick={() => setShowChat(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="h-[calc(100%-64px)]">
              <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiBaseUrl` | `string` | `http://localhost:8000` | Base URL for AUBS API |
| `wsBaseUrl` | `string` | `ws://localhost:8000` | Base URL for WebSocket connection |
| `enableWebSocket` | `boolean` | `false` | Enable WebSocket for real-time communication |
| `enableQuickActions` | `boolean` | `true` | Show quick action buttons |
| `enableVoice` | `boolean` | `false` | Enable voice input (future feature) |
| `className` | `string` | `''` | Additional CSS classes |
| `onSessionChange` | `(sessionId: string) => void` | `undefined` | Callback when session changes |
| `onMessageSent` | `(message: string) => void` | `undefined` | Callback when message is sent |

## Quick Actions

The component includes pre-defined quick actions for common queries:

1. **What's most urgent today?** - Shows urgent tasks and deadlines
2. **Show all deadlines** - Lists all upcoming deadlines
3. **Vision agent extractions** - Shows data extracted by Vision agent
4. **Show failed emails** - Displays email processing failures
5. **Create a task** - Helps create a new task
6. **Email status** - Shows recent email processing status
7. **System status** - Full system health report
8. **Agent performance** - AI agent performance metrics

## Example Questions

### Email Queries
```
- "What emails did we process today?"
- "Show me the most recent email from the fire inspector"
- "What's the status of the email about menu pricing?"
- "Show me all emails that failed to process"
- "What emails have attachments?"
```

### Task Queries
```
- "What tasks are due this week?"
- "Show me all high-priority tasks"
- "Create a task for following up on the fire inspection"
- "What tasks are overdue?"
- "What tasks did we create from emails today?"
```

### Deadline Queries
```
- "What deadlines are coming up?"
- "Show me all deadlines for next week"
- "What's the most urgent deadline?"
- "Show me deadlines with high confidence scores"
```

### Agent Queries
```
- "How are the AI agents performing?"
- "What did the Vision agent extract from recent emails?"
- "Show me execution times for the Email Processor agent"
- "What agents are currently active?"
```

### System Queries
```
- "Give me a system health report"
- "What's the overall processing status?"
- "Show me system statistics"
- "Are there any high-risk items?"
```

### General Queries
```
- "What's most urgent today?"
- "Give me a daily summary"
- "What needs my attention?"
- "Show me a weekly overview"
```

## API Integration

The component connects to these AUBS endpoints:

### Chat Endpoints
- `POST /api/chat` - Send a message
- `GET /api/chat/history/{session_id}` - Get conversation history
- `GET /api/chat/sessions` - List all sessions
- `POST /api/chat/sessions` - Create new session
- `DELETE /api/chat/sessions/{session_id}` - Delete session
- `GET /api/chat/context` - Get operational context
- `WS /ws/chat/{session_id}` - WebSocket connection

### Response Format

**HTTP Streaming Response**:
```
Content-Type: text/event-stream

data: Today we've
data:  processed 12
data:  emails...
```

**WebSocket Response**:
```json
{"type": "ack", "timestamp": "2025-01-15T10:30:00Z"}
{"type": "chunk", "content": "The fire"}
{"type": "chunk", "content": " inspection email"}
{"type": "complete", "timestamp": "2025-01-15T10:30:05Z"}
```

## State Management

The component manages these states:

- `messages` - Array of conversation messages
- `inputMessage` - Current input text
- `isLoading` - Loading state for API calls
- `sessionId` - Current session identifier
- `sessions` - List of available sessions
- `context` - Operational context data
- `isStreaming` - Streaming state for responses
- `wsConnected` - WebSocket connection status
- `error` - Error message display

## Styling

The component uses Tailwind CSS classes and is fully responsive. Key style features:

- **Gradient header** with operational awareness indicator
- **Message bubbles** with distinct user/assistant styling
- **Streaming animation** with typing cursor
- **Loading states** with animated dots
- **Error display** with prominent red styling
- **Quick actions** with hover effects
- **Responsive layout** for mobile and desktop

## Performance Considerations

1. **Message Streaming**: Uses HTTP streaming or WebSocket for real-time responses
2. **Auto-scroll**: Automatically scrolls to latest message
3. **Request Cancellation**: Aborts previous requests when new ones are sent
4. **Session Persistence**: Maintains conversation history across page reloads
5. **Lazy Loading**: Loads operational context on demand

## Accessibility

- **Keyboard Navigation**: Full support for Enter key to send messages
- **Focus Management**: Auto-focus on input after sending
- **Screen Reader**: Semantic HTML with proper ARIA labels
- **Color Contrast**: WCAG AA compliant color schemes

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Dependencies

Required packages (already included in parent package):
- `react` ^18.3.1
- `react-dom` ^18.3.1
- `tailwindcss` ^3.4.4

## Troubleshooting

### Connection Issues

If the chat shows "HTTP Mode" instead of "Connected":
1. Check if AUBS backend is running on the specified `apiBaseUrl`
2. Verify WebSocket server is accessible at `wsBaseUrl`
3. Check for CORS issues in browser console
4. Ensure firewall allows WebSocket connections

### No Response from AUBS

1. Verify AUBS backend is running: `http://localhost:8000/docs`
2. Check backend logs for errors
3. Verify session was created successfully
4. Check network tab for failed API calls

### Streaming Not Working

1. Ensure backend supports Server-Sent Events (SSE)
2. Check `Content-Type: text/event-stream` in response headers
3. Verify nginx/proxy doesn't buffer responses
4. Try disabling browser extensions that modify requests

### Session Not Persisting

1. Check browser localStorage is enabled
2. Verify session ID is returned from API
3. Check for session timeout on backend
4. Verify database connection for session storage

## Development

### Running Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint
```

## File Location

```
/c/Users/John/ohhhmail/openwebui/components/ChatWithAUBS.tsx
```

## Related Components

- `Dashboard.tsx` - Main operations dashboard
- `EmailDashboard.tsx` - Email processing view
- `TaskManager.tsx` - Task management interface
- `AgentMonitor.tsx` - Agent performance monitoring
- `UITARSDebugPanel.tsx` - Debug panel for executions

## License

MIT License - Part of the ohhhmail project

## Support

For issues or questions:
1. Check the [AUBS Chat API documentation](../aubs/CHAT_API.md)
2. Review [AUBS examples](../aubs/CHAT_EXAMPLES.md)
3. Check backend logs in `/c/Users/John/ohhhmail/logs/`
4. Open an issue in the repository

## Changelog

### Version 2.1.0
- Initial release with full operational awareness
- HTTP streaming support
- WebSocket support (optional)
- Quick actions
- Session management
- Operational context display
- Mobile responsive design
