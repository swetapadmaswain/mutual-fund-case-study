"""
Phase 2.6: Performance Optimization and Testing

This module provides performance optimization, comprehensive testing, monitoring, and analytics services for the Mutual Fund FAQ Assistant.
"""

from .performance_optimizer import PerformanceOptimizer
from .testing_framework import TestingFramework
from .monitoring_analytics import MonitoringAnalytics
from .caching_optimizer import CachingOptimizer
from .load_testing import LoadTesting
from .main import Phase26Pipeline

__all__ = [
    "PerformanceOptimizer",
    "TestingFramework",
    "MonitoringAnalytics",
    "CachingOptimizer",
    "LoadTesting",
    "Phase26Pipeline"
]

__version__ = "2.6.0"
