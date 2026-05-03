"""
Version Control System for Phase 2.5

Tracks document versions, handles content updates, manages version relationships, and implements rollback capabilities.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import difflib
import re

logger = logging.getLogger(__name__)

@dataclass
class DocumentVersion:
    """Represents a version of a document."""
    version_id: str
    document_id: str
    timestamp: datetime
    content_hash: str
    metadata_hash: str
    content_summary: str
    changes_summary: str
    author: str
    change_type: str  # "create", "update", "delete", "merge"
    parent_version: Optional[str]
    child_versions: List[str]
    tags: List[str]
    size_bytes: int
    chunk_count: int
    metadata: Dict[str, Any]

@dataclass
class VersionDiff:
    """Represents differences between versions."""
    version_a: str
    version_b: str
    content_changes: List[str]
    metadata_changes: Dict[str, Tuple[Any, Any]]
    similarity_score: float
    change_magnitude: str  # "minor", "moderate", "major"
    diff_summary: str

@dataclass
class VersionRelationship:
    """Represents relationship between versions."""
    parent_id: str
    child_id: str
    relationship_type: str  # "direct", "branch", "merge", "rollback"
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any]

class VersionControl:
    """
    Tracks document versions and manages version relationships.
    
    Features:
    - Document version tracking
    - Content update handling
    - Version relationship management
    - Rollback capabilities
    - Version comparison and diffing
    """
    
    def __init__(self, cache_dir: str = "cache/version_control"):
        """
        Initialize version control system.
        
        Args:
            cache_dir: Directory for caching version data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Version storage
        self.versions: Dict[str, DocumentVersion] = {}
        self.document_versions: Dict[str, List[str]] = {}  # document_id -> [version_ids]
        self.relationships: List[VersionRelationship] = []
        
        # Configuration
        self.max_versions_per_document = 50
        self.similarity_threshold = 0.8
        self.default_author = "system"
        
        # Analytics
        self.version_frequency = defaultdict(int)
        self.change_type_frequency = defaultdict(int)
        
        # Load existing data
        self._load_versions()
        self._load_relationships()
        
        logger.info(f"Version Control initialized with {len(self.versions)} versions")
    
    def _load_versions(self) -> None:
        """Load versions from cache."""
        versions_file = self.cache_dir / "versions.json"
        
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                
                for version_id, version_data in data.items():
                    version_data['timestamp'] = datetime.fromisoformat(version_data['timestamp'])
                    self.versions[version_id] = DocumentVersion(**version_data)
                
                # Rebuild document_versions mapping
                for version_id, version in self.versions.items():
                    if version.document_id not in self.document_versions:
                        self.document_versions[version.document_id] = []
                    self.document_versions[version.document_id].append(version_id)
                
                logger.info(f"Loaded {len(self.versions)} versions from cache")
                
            except Exception as e:
                logger.error(f"Error loading versions: {e}")
    
    def _load_relationships(self) -> None:
        """Load relationships from cache."""
        relationships_file = self.cache_dir / "relationships.json"
        
        if relationships_file.exists():
            try:
                with open(relationships_file, 'r') as f:
                    data = json.load(f)
                
                self.relationships = []
                for rel_data in data:
                    self.relationships.append(VersionRelationship(**rel_data))
                
                logger.info(f"Loaded {len(self.relationships)} relationships from cache")
                
            except Exception as e:
                logger.error(f"Error loading relationships: {e}")
    
    def _save_versions(self) -> None:
        """Save versions to cache."""
        try:
            versions_file = self.cache_dir / "versions.json"
            
            serializable_versions = {}
            for version_id, version in self.versions.items():
                version_dict = asdict(version)
                version_dict['timestamp'] = version.timestamp.isoformat()
                serializable_versions[version_id] = version_dict
            
            with open(versions_file, 'w') as f:
                json.dump(serializable_versions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving versions: {e}")
    
    def _save_relationships(self) -> None:
        """Save relationships to cache."""
        try:
            relationships_file = self.cache_dir / "relationships.json"
            
            serializable_relationships = []
            for rel in self.relationships:
                serializable_relationships.append(asdict(rel))
            
            with open(relationships_file, 'w') as f:
                json.dump(serializable_relationships, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving relationships: {e}")
    
    def track_document_versions(self, documents: List[Dict[str, Any]]) -> List[DocumentVersion]:
        """
        Track versions for multiple documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of created DocumentVersion objects
        """
        logger.info(f"Tracking versions for {len(documents)} documents")
        
        created_versions = []
        
        for document in documents:
            version = self._create_version(document, "create")
            created_versions.append(version)
        
        # Save versions
        self._save_versions()
        
        logger.info(f"Created {len(created_versions)} document versions")
        return created_versions
    
    def handle_content_updates(self, updates: List[Dict[str, Any]]) -> List[DocumentVersion]:
        """
        Handle content updates.
        
        Args:
            updates: List of update dictionaries with document data
            
        Returns:
            List of created DocumentVersion objects
        """
        logger.info(f"Handling {len(updates)} content updates")
        
        created_versions = []
        
        for update in updates:
            document_id = update.get('document_id', '')
            
            if not document_id:
                logger.warning(f"Update missing document_id: {update}")
                continue
            
            # Get latest version for this document
            latest_version_id = self._get_latest_version_id(document_id)
            
            # Create new version
            version = self._create_version(update, "update", latest_version_id)
            created_versions.append(version)
        
        # Save versions
        self._save_versions()
        
        logger.info(f"Created {len(created_versions)} update versions")
        return created_versions
    
    def _create_version(self, document: Dict[str, Any], change_type: str, parent_version_id: Optional[str] = None) -> DocumentVersion:
        """Create a new document version."""
        document_id = document.get('document_id', '')
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Generate hashes
        content_hash = hashlib.md5(content.encode()).hexdigest()
        metadata_str = json.dumps(metadata, sort_keys=True)
        metadata_hash = hashlib.md5(metadata_str.encode()).hexdigest()
        
        # Generate version ID
        timestamp = datetime.now()
        version_id = self._generate_version_id(document_id, timestamp, content_hash)
        
        # Generate summaries
        content_summary = self._generate_content_summary(content)
        changes_summary = self._generate_changes_summary(document, change_type)
        
        # Calculate size and chunk count
        size_bytes = len(content.encode('utf-8'))
        chunk_count = metadata.get('chunk_count', 0)
        
        # Create version object
        version = DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            timestamp=timestamp,
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            content_summary=content_summary,
            changes_summary=changes_summary,
            author=document.get('author', self.default_author),
            change_type=change_type,
            parent_version=parent_version_id,
            child_versions=[],
            tags=document.get('tags', []),
            size_bytes=size_bytes,
            chunk_count=chunk_count,
            metadata=metadata.copy()
        )
        
        # Store version
        self.versions[version_id] = version
        
        # Update document versions mapping
        if document_id not in self.document_versions:
            self.document_versions[document_id] = []
        self.document_versions[document_id].append(version_id)
        
        # Update parent-child relationships
        if parent_version_id and parent_version_id in self.versions:
            parent_version = self.versions[parent_version_id]
            parent_version.child_versions.append(version_id)
            
            # Create relationship
            relationship = VersionRelationship(
                parent_id=parent_version_id,
                child_id=version_id,
                relationship_type="direct",
                strength=1.0,
                metadata={"change_type": change_type}
            )
            self.relationships.append(relationship)
        
        # Update analytics
        self.version_frequency[document_id] += 1
        self.change_type_frequency[change_type] += 1
        
        # Clean up old versions if needed
        self._cleanup_old_versions(document_id)
        
        return version
    
    def _generate_version_id(self, document_id: str, timestamp: datetime, content_hash: str) -> str:
        """Generate unique version ID."""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        hash_short = content_hash[:8]
        return f"v_{document_id}_{timestamp_str}_{hash_short}"
    
    def _generate_content_summary(self, content: str) -> str:
        """Generate content summary."""
        if not content:
            return "Empty content"
        
        # Take first 100 characters
        summary = content[:100].strip()
        
        if len(content) > 100:
            summary += "..."
        
        return summary
    
    def _generate_changes_summary(self, document: Dict[str, Any], change_type: str) -> str:
        """Generate changes summary."""
        if change_type == "create":
            return f"Document created: {document.get('title', 'Untitled')}"
        elif change_type == "update":
            return f"Document updated: {document.get('title', 'Untitled')}"
        elif change_type == "delete":
            return f"Document deleted: {document.get('title', 'Untitled')}"
        else:
            return f"Document {change_type}: {document.get('title', 'Untitled')}"
    
    def _get_latest_version_id(self, document_id: str) -> Optional[str]:
        """Get the latest version ID for a document."""
        if document_id not in self.document_versions:
            return None
        
        version_ids = self.document_versions[document_id]
        if not version_ids:
            return None
        
        # Find the most recent version
        latest_version_id = max(
            version_ids,
            key=lambda vid: self.versions[vid].timestamp
        )
        
        return latest_version_id
    
    def _cleanup_old_versions(self, document_id: str) -> None:
        """Clean up old versions for a document."""
        if document_id not in self.document_versions:
            return
        
        version_ids = self.document_versions[document_id]
        
        if len(version_ids) <= self.max_versions_per_document:
            return
        
        # Sort by timestamp (newest first)
        sorted_versions = sorted(
            version_ids,
            key=lambda vid: self.versions[vid].timestamp,
            reverse=True
        )
        
        # Keep only the most recent versions
        versions_to_keep = sorted_versions[:self.max_versions_per_document]
        versions_to_remove = sorted_versions[self.max_versions_per_document:]
        
        # Remove old versions
        for version_id in versions_to_remove:
            if version_id in self.versions:
                del self.versions[version_id]
        
        # Update mapping
        self.document_versions[document_id] = versions_to_keep
        
        logger.info(f"Cleaned up {len(versions_to_remove)} old versions for document {document_id}")
    
    def manage_version_relationships(self, versions: List[DocumentVersion]) -> List[VersionRelationship]:
        """
        Manage relationships between versions.
        
        Args:
            versions: List of DocumentVersion objects
            
        Returns:
            List of VersionRelationship objects
        """
        logger.info(f"Managing relationships for {len(versions)} versions")
        
        new_relationships = []
        
        for version in versions:
            # Find potential parent versions
            potential_parents = self._find_potential_parents(version)
            
            for parent_id, similarity in potential_parents:
                if similarity >= self.similarity_threshold:
                    # Create relationship
                    relationship = VersionRelationship(
                        parent_id=parent_id,
                        child_id=version.version_id,
                        relationship_type="branch",
                        strength=similarity,
                        metadata={"similarity": similarity}
                    )
                    
                    new_relationships.append(relationship)
                    self.relationships.append(relationship)
        
        # Save relationships
        self._save_relationships()
        
        logger.info(f"Created {len(new_relationships)} version relationships")
        return new_relationships
    
    def _find_potential_parents(self, version: DocumentVersion) -> List[Tuple[str, float]]:
        """Find potential parent versions for a given version."""
        potential_parents = []
        
        # Look for versions of the same document
        if version.document_id in self.document_versions:
            for version_id in self.document_versions[version.document_id]:
                if version_id == version.version_id:
                    continue
                
                other_version = self.versions[version_id]
                
                # Calculate similarity based on content and metadata
                content_similarity = self._calculate_content_similarity(
                    version.content_hash, other_version.content_hash
                )
                
                metadata_similarity = self._calculate_metadata_similarity(
                    version.metadata_hash, other_version.metadata_hash
                )
                
                # Combined similarity score
                combined_similarity = (content_similarity + metadata_similarity) / 2
                
                if combined_similarity > 0.5:  # Only consider reasonable matches
                    potential_parents.append((version_id, combined_similarity))
        
        # Sort by similarity (highest first)
        potential_parents.sort(key=lambda x: x[1], reverse=True)
        
        return potential_parents[:5]  # Return top 5 potential parents
    
    def _calculate_content_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate content similarity based on hash."""
        if hash1 == hash2:
            return 1.0
        
        # For hash-based similarity, we can use a simple approach
        # In practice, you might want to store actual content for better comparison
        return 0.0  # Different hashes mean different content
    
    def _calculate_metadata_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate metadata similarity based on hash."""
        if hash1 == hash2:
            return 1.0
        
        return 0.0  # Different hashes mean different metadata
    
    def implement_rollback_capabilities(self, document_id: str, target_version_id: str) -> Optional[DocumentVersion]:
        """
        Implement rollback to a specific version.
        
        Args:
            document_id: ID of document to rollback
            target_version_id: Target version ID to rollback to
            
        Returns:
            New rollback version or None if failed
        """
        logger.info(f"Rolling back document {document_id} to version {target_version_id}")
        
        # Validate target version exists
        if target_version_id not in self.versions:
            logger.error(f"Target version {target_version_id} not found")
            return None
        
        target_version = self.versions[target_version_id]
        
        if target_version.document_id != document_id:
            logger.error(f"Version {target_version_id} does not belong to document {document_id}")
            return None
        
        # Get current latest version
        current_version_id = self._get_latest_version_id(document_id)
        
        # Create rollback version
        rollback_data = {
            "document_id": document_id,
            "content": f"ROLLED_BACK_TO:{target_version_id}",
            "metadata": target_version.metadata.copy(),
            "author": "rollback_system",
            "tags": ["rollback"],
            "title": f"Rollback to {target_version_id}"
        }
        
        rollback_version = self._create_version(
            rollback_data, 
            "rollback", 
            current_version_id
        )
        
        # Create rollback relationship
        rollback_relationship = VersionRelationship(
            parent_id=current_version_id,
            child_id=rollback_version.version_id,
            relationship_type="rollback",
            strength=1.0,
            metadata={
                "rollback_target": target_version_id,
                "rollback_reason": "manual_rollback"
            }
        )
        
        self.relationships.append(rollback_relationship)
        
        # Save changes
        self._save_versions()
        self._save_relationships()
        
        logger.info(f"Rollback completed: {rollback_version.version_id}")
        return rollback_version
    
    def get_version_history(self, document_id: str, limit: int = 10) -> List[DocumentVersion]:
        """
        Get version history for a document.
        
        Args:
            document_id: ID of document
            limit: Maximum number of versions to return
            
        Returns:
            List of DocumentVersion objects in chronological order
        """
        if document_id not in self.document_versions:
            return []
        
        version_ids = self.document_versions[document_id]
        
        # Get version objects and sort by timestamp
        versions = [self.versions[vid] for vid in version_ids if vid in self.versions]
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        
        return versions[:limit]
    
    def compare_versions(self, version_a_id: str, version_b_id: str) -> Optional[VersionDiff]:
        """
        Compare two versions.
        
        Args:
            version_a_id: First version ID
            version_b_id: Second version ID
            
        Returns:
            VersionDiff object or None if versions not found
        """
        if version_a_id not in self.versions or version_b_id not in self.versions:
            return None
        
        version_a = self.versions[version_a_id]
        version_b = self.versions[version_b_id]
        
        # Calculate content differences
        content_changes = self._calculate_content_differences(version_a, version_b)
        
        # Calculate metadata differences
        metadata_changes = self._calculate_metadata_differences(version_a, version_b)
        
        # Calculate similarity score
        similarity_score = self._calculate_version_similarity(version_a, version_b)
        
        # Determine change magnitude
        change_magnitude = self._determine_change_magnitude(content_changes, metadata_changes)
        
        # Generate diff summary
        diff_summary = self._generate_diff_summary(version_a, version_b, change_magnitude)
        
        return VersionDiff(
            version_a=version_a_id,
            version_b=version_b_id,
            content_changes=content_changes,
            metadata_changes=metadata_changes,
            similarity_score=similarity_score,
            change_magnitude=change_magnitude,
            diff_summary=diff_summary
        )
    
    def _calculate_content_differences(self, version_a: DocumentVersion, version_b: DocumentVersion) -> List[str]:
        """Calculate content differences between versions."""
        differences = []
        
        # Compare content hashes
        if version_a.content_hash != version_b.content_hash:
            differences.append("Content changed")
        
        # Compare content summaries
        if version_a.content_summary != version_b.content_summary:
            differences.append("Content summary changed")
        
        # Compare sizes
        size_diff = version_b.size_bytes - version_a.size_bytes
        if abs(size_diff) > 100:  # More than 100 bytes difference
            if size_diff > 0:
                differences.append(f"Content increased by {size_diff} bytes")
            else:
                differences.append(f"Content decreased by {abs(size_diff)} bytes")
        
        # Compare chunk counts
        if version_a.chunk_count != version_b.chunk_count:
            differences.append(f"Chunk count changed from {version_a.chunk_count} to {version_b.chunk_count}")
        
        return differences
    
    def _calculate_metadata_differences(self, version_a: DocumentVersion, version_b: DocumentVersion) -> Dict[str, Tuple[Any, Any]]:
        """Calculate metadata differences between versions."""
        differences = {}
        
        # Compare metadata hashes
        if version_a.metadata_hash != version_b.metadata_hash:
            # Detailed metadata comparison
            all_keys = set(version_a.metadata.keys()) | set(version_b.metadata.keys())
            
            for key in all_keys:
                value_a = version_a.metadata.get(key)
                value_b = version_b.metadata.get(key)
                
                if value_a != value_b:
                    differences[key] = (value_a, value_b)
        
        return differences
    
    def _calculate_version_similarity(self, version_a: DocumentVersion, version_b: DocumentVersion) -> float:
        """Calculate overall similarity between versions."""
        # Content similarity
        content_similarity = 1.0 if version_a.content_hash == version_b.content_hash else 0.0
        
        # Metadata similarity
        metadata_similarity = 1.0 if version_a.metadata_hash == version_b.metadata_hash else 0.0
        
        # Overall similarity (weighted)
        overall_similarity = (content_similarity * 0.7 + metadata_similarity * 0.3)
        
        return overall_similarity
    
    def _determine_change_magnitude(self, content_changes: List[str], metadata_changes: Dict[str, Tuple[Any, Any]]) -> str:
        """Determine the magnitude of changes."""
        total_changes = len(content_changes) + len(metadata_changes)
        
        if total_changes == 0:
            return "minor"
        elif total_changes <= 3:
            return "moderate"
        else:
            return "major"
    
    def _generate_diff_summary(self, version_a: DocumentVersion, version_b: DocumentVersion, magnitude: str) -> str:
        """Generate diff summary."""
        time_diff = version_b.timestamp - version_a.timestamp
        
        summary_parts = [
            f"Change magnitude: {magnitude}",
            f"Time difference: {time_diff.total_seconds() / 3600:.1f} hours"
        ]
        
        if version_a.change_type != version_b.change_type:
            summary_parts.append(f"Change type: {version_a.change_type} -> {version_b.change_type}")
        
        return ". ".join(summary_parts)
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """
        Get version control statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_versions = len(self.versions)
        total_documents = len(self.document_versions)
        total_relationships = len(self.relationships)
        
        # Version distribution by document
        versions_per_document = [
            len(versions) for versions in self.document_versions.values()
        ]
        
        avg_versions_per_document = (
            sum(versions_per_document) / len(versions_per_document)
            if versions_per_document else 0
        )
        
        # Change type distribution
        change_type_dist = dict(self.change_type_frequency)
        
        # Recent activity (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_versions = [
            version for version in self.versions.values()
            if version.timestamp > cutoff_time
        ]
        
        return {
            "total_versions": total_versions,
            "total_documents": total_documents,
            "total_relationships": total_relationships,
            "average_versions_per_document": avg_versions_per_document,
            "change_type_distribution": change_type_dist,
            "recent_versions_24h": len(recent_versions),
            "most_versioned_documents": dict(self.version_frequency.most_common(10))
        }
    
    def get_document_lineage(self, document_id: str) -> List[str]:
        """
        Get the complete lineage of a document.
        
        Args:
            document_id: ID of document
            
        Returns:
            List of version IDs in chronological order
        """
        if document_id not in self.document_versions:
            return []
        
        version_ids = self.document_versions[document_id]
        
        # Sort by timestamp
        sorted_versions = sorted(
            version_ids,
            key=lambda vid: self.versions[vid].timestamp
        )
        
        return sorted_versions
    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """
        Clean up old version data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        # Clean up old versions (keep only recent ones)
        old_version_ids = [
            vid for vid, version in self.versions.items()
            if version.timestamp < cutoff_date
        ]
        
        # Group by document to ensure we keep at least one version per document
        versions_to_remove = []
        for vid in old_version_ids:
            version = self.versions[vid]
            document_id = version.document_id
            
            # Check if this is the only version for the document
            if document_id in self.document_versions:
                doc_versions = [v for v in self.document_versions[document_id] if v in self.versions]
                if len(doc_versions) > 1:
                    versions_to_remove.append(vid)
        
        # Remove old versions
        for vid in versions_to_remove:
            if vid in self.versions:
                del self.versions[vid]
                cleaned_count += 1
        
        # Update document mappings
        for document_id in list(self.document_versions.keys()):
            self.document_versions[document_id] = [
                vid for vid in self.document_versions[document_id]
                if vid in self.versions
            ]
            
            if not self.document_versions[document_id]:
                del self.document_versions[document_id]
        
        # Clean up old relationships
        self.relationships = [
            rel for rel in self.relationships
            if rel.parent_id in self.versions and rel.child_id in self.versions
        ]
        
        # Save cleaned data
        self._save_versions()
        self._save_relationships()
        
        logger.info(f"Cleaned up {cleaned_count} old version items")
        return cleaned_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on version control system.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_version_statistics()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "statistics": stats
        }
        
        # Check for orphaned versions
        orphaned_versions = [
            vid for vid in self.versions.keys()
            if vid not in [rel.parent_id for rel in self.relationships] and
               vid not in [rel.child_id for rel in self.relationships]
        ]
        
        if len(orphaned_versions) > stats["total_versions"] * 0.1:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"High number of orphaned versions: {len(orphaned_versions)}")
        
        # Check for documents with too many versions
        max_versions = max(
            [len(versions) for versions in self.document_versions.values()],
            default=0
        )
        
        if max_versions > self.max_versions_per_document * 1.5:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Document with excessive versions: {max_versions}")
        
        return health_status
