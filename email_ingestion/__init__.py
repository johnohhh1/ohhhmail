"""
Email Ingestion Service

A production-ready email ingestion service that connects to Gmail via IMAP,
parses emails, extracts attachments, and forwards data to AUBS (Anthropic Universal Backend Service).
"""

__version__ = "1.0.0"
__author__ = "OhhhMail Team"

from .config import Settings
from .processor import EmailProcessor

__all__ = ["Settings", "EmailProcessor"]
