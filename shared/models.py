"""
ChiliHead OpsManager v2.1 - Pydantic Models
Shared data models used across all components
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ExecutionStatus(str, Enum):
    """Execution status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Agent type enum"""
    TRIAGE = "triage"
    VISION = "vision"
    DEADLINE = "deadline"
    TASK = "task"
    CONTEXT = "context"


class ActionType(str, Enum):
    """Action type enum"""
    CREATE_TASK = "create_task"
    SCHEDULE_EVENT = "schedule_event"
    SEND_NOTIFICATION = "send_notification"
    HUMAN_REVIEW = "human_review"


class EmailCategory(str, Enum):
    """Email category enum"""
    VENDOR = "vendor"
    STAFF = "staff"
    CUSTOMER = "customer"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ========== Email Models ==========

class EmailAttachment(BaseModel):
    """Email attachment model"""
    filename: str
    content_type: str
    size: int
    url: Optional[str] = None


class EmailData(BaseModel):
    """Email data model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    subject: str
    sender: str
    recipient: str
    body: str
    attachments: List[EmailAttachment] = Field(default_factory=list)
    received_at: datetime = Field(default_factory=datetime.now)
    headers: Dict[str, Any] = Field(default_factory=dict)


# ========== Agent Input/Output Models ==========

class AgentInput(BaseModel):
    """Base agent input model"""
    email_id: str
    session_id: str
    checkpoint_enabled: bool = True


class AgentOutput(BaseModel):
    """Base agent output model"""
    agent_type: AgentType
    findings: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    next_actions: List[str]
    execution_time_ms: int
    model_used: str
    ui_tars_checkpoints: List[str] = Field(default_factory=list)


class TriageInput(AgentInput):
    """Triage agent input"""
    body: str
    subject: str


class TriageOutput(AgentOutput):
    """Triage agent output"""
    agent_type: AgentType = AgentType.TRIAGE
    findings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "category": None,
            "urgency": 0,
            "type": None,
            "requires_vision": False,
            "has_deadline": False
        }
    )


class VisionInput(AgentInput):
    """Vision agent input"""
    attachments: List[EmailAttachment]


class VisionOutput(AgentOutput):
    """Vision agent output"""
    agent_type: AgentType = AgentType.VISION
    findings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "extracted_text": {},
            "invoice_data": None,
            "receipt_data": None,
            "images_processed": 0
        }
    )


class DeadlineInput(AgentInput):
    """Deadline scanner input"""
    body: str


class DeadlineOutput(AgentOutput):
    """Deadline scanner output"""
    agent_type: AgentType = AgentType.DEADLINE
    findings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "deadlines": [],
            "recurring_events": [],
            "parsed_dates": []
        }
    )


class TaskInput(AgentInput):
    """Task categorizer input"""
    body: str
    triage_output: Optional[Dict[str, Any]] = None


class TaskOutput(AgentOutput):
    """Task categorizer output"""
    agent_type: AgentType = AgentType.TASK
    findings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "tasks": [],
            "priorities": {},
            "assignees": {}
        }
    )


class ContextInput(AgentInput):
    """Context agent input"""
    triage_output: Dict[str, Any]
    vision_output: Optional[Dict[str, Any]] = None
    deadline_output: Dict[str, Any]
    task_output: Optional[Dict[str, Any]] = None
    historical_context: List[Dict[str, Any]] = Field(default_factory=list)


class ContextOutput(AgentOutput):
    """Context agent output - CRITICAL, NO FALLBACK"""
    agent_type: AgentType = AgentType.CONTEXT
    findings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "synthesis": "",
            "historical_pattern": None,
            "vendor_reliability": None,
            "recommendations": [],
            "risk_assessment": RiskLevel.LOW
        }
    )


# ========== Action Models ==========

class Action(BaseModel):
    """Base action model"""
    id: UUID = Field(default_factory=uuid4)
    execution_id: UUID
    action_type: ActionType
    payload: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None


class TaskAction(Action):
    """Create task action"""
    action_type: ActionType = ActionType.CREATE_TASK
    payload: Dict[str, Any] = Field(
        default_factory=lambda: {
            "title": "",
            "description": "",
            "due_date": None,
            "assignee": None,
            "priority": "medium"
        }
    )


class CalendarAction(Action):
    """Schedule event action"""
    action_type: ActionType = ActionType.SCHEDULE_EVENT
    payload: Dict[str, Any] = Field(
        default_factory=lambda: {
            "title": "",
            "time": None,
            "attendees": [],
            "location": None
        }
    )


class NotificationAction(Action):
    """Send notification action"""
    action_type: ActionType = ActionType.SEND_NOTIFICATION
    payload: Dict[str, Any] = Field(
        default_factory=lambda: {
            "recipient": "",
            "message": "",
            "urgency": "normal",
            "channel": "sms"
        }
    )


# ========== Execution Models ==========

class Execution(BaseModel):
    """Execution tracking model"""
    id: UUID = Field(default_factory=uuid4)
    email_id: str
    dag_id: str
    dolphin_execution_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_outputs: List[AgentOutput] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)


# ========== UI-TARS Models ==========

class UITARSCheckpoint(BaseModel):
    """UI-TARS checkpoint model"""
    timestamp: datetime = Field(default_factory=datetime.now)
    checkpoint_name: str
    data: Dict[str, Any]
    screenshot: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class UITARSSession(BaseModel):
    """UI-TARS session model"""
    id: UUID = Field(default_factory=uuid4)
    execution_id: UUID
    session_type: str
    checkpoints: List[UITARSCheckpoint] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.RUNNING


# ========== NATS Event Models ==========

class EventType(str, Enum):
    """Event type enum"""
    EMAIL_RECEIVED = "emails.received"
    EMAIL_PROCESSING = "emails.processing"
    EMAIL_COMPLETED = "emails.completed"
    DAG_SUBMITTED = "dolphin.dag.submitted"
    TASK_STARTED = "dolphin.task.started"
    TASK_COMPLETED = "dolphin.task.completed"
    TASK_FAILED = "dolphin.task.failed"
    AGENT_COMPLETE = "agents.{}.complete"
    UITARS_CHECKPOINT = "uitars.checkpoint"
    ACTION_CREATED = "actions.{}.created"


class Event(BaseModel):
    """Base event model"""
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_source: str
    event_data: Dict[str, Any]
    correlation_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ========== Configuration Models ==========

class AgentConfig(BaseModel):
    """Agent configuration model"""
    model: str
    timeout: int
    gpu: bool = False
    fallback_allowed: bool = True
    max_retries: int = 3


class AUBSConfig(BaseModel):
    """AUBS configuration model"""
    dolphin_url: str = "http://dolphin-server:12345"
    ui_tars_url: str = "http://uitars:8080"
    confidence_threshold: float = 0.9
    max_retries: int = 3
    agent_configs: Dict[str, AgentConfig] = Field(
        default_factory=lambda: {
            "triage": AgentConfig(
                model="llama-3.2-8b-instruct",
                timeout=15,
                gpu=False
            ),
            "vision": AgentConfig(
                model="llama-vision",
                timeout=30,
                gpu=True
            ),
            "deadline": AgentConfig(
                model="llama-3.2-8b-instruct",
                timeout=15,
                gpu=False
            ),
            "task": AgentConfig(
                model="llama-3.2-8b-instruct",
                timeout=15,
                gpu=False
            ),
            "context": AgentConfig(
                model="oss-120b",
                timeout=30,
                gpu=True,
                fallback_allowed=False  # CRITICAL
            )
        }
    )
