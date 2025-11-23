"""
Email Client Integration

Provides email operations for Gmail or other email providers.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from loguru import logger

from .base import MCPToolBase, MCPToolResult, MCPToolError, MCPToolConfig


class EmailFolder(str, Enum):
    """Email folder types."""

    INBOX = "INBOX"
    SENT = "SENT"
    DRAFTS = "DRAFTS"
    TRASH = "TRASH"
    SPAM = "SPAM"
    ARCHIVE = "ARCHIVE"


class EmailClientConfig(MCPToolConfig):
    """Configuration for Email Client."""

    email_address: Optional[str] = Field(default=None, description="Email address")
    credentials_file: Optional[str] = Field(default=None, description="Path to credentials file")
    base_url: str = Field(default="https://gmail.googleapis.com/gmail/v1", description="Gmail API base URL")
    user_id: str = Field(default="me", description="User ID for Gmail API")


class EmailRecipient(BaseModel):
    """Email recipient model."""

    email: EmailStr
    name: Optional[str] = None


class EmailSendRequest(BaseModel):
    """Request model for sending email."""

    to: List[EmailRecipient] = Field(..., description="Email recipients")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (HTML or plain text)")
    cc: List[EmailRecipient] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailRecipient] = Field(default_factory=list, description="BCC recipients")
    html: bool = Field(default=False, description="Whether body is HTML")
    reply_to: Optional[str] = Field(default=None, description="Reply-to address")


class EmailClient(MCPToolBase[EmailClientConfig]):
    """
    Email Client for Gmail API integration.

    Provides methods for:
    - Sending replies
    - Forwarding emails
    - Marking as read/unread
    - Moving to folders
    - Archiving emails
    """

    def _create_config(self, config: Dict[str, Any]) -> EmailClientConfig:
        """Create Email Client configuration."""
        return EmailClientConfig(**config)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Gmail authentication."""
        headers = super()._get_headers()
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _create_message_data(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        reply_to: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create email message data for Gmail API.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML
            reply_to: Reply-to address
            in_reply_to: Message ID this is replying to
            references: Thread references

        Returns:
            Message data dictionary
        """
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Create message
        if html:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "html"))
        else:
            message = MIMEText(body, "plain")

        message["To"] = ", ".join(to)
        message["Subject"] = subject

        if cc:
            message["Cc"] = ", ".join(cc)

        if bcc:
            message["Bcc"] = ", ".join(bcc)

        if reply_to:
            message["Reply-To"] = reply_to

        if in_reply_to:
            message["In-Reply-To"] = in_reply_to

        if references:
            message["References"] = references

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return {"raw": raw_message}

    async def send_reply(
        self,
        message_id: str,
        body: str,
        html: bool = False,
    ) -> MCPToolResult:
        """
        Send a reply to an email.

        Args:
            message_id: Original message ID to reply to
            body: Reply body
            html: Whether body is HTML

        Returns:
            MCPToolResult with sent message data
        """
        try:
            # Get original message to extract metadata
            original_response = await self._make_request(
                method="GET",
                endpoint=f"/users/{self.config.user_id}/messages/{message_id}",
                params={"format": "metadata"},
            )

            original = original_response.json()
            headers = {h["name"]: h["value"] for h in original.get("payload", {}).get("headers", [])}

            # Extract reply metadata
            to = [headers.get("From", "")]
            subject = headers.get("Subject", "")
            if not subject.startswith("Re: "):
                subject = f"Re: {subject}"

            thread_id = original.get("threadId")
            in_reply_to = headers.get("Message-ID")

            # Create reply message
            message_data = self._create_message_data(
                to=to,
                subject=subject,
                body=body,
                html=html,
                in_reply_to=in_reply_to,
                references=in_reply_to,
            )

            # Add thread ID to keep in same conversation
            message_data["threadId"] = thread_id

            # Send reply
            response = await self._make_request(
                method="POST",
                endpoint=f"/users/{self.config.user_id}/messages/send",
                data=message_data,
            )

            sent_message = response.json()

            logger.info(f"Sent reply to message {message_id}")

            return self._create_result(
                success=True,
                data={
                    "message_id": sent_message.get("id"),
                    "thread_id": sent_message.get("threadId"),
                    "label_ids": sent_message.get("labelIds", []),
                },
                tool="email",
                action="send_reply",
            )

        except MCPToolError as e:
            logger.error(f"Failed to send reply: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error sending reply: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def forward_email(
        self,
        message_id: str,
        to: List[str],
        body: Optional[str] = None,
    ) -> MCPToolResult:
        """
        Forward an email to other recipients.

        Args:
            message_id: Message ID to forward
            to: List of recipient email addresses
            body: Optional additional message body

        Returns:
            MCPToolResult
        """
        try:
            # Get original message
            original_response = await self._make_request(
                method="GET",
                endpoint=f"/users/{self.config.user_id}/messages/{message_id}",
                params={"format": "full"},
            )

            original = original_response.json()
            headers = {h["name"]: h["value"] for h in original.get("payload", {}).get("headers", [])}

            # Extract message content
            subject = headers.get("Subject", "")
            if not subject.startswith("Fwd: "):
                subject = f"Fwd: {subject}"

            # Get original body
            payload = original.get("payload", {})
            original_body = self._extract_body(payload)

            # Combine with forwarding message
            forward_body = ""
            if body:
                forward_body = f"{body}\n\n---------- Forwarded message ---------\n"

            forward_body += f"From: {headers.get('From', 'Unknown')}\n"
            forward_body += f"Date: {headers.get('Date', 'Unknown')}\n"
            forward_body += f"Subject: {headers.get('Subject', 'No Subject')}\n\n"
            forward_body += original_body

            # Create and send forwarded message
            message_data = self._create_message_data(
                to=to,
                subject=subject,
                body=forward_body,
                html=False,
            )

            response = await self._make_request(
                method="POST",
                endpoint=f"/users/{self.config.user_id}/messages/send",
                data=message_data,
            )

            sent_message = response.json()

            logger.info(f"Forwarded message {message_id} to {len(to)} recipients")

            return self._create_result(
                success=True,
                data={
                    "message_id": sent_message.get("id"),
                    "thread_id": sent_message.get("threadId"),
                    "recipients": to,
                },
                tool="email",
                action="forward_email",
            )

        except MCPToolError as e:
            logger.error(f"Failed to forward email: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error forwarding email: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        if "body" in payload and "data" in payload["body"]:
            import base64
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    import base64
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")

        return ""

    async def mark_as_read(self, message_id: str) -> MCPToolResult:
        """
        Mark an email as read.

        Args:
            message_id: Message ID

        Returns:
            MCPToolResult
        """
        return await self._modify_labels(
            message_id=message_id,
            remove_labels=["UNREAD"],
        )

    async def mark_as_unread(self, message_id: str) -> MCPToolResult:
        """
        Mark an email as unread.

        Args:
            message_id: Message ID

        Returns:
            MCPToolResult
        """
        return await self._modify_labels(
            message_id=message_id,
            add_labels=["UNREAD"],
        )

    async def move_to_folder(self, message_id: str, folder: EmailFolder) -> MCPToolResult:
        """
        Move email to a folder.

        Args:
            message_id: Message ID
            folder: Destination folder

        Returns:
            MCPToolResult
        """
        return await self._modify_labels(
            message_id=message_id,
            add_labels=[folder.value],
            remove_labels=["INBOX"],
        )

    async def archive(self, message_id: str) -> MCPToolResult:
        """
        Archive an email (remove from inbox).

        Args:
            message_id: Message ID

        Returns:
            MCPToolResult
        """
        return await self._modify_labels(
            message_id=message_id,
            remove_labels=["INBOX"],
        )

    async def _modify_labels(
        self,
        message_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> MCPToolResult:
        """
        Modify labels on a message.

        Args:
            message_id: Message ID
            add_labels: Labels to add
            remove_labels: Labels to remove

        Returns:
            MCPToolResult
        """
        try:
            payload: Dict[str, Any] = {}

            if add_labels:
                payload["addLabelIds"] = add_labels

            if remove_labels:
                payload["removeLabelIds"] = remove_labels

            if not payload:
                return self._create_result(
                    success=False,
                    error="No label modifications specified",
                    error_code="NO_MODIFICATIONS",
                )

            response = await self._make_request(
                method="POST",
                endpoint=f"/users/{self.config.user_id}/messages/{message_id}/modify",
                data=payload,
            )

            message = response.json()

            logger.info(f"Modified labels on message {message_id}")

            return self._create_result(
                success=True,
                data={
                    "message_id": message.get("id"),
                    "label_ids": message.get("labelIds", []),
                },
                tool="email",
                action="modify_labels",
            )

        except MCPToolError as e:
            logger.error(f"Failed to modify labels: {e.message}")
            return self._create_result(
                success=False,
                error=e.message,
                error_code=e.code,
                error_details=e.details,
            )
        except Exception as e:
            logger.exception(f"Unexpected error modifying labels: {e}")
            return self._create_result(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
            )

    async def _health_check_impl(self) -> bool:
        """Check Gmail API health."""
        try:
            await self._make_request(
                method="GET",
                endpoint=f"/users/{self.config.user_id}/profile",
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
