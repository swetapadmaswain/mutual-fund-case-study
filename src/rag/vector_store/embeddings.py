"""
Embedding model integration for Phase 2.2 - Vector Store Setup and Configuration.
"""
import asyncio
from typing import List, Dict, Any, Optional, Union
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError


class EmbeddingModel:
    """Handles embedding generation using sentence-transformers."""
    
    def __init__(self, 
                 model_name: str = "BAAI/bge-small-en",
                 device: str = "cpu",
                 batch_size: int = 32,
                 cache_dir: str = "cache/embeddings"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the embedding model
            device: Device to run inference on ('cpu' or 'cuda')
            batch_size: Batch size for embedding generation
            cache_dir: Directory for caching embeddings
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.tokenizer = None
        self.embedding_dim = 384  # bge-small-en dimension
        
        logger.info(f"Initialized EmbeddingModel with {model_name}")
    
    def load_model(self) -> None:
        """Load the embedding model and tokenizer."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=str(self.cache_dir / "model_cache")
            )
            
            # Update embedding dimension based on model
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except ImportError as e:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise DataCollectionError(f"Failed to import sentence-transformers: {e}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise DataCollectionError(f"Model loading failed: {e}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Clean and prepare text
            cleaned_text = self._prepare_text(text)
            
            # Generate embedding
            embedding = self.model.encode(
                cleaned_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise DataCollectionError(f"Text embedding failed: {e}")
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Clean and prepare texts
            cleaned_texts = [self._prepare_text(text) for text in texts]
            
            # Generate embeddings in batch
            embeddings = self.model.encode(
                cleaned_texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=show_progress
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Failed to embed texts batch: {e}")
            raise DataCollectionError(f"Batch embedding failed: {e}")
    
    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for embedding generation.
        
        Args:
            text: Raw text
            
        Returns:
            Prepared text
        """
        if not text or not text.strip():
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Truncate if too long (most models have max sequence length)
        max_length = 512  # Safe limit for most models
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Model information dictionary
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "device": self.device,
            "batch_size": self.batch_size,
            "model_loaded": self.model is not None,
            "cache_dir": str(self.cache_dir)
        }
    
    def cache_embeddings(self, 
                        embeddings: List[np.ndarray], 
                        texts: List[str], 
                        cache_key: str) -> None:
        """
        Cache embeddings to disk.
        
        Args:
            embeddings: List of embedding vectors
            texts: Original texts
            cache_key: Unique cache key
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            cache_data = {
                "model_name": self.model_name,
                "embedding_dim": self.embedding_dim,
                "timestamp": datetime.now().isoformat(),
                "texts": texts,
                "embeddings": [emb.tolist() if isinstance(emb, np.ndarray) else emb 
                              for emb in embeddings]
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(embeddings)} embeddings to {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to cache embeddings: {e}")
    
    def load_cached_embeddings(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Load cached embeddings from disk.
        
        Args:
            cache_key: Cache key to load
            
        Returns:
            Cached data or None if not found
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verify model compatibility
            if cache_data.get("model_name") != self.model_name:
                logger.warning(f"Cache model mismatch: {cache_data.get('model_name')} != {self.model_name}")
                return None
            
            if cache_data.get("embedding_dim") != self.embedding_dim:
                logger.warning(f"Cache dimension mismatch: {cache_data.get('embedding_dim')} != {self.embedding_dim}")
                return None
            
            logger.info(f"Loaded {len(cache_data.get('embeddings', []))} cached embeddings from {cache_file}")
            return cache_data
            
        except Exception as e:
            logger.error(f"Failed to load cached embeddings: {e}")
            return None


class EmbeddingCache:
    """Manages embedding caching and retrieval."""
    
    def __init__(self, cache_dir: str = "cache/embeddings"):
        """Initialize embedding cache."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index = {}
        self._load_cache_index()
    
    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
            else:
                self.cache_index = {}
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            self.cache_index = {}
    
    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def generate_cache_key(self, texts: List[str], model_name: str) -> str:
        """
        Generate cache key for texts and model.
        
        Args:
            texts: List of texts to cache
            model_name: Name of embedding model
            
        Returns:
            Cache key string
        """
        import hashlib
        
        # Create content hash
        content = f"{model_name}|" + "|".join(texts)
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def get_cached_embeddings(self, cache_key: str) -> Optional[List[np.ndarray]]:
        """
        Get cached embeddings.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached embeddings or None
        """
        if cache_key not in self.cache_index:
            return None
        
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                # Remove from index if file doesn't exist
                del self.cache_index[cache_key]
                self._save_cache_index()
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            embeddings = [np.array(emb) for emb in cache_data["embeddings"]]
            
            logger.debug(f"Retrieved {len(embeddings)} cached embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to get cached embeddings: {e}")
            return None
    
    def cache_embeddings(self, 
                        cache_key: str, 
                        embeddings: List[np.ndarray], 
                        texts: List[str], 
                        model_name: str) -> None:
        """
        Cache embeddings with metadata.
        
        Args:
            cache_key: Cache key
            embeddings: Embedding vectors
            texts: Original texts
            model_name: Model name
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            cache_data = {
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "texts": texts,
                "embeddings": [emb.tolist() for emb in embeddings]
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Update index
            self.cache_index[cache_key] = {
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "text_count": len(texts),
                "file_size": cache_file.stat().st_size
            }
            self._save_cache_index()
            
            logger.info(f"Cached {len(embeddings)} embeddings with key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache embeddings: {e}")
    
    def clear_cache(self, older_than_days: int = 30) -> None:
        """
        Clear old cache entries.
        
        Args:
            older_than_days: Remove entries older than this many days
        """
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 3600)
            keys_to_remove = []
            
            for cache_key, metadata in self.cache_index.items():
                timestamp = datetime.fromisoformat(metadata["timestamp"]).timestamp()
                if timestamp < cutoff_time:
                    keys_to_remove.append(cache_key)
            
            # Remove old files
            for cache_key in keys_to_remove:
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
                del self.cache_index[cache_key]
            
            self._save_cache_index()
            
            logger.info(f"Cleared {len(keys_to_remove)} old cache entries")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        total_files = 0
        total_size = 0
        model_counts = {}
        
        for cache_key, metadata in self.cache_index.items():
            total_files += 1
            total_size += metadata.get("file_size", 0)
            model_name = metadata.get("model_name", "unknown")
            model_counts[model_name] = model_counts.get(model_name, 0) + 1
        
        return {
            "total_cached_files": total_files,
            "total_cache_size_mb": total_size / (1024 * 1024),
            "models_used": list(model_counts.keys()),
            "cache_entries_per_model": model_counts,
            "cache_directory": str(self.cache_dir)
        }


class EmbeddingService:
    """High-level service for embedding operations."""
    
    def __init__(self, 
                 model_name: str = "BAAI/bge-small-en",
                 device: str = "cpu",
                 batch_size: int = 32,
                 enable_cache: bool = True):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of embedding model
            device: Device for inference
            batch_size: Batch size for processing
            enable_cache: Whether to use caching
        """
        self.embedding_model = EmbeddingModel(
            model_name=model_name,
            device=device,
            batch_size=batch_size
        )
        
        self.cache = EmbeddingCache() if enable_cache else None
        self.enable_cache = enable_cache
        
        logger.info(f"Initialized EmbeddingService with model: {model_name}")
    
    async def embed_texts_async(self, 
                               texts: List[str], 
                               use_cache: bool = None) -> List[np.ndarray]:
        """
        Asynchronously embed texts with caching.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache (overrides instance setting)
            
        Returns:
            List of embedding vectors
        """
        use_cache = use_cache if use_cache is not None else self.enable_cache
        
        try:
            # Check cache first
            if use_cache and self.cache:
                cache_key = self.cache.generate_cache_key(texts, self.embedding_model.model_name)
                cached_embeddings = self.cache.get_cached_embeddings(cache_key)
                
                if cached_embeddings is not None:
                    logger.debug(f"Using cached embeddings for {len(texts)} texts")
                    return cached_embeddings
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.embedding_model.embed_texts(texts)
            
            # Cache results
            if use_cache and self.cache:
                self.cache.cache_embeddings(
                    cache_key, embeddings, texts, self.embedding_model.model_name
                )
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise DataCollectionError(f"Embedding generation failed: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information.
        
        Returns:
            Service information dictionary
        """
        info = self.embedding_model.get_embedding_info()
        info.update({
            "cache_enabled": self.enable_cache,
            "cache_stats": self.cache.get_cache_stats() if self.cache else None
        })
        return info
