"""
FastAPI Email Ingestion Service

REST API for email ingestion service with health checks and manual triggers.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import Settings
from .processor import EmailProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global processor instance
processor: Optional[EmailProcessor] = None
background_task: Optional[asyncio.Task] = None


class ProcessResponse(BaseModel):
    """Response model for process endpoint."""
    status: str
    message: str
    stats: dict


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str
    version: str
    settings: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.

    Handles startup and shutdown events.
    """
    global processor, background_task

    # Startup
    logger.info("Starting email ingestion service")

    # Load settings
    settings = Settings()

    # Configure logging level
    logging.getLogger().setLevel(settings.log_level)

    # Initialize processor
    processor = EmailProcessor(settings)
    await processor.start()

    # Start background processing if configured
    if settings.poll_interval_seconds > 0:
        logger.info("Starting background email processing")
        background_task = asyncio.create_task(processor.run_continuous())

    logger.info("Email ingestion service started")

    yield

    # Shutdown
    logger.info("Shutting down email ingestion service")

    # Cancel background task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

    # Stop processor
    if processor:
        await processor.stop()

    logger.info("Email ingestion service stopped")


# Create FastAPI app
app = FastAPI(
    title="Email Ingestion Service",
    description="Gmail IMAP email ingestion service with AUBS integration",
    version="1.0.0",
    lifespan=lifespan
)


def get_processor() -> EmailProcessor:
    """
    Dependency to get processor instance.

    Returns:
        EmailProcessor instance

    Raises:
        HTTPException: If processor not initialized
    """
    if not processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    return processor


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "Email Ingestion Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(proc: EmailProcessor = Depends(get_processor)):
    """
    Health check endpoint.

    Returns service health and configuration information.
    """
    settings = proc.settings

    return HealthResponse(
        status="healthy",
        service="email-ingestion",
        version="1.0.0",
        settings={
            "gmail_email": settings.gmail_email,
            "imap_host": settings.imap_host,
            "imap_port": settings.imap_port,
            "inbox_folder": settings.inbox_folder,
            "poll_interval_seconds": settings.poll_interval_seconds,
            "batch_size": settings.batch_size,
            "aubs_api_url": settings.aubs_api_url,
            "attachment_storage_path": settings.attachment_storage_path
        }
    )


@app.post("/process", response_model=ProcessResponse)
async def trigger_process(proc: EmailProcessor = Depends(get_processor)):
    """
    Manually trigger email processing.

    Processes unread emails immediately regardless of poll interval.
    """
    logger.info("Manual process triggered")

    try:
        stats = await proc.process_once()

        return ProcessResponse(
            status="success",
            message="Email processing completed",
            stats=stats
        )

    except Exception as e:
        logger.error(f"Error processing emails: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/stats", response_model=dict)
async def get_stats(proc: EmailProcessor = Depends(get_processor)):
    """
    Get attachment storage statistics.

    Returns information about stored attachments.
    """
    try:
        stats = proc.attachment_handler.get_storage_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/cleanup", response_model=dict)
async def cleanup_storage(proc: EmailProcessor = Depends(get_processor)):
    """
    Cleanup empty directories in attachment storage.

    Removes empty directories to keep storage organized.
    """
    try:
        removed_count = await asyncio.to_thread(
            proc.attachment_handler.cleanup_empty_directories
        )

        return {
            "status": "success",
            "message": f"Cleaned up {removed_count} empty directories"
        }
    except Exception as e:
        logger.error(f"Error cleaning up storage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Load settings for uvicorn
    settings = Settings()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )
