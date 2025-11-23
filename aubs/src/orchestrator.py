"""
AUBS Orchestrator - Main orchestration logic
Coordinates email processing through Dolphin DAG execution
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import httpx
import structlog
from nats.aio.client import Client as NATSClient

from src.config import AUBSSettings
from src.dag_builder import EmailProcessingDAG
from src.action_router import ActionRouter
from shared.models import (
    EmailData,
    Execution,
    ExecutionStatus,
    Action,
    AgentOutput,
    Event,
    EventType
)

logger = structlog.get_logger()


class AUBSOrchestrator:
    """
    Main AUBS orchestrator
    Manages email processing workflow through Dolphin DAG execution
    """

    def __init__(self, settings: AUBSSettings):
        """
        Initialize orchestrator

        Args:
            settings: AUBS configuration settings
        """
        self.settings = settings
        self.http_client: Optional[httpx.AsyncClient] = None
        self.nats_client: Optional[NATSClient] = None
        self.dag_builder = EmailProcessingDAG(settings)
        self.action_router = ActionRouter(settings)

        # In-memory execution tracking (should be moved to Supabase in production)
        self.executions: Dict[UUID, Execution] = {}

        # Health status
        self.dolphin_healthy = False
        self.nats_connected = False

    async def initialize(self):
        """Initialize orchestrator components"""
        log = logger.bind(component="orchestrator")
        log.info("Initializing AUBS orchestrator")

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Initialize NATS client
        try:
            self.nats_client = NATSClient()
            await self.nats_client.connect(self.settings.nats_url)
            self.nats_connected = True
            log.info("Connected to NATS", url=self.settings.nats_url)
        except Exception as e:
            log.warning("Failed to connect to NATS", error=str(e))
            self.nats_connected = False

        # Check Dolphin health
        await self._check_dolphin_health()

        log.info("AUBS orchestrator initialized successfully")

    async def shutdown(self):
        """Shutdown orchestrator gracefully"""
        log = logger.bind(component="orchestrator")
        log.info("Shutting down AUBS orchestrator")

        if self.http_client:
            await self.http_client.aclose()

        if self.nats_client and self.nats_connected:
            await self.nats_client.close()

        log.info("AUBS orchestrator shutdown complete")

    async def _check_dolphin_health(self) -> bool:
        """Check if Dolphin server is healthy"""
        try:
            response = await self.http_client.get(f"{self.settings.dolphin_url}/health")
            self.dolphin_healthy = response.status_code == 200
            return self.dolphin_healthy
        except Exception as e:
            logger.warning("Dolphin health check failed", error=str(e))
            self.dolphin_healthy = False
            return False

    async def process_email(self, email: EmailData) -> Execution:
        """
        Main entry point for email processing
        Creates and submits Dolphin DAG for execution

        Args:
            email: Email data to process

        Returns:
            Execution tracking object
        """
        log = logger.bind(email_id=email.id, subject=email.subject)
        log.info("Starting email processing")

        # Create execution tracking
        execution = Execution(
            email_id=email.id,
            dag_id=f"email_{email.id}",
            status=ExecutionStatus.PENDING,
            metadata={
                "subject": email.subject,
                "sender": email.sender,
                "recipient": email.recipient,
                "has_attachments": len(email.attachments) > 0,
                "attachment_count": len(email.attachments)
            }
        )
        self.executions[execution.id] = execution

        # Publish event
        await self._publish_event(
            EventType.EMAIL_RECEIVED,
            {
                "execution_id": str(execution.id),
                "email_id": email.id,
                "subject": email.subject
            },
            execution.id
        )

        # Build DAG
        try:
            dag_definition = await self._build_dag(email, execution)
            log.info("DAG built successfully", dag_id=execution.dag_id)
        except Exception as e:
            log.error("Failed to build DAG", error=str(e))
            execution.status = ExecutionStatus.FAILED
            execution.error_message = f"DAG build failed: {str(e)}"
            execution.completed_at = datetime.utcnow()
            return execution

        # Submit DAG to Dolphin
        try:
            dolphin_execution_id = await self._submit_dag(dag_definition)
            execution.dolphin_execution_id = dolphin_execution_id
            execution.status = ExecutionStatus.RUNNING
            log.info("DAG submitted to Dolphin", dolphin_execution_id=dolphin_execution_id)

            # Publish event
            await self._publish_event(
                EventType.DAG_SUBMITTED,
                {
                    "execution_id": str(execution.id),
                    "dolphin_execution_id": dolphin_execution_id,
                    "dag_id": execution.dag_id
                },
                execution.id
            )
        except Exception as e:
            log.error("Failed to submit DAG to Dolphin", error=str(e))
            execution.status = ExecutionStatus.FAILED
            execution.error_message = f"DAG submission failed: {str(e)}"
            execution.completed_at = datetime.utcnow()
            return execution

        # Start monitoring in background
        asyncio.create_task(self._monitor_execution(execution))

        return execution

    async def _build_dag(self, email: EmailData, execution: Execution) -> Dict[str, Any]:
        """
        Build Dolphin DAG for email processing

        Args:
            email: Email data
            execution: Execution tracking object

        Returns:
            DAG definition dictionary
        """
        log = logger.bind(execution_id=str(execution.id))
        log.info("Building email processing DAG")

        # Use DAG builder to create definition
        dag_definition = await self.dag_builder.build(email, execution)

        log.info(
            "DAG built",
            task_count=len(dag_definition.get("tasks", [])),
            has_vision=any(
                t.get("task_id") == "vision_agent"
                for t in dag_definition.get("tasks", [])
            )
        )

        return dag_definition

    async def _submit_dag(self, dag_definition: Dict[str, Any]) -> str:
        """
        Submit DAG to Dolphin for execution

        Args:
            dag_definition: DAG definition dictionary

        Returns:
            Dolphin execution ID
        """
        response = await self.http_client.post(
            f"{self.settings.dolphin_url}/dags/submit",
            json=dag_definition
        )
        response.raise_for_status()

        result = response.json()
        return result["execution_id"]

    async def _monitor_execution(self, execution: Execution):
        """
        Monitor DAG execution and process results

        Args:
            execution: Execution to monitor
        """
        log = logger.bind(
            execution_id=str(execution.id),
            dolphin_execution_id=execution.dolphin_execution_id
        )
        log.info("Starting execution monitoring")

        poll_interval = 5  # seconds
        max_duration = self.settings.execution_timeout

        start_time = datetime.utcnow()

        while True:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > max_duration:
                log.error("Execution timeout", elapsed_seconds=elapsed)
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Execution timeout"
                execution.completed_at = datetime.utcnow()
                break

            # Get execution status from Dolphin
            try:
                response = await self.http_client.get(
                    f"{self.settings.dolphin_url}/executions/{execution.dolphin_execution_id}"
                )
                response.raise_for_status()
                status_data = response.json()

                dolphin_status = status_data.get("status")
                log.debug("Dolphin execution status", status=dolphin_status)

                if dolphin_status == "completed":
                    # Process completed execution
                    await self._process_completion(execution, status_data)
                    break
                elif dolphin_status == "failed":
                    # Handle failure
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = status_data.get("error", "Unknown error")
                    execution.completed_at = datetime.utcnow()
                    log.error("Execution failed", error=execution.error_message)
                    break

            except Exception as e:
                log.error("Error monitoring execution", error=str(e))
                # Continue monitoring unless this is a critical error
                # In production, implement retry logic

            # Wait before next poll
            await asyncio.sleep(poll_interval)

        # Publish completion event
        await self._publish_event(
            EventType.EMAIL_COMPLETED,
            {
                "execution_id": str(execution.id),
                "status": execution.status.value,
                "error": execution.error_message
            },
            execution.id
        )

    async def _process_completion(self, execution: Execution, status_data: Dict[str, Any]):
        """
        Process completed execution results

        Args:
            execution: Completed execution
            status_data: Status data from Dolphin
        """
        log = logger.bind(execution_id=str(execution.id))
        log.info("Processing completed execution")

        # Extract agent outputs from task results
        task_results = status_data.get("task_results", {})

        # Parse agent outputs (implement based on actual Dolphin response format)
        # This is a simplified example
        for task_id, result in task_results.items():
            if "agent" in task_id:
                # Parse agent output
                # In production, deserialize to proper AgentOutput models
                pass

        # Route actions based on context agent output
        context_result = task_results.get("context_agent")
        if context_result:
            actions = await self._route_actions(execution, context_result)
            execution.actions.extend(actions)
            log.info("Actions created", action_count=len(actions))

        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.utcnow()
        log.info("Execution completed successfully")

    async def _route_actions(
        self,
        execution: Execution,
        context_output: Dict[str, Any]
    ) -> List[Action]:
        """
        Route actions to MCP tools based on context agent output

        Args:
            execution: Current execution
            context_output: Context agent output

        Returns:
            List of created actions
        """
        log = logger.bind(execution_id=str(execution.id))
        log.info("Routing actions from context output")

        actions = await self.action_router.route(execution, context_output)

        # Publish action events
        for action in actions:
            await self._publish_event(
                f"actions.{action.action_type.value}.created",
                {
                    "action_id": str(action.id),
                    "execution_id": str(execution.id),
                    "action_type": action.action_type.value,
                    "confidence": action.confidence
                },
                execution.id
            )

        return actions

    async def _publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        correlation_id: Optional[UUID] = None
    ):
        """
        Publish event to NATS

        Args:
            event_type: Event type string
            event_data: Event data
            correlation_id: Optional correlation ID
        """
        if not self.nats_connected or not self.nats_client:
            logger.debug("NATS not connected, skipping event publish")
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
            logger.warning("Failed to publish event", event_type=event_type, error=str(e))

    async def get_execution_status(self, execution_id: UUID) -> Optional[Execution]:
        """
        Get execution status

        Args:
            execution_id: Execution UUID

        Returns:
            Execution object or None
        """
        return self.executions.get(execution_id)

    async def list_executions(
        self,
        limit: int = 50,
        status_filter: Optional[ExecutionStatus] = None
    ) -> List[Execution]:
        """
        List recent executions

        Args:
            limit: Maximum number to return
            status_filter: Optional status filter

        Returns:
            List of executions
        """
        executions = list(self.executions.values())

        if status_filter:
            executions = [e for e in executions if e.status == status_filter]

        # Sort by started_at descending
        executions.sort(key=lambda e: e.started_at, reverse=True)

        return executions[:limit]
