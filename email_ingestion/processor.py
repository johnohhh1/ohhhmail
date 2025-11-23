"""
Email Processor

Main orchestrator for email ingestion pipeline.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime
import json

from .config import Settings
from .gmail_client import GmailIMAPClient
from .email_parser import EmailParser, ParsedEmail
from .attachment_handler import AttachmentHandler

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Main email processing orchestrator."""

    def __init__(self, settings: Settings):
        """
        Initialize email processor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.gmail_client = GmailIMAPClient(settings)
        self.attachment_handler = AttachmentHandler(settings.attachment_storage_path)
        self.email_parser = EmailParser()

        # HTTP client for AUBS
        self.http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the processor and initialize connections."""
        logger.info("Starting email processor")

        # Initialize HTTP client for AUBS
        headers = {}
        if self.settings.aubs_api_key:
            headers["Authorization"] = f"Bearer {self.settings.aubs_api_key}"

        self.http_client = httpx.AsyncClient(
            base_url=self.settings.aubs_api_url,
            headers=headers,
            timeout=self.settings.aubs_timeout
        )

        logger.info("Email processor started")

    async def stop(self) -> None:
        """Stop the processor and cleanup connections."""
        logger.info("Stopping email processor")

        if self.http_client:
            await self.http_client.aclose()

        logger.info("Email processor stopped")

    async def send_to_aubs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send processed email data to AUBS.

        Args:
            data: Processed email data

        Returns:
            AUBS response

        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.http_client:
            raise RuntimeError("HTTP client not initialized")

        logger.debug(f"Sending email {data.get('email_id')} to AUBS")

        for attempt in range(self.settings.retry_attempts):
            try:
                response = await self.http_client.post(
                    "/emails",
                    json=data
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"Successfully sent email {data.get('email_id')} to AUBS")
                return result

            except httpx.HTTPError as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.settings.retry_attempts} failed: {e}"
                )

                if attempt < self.settings.retry_attempts - 1:
                    await asyncio.sleep(self.settings.retry_delay_seconds)
                else:
                    logger.error(f"Failed to send to AUBS after {self.settings.retry_attempts} attempts")
                    raise

    def process_email_sync(self, email_id: str, message) -> Optional[Dict[str, Any]]:
        """
        Process a single email (synchronous).

        Args:
            email_id: Email ID from IMAP
            message: Email message object

        Returns:
            Processed email data or None if processing fails
        """
        try:
            # Parse email
            parsed_email = self.email_parser.parse(
                email_id,
                message,
                max_attachment_size=self.settings.max_attachment_size_bytes
            )

            # Save attachments
            saved_attachments = self.attachment_handler.save_all_attachments(parsed_email)

            # Prepare data for AUBS
            email_data = parsed_email.to_dict()
            email_data["saved_attachments"] = saved_attachments
            email_data["processed_at"] = datetime.utcnow().isoformat()

            return email_data

        except Exception as e:
            logger.error(f"Failed to process email {email_id}: {e}", exc_info=True)
            return None

    async def process_email(self, email_id: str, message) -> Optional[Dict[str, Any]]:
        """
        Process a single email asynchronously.

        Args:
            email_id: Email ID from IMAP
            message: Email message object

        Returns:
            AUBS response or None if processing fails
        """
        # Process email synchronously (IMAP is blocking)
        email_data = await asyncio.to_thread(
            self.process_email_sync,
            email_id,
            message
        )

        if not email_data:
            return None

        # Send to AUBS
        try:
            response = await self.send_to_aubs(email_data)
            return response
        except Exception as e:
            logger.error(f"Failed to send email {email_id} to AUBS: {e}")
            return None

    async def process_batch(self) -> Dict[str, Any]:
        """
        Process a batch of unread emails.

        Returns:
            Processing statistics
        """
        stats = {
            "fetched": 0,
            "processed": 0,
            "failed": 0,
            "sent_to_aubs": 0,
            "start_time": datetime.utcnow().isoformat()
        }

        try:
            # Fetch unread emails (blocking operation)
            logger.info("Fetching unread emails")

            emails = await asyncio.to_thread(
                lambda: self.gmail_client.fetch_unread_emails(
                    limit=self.settings.batch_size
                )
            )

            stats["fetched"] = len(emails)
            logger.info(f"Fetched {len(emails)} unread emails")

            if not emails:
                return stats

            # Process emails concurrently
            tasks = []
            for email_id, message in emails:
                task = self.process_email(email_id, message)
                tasks.append((email_id, task))

            # Wait for all processing to complete
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            # Update statistics and mark emails
            for (email_id, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Exception processing email {email_id}: {result}")
                    stats["failed"] += 1
                elif result:
                    stats["processed"] += 1
                    stats["sent_to_aubs"] += 1

                    # Mark as read if configured
                    if self.settings.mark_as_read:
                        try:
                            await asyncio.to_thread(
                                self.gmail_client.mark_as_read,
                                email_id
                            )
                        except Exception as e:
                            logger.warning(f"Failed to mark email {email_id} as read: {e}")
                else:
                    stats["failed"] += 1

        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
        finally:
            stats["end_time"] = datetime.utcnow().isoformat()

        logger.info(
            f"Batch complete: {stats['processed']} processed, "
            f"{stats['sent_to_aubs']} sent to AUBS, "
            f"{stats['failed']} failed"
        )

        return stats

    async def run_continuous(self) -> None:
        """
        Run continuous email monitoring and processing.

        This method runs indefinitely and should be run as a background task.
        """
        logger.info(
            f"Starting continuous processing (poll interval: {self.settings.poll_interval_seconds}s)"
        )

        while True:
            try:
                # Connect to Gmail
                await asyncio.to_thread(self.gmail_client.connect)

                try:
                    # Process batch
                    stats = await self.process_batch()

                    logger.info(f"Batch stats: {json.dumps(stats, indent=2)}")

                finally:
                    # Disconnect from Gmail
                    await asyncio.to_thread(self.gmail_client.disconnect)

            except Exception as e:
                logger.error(f"Error in continuous processing: {e}", exc_info=True)

            # Wait before next poll
            logger.debug(f"Waiting {self.settings.poll_interval_seconds}s before next poll")
            await asyncio.sleep(self.settings.poll_interval_seconds)

    async def process_once(self) -> Dict[str, Any]:
        """
        Process emails once and exit.

        Returns:
            Processing statistics
        """
        logger.info("Processing emails (one-time)")

        try:
            # Connect to Gmail
            await asyncio.to_thread(self.gmail_client.connect)

            try:
                # Process batch
                stats = await self.process_batch()
                return stats

            finally:
                # Disconnect from Gmail
                await asyncio.to_thread(self.gmail_client.disconnect)

        except Exception as e:
            logger.error(f"Error processing emails: {e}", exc_info=True)
            raise
