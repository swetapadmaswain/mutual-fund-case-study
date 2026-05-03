"""
Phase 3: Query Processing and Response Generation

This module provides query classification, response generation, and formatting capabilities for the Mutual Fund FAQ Assistant.
"""

from .query_classifier import QueryClassifier
from .response_generator import ResponseGenerator
from .response_formatter import ResponseFormatter
from .compliance_safety import ComplianceSafetyLayer
from .integration_tests import RAGIntegrationTests
from .main import Phase3Pipeline

__all__ = [
    "QueryClassifier",
    "ResponseGenerator", 
    "ResponseFormatter",
    "ComplianceSafetyLayer",
    "RAGIntegrationTests",
    "Phase3Pipeline"
]

__version__ = "3.0.0"
