# Real-Time Analytics and Monitoring System
"""
Analytics module for the Advanced DDoS Testing Framework.
Provides metrics collection, performance tracking, and visualization.
"""

from .metrics_collector import (
    RealTimeMetricsCollector,
    MetricAggregator,
    MetricPoint,
    AggregatedMetric,
    get_metrics_collector,
    collect_metric,
    collect_attack_metrics
)

from .performance_tracker import MultiDimensionalPerformanceTracker as PerformanceTracker
from .visualization_engine import AdvancedVisualizationEngine as VisualizationEngine
from .predictive_analytics import PredictiveAnalyticsSystem as PredictiveAnalytics

# Alias for backward compatibility
MetricsCollector = RealTimeMetricsCollector

__all__ = [
    'RealTimeMetricsCollector',
    'MetricsCollector',
    'MetricAggregator',
    'MetricPoint',
    'AggregatedMetric',
    'get_metrics_collector',
    'collect_metric',
    'collect_attack_metrics',
    'PerformanceTracker',
    'VisualizationEngine',
    'PredictiveAnalytics'
]
