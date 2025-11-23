# Shared Utilities - Quick Reference Examples

Quick examples for using the logging, metrics, and events utilities.

## Logging Examples

### Basic Setup and Usage
```python
from shared.utils import setup_logging, get_logger, set_request_id, RequestContext

# Setup at application start
setup_logging(level="INFO", format_type="json")  # Production
# setup_logging(level="DEBUG", format_type="pretty")  # Development

# Get logger for your module
logger = get_logger(__name__)

# Simple logging
logger.info("Application started")
logger.warning("Unusual condition detected")
logger.error("Failed to process email", exc_info=True)

# With context data
logger.bind(email_id="123", status="processing").info("Processing email")

# Request correlation ID
with RequestContext() as request_id:
    logger.info("Handling request")  # Includes request_id in log
    process_request()

# Manual request ID
set_request_id("custom-id-123")
logger.info("Custom tracking")
```

### Timed Execution Logging
```python
from shared.utils import get_logger, log_execution_time

logger = get_logger(__name__)

@log_execution_time()
def process_email(email_id: str) -> dict:
    # Processing logic
    return result

# Logs: "process_email executed in 0.234s"
process_email("email-123")
```

### File-based Logging
```python
from shared.utils import setup_logging

# Log to both console and file with rotation
setup_logging(
    level="INFO",
    format_type="json",
    log_file="/var/log/ohhhmail/app.log"  # 10MB rotation, 7 day retention
)
```

---

## Metrics Examples

### Counter Metrics
```python
from shared.utils import get_registry

registry = get_registry()

# Create counter
emails_processed = registry.counter(
    "emails_processed_total",
    "Total emails processed by system"
)

# Basic usage
emails_processed.inc()  # Increment by 1
emails_processed.inc(5)  # Increment by 5

# With labels (dimensional data)
emails_by_agent = registry.counter(
    "emails_processed_by_agent_total",
    "Emails processed by agent type",
    labels=["agent_type", "status"]
)
emails_by_agent.inc_by_labels({"agent_type": "triage", "status": "success"})
emails_by_agent.inc_by_labels({"agent_type": "context", "status": "failed"})
```

### Gauge Metrics
```python
from shared.utils import get_registry

registry = get_registry()

# Create gauge
active_executions = registry.gauge(
    "active_executions",
    "Currently running email executions"
)

# Update current value
active_executions.set(5)
active_executions.inc()  # Now 6
active_executions.dec(2)  # Now 4

# With labels
agent_load = registry.gauge(
    "agent_load",
    "Load on each agent",
    labels=["agent_type"]
)
agent_load.set_by_labels({"agent_type": "triage"}, 3.5)
agent_load.set_by_labels({"agent_type": "context"}, 7.2)
```

### Histogram Metrics
```python
from shared.utils import get_registry

registry = get_registry()

# Create histogram with custom buckets
processing_time = registry.histogram(
    "email_processing_seconds",
    "Time to process email",
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0)
)

# Record observations
processing_time.observe(0.234)  # 234ms
processing_time.observe(1.5)    # 1.5s
processing_time.observe(5.2)    # 5.2s

# Analyze
p50 = processing_time.get_percentile(50)  # Median
p95 = processing_time.get_percentile(95)  # 95th percentile
p99 = processing_time.get_percentile(99)  # 99th percentile

count_fast = processing_time.get_bucket_count(0.5)  # How many <= 0.5s
```

### Metric Decorators
```python
from shared.utils import time_operation, track_execution_time

# Track execution time automatically
@time_operation("email_parsing")
def parse_email(raw_email: str) -> dict:
    # Parsing logic
    return parsed_email

# Track both count and duration
@track_execution_time(
    counter_name="actions_executed_total",
    histogram_name="action_duration_ms"
)
def execute_action(action: dict) -> dict:
    # Action execution logic
    return result
```

### Prometheus Export
```python
from shared.utils import get_registry

registry = get_registry()

# Export in Prometheus format (for /metrics endpoint)
prometheus_text = registry.export_prometheus()
print(prometheus_text)

# Output:
# # HELP emails_processed_total Total emails processed
# # TYPE emails_processed_total counter
# emails_processed_total 42
# # HELP email_processing_seconds Time to process email
# # TYPE email_processing_seconds histogram
# email_processing_seconds_bucket{le="0.1"} 5
# email_processing_seconds_bucket{le="0.5"} 12
# email_processing_seconds_bucket{le="1.0"} 18
# ...
```

---

## Event Examples

### Publishing Events
```python
from shared.utils import EventPublisher, EventType, set_request_id

# Initialize publisher
publisher = EventPublisher(nats_client)

# Get or create request ID
request_id = set_request_id()

# Publish generic event
event = publisher.publish_event(
    event_type=EventType.EMAIL_RECEIVED,
    event_source="gmail-service",
    data={
        "email_id": "email-123",
        "subject": "Urgent: Server down",
        "sender": "ops@company.com",
        "received_at": "2024-01-15T10:30:45Z"
    },
    correlation_id=request_id
)

# Publish agent completion
event = publisher.publish_agent_event(
    agent_type="triage",
    agent_output={
        "email_id": "email-123",
        "category": "urgent",
        "confidence": 0.95,
        "findings": {
            "priority": "high",
            "requires_human_review": False
        }
    },
    correlation_id=request_id
)

# Publish action
event = publisher.publish_action_event(
    action_id="act-456",
    action_type="create_task",
    status="executed",
    result={
        "task_id": "task-789",
        "assigned_to": "john@company.com",
        "due_date": "2024-01-15T17:00:00Z"
    },
    correlation_id=request_id
)

# Publish DAG execution
event = publisher.publish_dag_event(
    dag_id="dag-workflow-123",
    status="submitted",
    metadata={
        "email_id": "email-123",
        "execution_id": "exec-456"
    },
    correlation_id=request_id
)
```

### Creating Events Directly
```python
from shared.utils import Event, EventType
from uuid import uuid4

# Direct event creation
event = Event(
    event_type=EventType.AGENT_TRIAGE_COMPLETE,
    event_source="triage-agent",
    event_data={
        "email_id": "email-123",
        "category": "vendor",
        "confidence": 0.92
    }
)

# Convert to JSON for transmission
json_str = event.to_json()

# Convert to dict
event_dict = event.to_dict()
# {"id": "550e8400-e29b-41d4...", "event_type": "agents.triage.complete", ...}

# Access fields
print(event.id)  # UUID
print(event.event_type)  # "agents.triage.complete"
print(event.timestamp)  # datetime
```

### Event Validation
```python
from shared.utils import EventSchema, EventType

schema = EventSchema()

# Validate event data against schema
is_valid, errors = schema.validate(
    EventType.EMAIL_RECEIVED,
    {
        "email_id": "email-123",
        "subject": "Test",
        "sender": "test@example.com"
    }
)

if not is_valid:
    print(f"Validation errors: {errors}")
else:
    print("Event is valid!")

# Register custom event schema
schema.register_schema(
    "custom.event.type",
    {
        "required": ["custom_id", "timestamp"],
        "optional": ["metadata", "status"]
    }
)

is_valid, errors = schema.validate(
    "custom.event.type",
    {"custom_id": "cust-123", "timestamp": "2024-01-15T10:30:45Z"}
)
```

### NATS Subscription and Processing
```python
from shared.utils import Event, EventSchema, EventPublisher, set_request_id
from nats.aio.client import Client

async def setup_nats_handler(nc: Client):
    schema = EventSchema()

    async def handle_agent_complete(msg):
        # Parse event
        event = Event.model_validate_json(msg.data)

        # Set correlation ID for logging
        set_request_id(str(event.correlation_id))

        # Validate
        is_valid, errors = schema.validate(event.event_type, event.event_data)
        if not is_valid:
            logger.error(f"Invalid event: {errors}")
            return

        # Process based on type
        if "triage" in event.event_type:
            await handle_triage_complete(event)
        elif "context" in event.event_type:
            await handle_context_complete(event)

    # Subscribe to all agent completion events
    await nc.subscribe("agents.*.complete", cb=handle_agent_complete)
```

---

## Complete Integration Example

### Agent Processing Pipeline
```python
from shared.utils import (
    setup_logging, get_logger, set_request_id, RequestContext,
    get_registry, time_operation, track_execution_time,
    EventPublisher, EventType
)
from datetime import datetime
from uuid import uuid4

# Initialize
setup_logging(level="INFO", format_type="json")
logger = get_logger(__name__)
registry = get_registry()
publisher = EventPublisher(nats_client)

# Metrics
emails_processed = registry.counter("emails_processed_total")
processing_time = registry.histogram("email_processing_ms")
active_emails = registry.gauge("active_email_processing")

@track_execution_time("triage_agent_executions")
@time_operation("triage_agent")
def run_triage_agent(email_id: str, email_body: str) -> dict:
    """Run triage agent on email."""
    active_emails.inc()

    try:
        logger.bind(email_id=email_id).info("Starting triage analysis")

        # Triage logic
        result = {
            "category": "vendor",
            "priority": "high",
            "confidence": 0.95
        }

        emails_processed.inc()
        return result

    finally:
        active_emails.dec()

# Main processing
async def process_email_workflow(email_id: str, email_body: str):
    """Complete email processing workflow."""
    # Create request context for correlation
    with RequestContext() as request_id:
        logger.info(f"Starting email processing: {email_id}")

        try:
            # Run agent
            start = time.time()
            triage_result = run_triage_agent(email_id, email_body)
            elapsed_ms = (time.time() - start) * 1000
            processing_time.observe(elapsed_ms)

            # Publish event with correlation ID
            publisher.publish_agent_event(
                agent_type="triage",
                agent_output={
                    "email_id": email_id,
                    **triage_result,
                    "execution_time_ms": int(elapsed_ms)
                },
                correlation_id=request_id
            )

            logger.info(f"Email processing complete: {email_id}")

        except Exception as e:
            logger.error(f"Failed to process email: {email_id}", exc_info=True)
            emails_processed.inc_by_labels({"status": "failed"})

            # Publish error event
            publisher.publish_event(
                event_type=EventType.SYSTEM_ERROR,
                event_source="email-processor",
                data={
                    "email_id": email_id,
                    "error": str(e)
                },
                correlation_id=request_id
            )

            raise

# Export metrics for Prometheus
def get_metrics_endpoint():
    return registry.export_prometheus()
```

---

## Common Patterns

### Pattern 1: Service with Metrics Endpoint
```python
from flask import Flask, Response
from shared.utils import get_registry

app = Flask(__name__)

@app.route("/metrics")
def metrics():
    registry = get_registry()
    return Response(
        registry.export_prometheus(),
        mimetype="text/plain"
    )

@app.route("/email", methods=["POST"])
def process_email():
    counter = registry.counter("api_requests_total")
    counter.inc()
    # Process email...
    return {"status": "success"}
```

### Pattern 2: Request Tracing Middleware
```python
from shared.utils import set_request_id, RequestContext

def request_middleware(request):
    # Extract or generate request ID
    request_id = request.headers.get("X-Request-ID")

    with RequestContext(request_id) as rid:
        # All logs in this context include the request ID
        request.request_id = rid
        return process_request()
```

### Pattern 3: Async Event Handler
```python
from shared.utils import Event, set_request_id, get_logger

async def handle_email_event(msg):
    event = Event.model_validate_json(msg.data)

    # Set context for all logs in this handler
    set_request_id(str(event.correlation_id))
    logger = get_logger(__name__)

    logger.info(f"Received event: {event.event_type}")
    # Process event...
```

### Pattern 4: Decorated Business Logic
```python
from shared.utils import track_execution_time, time_operation, get_logger

logger = get_logger(__name__)

@track_execution_time("email_classifications")
@time_operation("classification")
def classify_email(email: dict) -> str:
    logger.info("Classifying email", email_id=email["id"])
    # Classification logic
    return category
```

---

## Environment Setup

```bash
# Development
export LOG_LEVEL=DEBUG
export LOG_FORMAT=pretty

# Production
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

## Testing Tips

```python
# Test without NATS client
publisher = EventPublisher()  # No client, validation only
event = publisher.publish_event(...)
assert publisher.get_published_count() == 1

# Test logging to temp file
import tempfile
with tempfile.NamedTemporaryFile() as f:
    setup_logging(log_file=f.name)
    logger.info("test")
    assert "test" in f.read()

# Test metrics collection
registry = get_registry()
counter = registry.counter("test")
counter.inc()
assert counter.value == 1
```

---

See `SHARED_UTILS_SUMMARY.md` for complete API documentation.
