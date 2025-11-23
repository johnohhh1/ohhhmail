"""
Prometheus metrics collection for monitoring and observability.
Provides counters, gauges, histograms, and helper decorators for performance tracking.
"""

import functools
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class Counter:
    """
    A counter metric that monotonically increases.

    Counters are useful for tracking total number of events,
    requests processed, errors encountered, etc.

    Example:
        >>> emails_processed = Counter("emails_processed_total", "Total emails processed")
        >>> emails_processed.inc()
        >>> emails_processed.inc(5)  # Increment by 5
        >>> print(emails_processed.value)  # 6
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ):
        """
        Initialize a counter metric.

        Args:
            name: Metric name (e.g., "emails_processed_total").
            description: Human-readable description of the metric.
            labels: Optional list of label names for dimensional data.

        Raises:
            ValueError: If name doesn't follow Prometheus naming conventions.
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.value = 0
        self.label_values: Dict[tuple, float] = {}

        if not self._is_valid_metric_name(name):
            raise ValueError(
                f"Invalid metric name: {name}. "
                "Must match [a-zA-Z_:][a-zA-Z0-9_:]*"
            )

    @staticmethod
    def _is_valid_metric_name(name: str) -> bool:
        """Validate metric name follows Prometheus conventions."""
        if not name:
            return False
        if not name[0].isalpha() and name[0] not in ("_", ":"):
            return False
        return all(c.isalnum() or c in ("_", ":") for c in name)

    def inc(self, amount: float = 1.0) -> None:
        """
        Increment the counter by the given amount.

        Args:
            amount: Value to increment by (default 1.0).

        Raises:
            ValueError: If amount is negative.

        Example:
            >>> counter.inc()
            >>> counter.inc(10)
        """
        if amount < 0:
            raise ValueError("Counter can only increase (amount must be >= 0)")
        self.value += amount

    def inc_by_labels(self, labels_dict: Dict[str, str], amount: float = 1.0) -> None:
        """
        Increment the counter with specific label values.

        Args:
            labels_dict: Dictionary mapping label names to values.
            amount: Value to increment by.

        Example:
            >>> counter = Counter("emails_processed", labels=["agent_type"])
            >>> counter.inc_by_labels({"agent_type": "triage"})
            >>> counter.inc_by_labels({"agent_type": "context"}, 5)
        """
        label_tuple = tuple(labels_dict.get(label) for label in self.labels)
        if amount < 0:
            raise ValueError("Counter can only increase")
        self.label_values[label_tuple] = self.label_values.get(label_tuple, 0) + amount

    def __repr__(self) -> str:
        return f"Counter({self.name}={self.value})"


class Gauge:
    """
    A gauge metric that can increase or decrease.

    Gauges are useful for tracking current state like memory usage,
    active connections, queue size, etc.

    Example:
        >>> active_executions = Gauge("active_executions", "Currently running executions")
        >>> active_executions.set(5)
        >>> active_executions.inc()  # 6
        >>> active_executions.dec(2)  # 4
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ):
        """
        Initialize a gauge metric.

        Args:
            name: Metric name (e.g., "active_connections").
            description: Human-readable description.
            labels: Optional list of label names.

        Raises:
            ValueError: If name doesn't follow Prometheus naming conventions.
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.value = 0.0
        self.label_values: Dict[tuple, float] = {}

        if not Counter._is_valid_metric_name(name):
            raise ValueError(
                f"Invalid metric name: {name}. "
                "Must match [a-zA-Z_:][a-zA-Z0-9_:]*"
            )

    def set(self, value: float) -> None:
        """
        Set the gauge to a specific value.

        Args:
            value: Numeric value to set.

        Example:
            >>> gauge.set(42)
        """
        self.value = float(value)

    def inc(self, amount: float = 1.0) -> None:
        """
        Increment the gauge.

        Args:
            amount: Value to add (can be negative).

        Example:
            >>> gauge.inc(5)
            >>> gauge.inc(-2)
        """
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        """
        Decrement the gauge.

        Args:
            amount: Value to subtract.

        Example:
            >>> gauge.dec()
            >>> gauge.dec(3)
        """
        self.value -= amount

    def set_by_labels(self, labels_dict: Dict[str, str], value: float) -> None:
        """
        Set gauge value with specific label values.

        Args:
            labels_dict: Dictionary mapping label names to values.
            value: Value to set.

        Example:
            >>> gauge = Gauge("agent_execution_time", labels=["agent_type"])
            >>> gauge.set_by_labels({"agent_type": "triage"}, 1.5)
        """
        label_tuple = tuple(labels_dict.get(label) for label in self.labels)
        self.label_values[label_tuple] = float(value)

    def __repr__(self) -> str:
        return f"Gauge({self.name}={self.value})"


class Histogram:
    """
    A histogram metric that tracks the distribution of values.

    Histograms are useful for measuring request duration, response size,
    processing time, etc. They automatically create buckets.

    Example:
        >>> request_duration = Histogram(
        ...     "request_duration_seconds",
        ...     "Request processing duration",
        ...     buckets=[0.1, 0.5, 1.0, 5.0]
        ... )
        >>> request_duration.observe(0.234)
        >>> request_duration.observe(1.5)
    """

    # Standard Prometheus buckets for timing in seconds
    DEFAULT_BUCKETS = (
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[tuple] = None,
        labels: Optional[List[str]] = None,
    ):
        """
        Initialize a histogram metric.

        Args:
            name: Metric name (e.g., "request_duration_seconds").
            description: Human-readable description.
            buckets: Tuple of increasing bucket boundaries. Uses default if None.
            labels: Optional list of label names.

        Raises:
            ValueError: If buckets are not sorted in ascending order.
        """
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self.labels = labels or []
        self.values: List[float] = []
        self.bucket_counts: Dict[tuple, Dict[float, int]] = {}

        # Validate buckets
        if not all(self.buckets[i] <= self.buckets[i + 1] for i in range(len(self.buckets) - 1)):
            raise ValueError("Buckets must be sorted in ascending order")

        if not Counter._is_valid_metric_name(name):
            raise ValueError(
                f"Invalid metric name: {name}. "
                "Must match [a-zA-Z_:][a-zA-Z0-9_:]*"
            )

    def observe(self, value: float) -> None:
        """
        Record an observation in the histogram.

        Args:
            value: Numeric value to observe.

        Example:
            >>> histogram.observe(0.234)  # Record a measurement
            >>> histogram.observe(1.5)
        """
        self.values.append(float(value))

    def observe_by_labels(
        self,
        labels_dict: Dict[str, str],
        value: float,
    ) -> None:
        """
        Record an observation with specific label values.

        Args:
            labels_dict: Dictionary mapping label names to values.
            value: Value to observe.

        Example:
            >>> hist = Histogram("processing_time", labels=["agent_type"])
            >>> hist.observe_by_labels({"agent_type": "triage"}, 0.5)
        """
        label_tuple = tuple(labels_dict.get(label) for label in self.labels)
        if label_tuple not in self.bucket_counts:
            self.bucket_counts[label_tuple] = {b: 0 for b in self.buckets}
        self.bucket_counts[label_tuple][float(value)] = (
            self.bucket_counts[label_tuple].get(float(value), 0) + 1
        )

    def get_percentile(self, percentile: float) -> Optional[float]:
        """
        Get the value at a given percentile.

        Args:
            percentile: Percentile to calculate (0-100).

        Returns:
            Value at the percentile, or None if no observations.

        Example:
            >>> histogram.observe(0.5)
            >>> histogram.observe(1.5)
            >>> histogram.get_percentile(95)  # 95th percentile
        """
        if not self.values:
            return None
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_bucket_count(self, bucket: float) -> int:
        """
        Get count of observations in a specific bucket.

        Args:
            bucket: Bucket boundary to check.

        Returns:
            Number of observations <= bucket.

        Example:
            >>> histogram.get_bucket_count(0.1)  # Count <= 0.1s
        """
        return sum(1 for v in self.values if v <= bucket)

    def __repr__(self) -> str:
        count = len(self.values)
        return f"Histogram({self.name}, observations={count})"


class MetricsRegistry:
    """
    Central registry for all metrics in the application.

    Manages creation and tracking of counters, gauges, and histograms.
    Provides export functionality for Prometheus.

    Example:
        >>> registry = MetricsRegistry()
        >>> registry.counter("emails_processed", "Total emails")
        >>> registry.gauge("queue_size", "Current queue size")
        >>> registry.histogram("processing_time", "Processing duration")
    """

    def __init__(self):
        """Initialize the metrics registry."""
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}

    def counter(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ) -> Counter:
        """
        Get or create a counter metric.

        Args:
            name: Metric name.
            description: Metric description.
            labels: Optional label names.

        Returns:
            Counter instance.

        Example:
            >>> counter = registry.counter("requests_total")
            >>> counter.inc()
        """
        if name not in self.counters:
            self.counters[name] = Counter(name, description, labels)
        return self.counters[name]

    def gauge(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ) -> Gauge:
        """
        Get or create a gauge metric.

        Args:
            name: Metric name.
            description: Metric description.
            labels: Optional label names.

        Returns:
            Gauge instance.

        Example:
            >>> gauge = registry.gauge("active_connections")
            >>> gauge.set(42)
        """
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description, labels)
        return self.gauges[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        buckets: Optional[tuple] = None,
        labels: Optional[List[str]] = None,
    ) -> Histogram:
        """
        Get or create a histogram metric.

        Args:
            name: Metric name.
            description: Metric description.
            buckets: Optional bucket boundaries.
            labels: Optional label names.

        Returns:
            Histogram instance.

        Example:
            >>> hist = registry.histogram("request_duration", buckets=(0.1, 1.0, 5.0))
            >>> hist.observe(0.5)
        """
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description, buckets, labels)
        return self.histograms[name]

    def export_prometheus(self) -> str:
        """
        Export all metrics in Prometheus text format.

        Returns:
            String in Prometheus format ready for scraping.

        Example:
            >>> prometheus_text = registry.export_prometheus()
            >>> print(prometheus_text)
            # HELP emails_processed_total Total emails processed
            # TYPE emails_processed_total counter
            emails_processed_total 42
        """
        lines = []

        # Export counters
        for counter in self.counters.values():
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            lines.append(f"{counter.name} {counter.value}")
            for label_tuple, value in counter.label_values.items():
                label_str = self._format_labels(counter.labels, label_tuple)
                lines.append(f"{counter.name}{{{label_str}}} {value}")

        # Export gauges
        for gauge in self.gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            lines.append(f"{gauge.name} {gauge.value}")
            for label_tuple, value in gauge.label_values.items():
                label_str = self._format_labels(gauge.labels, label_tuple)
                lines.append(f"{gauge.name}{{{label_str}}} {value}")

        # Export histograms
        for histogram in self.histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.description}")
            lines.append(f"# TYPE {histogram.name} histogram")
            if histogram.values:
                for bucket in histogram.buckets:
                    count = histogram.get_bucket_count(bucket)
                    lines.append(f'{histogram.name}_bucket{{le="{bucket}"}} {count}')
                lines.append(
                    f'{histogram.name}_bucket{{le="+Inf"}} {len(histogram.values)}'
                )
                lines.append(f"{histogram.name}_sum {sum(histogram.values)}")
                lines.append(f"{histogram.name}_count {len(histogram.values)}")

        return "\n".join(lines)

    @staticmethod
    def _format_labels(labels: List[str], values: tuple) -> str:
        """Format labels for Prometheus output."""
        if not labels or not values:
            return ""
        pairs = [f'{k}="{v}"' for k, v in zip(labels, values)]
        return ",".join(pairs)


# Global registry instance
_global_registry = MetricsRegistry()


def get_registry() -> MetricsRegistry:
    """
    Get the global metrics registry.

    Returns:
        MetricsRegistry: Global registry instance.

    Example:
        >>> registry = get_registry()
        >>> counter = registry.counter("requests_total")
    """
    return _global_registry


def time_operation(operation_name: str) -> Callable[[F], F]:
    """
    Decorator to automatically track operation timing in milliseconds.

    Creates or uses an existing histogram metric for the operation.

    Args:
        operation_name: Name of the operation for the histogram.

    Returns:
        Decorated function.

    Example:
        >>> @time_operation("email_processing")
        ... def process_email(email_id: str) -> dict:
        ...     # Process email
        ...     return result
        >>> process_email("123")  # Automatically tracked
    """
    histogram = _global_registry.histogram(
        f"{operation_name}_duration_ms",
        f"Duration of {operation_name} in milliseconds",
    )

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.time() - start) * 1000
                histogram.observe(elapsed_ms)
        return wrapper
    return decorator


def track_execution_time(
    counter_name: str = "operations_total",
    histogram_name: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to track both count and duration of function execution.

    Creates counter for total executions and histogram for timing.

    Args:
        counter_name: Name for the counter metric.
        histogram_name: Name for the histogram. If None, uses counter_name + "_duration_ms".

    Returns:
        Decorated function.

    Example:
        >>> @track_execution_time("emails_processed", "email_duration_ms")
        ... def process_email(email: dict) -> dict:
        ...     return result

        >>> process_email({"id": "123"})
        >>> # Increments counter and records timing
    """
    counter = _global_registry.counter(counter_name, f"Count of {counter_name}")
    hist_name = histogram_name or f"{counter_name}_duration_ms"
    histogram = _global_registry.histogram(hist_name, f"Duration of {counter_name}")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                counter.inc()
                return result
            finally:
                elapsed_ms = (time.time() - start) * 1000
                histogram.observe(elapsed_ms)
        return wrapper
    return decorator
