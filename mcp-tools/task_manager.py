"""
Task Manager Integration

Provides integration with Todoist or similar task management systems.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger

from .base import MCPToolBase, MCPToolResult, MCPToolError, MCPToolConfig


class TaskPriority(int, Enum):
    """Task priority levels."""

    NONE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4


class TaskStatus(str, Enum):
    """Task status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    DELETED = "deleted"


class TaskManagerConfig(MCPToolConfig):
    """Configuration for Task Manager."""

    api_token: Optional[str] = Field(default=None, description="Todoist API token")
    base_url: str = Field(default="https://api.todoist.com/rest/v2", description="Todoist API base URL")
    default_project_id: Optional[str] = Field(default=None, description="Default project ID")


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""

    title: str = Field(..., description="Task title", min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, description="Task description")
    due_date: Optional[str] = Field(default=None, description="Due date (YYYY-MM-DD or natural language)")
    priority: TaskPriority = Field(default=TaskPriority.NONE, description="Task priority")
    labels: List[str] = Field(default_factory=list, description="Task labels/tags")
    assignee: Optional[str] = Field(default=None, description="Task assignee")
    project_id: Optional[str] = Field(default=None, description="Project ID")


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""

    title: Optional[str] = Field(default=None, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    due_date: Optional[str] = Field(default=None, description="Due date")
    priority: Optional[TaskPriority] = Field(default=None, description="Task priority")
    labels: Optional[List[str]] = Field(default=None, description="Task labels")
    assignee: Optional[str] = Field(default=None, description="Task assignee")


class TaskManager(MCPToolBase[TaskManagerConfig]):
    """
    Task Manager for Todoist integration.

    Provides methods for:
    - Creating tasks
    - Updating tasks
    - Assigning tasks
    - Setting priorities
    - Managing labels
    - Completing tasks
    """

    def _create_config(self, config: Dict[str, Any]) -> TaskManagerConfig:
        """Create TaskManager configuration."""
        return TaskManagerConfig(**config)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Todoist authentication."""
        headers = super()._get_headers()
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        return headers

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NONE,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> MCPToolResult:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            due_date: Due date (YYYY-MM-DD or natural language like "tomorrow")
            priority: Task priority (1-4)
            labels: List of labels/tags
            assignee: User ID to assign task to
            project_id: Project ID (uses default if not provided)

        Returns:
            MCPToolResult with created task data
        """
        try:
            request = TaskCreateRequest(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                labels=labels or [],
                assignee=assignee,
                project_id=project_id or self.config.default_project_id,
            )

            # Build request payload
            payload: Dict[str, Any] = {
                "content": request.title,
            }

            if request.description:
                payload["description"] = request.description

            if request.due_date:
                payload["due_string"] = request.due_date

            if request.priority != TaskPriority.NONE:
                payload["priority"] = request.priority.value

            if request.labels:
                payload["labels"] = request.labels

            if request.project_id:
                payload["project_id"] = request.project_id

            # Make API request
            response = await self._make_request(
                method="POST",
                endpoint="/tasks",
                data=payload,
            )

            task_data = response.json()

            logger.info(f"Created task: {task_data.get('id')} - {title}")

            return self._create_result(
                success=True,
                data={
                    "task_id": task_data.get("id"),
                    "title": task_data.get("content"),
                    "url": task_data.get("url"),
                    "created_at": task_data.get("created_at"),
                    "due": task_data.get("due"),
                    "priority": task_data.get("priority"),
                    "labels": task_data.get("labels", []),
                },
                tool="task_manager",
                action="create_task",
            )

        except MCPToolError as e:
            logger.error(f"Failed to create task: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error creating task: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        labels: Optional[List[str]] = None,
    ) -> MCPToolResult:
        """
        Update an existing task.

        Args:
            task_id: Task ID to update
            title: New task title
            description: New task description
            due_date: New due date
            priority: New priority
            labels: New labels

        Returns:
            MCPToolResult with updated task data
        """
        try:
            payload: Dict[str, Any] = {}

            if title:
                payload["content"] = title
            if description is not None:
                payload["description"] = description
            if due_date:
                payload["due_string"] = due_date
            if priority is not None:
                payload["priority"] = priority.value
            if labels is not None:
                payload["labels"] = labels

            if not payload:
                return self._create_result(
                    success=False,
                    error="No update fields provided",
                    error_code="NO_UPDATES",
                )

            response = await self._make_request(
                method="POST",
                endpoint=f"/tasks/{task_id}",
                data=payload,
            )

            task_data = response.json()

            logger.info(f"Updated task: {task_id}")

            return self._create_result(
                success=True,
                data={
                    "task_id": task_data.get("id"),
                    "title": task_data.get("content"),
                    "updated_fields": list(payload.keys()),
                },
                tool="task_manager",
                action="update_task",
            )

        except MCPToolError as e:
            logger.error(f"Failed to update task {task_id}: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error updating task: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def complete_task(self, task_id: str) -> MCPToolResult:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID to complete

        Returns:
            MCPToolResult
        """
        try:
            await self._make_request(
                method="POST",
                endpoint=f"/tasks/{task_id}/close",
            )

            logger.info(f"Completed task: {task_id}")

            return self._create_result(
                success=True,
                data={"task_id": task_id, "status": TaskStatus.COMPLETED.value},
                tool="task_manager",
                action="complete_task",
            )

        except MCPToolError as e:
            logger.error(f"Failed to complete task {task_id}: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error completing task: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def get_task(self, task_id: str) -> MCPToolResult:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            MCPToolResult with task data
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/tasks/{task_id}",
            )

            task_data = response.json()

            return self._create_result(
                success=True,
                data={
                    "task_id": task_data.get("id"),
                    "title": task_data.get("content"),
                    "description": task_data.get("description"),
                    "due": task_data.get("due"),
                    "priority": task_data.get("priority"),
                    "labels": task_data.get("labels", []),
                    "is_completed": task_data.get("is_completed", False),
                    "created_at": task_data.get("created_at"),
                    "url": task_data.get("url"),
                },
                tool="task_manager",
                action="get_task",
            )

        except MCPToolError as e:
            logger.error(f"Failed to get task {task_id}: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error getting task: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def add_labels(self, task_id: str, labels: List[str]) -> MCPToolResult:
        """
        Add labels to a task.

        Args:
            task_id: Task ID
            labels: List of labels to add

        Returns:
            MCPToolResult
        """
        try:
            # Get current task to merge labels
            current_task = await self.get_task(task_id)
            if not current_task.success:
                return current_task

            current_labels = current_task.data.get("labels", [])  # type: ignore
            new_labels = list(set(current_labels + labels))

            return await self.update_task(task_id, labels=new_labels)

        except Exception as e:
            logger.exception(f"Unexpected error adding labels: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def _health_check_impl(self) -> bool:
        """Check Todoist API health."""
        try:
            await self._make_request(method="GET", endpoint="/projects")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
