"""Backward-compatible import path for Feature 06's metric registry."""

from src.observability.metrics import DurationSummary, MetricRegistry, MetricsSnapshot


class ApiMetrics(MetricRegistry):
    """Compatibility spelling retained for callers introduced in Feature 05."""


__all__ = ["ApiMetrics", "DurationSummary", "MetricRegistry", "MetricsSnapshot"]
