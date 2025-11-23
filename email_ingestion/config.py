"""
Configuration Management

Pydantic-based configuration for the email ingestion service.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Gmail IMAP Settings
    gmail_email: str = Field(..., description="Gmail email address")
    gmail_password: str = Field(..., description="Gmail app-specific password")
    imap_host: str = Field(default="imap.gmail.com", description="IMAP server host")
    imap_port: int = Field(default=993, description="IMAP server port")
    imap_timeout: int = Field(default=30, description="IMAP connection timeout in seconds")

    # Email Processing Settings
    inbox_folder: str = Field(default="INBOX", description="IMAP folder to monitor")
    mark_as_read: bool = Field(default=True, description="Mark processed emails as read")
    batch_size: int = Field(default=50, description="Number of emails to process per batch")
    max_attachment_size_mb: int = Field(default=25, description="Maximum attachment size in MB")

    # Attachment Storage
    attachment_storage_path: str = Field(
        default="./attachments",
        description="Local path to store attachments"
    )

    # AUBS Integration
    aubs_api_url: str = Field(..., description="AUBS API endpoint URL")
    aubs_api_key: Optional[str] = Field(default=None, description="AUBS API key")
    aubs_timeout: int = Field(default=60, description="AUBS API timeout in seconds")

    # Service Settings
    poll_interval_seconds: int = Field(
        default=60,
        description="Interval between email checks in seconds"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    enable_ssl: bool = Field(default=True, description="Enable SSL for IMAP")

    # Performance Settings
    max_workers: int = Field(default=5, description="Maximum concurrent workers")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay_seconds: int = Field(default=5, description="Delay between retries")

    @field_validator("gmail_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("imap_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @property
    def max_attachment_size_bytes(self) -> int:
        """Convert max attachment size to bytes."""
        return self.max_attachment_size_mb * 1024 * 1024
