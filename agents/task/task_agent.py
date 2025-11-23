"""
ChiliHead OpsManager v2.1 - Task Categorizer Agent
Identifies action items, assigns priorities, and suggests assignees
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from agents.base import BaseAgent
from shared.models import (
    AgentType,
    TaskInput,
    TaskOutput,
    AgentInput,
    AgentOutput
)
from shared.llm_config import LLMConfig


class TaskAgent(BaseAgent):
    """
    Task Categorizer Agent - Action item extraction and prioritization

    Responsibilities:
    - Identify actionable items in emails
    - Assign task priorities
    - Suggest appropriate assignees
    - Detect task dependencies
    - Estimate completion time
    """

    TASK_SYSTEM_PROMPT = """You are an expert task manager for restaurant operations.

Your job is to extract actionable tasks from emails and organize them effectively.

TASK IDENTIFICATION:
Identify tasks that require action, such as:
- Orders to place or approve
- Payments to process
- Schedules to create
- Issues to resolve
- Items to review or approve
- Calls/emails to send
- Meetings to schedule

PRIORITY LEVELS:
- CRITICAL: Immediate safety/health issues, critical system failures, urgent deadlines today
- HIGH: Time-sensitive orders, staff emergencies, important customer issues, deadlines this week
- MEDIUM: Regular operations, routine orders, general inquiries, deadlines next week
- LOW: Optional improvements, informational items, future planning

ASSIGNEE SUGGESTIONS:
Based on task type, suggest appropriate role:
- manager: Strategic decisions, vendor negotiations, staff issues
- kitchen_manager: Food orders, kitchen operations, menu changes
- foh_manager: Customer issues, reservations, front-of-house staff
- bookkeeper: Invoices, payments, financial records
- owner: Major decisions, significant expenses, legal matters

TASK DEPENDENCIES:
Identify if tasks must be completed in order or have prerequisites.

Respond with valid JSON:
{
  "tasks": [
    {
      "title": "<concise task title>",
      "description": "<full task description>",
      "priority": "critical|high|medium|low",
      "suggested_assignee": "<role>",
      "category": "ordering|payment|scheduling|customer_service|operations|other",
      "estimated_time_minutes": <number>,
      "requires_approval": <true|false>,
      "dependencies": ["<task titles this depends on>"],
      "deadline": "<deadline if extracted>",
      "confidence": <0.0-1.0>
    }
  ],
  "summary": "<overall summary of action items>",
  "total_estimated_time": <total minutes>,
  "blocking_tasks": ["<tasks that block others>"]
}"""

    def __init__(self, config: LLMConfig):
        """
        Initialize Task Categorizer Agent

        Args:
            config: LLM configuration
        """
        super().__init__(config, AgentType.TASK)

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process email for task extraction and categorization

        Args:
            input_data: TaskInput with email body and optional triage output

        Returns:
            TaskOutput with identified tasks and priorities
        """
        if not isinstance(input_data, TaskInput):
            raise ValueError("Input must be TaskInput")

        logger.info("Extracting and categorizing tasks")

        # Create checkpoint for task extraction start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="task_extraction_start",
                data={"body_length": len(input_data.body)}
            )

        # Build context-aware prompt
        context = ""
        if input_data.triage_output:
            category = input_data.triage_output.get("category", "unknown")
            urgency = input_data.triage_output.get("urgency", 50)
            context = f"\nEmail Category: {category}\nUrgency Score: {urgency}/100\n"

        # Extract tasks using LLM
        messages = [
            {
                "role": "user",
                "content": f"""Extract ALL actionable tasks from this email:
{context}
Email Content:
{input_data.body[:3000]}

Provide complete task analysis as JSON."""
            }
        ]

        # Generate task analysis
        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=self.TASK_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2000
        )

        # Parse response
        try:
            task_data = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse task response: {e}")
            task_data = {
                "tasks": [],
                "summary": "Failed to extract tasks",
                "total_estimated_time": 0,
                "blocking_tasks": []
            }

        # Enhance tasks with additional analysis
        enhanced_tasks = self._enhance_tasks(task_data.get("tasks", []), input_data.triage_output)

        # Build findings
        findings = {
            "tasks": enhanced_tasks,
            "priorities": self._build_priority_map(enhanced_tasks),
            "assignees": self._build_assignee_map(enhanced_tasks),
            "summary": task_data.get("summary", ""),
            "total_estimated_time": task_data.get("total_estimated_time", 0),
            "blocking_tasks": task_data.get("blocking_tasks", [])
        }

        # Calculate confidence
        confidence = self._calculate_confidence(task_data, enhanced_tasks)

        # Create checkpoint for task extraction completion
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="task_extraction_complete",
                data=findings
            )

        logger.success(f"Task extraction complete: {len(enhanced_tasks)} tasks identified")

        return TaskOutput(
            agent_type=AgentType.TASK,
            findings=findings,
            confidence=confidence,
            next_actions=["context_agent"],
            execution_time_ms=0,
            model_used=response.model_used,
            ui_tars_checkpoints=self.checkpoints
        )

    def _enhance_tasks(
        self,
        tasks: List[Dict[str, Any]],
        triage_output: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance task data with additional metadata

        Args:
            tasks: Raw task list from LLM
            triage_output: Optional triage context

        Returns:
            Enhanced task list
        """
        enhanced = []

        for idx, task in enumerate(tasks):
            # Add task ID
            task["id"] = f"task_{idx + 1}"

            # Validate priority
            task["priority"] = self._validate_priority(task.get("priority", "medium"))

            # Add source context
            if triage_output:
                task["email_category"] = triage_output.get("category")
                task["email_urgency"] = triage_output.get("urgency")

            # Normalize assignee
            task["suggested_assignee"] = self._normalize_assignee(
                task.get("suggested_assignee", "manager")
            )

            # Ensure confidence is set
            if "confidence" not in task:
                task["confidence"] = 0.7

            enhanced.append(task)

        return enhanced

    def _validate_priority(self, priority: str) -> str:
        """Validate and normalize priority"""
        valid_priorities = ["critical", "high", "medium", "low"]
        priority = priority.lower()

        if priority in valid_priorities:
            return priority

        logger.warning(f"Invalid priority '{priority}', defaulting to 'medium'")
        return "medium"

    def _normalize_assignee(self, assignee: str) -> str:
        """Normalize assignee role"""
        assignee_map = {
            "manager": "manager",
            "gm": "manager",
            "general manager": "manager",
            "kitchen": "kitchen_manager",
            "chef": "kitchen_manager",
            "kitchen manager": "kitchen_manager",
            "foh": "foh_manager",
            "front of house": "foh_manager",
            "server manager": "foh_manager",
            "accounting": "bookkeeper",
            "bookkeeper": "bookkeeper",
            "finance": "bookkeeper",
            "owner": "owner",
            "boss": "owner"
        }

        normalized = assignee_map.get(assignee.lower(), assignee)
        return normalized

    def _build_priority_map(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Build priority-to-task mapping

        Args:
            tasks: Enhanced task list

        Returns:
            Dictionary mapping priorities to task IDs
        """
        priority_map = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for task in tasks:
            priority = task.get("priority", "medium")
            task_id = task.get("id")

            if priority in priority_map:
                priority_map[priority].append(task_id)

        return priority_map

    def _build_assignee_map(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Build assignee-to-task mapping

        Args:
            tasks: Enhanced task list

        Returns:
            Dictionary mapping assignees to task IDs
        """
        assignee_map = {}

        for task in tasks:
            assignee = task.get("suggested_assignee", "manager")
            task_id = task.get("id")

            if assignee not in assignee_map:
                assignee_map[assignee] = []

            assignee_map[assignee].append(task_id)

        return assignee_map

    def _calculate_confidence(
        self,
        task_data: Dict[str, Any],
        tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence in task extraction

        Args:
            task_data: Raw task data from LLM
            tasks: Enhanced task list

        Returns:
            Confidence score (0.0-1.0)
        """
        if not tasks:
            return 0.3  # Low confidence if no tasks found

        # Average task confidences
        task_confidences = [t.get("confidence", 0.5) for t in tasks]
        avg_confidence = sum(task_confidences) / len(task_confidences)

        # Boost for having summary
        if task_data.get("summary"):
            avg_confidence += 0.1

        # Boost for dependency detection
        if task_data.get("blocking_tasks"):
            avg_confidence += 0.05

        return min(1.0, avg_confidence)
