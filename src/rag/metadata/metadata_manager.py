"""
Metadata Consistency System for Phase 2.5

Ensures metadata consistency across chunks, handles updates, and manages relationships.
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

logger = logging.getLogger(__name__)

@dataclass
class MetadataUpdate:
    """Represents a metadata update operation."""
    chunk_id: str
    field: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    update_type: str  # "field_update", "schema_change", "relationship_update"

@dataclass
class ValidationResult:
    """Result of metadata validation."""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    missing_fields: List[str]
    invalid_formats: List[str]
    consistency_score: float

@dataclass
class RelationshipMap:
    """Maps relationships between metadata items."""
    parent_child: Dict[str, List[str]]
    siblings: Dict[str, List[str]]
    cross_references: Dict[str, List[str]]
    hierarchy_levels: Dict[str, int]

class MetadataManager:
    """
    Ensures metadata consistency across chunks and manages metadata relationships.
    
    Features:
    - Metadata consistency validation
    - Update handling and tracking
    - Format validation
    - Relationship management
    - Schema enforcement
    """
    
    def __init__(self, cache_dir: str = "cache/metadata_manager"):
        """
        Initialize metadata manager.
        
        Args:
            cache_dir: Directory for caching metadata data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata schema definition
        self.schema = self._initialize_schema()
        
        # Metadata storage
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.update_history: List[MetadataUpdate] = []
        self.validation_cache: Dict[str, ValidationResult] = {}
        
        # Relationship tracking
        self.relationships = RelationshipMap(
            parent_child={},
            siblings={},
            cross_references={},
            hierarchy_levels={}
        )
        
        # Configuration
        self.validation_cache_ttl = timedelta(hours=1)
        self.max_history_items = 1000
        
        # Load existing data
        self._load_metadata_store()
        self._load_update_history()
        self._load_relationships()
        
        logger.info(f"Metadata Manager initialized with {len(self.metadata_store)} chunks")
    
    def _initialize_schema(self) -> Dict[str, Any]:
        """Initialize metadata schema definition."""
        return {
            "required_fields": {
                "chunk_id": str,
                "source_url": str,
                "fund_name": str,
                "content_type": str,
                "document_type": str,
                "last_updated": str,
                "chunk_index": int
            },
            "optional_fields": {
                "fund_type": str,
                "nav": str,
                "expense_ratio": str,
                "min_investment": str,
                "risk_level": str,
                "benchmark": str,
                "aum": str,
                "category": str,
                "tags": List[str],
                "language": str,
                "page_number": Optional[int],
                "section": str,
                "confidence_score": float,
                "quality_score": float
            },
            "format_constraints": {
                "source_url": r"^https?://[^\s/$.?#].[^\s]*$",
                "fund_name": r".{1,100}",
                "content_type": r"^(expense_ratio|nav|sip|risk|performance|general|procedural)$",
                "document_type": r"^(factsheet|prospectus|kyc|statement|faq|article)$",
                "last_updated": r"^\d{4}-\d{2}-\d{2}$",
                "chunk_index": r"^\d+$",
                "fund_type": r"^(equity|debt|hybrid|elss|liquid)$",
                "risk_level": r"^(low|moderate|high|very_high)$",
                "expense_ratio": r"^\d+(\.\d+)?%?$",
                "nav": r"^\d+(\.\d+)?$",
                "min_investment": r"^\d+(\.\d+)?$",
                "confidence_score": r"^[01]\.\d+$",
                "quality_score": r"^[01]\.\d+$"
            },
            "value_constraints": {
                "chunk_index": {"min": 0},
                "confidence_score": {"min": 0.0, "max": 1.0},
                "quality_score": {"min": 0.0, "max": 1.0}
            }
        }
    
    def _load_metadata_store(self) -> None:
        """Load metadata store from cache."""
        metadata_file = self.cache_dir / "metadata_store.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.metadata_store = json.load(f)
                
                logger.info(f"Loaded metadata for {len(self.metadata_store)} chunks")
                
            except Exception as e:
                logger.error(f"Error loading metadata store: {e}")
    
    def _load_update_history(self) -> None:
        """Load update history from cache."""
        history_file = self.cache_dir / "update_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                
                self.update_history = []
                for item in data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    self.update_history.append(MetadataUpdate(**item))
                
                logger.info(f"Loaded {len(self.update_history)} update history items")
                
            except Exception as e:
                logger.error(f"Error loading update history: {e}")
    
    def _load_relationships(self) -> None:
        """Load relationships from cache."""
        relationships_file = self.cache_dir / "relationships.json"
        
        if relationships_file.exists():
            try:
                with open(relationships_file, 'r') as f:
                    data = json.load(f)
                
                self.relationships = RelationshipMap(**data)
                
                logger.info(f"Loaded relationships for {len(self.relationships.parent_child)} chunks")
                
            except Exception as e:
                logger.error(f"Error loading relationships: {e}")
    
    def _save_metadata_store(self) -> None:
        """Save metadata store to cache."""
        try:
            metadata_file = self.cache_dir / "metadata_store.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata_store, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metadata store: {e}")
    
    def _save_update_history(self) -> None:
        """Save update history to cache."""
        try:
            history_file = self.cache_dir / "update_history.json"
            
            # Keep only recent history
            recent_history = self.update_history[-self.max_history_items:]
            
            serializable_history = []
            for update in recent_history:
                update_dict = asdict(update)
                update_dict['timestamp'] = update.timestamp.isoformat()
                serializable_history.append(update_dict)
            
            with open(history_file, 'w') as f:
                json.dump(serializable_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving update history: {e}")
    
    def _save_relationships(self) -> None:
        """Save relationships to cache."""
        try:
            relationships_file = self.cache_dir / "relationships.json"
            
            relationships_dict = asdict(self.relationships)
            with open(relationships_file, 'w') as f:
                json.dump(relationships_dict, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving relationships: {e}")
    
    def ensure_consistency(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure metadata consistency across chunks.
        
        Args:
            chunks: List of chunk dictionaries with metadata
            
        Returns:
            List of chunks with consistent metadata
        """
        logger.info(f"Ensuring consistency for {len(chunks)} chunks")
        
        consistent_chunks = []
        updates = []
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            
            if not chunk_id:
                # Generate chunk ID if missing
                chunk_id = self._generate_chunk_id(chunk)
                chunk['chunk_id'] = chunk_id
            
            # Validate and fix metadata
            fixed_chunk, chunk_updates = self._fix_chunk_metadata(chunk)
            
            # Store in metadata store
            self.metadata_store[chunk_id] = fixed_chunk.copy()
            
            # Track updates
            updates.extend(chunk_updates)
            
            consistent_chunks.append(fixed_chunk)
        
        # Update relationships
        self._update_relationships(consistent_chunks)
        
        # Save changes
        self._save_metadata_store()
        self._save_update_history()
        self._save_relationships()
        
        logger.info(f"Ensured consistency for {len(consistent_chunks)} chunks with {len(updates)} updates")
        return consistent_chunks
    
    def _generate_chunk_id(self, chunk: Dict[str, Any]) -> str:
        """Generate a unique chunk ID."""
        content = chunk.get('content', '')
        source_url = chunk.get('source_url', '')
        
        # Create hash from content and source
        hash_input = f"{content[:500]}{source_url}"
        chunk_hash = hashlib.md5(hash_input.encode()).hexdigest()
        
        return f"chunk_{chunk_hash[:12]}"
    
    def _fix_chunk_metadata(self, chunk: Dict[str, Any]) -> Tuple[Dict[str, Any], List[MetadataUpdate]]:
        """Fix metadata consistency issues in a chunk."""
        fixed_chunk = chunk.copy()
        updates = []
        
        # Check required fields
        for field, field_type in self.schema["required_fields"].items():
            if field not in fixed_chunk:
                # Add missing required field with default value
                default_value = self._get_default_value(field, field_type)
                fixed_chunk[field] = default_value
                
                updates.append(MetadataUpdate(
                    chunk_id=fixed_chunk.get('chunk_id', 'unknown'),
                    field=field,
                    old_value=None,
                    new_value=default_value,
                    timestamp=datetime.now(),
                    update_type="field_update"
                ))
        
        # Fix format issues
        for field, pattern in self.schema["format_constraints"].items():
            if field in fixed_chunk:
                current_value = fixed_chunk[field]
                if not self._validate_field_format(field, current_value):
                    fixed_value = self._fix_field_format(field, current_value)
                    if fixed_value != current_value:
                        fixed_chunk[field] = fixed_value
                        
                        updates.append(MetadataUpdate(
                            chunk_id=fixed_chunk.get('chunk_id', 'unknown'),
                            field=field,
                            old_value=current_value,
                            new_value=fixed_value,
                            timestamp=datetime.now(),
                            update_type="field_update"
                        ))
        
        # Fix value constraints
        for field, constraints in self.schema["value_constraints"].items():
            if field in fixed_chunk:
                current_value = fixed_chunk[field]
                if not self._validate_field_value(field, current_value, constraints):
                    fixed_value = self._fix_field_value(field, current_value, constraints)
                    if fixed_value != current_value:
                        fixed_chunk[field] = fixed_value
                        
                        updates.append(MetadataUpdate(
                            chunk_id=fixed_chunk.get('chunk_id', 'unknown'),
                            field=field,
                            old_value=current_value,
                            new_value=fixed_value,
                            timestamp=datetime.now(),
                            update_type="field_update"
                        ))
        
        return fixed_chunk, updates
    
    def _get_default_value(self, field: str, field_type: type) -> Any:
        """Get default value for a field type."""
        defaults = {
            str: "",
            int: 0,
            float: 0.0,
            bool: False,
            list: [],
            dict: {}
        }
        
        field_defaults = {
            "chunk_id": "",
            "source_url": "",
            "fund_name": "Unknown Fund",
            "content_type": "general",
            "document_type": "article",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "chunk_index": 0
        }
        
        return field_defaults.get(field, defaults.get(field_type, ""))
    
    def _validate_field_format(self, field: str, value: Any) -> bool:
        """Validate field format against schema."""
        if field not in self.schema["format_constraints"]:
            return True
        
        pattern = self.schema["format_constraints"][field]
        if not pattern or not isinstance(value, str):
            return True
        
        return bool(re.match(pattern, str(value)))
    
    def _fix_field_format(self, field: str, value: Any) -> Any:
        """Fix field format issues."""
        if field == "last_updated":
            # Try to parse and reformat date
            try:
                if isinstance(value, str):
                    # Try different date formats
                    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(value, fmt)
                            return parsed_date.strftime("%Y-%m-%d")
                        except ValueError:
                            continue
            except:
                pass
            return datetime.now().strftime("%Y-%m-%d")
        
        elif field == "source_url":
            # Fix URL format
            if isinstance(value, str):
                if not value.startswith(('http://', 'https://')):
                    return f"https://{value}"
            return value
        
        elif field == "fund_name":
            # Clean fund name
            if isinstance(value, str):
                return value.strip()[:100]  # Limit to 100 chars
            return str(value)
        
        elif field == "content_type":
            # Normalize content type
            if isinstance(value, str):
                valid_types = ["expense_ratio", "nav", "sip", "risk", "performance", "general", "procedural"]
                value_lower = value.lower().strip()
                if value_lower in valid_types:
                    return value_lower
            return "general"
        
        elif field == "document_type":
            # Normalize document type
            if isinstance(value, str):
                valid_types = ["factsheet", "prospectus", "kyc", "statement", "faq", "article"]
                value_lower = value.lower().strip()
                if value_lower in valid_types:
                    return value_lower
            return "article"
        
        return value
    
    def _validate_field_value(self, field: str, value: Any, constraints: Dict[str, Any]) -> bool:
        """Validate field value against constraints."""
        if "min" in constraints and value < constraints["min"]:
            return False
        if "max" in constraints and value > constraints["max"]:
            return False
        return True
    
    def _fix_field_value(self, field: str, value: Any, constraints: Dict[str, Any]) -> Any:
        """Fix field value to meet constraints."""
        if "min" in constraints and value < constraints["min"]:
            return constraints["min"]
        if "max" in constraints and value > constraints["max"]:
            return constraints["max"]
        return value
    
    def _update_relationships(self, chunks: List[Dict[str, Any]]) -> None:
        """Update metadata relationships based on chunks."""
        # Clear existing relationships
        self.relationships = RelationshipMap(
            parent_child={},
            siblings={},
            cross_references={},
            hierarchy_levels={}
        )
        
        # Build relationships
        fund_groups = defaultdict(list)
        content_type_groups = defaultdict(list)
        document_type_groups = defaultdict(list)
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            fund_name = chunk.get('fund_name', '')
            content_type = chunk.get('content_type', '')
            document_type = chunk.get('document_type', '')
            
            # Group by fund
            if fund_name:
                fund_groups[fund_name].append(chunk_id)
            
            # Group by content type
            if content_type:
                content_type_groups[content_type].append(chunk_id)
            
            # Group by document type
            if document_type:
                document_type_groups[document_type].append(chunk_id)
        
        # Build sibling relationships
        for group in [fund_groups, content_type_groups, document_type_groups]:
            for key, chunk_ids in group.items():
                for chunk_id in chunk_ids:
                    siblings = [cid for cid in chunk_ids if cid != chunk_id]
                    if siblings:
                        self.relationships.siblings[chunk_id] = siblings
        
        # Build hierarchy levels (fund -> document_type -> content_type)
        level_0 = set(fund_groups.keys())  # Fund level
        level_1 = set(document_type_groups.keys())  # Document level
        level_2 = set(content_type_groups.keys())  # Content level
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            fund_name = chunk.get('fund_name', '')
            document_type = chunk.get('document_type', '')
            content_type = chunk.get('content_type', '')
            
            # Determine hierarchy level
            if fund_name in level_0:
                self.relationships.hierarchy_levels[chunk_id] = 0
            elif document_type in level_1:
                self.relationships.hierarchy_levels[chunk_id] = 1
            elif content_type in level_2:
                self.relationships.hierarchy_levels[chunk_id] = 2
            else:
                self.relationships.hierarchy_levels[chunk_id] = 3
    
    def handle_updates(self, updates: List[MetadataUpdate]) -> None:
        """
        Handle metadata updates.
        
        Args:
            updates: List of metadata updates to apply
        """
        logger.info(f"Handling {len(updates)} metadata updates")
        
        for update in updates:
            chunk_id = update.chunk_id
            
            if chunk_id in self.metadata_store:
                chunk_metadata = self.metadata_store[chunk_id]
                
                # Apply update
                if update.field in chunk_metadata:
                    old_value = chunk_metadata[update.field]
                    chunk_metadata[update.field] = update.new_value
                    
                    # Add to update history
                    self.update_history.append(update)
                    
                    logger.debug(f"Updated {chunk_id}.{update.field}: {old_value} -> {update.new_value}")
        
        # Save changes
        self._save_metadata_store()
        self._save_update_history()
    
    def validate_formats(self, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Validate metadata formats.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            ValidationResult object
        """
        # Check cache first
        metadata_hash = hashlib.md5(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        cache_key = f"{metadata_hash}_{datetime.now().strftime('%Y-%m-%d')}"
        
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            # Check if cache is still valid
            if (datetime.now() - cached_result.timestamp.replace(tzinfo=None)) < self.validation_cache_ttl:
                return cached_result
        
        issues = []
        warnings = []
        missing_fields = []
        invalid_formats = []
        
        # Check required fields
        for field, field_type in self.schema["required_fields"].items():
            if field not in metadata:
                missing_fields.append(field)
                issues.append(f"Missing required field: {field}")
            elif not isinstance(metadata[field], field_type):
                invalid_formats.append(f"Invalid type for {field}: expected {field_type.__name__}, got {type(metadata[field]).__name__}")
        
        # Check format constraints
        for field, pattern in self.schema["format_constraints"].items():
            if field in metadata:
                if not self._validate_field_format(field, metadata[field]):
                    invalid_formats.append(f"Invalid format for {field}: {metadata[field]}")
        
        # Check value constraints
        for field, constraints in self.schema["value_constraints"].items():
            if field in metadata:
                if not self._validate_field_value(field, metadata[field], constraints):
                    issues.append(f"Invalid value for {field}: {metadata[field]}")
        
        # Calculate consistency score
        total_checks = len(self.schema["required_fields"]) + len(self.schema["format_constraints"]) + len(self.schema["value_constraints"])
        failed_checks = len(issues) + len(invalid_formats)
        consistency_score = (total_checks - failed_checks) / total_checks if total_checks > 0 else 0.0
        
        result = ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            missing_fields=missing_fields,
            invalid_formats=invalid_formats,
            consistency_score=consistency_score
        )
        
        # Cache result
        self.validation_cache[cache_key] = result
        
        return result
    
    def manage_relationships(self, chunks: List[Dict[str, Any]]) -> RelationshipMap:
        """
        Manage metadata relationships between chunks.
        
        Args:
            chunks: List of chunk metadata
            
        Returns:
            Updated RelationshipMap
        """
        self._update_relationships(chunks)
        self._save_relationships()
        
        return self.relationships
    
    def get_metadata_statistics(self) -> Dict[str, Any]:
        """
        Get metadata management statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_chunks = len(self.metadata_store)
        total_updates = len(self.update_history)
        
        # Field completeness
        field_completeness = {}
        for field in self.schema["required_fields"]:
            count = sum(1 for metadata in self.metadata_store.values() if field in metadata and metadata[field])
            field_completeness[field] = (count / total_chunks * 100) if total_chunks > 0 else 0
        
        # Update frequency
        update_frequency = Counter(update.field for update in self.update_history)
        
        # Relationship statistics
        total_relationships = (
            len(self.relationships.parent_child) +
            len(self.relationships.siblings) +
            len(self.relationships.cross_references)
        )
        
        return {
            "total_chunks": total_chunks,
            "total_updates": total_updates,
            "field_completeness": field_completeness,
            "update_frequency": dict(update_frequency.most_common(10)),
            "total_relationships": total_relationships,
            "average_relationships_per_chunk": (total_relationships / total_chunks) if total_chunks > 0 else 0,
            "validation_cache_size": len(self.validation_cache)
        }
    
    def get_chunks_by_field(self, field: str, value: Any) -> List[str]:
        """
        Get chunk IDs by field value.
        
        Args:
            field: Field name
            value: Field value to match
            
        Returns:
            List of chunk IDs
        """
        return [
            chunk_id for chunk_id, metadata in self.metadata_store.items()
            if metadata.get(field) == value
        ]
    
    def get_related_chunks(self, chunk_id: str, relationship_type: str = "siblings") -> List[str]:
        """
        Get related chunks by relationship type.
        
        Args:
            chunk_id: Chunk ID to find relations for
            relationship_type: Type of relationship ("siblings", "parent_child", "cross_references")
            
        Returns:
            List of related chunk IDs
        """
        if relationship_type == "siblings":
            return self.relationships.siblings.get(chunk_id, [])
        elif relationship_type == "parent_child":
            return self.relationships.parent_child.get(chunk_id, [])
        elif relationship_type == "cross_references":
            return self.relationships.cross_references.get(chunk_id, [])
        else:
            return []
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old metadata data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        # Clean up old update history
        old_updates = [
            i for i, update in enumerate(self.update_history)
            if update.timestamp < cutoff_date
        ]
        
        if old_updates:
            # Keep only recent updates
            self.update_history = [
                update for update in self.update_history
                if update.timestamp >= cutoff_date
            ][-self.max_history_items:]
            cleaned_count += len(old_updates)
        
        # Clean up old validation cache
        old_cache_keys = [
            key for key in self.validation_cache.keys()
            if key.endswith((cutoff_date - timedelta(days=1)).strftime('%Y-%m-%d'))
        ]
        
        for key in old_cache_keys:
            del self.validation_cache[key]
            cleaned_count += 1
        
        # Save cleaned data
        self._save_update_history()
        
        logger.info(f"Cleaned up {cleaned_count} old metadata items")
        return cleaned_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on metadata manager.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_metadata_statistics()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "statistics": stats
        }
        
        # Check for low field completeness
        low_completeness_fields = [
            field for field, completeness in stats["field_completeness"].items()
            if completeness < 90
        ]
        
        if low_completeness_fields:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low completeness in fields: {low_completeness_fields}")
        
        # Check for high update frequency (might indicate instability)
        if stats["total_updates"] > stats["total_chunks"] * 2:
            health_status["status"] = "degraded"
            health_status["issues"].append("High update frequency detected")
        
        return health_status
