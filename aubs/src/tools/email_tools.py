"""
AUBS Email Tools - Direct IMAP Access
v2 approach: No email cache, direct Gmail IMAP connection
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import re
import os
import structlog

logger = structlog.get_logger()


def decode_mime_header(header_value: str) -> str:
    """Decode MIME encoded header to string"""
    if not header_value:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(header_value):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            except Exception:
                decoded_parts.append(part.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(part)

    return ''.join(decoded_parts)


def extract_email_body(msg) -> str:
    """Extract plain text body from email message"""
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            # Prefer plain text
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    break
                except Exception as e:
                    logger.warning("Failed to decode email body part", error=str(e))
                    continue

            # Fall back to HTML if no plain text
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = payload.decode(charset, errors='replace')
                    # Strip HTML tags for a basic text version
                    body = re.sub(r'<[^>]+>', ' ', html_body)
                    body = re.sub(r'\s+', ' ', body).strip()
                except Exception as e:
                    logger.warning("Failed to decode HTML body", error=str(e))
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        except Exception as e:
            logger.warning("Failed to decode message payload", error=str(e))

    return body[:2000]  # Limit body length


def get_imap_connection():
    """Create IMAP connection to Gmail"""
    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_email or not gmail_app_password:
        raise ValueError("GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables required")

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(gmail_email, gmail_app_password)
    return imap


def get_emails(
    limit: int = 20,
    filter_type: str = "ALL",
    days_back: int = 7,
    sender_filter: Optional[str] = None,
    subject_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch emails directly from Gmail via IMAP

    Args:
        limit: Maximum number of emails to return (default 20)
        filter_type: IMAP search filter - "ALL", "UNSEEN", "SEEN", "FLAGGED"
        days_back: Only get emails from last N days (default 7)
        sender_filter: Optional filter for sender domain or address
        subject_filter: Optional filter for subject keywords

    Returns:
        List of email dictionaries with id, subject, sender, date, snippet
    """
    log = logger.bind(limit=limit, filter_type=filter_type, days_back=days_back)
    log.info("Fetching emails from Gmail IMAP")

    try:
        imap = get_imap_connection()
        imap.select("INBOX")

        # Build search criteria
        search_criteria = []

        # Add filter type
        if filter_type.upper() in ["UNSEEN", "SEEN", "FLAGGED", "UNFLAGGED", "ALL"]:
            search_criteria.append(filter_type.upper())
        else:
            search_criteria.append("ALL")

        # Add date filter
        if days_back > 0:
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            search_criteria.append(f'SINCE {since_date}')

        # Add sender filter
        if sender_filter:
            search_criteria.append(f'FROM "{sender_filter}"')

        # Add subject filter
        if subject_filter:
            search_criteria.append(f'SUBJECT "{subject_filter}"')

        # Join criteria with space (implicit AND)
        search_string = ' '.join(search_criteria)
        log.info("IMAP search", criteria=search_string)

        # Search emails
        status, messages = imap.search(None, search_string)

        if status != "OK":
            log.error("IMAP search failed", status=status)
            imap.logout()
            return []

        email_ids = messages[0].split()

        if not email_ids:
            log.info("No emails found matching criteria")
            imap.logout()
            return []

        # Get most recent emails (last N)
        email_ids = email_ids[-limit:]
        email_ids.reverse()  # Most recent first

        log.info(f"Found {len(email_ids)} emails")

        results = []
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = imap.fetch(email_id, "(RFC822)")

                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract headers
                subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
                sender = decode_mime_header(msg.get("From", "Unknown"))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", email_id.decode())

                # Parse date
                try:
                    date_obj = parsedate_to_datetime(date_str)
                    date_formatted = date_obj.isoformat()
                except Exception:
                    date_formatted = date_str

                # Extract body snippet
                body = extract_email_body(msg)
                snippet = body[:300] if body else ""

                results.append({
                    "id": email_id.decode(),
                    "message_id": message_id,
                    "subject": subject,
                    "sender": sender,
                    "date": date_formatted,
                    "snippet": snippet,
                    "has_attachments": any(
                        part.get("Content-Disposition", "").startswith("attachment")
                        for part in msg.walk() if msg.is_multipart()
                    )
                })

            except Exception as e:
                log.warning("Failed to parse email", email_id=email_id.decode(), error=str(e))
                continue

        imap.logout()
        log.info(f"Successfully fetched {len(results)} emails")
        return results

    except imaplib.IMAP4.error as e:
        log.error("IMAP error", error=str(e))
        raise ValueError(f"IMAP error: {str(e)}")
    except Exception as e:
        log.error("Failed to fetch emails", error=str(e))
        raise


def get_email_by_id(email_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full email content by ID

    Args:
        email_id: IMAP email ID

    Returns:
        Full email with body, headers, and attachment info
    """
    log = logger.bind(email_id=email_id)
    log.info("Fetching email by ID")

    try:
        imap = get_imap_connection()
        imap.select("INBOX")

        # Fetch email
        status, msg_data = imap.fetch(email_id.encode(), "(RFC822)")

        if status != "OK":
            log.error("Failed to fetch email", status=status)
            imap.logout()
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract all info
        subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
        sender = decode_mime_header(msg.get("From", "Unknown"))
        to = decode_mime_header(msg.get("To", ""))
        cc = decode_mime_header(msg.get("Cc", ""))
        date_str = msg.get("Date", "")
        message_id = msg.get("Message-ID", email_id)

        # Parse date
        try:
            date_obj = parsedate_to_datetime(date_str)
            date_formatted = date_obj.isoformat()
        except Exception:
            date_formatted = date_str

        # Get full body
        body = extract_email_body(msg)

        # Get attachments info
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": decode_mime_header(filename),
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b"")
                        })

        imap.logout()

        return {
            "id": email_id,
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "to": to,
            "cc": cc,
            "date": date_formatted,
            "body": body,
            "attachments": attachments
        }

    except Exception as e:
        log.error("Failed to fetch email", error=str(e))
        raise


async def triage_email(email_id: str) -> Dict[str, Any]:
    """
    AI triage of a specific email
    Uses EmailAnalyzer from email_analyzer.py

    Args:
        email_id: IMAP email ID

    Returns:
        Triage result with priority, category, suggested actions
    """
    from src.email_analyzer import EmailAnalyzer
    from shared.models import EmailData

    log = logger.bind(email_id=email_id)
    log.info("Triaging email")

    # Get full email
    email_content = get_email_by_id(email_id)
    if not email_content:
        raise ValueError(f"Email {email_id} not found")

    # Convert to EmailData for analyzer
    email_data = EmailData(
        id=email_id,
        subject=email_content["subject"],
        sender=email_content["sender"],
        recipient=email_content["to"],
        body_text=email_content["body"],
        body_html="",
        received_at=datetime.fromisoformat(email_content["date"]) if email_content["date"] else datetime.now(),
        attachments=[]
    )

    # Analyze
    analyzer = EmailAnalyzer()
    result = await analyzer.analyze(email_data)

    log.info(
        "Email triaged",
        urgency=result.get("urgency_score"),
        category=result.get("category")
    )

    return {
        "email_id": email_id,
        "subject": email_content["subject"],
        "sender": email_content["sender"],
        **result
    }
