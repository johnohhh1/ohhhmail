"""
Dolphin DAG Builder
Constructs dynamic task graphs for email processing
"""

import sys
import os
from typing import Dict, List, Any, Optional

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import structlog

from src.config import AUBSSettings
from shared.models import EmailData, Execution, AgentType

logger = structlog.get_logger()


class EmailProcessingDAG:
    """
    Builds Dolphin DAG definitions for email processing
    Implements conditional agent inclusion and XCom data passing
    """

    def __init__(self, settings: AUBSSettings):
        """
        Initialize DAG builder

        Args:
            settings: AUBS configuration
        """
        self.settings = settings
        self.agent_configs = settings.get_agent_configs()

    async def build(self, email: EmailData, execution: Execution) -> Dict[str, Any]:
        """
        Build DAG definition for email processing

        Args:
            email: Email to process
            execution: Execution tracking object

        Returns:
            Dolphin DAG definition
        """
        log = logger.bind(
            email_id=email.id,
            execution_id=str(execution.id)
        )
        log.info("Building email processing DAG")

        has_attachments = len(email.attachments) > 0

        # Build task list
        tasks = []

        # 1. Triage Agent (always runs first)
        triage_task = self._build_triage_task(email, execution)
        tasks.append(triage_task)

        # 2. Vision Agent (conditional - only if attachments)
        if has_attachments:
            vision_task = self._build_vision_task(email, execution)
            tasks.append(vision_task)
            log.info("Vision agent included - email has attachments")

        # 3. Deadline Scanner (always runs, depends on triage)
        deadline_task = self._build_deadline_task(email, execution)
        tasks.append(deadline_task)

        # 4. Task Categorizer (conditional, based on triage output)
        task_task = self._build_task_categorizer_task(email, execution)
        tasks.append(task_task)

        # 5. Context Agent (CRITICAL - always runs last, depends on all)
        context_task = self._build_context_task(
            email,
            execution,
            has_vision=has_attachments
        )
        tasks.append(context_task)

        # Build DAG definition
        dag_definition = {
            "dag_id": execution.dag_id,
            "description": f"Email processing: {email.subject}",
            "schedule": None,  # One-time execution
            "max_retries": self.settings.max_retries,
            "timeout": self.settings.execution_timeout,
            "tasks": tasks,
            "metadata": {
                "email_id": email.id,
                "execution_id": str(execution.id),
                "subject": email.subject,
                "has_attachments": has_attachments
            }
        }

        log.info(
            "DAG definition built",
            task_count=len(tasks),
            includes_vision=has_attachments
        )

        return dag_definition

    def _build_triage_task(self, email: EmailData, execution: Execution) -> Dict[str, Any]:
        """Build triage agent task"""
        config = self.agent_configs["triage"]

        return {
            "task_id": "triage_agent",
            "agent_type": AgentType.TRIAGE.value,
            "depends_on": [],
            "operator": "AgentOperator",
            "config": {
                "agent_url": "http://agents:8001/triage",
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries
            },
            "input": {
                "email_id": email.id,
                "session_id": str(execution.id),
                "subject": email.subject,
                "body": email.body,
                "checkpoint_enabled": True
            },
            "xcom_push": True,  # Push output for downstream tasks
            "on_failure": "retry" if config.fallback_allowed else "fail"
        }

    def _build_vision_task(self, email: EmailData, execution: Execution) -> Dict[str, Any]:
        """Build vision agent task"""
        config = self.agent_configs["vision"]

        return {
            "task_id": "vision_agent",
            "agent_type": AgentType.VISION.value,
            "depends_on": ["triage_agent"],  # Runs after triage
            "operator": "AgentOperator",
            "config": {
                "agent_url": "http://agents:8002/vision",
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries
            },
            "input": {
                "email_id": email.id,
                "session_id": str(execution.id),
                "attachments": [
                    {
                        "filename": att.filename,
                        "content_type": att.content_type,
                        "size": att.size,
                        "url": att.url
                    }
                    for att in email.attachments
                ],
                "checkpoint_enabled": True
            },
            "xcom_push": True,
            "on_failure": "retry" if config.fallback_allowed else "fail"
        }

    def _build_deadline_task(self, email: EmailData, execution: Execution) -> Dict[str, Any]:
        """Build deadline scanner task"""
        config = self.agent_configs["deadline"]

        return {
            "task_id": "deadline_agent",
            "agent_type": AgentType.DEADLINE.value,
            "depends_on": ["triage_agent"],
            "operator": "AgentOperator",
            "config": {
                "agent_url": "http://agents:8003/deadline",
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries
            },
            "input": {
                "email_id": email.id,
                "session_id": str(execution.id),
                "body": email.body,
                "checkpoint_enabled": True
            },
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent.findings }}"
            },
            "on_failure": "retry" if config.fallback_allowed else "fail"
        }

    def _build_task_categorizer_task(
        self,
        email: EmailData,
        execution: Execution
    ) -> Dict[str, Any]:
        """Build task categorizer task"""
        config = self.agent_configs["task"]

        return {
            "task_id": "task_agent",
            "agent_type": AgentType.TASK.value,
            "depends_on": ["triage_agent"],
            "operator": "AgentOperator",
            "config": {
                "agent_url": "http://agents:8004/task",
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries
            },
            "input": {
                "email_id": email.id,
                "session_id": str(execution.id),
                "body": email.body,
                "checkpoint_enabled": True
            },
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent.findings }}"
            },
            "conditional": "{{ xcom.triage_agent.findings.type in ['task', 'action_required'] }}",
            "on_failure": "retry" if config.fallback_allowed else "fail"
        }

    def _build_context_task(
        self,
        email: EmailData,
        execution: Execution,
        has_vision: bool
    ) -> Dict[str, Any]:
        """
        Build context agent task (CRITICAL - NO FALLBACK)

        Args:
            email: Email data
            execution: Execution tracking
            has_vision: Whether vision agent is included

        Returns:
            Context agent task definition
        """
        config = self.agent_configs["context"]

        # Build dependencies - context depends on ALL upstream agents
        dependencies = ["triage_agent", "deadline_agent", "task_agent"]
        if has_vision:
            dependencies.append("vision_agent")

        # Build XCom pull configuration
        xcom_pull = {
            "triage_output": "{{ xcom.triage_agent }}",
            "deadline_output": "{{ xcom.deadline_agent }}",
            "task_output": "{{ xcom.task_agent }}"
        }

        if has_vision:
            xcom_pull["vision_output"] = "{{ xcom.vision_agent }}"

        return {
            "task_id": "context_agent",
            "agent_type": AgentType.CONTEXT.value,
            "depends_on": dependencies,
            "operator": "AgentOperator",
            "config": {
                "agent_url": "http://agents:8005/context",
                "model": config.model,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries
            },
            "input": {
                "email_id": email.id,
                "session_id": str(execution.id),
                "checkpoint_enabled": True,
                "historical_context": []  # TODO: Fetch from Supabase
            },
            "xcom_push": True,
            "xcom_pull": xcom_pull,
            "on_failure": "fail",  # CRITICAL - NO FALLBACK
            "critical": True,  # Mark as critical task
            "sla": config.timeout,
            "metadata": {
                "critical": True,
                "no_fallback": True,
                "requires_high_quality": True
            }
        }

    def get_task_graph_visualization(self, dag: Dict[str, Any]) -> str:
        """
        Generate ASCII visualization of task graph

        Args:
            dag: DAG definition

        Returns:
            ASCII art representation
        """
        tasks = dag.get("tasks", [])
        has_vision = any(t["task_id"] == "vision_agent" for t in tasks)

        if has_vision:
            return """
            Email Processing DAG (with Vision)

            [Triage Agent]
                  |
                  +-------+-------+
                  |       |       |
            [Vision] [Deadline] [Task]
                  |       |       |
                  +-------+-------+
                          |
                  [Context Agent]
                          |
                      [Actions]
            """
        else:
            return """
            Email Processing DAG (no Vision)

            [Triage Agent]
                  |
                  +-------+
                  |       |
            [Deadline] [Task]
                  |       |
                  +-------+
                      |
              [Context Agent]
                      |
                  [Actions]
            """
