"""
AUBS FastAPI Application
Main entry point for the orchestration service
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from contextlib import asynccontextmanager

from src.config import settings
from src.simple_orchestrator import SimpleOrchestrator
from src.chat import AUBSChatService
from shared.models import EmailData, Execution, ExecutionStatus

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
EMAIL_PROCESSING_COUNTER = Counter(
    "aubs_emails_processed_total",
    "Total number of emails processed",
    ["status"]
)
PROCESSING_DURATION = Histogram(
    "aubs_processing_duration_seconds",
    "Email processing duration in seconds"
)
AGENT_EXECUTION_COUNTER = Counter(
    "aubs_agent_executions_total",
    "Total agent executions",
    ["agent_type", "status"]
)
ACTION_CREATED_COUNTER = Counter(
    "aubs_actions_created_total",
    "Total actions created",
    ["action_type"]
)

# Global orchestrator and chat service instances
orchestrator: Optional[SimpleOrchestrator] = None
chat_service: Optional[AUBSChatService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global orchestrator, chat_service

    # Startup
    logger.info("Starting Simple AUBS service (NO Dolphin)", version="2.1.0")
    orchestrator = SimpleOrchestrator(settings)
    await orchestrator.initialize()
    logger.info("Simple orchestrator initialized successfully")

    # Initialize chat service
    chat_service = AUBSChatService(settings, orchestrator)
    await chat_service.initialize()
    logger.info("AUBS chat service initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AUBS orchestration service")
    if chat_service:
        await chat_service.shutdown()
    if orchestrator:
        await orchestrator.shutdown()
    logger.info("AUBS orchestrator shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AUBS - Autonomous Unified Business System",
    description="Central orchestration service for email processing",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aubs",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "nats_connected": orchestrator.nats_connected if orchestrator else False,
        "chat_service_active": chat_service is not None
    }


@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    # Check if analyzer is initialized (core dependency)
    if not orchestrator.analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email analyzer not initialized"
        )

    return {"status": "ready"}


@app.post("/process-email", status_code=status.HTTP_202_ACCEPTED)
async def process_email(
    email: EmailData,
    background_tasks: BackgroundTasks
):
    """
    Process an email through the AUBS orchestration pipeline

    Args:
        email: Email data to process
        background_tasks: FastAPI background tasks

    Returns:
        Execution tracking information
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not available"
        )

    log = logger.bind(email_id=email.id, subject=email.subject)
    log.info("Received email for processing")

    try:
        # Start processing in background
        execution = await orchestrator.process_email(email)

        # Track metrics
        EMAIL_PROCESSING_COUNTER.labels(status="accepted").inc()

        log.info("Email processing started", execution_id=str(execution.id))

        return {
            "execution_id": str(execution.id),
            "email_id": email.id,
            "status": execution.status.value,
            "message": "Email processing started",
            "started_at": execution.started_at.isoformat()
        }

    except Exception as e:
        log.error("Failed to process email", error=str(e))
        EMAIL_PROCESSING_COUNTER.labels(status="failed").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email: {str(e)}"
        )


@app.get("/executions/{execution_id}")
async def get_execution_status(execution_id: UUID):
    """
    Get status of a specific execution

    Args:
        execution_id: Execution UUID

    Returns:
        Execution details and status
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not available"
        )

    log = logger.bind(execution_id=str(execution_id))

    try:
        execution = await orchestrator.get_execution_status(execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )

        log.info("Retrieved execution status", status=execution.status.value)

        return {
            "execution_id": str(execution.id),
            "email_id": execution.email_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error_message": execution.error_message,
            "agent_outputs": [
                {
                    "agent_type": output.agent_type.value,
                    "confidence": output.confidence,
                    "execution_time_ms": output.execution_time_ms
                }
                for output in execution.agent_outputs
            ],
            "actions": [
                {
                    "id": str(action.id),
                    "action_type": action.action_type.value,
                    "status": action.status.value,
                    "confidence": action.confidence
                }
                for action in execution.actions
            ],
            "metadata": execution.metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to retrieve execution status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve execution status: {str(e)}"
        )


@app.get("/executions")
async def list_executions(
    limit: int = 50,
    status_filter: Optional[ExecutionStatus] = None
):
    """
    List recent executions

    Args:
        limit: Maximum number of executions to return
        status_filter: Optional status filter

    Returns:
        List of executions
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not available"
        )

    try:
        executions = await orchestrator.list_executions(
            limit=limit,
            status_filter=status_filter
        )

        return {
            "count": len(executions),
            "executions": [
                {
                    "execution_id": str(exec.id),
                    "email_id": exec.email_id,
                    "status": exec.status.value,
                    "started_at": exec.started_at.isoformat(),
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None
                }
                for exec in executions
            ]
        }

    except Exception as e:
        logger.error("Failed to list executions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}"
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


@app.get("/config")
async def get_config():
    """Get current configuration (sanitized)"""
    return {
        "environment": settings.environment,
        "dolphin_url": settings.dolphin_url,
        "ui_tars_url": settings.ui_tars_url,
        "confidence_threshold": settings.confidence_threshold,
        "max_retries": settings.max_retries,
        "execution_timeout": settings.execution_timeout,
        "agents": {
            name: {
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "fallback_allowed": config.fallback_allowed
            }
            for name, config in settings.get_agent_configs().items()
        }
    }


# ========== Email Tools API Endpoints (v2) ==========

from src.tools.email_tools import get_emails, get_email_by_id, triage_email


class EmailListRequest(BaseModel):
    """Email list request parameters"""
    limit: int = 20
    filter_type: str = "ALL"
    days_back: int = 7
    sender_filter: Optional[str] = None
    subject_filter: Optional[str] = None


@app.get("/api/emails", status_code=status.HTTP_200_OK)
async def list_emails(
    limit: int = 20,
    filter_type: str = "ALL",
    days_back: int = 7,
    sender_filter: Optional[str] = None,
    subject_filter: Optional[str] = None
):
    """
    Get emails from Gmail via direct IMAP

    Args:
        limit: Maximum emails to return (default 20)
        filter_type: IMAP filter - ALL, UNSEEN, SEEN, FLAGGED
        days_back: Only get emails from last N days
        sender_filter: Filter by sender email/domain
        subject_filter: Filter by subject keywords

    Returns:
        List of emails with id, subject, sender, date, snippet
    """
    log = logger.bind(limit=limit, filter_type=filter_type)
    log.info("API: Fetching emails")

    try:
        emails = get_emails(
            limit=limit,
            filter_type=filter_type,
            days_back=days_back,
            sender_filter=sender_filter,
            subject_filter=subject_filter
        )

        log.info(f"API: Returning {len(emails)} emails")

        return {
            "count": len(emails),
            "emails": emails
        }

    except ValueError as e:
        log.error("Email fetch failed - configuration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        log.error("Email fetch failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@app.get("/api/emails/{email_id}", status_code=status.HTTP_200_OK)
async def get_single_email(email_id: str):
    """
    Get full email content by IMAP ID

    Args:
        email_id: IMAP email ID

    Returns:
        Full email with body, headers, attachments
    """
    log = logger.bind(email_id=email_id)
    log.info("API: Fetching email by ID")

    try:
        email_content = get_email_by_id(email_id)

        if not email_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email {email_id} not found"
            )

        return email_content

    except HTTPException:
        raise
    except Exception as e:
        log.error("Email fetch failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email: {str(e)}"
        )


@app.post("/api/emails/{email_id}/triage", status_code=status.HTTP_200_OK)
async def triage_single_email(email_id: str):
    """
    AI triage of a specific email

    Args:
        email_id: IMAP email ID

    Returns:
        Triage result with priority, category, suggested actions
    """
    log = logger.bind(email_id=email_id)
    log.info("API: Triaging email")

    try:
        result = await triage_email(email_id)
        log.info("API: Triage completed", urgency=result.get("urgency_score"))
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        log.error("Triage failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to triage email: {str(e)}"
        )


# ========== Chat API Endpoints ==========

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[UUID] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    session_id: UUID
    message: str
    timestamp: datetime


@app.post("/api/chat", status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Send chat message and get response

    Args:
        request: Chat request with message and optional session_id

    Returns:
        Chat response or streaming response
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    log = logger.bind(message_length=len(request.message))

    try:
        # Get or create session
        if request.session_id:
            session = await chat_service.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} not found"
                )
            session_id = request.session_id
        else:
            session = await chat_service.create_session()
            session_id = session.id

        log = log.bind(session_id=str(session_id))
        log.info("Processing chat message")

        if request.stream:
            # Streaming response
            async def generate_stream():
                async for chunk in chat_service.chat(session_id, request.message, stream=True):
                    # Send as Server-Sent Events
                    yield f"data: {chunk}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": str(session_id)
                }
            )
        else:
            # Non-streaming response
            response_text = ""
            async for chunk in chat_service.chat(session_id, request.message, stream=False):
                response_text = chunk

            log.info("Chat response generated", response_length=len(response_text))

            return ChatResponse(
                session_id=session_id,
                message=response_text,
                timestamp=datetime.utcnow()
            )

    except HTTPException:
        raise
    except Exception as e:
        log.error("Chat request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: UUID, limit: int = 50):
    """
    Get chat history for a session

    Args:
        session_id: Chat session ID
        limit: Maximum messages to return

    Returns:
        Chat message history
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    log = logger.bind(session_id=str(session_id))

    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        messages = await chat_service.get_chat_history(session_id, limit=limit)

        log.info("Retrieved chat history", message_count=len(messages))

        return {
            "session_id": str(session_id),
            "message_count": len(messages),
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to retrieve chat history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@app.get("/api/chat/sessions")
async def list_chat_sessions(user_id: str = "default", limit: int = 20):
    """
    List chat sessions for a user

    Args:
        user_id: User identifier
        limit: Maximum sessions to return

    Returns:
        List of chat sessions
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    try:
        sessions = await chat_service.list_sessions(user_id=user_id, limit=limit)

        logger.info("Retrieved chat sessions", session_count=len(sessions), user_id=user_id)

        return {
            "user_id": user_id,
            "session_count": len(sessions),
            "sessions": [
                {
                    "id": str(session.id),
                    "started_at": session.started_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "message_count": session.message_count,
                    "metadata": session.metadata
                }
                for session in sessions
            ]
        }

    except Exception as e:
        logger.error("Failed to list chat sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chat sessions: {str(e)}"
        )


@app.post("/api/chat/sessions", status_code=status.HTTP_201_CREATED)
async def create_chat_session(user_id: str = "default"):
    """
    Create a new chat session

    Args:
        user_id: User identifier

    Returns:
        Created session information
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    try:
        session = await chat_service.create_session(user_id=user_id)

        logger.info("Chat session created", session_id=str(session.id), user_id=user_id)

        return {
            "id": str(session.id),
            "user_id": session.user_id,
            "started_at": session.started_at.isoformat(),
            "message_count": session.message_count
        }

    except Exception as e:
        logger.error("Failed to create chat session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}"
        )


@app.delete("/api/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: UUID):
    """
    Delete a chat session

    Args:
        session_id: Session ID to delete

    Returns:
        No content on success
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    try:
        deleted = await chat_service.delete_session(session_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        logger.info("Chat session deleted", session_id=str(session_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete chat session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )


@app.get("/api/chat/context")
async def get_operational_context():
    """
    Get operational context summary

    Returns:
        Summary of current operational state
    """
    if not chat_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not available"
        )

    try:
        context_summary = await chat_service.get_context_summary()

        logger.info("Retrieved operational context summary")

        return context_summary

    except Exception as e:
        logger.error("Failed to retrieve operational context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operational context: {str(e)}"
        )


@app.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: UUID):
    """
    WebSocket endpoint for real-time chat streaming

    Args:
        websocket: WebSocket connection
        session_id: Chat session ID
    """
    if not chat_service:
        await websocket.close(code=1011, reason="Chat service not available")
        return

    await websocket.accept()

    log = logger.bind(session_id=str(session_id), transport="websocket")
    log.info("WebSocket chat connection established")

    try:
        # Verify session exists
        session = await chat_service.get_session(session_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": f"Session {session_id} not found"
            })
            await websocket.close(code=1008, reason="Session not found")
            return

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message = data.get("message")
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message is required"
                })
                continue

            log.info("WebSocket message received", message_length=len(message))

            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Stream response
            try:
                async for chunk in chat_service.chat(session_id, message, stream=True):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })

                # Send completion marker
                await websocket.send_json({
                    "type": "complete",
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                log.error("Error processing chat message", error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })

    except WebSocketDisconnect:
        log.info("WebSocket chat connection closed")
    except Exception as e:
        log.error("WebSocket error", error=str(e))
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass


# ========== Settings API Endpoints ==========

class SettingsUpdate(BaseModel):
    """Settings update request model"""
    email_filter: Optional[dict] = None
    models: Optional[dict] = None
    thresholds: Optional[dict] = None
    notifications: Optional[dict] = None
    integrations: Optional[dict] = None


@app.get("/api/settings")
async def get_settings():
    """
    Get all system settings including email filtering

    Returns:
        Complete system settings
    """
    try:
        # Load email ingestion settings from environment
        import os
        from dotenv import load_dotenv

        # Reload .env file to get latest values
        env_path = os.path.join(os.path.dirname(__file__), "../../infrastructure/docker/.env")
        load_dotenv(env_path, override=True)

        # Parse email filtering settings
        def parse_list(value, default=[]):
            if not value:
                return default
            return [item.strip() for item in value.split(",") if item.strip()]

        email_filter = {
            "allowed_domains": parse_list(os.getenv("ALLOWED_DOMAINS", "")),
            "allowed_senders": parse_list(os.getenv("ALLOWED_SENDERS", "")),
            "blocked_domains": parse_list(os.getenv("BLOCKED_DOMAINS", "")),
            "blocked_senders": parse_list(os.getenv("BLOCKED_SENDERS", "")),
            "polling_interval": int(os.getenv("EMAIL_POLLING_INTERVAL", "60"))
        }

        # Get agent configurations
        agent_configs = settings.get_agent_configs()
        models = {}
        for agent_name, config in agent_configs.items():
            models[agent_name] = {
                "provider": config.provider,
                "model_name": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "fallback_allowed": config.fallback_allowed
            }

        # Placeholder for other settings
        thresholds = {
            "high_confidence": settings.confidence_threshold,
            "medium_confidence": 0.7,
            "low_confidence": 0.5,
            "auto_process_threshold": settings.confidence_threshold
        }

        notifications = {
            "email_notifications": False,
            "slack_notifications": False,
            "notify_on_high_confidence": True,
            "notify_on_low_confidence": True,
            "notify_on_errors": True
        }

        integrations = {
            "gmail_enabled": True,
            "calendar_sync": False,
            "task_manager_integration": False
        }

        logger.info("Retrieved system settings")

        return {
            "settings": {
                "email_filter": email_filter,
                "models": models,
                "thresholds": thresholds,
                "notifications": notifications,
                "integrations": integrations
            }
        }

    except Exception as e:
        logger.error("Failed to retrieve settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@app.put("/api/settings")
async def update_settings(update: SettingsUpdate):
    """
    Update system settings

    Args:
        update: Settings to update

    Returns:
        Updated settings confirmation
    """
    try:
        import os
        from dotenv import load_dotenv, set_key

        env_path = os.path.join(os.path.dirname(__file__), "../../infrastructure/docker/.env")

        # Update email filter settings if provided
        if update.email_filter:
            email_filter = update.email_filter

            if "allowed_domains" in email_filter:
                domains = ",".join(email_filter["allowed_domains"])
                set_key(env_path, "ALLOWED_DOMAINS", domains)

            if "allowed_senders" in email_filter:
                senders = ",".join(email_filter["allowed_senders"])
                set_key(env_path, "ALLOWED_SENDERS", senders)

            if "blocked_domains" in email_filter:
                domains = ",".join(email_filter["blocked_domains"])
                set_key(env_path, "BLOCKED_DOMAINS", domains)

            if "blocked_senders" in email_filter:
                senders = ",".join(email_filter["blocked_senders"])
                set_key(env_path, "BLOCKED_SENDERS", senders)

            if "polling_interval" in email_filter:
                set_key(env_path, "EMAIL_POLLING_INTERVAL", str(email_filter["polling_interval"]))

        logger.info("Settings updated successfully")

        return {
            "message": "Settings updated successfully",
            "note": "Some settings require service restart to take effect"
        }

    except Exception as e:
        logger.error("Failed to update settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )


@app.get("/api/models/available")
async def get_available_models():
    """
    Get available models for each provider

    Returns:
        Dictionary of available models by provider
    """
    try:
        models = {
            "ollama": [
                "llama3.2:8b-instruct",
                "llama3.2:3b",
                "llama3.2-vision:11b",
                "mistral:7b",
                "phi3:mini",
                "qwen2.5:7b"
            ],
            "openai": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            "anthropic": [
                "claude-sonnet-4",
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]
        }

        return {"models": models}

    except Exception as e:
        logger.error("Failed to retrieve available models", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available models: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
