"""
Email Processing DAG
Defines the task graph for email processing using Dolphin scheduler
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from aubs.src.dag_builder import EmailProcessingDAG as DAGBuilder
from aubs.src.config import settings
from shared.models import EmailData, Execution, AgentType

import structlog

logger = structlog.get_logger()


class EmailProcessingDAG:
    """
    Email Processing DAG for Dolphin Scheduler
    Orchestrates the complete email processing pipeline:
    1. Triage Agent - Initial email classification
    2. Vision Agent - Attachment analysis (conditional)
    3. Deadline Agent - Deadline extraction
    4. Task Categorizer - Task identification
    5. Context Agent - Final synthesis and routing (CRITICAL)
    """

    DAG_ID = "email_processing_v1"

    @classmethod
    def get_dag_definition(cls) -> Dict[str, Any]:
        """
        Get DAG metadata and configuration
        Returns:
            DAG definition for Dolphin
        """
        return {
            "dag_id": cls.DAG_ID,
            "description": "Email processing and classification pipeline",
            "owner": "ohhhmail",
            "email_on_failure": False,
            "email_on_retry": False,
            "retries": settings.max_retries,
            "retry_delay": timedelta(minutes=5),
            "timeout": timedelta(seconds=settings.execution_timeout),
            "depends_on_past": False,
            "catchup": False,
            "tags": ["email", "processing", "critical"],
            "max_active_runs": 10,
        }

    @classmethod
    async def build_from_email(
        cls,
        email: EmailData,
        execution: Execution
    ) -> Dict[str, Any]:
        """
        Build DAG instance from email data
        Args:
            email: Email to process
            execution: Execution tracking object
        Returns:
            Complete DAG definition
        """
        log = logger.bind(
            email_id=email.id,
            execution_id=str(execution.id),
            dag_id=execution.dag_id
        )
        log.info("Building email processing DAG from email")

        # Use AUBS DAG builder for core logic
        builder = DAGBuilder(settings)
        dag_definition = await builder.build(email, execution)

        # Enhance with Dolphin-specific configuration
        dag_definition.update(cls.get_dag_definition())
        dag_definition["dag_id"] = execution.dag_id

        log.info(
            "DAG built successfully",
            task_count=len(dag_definition.get("tasks", [])),
            has_attachments=dag_definition.get("metadata", {}).get("has_attachments", False)
        )

        return dag_definition

    @classmethod
    def get_task_definitions(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all task definitions for the DAG
        Returns:
            Dictionary of task definitions by task_id
        """
        return {
            "triage_agent": cls._get_triage_task_config(),
            "vision_agent": cls._get_vision_task_config(),
            "deadline_agent": cls._get_deadline_task_config(),
            "task_agent": cls._get_task_agent_config(),
            "context_agent": cls._get_context_task_config(),
        }

    @classmethod
    def _get_triage_task_config(cls) -> Dict[str, Any]:
        """Triage agent task configuration"""
        config = settings.get_agent_configs()["triage"]
        return {
            "task_id": "triage_agent",
            "agent_type": AgentType.TRIAGE.value,
            "operator": "AgentOperator",
            "pool": "cpu_workers",
            "queue": "default",

            # Agent configuration
            "config": {
                "agent_url": "http://agents:8001/triage",
                "model": config.model,
                "provider": settings.triage_agent_provider,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries,
            },

            # Task configuration
            "task_config": {
                "retry_policy": {
                    "max_attempts": config.max_retries,
                    "backoff_type": "exponential",
                    "initial_delay": 1,
                    "max_delay": 60,
                },
                "fallback_allowed": config.fallback_allowed,
                "critical": False,
            },

            # Data passing
            "xcom_push": True,
            "on_failure": "retry" if config.fallback_allowed else "fail",

            # Task priority
            "priority_weight": 100,
            "weight_rule": "upstream",
        }

    @classmethod
    def _get_vision_task_config(cls) -> Dict[str, Any]:
        """Vision agent task configuration (conditional)"""
        config = settings.get_agent_configs()["vision"]
        return {
            "task_id": "vision_agent",
            "agent_type": AgentType.VISION.value,
            "operator": "AgentOperator",
            "pool": "gpu_workers",
            "queue": "default",

            # Agent configuration
            "config": {
                "agent_url": "http://agents:8002/vision",
                "model": config.model,
                "provider": settings.vision_agent_provider,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries,
            },

            # Task configuration
            "task_config": {
                "retry_policy": {
                    "max_attempts": config.max_retries,
                    "backoff_type": "exponential",
                    "initial_delay": 2,
                    "max_delay": 120,
                },
                "fallback_allowed": config.fallback_allowed,
                "critical": False,
            },

            # Conditional execution
            "trigger_rule": "all_success",
            "depends_on": ["triage_agent"],

            # Data passing
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent }}",
            },
            "on_failure": "retry" if config.fallback_allowed else "fail",

            # Task priority
            "priority_weight": 80,
            "weight_rule": "upstream",
        }

    @classmethod
    def _get_deadline_task_config(cls) -> Dict[str, Any]:
        """Deadline agent task configuration"""
        config = settings.get_agent_configs()["deadline"]
        return {
            "task_id": "deadline_agent",
            "agent_type": AgentType.DEADLINE.value,
            "operator": "AgentOperator",
            "pool": "cpu_workers",
            "queue": "default",

            # Agent configuration
            "config": {
                "agent_url": "http://agents:8003/deadline",
                "model": config.model,
                "provider": settings.deadline_agent_provider,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries,
            },

            # Task configuration
            "task_config": {
                "retry_policy": {
                    "max_attempts": config.max_retries,
                    "backoff_type": "exponential",
                    "initial_delay": 1,
                    "max_delay": 60,
                },
                "fallback_allowed": config.fallback_allowed,
                "critical": False,
            },

            # Dependency
            "depends_on": ["triage_agent"],

            # Data passing
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent }}",
            },
            "on_failure": "retry" if config.fallback_allowed else "fail",

            # Task priority
            "priority_weight": 85,
            "weight_rule": "upstream",
        }

    @classmethod
    def _get_task_agent_config(cls) -> Dict[str, Any]:
        """Task categorizer agent task configuration"""
        config = settings.get_agent_configs()["task"]
        return {
            "task_id": "task_agent",
            "agent_type": AgentType.TASK.value,
            "operator": "AgentOperator",
            "pool": "cpu_workers",
            "queue": "default",

            # Agent configuration
            "config": {
                "agent_url": "http://agents:8004/task",
                "model": config.model,
                "provider": settings.task_agent_provider,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries,
            },

            # Task configuration
            "task_config": {
                "retry_policy": {
                    "max_attempts": config.max_retries,
                    "backoff_type": "exponential",
                    "initial_delay": 1,
                    "max_delay": 60,
                },
                "fallback_allowed": config.fallback_allowed,
                "critical": False,
            },

            # Dependency
            "depends_on": ["triage_agent"],

            # Conditional execution based on triage output
            "trigger_rule": "all_success",
            "condition": "{{ xcom.triage_agent.findings.type in ['task', 'action_required'] }}",

            # Data passing
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent }}",
            },
            "on_failure": "retry" if config.fallback_allowed else "fail",

            # Task priority
            "priority_weight": 90,
            "weight_rule": "upstream",
        }

    @classmethod
    def _get_context_task_config(cls) -> Dict[str, Any]:
        """
        Context agent task configuration (CRITICAL - NO FALLBACK)
        This task must succeed - it synthesizes all agent outputs
        """
        config = settings.get_agent_configs()["context"]
        return {
            "task_id": "context_agent",
            "agent_type": AgentType.CONTEXT.value,
            "operator": "AgentOperator",
            "pool": "critical_workers",
            "queue": "critical",

            # Agent configuration
            "config": {
                "agent_url": "http://agents:8005/context",
                "model": config.model,
                "provider": settings.context_agent_provider,
                "timeout": config.timeout,
                "gpu": config.gpu,
                "max_retries": config.max_retries,
            },

            # Task configuration (CRITICAL)
            "task_config": {
                "retry_policy": {
                    "max_attempts": 1,  # NO RETRIES FOR CRITICAL
                    "backoff_type": "fixed",
                    "initial_delay": 0,
                    "max_delay": 0,
                },
                "fallback_allowed": False,  # NO FALLBACK
                "critical": True,
                "no_fallback": True,
                "requires_high_quality": True,
            },

            # Dependency on ALL upstream tasks
            "depends_on": [
                "triage_agent",
                "deadline_agent",
                "task_agent",
                # vision_agent is conditionally added based on attachments
            ],

            # Data passing from all agents
            "xcom_push": True,
            "xcom_pull": {
                "triage_output": "{{ xcom.triage_agent }}",
                "deadline_output": "{{ xcom.deadline_agent }}",
                "task_output": "{{ xcom.task_agent }}",
                # vision_output added conditionally
            },

            # Failure handling (strict)
            "on_failure": "fail",
            "trigger_rule": "all_success",

            # SLA and monitoring
            "sla": timedelta(seconds=config.timeout),
            "sla_miss_callback": "on_context_agent_sla_miss",

            # Task priority (highest)
            "priority_weight": 110,
            "weight_rule": "absolute",

            # Execution configuration
            "max_tries": 1,
            "pool_slots": 1,

            # Metadata
            "metadata": {
                "critical": True,
                "no_fallback": True,
                "requires_high_quality": True,
                "final_synthesis": True,
            },
        }

    @classmethod
    def get_conditional_dependencies(cls, has_attachments: bool) -> List[str]:
        """
        Get task dependencies based on email properties
        Args:
            has_attachments: Whether email has attachments
        Returns:
            List of dependent task IDs for context agent
        """
        dependencies = [
            "triage_agent",
            "deadline_agent",
            "task_agent",
        ]

        if has_attachments:
            dependencies.append("vision_agent")

        return dependencies

    @classmethod
    def get_conditional_xcom_pulls(cls, has_attachments: bool) -> Dict[str, str]:
        """
        Get XCom pulls based on email properties
        Args:
            has_attachments: Whether email has attachments
        Returns:
            Dictionary of XCom pull configurations
        """
        pulls = {
            "triage_output": "{{ xcom.triage_agent }}",
            "deadline_output": "{{ xcom.deadline_agent }}",
            "task_output": "{{ xcom.task_agent }}",
        }

        if has_attachments:
            pulls["vision_output"] = "{{ xcom.vision_agent }}"

        return pulls

    @classmethod
    def get_visualization(cls, has_attachments: bool = False) -> str:
        """
        Get ASCII visualization of task graph
        Args:
            has_attachments: Whether to show vision agent
        Returns:
            ASCII art representation
        """
        if has_attachments:
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
          [Context Agent] ← CRITICAL (no fallback)
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
      [Context Agent] ← CRITICAL (no fallback)
              |
          [Actions]
            """


# Export DAG instance for Dolphin
email_processing_dag = EmailProcessingDAG()
