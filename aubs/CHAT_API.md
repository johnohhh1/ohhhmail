# AUBS Chat API Documentation

## Overview

The AUBS Chat API provides an intelligent conversational interface with **complete operational awareness** of your email processing system. The chat assistant has real-time access to:

- All processed emails
- Current tasks and deadlines
- Agent performance metrics
- Recent actions taken
- System status and health
- 30-day historical context via Context Agent memory

## Features

- **Full Operational Context**: The chat assistant knows everything happening in your system
- **Streaming Responses**: Real-time streaming for better UX
- **WebSocket Support**: Bi-directional real-time communication
- **Session Management**: Persistent conversation history
- **Claude Sonnet 4**: Powered by Anthropic's latest model
- **Proactive Insights**: Assistant identifies issues requiring attention

## API Endpoints

### 1. Send Chat Message

**Endpoint**: `POST /api/chat`

**Request Body**:
```json
{
  "message": "What emails did we process today?",
  "session_id": "uuid-optional",
  "stream": false
}
```

**Response** (Non-streaming):
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Today we've processed 12 emails...",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response** (Streaming):
```
Content-Type: text/event-stream

data: Today we've
data:  processed 12
data:  emails...
```

### 2. Get Chat History

**Endpoint**: `GET /api/chat/history/{session_id}?limit=50`

**Response**:
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message_count": 10,
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "What emails did we process today?",
      "timestamp": "2025-01-15T10:30:00Z",
      "metadata": {}
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Today we've processed 12 emails...",
      "timestamp": "2025-01-15T10:30:05Z",
      "metadata": {}
    }
  ]
}
```

### 3. List Chat Sessions

**Endpoint**: `GET /api/chat/sessions?user_id=default&limit=20`

**Response**:
```json
{
  "user_id": "default",
  "session_count": 5,
  "sessions": [
    {
      "id": "session-uuid",
      "started_at": "2025-01-15T09:00:00Z",
      "last_activity": "2025-01-15T10:30:00Z",
      "message_count": 15,
      "metadata": {}
    }
  ]
}
```

### 4. Create Chat Session

**Endpoint**: `POST /api/chat/sessions?user_id=default`

**Response**:
```json
{
  "id": "new-session-uuid",
  "user_id": "default",
  "started_at": "2025-01-15T11:00:00Z",
  "message_count": 0
}
```

### 5. Delete Chat Session

**Endpoint**: `DELETE /api/chat/sessions/{session_id}`

**Response**: `204 No Content`

### 6. Get Operational Context

**Endpoint**: `GET /api/chat/context`

**Response**:
```json
{
  "statistics": {
    "total_emails_processed": 145,
    "emails_today": 12,
    "active_executions": 2,
    "failed_executions": 3,
    "total_tasks_created": 48,
    "total_events_scheduled": 25
  },
  "recent_activity": {
    "emails_count": 10,
    "tasks_count": 15,
    "deadlines_count": 8
  },
  "system_health": {
    "dolphin_connected": true,
    "nats_connected": true,
    "active_sessions": 3,
    "total_messages": 142
  },
  "high_risk_items_count": 2
}
```

### 7. WebSocket Chat (Real-time)

**Endpoint**: `WS /ws/chat/{session_id}`

**Client sends**:
```json
{
  "message": "What's the status of the fire inspection email?"
}
```

**Server streams**:
```json
{"type": "ack", "timestamp": "2025-01-15T10:30:00Z"}
{"type": "chunk", "content": "The fire"}
{"type": "chunk", "content": " inspection email"}
{"type": "chunk", "content": " was processed..."}
{"type": "complete", "timestamp": "2025-01-15T10:30:05Z"}
```

## Usage Examples

### Python

```python
import httpx
import json

# Create session
response = httpx.post("http://localhost:8000/api/chat/sessions")
session = response.json()
session_id = session["id"]

# Send message
chat_response = httpx.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Show me failed email executions",
        "session_id": session_id,
        "stream": False
    }
)

print(chat_response.json()["message"])

# Get history
history = httpx.get(
    f"http://localhost:8000/api/chat/history/{session_id}"
)
print(json.dumps(history.json(), indent=2))
```

### JavaScript (Streaming)

```javascript
// Create session
const sessionResponse = await fetch('http://localhost:8000/api/chat/sessions', {
  method: 'POST'
});
const session = await sessionResponse.json();

// Send message with streaming
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What tasks need attention?',
    session_id: session.id,
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const content = line.slice(6);
      console.log(content);
    }
  }
}
```

### WebSocket (Real-time)

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: 'What emails came in today?'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'ack':
      console.log('Message acknowledged');
      break;
    case 'chunk':
      process.stdout.write(data.content);
      break;
    case 'complete':
      console.log('\nResponse complete');
      break;
    case 'error':
      console.error('Error:', data.message);
      break;
  }
};
```

### cURL

```bash
# Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/chat/sessions | jq -r '.id')

# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What are the high-priority tasks?\",
    \"session_id\": \"$SESSION_ID\",
    \"stream\": false
  }" | jq

# Get operational context
curl http://localhost:8000/api/chat/context | jq

# Get chat history
curl "http://localhost:8000/api/chat/history/$SESSION_ID?limit=10" | jq
```

## What the Chat Assistant Knows

### Email Processing
- Total emails processed (all time and today)
- Recent emails with subjects, senders, status
- Failed email processing attempts
- Emails with attachments

### Tasks & Actions
- All tasks created from emails
- Task priorities and due dates
- Task creation timestamps
- Task status (pending, completed, etc.)

### Deadlines & Events
- Upcoming deadlines extracted from emails
- Deadline confidence scores
- Associated email context
- Calendar events scheduled

### Agent Performance
- Execution counts per agent type
- Average execution times
- Confidence scores
- Model usage statistics

### System Health
- Dolphin server connection status
- NATS message broker status
- Active chat sessions
- Total messages processed

### High-Risk Items
- Failed executions with error messages
- High-priority tasks
- Overdue deadlines
- System anomalies

## Example Conversations

### 1. Daily Summary
```
User: "Give me a summary of today's email activity"