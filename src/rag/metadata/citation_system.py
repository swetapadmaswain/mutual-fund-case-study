"""
Citation System for Phase 2.5

Generates accurate citations, handles multiple sources, validates formats, and tracks usage.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class Citation:
    """Represents a citation with all required information."""
    chunk_id: str
    source_url: str
    source_title: str
    fund_name: str
    document_type: str
    content_type: str
    page_number: Optional[int]
    section: str
    last_updated: str
    confidence_score: float
    citation_format: str
    formatted_citation: str
    metadata: Dict[str, Any]

@dataclass
class UsageStats:
    """Statistics for citation usage."""
    total_uses: int
    first_used: datetime
    last_used: datetime
    query_types: List[str]
    response_types: List[str]
    average_relevance: float

class CitationSystem:
    """
    Generates accurate citations and manages citation tracking.
    
    Features:
    - Accurate citation generation
    - Multiple source handling
    - Format validation
    - Usage tracking
    - Citation analytics
    """
    
    def __init__(self, cache_dir: str = "cache/citation_system"):
        """
        Initialize citation system.
        
        Args:
            cache_dir: Directory for caching citation data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Citation storage
        self.citations: Dict[str, Citation] = {}
        self.usage_stats: Dict[str, UsageStats] = {}
        
        # Citation formats
        self.formats = self._initialize_formats()
        
        # Configuration
        self.default_format = "hdfc_standard"
        self.max_citation_length = 200
        self.confidence_threshold = 0.7
        
        # Analytics
        self.citation_frequency = Counter()
        self.format_usage = Counter()
        
        # Load existing data
        self._load_citations()
        self._load_usage_stats()
        
        logger.info(f"Citation System initialized with {len(self.citations)} citations")
    
    def _initialize_formats(self) -> Dict[str, Dict[str, Any]]:
        """Initialize citation format templates."""
        return {
            "hdfc_standard": {
                "template": "HDFC Mutual Fund - {fund_name} ({document_type}). {content_type}. Available at: {source_url}. Last updated: {last_updated}.",
                "required_fields": ["fund_name", "document_type", "content_type", "source_url", "last_updated"],
                "optional_fields": ["page_number", "section"]
            },
            "academic": {
                "template": "{fund_name} ({document_type}). {content_type}. HDFC Mutual Fund. Retrieved {last_updated} from {source_url}.",
                "required_fields": ["fund_name", "document_type", "content_type", "source_url", "last_updated"],
                "optional_fields": ["page_number", "section"]
            },
            "simple": {
                "template": "Source: {source_url} (HDFC {fund_name} - {document_type})",
                "required_fields": ["source_url", "fund_name", "document_type"],
                "optional_fields": ["content_type", "last_updated"]
            },
            "minimal": {
                "template": "{source_url}",
                "required_fields": ["source_url"],
                "optional_fields": []
            }
        }
    
    def _load_citations(self) -> None:
        """Load citations from cache."""
        citations_file = self.cache_dir / "citations.json"
        
        if citations_file.exists():
            try:
                with open(citations_file, 'r') as f:
                    data = json.load(f)
                
                for citation_id, citation_data in data.items():
                    self.citations[citation_id] = Citation(**citation_data)
                
                logger.info(f"Loaded {len(self.citations)} citations from cache")
                
            except Exception as e:
                logger.error(f"Error loading citations: {e}")
    
    def _load_usage_stats(self) -> None:
        """Load usage statistics from cache."""
        stats_file = self.cache_dir / "usage_stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                for citation_id, stats_data in data.items():
                    stats_data['first_used'] = datetime.fromisoformat(stats_data['first_used'])
                    stats_data['last_used'] = datetime.fromisoformat(stats_data['last_used'])
                    self.usage_stats[citation_id] = UsageStats(**stats_data)
                
                logger.info(f"Loaded usage stats for {len(self.usage_stats)} citations")
                
            except Exception as e:
                logger.error(f"Error loading usage stats: {e}")
    
    def _save_citations(self) -> None:
        """Save citations to cache."""
        try:
            citations_file = self.cache_dir / "citations.json"
            
            serializable_citations = {}
            for citation_id, citation in self.citations.items():
                serializable_citations[citation_id] = asdict(citation)
            
            with open(citations_file, 'w') as f:
                json.dump(serializable_citations, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving citations: {e}")
    
    def _save_usage_stats(self) -> None:
        """Save usage statistics to cache."""
        try:
            stats_file = self.cache_dir / "usage_stats.json"
            
            serializable_stats = {}
            for citation_id, stats in self.usage_stats.items():
                stats_dict = asdict(stats)
                stats_dict['first_used'] = stats.first_used.isoformat()
                stats_dict['last_used'] = stats.last_used.isoformat()
                serializable_stats[citation_id] = stats_dict
            
            with open(stats_file, 'w') as f:
                json.dump(serializable_stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving usage stats: {e}")
    
    def generate_citation(self, chunk: Dict[str, Any], format_name: Optional[str] = None) -> Citation:
        """
        Generate citation for a chunk.
        
        Args:
            chunk: Chunk dictionary with metadata
            format_name: Citation format to use (optional)
            
        Returns:
            Citation object
        """
        format_name = format_name or self.default_format
        
        if format_name not in self.formats:
            format_name = self.default_format
        
        format_template = self.formats[format_name]
        
        # Extract citation data
        citation_data = self._extract_citation_data(chunk)
        
        # Validate required fields
        missing_fields = [
            field for field in format_template["required_fields"]
            if field not in citation_data or not citation_data[field]
        ]
        
        if missing_fields:
            logger.warning(f"Missing required citation fields: {missing_fields}")
        
        # Generate formatted citation
        formatted_citation = self._format_citation(citation_data, format_template["template"])
        
        # Create citation ID
        citation_id = self._generate_citation_id(citation_data)
        
        # Create citation object
        citation = Citation(
            chunk_id=chunk.get('chunk_id', ''),
            source_url=citation_data.get('source_url', ''),
            source_title=citation_data.get('source_title', ''),
            fund_name=citation_data.get('fund_name', ''),
            document_type=citation_data.get('document_type', ''),
            content_type=citation_data.get('content_type', ''),
            page_number=citation_data.get('page_number'),
            section=citation_data.get('section', ''),
            last_updated=citation_data.get('last_updated', ''),
            confidence_score=citation_data.get('confidence_score', 1.0),
            citation_format=format_name,
            formatted_citation=formatted_citation,
            metadata=citation_data
        )
        
        # Store citation
        self.citations[citation_id] = citation
        
        # Update analytics
        self.citation_frequency[citation_id] += 1
        self.format_usage[format_name] += 1
        
        return citation
    
    def _extract_citation_data(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract citation data from chunk metadata."""
        citation_data = {}
        
        # Direct field mapping
        field_mapping = {
            'source_url': 'source_url',
            'fund_name': 'fund_name',
            'document_type': 'document_type',
            'content_type': 'content_type',
            'page_number': 'page_number',
            'section': 'section',
            'last_updated': 'last_updated',
            'confidence_score': 'confidence_score'
        }
        
        for chunk_field, citation_field in field_mapping.items():
            if chunk_field in chunk:
                citation_data[citation_field] = chunk[chunk_field]
        
        # Generate source title if not present
        if 'source_title' not in citation_data:
            citation_data['source_title'] = self._generate_source_title(citation_data)
        
        return citation_data
    
    def _generate_source_title(self, citation_data: Dict[str, Any]) -> str:
        """Generate source title from citation data."""
        fund_name = citation_data.get('fund_name', 'HDFC Mutual Fund')
        document_type = citation_data.get('document_type', 'Document')
        
        return f"{fund_name} - {document_type.title()}"
    
    def _format_citation(self, data: Dict[str, Any], template: str) -> str:
        """Format citation using template."""
        try:
            # Replace placeholders with actual data
            formatted = template.format(**data)
            
            # Clean up extra spaces and ensure proper formatting
            formatted = re.sub(r'\s+', ' ', formatted).strip()
            
            # Ensure citation length is reasonable
            if len(formatted) > self.max_citation_length:
                # Truncate intelligently
                formatted = formatted[:self.max_citation_length - 3] + "..."
            
            return formatted
            
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            # Fallback to simple format
            return data.get('source_url', 'Source unavailable')
    
    def _generate_citation_id(self, citation_data: Dict[str, Any]) -> str:
        """Generate unique citation ID."""
        # Create hash from key citation data
        hash_input = f"{citation_data.get('source_url', '')}{citation_data.get('chunk_id', '')}"
        citation_hash = hashlib.md5(hash_input.encode()).hexdigest()
        
        return f"citation_{citation_hash[:12]}"
    
    def handle_multiple_sources(self, chunks: List[Dict[str, Any]], format_name: Optional[str] = None) -> Citation:
        """
        Handle multiple sources for a single citation.
        
        Args:
            chunks: List of chunk dictionaries
            format_name: Citation format to use
            
        Returns:
            Consolidated Citation object
        """
        if not chunks:
            raise ValueError("No chunks provided for citation")
        
        if len(chunks) == 1:
            return self.generate_citation(chunks[0], format_name)
        
        # Generate individual citations
        individual_citations = [
            self.generate_citation(chunk, format_name) 
            for chunk in chunks
        ]
        
        # Consolidate citation data
        consolidated_data = self._consolidate_citation_data(individual_citations)
        
        # Create consolidated citation
        format_name = format_name or self.default_format
        format_template = self.formats[format_name]
        
        # Create multi-source template
        multi_source_template = self._create_multi_source_template(format_template["template"])
        
        formatted_citation = self._format_citation(consolidated_data, multi_source_template)
        
        # Create citation ID
        citation_id = self._generate_citation_id(consolidated_data)
        
        # Create consolidated citation object
        consolidated_citation = Citation(
            chunk_id="multi_source",
            source_url=consolidated_data.get('source_url', ''),
            source_title=consolidated_data.get('source_title', ''),
            fund_name=consolidated_data.get('fund_name', ''),
            document_type=consolidated_data.get('document_type', ''),
            content_type=consolidated_data.get('content_type', ''),
            page_number=consolidated_data.get('page_number'),
            section=consolidated_data.get('section', ''),
            last_updated=consolidated_data.get('last_updated', ''),
            confidence_score=consolidated_data.get('confidence_score', 1.0),
            citation_format=f"{format_name}_multi",
            formatted_citation=formatted_citation,
            metadata={
                **consolidated_data,
                "source_count": len(chunks),
                "individual_citations": [c.citation_id for c in individual_citations]
            }
        )
        
        # Store consolidated citation
        self.citations[citation_id] = consolidated_citation
        
        return consolidated_citation
    
    def _consolidate_citation_data(self, citations: List[Citation]) -> Dict[str, Any]:
        """Consolidate citation data from multiple citations."""
        consolidated = {}
        
        # Use the most recent or highest confidence citation as base
        base_citation = max(citations, key=lambda c: (c.confidence_score, c.last_updated))
        
        # Copy base data
        for key, value in asdict(base_citation).items():
            if key not in ['chunk_id', 'citation_id', 'formatted_citation']:
                consolidated[key] = value
        
        # Handle multiple sources
        if len(citations) > 1:
            source_urls = [c.source_url for c in citations if c.source_url]
            if len(source_urls) > 1:
                consolidated['source_url'] = f"Multiple sources: {', '.join(source_urls[:3])}"
                if len(source_urls) > 3:
                    consolidated['source_url'] += f" and {len(source_urls) - 3} more"
        
        # Consolidate fund names if different
        fund_names = list(set(c.fund_name for c in citations if c.fund_name))
        if len(fund_names) > 1:
            consolidated['fund_name'] = f"Multiple funds: {', '.join(fund_names[:2])}"
        
        return consolidated
    
    def _create_multi_source_template(self, base_template: str) -> str:
        """Create template for multiple sources."""
        # Modify template to handle multiple sources
        if "{source_url}" in base_template:
            multi_template = base_template.replace(
                "{source_url}",
                "{source_url} (Multiple sources)"
            )
        else:
            multi_template = base_template
        
        return multi_template
    
    def validate_format(self, citation: Citation) -> bool:
        """
        Validate citation format.
        
        Args:
            citation: Citation object to validate
            
        Returns:
            True if format is valid
        """
        format_template = self.formats.get(citation.citation_format)
        
        if not format_template:
            logger.error(f"Unknown citation format: {citation.citation_format}")
            return False
        
        # Check required fields
        for field in format_template["required_fields"]:
            if not hasattr(citation, field) or not getattr(citation, field):
                logger.error(f"Missing required citation field: {field}")
                return False
        
        # Validate URL format
        if citation.source_url:
            try:
                parsed = urlparse(citation.source_url)
                if not parsed.scheme or not parsed.netloc:
                    logger.error(f"Invalid URL format: {citation.source_url}")
                    return False
            except Exception as e:
                logger.error(f"URL parsing error: {e}")
                return False
        
        # Validate date format
        if citation.last_updated:
            try:
                datetime.strptime(citation.last_updated, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid date format: {citation.last_updated}")
                return False
        
        return True
    
    def track_usage(self, citation_id: str, query_type: str, response_type: str, relevance_score: float = 1.0) -> None:
        """
        Track citation usage.
        
        Args:
            citation_id: ID of citation to track
            query_type: Type of query that used the citation
            response_type: Type of response generated
            relevance_score: Relevance score of the citation
        """
        now = datetime.now()
        
        if citation_id not in self.usage_stats:
            self.usage_stats[citation_id] = UsageStats(
                total_uses=0,
                first_used=now,
                last_used=now,
                query_types=[],
                response_types=[],
                average_relevance=0.0
            )
        
        stats = self.usage_stats[citation_id]
        stats.total_uses += 1
        stats.last_used = now
        
        # Update query types and response types
        if query_type not in stats.query_types:
            stats.query_types.append(query_type)
        if response_type not in stats.response_types:
            stats.response_types.append(response_type)
        
        # Update average relevance
        if stats.total_uses == 1:
            stats.average_relevance = relevance_score
        else:
            stats.average_relevance = (
                (stats.average_relevance * (stats.total_uses - 1) + relevance_score) / 
                stats.total_uses
            )
        
        # Update citation frequency
        self.citation_frequency[citation_id] += 1
        
        # Save updated stats
        self._save_usage_stats()
    
    def get_usage_stats(self, citation_id: str) -> Optional[UsageStats]:
        """
        Get usage statistics for a citation.
        
        Args:
            citation_id: ID of citation
            
        Returns:
            UsageStats object or None if not found
        """
        return self.usage_stats.get(citation_id)
    
    def get_citation_analytics(self) -> Dict[str, Any]:
        """
        Get citation analytics.
        
        Returns:
            Dictionary with analytics data
        """
        total_citations = len(self.citations)
        total_usage = sum(stats.total_uses for stats in self.usage_stats.values())
        
        # Most used citations
        most_used = self.citation_frequency.most_common(10)
        
        # Format usage
        format_usage = dict(self.format_usage.most_common())
        
        # Citation quality metrics
        avg_confidence = 0.0
        if self.citations:
            avg_confidence = sum(c.confidence_score for c in self.citations.values()) / len(self.citations)
        
        # Usage by query type
        query_type_usage = defaultdict(int)
        for stats in self.usage_stats.values():
            for query_type in stats.query_types:
                query_type_usage[query_type] += 1
        
        return {
            "total_citations": total_citations,
            "total_usage": total_usage,
            "average_usage_per_citation": (total_usage / total_citations) if total_citations > 0 else 0,
            "most_used_citations": most_used,
            "format_usage": format_usage,
            "average_confidence_score": avg_confidence,
            "usage_by_query_type": dict(query_type_usage),
            "citations_with_usage": len(self.usage_stats),
            "citations_without_usage": total_citations - len(self.usage_stats)
        }
    
    def get_citations_by_fund(self, fund_name: str) -> List[Citation]:
        """
        Get all citations for a specific fund.
        
        Args:
            fund_name: Name of the fund
            
        Returns:
            List of Citation objects
        """
        return [
            citation for citation in self.citations.values()
            if citation.fund_name == fund_name
        ]
    
    def get_citations_by_document_type(self, document_type: str) -> List[Citation]:
        """
        Get all citations for a specific document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            List of Citation objects
        """
        return [
            citation for citation in self.citations.values()
            if citation.document_type == document_type
        ]
    
    def search_citations(self, query: str, limit: int = 10) -> List[Citation]:
        """
        Search citations by content.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching Citation objects
        """
        query_lower = query.lower()
        matching_citations = []
        
        for citation in self.citations.values():
            # Search in various fields
            searchable_text = " ".join([
                citation.formatted_citation.lower(),
                citation.source_title.lower(),
                citation.fund_name.lower(),
                citation.content_type.lower(),
                citation.document_type.lower()
            ])
            
            if query_lower in searchable_text:
                matching_citations.append(citation)
        
        # Sort by confidence score and usage
        matching_citations.sort(key=lambda c: (
            c.confidence_score,
            self.usage_stats.get(c.chunk_id, UsageStats(0, datetime.now(), datetime.now(), [], [], 0)).total_uses
        ), reverse=True)
        
        return matching_citations[:limit]
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old citation data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        # Clean up old usage stats (keep only recently used)
        old_citation_ids = [
            citation_id for citation_id, stats in self.usage_stats.items()
            if stats.last_used < cutoff_date and stats.total_uses < 5
        ]
        
        for citation_id in old_citation_ids:
            del self.usage_stats[citation_id]
            cleaned_count += 1
        
        # Save cleaned data
        self._save_usage_stats()
        
        logger.info(f"Cleaned up {cleaned_count} old citation data items")
        return cleaned_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on citation system.
        
        Returns:
            Health status dictionary
        """
        analytics = self.get_citation_analytics()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "analytics": analytics
        }
        
        # Check for low average confidence
        if analytics["average_confidence_score"] < self.confidence_threshold:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low average confidence: {analytics['average_confidence_score']:.2f}")
        
        # Check for high number of unused citations
        unused_ratio = analytics["citations_without_usage"] / analytics["total_citations"] if analytics["total_citations"] > 0 else 0
        if unused_ratio > 0.5:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"High unused citation ratio: {unused_ratio:.1%}")
        
        return health_status
