# AUBS Chat - Operational Awareness Assistant

## Overview

AUBS Chat provides an intelligent conversational interface with **complete operational awareness** of your email processing system. Ask questions, get insights, and monitor operations through natural language.

## Quick Start

### 1. Set Environment Variable

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Start AUBS

```bash
cd C:\Users\John\ohhhmail\aubs
python -m src.main
```

### 3. Test the Chat

```bash
# Run integration tests
python test_chat.py

# Or test manually
curl -X POST http://localhost:8000/api/chat/sessions
```

## What Can You Ask?

### System Status
```
"What's the current system status?"
"Is everything running okay?"
"How are the agents performing?"
```

### Email Processing
```
"What emails did we process today?"
"Show me recent emails from Sysco Foods"
"What happened with the fire inspection email?"
```

### Tasks & Deadlines
```
"What tasks need attention?"
"Show me high-priority tasks"
"What deadlines are coming up?"
```

### Failures & Issues
```
"Show me failed executions"
"What errors occurred today?"
"Are there any high-risk items?"
```

### Historical Patterns
```
"Do we have patterns with vendor emails?"
"What's our average processing time?"
"Show me agent performance trends"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, get response |
| `/api/chat/history/{session_id}` | GET | Get conversation history |
| `/api/chat/sessions` | GET | List all sessions |
| `/api/chat/sessions` | POST | Create new session |
| `/api/chat/sessions/{session_id}` | DELETE | Delete session |
| `/api/chat/context` | GET | Get operational context |
| `/ws/chat/{session_id}` | WS | WebSocket streaming |

## Files

### Implementation
- **`src/chat.py`** - Core chat service (850+ lines)
- **`src/main.py`** - FastAPI endpoints (updated)

### Documentation
- **`CHAT_API.md`** - Complete API reference
- **`CHAT_EXAMPLES.md`** - 8 realistic conversation examples
- **`CHAT_SETUP.md`** - Setup, testing, production guide
- **`CHAT_SUMMARY.md`** - Implementation overview

### Testing
- **`test_chat.py`** - Integration test suite

## Example Usage

### Python

```python
import httpx

# Create session
session = httpx.post("http://localhost:8000/api/chat/sessions").json()
session_id = session["id"]

# Send message
response = httpx.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "What emails did we process today?",
        "session_id": session_id
    }
).json()

print(response["message"])
```

### cURL

```bash
# Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/chat/sessions | jq -r '.id')

# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What tasks need attention?\",
    \"session_id\": \"$SESSION_ID\"
  }" | jq
```

### JavaScript (Streaming)

```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Show me system health',
    session_id: sessionId,
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  console.log(chunk);
}
```

## What the Assistant Knows

### Real-time Data
- All processed emails
- Current task status
- Recent agent outputs
- System health metrics
- Active executions
- Failed processes

### Historical Context (30 days)
- Email processing patterns
- Vendor reliability scores
- Task completion rates
- Agent performance trends
- Common failure modes

### Operational Metrics
- Total emails processed
- Success/failure rates
- Average processing times
- Agent confidence scores
- System uptime

## Features

✅ **Complete Operational Awareness**
- Every email, task, deadline, action

✅ **Multiple Response Modes**
- Non-streaming (fast, complete)
- HTTP streaming (Server-Sent Events)
- WebSocket (real-time bidirectional)

✅ **Intelligent Context**
- Dynamic system prompts
- Recent activity summaries
- Performance metrics
- High-risk item identification

✅ **Session Management**
- Persistent conversations
- History tracking
- Multi-user support

✅ **Production Ready**
- Structured logging
- Error handling
- Health checks
- Graceful shutdown

## Testing

### Run Full Test Suite

```bash
python test_chat.py
```

Expected output:
```
============================================================
AUBS Chat Integration Tests
============================================================

1. Testing health endpoint...
   ✓ Health check passed
   ✓ Chat service active: True
   ✓ Dolphin connected: True
   ✓ NATS connected: True

2. Testing session creation...
   ✓ Session created: abc-123-def-456
   ✓ User ID: default
   ✓ Message count: 0

3. Testing operational context...
   ✓ Operational context retrieved
   ✓ Total emails processed: 145
   ✓ Emails today: 12
   ✓ Active executions: 2
   ✓ Tasks created: 48
   ✓ High-risk items: 2

4. Testing non-streaming chat...
   ✓ Chat response received
   ✓ Session ID: abc-123-def-456
   ✓ Response length: 543 chars

   Response preview:
   The system is currently healthy and operational. Here's the current status:

   **System Health:**
   - AUBS Orchestrator: Running
   - Dolphin Server: Connected...

5. Testing streaming chat...
   ✓ Streaming started
   ✓ Response chunks: ..................
   ✓ Streaming complete
   ✓ Total chunks: 87
   ✓ Total length: 412 chars

6. Testing chat history...
   ✓ History retrieved
   ✓ Message count: 4
   ✓ Message 1: [user] What's the current system status?...
   ✓ Message 2: [assistant] The system is currently healthy and opera...
   ✓ Message 3: [user] Give me a brief summary...
   ✓ Message 4: [assistant] Here's a brief summary of current operati...

7. Testing session listing...
   ✓ Sessions retrieved
   ✓ Session count: 1
   ✓ Session: abc-123-def-456 (4 messages)

8. Testing session deletion...
   ✓ Session deleted: abc-123-def-456

============================================================
Test Summary
============================================================
✓ PASS: Health Check
✓ PASS: Create Session
✓ PASS: Operational Context
✓ PASS: Non-Streaming Chat
✓ PASS: Streaming Chat
✓ PASS: Chat History
✓ PASS: List Sessions
✓ PASS: Delete Session
============================================================
Results: 8/8 tests passed
============================================================
```

### Manual Testing

```bash
# 1. Create session
curl -X POST http://localhost:8000/api/chat/sessions

# 2. Get context
curl http://localhost:8000/api/chat/context | jq

# 3. Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the system status?"}' | jq
```

## Architecture

```
┌──────────────┐
│   Client     │
│   (User)     │
└──────┬───────┘
       │ HTTP/WebSocket
       ▼
┌──────────────────────┐
│   FastAPI Router     │
│   /api/chat/*        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐      ┌─────────────────┐
│  AUBSChatService     │─────▶│  Anthropic API  │
│  - Context building  │      │  Claude Sonnet 4│
│  - Session mgmt      │      └─────────────────┘
│  - Streaming         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐      ┌─────────────────┐
│  AUBSOrchestrator    │─────▶│  Executions DB  │
│  - Email processing  │      │  - Emails       │
│  - Agent outputs     │      │  - Tasks        │
│  - Actions           │      │  - Deadlines    │
└──────────────────────┘      │  - Agents       │
                              └─────────────────┘
```

## Cost Estimation

### Anthropic API Pricing
- Claude Sonnet 4: ~$3/1M input tokens, ~$15/1M output tokens
- Average chat: ~2,000 tokens (input + output)
- Cost per chat: ~$0.036

### Monthly Estimates
| Usage | Daily Cost | Monthly Cost |
|-------|-----------|--------------|
| 100 chats/day | $3.60 | $108 |
| 500 chats/day | $18.00 | $540 |
| 1,000 chats/day | $36.00 | $1,080 |

### Cost Optimization
- Cache common queries (50% reduction)
- Limit conversation history (30% reduction)
- Compress context (20% reduction)
- **Total potential savings: ~60-70%**

## Production Deployment

### 1. Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional
CHAT_MODEL=claude-sonnet-4-20250514
MAX_CONVERSATION_HISTORY=10
CONTEXT_CACHE_TTL=300
```

### 2. Database Migration

Switch from in-memory to PostgreSQL:

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL,
    message_count INTEGER DEFAULT 0,
    metadata JSONB
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_messages_session_id ON chat_messages(session_id);
```

### 3. Add Authentication

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Validate token
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return get_user_from_token(token)

@app.post("/api/chat")
async def chat(request: ChatRequest, user = Depends(verify_token)):
    # Process chat with authenticated user
    ...
```

### 4. Add Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/chat", dependencies=[
    Depends(RateLimiter(times=10, seconds=60))
])
async def chat(request: ChatRequest):
    # Rate limited to 10 requests per minute
    ...
```

### 5. Monitoring

```python
from prometheus_client import Counter, Histogram

CHAT_REQUESTS = Counter("chat_requests_total", "Total chat requests")
CHAT_DURATION = Histogram("chat_duration_seconds", "Chat duration")
CHAT_TOKENS = Histogram("chat_tokens_total", "Tokens per chat")

@CHAT_DURATION.time()
async def chat(...):
    CHAT_REQUESTS.inc()
    ...
```

## Troubleshooting

### Chat service not available
```bash
# Check health
curl http://localhost:8000/health

# Verify ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY

# Check logs
tail -f logs/aubs.log | grep -i chat
```

### Slow responses
```bash
# Use streaming for better UX
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "...", "stream": true}'

# Check Anthropic API status
curl https://status.anthropic.com
```

### Context incomplete
```bash
# Verify orchestrator has data
curl http://localhost:8000/api/chat/context | jq

# Check executions
curl http://localhost:8000/executions | jq
```

## Documentation

- **[CHAT_API.md](CHAT_API.md)** - Complete API reference
- **[CHAT_EXAMPLES.md](CHAT_EXAMPLES.md)** - 8 realistic conversation examples
- **[CHAT_SETUP.md](CHAT_SETUP.md)** - Setup, testing, production guide
- **[CHAT_SUMMARY.md](CHAT_SUMMARY.md)** - Implementation overview

## Support

For questions or issues:
1. Check the documentation files above
2. Review the integration tests in `test_chat.py`
3. Examine logs for errors
4. Verify Anthropic API key and connectivity

## License

Same as AUBS project

---

**Built with Claude Sonnet 4 for complete operational awareness.**
