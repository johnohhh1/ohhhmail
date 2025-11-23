"""
ChiliHead OpsManager v2.1 - Dolphin Worker Integration Base
Base class for integrating agents with Apache Dolphin Scheduler
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from pydolphinscheduler.core.task import Task
from shared.models import AgentInput, AgentOutput, ExecutionStatus


class DolphinWorkerBase:
    """
    Base class for Dolphin Scheduler worker integration

    Provides common functionality for registering agents as Dolphin tasks
    and handling execution lifecycle
    """

    def __init__(
        self,
        task_name: str,
        queue: str = "default",
        timeout: int = 300,
        retries: int = 3
    ):
        """
        Initialize Dolphin worker base

        Args:
            task_name: Name of the task in Dolphin
            queue: Worker queue name
            timeout: Task timeout in seconds
            retries: Number of retry attempts
        """
        self.task_name = task_name
        self.queue = queue
        self.timeout = timeout
        self.retries = retries
        self.execution_id: Optional[str] = None
        self.status = ExecutionStatus.PENDING

    @abstractmethod
    async def execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task with given context

        Args:
            context: Dolphin task context with input parameters

        Returns:
            Task execution result
        """
        pass

    def create_dolphin_task(
        self,
        workflow_name: str,
        task_params: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create Dolphin Scheduler task definition

        Args:
            workflow_name: Name of the parent workflow
            task_params: Additional task parameters

        Returns:
            Configured Dolphin Task object
        """
        from pydolphinscheduler.tasks.python import Python

        task_params = task_params or {}

        task = Python(
            name=self.task_name,
            code=self._generate_task_code(),
            **task_params
        )

        logger.info(f"Created Dolphin task: {self.task_name}")

        return task

    def _generate_task_code(self) -> str:
        """
        Generate Python code to execute in Dolphin worker

        Returns:
            Python code as string
        """
        return f"""
import asyncio
from {self.__class__.__module__} import {self.__class__.__name__}

async def main():
    worker = {self.__class__.__name__}(
        task_name="{self.task_name}",
        queue="{self.queue}",
        timeout={self.timeout},
        retries={self.retries}
    )

    # Get context from Dolphin
    context = {{}}  # Dolphin injects this

    result = await worker.execute_task(context)
    print(f"Task completed: {{result}}")

if __name__ == "__main__":
    asyncio.run(main())
"""

    async def report_progress(self, progress: int, message: str) -> None:
        """
        Report task progress to Dolphin

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        logger.info(f"[{self.task_name}] Progress {progress}%: {message}")

        # TODO: Integrate with Dolphin progress reporting API
        # For now, just log

    async def update_status(self, status: ExecutionStatus, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update task execution status

        Args:
            status: New execution status
            metadata: Optional metadata to attach
        """
        self.status = status
        logger.info(f"[{self.task_name}] Status updated to {status.value}")

        if metadata:
            logger.debug(f"[{self.task_name}] Metadata: {metadata}")

        # TODO: Push status to NATS or Redis for real-time updates

    def get_task_context(self, dolphin_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate task context from Dolphin

        Args:
            dolphin_context: Raw context from Dolphin

        Returns:
            Validated and structured context
        """
        # Extract common parameters
        context = {
            "email_id": dolphin_context.get("email_id"),
            "session_id": dolphin_context.get("session_id"),
            "workflow_id": dolphin_context.get("workflow_id"),
            "upstream_outputs": dolphin_context.get("upstream_outputs", {}),
            "checkpoint_enabled": dolphin_context.get("checkpoint_enabled", True)
        }

        # Validate required fields
        if not context["email_id"]:
            raise ValueError("Missing required parameter: email_id")

        if not context["session_id"]:
            raise ValueError("Missing required parameter: session_id")

        return context

    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task execution error

        Args:
            error: Exception that occurred
            context: Task context

        Returns:
            Error result dictionary
        """
        logger.error(f"[{self.task_name}] Error: {error}")

        await self.update_status(
            ExecutionStatus.FAILED,
            metadata={"error": str(error), "context": context}
        )

        return {
            "success": False,
            "error": str(error),
            "task_name": self.task_name,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_success(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful task execution

        Args:
            result: Task execution result
            context: Task context

        Returns:
            Success result dictionary
        """
        logger.success(f"[{self.task_name}] Completed successfully")

        await self.update_status(
            ExecutionStatus.COMPLETED,
            metadata={"result": result, "context": context}
        )

        return {
            "success": True,
            "result": result,
            "task_name": self.task_name,
            "timestamp": datetime.now().isoformat()
        }


class AgentWorker(DolphinWorkerBase):
    """
    Specialized worker for AI agents

    Integrates BaseAgent with Dolphin Scheduler
    """

    def __init__(
        self,
        agent,
        task_name: str,
        queue: str = "ai_agents",
        timeout: int = 300,
        retries: int = 3
    ):
        """
        Initialize agent worker

        Args:
            agent: BaseAgent instance
            task_name: Task name in Dolphin
            queue: Worker queue
            timeout: Task timeout
            retries: Retry attempts
        """
        super().__init__(task_name, queue, timeout, retries)
        self.agent = agent

    async def execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task

        Args:
            context: Dolphin task context

        Returns:
            Agent execution result
        """
        try:
            # Extract and validate context
            task_context = self.get_task_context(context)

            # Create agent input (agent-specific implementation needed)
            agent_input = self._create_agent_input(task_context)

            # Report progress
            await self.report_progress(10, f"Starting {self.agent.agent_type.value} agent")

            # Execute agent
            result = await self.agent.execute(agent_input)

            await self.report_progress(90, "Agent processing complete")

            if result.success:
                return await self.handle_success(
                    result.model_dump(),
                    task_context
                )
            else:
                return await self.handle_error(
                    Exception(result.error),
                    task_context
                )

        except Exception as e:
            return await self.handle_error(e, context)

    @abstractmethod
    def _create_agent_input(self, context: Dict[str, Any]) -> AgentInput:
        """
        Create agent-specific input from task context

        Args:
            context: Task context

        Returns:
            Agent input object
        """
        pass
