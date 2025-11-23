"""
Shared utility modules for ChiliHead OpsManager v2.1
Provides logging, metrics, and event handling functionality
"""

from .events import Event, EventPublisher, EventType
from .logging import get_logger, setup_logging
from .metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    time_operation,
    track_execution_time,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsRegistry",
    "time_operation",
    "track_execution_time",
    # Events
    "Event",
    "EventType",
    "EventPublisher",
]
