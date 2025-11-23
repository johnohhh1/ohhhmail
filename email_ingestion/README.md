# Email Ingestion Service

A production-ready email ingestion service that connects to Gmail via IMAP, parses emails, extracts attachments, and forwards data to AUBS (Anthropic Universal Backend Service).

## Features

- **Gmail IMAP Integration**: Secure connection to Gmail with SSL/TLS
- **Email Parsing**: Complete MIME email parsing with header decoding
- **Attachment Handling**: Extract and save attachments with deduplication
- **AUBS Integration**: POST processed emails to AUBS API
- **Async Processing**: Non-blocking async operations for high performance
- **Error Handling**: Comprehensive error handling with retry logic
- **Type Safety**: Full type hints and Pydantic validation
- **FastAPI REST API**: HTTP endpoints for manual triggers and monitoring
- **Docker Support**: Containerized deployment with docker-compose
- **Continuous Processing**: Background polling with configurable intervals

## Architecture

```
email_ingestion/
├── __init__.py              # Package initialization
├── config.py                # Pydantic configuration
├── gmail_client.py          # IMAP client implementation
├── email_parser.py          # MIME email parser
├── attachment_handler.py    # Attachment storage manager
├── processor.py             # Main orchestrator
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker build configuration
└── docker-compose.yml      # Docker Compose setup
```

## Installation

### Local Development

1. **Clone the repository**:
```bash
cd C:\Users\John\ohhhmail\email_ingestion
```

2. **Create virtual environment**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the service**:
```bash
python -m uvicorn email_ingestion.main:app --reload
```

### Docker Deployment

1. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. **Build and run**:
```bash
docker-compose up -d
```

3. **View logs**:
```bash
docker-compose logs -f email-ingestion
```

## Configuration

All configuration is managed through environment variables (`.env` file):

### Gmail IMAP Settings

- `GMAIL_EMAIL`: Your Gmail address
- `GMAIL_PASSWORD`: App-specific password (not your regular password!)
- `IMAP_HOST`: IMAP server (default: `imap.gmail.com`)
- `IMAP_PORT`: IMAP port (default: `993`)
- `IMAP_TIMEOUT`: Connection timeout in seconds (default: `30`)

### Email Processing

- `INBOX_FOLDER`: IMAP folder to monitor (default: `INBOX`)
- `MARK_AS_READ`: Mark processed emails as read (default: `true`)
- `BATCH_SIZE`: Emails to process per batch (default: `50`)
- `MAX_ATTACHMENT_SIZE_MB`: Maximum attachment size (default: `25`)

### AUBS Integration

- `AUBS_API_URL`: AUBS API endpoint URL
- `AUBS_API_KEY`: Optional API key for authentication
- `AUBS_TIMEOUT`: API request timeout (default: `60`)

### Service Settings

- `POLL_INTERVAL_SECONDS`: Polling interval (default: `60`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `ENABLE_SSL`: Use SSL for IMAP (default: `true`)

### Performance

- `MAX_WORKERS`: Concurrent workers (default: `5`)
- `RETRY_ATTEMPTS`: Retry attempts (default: `3`)
- `RETRY_DELAY_SECONDS`: Delay between retries (default: `5`)

## Gmail Setup

### Enable IMAP

1. Open Gmail settings
2. Go to "Forwarding and POP/IMAP"
3. Enable IMAP
4. Save changes

### Create App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to "App passwords"
4. Select "Mail" and your device
5. Copy the generated password
6. Use this as `GMAIL_PASSWORD` in `.env`

## API Endpoints

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "email-ingestion",
  "version": "1.0.0",
  "settings": {
    "gmail_email": "your-email@gmail.com",
    "imap_host": "imap.gmail.com",
    "poll_interval_seconds": 60
  }
}
```

### POST /process

Manually trigger email processing.

**Response**:
```json
{
  "status": "success",
  "message": "Email processing completed",
  "stats": {
    "fetched": 10,
    "processed": 10,
    "failed": 0,
    "sent_to_aubs": 10
  }
}
```

### GET /stats

Get attachment storage statistics.

**Response**:
```json
{
  "status": "success",
  "stats": {
    "total_files": 42,
    "total_size_bytes": 15728640,
    "total_size_mb": 15.0,
    "storage_path": "/app/attachments"
  }
}
```

### POST /cleanup

Cleanup empty directories in attachment storage.

**Response**:
```json
{
  "status": "success",
  "message": "Cleaned up 5 empty directories"
}
```

## Usage Examples

### Manual Processing

```bash
curl -X POST http://localhost:8000/process
```

### Check Health

```bash
curl http://localhost:8000/health
```

### Get Statistics

```bash
curl http://localhost:8000/stats
```

### Cleanup Storage

```bash
curl -X POST http://localhost:8000/cleanup
```

## Data Flow

1. **Fetch**: Connect to Gmail IMAP and fetch unread emails
2. **Parse**: Parse MIME emails and extract metadata
3. **Extract**: Save attachments to local storage
4. **Transform**: Convert to AUBS-compatible format
5. **Send**: POST processed data to AUBS API
6. **Mark**: Mark emails as read (if configured)

## Error Handling

- **IMAP Errors**: Automatic reconnection with exponential backoff
- **Parsing Errors**: Skip invalid emails and log errors
- **Attachment Errors**: Continue processing other attachments
- **AUBS Errors**: Retry with configurable attempts and delays
- **Global Errors**: Catch-all exception handler with logging

## Monitoring

### Logs

Logs are written to stdout and can be configured with `LOG_LEVEL`:

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Health Checks

Docker health checks run every 30 seconds:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Security

### Best Practices

1. **Use App Passwords**: Never use your main Gmail password
2. **Enable SSL**: Always use SSL for IMAP connections
3. **Secure API Keys**: Store AUBS API keys in environment variables
4. **Validate Input**: All email content is validated and sanitized
5. **Limit Attachment Size**: Configure max attachment size to prevent abuse

### Secrets Management

- Never commit `.env` files to version control
- Use Docker secrets for production deployments
- Rotate API keys and passwords regularly

## Performance

### Optimization Tips

1. **Batch Size**: Adjust `BATCH_SIZE` based on email volume
2. **Poll Interval**: Increase `POLL_INTERVAL_SECONDS` for lower volume
3. **Max Workers**: Tune `MAX_WORKERS` based on CPU cores
4. **Attachment Storage**: Use fast SSD for attachment storage
5. **Network**: Ensure low-latency connection to IMAP and AUBS

### Scaling

- **Horizontal**: Run multiple instances with different folders
- **Vertical**: Increase CPU/memory for higher throughput
- **Storage**: Use network storage for shared attachments

## Troubleshooting

### IMAP Connection Issues

```python
# Check IMAP connectivity
telnet imap.gmail.com 993
```

### Authentication Failures

- Verify app password is correct
- Check 2-Step Verification is enabled
- Ensure IMAP is enabled in Gmail settings

### Attachment Not Saving

- Check `ATTACHMENT_STORAGE_PATH` permissions
- Verify disk space is available
- Check `MAX_ATTACHMENT_SIZE_MB` limit

### AUBS Connection Failures

- Verify `AUBS_API_URL` is correct
- Check `AUBS_API_KEY` if required
- Test connectivity: `curl $AUBS_API_URL/health`

## Development

### Running Tests

```bash
pytest tests/ -v --cov=email_ingestion
```

### Code Quality

```bash
# Format code
black email_ingestion/

# Sort imports
isort email_ingestion/

# Type checking
mypy email_ingestion/

# Linting
flake8 email_ingestion/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@ohhhmail.com
- Documentation: [Full docs]
