"""
SMS Manager Integration

Provides integration with Twilio SMS API.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
from loguru import logger

from .base import MCPToolBase, MCPToolResult, MCPToolError, MCPToolConfig


class UrgencyLevel(str, Enum):
    """SMS urgency levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SMSStatus(str, Enum):
    """SMS delivery status."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class SMSConfig(MCPToolConfig):
    """Configuration for SMS Manager."""

    account_sid: Optional[str] = Field(default=None, description="Twilio Account SID")
    auth_token: Optional[str] = Field(default=None, description="Twilio Auth Token")
    from_number: Optional[str] = Field(default=None, description="Twilio phone number to send from")
    base_url: str = Field(default="https://api.twilio.com/2010-04-01", description="Twilio API base URL")
    max_message_length: int = Field(default=1600, description="Maximum SMS message length")


class SMSSendRequest(BaseModel):
    """Request model for sending SMS."""

    to: str = Field(..., description="Recipient phone number (E.164 format)")
    message: str = Field(..., description="SMS message content", min_length=1)
    urgency: UrgencyLevel = Field(default=UrgencyLevel.NORMAL, description="Message urgency level")
    status_callback: Optional[str] = Field(default=None, description="Webhook URL for delivery status")

    @validator("to")
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove common formatting characters
        cleaned = v.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if not cleaned.startswith("+"):
            raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
        if not cleaned[1:].isdigit():
            raise ValueError("Phone number must contain only digits after country code")
        return cleaned

    @validator("message")
    def validate_message_length(cls, v: str) -> str:
        """Validate message length."""
        if len(v) > 1600:
            raise ValueError("Message exceeds maximum length of 1600 characters")
        return v


class SMSManager(MCPToolBase[SMSConfig]):
    """
    SMS Manager for Twilio integration.

    Provides methods for:
    - Sending SMS messages
    - Sending to multiple recipients
    - Tracking delivery status
    - Message templating
    - Urgency handling
    """

    def _create_config(self, config: Dict[str, Any]) -> SMSConfig:
        """Create SMS Manager configuration."""
        return SMSConfig(**config)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Twilio API."""
        headers = super()._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return headers

    def _get_auth(self) -> Optional[tuple]:
        """Get basic auth credentials for Twilio."""
        if self.config.account_sid and self.config.auth_token:
            return (self.config.account_sid, self.config.auth_token)
        return None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Override to use form-encoded data for Twilio."""
        if not self._initialized:
            await self.initialize()

        if not self.config.enabled:
            raise MCPToolError(
                f"{self.__class__.__name__} is disabled",
                code="TOOL_DISABLED",
            )

        if self.client is None:
            raise MCPToolError(
                "HTTP client not initialized",
                code="CLIENT_NOT_INITIALIZED",
            )

        try:
            logger.debug(f"Making {method} request to {endpoint}")

            request_headers = self._get_headers()
            if headers:
                request_headers.update(headers)

            auth = self._get_auth()

            response = await self.client.request(
                method=method,
                url=endpoint,
                data=data,  # Twilio uses form data, not JSON
                params=params,
                headers=request_headers,
                auth=auth,
            )

            response.raise_for_status()
            return response

        except Exception as e:
            logger.exception(f"Request failed: {e}")
            raise

    def _get_urgency_priority(self, urgency: UrgencyLevel) -> int:
        """
        Get priority value for urgency level.

        Args:
            urgency: Urgency level

        Returns:
            Priority value (higher = more urgent)
        """
        return {
            UrgencyLevel.LOW: 1,
            UrgencyLevel.NORMAL: 2,
            UrgencyLevel.HIGH: 3,
            UrgencyLevel.URGENT: 4,
        }.get(urgency, 2)

    def _apply_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Apply variables to message template.

        Args:
            template: Message template with {variable} placeholders
            variables: Dictionary of variable values

        Returns:
            Formatted message
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            raise MCPToolError(
                f"Missing template variable: {e}",
                code="TEMPLATE_ERROR",
            )

    async def send_sms(
        self,
        to: str,
        message: str,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        status_callback: Optional[str] = None,
    ) -> MCPToolResult:
        """
        Send SMS message to a single recipient.

        Args:
            to: Recipient phone number in E.164 format (e.g., +1234567890)
            message: SMS message content
            urgency: Message urgency level
            status_callback: Optional webhook URL for delivery status updates

        Returns:
            MCPToolResult with message SID and status
        """
        try:
            # Validate request
            request = SMSSendRequest(
                to=to,
                message=message,
                urgency=urgency,
                status_callback=status_callback,
            )

            # Build Twilio request
            form_data = {
                "To": request.to,
                "From": self.config.from_number,
                "Body": request.message,
            }

            if request.status_callback:
                form_data["StatusCallback"] = request.status_callback

            # Make API request
            endpoint = f"/Accounts/{self.config.account_sid}/Messages.json"

            response = await self._make_request(
                method="POST",
                endpoint=endpoint,
                data=form_data,
            )

            message_data = response.json()

            logger.info(f"Sent SMS to {to}: {message_data.get('sid')}")

            return self._create_result(
                success=True,
                data={
                    "message_sid": message_data.get("sid"),
                    "to": message_data.get("to"),
                    "from": message_data.get("from"),
                    "status": message_data.get("status"),
                    "date_created": message_data.get("date_created"),
                    "urgency": urgency.value,
                    "segments": message_data.get("num_segments", 1),
                },
                tool="sms",
                action="send_sms",
            )

        except MCPToolError as e:
            logger.error(f"Failed to send SMS: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error sending SMS: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> MCPToolResult:
        """
        Send SMS to multiple recipients.

        Args:
            recipients: List of phone numbers in E.164 format
            message: SMS message content
            urgency: Message urgency level

        Returns:
            MCPToolResult with results for each recipient
        """
        try:
            results = []
            failed = []

            for recipient in recipients:
                result = await self.send_sms(
                    to=recipient,
                    message=message,
                    urgency=urgency,
                )

                if result.success:
                    results.append(result.data)
                else:
                    failed.append({
                        "recipient": recipient,
                        "error": result.error,
                    })

            logger.info(
                f"Sent bulk SMS to {len(results)}/{len(recipients)} recipients"
            )

            return self._create_result(
                success=len(failed) == 0,
                data={
                    "total": len(recipients),
                    "sent": len(results),
                    "failed": len(failed),
                    "results": results,
                    "failures": failed,
                },
                tool="sms",
                action="send_bulk_sms",
            )

        except Exception as e:
            logger.exception(f"Unexpected error sending bulk SMS: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def get_message_status(self, message_sid: str) -> MCPToolResult:
        """
        Get delivery status for a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            MCPToolResult with message status
        """
        try:
            endpoint = f"/Accounts/{self.config.account_sid}/Messages/{message_sid}.json"

            response = await self._make_request(
                method="GET",
                endpoint=endpoint,
            )

            message_data = response.json()

            return self._create_result(
                success=True,
                data={
                    "message_sid": message_data.get("sid"),
                    "status": message_data.get("status"),
                    "to": message_data.get("to"),
                    "from": message_data.get("from"),
                    "date_sent": message_data.get("date_sent"),
                    "error_code": message_data.get("error_code"),
                    "error_message": message_data.get("error_message"),
                    "price": message_data.get("price"),
                    "price_unit": message_data.get("price_unit"),
                },
                tool="sms",
                action="get_message_status",
            )

        except MCPToolError as e:
            logger.error(f"Failed to get message status: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error getting status: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def send_from_template(
        self,
        to: str,
        template: str,
        variables: Dict[str, str],
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> MCPToolResult:
        """
        Send SMS using a message template.

        Args:
            to: Recipient phone number
            template: Message template with {variable} placeholders
            variables: Dictionary of template variables
            urgency: Message urgency level

        Returns:
            MCPToolResult
        """
        try:
            message = self._apply_template(template, variables)
            return await self.send_sms(to=to, message=message, urgency=urgency)

        except MCPToolError as e:
            logger.error(f"Failed to send templated SMS: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error sending templated SMS: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def _health_check_impl(self) -> bool:
        """Check Twilio API health."""
        try:
            endpoint = f"/Accounts/{self.config.account_sid}.json"
            await self._make_request(method="GET", endpoint=endpoint)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
