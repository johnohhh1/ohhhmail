# AUBS Chat - Setup Guide

## Prerequisites

1. **Anthropic API Key** - Required for Claude Sonnet 4
2. **Running AUBS Orchestrator** - Chat service requires orchestrator
3. **Python Dependencies** - Install required packages

## Installation

### 1. Install Dependencies

Add to your `requirements.txt`:
```
anthropic>=0.18.0
httpx>=0.26.0
```

Install:
```bash
pip install anthropic httpx
```

### 2. Set Environment Variables

Add to your `.env` file:
```bash
# Anthropic API Key for Chat
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Override default model
CHAT_MODEL=claude-sonnet-4-20250514
```

### 3. Verify Setup

The chat service is automatically initialized with the orchestrator. Check health:

```bash
curl http://localhost:8000/health
```

Response should include:
```json
{
  "status": "healthy",
  "chat_service_active": true,
  ...
}
```

## Quick Start

### 1. Create a Chat Session

```bash
curl -X POST http://localhost:8000/api/chat/sessions
```

Response:
```json
{
  "id": "abc-123-def-456",
  "user_id": "default",
  "started_at": "2025-01-15T10:00:00Z",
  "message_count": 0
}
```

### 2. Send a Message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What emails did we process today?",
    "session_id": "abc-123-def-456"
  }'
```

### 3. Get Chat History

```bash
curl http://localhost:8000/api/chat/history/abc-123-def-456
```

## Testing

### Test Non-Streaming Chat

```python
import httpx

# Create session
session_response = httpx.post("http://localhost:8000/api/chat/sessions")
session_id = session_response.json()["id"]

# Send message
response = httpx.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Show me a summary of today's activity",
        "session_id": session_id,
        "stream": False
    }
)

print(response.json()["message"])
```

### Test Streaming Chat

```python
import httpx

session_id = "your-session-id"

with httpx.stream(
    "POST",
    "http://localhost:8000/api/chat",
    json={
        "message": "What are the high-priority tasks?",
        "session_id": session_id,
        "stream": True
    }
) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            print(line[6:], end="", flush=True)
    print()
```

### Test WebSocket

```python
import asyncio
import websockets
import json

async def test_websocket():
    session_id = "your-session-id"
    uri = f"ws://localhost:8000/ws/chat/{session_id}"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "message": "What's the system status?"
        }))

        # Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "complete":
                print("\n\nComplete!")
                break
            elif data["type"] == "error":
                print(f"\nError: {data['message']}")
                break

asyncio.run(test_websocket())
```

## Operational Context

The chat assistant has access to:

### Real-time Data
- All processed emails
- Current task status
- Recent agent outputs
- System health metrics
- Active executions

### Historical Context (30 days)
- Email processing patterns
- Vendor reliability scores
- Task completion rates
- Agent performance trends
- Common failure modes

### The assistant can answer questions like:
- "What emails did we process today?"
- "Show me failed executions"
- "What tasks are due this week?"
- "How are the agents performing?"
- "What happened with the fire inspection email?"
- "Do we have patterns with vendor emails?"
- "Is everything running okay?"
- "Anything I should know about?"

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       ▼
┌─────────────────┐
│  FastAPI        │
│  /api/chat      │
└────────┬────────┘
         │
         ▼
┌──────────────────┐      ┌─────────────────┐
│  AUBSChatService │─────▶│  Claude API     │
│                  │      │  (Sonnet 4)     │
└────────┬─────────┘      └─────────────────┘
         │
         │ Operational Context
         ▼
┌──────────────────┐      ┌─────────────────┐
│  AUBSOrchestrator│─────▶│  Executions     │
│                  │      │  Agent Outputs  │
└──────────────────┘      │  Actions        │
                          │  Metadata       │
                          └─────────────────┘
```

## Session Management

### In-Memory (Current)
- Sessions stored in memory
- Lost on restart
- Fast access
- Development use

### PostgreSQL (Production - Recommended)

To enable PostgreSQL persistence, update `chat.py`:

```python
class AUBSChatService:
    def __init__(self, settings: AUBSSettings, orchestrator):
        self.settings = settings
        self.orchestrator = orchestrator
        self.anthropic = AsyncAnthropic()

        # PostgreSQL connection
        self.db_pool = None  # Initialize connection pool

    async def initialize(self):
        # Initialize PostgreSQL
        self.db_pool = await asyncpg.create_pool(
            settings.supabase_url,
            min_size=5,
            max_size=20
        )

        # Create tables if needed
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    metadata JSONB
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY,
                    session_id UUID REFERENCES chat_sessions(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata JSONB
                )
            """)
```

## Monitoring

### Check Active Sessions

```bash
curl http://localhost:8000/api/chat/sessions
```

### Check Operational Context

```bash
curl http://localhost:8000/api/chat/context
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Chat service not available
- Verify `ANTHROPIC_API_KEY` is set
- Check orchestrator is running
- Review logs for initialization errors

### Slow responses
- Check Anthropic API status
- Verify network connectivity
- Consider using streaming for better UX

### Context seems incomplete
- Verify orchestrator has processed emails
- Check execution data is being stored
- Review Context Agent integration

### WebSocket connection fails
- Check firewall settings
- Verify WebSocket support in proxy/load balancer
- Test with direct connection first

## Production Considerations

### 1. Database Persistence
- Implement PostgreSQL for session/message storage
- Add indexes on session_id and user_id
- Set up regular backups

### 2. Rate Limiting
- Implement rate limits on chat endpoints
- Use Redis for distributed rate limiting
- Set per-user quotas

### 3. Caching
- Cache operational context (5-minute TTL)
- Cache agent performance stats (15-minute TTL)
- Use Redis for distributed caching

### 4. Security
- Implement proper authentication
- Add API key validation
- Use HTTPS in production
- Validate and sanitize user input

### 5. Monitoring
- Track chat response times
- Monitor Anthropic API usage
- Alert on high error rates
- Log all interactions (GDPR compliant)

### 6. Scaling
- Run multiple chat service instances
- Use load balancer for distribution
- Consider message queue for high volume
- Implement circuit breakers for Claude API

## Cost Optimization

### Anthropic API Costs
- Claude Sonnet 4: ~$3/million input tokens, ~$15/million output tokens
- Average chat: ~2,000 tokens (input + output)
- Estimated cost: ~$0.036 per chat interaction

### Optimization Strategies
1. **Cache common queries** - Same questions get same context
2. **Limit conversation history** - Only last 10 messages
3. **Compress operational context** - Send summaries not full data
4. **Use streaming** - Better UX, same cost
5. **Implement quotas** - Per-user daily limits

### Example Monthly Costs (1000 chats/day)
- Daily: 1000 chats × $0.036 = $36
- Monthly: $36 × 30 = $1,080

Reduce by 50% with caching: ~$540/month

## Next Steps

1. Test the chat endpoints
2. Try example conversations
3. Integrate with your frontend
4. Set up monitoring
5. Plan for production deployment

For more examples, see [CHAT_EXAMPLES.md](CHAT_EXAMPLES.md)
For API reference, see [CHAT_API.md](CHAT_API.md)
