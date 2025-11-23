"""
Action Router
Routes actions to appropriate MCP tools based on context agent output
Implements confidence checking and high-risk detection
"""

import sys
import os
from typing import Dict, List, Any, Optional
from uuid import uuid4

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import httpx
import structlog

from src.config import AUBSSettings
from shared.models import (
    Action,
    ActionType,
    Execution,
    ExecutionStatus,
    TaskAction,
    CalendarAction,
    NotificationAction,
    RiskLevel
)

logger = structlog.get_logger()


class ActionRouter:
    """
    Routes actions to MCP tools with confidence checking
    Implements human review queue for high-risk actions
    """

    def __init__(self, settings: AUBSSettings):
        """
        Initialize action router

        Args:
            settings: AUBS configuration
        """
        self.settings = settings
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.high_risk_keywords = settings.get_high_risk_keywords()

    async def route(
        self,
        execution: Execution,
        context_output: Dict[str, Any]
    ) -> List[Action]:
        """
        Route actions based on context agent output

        Args:
            execution: Current execution
            context_output: Context agent output data

        Returns:
            List of created actions
        """
        log = logger.bind(execution_id=str(execution.id))
        log.info("Routing actions from context output")

        findings = context_output.get("findings", {})
        confidence = context_output.get("confidence", 0.0)
        recommendations = findings.get("recommendations", [])
        risk_level = findings.get("risk_assessment", RiskLevel.LOW)

        actions: List[Action] = []

        # Check if confidence meets threshold
        if confidence < self.settings.confidence_threshold:
            log.warning(
                "Confidence below threshold, creating human review action",
                confidence=confidence,
                threshold=self.settings.confidence_threshold
            )
            review_action = await self._create_human_review_action(
                execution,
                context_output,
                reason="Low confidence"
            )
            actions.append(review_action)
            return actions

        # Check for high-risk
        is_high_risk = self._detect_high_risk(context_output)
        if is_high_risk or risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            log.warning(
                "High-risk email detected, creating review action",
                risk_level=risk_level
            )
            review_action = await self._create_human_review_action(
                execution,
                context_output,
                reason=f"High risk: {risk_level}"
            )
            actions.append(review_action)
            return actions

        # Parse recommendations and create actions
        for recommendation in recommendations:
            action_type = recommendation.get("action_type")
            action_data = recommendation.get("data", {})
            action_confidence = recommendation.get("confidence", confidence)

            try:
                if action_type == "create_task":
                    action = await self._create_task_action(
                        execution,
                        action_data,
                        action_confidence
                    )
                    actions.append(action)

                elif action_type == "schedule_event":
                    action = await self._create_calendar_action(
                        execution,
                        action_data,
                        action_confidence
                    )
                    actions.append(action)

                elif action_type == "send_notification":
                    action = await self._create_notification_action(
                        execution,
                        action_data,
                        action_confidence
                    )
                    actions.append(action)

                else:
                    log.warning("Unknown action type", action_type=action_type)

            except Exception as e:
                log.error(
                    "Failed to create action",
                    action_type=action_type,
                    error=str(e)
                )

        log.info("Actions created successfully", action_count=len(actions))
        return actions

    def _detect_high_risk(self, context_output: Dict[str, Any]) -> bool:
        """
        Detect high-risk content based on keywords and patterns

        Args:
            context_output: Context agent output

        Returns:
            True if high-risk detected
        """
        findings = context_output.get("findings", {})
        synthesis = findings.get("synthesis", "").lower()

        # Check for high-risk keywords
        for keyword in self.high_risk_keywords:
            if keyword in synthesis:
                logger.info("High-risk keyword detected", keyword=keyword)
                return True

        return False

    async def _create_task_action(
        self,
        execution: Execution,
        data: Dict[str, Any],
        confidence: float
    ) -> TaskAction:
        """
        Create task action and route to Todoist MCP

        Args:
            execution: Current execution
            data: Task data
            confidence: Action confidence

        Returns:
            Created task action
        """
        log = logger.bind(execution_id=str(execution.id))

        action = TaskAction(
            execution_id=execution.id,
            payload={
                "title": data.get("title", "New Task"),
                "description": data.get("description", ""),
                "due_date": data.get("due_date"),
                "assignee": data.get("assignee"),
                "priority": data.get("priority", "medium")
            },
            confidence=confidence
        )

        if self.settings.mcp_todoist_enabled:
            try:
                # Call Todoist MCP tool
                result = await self._call_todoist_mcp(action.payload)
                action.status = ExecutionStatus.COMPLETED
                action.result = result
                log.info("Task created in Todoist", task_id=result.get("id"))
            except Exception as e:
                log.error("Failed to create task in Todoist", error=str(e))
                action.status = ExecutionStatus.FAILED
                action.result = {"error": str(e)}
        else:
            log.info("Todoist MCP disabled, task action created but not executed")

        return action

    async def _create_calendar_action(
        self,
        execution: Execution,
        data: Dict[str, Any],
        confidence: float
    ) -> CalendarAction:
        """
        Create calendar action and route to Google Calendar MCP

        Args:
            execution: Current execution
            data: Event data
            confidence: Action confidence

        Returns:
            Created calendar action
        """
        log = logger.bind(execution_id=str(execution.id))

        action = CalendarAction(
            execution_id=execution.id,
            payload={
                "title": data.get("title", "New Event"),
                "time": data.get("time"),
                "attendees": data.get("attendees", []),
                "location": data.get("location")
            },
            confidence=confidence
        )

        if self.settings.mcp_gcal_enabled:
            try:
                # Call Google Calendar MCP tool
                result = await self._call_gcal_mcp(action.payload)
                action.status = ExecutionStatus.COMPLETED
                action.result = result
                log.info("Event created in Google Calendar", event_id=result.get("id"))
            except Exception as e:
                log.error("Failed to create calendar event", error=str(e))
                action.status = ExecutionStatus.FAILED
                action.result = {"error": str(e)}
        else:
            log.info("Google Calendar MCP disabled, calendar action created but not executed")

        return action

    async def _create_notification_action(
        self,
        execution: Execution,
        data: Dict[str, Any],
        confidence: float
    ) -> NotificationAction:
        """
        Create notification action and route to Twilio MCP

        Args:
            execution: Current execution
            data: Notification data
            confidence: Action confidence

        Returns:
            Created notification action
        """
        log = logger.bind(execution_id=str(execution.id))

        action = NotificationAction(
            execution_id=execution.id,
            payload={
                "recipient": data.get("recipient", ""),
                "message": data.get("message", ""),
                "urgency": data.get("urgency", "normal"),
                "channel": data.get("channel", "sms")
            },
            confidence=confidence
        )

        if self.settings.mcp_twilio_enabled:
            try:
                # Call Twilio MCP tool
                result = await self._call_twilio_mcp(action.payload)
                action.status = ExecutionStatus.COMPLETED
                action.result = result
                log.info("Notification sent via Twilio", message_sid=result.get("sid"))
            except Exception as e:
                log.error("Failed to send notification", error=str(e))
                action.status = ExecutionStatus.FAILED
                action.result = {"error": str(e)}
        else:
            log.info("Twilio MCP disabled, notification action created but not executed")

        return action

    async def _create_human_review_action(
        self,
        execution: Execution,
        context_output: Dict[str, Any],
        reason: str
    ) -> Action:
        """
        Create human review action for manual intervention

        Args:
            execution: Current execution
            context_output: Context agent output
            reason: Reason for human review

        Returns:
            Human review action
        """
        log = logger.bind(execution_id=str(execution.id))
        log.info("Creating human review action", reason=reason)

        action = Action(
            execution_id=execution.id,
            action_type=ActionType.HUMAN_REVIEW,
            payload={
                "reason": reason,
                "context_output": context_output,
                "review_url": f"http://uitars:8080/review/{execution.id}",
                "priority": "high"
            },
            confidence=0.0,  # No confidence for review actions
            status=ExecutionStatus.PENDING
        )

        # Send to UI-TARS review queue
        try:
            await self._send_to_review_queue(execution, action)
            log.info("Review action sent to UI-TARS")
        except Exception as e:
            log.error("Failed to send to review queue", error=str(e))

        return action

    async def _call_todoist_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Todoist MCP tool

        Args:
            payload: Task data

        Returns:
            MCP response
        """
        # TODO: Implement actual MCP tool call
        # This would use the MCP tools service
        logger.info("Calling Todoist MCP tool", payload=payload)

        # Placeholder implementation
        return {
            "id": str(uuid4()),
            "status": "created",
            "tool": "todoist"
        }

    async def _call_gcal_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Google Calendar MCP tool

        Args:
            payload: Event data

        Returns:
            MCP response
        """
        # TODO: Implement actual MCP tool call
        logger.info("Calling Google Calendar MCP tool", payload=payload)

        # Placeholder implementation
        return {
            "id": str(uuid4()),
            "status": "created",
            "tool": "google_calendar"
        }

    async def _call_twilio_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Twilio MCP tool

        Args:
            payload: Notification data

        Returns:
            MCP response
        """
        # TODO: Implement actual MCP tool call
        logger.info("Calling Twilio MCP tool", payload=payload)

        # Placeholder implementation
        return {
            "sid": str(uuid4()),
            "status": "sent",
            "tool": "twilio"
        }

    async def _send_to_review_queue(
        self,
        execution: Execution,
        action: Action
    ):
        """
        Send action to UI-TARS review queue

        Args:
            execution: Current execution
            action: Review action
        """
        try:
            response = await self.http_client.post(
                f"{self.settings.ui_tars_url}/review/queue",
                json={
                    "execution_id": str(execution.id),
                    "action_id": str(action.id),
                    "payload": action.payload
                }
            )
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to send to review queue", error=str(e))
            raise

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
