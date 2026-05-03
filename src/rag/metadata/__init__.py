"""
Phase 2.5: Metadata and Source Management

This module provides metadata and source management services for the Mutual Fund FAQ Assistant.
"""

from .source_manager import SourceManager
from .metadata_manager import MetadataManager
from .citation_system import CitationSystem
from .version_control import VersionControl
from .main import Phase25Pipeline

__all__ = [
    "SourceManager",
    "MetadataManager", 
    "CitationSystem",
    "VersionControl",
    "Phase25Pipeline"
]

__version__ = "2.5.0"
