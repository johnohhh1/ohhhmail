"""
Structured logging setup using loguru
Provides production-grade logging with JSON formatting, correlation IDs, and request tracking
"""

import json
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from loguru import logger

# Global request ID context
_request_id: Optional[str] = None


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the current request ID for correlation tracking across services.

    Args:
        request_id: Optional string request ID. If None, generates a new UUID.

    Returns:
        str: The request ID being used.

    Example:
        >>> rid = set_request_id()
        >>> logger.info("Processing request")  # Will include request_id in log
    """
    global _request_id
    _request_id = request_id or str(uuid4())
    return _request_id


def get_request_id() -> Optional[str]:
    """
    Get the current request ID.

    Returns:
        Optional[str]: Current request ID or None if not set.
    """
    return _request_id


def clear_request_id() -> None:
    """Clear the current request ID."""
    global _request_id
    _request_id = None


def json_sink(message: dict) -> None:
    """
    Custom JSON sink for loguru that formats logs as JSON for production.

    Args:
        message: Log message record from loguru.

    Example:
        Outputs JSON like:
        {
            "timestamp": "2024-01-15T10:30:45.123Z",
            "level": "INFO",
            "logger": "ohhhmail.agents.triage",
            "message": "Processing email",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "execution_id": "...",
            "extra": {...}
        }
    """
    log_record = message.record
    log_data = {
        "timestamp": log_record["time"].isoformat() + "Z",
        "level": log_record["level"].name,
        "logger": log_record["name"],
        "message": log_record["message"],
        "module": log_record["module"],
        "function": log_record["function"],
        "line": log_record["line"],
    }

    # Add request ID if available
    if _request_id:
        log_data["request_id"] = _request_id

    # Add extra fields from context
    if log_record["extra"]:
        log_data["context"] = dict(log_record["extra"])

    # Add exception info if present
    if log_record["exception"]:
        log_data["exception"] = {
            "type": log_record["exception"].exc_type.__name__,
            "message": str(log_record["exception"].exc_value),
            "traceback": log_record["exc_info"][2],
        }

    # Write JSON to stdout
    print(json.dumps(log_data, default=str), file=sys.stdout)


def pretty_sink(message: dict) -> None:
    """
    Custom pretty sink for loguru that formats logs for human readability in development.

    Args:
        message: Log message record from loguru.

    Example:
        Outputs like:
        2024-01-15 10:30:45.123 | INFO     | ohhhmail.agents.triage:123 - Processing email
        request_id="550e8400-e29b-41d4-a716-446655440000"
    """
    log_record = message.record

    # Format base log line
    timestamp = log_record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = log_record["level"].name
    logger_name = log_record["name"]
    line_no = log_record["line"]
    function = log_record["function"]
    msg = log_record["message"]

    # Color codes for terminal
    level_colors = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    reset = "\033[0m"
    color = level_colors.get(level, reset)

    # Build output
    output = f"{timestamp} | {color}{level:<8}{reset} | {logger_name}:{function}:{line_no} - {msg}"

    # Add request ID if available
    if _request_id:
        output += f"\n  request_id={_request_id}"

    # Add extra fields
    if log_record["extra"]:
        for key, value in log_record["extra"].items():
            output += f"\n  {key}={value}"

    # Add exception info
    if log_record["exception"]:
        exc = log_record["exception"]
        output += f"\n  Exception: {exc.exc_type.__name__}: {exc.exc_value}"

    print(output, file=sys.stdout)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
) -> None:
    """
    Initialize structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                Can also be read from LOG_LEVEL environment variable.
        format_type: Log format type - "json" for production, "pretty" for development.
                     Can also be read from LOG_FORMAT environment variable.
        log_file: Optional file path to write logs to. If provided, logs will be
                  written to both console and file.

    Returns:
        None

    Example:
        >>> setup_logging(level="DEBUG", format_type="pretty")
        >>> logger.info("Application started")

        For production:
        >>> setup_logging(level="INFO", format_type="json")
        >>> logger.info("Request processed", execution_id="123", status="success")

    Raises:
        ValueError: If level is not a valid log level.
    """
    import os

    # Read from environment variables if provided
    level = os.getenv("LOG_LEVEL", level).upper()
    format_type = os.getenv("LOG_FORMAT", format_type).lower()

    # Validate level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level not in valid_levels:
        raise ValueError(
            f"Invalid log level: {level}. Must be one of {valid_levels}"
        )

    if format_type not in {"json", "pretty"}:
        raise ValueError(
            f"Invalid format type: {format_type}. Must be 'json' or 'pretty'"
        )

    # Remove default handler
    logger.remove()

    # Select sink function
    sink_fn = json_sink if format_type == "json" else pretty_sink

    # Add console handler
    logger.add(
        sink_fn,
        level=level,
        format="{message}",  # Message is handled by sink function
        colorize=False,
    )

    # Add file handler if requested
    if log_file:
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",  # Rotate when file reaches 10MB
            retention="7 days",  # Keep logs for 7 days
        )


def get_logger(name: str) -> object:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name, typically __name__.

    Returns:
        Logger instance with module context.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.error("Failed to process", exc_info=True)

    Context binding example:
        >>> logger = get_logger(__name__)
        >>> logger.bind(execution_id="123", email_id="456").info("Processing")
    """
    return logger.bind(module=name)


# Convenience context manager for request tracking
class RequestContext:
    """
    Context manager for tracking a request across function calls.

    Example:
        >>> with RequestContext() as rid:
        ...     logger.info("Processing request")
        ...     process_email()  # All logs will include this request_id

        >>> with RequestContext("custom-id-123"):
        ...     logger.info("Custom request tracking")
    """

    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize request context.

        Args:
            request_id: Optional custom request ID. If None, generates a UUID.
        """
        self.request_id = request_id
        self.previous_id = None

    def __enter__(self) -> str:
        """Enter context and set request ID."""
        self.previous_id = _request_id
        return set_request_id(self.request_id)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore previous request ID."""
        global _request_id
        _request_id = self.previous_id


# Convenience decorator for execution timing
def log_execution_time(level: str = "INFO"):
    """
    Decorator to log execution time of a function.

    Args:
        level: Log level for the timing message.

    Example:
        >>> @log_execution_time()
        ... def process_email(email_id: str) -> dict:
        ...     # Processing logic
        ...     return result
        >>> process_email("123")  # Logs: "process_email executed in 0.234s"
    """
    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                log_func = getattr(logger, level.lower())
                log_func(
                    f"{func.__name__} executed in {elapsed:.3f}s",
                    execution_time_ms=int(elapsed * 1000),
                )
        return wrapper
    return decorator
