# AUBS - Autonomous Unified Business System

Central orchestration service for ChiliHead OpsManager v2.1 email processing.

## Overview

AUBS orchestrates email processing through Dolphin DAG execution, coordinating multiple AI agents and routing actions to MCP tools.

## Architecture

```
Email Input → AUBS Orchestrator → Dolphin DAG → AI Agents → Action Router → MCP Tools
                                                                            ↓
                                                                      UI-TARS Review
```

## Components

### Main Application (`src/main.py`)
- FastAPI application
- Health check endpoints
- Email processing API
- Execution status tracking
- Prometheus metrics

### Orchestrator (`src/orchestrator.py`)
- Email processing coordination
- DAG submission to Dolphin
- Execution monitoring
- Action routing
- NATS event publishing

### DAG Builder (`src/dag_builder.py`)
- Dynamic task graph construction
- Conditional agent inclusion
- XCom data passing configuration
- Vision agent only included if attachments present

### Action Router (`src/action_router.py`)
- Routes actions to MCP tools
- Confidence threshold checking
- High-risk detection
- Human review queue integration

### Configuration (`src/config.py`)
- Environment-based settings
- Agent configurations
- LLM provider settings
- Validation logic

## API Endpoints

### Health & Status
```bash
GET /health              # Health check
GET /ready               # Readiness check
GET /metrics             # Prometheus metrics
GET /config              # Current configuration
```

### Email Processing
```bash
POST /process-email      # Submit email for processing
GET /executions/{id}     # Get execution status
GET /executions          # List executions
```

## Configuration

### Environment Variables

**Service Configuration:**
- `ENVIRONMENT` - Environment name (development/production)
- `LOG_LEVEL` - Logging level (INFO/DEBUG/WARNING/ERROR)

**External Services:**
- `DOLPHIN_URL` - Dolphin server URL (default: http://dolphin-server:12345)
- `UI_TARS_URL` - UI-TARS service URL (default: http://uitars:8080)
- `NATS_URL` - NATS server URL (default: nats://nats:4222)
- `SUPABASE_URL` - Supabase URL
- `SUPABASE_KEY` - Supabase API key

**Orchestration Settings:**
- `CONFIDENCE_THRESHOLD` - Minimum confidence for automated actions (0.0-1.0, default: 0.9)
- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `EXECUTION_TIMEOUT` - Maximum execution time in seconds (default: 300)

**Agent Configuration:**
For each agent (triage, vision, deadline, task, context):
- `{AGENT}_AGENT_PROVIDER` - LLM provider (openai/anthropic/ollama)
- `{AGENT}_AGENT_MODEL` - Model name
- `{AGENT}_AGENT_TIMEOUT` - Timeout in seconds
- `{AGENT}_AGENT_GPU` - GPU required (true/false)
- `{AGENT}_AGENT_FALLBACK` - Fallback provider:model or DISABLED

**MCP Tool Settings:**
- `MCP_TODOIST_ENABLED` - Enable Todoist integration (default: true)
- `MCP_GCAL_ENABLED` - Enable Google Calendar integration (default: true)
- `MCP_TWILIO_ENABLED` - Enable Twilio integration (default: true)

**High-Risk Detection:**
- `HIGH_RISK_KEYWORDS` - Comma-separated keywords (default: fire,lawsuit,inspection,deadline,urgent,overdue)

## Example Usage

### Submit Email for Processing
```bash
curl -X POST http://localhost:8000/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Vendor Invoice Due Tomorrow",
    "sender": "vendor@example.com",
    "recipient": "manager@restaurant.com",
    "body": "Invoice #1234 for $500 due by 2024-02-15",
    "attachments": [
      {
        "filename": "invoice.pdf",
        "content_type": "application/pdf",
        "size": 52000,
        "url": "https://storage/invoice.pdf"
      }
    ]
  }'
```

Response:
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "email_id": "email_123",
  "status": "running",
  "message": "Email processing started",
  "started_at": "2024-02-14T10:30:00Z"
}
```

### Check Execution Status
```bash
curl http://localhost:8000/executions/123e4567-e89b-12d3-a456-426614174000
```

Response:
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "email_id": "email_123",
  "status": "completed",
  "started_at": "2024-02-14T10:30:00Z",
  "completed_at": "2024-02-14T10:32:15Z",
  "agent_outputs": [
    {
      "agent_type": "triage",
      "confidence": 0.95,
      "execution_time_ms": 1200
    },
    {
      "agent_type": "vision",
      "confidence": 0.92,
      "execution_time_ms": 2500
    }
  ],
  "actions": [
    {
      "id": "action_123",
      "action_type": "create_task",
      "status": "completed",
      "confidence": 0.94
    }
  ]
}
```

## DAG Workflow

### With Attachments (Vision Included)
```
[Triage Agent]
      |
      +-------+-------+
      |       |       |
[Vision] [Deadline] [Task]
      |       |       |
      +-------+-------+
              |
      [Context Agent]
              |
          [Actions]
```

### Without Attachments (No Vision)
```
[Triage Agent]
      |
      +-------+
      |       |
[Deadline] [Task]
      |       |
      +-------+
          |
  [Context Agent]
          |
      [Actions]
```

## Agent Pipeline

1. **Triage Agent** (Always)
   - Categorizes email
   - Determines urgency
   - Identifies if vision/deadlines needed

2. **Vision Agent** (Conditional)
   - Only runs if attachments present
   - Processes PDFs, images
   - Extracts invoice data

3. **Deadline Scanner** (Always)
   - Extracts dates and deadlines
   - Identifies recurring events
   - Parses temporal expressions

4. **Task Categorizer** (Conditional)
   - Runs if triage indicates tasks
   - Extracts action items
   - Assigns priorities

5. **Context Agent** (CRITICAL - Always)
   - Synthesizes all agent outputs
   - Provides recommendations
   - Risk assessment
   - NO FALLBACK ALLOWED

## Action Routing

Actions are routed based on confidence and risk:

### High Confidence (≥ 0.9) + Low Risk
→ Automatic execution via MCP tools

### Low Confidence (< 0.9)
→ Human review queue via UI-TARS

### High Risk Detection
Keywords: fire, lawsuit, inspection, deadline, urgent, overdue
→ Automatic human review queue

## Monitoring

### Prometheus Metrics
- `aubs_emails_processed_total{status}` - Total emails processed
- `aubs_processing_duration_seconds` - Processing duration histogram
- `aubs_agent_executions_total{agent_type,status}` - Agent executions
- `aubs_actions_created_total{action_type}` - Actions created

### Health Checks
- `/health` - Service health
- `/ready` - Kubernetes readiness probe

### Structured Logging
All logs output in JSON format with structured fields:
- `timestamp` - ISO 8601 timestamp
- `level` - Log level
- `logger` - Logger name
- `execution_id` - Execution tracking ID
- `email_id` - Email identifier
- Additional context fields

## Docker Deployment

### Build
```bash
docker build -t aubs:latest -f Dockerfile .
```

### Run Development
```bash
docker run -p 8000:8000 \
  --env-file .env \
  --target development \
  aubs:latest
```

### Run Production
```bash
docker run -p 8000:8000 \
  --env-file .env \
  --target production \
  aubs:latest
```

## Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests
```bash
pytest tests/ -v
```

## Integration Points

### Upstream
- Gmail webhook → Email input

### Downstream
- Dolphin server → DAG execution
- Agent services → AI processing
- MCP tools → Action execution
- UI-TARS → Human review
- NATS → Event streaming
- Supabase → Data persistence

## Error Handling

- Automatic retries with exponential backoff
- Agent failures trigger fallback models (except context agent)
- Execution timeout protection
- Graceful degradation
- Human review escalation

## Security

- No secrets in logs
- API key validation
- Rate limiting (TODO)
- Request validation via Pydantic
- CORS configuration
- Non-root Docker user

## Future Enhancements

- [ ] Supabase persistence for executions
- [ ] Redis caching layer
- [ ] Rate limiting middleware
- [ ] WebSocket execution streaming
- [ ] Advanced metrics and alerting
- [ ] Multi-tenant support
- [ ] Historical context integration
- [ ] A/B testing for agent configurations

## License

Proprietary - ChiliHead OpsManager v2.1
