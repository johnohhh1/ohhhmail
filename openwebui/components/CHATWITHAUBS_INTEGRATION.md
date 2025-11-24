# ChatWithAUBS - Integration Guide

Quick guide to integrate the ChatWithAUBS component into your application.

## Quick Start (5 minutes)

### 1. Basic Integration

```tsx
import React from 'react';
import { ChatWithAUBS } from '@chilihead/openwebui-components';

function App() {
  return (
    <div className="h-screen">
      <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
    </div>
  );
}

export default App;
```

**That's it!** The component will:
- Create a chat session automatically
- Load operational context
- Enable streaming responses
- Show quick actions
- Handle all state management

### 2. Verify Backend is Running

Before using the chat, ensure AUBS backend is running:

```bash
# Navigate to AUBS directory
cd /c/Users/John/ohhhmail/aubs

# Start AUBS server
python -m uvicorn src.main:app --reload --port 8000

# Test in browser
http://localhost:8000/docs
```

### 3. Test the Chat

Ask AUBS these questions to verify it's working:

```
✅ "What emails did we process today?"
✅ "Show me all tasks"
✅ "What's most urgent?"
✅ "Give me a system health report"
```

## Common Integration Patterns

### Pattern 1: Floating Chat Button

Perfect for adding chat to existing dashboards without disrupting the layout.

```tsx
import React, { useState } from 'react';
import { ChatWithAUBS } from '@chilihead/openwebui-components';

function Dashboard() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <>
      {/* Your existing dashboard */}
      <div className="p-8">
        <h1>My Dashboard</h1>
        {/* ... your content ... */}
      </div>

      {/* Floating chat button */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 text-white rounded-full shadow-lg"
      >
        💬
      </button>

      {/* Chat modal */}
      {chatOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl h-[80vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-xl font-bold">Chat with AUBS</h2>
              <button onClick={() => setChatOpen(false)}>✕</button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

**Use case**: Existing applications where you want to add AI assistance without redesigning.

### Pattern 2: Sidebar Chat

Chat appears as a permanent sidebar. Great for power users.

```tsx
function App() {
  return (
    <div className="flex h-screen">
      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <YourMainContent />
      </div>

      {/* Chat sidebar */}
      <div className="w-[400px] border-l">
        <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
      </div>
    </div>
  );
}
```

**Use case**: Operations dashboards where constant AI assistance is valuable.

### Pattern 3: Tab-Based

Chat is a dedicated tab in your navigation.

```tsx
function App() {
  const [tab, setTab] = useState('dashboard');

  return (
    <div className="h-screen flex flex-col">
      <nav className="flex gap-4 p-4 border-b">
        <button onClick={() => setTab('dashboard')}>Dashboard</button>
        <button onClick={() => setTab('chat')}>Chat</button>
      </nav>

      <div className="flex-1">
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'chat' && (
          <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
        )}
      </div>
    </div>
  );
}
```

**Use case**: Clean separation between different app functions.

## Configuration Options

### Enable WebSocket (Real-time)

For instant responses and real-time updates:

```tsx
<ChatWithAUBS
  apiBaseUrl="http://localhost:8000"
  wsBaseUrl="ws://localhost:8000"
  enableWebSocket={true}
/>
```

### Hide Quick Actions

For a cleaner interface:

```tsx
<ChatWithAUBS
  apiBaseUrl="http://localhost:8000"
  enableQuickActions={false}
/>
```

### Add Event Handlers

Track chat activity:

```tsx
<ChatWithAUBS
  apiBaseUrl="http://localhost:8000"
  onSessionChange={(sessionId) => {
    console.log('Session:', sessionId);
    localStorage.setItem('lastSessionId', sessionId);
  }}
  onMessageSent={(message) => {
    console.log('Sent:', message);
    // Send to analytics
  }}
/>
```

## Styling

### Custom Container Classes

```tsx
<ChatWithAUBS
  apiBaseUrl="http://localhost:8000"
  className="shadow-2xl rounded-lg"
/>
```

### Custom Theme (via Tailwind)

The component uses these Tailwind classes that you can customize:

```css
/* In your tailwind.config.js */
module.exports = {
  theme: {
    extend: {
      colors: {
        'chat-primary': '#3B82F6',  /* Blue-600 */
        'chat-secondary': '#10B981', /* Green-500 */
      },
    },
  },
}
```

Then override in your global CSS:

```css
.bg-blue-600 {
  @apply bg-chat-primary;
}
```

## Production Deployment

### Environment Variables

Create `.env` file:

```bash
REACT_APP_AUBS_API_URL=https://your-api.com
REACT_APP_AUBS_WS_URL=wss://your-api.com
```

Use in component:

```tsx
<ChatWithAUBS
  apiBaseUrl={process.env.REACT_APP_AUBS_API_URL}
  wsBaseUrl={process.env.REACT_APP_AUBS_WS_URL}
  enableWebSocket={true}
/>
```

### CORS Configuration

Ensure your AUBS backend allows your frontend domain:

```python
# In AUBS backend (main.py)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WebSocket Proxy (nginx)

If using nginx, configure WebSocket proxy:

```nginx
location /ws/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Common Issues & Solutions

### Issue 1: "Failed to create session"

**Cause**: Backend not running or incorrect API URL

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/api/chat/context

# Verify URL in component
<ChatWithAUBS apiBaseUrl="http://localhost:8000" />
```

### Issue 2: CORS errors in browser console

**Cause**: Backend not configured for CORS

**Solution**: Add CORS middleware to AUBS backend (see Production Deployment)

### Issue 3: Messages not streaming

**Cause**: Proxy buffering responses

**Solution**: Disable buffering in nginx:
```nginx
proxy_buffering off;
proxy_cache off;
```

### Issue 4: WebSocket connection fails

**Cause**: Wrong WebSocket URL or firewall blocking

**Solution**:
```tsx
// Try without WebSocket first
<ChatWithAUBS
  apiBaseUrl="http://localhost:8000"
  enableWebSocket={false}
/>
```

## Testing

### Manual Testing Checklist

- [ ] Chat loads without errors
- [ ] Can send messages
- [ ] Streaming works
- [ ] Quick actions work
- [ ] Session history loads
- [ ] Operational context displays
- [ ] New session creation works
- [ ] Session deletion works

### Automated Testing

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatWithAUBS from './ChatWithAUBS';

test('sends message successfully', async () => {
  render(<ChatWithAUBS apiBaseUrl="http://localhost:8000" />);

  const input = screen.getByPlaceholderText(/Ask AUBS/);
  const sendButton = screen.getByText('Send');

  fireEvent.change(input, { target: { value: 'Test message' } });
  fireEvent.click(sendButton);

  await waitFor(() => {
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });
});
```

## Performance Optimization

### 1. Lazy Loading

```tsx
import { lazy, Suspense } from 'react';

const ChatWithAUBS = lazy(() => import('./ChatWithAUBS'));

function App() {
  return (
    <Suspense fallback={<div>Loading chat...</div>}>
      <ChatWithAUBS apiBaseUrl="http://localhost:8000" />
    </Suspense>
  );
}
```

### 2. Memoization

```tsx
import { memo } from 'react';

const MemoizedChat = memo(ChatWithAUBS);

function App() {
  return <MemoizedChat apiBaseUrl="http://localhost:8000" />;
}
```

### 3. Request Debouncing

The component already includes request cancellation, but you can add debouncing:

```tsx
// Component already handles this internally
// No additional configuration needed
```

## Mobile Optimization

The component is mobile-responsive by default. For better mobile experience:

```tsx
function MobileApp() {
  return (
    <div className="h-screen">
      <ChatWithAUBS
        apiBaseUrl="http://localhost:8000"
        // Quick actions work great on mobile
        enableQuickActions={true}
        // Disable WebSocket on mobile to save battery
        enableWebSocket={false}
      />
    </div>
  );
}
```

## Analytics Integration

### Google Analytics

```tsx
function App() {
  return (
    <ChatWithAUBS
      apiBaseUrl="http://localhost:8000"
      onMessageSent={(message) => {
        window.gtag('event', 'chat_message', {
          message_length: message.length,
        });
      }}
      onSessionChange={(sessionId) => {
        window.gtag('event', 'chat_session', {
          session_id: sessionId,
        });
      }}
    />
  );
}
```

### Custom Analytics

```tsx
function App() {
  return (
    <ChatWithAUBS
      apiBaseUrl="http://localhost:8000"
      onMessageSent={async (message) => {
        await fetch('/api/analytics', {
          method: 'POST',
          body: JSON.stringify({
            event: 'chat_message',
            data: { message },
          }),
        });
      }}
    />
  );
}
```

## Next Steps

1. **Read the full documentation**: [ChatWithAUBS.md](./ChatWithAUBS.md)
2. **Check out examples**: [ChatWithAUBSDemo.tsx](./ChatWithAUBSDemo.tsx)
3. **Review AUBS API docs**: [CHAT_API.md](../aubs/CHAT_API.md)
4. **Explore other components**: [Dashboard.tsx](./Dashboard.tsx), [TaskManager.tsx](./TaskManager.tsx)

## Support

Need help? Check these resources:

1. Component documentation: `/c/Users/John/ohhhmail/openwebui/components/ChatWithAUBS.md`
2. AUBS API docs: `/c/Users/John/ohhhmail/aubs/CHAT_API.md`
3. Example integrations: `/c/Users/John/ohhhmail/openwebui/components/ChatWithAUBSDemo.tsx`
4. Backend logs: `/c/Users/John/ohhhmail/logs/`

## File Locations

```
ChatWithAUBS.tsx                    - Main component
ChatWithAUBS.md                     - Full documentation
ChatWithAUBSDemo.tsx                - Integration examples
CHATWITHAUBS_INTEGRATION.md         - This guide
```

All files located at: `/c/Users/John/ohhhmail/openwebui/components/`
