"""
Source Link Management for Phase 2.5

Manages source URL validity, link rot detection, versioning, and updates.
"""

import asyncio
import aiohttp
import time
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

@dataclass
class Source:
    """Represents a source URL with metadata."""
    url: str
    title: str
    domain: str
    last_checked: datetime
    last_valid: datetime
    status: str  # "valid", "broken", "redirected", "unknown"
    http_status: Optional[int]
    response_time: float
    content_hash: Optional[str]
    redirect_url: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class BrokenLink:
    """Represents a broken link with details."""
    url: str
    error_type: str
    http_status: Optional[int]
    error_message: str
    last_checked: datetime
    retry_count: int

@dataclass
class VersionedSource:
    """Represents a versioned source."""
    url: str
    version: str
    timestamp: datetime
    content_hash: str
    title: str
    metadata: Dict[str, Any]
    previous_versions: List[str]

@dataclass
class SourceUpdate:
    """Represents a source update."""
    url: str
    old_hash: Optional[str]
    new_hash: str
    update_type: str  # "content_changed", "redirect", "metadata_updated"
    timestamp: datetime
    changes: Dict[str, Any]

class SourceManager:
    """
    Manages source links for accurate citations and link rot detection.
    
    Features:
    - Source URL validation
    - Link rot detection
    - Source versioning
    - Update management
    - Performance monitoring
    """
    
    def __init__(self, cache_dir: str = "cache/source_manager"):
        """
        Initialize source manager.
        
        Args:
            cache_dir: Directory for caching source data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Source storage
        self.sources: Dict[str, Source] = {}
        self.broken_links: Dict[str, BrokenLink] = {}
        self.versioned_sources: Dict[str, List[VersionedSource]] = {}
        
        # Configuration
        self.check_interval = timedelta(hours=24)  # Check every 24 hours
        self.max_retries = 3
        self.timeout = 10  # seconds
        self.user_agent = "MutualFundFAQBot/1.0"
        
        # Performance tracking
        self.total_checks = 0
        self.successful_checks = 0
        self.broken_links_found = 0
        self.average_response_time = 0.0
        
        # Load existing data
        self._load_sources()
        self._load_broken_links()
        self._load_versioned_sources()
        
        logger.info(f"Source Manager initialized with {len(self.sources)} sources")
    
    def _load_sources(self) -> None:
        """Load existing sources from cache."""
        sources_file = self.cache_dir / "sources.json"
        
        if sources_file.exists():
            try:
                with open(sources_file, 'r') as f:
                    data = json.load(f)
                
                for url, source_data in data.items():
                    # Convert string timestamps back to datetime
                    source_data['last_checked'] = datetime.fromisoformat(source_data['last_checked'])
                    source_data['last_valid'] = datetime.fromisoformat(source_data['last_valid'])
                    
                    self.sources[url] = Source(**source_data)
                
                logger.info(f"Loaded {len(self.sources)} sources from cache")
                
            except Exception as e:
                logger.error(f"Error loading sources: {e}")
    
    def _load_broken_links(self) -> None:
        """Load broken links from cache."""
        broken_file = self.cache_dir / "broken_links.json"
        
        if broken_file.exists():
            try:
                with open(broken_file, 'r') as f:
                    data = json.load(f)
                
                for url, broken_data in data.items():
                    broken_data['last_checked'] = datetime.fromisoformat(broken_data['last_checked'])
                    self.broken_links[url] = BrokenLink(**broken_data)
                
                logger.info(f"Loaded {len(self.broken_links)} broken links from cache")
                
            except Exception as e:
                logger.error(f"Error loading broken links: {e}")
    
    def _load_versioned_sources(self) -> None:
        """Load versioned sources from cache."""
        versions_file = self.cache_dir / "versioned_sources.json"
        
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                
                for url, versions_data in data.items():
                    versions = []
                    for version_data in versions_data:
                        version_data['timestamp'] = datetime.fromisoformat(version_data['timestamp'])
                        versions.append(VersionedSource(**version_data))
                    
                    self.versioned_sources[url] = versions
                
                logger.info(f"Loaded versioned sources for {len(self.versioned_sources)} URLs")
                
            except Exception as e:
                logger.error(f"Error loading versioned sources: {e}")
    
    def _save_sources(self) -> None:
        """Save sources to cache."""
        try:
            sources_file = self.cache_dir / "sources.json"
            
            # Convert datetime objects to strings for JSON serialization
            serializable_sources = {}
            for url, source in self.sources.items():
                source_dict = asdict(source)
                source_dict['last_checked'] = source.last_checked.isoformat()
                source_dict['last_valid'] = source.last_valid.isoformat()
                serializable_sources[url] = source_dict
            
            with open(sources_file, 'w') as f:
                json.dump(serializable_sources, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving sources: {e}")
    
    def _save_broken_links(self) -> None:
        """Save broken links to cache."""
        try:
            broken_file = self.cache_dir / "broken_links.json"
            
            serializable_broken = {}
            for url, broken in self.broken_links.items():
                broken_dict = asdict(broken)
                broken_dict['last_checked'] = broken.last_checked.isoformat()
                serializable_broken[url] = broken_dict
            
            with open(broken_file, 'w') as f:
                json.dump(serializable_broken, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving broken links: {e}")
    
    def _save_versioned_sources(self) -> None:
        """Save versioned sources to cache."""
        try:
            versions_file = self.cache_dir / "versioned_sources.json"
            
            serializable_versions = {}
            for url, versions in self.versioned_sources.items():
                versions_list = []
                for version in versions:
                    version_dict = asdict(version)
                    version_dict['timestamp'] = version.timestamp.isoformat()
                    versions_list.append(version_dict)
                serializable_versions[url] = versions_list
            
            with open(versions_file, 'w') as f:
                json.dump(serializable_versions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving versioned sources: {e}")
    
    async def validate_source_links(self, sources: List[Dict[str, Any]]) -> List[Source]:
        """
        Validate a list of source links.
        
        Args:
            sources: List of source dictionaries with 'url' and 'title'
            
        Returns:
            List of validated Source objects
        """
        logger.info(f"Validating {len(sources)} source links")
        
        validated_sources = []
        tasks = []
        
        for source_data in sources:
            url = source_data.get('url', '')
            title = source_data.get('title', '')
            
            if url:
                task = self._validate_single_source(url, title)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Source):
                    validated_sources.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error validating source: {result}")
        
        # Save updated sources
        self._save_sources()
        self._save_broken_links()
        
        logger.info(f"Validated {len(validated_sources)} sources")
        return validated_sources
    
    async def _validate_single_source(self, url: str, title: str = "") -> Source:
        """
        Validate a single source URL.
        
        Args:
            url: URL to validate
            title: Source title
            
        Returns:
            Source object with validation results
        """
        start_time = time.time()
        self.total_checks += 1
        
        # Check if we already have this source
        if url in self.sources:
            source = self.sources[url]
            # Check if we need to revalidate (older than 24 hours)
            if datetime.now() - source.last_checked < self.check_interval:
                logger.debug(f"Using cached validation for {url}")
                return source
        
        # Create new source object
        domain = urlparse(url).netloc
        now = datetime.now()
        
        source = Source(
            url=url,
            title=title or f"Source from {domain}",
            domain=domain,
            last_checked=now,
            last_valid=now,
            status="unknown",
            http_status=None,
            response_time=0.0,
            content_hash=None,
            redirect_url=None,
            metadata={}
        )
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={'User-Agent': self.user_agent}
            ) as session:
                
                async with session.get(url) as response:
                    source.response_time = time.time() - start_time
                    source.http_status = response.status
                    
                    if response.status == 200:
                        source.status = "valid"
                        source.last_valid = now
                        self.successful_checks += 1
                        
                        # Calculate content hash
                        content = await response.text()
                        source.content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        # Extract metadata
                        source.metadata = self._extract_metadata(response, content)
                        
                        logger.debug(f"Source valid: {url} ({source.response_time:.2f}s)")
                        
                    elif 300 <= response.status < 400:
                        # Redirect
                        source.status = "redirected"
                        source.redirect_url = str(response.url)
                        source.last_valid = now
                        self.successful_checks += 1
                        
                        logger.debug(f"Source redirected: {url} -> {source.redirect_url}")
                        
                    else:
                        source.status = "broken"
                        self._add_broken_link(url, "http_error", response.status, f"HTTP {response.status}")
                        self.broken_links_found += 1
                        
                        logger.warning(f"Source broken: {url} (HTTP {response.status})")
        
        except asyncio.TimeoutError:
            source.status = "broken"
            source.response_time = self.timeout
            self._add_broken_link(url, "timeout", None, "Request timeout")
            self.broken_links_found += 1
            
            logger.warning(f"Source timeout: {url}")
            
        except Exception as e:
            source.status = "broken"
            source.response_time = time.time() - start_time
            self._add_broken_link(url, "exception", None, str(e))
            self.broken_links_found += 1
            
            logger.error(f"Source error: {url} - {e}")
        
        # Update average response time
        self._update_average_response_time(source.response_time)
        
        # Store source
        self.sources[url] = source
        
        return source
    
    def _extract_metadata(self, response: aiohttp.ClientResponse, content: str) -> Dict[str, Any]:
        """Extract metadata from response."""
        metadata = {}
        
        # HTTP headers
        metadata['content_type'] = response.headers.get('content-type', '')
        metadata['content_length'] = response.headers.get('content-length', '')
        metadata['last_modified'] = response.headers.get('last-modified', '')
        
        # HTML metadata
        if 'html' in metadata.get('content_type', '').lower():
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                metadata['page_title'] = title_match.group(1).strip()
            
            # Extract description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if desc_match:
                metadata['description'] = desc_match.group(1).strip()
        
        return metadata
    
    def _add_broken_link(self, url: str, error_type: str, http_status: Optional[int], error_message: str) -> None:
        """Add or update a broken link."""
        now = datetime.now()
        
        if url in self.broken_links:
            # Update existing broken link
            broken = self.broken_links[url]
            broken.last_checked = now
            broken.retry_count += 1
        else:
            # Create new broken link
            self.broken_links[url] = BrokenLink(
                url=url,
                error_type=error_type,
                http_status=http_status,
                error_message=error_message,
                last_checked=now,
                retry_count=1
            )
    
    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time."""
        if self.successful_checks > 0:
            self.average_response_time = (
                (self.average_response_time * (self.successful_checks - 1) + response_time) / 
                self.successful_checks
            )
    
    async def detect_link_rot(self, sources: List[Source]) -> List[BrokenLink]:
        """
        Detect link rot in the given sources.
        
        Args:
            sources: List of Source objects to check
            
        Returns:
            List of BrokenLink objects
        """
        logger.info(f"Checking for link rot in {len(sources)} sources")
        
        broken_links = []
        
        for source in sources:
            if source.status == "broken":
                broken_link = self.broken_links.get(source.url)
                if broken_link:
                    broken_links.append(broken_link)
                else:
                    # Create broken link from source
                    broken_links.append(BrokenLink(
                        url=source.url,
                        error_type="status_broken",
                        http_status=source.http_status,
                        error_message="Source marked as broken",
                        last_checked=source.last_checked,
                        retry_count=1
                    ))
        
        logger.info(f"Found {len(broken_links)} broken links")
        return broken_links
    
    async def version_sources(self, sources: List[Source]) -> List[VersionedSource]:
        """
        Create versioned copies of sources.
        
        Args:
            sources: List of Source objects to version
            
        Returns:
            List of VersionedSource objects
        """
        logger.info(f"Creating versions for {len(sources)} sources")
        
        versioned_sources = []
        
        for source in sources:
            if source.content_hash:
                # Generate version ID
                version_id = f"{source.content_hash[:8]}_{int(source.last_valid.timestamp())}"
                
                # Check if this version already exists
                existing_versions = self.versioned_sources.get(source.url, [])
                existing_hashes = {v.content_hash for v in existing_versions}
                
                if source.content_hash not in existing_hashes:
                    # Create new version
                    versioned_source = VersionedSource(
                        url=source.url,
                        version=version_id,
                        timestamp=source.last_valid,
                        content_hash=source.content_hash,
                        title=source.title,
                        metadata=source.metadata.copy(),
                        previous_versions=[v.version for v in existing_versions]
                    )
                    
                    versioned_sources.append(versioned_source)
                    
                    # Update versioned sources storage
                    if source.url not in self.versioned_sources:
                        self.versioned_sources[source.url] = []
                    self.versioned_sources[source.url].append(versioned_source)
                    
                    # Keep only last 10 versions
                    self.versioned_sources[source.url] = sorted(
                        self.versioned_sources[source.url],
                        key=lambda v: v.timestamp,
                        reverse=True
                    )[:10]
        
        # Save versioned sources
        self._save_versioned_sources()
        
        logger.info(f"Created {len(versioned_sources)} new source versions")
        return versioned_sources
    
    async def handle_source_updates(self, updates: List[Dict[str, Any]]) -> List[SourceUpdate]:
        """
        Handle source updates and changes.
        
        Args:
            updates: List of update dictionaries
            
        Returns:
            List of SourceUpdate objects
        """
        logger.info(f"Handling {len(updates)} source updates")
        
        source_updates = []
        
        for update_data in updates:
            url = update_data.get('url', '')
            update_type = update_data.get('type', 'content_changed')
            changes = update_data.get('changes', {})
            
            if url and url in self.sources:
                source = self.sources[url]
                old_hash = source.content_hash
                
                # Re-validate the source to get new hash
                updated_source = await self._validate_single_source(url, source.title)
                
                if updated_source.content_hash != old_hash:
                    source_update = SourceUpdate(
                        url=url,
                        old_hash=old_hash,
                        new_hash=updated_source.content_hash,
                        update_type=update_type,
                        timestamp=datetime.now(),
                        changes=changes
                    )
                    
                    source_updates.append(source_update)
                    
                    # Update source in storage
                    self.sources[url] = updated_source
        
        # Save updated sources
        self._save_sources()
        
        logger.info(f"Processed {len(source_updates)} source updates")
        return source_updates
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """
        Get source management statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_sources = len(self.sources)
        valid_sources = len([s for s in self.sources.values() if s.status == "valid"])
        broken_sources = len([s for s in self.sources.values() if s.status == "broken"])
        redirected_sources = len([s for s in self.sources.values() if s.status == "redirected"])
        
        return {
            "total_sources": total_sources,
            "valid_sources": valid_sources,
            "broken_sources": broken_sources,
            "redirected_sources": redirected_sources,
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "broken_links_found": self.broken_links_found,
            "average_response_time": self.average_response_time,
            "success_rate": (self.successful_checks / self.total_checks * 100) if self.total_checks > 0 else 0,
            "broken_link_rate": (broken_sources / total_sources * 100) if total_sources > 0 else 0
        }
    
    def get_sources_by_domain(self, domain: str) -> List[Source]:
        """
        Get all sources from a specific domain.
        
        Args:
            domain: Domain to filter by
            
        Returns:
            List of Source objects
        """
        return [source for source in self.sources.values() if source.domain == domain]
    
    def get_broken_links_by_type(self, error_type: str) -> List[BrokenLink]:
        """
        Get broken links by error type.
        
        Args:
            error_type: Error type to filter by
            
        Returns:
            List of BrokenLink objects
        """
        return [broken for broken in self.broken_links.values() if broken.error_type == error_type]
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old source data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        # Clean up old broken links
        old_broken = [
            url for url, broken in self.broken_links.items()
            if broken.last_checked < cutoff_date and broken.retry_count > self.max_retries
        ]
        
        for url in old_broken:
            del self.broken_links[url]
            cleaned_count += 1
        
        # Clean up old versioned sources (keep only last 10 versions per URL)
        for url in self.versioned_sources:
            versions = self.versioned_sources[url]
            old_versions = [v for v in versions if v.timestamp < cutoff_date]
            
            if old_versions:
                # Keep only recent versions
                self.versioned_sources[url] = [
                    v for v in versions if v.timestamp >= cutoff_date
                ][:10]
                cleaned_count += len(old_versions)
        
        # Save cleaned data
        self._save_broken_links()
        self._save_versioned_sources()
        
        logger.info(f"Cleaned up {cleaned_count} old source data items")
        return cleaned_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on source manager.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_source_statistics()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "statistics": stats
        }
        
        # Check for high broken link rate
        if stats["broken_link_rate"] > 20:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"High broken link rate: {stats['broken_link_rate']:.1f}%")
        
        # Check for low success rate
        if stats["success_rate"] < 80:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low success rate: {stats['success_rate']:.1f}%")
        
        # Check for slow response times
        if stats["average_response_time"] > 5.0:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Slow response time: {stats['average_response_time']:.2f}s")
        
        return health_status
