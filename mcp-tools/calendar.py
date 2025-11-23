"""
Calendar Manager Integration

Provides integration with Google Calendar API.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
from loguru import logger

from .base import MCPToolBase, MCPToolResult, MCPToolError, MCPToolConfig


class CalendarConfig(MCPToolConfig):
    """Configuration for Calendar Manager."""

    credentials_file: Optional[str] = Field(default=None, description="Path to Google credentials JSON")
    calendar_id: str = Field(default="primary", description="Calendar ID to use")
    base_url: str = Field(default="https://www.googleapis.com/calendar/v3", description="Google Calendar API URL")
    send_notifications: bool = Field(default=True, description="Send email notifications for events")


class EventAttendee(BaseModel):
    """Event attendee model."""

    email: EmailStr
    display_name: Optional[str] = None
    optional: bool = False
    response_status: Optional[str] = None


class EventCreateRequest(BaseModel):
    """Request model for creating a calendar event."""

    title: str = Field(..., description="Event title", min_length=1)
    description: Optional[str] = Field(default=None, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    duration_minutes: int = Field(default=60, description="Event duration in minutes", gt=0)
    attendees: List[EventAttendee] = Field(default_factory=list, description="Event attendees")
    location: Optional[str] = Field(default=None, description="Event location")
    send_invitations: bool = Field(default=True, description="Send email invitations to attendees")


class CalendarManager(MCPToolBase[CalendarConfig]):
    """
    Calendar Manager for Google Calendar integration.

    Provides methods for:
    - Creating events
    - Updating events
    - Deleting events
    - Adding attendees
    - Checking conflicts
    - Sending invitations
    """

    def _create_config(self, config: Dict[str, Any]) -> CalendarConfig:
        """Create Calendar configuration."""
        return CalendarConfig(**config)

    async def _on_initialize(self) -> None:
        """Initialize Google Calendar API client."""
        # In production, this would setup OAuth2 credentials
        # For now, we'll use API key authentication
        logger.info("Calendar manager initialized")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Google API authentication."""
        headers = super()._get_headers()
        if self.config.api_key:
            # Google uses API key in query params, but we'll keep this for consistency
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _format_datetime(self, dt: datetime) -> Dict[str, str]:
        """
        Format datetime for Google Calendar API.

        Args:
            dt: Datetime to format

        Returns:
            Dictionary with dateTime and timeZone
        """
        return {
            "dateTime": dt.isoformat(),
            "timeZone": "UTC",
        }

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = 60,
        description: Optional[str] = None,
        attendees: Optional[List[Dict[str, Any]]] = None,
        location: Optional[str] = None,
        send_invitations: bool = True,
    ) -> MCPToolResult:
        """
        Create a calendar event.

        Args:
            title: Event title
            start_time: Event start time
            duration_minutes: Event duration in minutes
            description: Event description
            attendees: List of attendee dictionaries with 'email' and optional 'displayName'
            location: Event location
            send_invitations: Whether to send email invitations

        Returns:
            MCPToolResult with created event data
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)

            # Build event payload
            event_payload: Dict[str, Any] = {
                "summary": title,
                "start": self._format_datetime(start_time),
                "end": self._format_datetime(end_time),
            }

            if description:
                event_payload["description"] = description

            if location:
                event_payload["location"] = location

            if attendees:
                event_payload["attendees"] = [
                    {
                        "email": att.get("email"),
                        "displayName": att.get("displayName", att.get("email")),
                        "optional": att.get("optional", False),
                    }
                    for att in attendees
                ]

            # Add reminders
            event_payload["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},  # 1 day before
                    {"method": "popup", "minutes": 30},  # 30 minutes before
                ],
            }

            # Make API request
            params = {"sendNotifications": "true" if send_invitations else "false"}

            response = await self._make_request(
                method="POST",
                endpoint=f"/calendars/{self.config.calendar_id}/events",
                data=event_payload,
                params=params,
            )

            event_data = response.json()

            logger.info(f"Created calendar event: {event_data.get('id')} - {title}")

            return self._create_result(
                success=True,
                data={
                    "event_id": event_data.get("id"),
                    "title": event_data.get("summary"),
                    "start": event_data.get("start"),
                    "end": event_data.get("end"),
                    "html_link": event_data.get("htmlLink"),
                    "hangout_link": event_data.get("hangoutLink"),
                    "attendees": event_data.get("attendees", []),
                    "created": event_data.get("created"),
                },
                tool="calendar",
                action="create_event",
            )

        except MCPToolError as e:
            logger.error(f"Failed to create calendar event: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error creating event: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        send_notifications: bool = True,
    ) -> MCPToolResult:
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID to update
            title: New event title
            start_time: New start time
            duration_minutes: New duration
            description: New description
            location: New location
            send_notifications: Send notifications about the update

        Returns:
            MCPToolResult with updated event data
        """
        try:
            # First, get the current event
            get_response = await self._make_request(
                method="GET",
                endpoint=f"/calendars/{self.config.calendar_id}/events/{event_id}",
            )

            current_event = get_response.json()
            updated_event = current_event.copy()

            # Update fields
            if title:
                updated_event["summary"] = title

            if description is not None:
                updated_event["description"] = description

            if location is not None:
                updated_event["location"] = location

            if start_time:
                updated_event["start"] = self._format_datetime(start_time)
                if duration_minutes:
                    end_time = start_time + timedelta(minutes=duration_minutes)
                else:
                    # Keep original duration
                    original_start = datetime.fromisoformat(
                        current_event["start"]["dateTime"].replace("Z", "+00:00")
                    )
                    original_end = datetime.fromisoformat(
                        current_event["end"]["dateTime"].replace("Z", "+00:00")
                    )
                    duration = original_end - original_start
                    end_time = start_time + duration
                updated_event["end"] = self._format_datetime(end_time)

            # Make update request
            params = {"sendNotifications": "true" if send_notifications else "false"}

            response = await self._make_request(
                method="PUT",
                endpoint=f"/calendars/{self.config.calendar_id}/events/{event_id}",
                data=updated_event,
                params=params,
            )

            event_data = response.json()

            logger.info(f"Updated calendar event: {event_id}")

            return self._create_result(
                success=True,
                data={
                    "event_id": event_data.get("id"),
                    "title": event_data.get("summary"),
                    "start": event_data.get("start"),
                    "end": event_data.get("end"),
                    "html_link": event_data.get("htmlLink"),
                },
                tool="calendar",
                action="update_event",
            )

        except MCPToolError as e:
            logger.error(f"Failed to update event {event_id}: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error updating event: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def delete_event(
        self, event_id: str, send_notifications: bool = True
    ) -> MCPToolResult:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID to delete
            send_notifications: Send cancellation notifications to attendees

        Returns:
            MCPToolResult
        """
        try:
            params = {"sendNotifications": "true" if send_notifications else "false"}

            await self._make_request(
                method="DELETE",
                endpoint=f"/calendars/{self.config.calendar_id}/events/{event_id}",
                params=params,
            )

            logger.info(f"Deleted calendar event: {event_id}")

            return self._create_result(
                success=True,
                data={"event_id": event_id, "deleted": True},
                tool="calendar",
                action="delete_event",
            )

        except MCPToolError as e:
            logger.error(f"Failed to delete event {event_id}: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error deleting event: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def check_conflicts(
        self, start_time: datetime, end_time: datetime
    ) -> MCPToolResult:
        """
        Check for calendar conflicts in a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            MCPToolResult with list of conflicting events
        """
        try:
            params = {
                "timeMin": start_time.isoformat() + "Z",
                "timeMax": end_time.isoformat() + "Z",
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            response = await self._make_request(
                method="GET",
                endpoint=f"/calendars/{self.config.calendar_id}/events",
                params=params,
            )

            events_data = response.json()
            events = events_data.get("items", [])

            conflicts = [
                {
                    "event_id": event.get("id"),
                    "title": event.get("summary"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                }
                for event in events
            ]

            logger.info(f"Found {len(conflicts)} conflicting events")

            return self._create_result(
                success=True,
                data={
                    "has_conflicts": len(conflicts) > 0,
                    "conflict_count": len(conflicts),
                    "conflicts": conflicts,
                },
                tool="calendar",
                action="check_conflicts",
            )

        except MCPToolError as e:
            logger.error(f"Failed to check conflicts: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error checking conflicts: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def add_attendees(
        self, event_id: str, attendees: List[Dict[str, Any]], send_invitations: bool = True
    ) -> MCPToolResult:
        """
        Add attendees to an event.

        Args:
            event_id: Event ID
            attendees: List of attendee dictionaries
            send_invitations: Send email invitations to new attendees

        Returns:
            MCPToolResult
        """
        try:
            # Get current event
            get_response = await self._make_request(
                method="GET",
                endpoint=f"/calendars/{self.config.calendar_id}/events/{event_id}",
            )

            current_event = get_response.json()
            current_attendees = current_event.get("attendees", [])

            # Add new attendees
            new_attendees = [
                {
                    "email": att.get("email"),
                    "displayName": att.get("displayName", att.get("email")),
                    "optional": att.get("optional", False),
                }
                for att in attendees
            ]

            # Merge with existing
            all_attendees = current_attendees + new_attendees
            current_event["attendees"] = all_attendees

            # Update event
            params = {"sendNotifications": "true" if send_invitations else "false"}

            response = await self._make_request(
                method="PUT",
                endpoint=f"/calendars/{self.config.calendar_id}/events/{event_id}",
                data=current_event,
                params=params,
            )

            event_data = response.json()

            logger.info(f"Added {len(new_attendees)} attendees to event {event_id}")

            return self._create_result(
                success=True,
                data={
                    "event_id": event_id,
                    "attendees": event_data.get("attendees", []),
                    "added_count": len(new_attendees),
                },
                tool="calendar",
                action="add_attendees",
            )

        except MCPToolError as e:
            logger.error(f"Failed to add attendees: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error adding attendees: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def _health_check_impl(self) -> bool:
        """Check Google Calendar API health."""
        try:
            await self._make_request(
                method="GET",
                endpoint=f"/calendars/{self.config.calendar_id}",
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
