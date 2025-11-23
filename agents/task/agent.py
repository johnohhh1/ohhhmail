"""
ChiliHead OpsManager v2.1 - Task Categorizer Agent
Extracts action items, tasks, and priorities from emails
Model: ollama:llama3.2:8b-instruct
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from shared.models import AgentType, TaskInput, TaskOutput
from agents.base.agent_contract import BaseAgent
from agents.task.prompts import TASK_SYSTEM_PROMPT, TASK_USER_TEMPLATE


class TaskAgent(BaseAgent):
    """
    Task detection and categorization agent

    Responsibilities:
    - Extract action items from email content
    - Identify task priorities (low/medium/high/urgent)
    - Detect task assignees (who should do what)
    - Categorize task types (order, payment, maintenance, etc.)
    - Estimate task complexity/effort
    - Link tasks to deadlines
    """

    def __init__(self, config):
        """Initialize task agent"""
        super().__init__(config, AgentType.TASK)

    async def process(self, input_data: TaskInput) -> TaskOutput:
        """
        Process email for task extraction

        Args:
            input_data: TaskInput with email body and optional triage output

        Returns:
            TaskOutput with extracted tasks and priorities
        """
        # Create checkpoint at start
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="task_start",
                data={"email_id": input_data.email_id}
            )

        # Get context from triage if available
        triage_context = self._extract_triage_context(input_data.triage_output)

        # Prepare messages for LLM
        messages = [
            {
                "role": "user",
                "content": TASK_USER_TEMPLATE.format(
                    body=input_data.body[:3000],  # Limit to 3000 chars
                    context=triage_context
                )
            }
        ]

        # Generate task analysis
        logger.info(f"Extracting tasks for email {input_data.email_id}")

        response = await self._generate_with_llm(
            messages=messages,
            system_prompt=TASK_SYSTEM_PROMPT,
            temperature=0.4,  # Moderate temperature for creative task identification
            max_tokens=1000
        )

        # Parse response
        try:
            result = self._extract_json_from_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse task response: {e}")
            result = {
                "tasks": [],
                "priorities": {},
                "assignees": {}
            }

        # Normalize and enrich findings
        findings = self._normalize_findings(result)

        # Create analysis checkpoint
        if input_data.checkpoint_enabled:
            await self._create_checkpoint(
                session_id=input_data.session_id,
                checkpoint_name="task_analysis",
                data={
                    "tasks_found": len(findings["tasks"]),
                    "high_priority": len([t for t in findings["tasks"] if t.get("priority") == "high"])
                }
            )

        # Determine next actions
        next_actions = self._determine_next_actions(findings)

        # Calculate confidence
        confidence = self._calculate_confidence(findings)

        # Build output
        output = TaskOutput(
            findings=findings,
            confidence=confidence,
            next_actions=next_actions,
            execution_time_ms=0,  # Will be set by base execute()
            model_used=self.model_name,
            ui_tars_checkpoints=self.checkpoints
        )

        return output

    def _extract_triage_context(self, triage_output: Optional[Dict[str, Any]]) -> str:
        """
        Extract relevant context from triage output

        Args:
            triage_output: Triage agent output dict

        Returns:
            Context string for task extraction
        """
        if not triage_output:
            return "No triage context available."

        category = triage_output.get("category", "unknown")
        urgency = triage_output.get("urgency", 50)
        email_type = triage_output.get("type", "general")

        context = f"Email category: {category}, Type: {email_type}, Urgency: {urgency}/100"

        return context

    def _normalize_findings(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and enrich task findings

        Args:
            result: Raw LLM output

        Returns:
            Normalized findings dictionary
        """
        tasks = result.get("tasks", [])

        # Normalize each task
        normalized_tasks = []
        for i, task in enumerate(tasks):
            normalized_task = {
                "id": f"task_{i+1}",
                "description": task.get("description", ""),
                "priority": self._normalize_priority(task.get("priority", "medium")),
                "assignee": task.get("assignee"),
                "category": task.get("category", "general"),
                "estimated_effort": task.get("estimated_effort", "medium"),
                "deadline": task.get("deadline"),
                "dependencies": task.get("dependencies", []),
                "tags": task.get("tags", [])
            }

            # Only include tasks with descriptions
            if normalized_task["description"]:
                normalized_tasks.append(normalized_task)

        # Build priority mapping
        priorities = {}
        for task in normalized_tasks:
            priorities[task["id"]] = task["priority"]

        # Build assignee mapping
        assignees = {}
        for task in normalized_tasks:
            if task.get("assignee"):
                assignees[task["id"]] = task["assignee"]

        return {
            "tasks": normalized_tasks,
            "priorities": priorities,
            "assignees": assignees
        }

    def _normalize_priority(self, priority: str) -> str:
        """
        Normalize priority to standard values

        Args:
            priority: Raw priority string

        Returns:
            Normalized priority (low/medium/high/urgent)
        """
        priority = str(priority).lower().strip()

        if priority in ["urgent", "critical", "asap", "immediate"]:
            return "urgent"
        elif priority in ["high", "important"]:
            return "high"
        elif priority in ["low", "minor"]:
            return "low"
        else:
            return "medium"

    def _calculate_confidence(self, findings: Dict[str, Any]) -> float:
        """
        Calculate confidence in task extraction

        Args:
            findings: Task findings

        Returns:
            Confidence score 0.0-1.0
        """
        tasks = findings.get("tasks", [])

        if not tasks:
            return 0.0

        # Base confidence
        confidence = 0.6

        # Increase for tasks with assignees
        tasks_with_assignees = [t for t in tasks if t.get("assignee")]
        if tasks_with_assignees:
            confidence += 0.1 * (len(tasks_with_assignees) / len(tasks))

        # Increase for tasks with deadlines
        tasks_with_deadlines = [t for t in tasks if t.get("deadline")]
        if tasks_with_deadlines:
            confidence += 0.1 * (len(tasks_with_deadlines) / len(tasks))

        # Increase for categorized tasks
        tasks_with_categories = [t for t in tasks if t.get("category") != "general"]
        if tasks_with_categories:
            confidence += 0.1 * (len(tasks_with_categories) / len(tasks))

        # Increase for well-formed tasks (have multiple fields)
        well_formed = [
            t for t in tasks
            if t.get("assignee") and t.get("category") and t.get("priority")
        ]
        if well_formed:
            confidence += 0.1 * (len(well_formed) / len(tasks))

        return min(1.0, confidence)

    def _determine_next_actions(self, findings: Dict[str, Any]) -> List[str]:
        """
        Determine next actions based on extracted tasks

        Args:
            findings: Task findings

        Returns:
            List of next actions
        """
        actions = []

        tasks = findings.get("tasks", [])

        if not tasks:
            return actions

        # Create task tickets
        actions.append("create_task_tickets")

        # Check for urgent tasks
        urgent_tasks = [t for t in tasks if t.get("priority") == "urgent"]
        if urgent_tasks:
            actions.append("notify_urgent_tasks")

        # Check for tasks with assignees
        tasks_with_assignees = [t for t in tasks if t.get("assignee")]
        if tasks_with_assignees:
            actions.append("assign_tasks")

        # Check for tasks with deadlines
        tasks_with_deadlines = [t for t in tasks if t.get("deadline")]
        if tasks_with_deadlines:
            actions.append("schedule_reminders")

        return actions

    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort tasks by priority and deadline

        Args:
            tasks: List of task dictionaries

        Returns:
            Sorted list of tasks
        """
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}

        def task_sort_key(task: Dict[str, Any]) -> tuple:
            priority = task.get("priority", "medium")
            priority_score = priority_order.get(priority, 2)

            # Tasks with deadlines come first
            has_deadline = 0 if task.get("deadline") else 1

            return (has_deadline, priority_score)

        return sorted(tasks, key=task_sort_key)

    async def batch_extract(self, inputs: List[TaskInput]) -> List[TaskOutput]:
        """
        Extract tasks from multiple emails

        Args:
            inputs: List of task inputs

        Returns:
            List of task outputs
        """
        outputs = []

        for input_data in inputs:
            try:
                result = await self.execute(input_data)
                if result.success and result.output:
                    outputs.append(result.output)
                else:
                    logger.error(f"Task extraction failed for {input_data.email_id}: {result.error}")
            except Exception as e:
                logger.error(f"Exception processing {input_data.email_id}: {e}")

        logger.info(f"Batch extracted tasks from {len(outputs)}/{len(inputs)} emails")

        return outputs
