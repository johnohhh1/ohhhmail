"""
Gmail IMAP Client

Handles IMAP connection, authentication, and email fetching from Gmail.
"""

import imaplib
import email
from typing import List, Optional, Tuple
from email.message import Message
import logging
from contextlib import contextmanager

from config import Settings

logger = logging.getLogger(__name__)


class GmailIMAPClient:
    """Gmail IMAP client for email retrieval."""

    def __init__(self, settings: Settings):
        """
        Initialize Gmail IMAP client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """
        Establish IMAP connection to Gmail.

        Raises:
            imaplib.IMAP4.error: If connection fails
            Exception: For other connection errors
        """
        try:
            logger.info(f"Connecting to {self.settings.imap_host}:{self.settings.imap_port}")

            if self.settings.enable_ssl:
                self.imap = imaplib.IMAP4_SSL(
                    self.settings.imap_host,
                    self.settings.imap_port,
                    timeout=self.settings.imap_timeout
                )
            else:
                self.imap = imaplib.IMAP4(
                    self.settings.imap_host,
                    self.settings.imap_port,
                    timeout=self.settings.imap_timeout
                )

            # Login
            self.imap.login(
                self.settings.gmail_email,
                self.settings.gmail_password
            )

            logger.info(f"Successfully connected as {self.settings.gmail_email}")

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            raise

    def disconnect(self) -> None:
        """Safely disconnect from IMAP server."""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                logger.info("Disconnected from Gmail")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.imap = None

    @contextmanager
    def connection(self):
        """
        Context manager for IMAP connection.

        Usage:
            with client.connection():
                emails = client.fetch_unread_emails()
        """
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def select_folder(self, folder: str = "INBOX") -> Tuple[str, List[bytes]]:
        """
        Select an IMAP folder.

        Args:
            folder: Folder name to select

        Returns:
            Tuple of (status, data)

        Raises:
            ValueError: If not connected
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        logger.debug(f"Selecting folder: {folder}")
        status, data = self.imap.select(folder)

        if status != "OK":
            raise imaplib.IMAP4.error(f"Failed to select folder {folder}")

        return status, data

    def search_emails(self, criteria: str = "UNSEEN") -> List[str]:
        """
        Search for emails matching criteria.

        Args:
            criteria: IMAP search criteria (e.g., "UNSEEN", "ALL")

        Returns:
            List of email IDs

        Raises:
            ValueError: If not connected
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        logger.debug(f"Searching emails with criteria: {criteria}")
        status, data = self.imap.search(None, criteria)

        if status != "OK":
            raise imaplib.IMAP4.error(f"Search failed with criteria: {criteria}")

        # Parse email IDs
        email_ids = data[0].split()
        logger.info(f"Found {len(email_ids)} emails matching criteria: {criteria}")

        return [email_id.decode() for email_id in email_ids]

    def fetch_email(self, email_id: str) -> Message:
        """
        Fetch a single email by ID.

        Args:
            email_id: Email ID to fetch

        Returns:
            Email message object

        Raises:
            ValueError: If not connected
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        logger.debug(f"Fetching email ID: {email_id}")
        status, data = self.imap.fetch(email_id, "(RFC822)")

        if status != "OK":
            raise imaplib.IMAP4.error(f"Failed to fetch email {email_id}")

        # Parse email
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        return email_message

    def mark_as_read(self, email_id: str) -> None:
        """
        Mark an email as read.

        Args:
            email_id: Email ID to mark

        Raises:
            ValueError: If not connected
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        logger.debug(f"Marking email {email_id} as read")
        self.imap.store(email_id, "+FLAGS", "\\Seen")

    def mark_as_unread(self, email_id: str) -> None:
        """
        Mark an email as unread.

        Args:
            email_id: Email ID to mark

        Raises:
            ValueError: If not connected
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        logger.debug(f"Marking email {email_id} as unread")
        self.imap.store(email_id, "-FLAGS", "\\Seen")

    def fetch_unread_emails(self, limit: Optional[int] = None) -> List[Tuple[str, Message]]:
        """
        Fetch all unread emails.

        Args:
            limit: Maximum number of emails to fetch

        Returns:
            List of tuples (email_id, email_message)
        """
        self.select_folder(self.settings.inbox_folder)
        email_ids = self.search_emails("UNSEEN")

        # Apply limit
        if limit:
            email_ids = email_ids[:limit]

        emails = []
        for email_id in email_ids:
            try:
                message = self.fetch_email(email_id)
                emails.append((email_id, message))
            except Exception as e:
                logger.error(f"Failed to fetch email {email_id}: {e}")
                continue

        return emails

    def get_folder_list(self) -> List[str]:
        """
        Get list of available IMAP folders.

        Returns:
            List of folder names
        """
        if not self.imap:
            raise ValueError("Not connected to IMAP server")

        status, folders = self.imap.list()
        if status != "OK":
            raise imaplib.IMAP4.error("Failed to list folders")

        folder_list = []
        for folder in folders:
            # Parse folder name from response
            parts = folder.decode().split('"')
            if len(parts) >= 3:
                folder_list.append(parts[-2])

        return folder_list
