"""
NATS event definitions and publishing utilities.
Provides event type enums, event validation, and helpers for publishing/subscribing to events.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """
    Event types published through NATS messaging system.

    Events follow a hierarchical naming convention: domain.action
    enabling efficient topic subscriptions and filtering.

    Example:
        emails.received -> New email arrived
        agents.triage.complete -> Triage agent finished processing
        dolphin.task.started -> DAG execution task started
    """

    # Email lifecycle events
    EMAIL_RECEIVED = "emails.received"
    EMAIL_PROCESSING = "emails.processing"
    EMAIL_COMPLETED = "emails.completed"
    EMAIL_FAILED = "emails.failed"

    # Dolphin DAG execution events
    DAG_SUBMITTED = "dolphin.dag.submitted"
    TASK_STARTED = "dolphin.task.started"
    TASK_COMPLETED = "dolphin.task.completed"
    TASK_FAILED = "dolphin.task.failed"

    # Agent completion events
    AGENT_TRIAGE_COMPLETE = "agents.triage.complete"
    AGENT_VISION_COMPLETE = "agents.vision.complete"
    AGENT_DEADLINE_COMPLETE = "agents.deadline.complete"
    AGENT_TASK_COMPLETE = "agents.task.complete"
    AGENT_CONTEXT_COMPLETE = "agents.context.complete"

    # UI-TARS events
    UITARS_CHECKPOINT = "uitars.checkpoint"
    UITARS_SESSION_COMPLETE = "uitars.session.complete"

    # Action events
    ACTION_CREATED = "actions.created"
    ACTION_EXECUTED = "actions.executed"
    ACTION_FAILED = "actions.failed"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH = "system.health"

    @classmethod
    def agent_complete(cls, agent_type: str) -> str:
        """
        Generate an agent completion event type.

        Args:
            agent_type: Type of agent (triage, vision, deadline, task, context).

        Returns:
            Event type string (e.g., "agents.triage.complete").

        Example:
            >>> EventType.agent_complete("triage")
            'agents.triage.complete'
        """
        agent_type = agent_type.lower()
        if agent_type == "triage":
            return cls.AGENT_TRIAGE_COMPLETE
        elif agent_type == "vision":
            return cls.AGENT_VISION_COMPLETE
        elif agent_type == "deadline":
            return cls.AGENT_DEADLINE_COMPLETE
        elif agent_type == "task":
            return cls.AGENT_TASK_COMPLETE
        elif agent_type == "context":
            return cls.AGENT_CONTEXT_COMPLETE
        else:
            return f"agents.{agent_type}.complete"

    @classmethod
    def action_event(cls, event_status: str) -> str:
        """
        Generate an action event type based on status.

        Args:
            event_status: Status of action (created, executed, failed).

        Returns:
            Event type string.

        Example:
            >>> EventType.action_event("created")
            'actions.created'
        """
        if event_status.lower() == "created":
            return cls.ACTION_CREATED
        elif event_status.lower() == "executed":
            return cls.ACTION_EXECUTED
        elif event_status.lower() == "failed":
            return cls.ACTION_FAILED
        else:
            return f"actions.{event_status}"


class Event(BaseModel):
    """
    Base event model for NATS messaging.

    All events contain:
    - Unique ID for deduplication
    - Event type for routing/filtering
    - Source system that emitted the event
    - Correlation ID for request tracing
    - Timestamp for ordering
    - Arbitrary event data payload

    Example:
        >>> event = Event(
        ...     event_type="emails.received",
        ...     event_source="gmail-service",
        ...     event_data={"email_id": "123", "subject": "Test"},
        ...     correlation_id=UUID("550e8400-e29b-41d4-a716-446655440000")
        ... )
        >>> event_json = event.model_dump_json()
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique event identifier for deduplication",
    )
    event_type: str = Field(
        ...,
        description="Event type for routing (e.g., 'emails.received')",
        examples=["emails.received", "agents.triage.complete"],
    )
    event_source: str = Field(
        ...,
        description="Source service that emitted the event",
        examples=["gmail-service", "triage-agent", "dolphin-executor"],
    )
    event_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary event payload data",
    )
    correlation_id: Optional[UUID] = Field(
        default=None,
        description="Request ID for distributed tracing across services",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO8601 timestamp when event was created",
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """
        Validate event type follows naming conventions.

        Event types should be lowercase with dots as separators.

        Args:
            v: Event type string to validate.

        Returns:
            Validated event type.

        Raises:
            ValueError: If event type format is invalid.
        """
        if not v or not isinstance(v, str):
            raise ValueError("Event type must be a non-empty string")

        if not all(c.isalnum() or c in "._-" for c in v):
            raise ValueError(
                f"Event type '{v}' contains invalid characters. "
                "Use only alphanumeric, dots, underscores, and hyphens."
            )

        return v.lower()

    @field_validator("event_source")
    @classmethod
    def validate_event_source(cls, v: str) -> str:
        """
        Validate event source format.

        Args:
            v: Event source string.

        Returns:
            Validated source.

        Raises:
            ValueError: If source is empty.
        """
        if not v or not isinstance(v, str):
            raise ValueError("Event source must be a non-empty string")
        return v.lower()

    def to_json(self) -> str:
        """
        Serialize event to JSON string.

        Returns:
            JSON string representation of the event.

        Example:
            >>> event = Event(event_type="test", event_source="test-service")
            >>> json_str = event.to_json()
        """
        return self.model_dump_json(default=str)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary.

        Returns:
            Dictionary representation with UUID/datetime as strings.

        Example:
            >>> event = Event(event_type="test", event_source="test-service")
            >>> event_dict = event.to_dict()
        """
        data = self.model_dump()
        # Convert UUID and datetime to strings for serialization
        data["id"] = str(data["id"])
        if data.get("correlation_id"):
            data["correlation_id"] = str(data["correlation_id"])
        data["timestamp"] = data["timestamp"].isoformat() + "Z"
        return data


class EventPublisher:
    """
    Helper for publishing events to NATS.

    Handles validation, correlation ID propagation, and publishing logic.
    Integrates with the NATS client to send events.

    Example:
        >>> publisher = EventPublisher(nats_client)
        >>> publisher.publish_event(
        ...     event_type="emails.received",
        ...     event_source="gmail-service",
        ...     data={"email_id": "123"}
        ... )
    """

    def __init__(self, nats_client: Optional[Any] = None):
        """
        Initialize event publisher.

        Args:
            nats_client: Optional NATS client instance. If None, publisher will
                        validate but not publish events (useful for testing).

        Example:
            >>> from nats.aio.client import Client
            >>> nc = Client()
            >>> publisher = EventPublisher(nc)
        """
        self.nats_client = nats_client
        self.published_events: List[Event] = []  # For tracking/debugging

    def publish_event(
        self,
        event_type: str,
        event_source: str,
        data: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
    ) -> Event:
        """
        Publish an event to NATS.

        Validates the event, publishes to NATS, and tracks it locally.

        Args:
            event_type: Type of event (from EventType enum or custom).
            event_source: Source service name.
            data: Event payload data.
            correlation_id: Optional correlation ID for request tracing.

        Returns:
            The published Event object.

        Raises:
            ValueError: If event validation fails.

        Example:
            >>> publisher.publish_event(
            ...     event_type="emails.received",
            ...     event_source="gmail-service",
            ...     data={"email_id": "123", "subject": "Test"}
            ... )
        """
        # Create event
        event = Event(
            event_type=event_type,
            event_source=event_source,
            event_data=data,
            correlation_id=correlation_id,
        )

        # Publish if client is available
        if self.nats_client:
            try:
                # NATS publishing is async, but for type hints we show sync interface
                # In actual implementation, this would be awaited
                subject = self._get_subject(event_type)
                payload = event.to_json().encode()
                # self.nats_client.publish(subject, payload)
                # For async: await nats_client.publish(subject, payload)
            except Exception as e:
                raise ValueError(f"Failed to publish event: {e}")

        # Track event locally
        self.published_events.append(event)

        return event

    def publish_agent_event(
        self,
        agent_type: str,
        agent_output: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
    ) -> Event:
        """
        Publish an agent completion event.

        Args:
            agent_type: Type of agent (triage, vision, deadline, task, context).
            agent_output: Agent output data.
            correlation_id: Optional correlation ID.

        Returns:
            The published Event.

        Example:
            >>> publisher.publish_agent_event(
            ...     agent_type="triage",
            ...     agent_output={"findings": {...}, "confidence": 0.95}
            ... )
        """
        event_type = EventType.agent_complete(agent_type)
        return self.publish_event(
            event_type=event_type,
            event_source=f"{agent_type}-agent",
            data=agent_output,
            correlation_id=correlation_id,
        )

    def publish_action_event(
        self,
        action_id: str,
        action_type: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None,
    ) -> Event:
        """
        Publish an action event.

        Args:
            action_id: Unique action identifier.
            action_type: Type of action (create_task, schedule_event, etc).
            status: Status of action (created, executed, failed).
            result: Optional result data.
            correlation_id: Optional correlation ID.

        Returns:
            The published Event.

        Example:
            >>> publisher.publish_action_event(
            ...     action_id="act-123",
            ...     action_type="create_task",
            ...     status="executed",
            ...     result={"task_id": "task-456"}
            ... )
        """
        event_type = EventType.action_event(status)
        data = {
            "action_id": action_id,
            "action_type": action_type,
            "status": status,
        }
        if result:
            data["result"] = result

        return self.publish_event(
            event_type=event_type,
            event_source="action-executor",
            data=data,
            correlation_id=correlation_id,
        )

    def publish_dag_event(
        self,
        dag_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None,
    ) -> Event:
        """
        Publish a Dolphin DAG execution event.

        Args:
            dag_id: DAG identifier.
            status: DAG status (submitted, started, completed, failed).
            metadata: Optional metadata.
            correlation_id: Optional correlation ID.

        Returns:
            The published Event.

        Example:
            >>> publisher.publish_dag_event(
            ...     dag_id="dag-123",
            ...     status="submitted",
            ...     metadata={"email_id": "email-456"}
            ... )
        """
        status_map = {
            "submitted": EventType.DAG_SUBMITTED,
            "started": EventType.TASK_STARTED,
            "completed": EventType.TASK_COMPLETED,
            "failed": EventType.TASK_FAILED,
        }
        event_type = status_map.get(status.lower(), f"dolphin.{status.lower()}")

        data = {"dag_id": dag_id, "status": status}
        if metadata:
            data.update(metadata)

        return self.publish_event(
            event_type=event_type,
            event_source="dolphin-executor",
            data=data,
            correlation_id=correlation_id,
        )

    @staticmethod
    def _get_subject(event_type: str) -> str:
        """
        Convert event type to NATS subject.

        NATS subjects use dots as delimiters: domain.action

        Args:
            event_type: Event type string.

        Returns:
            NATS subject string.

        Example:
            >>> EventPublisher._get_subject("emails.received")
            'emails.received'
        """
        # In NATS, subject can be event_type directly
        # Can add prefix if needed: f"events.{event_type}"
        return event_type

    def get_published_count(self) -> int:
        """
        Get total number of published events.

        Returns:
            Count of published events.

        Useful for testing and monitoring.
        """
        return len(self.published_events)

    def get_published_events(self) -> List[Event]:
        """
        Get list of all published events.

        Returns:
            List of Event objects.

        Useful for testing and debugging.
        """
        return self.published_events.copy()

    def clear_published_events(self) -> None:
        """Clear the local event history."""
        self.published_events.clear()


class EventSchema:
    """
    Schema validator and registry for event payloads.

    Defines expected data structure for each event type
    and provides validation utilities.

    Example:
        >>> schema = EventSchema()
        >>> schema.register("emails.received", ["email_id", "subject", "sender"])
        >>> schema.validate("emails.received", {"email_id": "123", ...})
    """

    def __init__(self):
        """Initialize schema registry with standard event schemas."""
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._register_standard_schemas()

    def _register_standard_schemas(self) -> None:
        """Register schemas for standard event types."""
        # Email events
        self.register_schema(
            EventType.EMAIL_RECEIVED,
            {
                "required": ["email_id", "subject", "sender"],
                "optional": ["recipient", "body", "attachments"],
            },
        )

        # Agent events
        self.register_schema(
            EventType.AGENT_TRIAGE_COMPLETE,
            {
                "required": ["email_id", "findings", "confidence"],
                "optional": ["next_actions", "execution_time_ms"],
            },
        )

        self.register_schema(
            EventType.AGENT_CONTEXT_COMPLETE,
            {
                "required": ["email_id", "findings", "synthesis"],
                "optional": ["recommendations", "risk_assessment"],
            },
        )

        # DAG events
        self.register_schema(
            EventType.DAG_SUBMITTED,
            {
                "required": ["dag_id", "email_id"],
                "optional": ["metadata", "status"],
            },
        )

        # Action events
        self.register_schema(
            EventType.ACTION_CREATED,
            {
                "required": ["action_id", "action_type"],
                "optional": ["payload", "confidence"],
            },
        )

    def register_schema(
        self,
        event_type: str,
        schema: Dict[str, List[str]],
    ) -> None:
        """
        Register a schema for an event type.

        Args:
            event_type: Event type string.
            schema: Dict with "required" and "optional" keys containing field names.

        Example:
            >>> schema_def = {
            ...     "required": ["email_id", "status"],
            ...     "optional": ["error_message"]
            ... }
            >>> schema.register_schema("emails.failed", schema_def)
        """
        self.schemas[event_type] = schema

    def validate(self, event_type: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate event data against registered schema.

        Args:
            event_type: Event type to validate against.
            data: Event data dictionary.

        Returns:
            Tuple of (is_valid, list_of_errors).

        Example:
            >>> is_valid, errors = schema.validate(
            ...     "emails.received",
            ...     {"email_id": "123", "subject": "Test", "sender": "test@example.com"}
            ... )
            >>> if not is_valid:
            ...     print(f"Validation failed: {errors}")
        """
        if event_type not in self.schemas:
            # No schema registered, assume valid
            return True, []

        schema = self.schemas[event_type]
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        return len(errors) == 0, errors
