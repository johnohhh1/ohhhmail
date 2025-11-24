"""
AUBS Chat Service - Operational Awareness Assistant
Provides intelligent chat interface with complete context of all operations
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncIterator, Dict, List, Optional, Any
from uuid import UUID, uuid4

import httpx
import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from src.config import AUBSSettings
from shared.models import ExecutionStatus, AgentType, ActionType

logger = structlog.get_logger()


class ChatMessage(BaseModel):
    """Chat message model"""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """Chat session model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = "default"
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperationalContext(BaseModel):
    """Complete operational context for chat"""
    total_emails_processed: int = 0
    emails_today: int = 0
    active_executions: int = 0
    failed_executions: int = 0
    total_tasks_created: int = 0
    total_events_scheduled: int = 0
    recent_emails: List[Dict[str, Any]] = Field(default_factory=list)
    current_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_deadlines: List[Dict[str, Any]] = Field(default_factory=list)
    agent_performance: Dict[str, Any] = Field(default_factory=dict)
    system_health: Dict[str, Any] = Field(default_factory=dict)
    high_risk_items: List[Dict[str, Any]] = Field(default_factory=list)


class AUBSChatService:
    """
    AUBS Chat Service with full operational awareness

    Features:
    - Full context of all processed emails
    - Current tasks and deadlines
    - Agent performance metrics
    - Recent actions taken
    - System status
    - 30-day memory via Context Agent integration
    - Streaming responses
    - Session management
    """

    def __init__(self, settings: AUBSSettings, orchestrator):
        """
        Initialize chat service

        Args:
            settings: AUBS configuration
            orchestrator: Reference to AUBSOrchestrator for context
        """
        self.settings = settings
        self.orchestrator = orchestrator

        # Initialize Anthropic client for Claude
        self.anthropic = AsyncAnthropic()

        # In-memory storage (should be PostgreSQL in production)
        self.sessions: Dict[UUID, ChatSession] = {}
        self.messages: Dict[UUID, List[ChatMessage]] = {}

        # HTTP client for external services
        self.http_client: Optional[httpx.AsyncClient] = None

        logger.info("AUBS Chat Service initialized")

    async def initialize(self):
        """Initialize chat service components"""
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("Chat service HTTP client initialized")

    async def shutdown(self):
        """Shutdown chat service gracefully"""
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Chat service shutdown complete")

    async def create_session(self, user_id: str = "default") -> ChatSession:
        """
        Create new chat session

        Args:
            user_id: User identifier

        Returns:
            Created chat session
        """
        session = ChatSession(user_id=user_id)
        self.sessions[session.id] = session
        self.messages[session.id] = []

        logger.info("Chat session created", session_id=str(session.id), user_id=user_id)
        return session

    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """
        Get chat session by ID

        Args:
            session_id: Session UUID

        Returns:
            Chat session or None
        """
        return self.sessions.get(session_id)

    async def list_sessions(self, user_id: str = "default", limit: int = 20) -> List[ChatSession]:
        """
        List chat sessions for user

        Args:
            user_id: User identifier
            limit: Maximum sessions to return

        Returns:
            List of chat sessions
        """
        user_sessions = [
            s for s in self.sessions.values()
            if s.user_id == user_id
        ]

        # Sort by last activity descending
        user_sessions.sort(key=lambda s: s.last_activity, reverse=True)

        return user_sessions[:limit]

    async def get_operational_context(self) -> OperationalContext:
        """
        Gather complete operational context for chat

        Returns:
            Comprehensive operational context
        """
        log = logger.bind(component="operational_context")
        log.info("Gathering operational context")

        context = OperationalContext()

        # Get all executions from orchestrator
        all_executions = list(self.orchestrator.executions.values())

        # Calculate statistics
        context.total_emails_processed = len(all_executions)

        # Count emails today
        today = datetime.now().date()
        context.emails_today = sum(
            1 for e in all_executions
            if e.started_at.date() == today
        )

        # Active and failed executions
        context.active_executions = sum(
            1 for e in all_executions
            if e.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        )
        context.failed_executions = sum(
            1 for e in all_executions
            if e.status == ExecutionStatus.FAILED
        )

        # Count actions
        for execution in all_executions:
            for action in execution.actions:
                if action.action_type == ActionType.CREATE_TASK:
                    context.total_tasks_created += 1
                elif action.action_type == ActionType.SCHEDULE_EVENT:
                    context.total_events_scheduled += 1

        # Recent emails (last 10)
        recent_executions = sorted(
            all_executions,
            key=lambda e: e.started_at,
            reverse=True
        )[:10]

        context.recent_emails = [
            {
                "email_id": e.email_id,
                "subject": e.metadata.get("subject", "N/A"),
                "sender": e.metadata.get("sender", "N/A"),
                "status": e.status.value,
                "started_at": e.started_at.isoformat(),
                "has_attachments": e.metadata.get("has_attachments", False)
            }
            for e in recent_executions
        ]

        # Current tasks (from recent executions)
        tasks = []
        for execution in recent_executions[:20]:
            for action in execution.actions:
                if action.action_type == ActionType.CREATE_TASK:
                    tasks.append({
                        "title": action.payload.get("title", "N/A"),
                        "description": action.payload.get("description", ""),
                        "due_date": action.payload.get("due_date"),
                        "priority": action.payload.get("priority", "medium"),
                        "status": action.status.value,
                        "created_at": action.created_at.isoformat()
                    })
        context.current_tasks = tasks[:15]

        # Upcoming deadlines (from deadline agent outputs)
        deadlines = []
        for execution in all_executions:
            for agent_output in execution.agent_outputs:
                if agent_output.agent_type == AgentType.DEADLINE:
                    deadline_findings = agent_output.findings.get("deadlines", [])
                    for deadline in deadline_findings:
                        deadlines.append({
                            "description": deadline.get("description", "N/A"),
                            "date": deadline.get("date"),
                            "email_subject": execution.metadata.get("subject", "N/A"),
                            "confidence": agent_output.confidence
                        })

        # Sort by date and get upcoming
        deadlines.sort(key=lambda d: d.get("date") or "9999-12-31")
        context.upcoming_deadlines = deadlines[:10]

        # Agent performance
        agent_stats = {}
        for agent_type in AgentType:
            agent_executions = []
            for execution in all_executions:
                for output in execution.agent_outputs:
                    if output.agent_type == agent_type:
                        agent_executions.append(output)

            if agent_executions:
                avg_time = sum(o.execution_time_ms for o in agent_executions) / len(agent_executions)
                avg_confidence = sum(o.confidence for o in agent_executions) / len(agent_executions)

                agent_stats[agent_type.value] = {
                    "executions": len(agent_executions),
                    "avg_execution_time_ms": round(avg_time, 2),
                    "avg_confidence": round(avg_confidence, 3)
                }

        context.agent_performance = agent_stats

        # System health
        context.system_health = {
            "dolphin_connected": self.orchestrator.dolphin_healthy,
            "nats_connected": self.orchestrator.nats_connected,
            "active_sessions": len(self.sessions),
            "total_messages": sum(len(msgs) for msgs in self.messages.values())
        }

        # High-risk items (failed executions, high-priority tasks)
        high_risk = []
        for execution in all_executions:
            if execution.status == ExecutionStatus.FAILED:
                high_risk.append({
                    "type": "failed_execution",
                    "subject": execution.metadata.get("subject", "N/A"),
                    "error": execution.error_message or "Unknown error",
                    "timestamp": execution.started_at.isoformat()
                })

        for task in context.current_tasks:
            if task.get("priority") == "high":
                high_risk.append({
                    "type": "high_priority_task",
                    "title": task["title"],
                    "due_date": task.get("due_date"),
                    "status": task["status"]
                })

        context.high_risk_items = high_risk[:10]

        log.info(
            "Operational context gathered",
            total_emails=context.total_emails_processed,
            active=context.active_executions,
            tasks=context.total_tasks_created
        )

        return context

    async def _build_system_prompt(self, context: OperationalContext) -> str:
        """
        Build system prompt with operational context

        Args:
            context: Operational context

        Returns:
            System prompt for Claude
        """
        prompt = f"""You are AUBS (Auburn Hills Business System) - John's personal assistant for Chili's #605 in Auburn Hills.

# WHO YOU ARE
You're a friendly, supportive operations assistant who helps John stay on top of everything at the restaurant. You've been designed specifically for Chili's operations and understand the unique challenges of running a high-volume casual dining restaurant.

# COMMUNICATION STYLE
- Be conversational and warm - you're John's trusted partner, not a robot
- Use "we" when talking about the restaurant ("we need to...", "our team...")
- Celebrate wins! If something's going well, acknowledge it
- Be direct but supportive when there are problems
- Keep responses concise unless John asks for details
- Use casual language when appropriate ("Hey, looks like...", "Heads up...")

# YOUR PRIORITIES (In Order)
1. **Deadlines from leadership** (DM, AMD, RVP emails) - These are CRITICAL
2. **Team issues** (callouts, no-shows, morale problems)
3. **Guest impact** (complaints, feedback, service issues)
4. **Performance metrics** (comp sales %, GWAP scores, operational numbers)
5. **Routine operations** (schedules, inventory, maintenance)

# RESTAURANT OPERATIONS KNOWLEDGE

## RAP Mobile Metrics You Understand:
- **Comp Sales %** - Year-over-year sales comparison
- **GWAP (Guest Wait and Prep)** - Speed of service scores
- **Labor %** - Labor cost as percentage of sales
- **Food Cost %** - Food cost tracking
- **Daily Sales** - Revenue tracking
- **Guest Count** - Traffic patterns
- **Check Average** - Per-guest spending

## HotSchedules Context:
- Manager schedules and shift coverage
- Team member availability and time-off requests
- Labor budget vs. actual hours
- Shift notes and communication

## Chili's-Specific Context:
- You know the store number is #605 in Auburn Hills
- You understand Brinker corporate structure (DM → AMD → RVP)
- You're familiar with Chili's menu, operations, and standards
- You know the 5-pillar delegation system (but that can wait for now)

# CURRENT OPERATIONAL AWARENESS

## EMAIL PROCESSING STATUS
- Total emails processed: {context.total_emails_processed}
- Emails processed today: {context.emails_today}
- Active processing: {context.active_executions}
- Failed: {context.failed_executions}

## RECENT EMAILS ({len(context.recent_emails)} most recent)
"""
        for email in context.recent_emails[:5]:
            prompt += f"\n- From: {email['sender']}"
            prompt += f"\n  Subject: {email['subject']}"
            prompt += f"\n  Status: {email['status']}"
            prompt += f"\n  Time: {email['started_at']}"

        prompt += f"\n\n## CURRENT TASKS ({len(context.current_tasks)} tasks)"
        for task in context.current_tasks[:5]:
            prompt += f"\n- {task['title']} (Priority: {task['priority']})"
            if task.get('due_date'):
                prompt += f" - Due: {task['due_date']}"

        prompt += f"\n\n## UPCOMING DEADLINES ({len(context.upcoming_deadlines)} deadlines)"
        for deadline in context.upcoming_deadlines[:5]:
            prompt += f"\n- {deadline['description']}"
            if deadline.get('date'):
                prompt += f" - {deadline['date']}"

        prompt += "\n\n## AGENT PERFORMANCE"
        for agent_name, stats in context.agent_performance.items():
            prompt += f"\n- {agent_name.upper()}: {stats['executions']} runs, "
            prompt += f"avg {stats['avg_execution_time_ms']}ms, "
            prompt += f"{stats['avg_confidence']*100:.0f}% confidence"

        prompt += "\n\n## SYSTEM STATUS"
        prompt += f"\n- Dolphin Scheduler: {'✓ Connected' if context.system_health['dolphin_connected'] else '✗ Disconnected'}"
        prompt += f"\n- NATS Messaging: {'✓ Connected' if context.system_health['nats_connected'] else '✗ Disconnected'}"
        prompt += f"\n- Active chat sessions: {context.system_health['active_sessions']}"

        if context.high_risk_items:
            prompt += f"\n\n## ⚠️ NEEDS YOUR ATTENTION ({len(context.high_risk_items)} items)"
            for item in context.high_risk_items[:3]:
                if item['type'] == 'failed_execution':
                    prompt += f"\n- Email processing failed: {item['subject']} - {item['error']}"
                elif item['type'] == 'high_priority_task':
                    prompt += f"\n- High priority task: {item['title']}"
                    if item.get('due_date'):
                        prompt += f" (Due: {item['due_date']})"

        prompt += """

# HOW TO RESPOND

**When John asks about priorities:**
- Lead with leadership deadlines first
- Mention team/staffing issues second
- Flag guest complaints/feedback third
- Cover performance metrics fourth
- Routine stuff last

**When John asks "What's urgent?":**
- List items by priority order above
- Include specific deadlines with dates/times
- Mention who sent the email if it's from leadership
- Be specific: "Your DM needs the manager schedule by Friday 5pm"

**When John asks about metrics:**
- Pull from operational data if available
- Reference trends ("Sales are up 3% vs. last week...")
- Flag anything concerning proactively
- Offer to dig deeper if needed

**When John needs help prioritizing:**
- Ask clarifying questions about his day
- Suggest time blocks for different task types
- Factor in his energy levels and meeting schedule
- Be realistic about what can actually get done

**Your tone should be:**
- Like a trusted assistant who "gets it"
- Supportive but honest
- Celebration when things go well
- Calm and solution-focused when things go wrong
- Never judgmental or condescending

Remember: You're here to make John's life easier, help him stay ahead of problems, and support him in running an excellent restaurant. Be the assistant he can count on to keep track of everything while he's focused on leading the team.
"""

        return prompt

    async def chat(
        self,
        session_id: UUID,
        message: str,
        stream: bool = False
    ) -> AsyncIterator[str]:
        """
        Send message and get response (with optional streaming)

        Args:
            session_id: Chat session ID
            message: User message
            stream: Whether to stream response

        Yields:
            Response chunks (if streaming) or full response
        """
        log = logger.bind(session_id=str(session_id))

        # Get or create session
        session = await self.get_session(session_id)
        if not session:
            log.warning("Session not found, creating new session")
            session = await self.create_session()

        # Update session activity
        session.last_activity = datetime.now()
        session.message_count += 1

        # Store user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=message
        )
        self.messages[session_id].append(user_msg)

        log.info("User message received", message_length=len(message))

        # Get operational context
        context = await self.get_operational_context()

        # Build system prompt
        system_prompt = await self._build_system_prompt(context)

        # Build conversation history
        conversation = []
        for msg in self.messages[session_id][-10:]:  # Last 10 messages for context
            if msg.role in ["user", "assistant"]:
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })

        log.info("Calling Claude API", stream=stream)

        try:
            if stream:
                # Streaming response
                response_chunks = []

                async with self.anthropic.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=conversation
                ) as stream_response:
                    async for chunk in stream_response.text_stream:
                        response_chunks.append(chunk)
                        yield chunk

                # Store complete assistant message
                full_response = "".join(response_chunks)
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response
                )
                self.messages[session_id].append(assistant_msg)

                log.info("Streaming response completed", response_length=len(full_response))

            else:
                # Non-streaming response
                response = await self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=conversation
                )

                content = response.content[0].text

                # Store assistant message
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=content
                )
                self.messages[session_id].append(assistant_msg)

                log.info("Response generated", response_length=len(content))

                yield content

        except Exception as e:
            log.error("Error generating response", error=str(e))
            error_msg = f"I encountered an error: {str(e)}"
            yield error_msg

    async def get_chat_history(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get chat history for session

        Args:
            session_id: Session ID
            limit: Maximum messages to return

        Returns:
            List of chat messages
        """
        messages = self.messages.get(session_id, [])
        return messages[-limit:] if messages else []

    async def delete_session(self, session_id: UUID) -> bool:
        """
        Delete chat session and its messages

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.messages:
                del self.messages[session_id]

            logger.info("Chat session deleted", session_id=str(session_id))
            return True

        return False

    async def get_context_summary(self) -> Dict[str, Any]:
        """
        Get summary of operational context

        Returns:
            Summary dictionary
        """
        context = await self.get_operational_context()

        return {
            "statistics": {
                "total_emails_processed": context.total_emails_processed,
                "emails_today": context.emails_today,
                "active_executions": context.active_executions,
                "failed_executions": context.failed_executions,
                "total_tasks_created": context.total_tasks_created,
                "total_events_scheduled": context.total_events_scheduled
            },
            "recent_activity": {
                "emails_count": len(context.recent_emails),
                "tasks_count": len(context.current_tasks),
                "deadlines_count": len(context.upcoming_deadlines)
            },
            "system_health": context.system_health,
            "high_risk_items_count": len(context.high_risk_items)
        }
