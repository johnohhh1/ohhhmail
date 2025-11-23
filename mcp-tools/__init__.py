"""
MCP Tools Integration Package

Provides integrations for task management, calendar, SMS, and email operations.
"""

from typing import Dict, Any, Optional
from .base import MCPToolBase, MCPToolResult, MCPToolError
from .task_manager import TaskManager
from .calendar import CalendarManager
from .sms import SMSManager
from .email_client import EmailClient

__version__ = "1.0.0"

__all__ = [
    "MCPToolBase",
    "MCPToolResult",
    "MCPToolError",
    "TaskManager",
    "CalendarManager",
    "SMSManager",
    "EmailClient",
    "MCPToolsManager",
]


class MCPToolsManager:
    """
    Central manager for all MCP tools.
    Provides easy access to all integrated services.
    """

    def __init__(
        self,
        task_manager_config: Optional[Dict[str, Any]] = None,
        calendar_config: Optional[Dict[str, Any]] = None,
        sms_config: Optional[Dict[str, Any]] = None,
        email_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MCP Tools Manager.

        Args:
            task_manager_config: Configuration for task manager
            calendar_config: Configuration for calendar
            sms_config: Configuration for SMS
            email_config: Configuration for email client
        """
        self.task_manager = TaskManager(task_manager_config or {})
        self.calendar = CalendarManager(calendar_config or {})
        self.sms = SMSManager(sms_config or {})
        self.email = EmailClient(email_config or {})

    async def initialize(self) -> None:
        """Initialize all tools."""
        await self.task_manager.initialize()
        await self.calendar.initialize()
        await self.sms.initialize()
        await self.email.initialize()

    async def close(self) -> None:
        """Close all tools and cleanup resources."""
        await self.task_manager.close()
        await self.calendar.close()
        await self.sms.close()
        await self.email.close()

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health status of all tools.

        Returns:
            Dictionary with health status for each tool
        """
        return {
            "task_manager": await self.task_manager.health_check(),
            "calendar": await self.calendar.health_check(),
            "sms": await self.sms.health_check(),
            "email": await self.email.health_check(),
        }
