# Shared Utilities Module Summary

ChiliHead OpsManager v2.1 - Shared utility modules for logging, metrics, and event handling.

## Files Created

### 1. `shared/utils/__init__.py` (32 lines)
**Exports**: All public APIs from utility modules

Exports:
- `setup_logging()`, `get_logger()` - Logging utilities
- `Counter`, `Gauge`, `Histogram`, `MetricsRegistry` - Metrics classes
- `time_operation()`, `track_execution_time()` - Metrics decorators
- `Event`, `EventType`, `EventPublisher` - Event classes

**Usage**:
```python
from shared.utils import setup_logging, get_logger, get_registry
```

---

### 2. `shared/utils/logging.py` (319 lines)
**Purpose**: Structured logging with loguru, JSON/pretty formatting, correlation IDs

**Key Classes**:
- `RequestContext` - Context manager for request ID tracking
- Custom sinks: `json_sink()`, `pretty_sink()` - Production/development formatters

**Key Functions**:
- `setup_logging(level, format_type, log_file)` - Initialize logging
  - Supports LOG_LEVEL and LOG_FORMAT environment variables
  - JSON output for production, pretty output for development
  - Optional file rotation support (10MB per file, 7-day retention)

- `get_logger(name)` - Get logger for module
  - Returns loguru logger with module context binding
  - Supports adding extra fields: `logger.bind(execution_id="123")`

- `set_request_id()` / `get_request_id()` / `clear_request_id()` - Request ID management
  - Global correlation ID across services
  - Auto-generates UUID if not provided

- `@log_execution_time(level)` - Decorator to log function timing

**Features**:
- JSON formatting for production with timestamp, level, logger, message, context, exceptions
- Pretty formatting for development with colors and readability
- Request ID correlation for distributed tracing
- Module, function, and line number tracking
- Exception information capture
- File rotation and retention policies

**Example Usage**:
```python
# Setup
from shared.utils import setup_logging, get_logger, set_request_id, RequestContext

setup_logging(level="INFO", format_type="json")
logger = get_logger(__name__)

# Request tracking
with RequestContext() as request_id:
    logger.info("Processing request")

# Execution timing
@log_execution_time()
def process_email(email_id):
    # Function timing logged automatically
    pass

# Context binding
logger.bind(execution_id="exec-123", email_id="email-456").info("Starting")
```

---

### 3. `shared/utils/metrics.py` (591 lines)
**Purpose**: Prometheus metrics for observability - counters, gauges, histograms

**Key Classes**:
- `Counter` - Monotonically increasing metric (events, requests, errors)
  - Methods: `inc(amount)`, `inc_by_labels(labels_dict, amount)`
  - Thread-safe tracking by label values

- `Gauge` - Current state metric (active connections, queue size, memory)
  - Methods: `set(value)`, `inc(amount)`, `dec(amount)`, `set_by_labels()`
  - Can increase or decrease

- `Histogram` - Distribution tracking (request duration, response size)
  - Methods: `observe(value)`, `observe_by_labels()`, `get_percentile()`, `get_bucket_count()`
  - Default buckets: 0.005s, 0.01s, 0.025s, ..., 10.0s (14 buckets)
  - Calculates percentiles and bucket distributions

- `MetricsRegistry` - Central metrics management
  - Methods: `counter()`, `gauge()`, `histogram()`, `export_prometheus()`
  - Exports in Prometheus text format (# HELP, # TYPE, metric lines)
  - Global instance: `get_registry()`

**Key Functions**:
- `get_registry()` - Get global metrics registry
- `@time_operation(name)` - Auto-track function duration as histogram
- `@track_execution_time(counter, histogram)` - Track both count and duration

**Features**:
- Prometheus-compliant naming and formatting
- Metric validation (names must match [a-zA-Z_:][a-zA-Z0-9_:]*)
- Label support for dimensional metrics
- Histogram with percentile calculations
- Bucket validation (must be sorted)
- Full Prometheus text format export
- Type hints and comprehensive documentation

**Example Usage**:
```python
from shared.utils import get_registry, time_operation, track_execution_time

# Initialize metrics
registry = get_registry()
emails_processed = registry.counter(
    "emails_processed_total",
    "Total emails processed",
    labels=["agent_type"]
)
processing_time = registry.histogram(
    "email_processing_seconds",
    "Time to process email",
    buckets=(0.1, 0.5, 1.0, 5.0)
)

# Track metrics
emails_processed.inc_by_labels({"agent_type": "triage"})
processing_time.observe(0.234)

# Decorators
@time_operation("email_parsing")
def parse_email(email):
    return parsed_email

@track_execution_time("actions_executed", "action_duration_ms")
def execute_action(action):
    return result

# Export for Prometheus scraping
prometheus_output = registry.export_prometheus()
```

---

### 4. `shared/utils/events.py` (617 lines)
**Purpose**: NATS event definitions, validation, and publishing

**Key Enums**:
- `EventType` - Standard event types with hierarchical naming (domain.action)
  - Email events: `EMAIL_RECEIVED`, `EMAIL_PROCESSING`, `EMAIL_COMPLETED`, `EMAIL_FAILED`
  - Agent events: `AGENT_TRIAGE_COMPLETE`, `AGENT_VISION_COMPLETE`, `AGENT_DEADLINE_COMPLETE`, `AGENT_TASK_COMPLETE`, `AGENT_CONTEXT_COMPLETE`
  - DAG events: `DAG_SUBMITTED`, `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`
  - UI-TARS events: `UITARS_CHECKPOINT`, `UITARS_SESSION_COMPLETE`
  - Action events: `ACTION_CREATED`, `ACTION_EXECUTED`, `ACTION_FAILED`
  - System events: `SYSTEM_ERROR`, `SYSTEM_HEALTH`
  - Helper methods: `agent_complete(agent_type)`, `action_event(status)`

**Key Classes**:
- `Event` - Base event model (Pydantic)
  - Fields: id (UUID), event_type, event_source, event_data (dict), correlation_id, timestamp
  - Validation: event_type (alphanumeric, dots, underscores), event_source (non-empty)
  - Methods: `to_json()`, `to_dict()` with proper UUID/datetime serialization
  - Default fields: auto-generated UUID, current timestamp

- `EventPublisher` - Event publishing and tracking
  - Methods:
    - `publish_event(type, source, data, correlation_id)` - Publish generic event
    - `publish_agent_event(agent_type, output, correlation_id)` - Publish agent completion
    - `publish_action_event(action_id, type, status, result, correlation_id)` - Publish action
    - `publish_dag_event(dag_id, status, metadata, correlation_id)` - Publish DAG event
  - Tracking: `get_published_count()`, `get_published_events()`, `clear_published_events()`
  - NATS integration ready (configurable with or without client)

- `EventSchema` - Schema validation for event payloads
  - Methods: `register_schema()`, `validate(event_type, data)`
  - Pre-registered schemas for standard event types
  - Returns: (is_valid: bool, errors: List[str])
  - Validates required and optional fields

**Features**:
- Type-safe event definitions with Pydantic validation
- Hierarchical event naming for efficient NATS subscriptions
- Correlation ID support for distributed request tracing
- Event schema validation and registration
- JSON/dict serialization with proper type handling
- Flexible event publishing with optional NATS client
- Event history tracking for testing/debugging
- Comprehensive docstrings and examples

**Example Usage**:
```python
from shared.utils import Event, EventType, EventPublisher, EventSchema

# Create event directly
event = Event(
    event_type=EventType.EMAIL_RECEIVED,
    event_source="gmail-service",
    event_data={
        "email_id": "email-123",
        "subject": "Test email",
        "sender": "sender@example.com"
    }
)

# Publish events
publisher = EventPublisher(nats_client)

# Generic event
event = publisher.publish_event(
    event_type="emails.received",
    event_source="gmail-service",
    data={"email_id": "123", "subject": "Test"}
)

# Agent completion
event = publisher.publish_agent_event(
    agent_type="triage",
    agent_output={"findings": {...}, "confidence": 0.95}
)

# Action event
event = publisher.publish_action_event(
    action_id="act-123",
    action_type="create_task",
    status="executed",
    result={"task_id": "task-456"}
)

# DAG event
event = publisher.publish_dag_event(
    dag_id="dag-123",
    status="submitted",
    metadata={"email_id": "email-456"}
)

# Schema validation
schema = EventSchema()
is_valid, errors = schema.validate(
    EventType.EMAIL_RECEIVED,
    {"email_id": "123", "subject": "Test", "sender": "test@example.com"}
)
if not is_valid:
    print(f"Validation errors: {errors}")

# NATS subject generation
subject = EventPublisher._get_subject("emails.received")  # "emails.received"
```

---

## Module Statistics

| Module | Lines | Classes | Functions | Purpose |
|--------|-------|---------|-----------|---------|
| `__init__.py` | 32 | 0 | 1 | Module exports |
| `logging.py` | 319 | 1 | 9 | Structured logging |
| `metrics.py` | 591 | 4 | 2 | Prometheus metrics |
| `events.py` | 617 | 4 | 2 | NATS events |
| **TOTAL** | **1,559** | **9** | **14** | - |

---

## Key Features Across All Modules

### Type Hints
- Full type annotations on all functions and classes
- Generic types (Dict, List, Optional, etc.) from typing module
- Return type hints for all functions
- Type validation in Pydantic models

### Documentation
- Comprehensive module docstrings
- Class docstrings with purpose and example usage
- Function docstrings with Args, Returns, Raises, Examples
- Inline comments for complex logic
- Usage examples in comments showing common patterns

### Error Handling
- Input validation in __init__ and methods
- Meaningful error messages with context
- ValueError exceptions with helpful guidance
- Exception propagation where appropriate
- Try/finally blocks for resource cleanup

### Design Patterns
- Registry pattern (MetricsRegistry, EventSchema)
- Context manager pattern (RequestContext)
- Decorator pattern (time_operation, track_execution_time, log_execution_time)
- Factory pattern (EventType helper methods)
- Singleton pattern (global metrics registry, request ID)

---

## Integration Examples

### Complete Application Setup
```python
from shared.utils import (
    setup_logging, get_logger, get_registry,
    EventPublisher, EventType
)

# Initialize logging
setup_logging(level="INFO", format_type="json")
logger = get_logger(__name__)

# Initialize metrics
registry = get_registry()
emails_processed = registry.counter("emails_processed_total")
processing_time = registry.histogram("processing_duration_ms")

# Initialize event publisher
publisher = EventPublisher(nats_client)

# Use in application
try:
    logger.info("Starting email processor")

    with RequestContext():
        # Process email
        emails_processed.inc()
        processing_time.observe(elapsed_ms)

        # Publish event
        publisher.publish_event(
            event_type=EventType.EMAIL_COMPLETED,
            event_source="processor",
            data={"email_id": "123"}
        )
except Exception as e:
    logger.error("Failed to process email", exc_info=True)
    emails_processed.inc_by_labels({"status": "failed"})
```

### Multi-Service Communication
```python
# Service A: Process and publish
publisher = EventPublisher(nats_client)

with RequestContext() as request_id:
    logger.info("Processing request")
    result = process_email(email)

    # Publish completion with correlation ID
    publisher.publish_agent_event(
        agent_type="triage",
        agent_output=result,
        correlation_id=request_id
    )

# Service B: Subscribe and consume
schema = EventSchema()

async def handle_event(msg):
    event = Event.model_validate_json(msg.data)

    # Validate schema
    is_valid, errors = schema.validate(event.event_type, event.event_data)
    if not is_valid:
        logger.error("Invalid event", errors=errors)
        return

    # Log with correlation ID
    logger.bind(correlation_id=event.correlation_id).info(f"Event: {event.event_type}")

    # Process event
    await process_event(event)
```

---

## Environment Variables

### Logging Configuration
- `LOG_LEVEL` - Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT` - Set format type (json, pretty)

Example:
```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=pretty
```

---

## Dependencies

The utilities have minimal dependencies:
- `loguru` - Structured logging (specified in requirements.txt)
- `pydantic` - Data validation (already in project)
- Standard library: `json`, `sys`, `time`, `functools`, `enum`, `uuid`, `datetime`, `typing`

No additional dependencies required for metrics or events modules - pure Python implementations.

---

## Testing Integration

All modules include comprehensive docstrings with example usage suitable for pytest/unittest:

```python
import pytest
from shared.utils import setup_logging, get_logger, get_registry, EventPublisher

def test_logging_setup(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logging(level="DEBUG", format_type="pretty", log_file=str(log_file))
    logger = get_logger(__name__)
    logger.info("Test message")
    assert log_file.exists()

def test_metrics():
    registry = get_registry()
    counter = registry.counter("test_counter")
    counter.inc()
    assert counter.value == 1

def test_event_publisher():
    publisher = EventPublisher()  # No client = validation only
    event = publisher.publish_event(
        event_type="test.event",
        event_source="test",
        data={"key": "value"}
    )
    assert event.event_type == "test.event"
    assert publisher.get_published_count() == 1
```

---

## Next Steps

1. **Integration**: Import and use in agents, services, and application entry points
2. **Configuration**: Set LOG_LEVEL and LOG_FORMAT environment variables as needed
3. **Metrics Scraping**: Expose `/metrics` endpoint that calls `registry.export_prometheus()`
4. **NATS Connection**: Pass configured NATS client to EventPublisher
5. **Monitoring**: Set up Prometheus scraping and alert rules based on metrics
6. **Testing**: Use in-memory EventPublisher (without NATS client) in unit tests

---

**Created**: 2025-11-23
**Total Lines of Code**: 1,559
**Total Classes**: 9
**Total Functions**: 14
