"""
AUBS Orchestrator - Simplified (NO Dolphin)
Direct LLM analysis for email triage
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from nats.aio.client import Client as NATSClient

from src.config import AUBSSettings
from src.email_analyzer import EmailAnalyzer
from shared.models import (
    EmailData,
    Execution,
    ExecutionStatus,
    Event,
    EventType
)

logger = structlog.get_logger()


class SimpleOrchestrator:
    """
    Simple AUBS orchestrator - NO Dolphin
    Direct LLM analysis only
    """

    def __init__(self, settings: AUBSSettings):
        self.settings = settings
        self.analyzer = None
        self.nats_client: Optional[NATSClient] = None

        # In-memory execution tracking
        self.executions: Dict[UUID, Execution] = {}

        self.nats_connected = False

    async def initialize(self):
        """Initialize orchestrator"""
        log = logger.bind(component="orchestrator")
        log.info("Initializing Simple AUBS orchestrator (NO Dolphin)")

        # Initialize email analyzer
        try:
            self.analyzer = EmailAnalyzer()
            log.info("Email analyzer initialized")
        except Exception as e:
            log.error("Failed to initialize analyzer", error=str(e))
            raise

        # Initialize NATS
        try:
            self.nats_client = NATSClient()
            await self.nats_client.connect(self.settings.nats_url)
            self.nats_connected = True
            log.info("Connected to NATS", url=self.settings.nats_url)
        except Exception as e:
            log.warning("Failed to connect to NATS", error=str(e))

        log.info("Simple orchestrator initialized")

    async def shutdown(self):
        """Shutdown gracefully"""
        if self.nats_client and self.nats_connected:
            await self.nats_client.close()

    async def process_email(self, email: EmailData) -> Execution:
        """
        Process email with direct LLM analysis

        Args:
            email: Email to process

        Returns:
            Execution with results
        """
        log = logger.bind(email_id=email.id, subject=email.subject)
        log.info("Processing email")

        # Create execution
        execution = Execution(
            email_id=email.id,
            dag_id=f"email_{email.id}",
            status=ExecutionStatus.PENDING,
            metadata={
                "subject": email.subject,
                "sender": email.sender,
                "recipient": email.recipient,
                "has_attachments": len(email.attachments) > 0
            }
        )
        self.executions[execution.id] = execution

        # Publish start event
        await self._publish_event(
            EventType.EMAIL_RECEIVED,
            {
                "execution_id": str(execution.id),
                "email_id": email.id,
                "subject": email.subject
            },
            execution.id
        )

        # Analyze with LLM
        try:
            execution.status = ExecutionStatus.RUNNING
            log.info("Starting LLM analysis")

            triage_result = await self.analyzer.analyze(email)

            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.metadata["triage_result"] = triage_result

            log.info(
                "Analysis completed",
                urgency=triage_result.get("urgency_score"),
                confidence=triage_result.get("confidence"),
                category=triage_result.get("category")
            )

            # Publish completion
            await self._publish_event(
                EventType.EXECUTION_COMPLETED,
                {
                    "execution_id": str(execution.id),
                    "email_id": email.id,
                    "triage_result": triage_result
                },
                execution.id
            )

        except Exception as e:
            log.error("Analysis failed", error=str(e))
            execution.status = ExecutionStatus.FAILED
            execution.error_message = f"Analysis failed: {str(e)}"
            execution.completed_at = datetime.utcnow()

        return execution

    async def _publish_event(
        self,
        event_type: str,
        event_data: Dict,
        correlation_id: Optional[UUID] = None
    ):
        """Publish event to NATS"""
        if not self.nats_connected or not self.nats_client:
            return

        event = Event(
            event_type=event_type,
            event_source="aubs",
            event_data=event_data,
            correlation_id=correlation_id
        )

        try:
            await self.nats_client.publish(
                event_type.replace(".", "_"),
                event.model_dump_json().encode()
            )
        except Exception as e:
            logger.warning("Failed to publish event", error=str(e))

    async def get_execution_status(self, execution_id: UUID) -> Optional[Execution]:
        """Get execution status"""
        return self.executions.get(execution_id)

    async def list_executions(
        self,
        limit: int = 50,
        status_filter: Optional[ExecutionStatus] = None
    ) -> List[Execution]:
        """List recent executions"""
        executions = list(self.executions.values())

        if status_filter:
            executions = [e for e in executions if e.status == status_filter]

        executions.sort(key=lambda e: e.started_at, reverse=True)
        return executions[:limit]
