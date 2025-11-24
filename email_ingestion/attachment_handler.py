"""
Attachment Handler

Handles saving, organizing, and managing email attachments.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import mimetypes

from email_parser import EmailAttachment, ParsedEmail

logger = logging.getLogger(__name__)


class AttachmentHandler:
    """Handler for email attachments."""

    def __init__(self, storage_path: str):
        """
        Initialize attachment handler.

        Args:
            storage_path: Base path for storing attachments
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        """Create storage directory if it doesn't exist."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Attachment storage directory: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise

    @staticmethod
    def generate_file_hash(content: bytes) -> str:
        """
        Generate SHA-256 hash of file content.

        Args:
            content: File content

        Returns:
            Hex string of hash
        """
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '\x00', '\n', '\r']
        sanitized = filename

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')

        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext

        return sanitized

    def get_storage_path_for_email(self, email_id: str, date: Optional[datetime] = None) -> Path:
        """
        Get storage path for an email's attachments.

        Args:
            email_id: Email ID
            date: Email date for organizing by date

        Returns:
            Path object for storage directory
        """
        if date:
            # Organize by year/month/day
            date_path = date.strftime("%Y/%m/%d")
            storage_dir = self.storage_path / date_path / email_id
        else:
            storage_dir = self.storage_path / email_id

        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir

    def save_attachment(
        self,
        attachment: EmailAttachment,
        email_id: str,
        email_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Save attachment to disk.

        Args:
            attachment: EmailAttachment object
            email_id: Email ID for organization
            email_date: Email date for organization

        Returns:
            Dictionary with save metadata

        Raises:
            IOError: If save fails
        """
        try:
            # Get storage directory
            storage_dir = self.get_storage_path_for_email(email_id, email_date)

            # Sanitize filename
            safe_filename = self.sanitize_filename(attachment.filename)

            # Generate unique filename if file exists
            file_path = storage_dir / safe_filename
            if file_path.exists():
                name, ext = os.path.splitext(safe_filename)
                counter = 1
                while file_path.exists():
                    safe_filename = f"{name}_{counter}{ext}"
                    file_path = storage_dir / safe_filename
                    counter += 1

            # Save file
            file_path.write_bytes(attachment.content)

            # Generate hash for deduplication
            file_hash = self.generate_file_hash(attachment.content)

            # Get file stats
            file_stats = file_path.stat()

            metadata = {
                "filename": safe_filename,
                "original_filename": attachment.filename,
                "path": str(file_path.absolute()),
                "relative_path": str(file_path.relative_to(self.storage_path)),
                "size": file_stats.st_size,
                "hash": file_hash,
                "content_type": attachment.content_type,
                "content_id": attachment.content_id,
                "saved_at": datetime.utcnow().isoformat(),
                "email_id": email_id
            }

            logger.info(f"Saved attachment: {safe_filename} ({file_stats.st_size} bytes)")
            return metadata

        except Exception as e:
            logger.error(f"Failed to save attachment {attachment.filename}: {e}")
            raise

    def save_all_attachments(self, parsed_email: ParsedEmail) -> list[Dict[str, Any]]:
        """
        Save all attachments from a parsed email.

        Args:
            parsed_email: ParsedEmail object

        Returns:
            List of attachment metadata dictionaries
        """
        saved_attachments = []

        for attachment in parsed_email.attachments:
            try:
                metadata = self.save_attachment(
                    attachment,
                    parsed_email.email_id,
                    parsed_email.date
                )
                saved_attachments.append(metadata)
            except Exception as e:
                logger.error(f"Failed to save attachment: {e}")
                # Continue processing other attachments
                continue

        logger.info(
            f"Saved {len(saved_attachments)}/{len(parsed_email.attachments)} attachments "
            f"for email {parsed_email.email_id}"
        )

        return saved_attachments

    def delete_attachment(self, file_path: str) -> bool:
        """
        Delete an attachment file.

        Args:
            file_path: Path to attachment file

        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted attachment: {file_path}")
                return True
            else:
                logger.warning(f"Attachment not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete attachment {file_path}: {e}")
            return False

    def cleanup_empty_directories(self) -> int:
        """
        Remove empty directories in storage path.

        Returns:
            Number of directories removed
        """
        removed_count = 0

        try:
            # Walk from bottom up to remove nested empty directories
            for dirpath, dirnames, filenames in os.walk(self.storage_path, topdown=False):
                if not dirnames and not filenames and dirpath != str(self.storage_path):
                    try:
                        Path(dirpath).rmdir()
                        removed_count += 1
                        logger.debug(f"Removed empty directory: {dirpath}")
                    except Exception as e:
                        logger.warning(f"Failed to remove directory {dirpath}: {e}")
        except Exception as e:
            logger.error(f"Failed to cleanup directories: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} empty directories")

        return removed_count

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about attachment storage.

        Returns:
            Dictionary with storage statistics
        """
        total_files = 0
        total_size = 0

        try:
            for root, dirs, files in os.walk(self.storage_path):
                total_files += len(files)
                for file in files:
                    try:
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.storage_path.absolute())
        }
