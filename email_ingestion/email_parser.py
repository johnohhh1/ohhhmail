"""
Email Parser

Parses MIME emails and extracts metadata, body content, and attachments.
"""

import email
from email.message import Message
from email.header import decode_header
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging
import chardet
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    """Email attachment metadata."""

    filename: str
    content_type: str
    size: int
    content: bytes
    content_id: Optional[str] = None


@dataclass
class ParsedEmail:
    """Parsed email data structure."""

    email_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    date: Optional[datetime] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "email_id": self.email_id,
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "cc": self.cc,
            "bcc": self.bcc,
            "date": self.date.isoformat() if self.date else None,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "attachments": [
                {
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size": att.size,
                    "content_id": att.content_id
                }
                for att in self.attachments
            ],
            "headers": self.headers,
            "message_id": self.message_id,
            "in_reply_to": self.in_reply_to,
            "references": self.references
        }


class EmailParser:
    """Parser for MIME email messages."""

    @staticmethod
    def decode_header_value(header_value: str) -> str:
        """
        Decode email header value.

        Args:
            header_value: Raw header value

        Returns:
            Decoded header string
        """
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        # Try to detect encoding
                        detected = chardet.detect(part)
                        detected_encoding = detected.get("encoding", "utf-8")
                        decoded_string += part.decode(detected_encoding, errors="replace")
                except Exception as e:
                    logger.warning(f"Failed to decode header part: {e}")
                    decoded_string += part.decode("utf-8", errors="replace")
            else:
                decoded_string += str(part)

        return decoded_string.strip()

    @staticmethod
    def extract_email_addresses(header_value: str) -> List[str]:
        """
        Extract email addresses from header value.

        Args:
            header_value: Header value containing email addresses

        Returns:
            List of email addresses
        """
        if not header_value:
            return []

        decoded = EmailParser.decode_header_value(header_value)

        # Split by comma and extract addresses
        addresses = []
        parts = decoded.split(",")

        for part in parts:
            part = part.strip()
            # Extract email from "Name <email@example.com>" format
            if "<" in part and ">" in part:
                start = part.index("<") + 1
                end = part.index(">")
                email_addr = part[start:end].strip()
            else:
                email_addr = part

            if email_addr and "@" in email_addr:
                addresses.append(email_addr)

        return addresses

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse email date string.

        Args:
            date_str: Date string from email header

        Returns:
            Datetime object or None
        """
        if not date_str:
            return None

        try:
            # Parse email date format
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    @staticmethod
    def decode_payload(part: Message) -> str:
        """
        Decode message payload with proper charset handling.

        Args:
            part: Message part to decode

        Returns:
            Decoded string
        """
        payload = part.get_payload(decode=True)
        if not payload:
            return ""

        # Get charset
        charset = part.get_content_charset()

        if charset:
            try:
                return payload.decode(charset, errors="replace")
            except Exception as e:
                logger.warning(f"Failed to decode with charset {charset}: {e}")

        # Try to detect encoding
        try:
            detected = chardet.detect(payload)
            detected_charset = detected.get("encoding", "utf-8")
            return payload.decode(detected_charset, errors="replace")
        except Exception as e:
            logger.warning(f"Failed to decode payload: {e}")
            return payload.decode("utf-8", errors="replace")

    @staticmethod
    def extract_body(message: Message) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text and HTML body from email.

        Args:
            message: Email message

        Returns:
            Tuple of (text_body, html_body)
        """
        text_body = None
        html_body = None

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain" and not text_body:
                    text_body = EmailParser.decode_payload(part)
                elif content_type == "text/html" and not html_body:
                    html_body = EmailParser.decode_payload(part)
        else:
            content_type = message.get_content_type()
            if content_type == "text/plain":
                text_body = EmailParser.decode_payload(message)
            elif content_type == "text/html":
                html_body = EmailParser.decode_payload(message)

        return text_body, html_body

    @staticmethod
    def extract_attachments(message: Message, max_size_bytes: Optional[int] = None) -> List[EmailAttachment]:
        """
        Extract attachments from email.

        Args:
            message: Email message
            max_size_bytes: Maximum attachment size in bytes

        Returns:
            List of EmailAttachment objects
        """
        attachments = []

        for part in message.walk():
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition or part.get_filename():
                filename = part.get_filename()

                if not filename:
                    # Generate filename if missing
                    ext = "bin"
                    if part.get_content_type() == "text/plain":
                        ext = "txt"
                    elif part.get_content_type() == "text/html":
                        ext = "html"
                    filename = f"attachment_{len(attachments) + 1}.{ext}"
                else:
                    filename = EmailParser.decode_header_value(filename)

                # Get attachment content
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                size = len(payload)

                # Check size limit
                if max_size_bytes and size > max_size_bytes:
                    logger.warning(
                        f"Skipping attachment {filename}: size {size} bytes exceeds limit {max_size_bytes} bytes"
                    )
                    continue

                attachment = EmailAttachment(
                    filename=filename,
                    content_type=part.get_content_type(),
                    size=size,
                    content=payload,
                    content_id=part.get("Content-ID")
                )

                attachments.append(attachment)
                logger.debug(f"Extracted attachment: {filename} ({size} bytes)")

        return attachments

    @classmethod
    def parse(
        cls,
        email_id: str,
        message: Message,
        max_attachment_size: Optional[int] = None
    ) -> ParsedEmail:
        """
        Parse email message into structured data.

        Args:
            email_id: Email ID from IMAP
            message: Email message object
            max_attachment_size: Maximum attachment size in bytes

        Returns:
            ParsedEmail object
        """
        logger.debug(f"Parsing email ID: {email_id}")

        # Extract headers
        subject = cls.decode_header_value(message.get("Subject", ""))
        sender = cls.decode_header_value(message.get("From", ""))
        recipients = cls.extract_email_addresses(message.get("To", ""))
        cc = cls.extract_email_addresses(message.get("Cc", ""))
        bcc = cls.extract_email_addresses(message.get("Bcc", ""))
        date = cls.parse_date(message.get("Date"))
        message_id = message.get("Message-ID")
        in_reply_to = message.get("In-Reply-To")
        references_str = message.get("References", "")
        references = [ref.strip() for ref in references_str.split()] if references_str else []

        # Extract body
        text_body, html_body = cls.extract_body(message)

        # Extract attachments
        attachments = cls.extract_attachments(message, max_attachment_size)

        # Extract all headers
        headers = {}
        for key, value in message.items():
            headers[key] = cls.decode_header_value(value)

        parsed_email = ParsedEmail(
            email_id=email_id,
            subject=subject,
            sender=sender,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            date=date,
            body_text=text_body,
            body_html=html_body,
            attachments=attachments,
            headers=headers,
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references
        )

        logger.info(
            f"Parsed email: {subject} from {sender} "
            f"({len(attachments)} attachments, {len(text_body or '')} chars text)"
        )

        return parsed_email
