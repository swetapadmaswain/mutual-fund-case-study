"""
Vector database implementation using ChromaDB for Phase 2.2.
"""
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import uuid

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.chunker import Chunk


class VectorDatabase:
    """ChromaDB-based vector database for storing and retrieving embeddings."""
    
    def __init__(self, 
                 collection_name: str = "mutual_fund_chunks",
                 persist_directory: str = "cache/vector_db",
                 embedding_dimension: int = 384):
        """
        Initialize vector database.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            embedding_dimension: Dimension of embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_dimension = embedding_dimension
        
        self.client = None
        self.collection = None
        
        logger.info(f"Initialized VectorDatabase with collection: {collection_name}")
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            logger.info("Initializing ChromaDB client")
            
            # Create client with persistence
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Mutual Fund FAQ Assistant Chunks",
                        "created_at": datetime.now().isoformat(),
                        "embedding_dimension": self.embedding_dimension
                    }
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
        except ImportError as e:
            logger.error("ChromaDB not installed. Install with: pip install chromadb")
            raise DataCollectionError(f"Failed to import ChromaDB: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise DataCollectionError(f"ChromaDB initialization failed: {e}")
    
    def add_chunks(self, chunks: List[Chunk], embeddings: List[np.ndarray]) -> List[str]:
        """
        Add chunks with embeddings to the database.
        
        Args:
            chunks: List of chunks to add
            embeddings: List of embedding vectors
            
        Returns:
            List of document IDs
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunks count ({len(chunks)}) != embeddings count ({len(embeddings)})")
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                # Generate unique ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
                
                # Document content
                documents.append(chunk.content)
                
                # Enhanced metadata
                metadata = chunk.metadata.copy()
                metadata.update({
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "token_count": chunk.token_count,
                    "source_document_id": chunk.source_document_id,
                    "chunk_type": chunk.chunk_type,
                    "added_at": datetime.now().isoformat(),
                    "embedding_dimension": self.embedding_dimension
                })
                
                # Add hierarchical keys as separate metadata fields for filtering
                if "hierarchical_keys" in metadata:
                    hierarchical_keys = metadata["hierarchical_keys"]
                    for key in hierarchical_keys:
                        if ":" in key:
                            key_type, key_value = key.split(":", 1)
                            metadata[f"hierarchical_{key_type}"] = key_value
                
                metadatas.append(metadata)
            
            # Convert embeddings to list format
            embedding_list = [emb.tolist() if isinstance(emb, np.ndarray) else emb 
                             for emb in embeddings]
            
            # Add to collection
            logger.info(f"Adding {len(chunks)} chunks to vector database")
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embedding_list
            )
            
            logger.info(f"Successfully added {len(ids)} documents to collection")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add chunks to database: {e}")
            raise DataCollectionError(f"Database insertion failed: {e}")
    
    def search(self, 
               query_embedding: np.ndarray, 
               top_k: int = 5,
               where_filter: Optional[Dict[str, Any]] = None,
               where_document_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            where_filter: Metadata filter
            where_document_filter: Document content filter
            
        Returns:
            List of search results
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            # Convert embedding to list format
            query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
            
            # Build query parameters
            query_params = {
                "query_embeddings": [query_list],
                "n_results": top_k
            }
            
            # Add filters if provided
            if where_filter:
                query_params["where"] = where_filter
            
            if where_document_filter:
                query_params["where_document"] = where_document_filter
            
            # Execute search
            logger.debug(f"Searching with top_k={top_k}, filters={where_filter}")
            results = self.collection.query(**query_params)
            
            # Format results
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                    }
                    formatted_results.append(result)
            
            logger.debug(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search database: {e}")
            raise DataCollectionError(f"Database search failed: {e}")
    
    def get_by_filter(self, 
                     where_filter: Dict[str, Any],
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get documents by metadata filter.
        
        Args:
            where_filter: Metadata filter
            limit: Maximum number of results
            
        Returns:
            List of documents
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            query_params = {
                "where": where_filter,
                "include": ["documents", "metadatas"]
            }
            
            if limit:
                query_params["limit"] = limit
            
            results = self.collection.get(**query_params)
            
            formatted_results = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    result = {
                        "id": results["ids"][i],
                        "document": results["documents"][i],
                        "metadata": results["metadatas"][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to get documents by filter: {e}")
            raise DataCollectionError(f"Database query failed: {e}")
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"] and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            return None
    
    def update_document(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update document metadata.
        
        Args:
            doc_id: Document ID
            metadata: New metadata
            
        Returns:
            Success status
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            self.collection.update(
                ids=[doc_id],
                metadatas=[metadata]
            )
            logger.info(f"Updated metadata for document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the database.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Success status
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Collection statistics
        """
        if self.client is None:
            self._initialize_client()
        
        try:
            # Get collection count
            count = self.collection.count()
            
            # Get collection metadata
            collection_info = self.collection.metadata or {}
            
            # Sample some documents to analyze metadata distribution
            sample_results = self.collection.get(limit=100, include=["metadatas"])
            
            # Analyze metadata distribution
            metadata_stats = {}
            if sample_results["metadatas"]:
                for metadata in sample_results["metadatas"]:
                    for key, value in metadata.items():
                        if key not in metadata_stats:
                            metadata_stats[key] = {}
                        
                        value_str = str(value)
                        metadata_stats[key][value_str] = metadata_stats[key].get(value_str, 0) + 1
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_dimension": self.embedding_dimension,
                "persist_directory": str(self.persist_directory),
                "collection_metadata": collection_info,
                "metadata_distribution": metadata_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def create_index(self, index_type: str = "auto") -> bool:
        """
        Create index for faster search (if supported).
        
        Args:
            index_type: Type of index to create
            
        Returns:
            Success status
        """
        try:
            # ChromaDB automatically handles indexing
            # This is a placeholder for future index optimization
            logger.info(f"Index creation requested (type: {index_type}). ChromaDB handles indexing automatically.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def backup_collection(self, backup_path: str) -> bool:
        """
        Backup the collection to a specified path.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            Success status
        """
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Export collection data
            all_results = self.collection.get(include=["documents", "metadatas", "embeddings"])
            
            backup_data = {
                "collection_name": self.collection_name,
                "collection_metadata": self.collection.metadata,
                "embedding_dimension": self.embedding_dimension,
                "export_timestamp": datetime.now().isoformat(),
                "document_count": len(all_results["ids"]),
                "ids": all_results["ids"],
                "documents": all_results["documents"],
                "metadatas": all_results["metadatas"],
                "embeddings": all_results["embeddings"]
            }
            
            # Save backup
            backup_file = backup_dir / f"{self.collection_name}_backup.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backed up {len(all_results['ids'])} documents to {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup collection: {e}")
            return False
    
    def restore_collection(self, backup_path: str) -> bool:
        """
        Restore collection from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Success status
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Load backup data
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Clear existing collection
            if self.collection:
                self.collection.delete()
            
            # Restore data
            self.collection.add(
                ids=backup_data["ids"],
                documents=backup_data["documents"],
                metadatas=backup_data["metadatas"],
                embeddings=backup_data["embeddings"]
            )
            
            logger.info(f"Restored {len(backup_data['ids'])} documents from backup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore collection: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            Success status
        """
        try:
            if self.collection:
                self.collection.delete()
                logger.info("Cleared all documents from collection")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        try:
            if self.client:
                # ChromaDB handles cleanup automatically
                logger.info("Closed vector database connection")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


class HierarchicalVectorDB:
    """Enhanced vector database with hierarchical indexing for mutual fund data."""
    
    def __init__(self, base_db: VectorDatabase):
        """
        Initialize hierarchical vector database.
        
        Args:
            base_db: Base vector database instance
        """
        self.base_db = base_db
        self.fund_hierarchy = {}
        self._build_fund_hierarchy()
    
    def _build_fund_hierarchy(self) -> None:
        """Build fund hierarchy from existing data."""
        try:
            # Get all unique funds and types
            all_docs = self.base_db.get_by_filter({}, limit=1000)
            
            for doc in all_docs:
                metadata = doc["metadata"]
                fund_name = metadata.get("hierarchical_fund", "")
                fund_type = metadata.get("hierarchical_type", "")
                content_type = metadata.get("hierarchical_content", "")
                
                if fund_name and fund_name not in self.fund_hierarchy:
                    self.fund_hierarchy[fund_name] = {
                        "fund_type": fund_type,
                        "content_types": set(),
                        "document_count": 0
                    }
                
                if fund_name in self.fund_hierarchy:
                    if content_type:
                        self.fund_hierarchy[fund_name]["content_types"].add(content_type)
                    self.fund_hierarchy[fund_name]["document_count"] += 1
            
            # Convert sets to lists for JSON serialization
            for fund_data in self.fund_hierarchy.values():
                fund_data["content_types"] = list(fund_data["content_types"])
            
            logger.info(f"Built hierarchy for {len(self.fund_hierarchy)} funds")
            
        except Exception as e:
            logger.error(f"Failed to build fund hierarchy: {e}")
    
    def search_by_fund(self, 
                      query_embedding: np.ndarray, 
                      fund_name: str, 
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search within a specific fund.
        
        Args:
            query_embedding: Query embedding
            fund_name: Fund name to search within
            top_k: Number of results
            
        Returns:
            Search results
        """
        filter_dict = {"hierarchical_fund": fund_name}
        return self.base_db.search(query_embedding, top_k, where_filter=filter_dict)
    
    def search_by_fund_type(self, 
                           query_embedding: np.ndarray, 
                           fund_type: str, 
                           top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by fund type.
        
        Args:
            query_embedding: Query embedding
            fund_type: Fund type (e.g., "mid_cap", "large_cap")
            top_k: Number of results
            
        Returns:
            Search results
        """
        filter_dict = {"hierarchical_type": fund_type}
        return self.base_db.search(query_embedding, top_k, where_filter=filter_dict)
    
    def search_by_content_type(self, 
                              query_embedding: np.ndarray, 
                              content_type: str, 
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by content type.
        
        Args:
            query_embedding: Query embedding
            content_type: Content type (e.g., "expense_ratio", "nav")
            top_k: Number of results
            
        Returns:
            Search results
        """
        filter_dict = {"hierarchical_content": content_type}
        return self.base_db.search(query_embedding, top_k, where_filter=filter_dict)
    
    def get_fund_summary(self, fund_name: str) -> Dict[str, Any]:
        """
        Get summary of a specific fund.
        
        Args:
            fund_name: Fund name
            
        Returns:
            Fund summary
        """
        if fund_name not in self.fund_hierarchy:
            return {"error": f"Fund not found: {fund_name}"}
        
        fund_data = self.fund_hierarchy[fund_name]
        
        # Get sample documents
        sample_docs = self.base_db.get_by_filter(
            {"hierarchical_fund": fund_name}, 
            limit=5
        )
        
        return {
            "fund_name": fund_name,
            "fund_type": fund_data["fund_type"],
            "content_types": fund_data["content_types"],
            "document_count": fund_data["document_count"],
            "sample_documents": sample_docs
        }
    
    def get_hierarchy_stats(self) -> Dict[str, Any]:
        """
        Get hierarchy statistics.
        
        Returns:
            Hierarchy statistics
        """
        return {
            "total_funds": len(self.fund_hierarchy),
            "fund_types": list(set(data["fund_type"] for data in self.fund_hierarchy.values())),
            "total_documents": sum(data["document_count"] for data in self.fund_hierarchy.values()),
            "fund_details": self.fund_hierarchy
        }
