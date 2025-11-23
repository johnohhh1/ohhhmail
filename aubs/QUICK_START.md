# AUBS Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- API keys for LLM providers (OpenAI, Anthropic)
- NATS server running (or use docker-compose)

## Quick Start with Docker Compose

### 1. Configure Environment

```bash
cd C:\Users\John\ohhhmail\aubs
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Start Services

```bash
docker-compose up
```

This starts:
- AUBS service on http://localhost:8000
- NATS server on nats://localhost:4222

### 3. Test Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "aubs",
  "version": "2.1.0",
  "timestamp": "2024-02-14T10:30:00Z",
  "dolphin_connected": false,
  "nats_connected": true
}
```

### 4. Submit Test Email

```bash
curl -X POST http://localhost:8000/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Email",
    "sender": "test@example.com",
    "recipient": "manager@restaurant.com",
    "body": "This is a test email with a deadline tomorrow.",
    "attachments": []
  }'
```

Expected response:
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "email_id": "...",
  "status": "running",
  "message": "Email processing started",
  "started_at": "2024-02-14T10:30:00Z"
}
```

### 5. Check Execution Status

```bash
curl http://localhost:8000/executions/123e4567-e89b-12d3-a456-426614174000
```

### 6. View Metrics

```bash
curl http://localhost:8000/metrics
```

## Local Development (without Docker)

### 1. Install Dependencies

```bash
cd C:\Users\John\ohhhmail\aubs
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Locally

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Tests

```bash
pytest tests/ -v
```

## Production Deployment

### 1. Build Production Image

```bash
docker build -t aubs:latest --target production .
```

### 2. Run Production Container

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name aubs \
  aubs:latest
```

### 3. View Logs

```bash
docker logs -f aubs
```

## Integration with Full System

### 1. Ensure Dependencies Running

Required services:
- Dolphin server (http://dolphin-server:12345)
- Agent services (http://agents:800X)
- UI-TARS (http://uitars:8080)
- NATS (nats://nats:4222)
- Supabase (http://supabase:8000)

### 2. Configure Service URLs

In `.env`:
```bash
DOLPHIN_URL=http://dolphin-server:12345
UI_TARS_URL=http://uitars:8080
NATS_URL=nats://nats:4222
SUPABASE_URL=http://supabase:8000
```

### 3. Start Complete Stack

```bash
cd C:\Users\John\ohhhmail
docker-compose up
```

## Common Issues

### Dolphin Not Connected

**Symptom**: `dolphin_connected: false` in health check

**Solution**:
1. Ensure Dolphin server is running
2. Check `DOLPHIN_URL` in `.env`
3. Verify network connectivity

```bash
curl http://dolphin-server:12345/health
```

### NATS Connection Failed

**Symptom**: `nats_connected: false` in health check

**Solution**:
1. Ensure NATS server is running
2. Check `NATS_URL` in `.env`
3. Verify NATS is accessible

```bash
docker logs nats
```

### Agent Timeout

**Symptom**: Execution fails with timeout error

**Solution**:
1. Increase `{AGENT}_AGENT_TIMEOUT` in `.env`
2. Check agent service logs
3. Verify LLM provider availability

### Low Confidence Actions

**Symptom**: All actions going to human review

**Solution**:
1. Lower `CONFIDENCE_THRESHOLD` in `.env` (carefully!)
2. Check context agent output quality
3. Verify agent configurations

## API Examples

### Process Email with Attachment

```bash
curl -X POST http://localhost:8000/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Invoice #1234",
    "sender": "vendor@example.com",
    "recipient": "accounts@restaurant.com",
    "body": "Please find attached invoice #1234 for $500. Due by 2024-02-15.",
    "attachments": [
      {
        "filename": "invoice.pdf",
        "content_type": "application/pdf",
        "size": 52000,
        "url": "https://storage.example.com/invoice.pdf"
      }
    ]
  }'
```

### List Recent Executions

```bash
curl "http://localhost:8000/executions?limit=10"
```

### Filter by Status

```bash
curl "http://localhost:8000/executions?status_filter=completed&limit=20"
```

### Get Configuration

```bash
curl http://localhost:8000/config
```

## Monitoring

### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'aubs'
    static_configs:
      - targets: ['aubs:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import metrics:
- `aubs_emails_processed_total`
- `aubs_processing_duration_seconds`
- `aubs_agent_executions_total`
- `aubs_actions_created_total`

## Debugging

### Enable Debug Logging

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart service:
```bash
docker-compose restart aubs
```

### View Structured Logs

```bash
docker logs aubs | jq .
```

### Check Agent Configuration

```bash
curl http://localhost:8000/config | jq .agents
```

## Performance Tuning

### Increase Workers (Production)

Modify Dockerfile CMD:
```dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

### Adjust Timeouts

In `.env`:
```bash
EXECUTION_TIMEOUT=600  # 10 minutes
TRIAGE_AGENT_TIMEOUT=30
CONTEXT_AGENT_TIMEOUT=60
```

### Optimize Polling Interval

In `src/orchestrator.py`:
```python
poll_interval = 2  # Check every 2 seconds instead of 5
```

## Next Steps

1. **Connect to Dolphin**: Ensure Dolphin server is running
2. **Deploy Agents**: Start AI agent services
3. **Configure MCP Tools**: Set up Todoist, Google Calendar, Twilio
4. **Test End-to-End**: Process real email through full pipeline
5. **Monitor Performance**: Set up Grafana dashboards
6. **Scale as Needed**: Add workers, optimize timeouts

## Support

For issues or questions:
1. Check logs: `docker logs aubs`
2. Verify configuration: `curl http://localhost:8000/config`
3. Test health: `curl http://localhost:8000/health`
4. Review documentation: `README.md`
5. Run tests: `pytest tests/ -v`

## Summary

AUBS is now running! Key endpoints:
- Health: http://localhost:8000/health
- Process Email: http://localhost:8000/process-email
- Status: http://localhost:8000/executions/{id}
- Metrics: http://localhost:8000/metrics

Ready for email processing orchestration! 🚀
