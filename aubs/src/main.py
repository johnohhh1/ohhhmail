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

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from contextlib import asynccontextmanager

from src.config import settings
from src.orchestrator import AUBSOrchestrator
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

# Global orchestrator instance
orchestrator: Optional[AUBSOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global orchestrator

    # Startup
    logger.info("Starting AUBS orchestration service", version="2.1.0")
    orchestrator = AUBSOrchestrator(settings)
    await orchestrator.initialize()
    logger.info("AUBS orchestrator initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AUBS orchestration service")
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
        "dolphin_connected": orchestrator.dolphin_healthy if orchestrator else False,
        "nats_connected": orchestrator.nats_connected if orchestrator else False
    }


@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )

    if not orchestrator.dolphin_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dolphin server not reachable"
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
