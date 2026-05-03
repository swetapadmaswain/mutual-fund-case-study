"""
Hierarchical indexing system for Phase 2.2 - Fund-specific organization and routing.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.chunker import Chunk


@dataclass
class FundHierarchy:
    """Represents fund hierarchy structure."""
    fund_name: str
    fund_type: str
    fund_category: str
    content_types: List[str]
    document_count: int
    last_updated: str


class HierarchicalIndexer:
    """Manages hierarchical indexing for mutual fund data."""
    
    def __init__(self, index_path: str = "cache/hierarchical_index"):
        """
        Initialize hierarchical indexer.
        
        Args:
            index_path: Path to store index files
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Hierarchical structure
        self.fund_hierarchy: Dict[str, FundHierarchy] = {}
        self.type_hierarchy: Dict[str, List[str]] = {}  # fund_type -> list of funds
        self.content_hierarchy: Dict[str, List[str]] = {}  # content_type -> list of chunks
        self.document_index: Dict[str, List[str]] = {}  # document_id -> list of chunk_ids
        
        # Fund type mappings
        self.fund_type_mappings = {
            'mid cap': 'mid_cap',
            'large cap': 'large_cap',
            'small cap': 'small_cap',
            'multi cap': 'multi_cap',
            'flexi cap': 'flexi_cap',
            'elss': 'elss',
            'tax saver': 'elss',
            'equity': 'equity',
            'debt': 'debt',
            'hybrid': 'hybrid',
            'focused': 'focused',
            'arbitrage': 'arbitrage'
        }
        
        # Content type mappings
        self.content_type_mappings = {
            'expense_ratio': 'expense_ratio',
            'exit_load': 'exit_load',
            'nav': 'nav',
            'sip': 'sip',
            'aum': 'aum',
            'risk': 'risk',
            'benchmark': 'benchmark',
            'portfolio': 'portfolio',
            'allocation': 'allocation',
            'performance': 'performance',
            'objective': 'objective',
            'returns': 'returns',
            'general': 'general'
        }
        
        logger.info("Initialized HierarchicalIndexer")
    
    def build_index(self, chunks: List[Chunk]) -> None:
        """
        Build hierarchical index from chunks.
        
        Args:
            chunks: List of chunks to index
        """
        logger.info(f"Building hierarchical index from {len(chunks)} chunks")
        
        # Clear existing index
        self.fund_hierarchy.clear()
        self.type_hierarchy.clear()
        self.content_hierarchy.clear()
        self.document_index.clear()
        
        # Process each chunk
        for chunk in chunks:
            self._process_chunk(chunk)
        
        # Save index
        self._save_index()
        
        logger.info(f"Built index for {len(self.fund_hierarchy)} funds")
    
    def _process_chunk(self, chunk: Chunk) -> None:
        """
        Process a single chunk and update hierarchical structures.
        
        Args:
            chunk: Chunk to process
        """
        metadata = chunk.metadata
        
        # Extract fund information
        fund_name = self._extract_fund_name(metadata)
        fund_type = self._extract_fund_type(metadata, chunk.content)
        fund_category = self._extract_fund_category(fund_type)
        content_types = self._extract_content_types(metadata)
        
        if not fund_name:
            logger.warning(f"Chunk {chunk.chunk_id} has no fund name, skipping")
            return
        
        # Update fund hierarchy
        if fund_name not in self.fund_hierarchy:
            self.fund_hierarchy[fund_name] = FundHierarchy(
                fund_name=fund_name,
                fund_type=fund_type,
                fund_category=fund_category,
                content_types=[],
                document_count=0,
                last_updated=datetime.now().isoformat()
            )
        
        # Update fund entry
        fund_entry = self.fund_hierarchy[fund_name]
        fund_entry.document_count += 1
        fund_entry.last_updated = datetime.now().isoformat()
        
        # Add content types
        for content_type in content_types:
            if content_type not in fund_entry.content_types:
                fund_entry.content_types.append(content_type)
        
        # Update type hierarchy
        if fund_type not in self.type_hierarchy:
            self.type_hierarchy[fund_type] = []
        if fund_name not in self.type_hierarchy[fund_type]:
            self.type_hierarchy[fund_type].append(fund_name)
        
        # Update content hierarchy
        for content_type in content_types:
            if content_type not in self.content_hierarchy:
                self.content_hierarchy[content_type] = []
            if chunk.chunk_id not in self.content_hierarchy[content_type]:
                self.content_hierarchy[content_type].append(chunk.chunk_id)
        
        # Update document index
        doc_id = chunk.source_document_id
        if doc_id not in self.document_index:
            self.document_index[doc_id] = []
        if chunk.chunk_id not in self.document_index[doc_id]:
            self.document_index[doc_id].append(chunk.chunk_id)
    
    def _extract_fund_name(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract fund name from metadata."""
        # Try different metadata fields
        fund_name = metadata.get('fund_name')
        if not fund_name:
            fund_name = metadata.get('citation_info', {}).get('fund_name')
        if not fund_name:
            # Try to extract from hierarchical keys
            hierarchical_keys = metadata.get('hierarchical_keys', [])
            for key in hierarchical_keys:
                if key.startswith('fund:'):
                    return key.split(':', 1)[1]
        
        return fund_name.lower() if fund_name else None
    
    def _extract_fund_type(self, metadata: Dict[str, Any], content: str) -> str:
        """Extract fund type from metadata and content."""
        # Try metadata first
        fund_type = metadata.get('fund_type')
        if fund_type:
            return self.fund_type_mappings.get(fund_type.lower(), self._normalize_key(fund_type))
        
        # Try hierarchical keys
        hierarchical_keys = metadata.get('hierarchical_keys', [])
        for key in hierarchical_keys:
            if key.startswith('type:'):
                return key.split(':', 1)[1]
        
        # Extract from content
        content_lower = content.lower()
        for pattern, mapped_type in self.fund_type_mappings.items():
            if pattern in content_lower:
                return mapped_type
        
        return 'unknown'
    
    def _extract_fund_category(self, fund_type: str) -> str:
        """Extract fund category from fund type."""
        if fund_type in ['large_cap', 'mid_cap', 'small_cap', 'multi_cap', 'flexi_cap']:
            return 'equity'
        elif fund_type == 'elss':
            return 'tax_saving'
        elif fund_type in ['debt', 'hybrid']:
            return fund_type
        elif fund_type == 'focused':
            return 'equity'
        elif fund_type == 'arbitrage':
            return 'hybrid'
        else:
            return 'other'
    
    def _extract_content_types(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract content types from metadata."""
        content_types = []
        
        # Try content_type field
        content_type = metadata.get('content_type')
        if content_type:
            mapped_type = self.content_type_mappings.get(content_type.lower(), content_type)
            content_types.append(mapped_type)
        
        # Try hierarchical keys
        hierarchical_keys = metadata.get('hierarchical_keys', [])
        for key in hierarchical_keys:
            if key.startswith('content:'):
                content_type = key.split(':', 1)[1]
                mapped_type = self.content_type_mappings.get(content_type, content_type)
                content_types.append(mapped_type)
        
        # Try retrieval tags
        retrieval_tags = metadata.get('retrieval_tags', [])
        for tag in retrieval_tags:
            mapped_type = self.content_type_mappings.get(tag.lower(), tag)
            if mapped_type not in content_types:
                content_types.append(mapped_type)
        
        # Try financial data
        financial_data = metadata.get('financial_data', {})
        for data_type in financial_data.keys():
            mapped_type = self.content_type_mappings.get(data_type, data_type)
            if mapped_type not in content_types:
                content_types.append(mapped_type)
        
        return content_types if content_types else ['general']
    
    def _normalize_key(self, key: str) -> str:
        """Normalize key for consistent storage."""
        return re.sub(r'[^a-z0-9_]', '_', key.lower())
    
    def get_funds_by_type(self, fund_type: str) -> List[str]:
        """
        Get all funds of a specific type.
        
        Args:
            fund_type: Fund type to filter by
            
        Returns:
            List of fund names
        """
        return self.type_hierarchy.get(fund_type, [])
    
    def get_chunks_by_content_type(self, content_type: str) -> List[str]:
        """
        Get all chunks of a specific content type.
        
        Args:
            content_type: Content type to filter by
            
        Returns:
            List of chunk IDs
        """
        return self.content_hierarchy.get(content_type, [])
    
    def get_fund_info(self, fund_name: str) -> Optional[FundHierarchy]:
        """
        Get detailed information about a specific fund.
        
        Args:
            fund_name: Fund name
            
        Returns:
            Fund hierarchy information or None
        """
        return self.fund_hierarchy.get(fund_name.lower())
    
    def search_funds(self, query: str, fund_type: str = None) -> List[FundHierarchy]:
        """
        Search for funds by name or type.
        
        Args:
            query: Search query
            fund_type: Optional fund type filter
            
        Returns:
            List of matching fund hierarchies
        """
        query_lower = query.lower()
        results = []
        
        for fund_name, fund_info in self.fund_hierarchy.items():
            # Filter by type if specified
            if fund_type and fund_info.fund_type != fund_type:
                continue
            
            # Search in fund name
            if query_lower in fund_name:
                results.append(fund_info)
                continue
            
            # Search in content types
            for content_type in fund_info.content_types:
                if query_lower in content_type:
                    results.append(fund_info)
                    break
        
        return results
    
    def get_fund_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the fund hierarchy.
        
        Returns:
            Statistics dictionary
        """
        # Count by fund type
        type_counts = {}
        for fund_info in self.fund_hierarchy.values():
            fund_type = fund_info.fund_type
            type_counts[fund_type] = type_counts.get(fund_type, 0) + 1
        
        # Count by category
        category_counts = {}
        for fund_info in self.fund_hierarchy.values():
            category = fund_info.fund_category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Content type distribution
        content_type_counts = {}
        for content_type, chunk_ids in self.content_hierarchy.items():
            content_type_counts[content_type] = len(chunk_ids)
        
        # Document statistics
        total_documents = len(self.document_index)
        total_chunks = sum(len(chunk_ids) for chunk_ids in self.document_index.values())
        
        return {
            "total_funds": len(self.fund_hierarchy),
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "fund_types": list(self.type_hierarchy.keys()),
            "fund_type_distribution": type_counts,
            "fund_categories": list(set(info.fund_category for info in self.fund_hierarchy.values())),
            "category_distribution": category_counts,
            "content_types": list(self.content_hierarchy.keys()),
            "content_type_distribution": content_type_counts,
            "average_chunks_per_fund": total_chunks / len(self.fund_hierarchy) if self.fund_hierarchy else 0,
            "average_documents_per_fund": total_documents / len(self.fund_hierarchy) if self.fund_hierarchy else 0
        }
    
    def create_fund_hierarchy(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Create comprehensive fund hierarchy structure.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Fund hierarchy dictionary
        """
        hierarchy = {
            "funds": {},
            "types": {},
            "content_types": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_chunks": len(chunks),
                "total_funds": 0
            }
        }
        
        # Process chunks
        for chunk in chunks:
            metadata = chunk.metadata
            fund_name = self._extract_fund_name(metadata)
            fund_type = self._extract_fund_type(metadata, chunk.content)
            content_types = self._extract_content_types(metadata)
            
            if not fund_name:
                continue
            
            # Add to funds
            if fund_name not in hierarchy["funds"]:
                hierarchy["funds"][fund_name] = {
                    "fund_type": fund_type,
                    "content_types": set(),
                    "chunks": [],
                    "documents": set()
                }
            
            hierarchy["funds"][fund_name]["chunks"].append(chunk.chunk_id)
            hierarchy["funds"][fund_name]["documents"].add(chunk.source_document_id)
            hierarchy["funds"][fund_name]["content_types"].update(content_types)
            
            # Add to types
            if fund_type not in hierarchy["types"]:
                hierarchy["types"][fund_type] = set()
            hierarchy["types"][fund_type].add(fund_name)
            
            # Add to content types
            for content_type in content_types:
                if content_type not in hierarchy["content_types"]:
                    hierarchy["content_types"][content_type] = []
                hierarchy["content_types"][content_type].append(chunk.chunk_id)
        
        # Convert sets to lists for JSON serialization
        for fund_data in hierarchy["funds"].values():
            fund_data["content_types"] = list(fund_data["content_types"])
            fund_data["documents"] = list(fund_data["documents"])
        
        for fund_set in hierarchy["types"].values():
            hierarchy["types"][fund_type] = list(fund_set)
        
        hierarchy["metadata"]["total_funds"] = len(hierarchy["funds"])
        
        return hierarchy
    
    def setup_metadata_filters(self) -> Dict[str, Any]:
        """
        Setup metadata filters for vector database queries.
        
        Returns:
            Filter configurations
        """
        filters = {
            "fund_filters": {},
            "type_filters": {},
            "content_filters": {},
            "combined_filters": {}
        }
        
        # Fund filters
        for fund_name in self.fund_hierarchy.keys():
            filters["fund_filters"][fund_name] = {"hierarchical_fund": fund_name}
        
        # Type filters
        for fund_type in self.type_hierarchy.keys():
            filters["type_filters"][fund_type] = {"hierarchical_type": fund_type}
        
        # Content filters
        for content_type in self.content_hierarchy.keys():
            filters["content_filters"][content_type] = {"hierarchical_content": content_type}
        
        # Combined filters
        for fund_type, funds in self.type_hierarchy.items():
            for fund_name in funds:
                fund_info = self.fund_hierarchy.get(fund_name)
                if fund_info:
                    for content_type in fund_info.content_types:
                        filter_key = f"{fund_name}_{content_type}"
                        filters["combined_filters"][filter_key] = {
                            "hierarchical_fund": fund_name,
                            "hierarchical_content": content_type
                        }
        
        return filters
    
    def route_queries(self, query: str, fund_type: str = None) -> Dict[str, Any]:
        """
        Route queries to appropriate search strategies.
        
        Args:
            query: User query
            fund_type: Optional fund type filter
            
        Returns:
            Query routing information
        """
        query_lower = query.lower()
        
        # Analyze query for routing
        routing_info = {
            "query": query,
            "query_type": "general",
            "target_funds": [],
            "target_types": [],
            "target_content_types": [],
            "search_strategy": "semantic",
            "filters": {}
        }
        
        # Check for specific fund mentions
        for fund_name in self.fund_hierarchy.keys():
            if fund_name in query_lower:
                routing_info["target_funds"].append(fund_name)
                routing_info["query_type"] = "fund_specific"
        
        # Check for fund type mentions
        for type_name in self.type_hierarchy.keys():
            if type_name.replace('_', ' ') in query_lower or type_name in query_lower:
                routing_info["target_types"].append(type_name)
                routing_info["query_type"] = "type_specific"
        
        # Check for content type mentions
        content_keywords = {
            "expense_ratio": ["expense ratio", "charges", "fees"],
            "exit_load": ["exit load", "withdrawal", "redemption"],
            "nav": ["nav", "net asset value"],
            "sip": ["sip", "systematic investment", "monthly"],
            "aum": ["aum", "assets under management"],
            "risk": ["risk", "riskometer", "risk level"],
            "benchmark": ["benchmark", "index"],
            "performance": ["performance", "returns", "growth"]
        }
        
        for content_type, keywords in content_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    routing_info["target_content_types"].append(content_type)
                    routing_info["query_type"] = "content_specific"
                    break
        
        # Apply fund type filter if specified
        if fund_type:
            routing_info["target_types"] = [fund_type]
            routing_info["target_funds"] = self.get_funds_by_type(fund_type)
        
        # Build filters
        if routing_info["target_funds"]:
            routing_info["filters"]["hierarchical_fund"] = {"$in": routing_info["target_funds"]}
        
        if routing_info["target_types"]:
            routing_info["filters"]["hierarchical_type"] = {"$in": routing_info["target_types"]}
        
        if routing_info["target_content_types"]:
            routing_info["filters"]["hierarchical_content"] = {"$in": routing_info["target_content_types"]}
        
        # Determine search strategy
        if routing_info["target_funds"]:
            routing_info["search_strategy"] = "fund_focused"
        elif routing_info["target_content_types"]:
            routing_info["search_strategy"] = "content_focused"
        elif routing_info["target_types"]:
            routing_info["search_strategy"] = "type_focused"
        else:
            routing_info["search_strategy"] = "general"
        
        return routing_info
    
    def optimize_index_structure(self) -> Dict[str, Any]:
        """
        Optimize index structure for better performance.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            "original_structure": self.get_fund_statistics(),
            "optimizations_applied": [],
            "performance_improvements": {}
        }
        
        # Remove empty content types
        empty_content_types = [
            ct for ct, chunks in self.content_hierarchy.items() 
            if len(chunks) == 0
        ]
        for ct in empty_content_types:
            del self.content_hierarchy[ct]
            optimization_results["optimizations_applied"].append(f"Removed empty content type: {ct}")
        
        # Merge similar content types
        similar_types = {
            "performance": ["returns", "performance"],
            "fees": ["expense_ratio", "exit_load"],
            "investment": ["sip", "investment"]
        }
        
        for merged_type, similar_content_types in similar_types.items():
            existing_types = [ct for ct in similar_content_types if ct in self.content_hierarchy]
            if len(existing_types) > 1:
                # Merge content types
                all_chunks = []
                for ct in existing_types:
                    all_chunks.extend(self.content_hierarchy[ct])
                    del self.content_hierarchy[ct]
                
                self.content_hierarchy[merged_type] = list(set(all_chunks))
                optimization_results["optimizations_applied"].append(f"Merged {existing_types} into {merged_type}")
        
        # Rebuild fund hierarchy
        for fund_name, fund_info in self.fund_hierarchy.items():
            # Update content types based on new content hierarchy
            new_content_types = []
            for chunk_id in self.document_index.get(fund_info.fund_name.lower(), []):
                for content_type, chunk_ids in self.content_hierarchy.items():
                    if chunk_id in chunk_ids and content_type not in new_content_types:
                        new_content_types.append(content_type)
            
            fund_info.content_types = new_content_types
        
        # Save optimized index
        self._save_index()
        
        optimization_results["final_structure"] = self.get_fund_statistics()
        optimization_results["optimization_timestamp"] = datetime.now().isoformat()
        
        return optimization_results
    
    def _save_index(self) -> None:
        """Save hierarchical index to disk."""
        try:
            # Convert dataclasses to dictionaries for JSON serialization
            fund_hierarchy_dict = {}
            for fund_name, fund_info in self.fund_hierarchy.items():
                fund_hierarchy_dict[fund_name] = {
                    "fund_name": fund_info.fund_name,
                    "fund_type": fund_info.fund_type,
                    "fund_category": fund_info.fund_category,
                    "content_types": fund_info.content_types,
                    "document_count": fund_info.document_count,
                    "last_updated": fund_info.last_updated
                }
            
            index_data = {
                "fund_hierarchy": fund_hierarchy_dict,
                "type_hierarchy": self.type_hierarchy,
                "content_hierarchy": self.content_hierarchy,
                "document_index": self.document_index,
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            index_file = self.index_path / "hierarchical_index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved hierarchical index to {index_file}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def load_index(self) -> bool:
        """
        Load hierarchical index from disk.
        
        Returns:
            Success status
        """
        try:
            index_file = self.index_path / "hierarchical_index.json"
            
            if not index_file.exists():
                logger.info("No existing index found, will build new one")
                return False
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Load fund hierarchy
            self.fund_hierarchy.clear()
            for fund_name, fund_data in index_data["fund_hierarchy"].items():
                self.fund_hierarchy[fund_name] = FundHierarchy(
                    fund_name=fund_data["fund_name"],
                    fund_type=fund_data["fund_type"],
                    fund_category=fund_data["fund_category"],
                    content_types=fund_data["content_types"],
                    document_count=fund_data["document_count"],
                    last_updated=fund_data["last_updated"]
                )
            
            # Load other hierarchies
            self.type_hierarchy = index_data["type_hierarchy"]
            self.content_hierarchy = index_data["content_hierarchy"]
            self.document_index = index_data["document_index"]
            
            logger.info(f"Loaded hierarchical index with {len(self.fund_hierarchy)} funds")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False


# Import regex for normalization
import re
