# Shared Utilities Reference

Production-grade shared utilities for ChiliHead OpsManager v2.1: logging, metrics, and event handling.

## At a Glance

| Module | Purpose | Key Classes | Size |
|--------|---------|-------------|------|
| `logging.py` | Structured logging | `RequestContext`, `@log_execution_time` | 319 lines |
| `metrics.py` | Prometheus metrics | `Counter`, `Gauge`, `Histogram`, `MetricsRegistry` | 591 lines |
| `events.py` | NATS events | `Event`, `EventPublisher`, `EventSchema` | 617 lines |

**Total: 1,559 lines of production-ready code**

---

## Import Everything You Need

```python
# Logging
from shared.utils import setup_logging, get_logger, RequestContext, set_request_id

# Metrics
from shared.utils import get_registry, time_operation, track_execution_time

# Events
from shared.utils import Event, EventPublisher, EventType, EventSchema
```

---

## 30-Second Setup

```python
# Initialize
setup_logging(level="INFO", format_type="json")
logger = get_logger(__name__)
registry = get_registry()
publisher = EventPublisher(nats_client)

# Use
logger.info("Started", email_id="123")
registry.counter("emails_total").inc()
publisher.publish_event(
    event_type="emails.received",
    event_source="service",
    data={"email_id": "123"}
)
```

---

## Core Features

### Logging (`logging.py`)
- Structured JSON logging for production
- Pretty formatting for development
- Request ID correlation across services
- Auto-rotating log files
- Context binding (`logger.bind(...)`)
- Execution timing decorator

### Metrics (`metrics.py`)
- Prometheus-compliant counters, gauges, histograms
- Dimensional metrics with labels
- Percentile calculations (p50, p95, p99)
- Text format export for `/metrics` endpoint
- Automatic timing decorators
- Built-in bucket strategies

### Events (`events.py`)
- Type-safe Pydantic event models
- Standard event types (EMAIL_RECEIVED, AGENT_COMPLETE, etc.)
- Event validation and schemas
- Correlation ID support for tracing
- NATS integration ready
- Event history tracking for debugging

---

## Configuration

### Environment Variables
```bash
# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FORMAT=json|pretty

# Example
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### Programmatic Setup
```python
setup_logging(
    level="INFO",           # Log level
    format_type="json",     # json or pretty
    log_file="/var/log/app.log"  # Optional file output
)
```

---

## Common Patterns

### Pattern 1: Request Tracking
```python
from shared.utils import RequestContext, get_logger

logger = get_logger(__name__)

with RequestContext() as request_id:
    # All logs in this block include request_id
    logger.info("Processing request")
    do_work()  # Even if called from other functions
```

### Pattern 2: Metrics Endpoint
```python
from flask import Flask, Response
from shared.utils import get_registry

@app.route("/metrics")
def metrics():
    registry = get_registry()
    return Response(registry.export_prometheus(), mimetype="text/plain")
```

### Pattern 3: Event Publishing Pipeline
```python
from shared.utils import EventPublisher, set_request_id

publisher = EventPublisher(nats_client)
request_id = set_request_id()

# Publish with automatic correlation
publisher.publish_agent_event(
    agent_type="triage",
    agent_output=result,
    correlation_id=request_id  # Chains requests across services
)
```

### Pattern 4: Decorated Functions
```python
from shared.utils import track_execution_time, time_operation

@track_execution_time("emails_processed")  # Count + timing
@time_operation("email_processing")        # Just timing
def process_email(email: dict) -> dict:
    return result
```

---

## API Quick Reference

### Logging Functions
```python
setup_logging(level, format_type, log_file)  # Initialize
get_logger(name)                              # Get logger
set_request_id(id)                            # Set correlation ID
get_request_id()                              # Get current ID
clear_request_id()                            # Clear ID

# Usage
logger = get_logger(__name__)
logger.info("message")
logger.bind(email_id="123").info("message")
logger.error("failed", exc_info=True)

# Decorator
@log_execution_time()
def func(): pass
```

### Metrics Classes
```python
# Counter (monotonic)
counter = registry.counter("name", "description", labels=[])
counter.inc()
counter.inc(5)
counter.inc_by_labels({"label": "value"})

# Gauge (current state)
gauge = registry.gauge("name", "description")
gauge.set(42)
gauge.inc(5)
gauge.dec(2)
gauge.set_by_labels({"label": "value"}, 42)

# Histogram (distribution)
hist = registry.histogram("name", "description", buckets=(0.1, 1.0, 5.0))
hist.observe(0.234)
hist.get_percentile(95)
hist.get_bucket_count(1.0)

# Registry
registry = get_registry()
registry.export_prometheus()  # For /metrics endpoint
```

### Metrics Decorators
```python
@time_operation("operation_name")  # Histogram only
@track_execution_time("counter_name", "histogram_name")  # Both
```

### Events Classes
```python
# Event
event = Event(
    event_type="emails.received",
    event_source="service",
    event_data={"email_id": "123"},
    correlation_id=uuid4()
)
event.to_json()  # JSON string
event.to_dict()  # Dictionary

# EventType (enum)
EventType.EMAIL_RECEIVED
EventType.AGENT_TRIAGE_COMPLETE
EventType.agent_complete("triage")

# EventPublisher
publisher = EventPublisher(nats_client)
publisher.publish_event(type, source, data, correlation_id)
publisher.publish_agent_event(agent_type, output, correlation_id)
publisher.publish_action_event(action_id, type, status, result, correlation_id)
publisher.publish_dag_event(dag_id, status, metadata, correlation_id)

# EventSchema
schema = EventSchema()
is_valid, errors = schema.validate(event_type, data)
schema.register_schema(event_type, {"required": [...], "optional": [...]})
```

---

## Examples

### Complete Integration Example
```python
from shared.utils import (
    setup_logging, get_logger, RequestContext, get_registry,
    EventPublisher, EventType, time_operation
)

# Setup
setup_logging(level="INFO", format_type="json")
logger = get_logger(__name__)
registry = get_registry()
publisher = EventPublisher(nats_client)

# Metrics
emails_processed = registry.counter("emails_processed_total")
processing_time = registry.histogram("email_processing_ms")

@time_operation("email_parsing")
def parse_email(raw):
    return parsed

# Main workflow
async def process_email(email_id, body):
    with RequestContext() as rid:
        logger.info(f"Processing: {email_id}")

        try:
            result = parse_email(body)
            emails_processed.inc()

            publisher.publish_event(
                event_type=EventType.EMAIL_COMPLETED,
                event_source="processor",
                data={"email_id": email_id, "status": "success"},
                correlation_id=rid
            )

        except Exception as e:
            logger.error("Failed", exc_info=True)
            publisher.publish_event(
                event_type=EventType.EMAIL_FAILED,
                event_source="processor",
                data={"email_id": email_id, "error": str(e)},
                correlation_id=rid
            )
            raise
```

### Metrics Endpoint (Flask)
```python
from flask import Flask, Response
from shared.utils import setup_logging, get_registry

app = Flask(__name__)
setup_logging()

@app.route("/metrics")
def metrics():
    return Response(
        get_registry().export_prometheus(),
        mimetype="text/plain"
    )
```

### Event Listener (NATS)
```python
from shared.utils import Event, set_request_id, get_logger

logger = get_logger(__name__)

async def handle_email_event(msg):
    event = Event.model_validate_json(msg.data)
    set_request_id(str(event.correlation_id))
    logger.info(f"Event: {event.event_type}")
    # Process...
```

---

## Files Included

1. **`__init__.py`** - Module exports
2. **`logging.py`** - Structured logging implementation
3. **`metrics.py`** - Prometheus metrics implementation
4. **`events.py`** - NATS event definitions and publishing
5. **`EXAMPLES.md`** - Copy-paste examples (in utils/ directory)
6. **`README.md`** - This file (in utils/ directory)

Additional documentation:
- **`SHARED_UTILS_SUMMARY.md`** - Comprehensive API docs (in project root)

---

## Testing

### Test Logging
```python
import tempfile
from shared.utils import setup_logging, get_logger

with tempfile.NamedTemporaryFile(mode='w+') as f:
    setup_logging(log_file=f.name)
    logger = get_logger(__name__)
    logger.info("test")
    f.seek(0)
    assert "test" in f.read()
```

### Test Metrics
```python
from shared.utils import get_registry

registry = get_registry()
counter = registry.counter("test")
counter.inc()
assert counter.value == 1

prometheus = registry.export_prometheus()
assert "test" in prometheus
```

### Test Events
```python
from shared.utils import EventPublisher

publisher = EventPublisher()  # No NATS client
event = publisher.publish_event(
    event_type="test",
    event_source="test",
    data={}
)
assert publisher.get_published_count() == 1
```

---

## Performance Considerations

- **Logging**: Async in production via loguru, minimal overhead
- **Metrics**: In-memory, negligible overhead
- **Events**: Async to NATS, configurable batching
- **Decorators**: Minimal overhead, ~1-2ms per call

---

## Dependencies

- `loguru` - Structured logging (already in requirements)
- `pydantic` - Data validation (already in project)
- Standard library only for metrics and events

---

## Best Practices

1. **Initialize once**: Call `setup_logging()` in application entry point
2. **Use context managers**: `with RequestContext(): ...` for request tracking
3. **Bind context**: `logger.bind(execution_id="...").info(...)`
4. **Export metrics**: Expose at `/metrics` endpoint for Prometheus
5. **Correlate requests**: Pass `correlation_id` between services
6. **Validate events**: Use `EventSchema` before processing
7. **Test without NATS**: `EventPublisher()` works in unit tests

---

## Support

For complete API documentation, see `SHARED_UTILS_SUMMARY.md`.
For examples and patterns, see `EXAMPLES.md` in this directory.

---

**Version**: 1.0.0
**Status**: Production Ready
**Python**: 3.8+
