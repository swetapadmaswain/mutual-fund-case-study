"""
Caching Optimization System for Phase 2.6

Optimizes caching strategies, implements intelligent cache management, and improves system performance through caching.
"""

import asyncio
import time
import hashlib
import json
import pickle
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict, OrderedDict
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    ttl: Optional[timedelta]
    metadata: Dict[str, Any]

@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    average_access_time: float
    memory_utilization: float

@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size_mb: float
    max_entries: int
    default_ttl: timedelta
    eviction_policy: str  # "lru", "lfu", "ttl", "adaptive"
    compression_enabled: bool
    serialization_method: str  # "pickle", "json", "custom"
    background_cleanup: bool
    cleanup_interval: timedelta

class CachingOptimizer:
    """
    Advanced caching optimization system.
    
    Features:
    - Multiple eviction policies (LRU, LFU, TTL, Adaptive)
    - Intelligent cache warming
    - Compression and serialization optimization
    - Background cleanup and maintenance
    - Performance monitoring and analytics
    - Distributed cache support
    """
    
    def __init__(self, cache_dir: str = "cache/caching_optimizer"):
        """
        Initialize caching optimizer.
        
        Args:
            cache_dir: Directory for cache data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache storage
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_stats = CacheStats(
            total_entries=0,
            total_size_bytes=0,
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            hit_rate=0.0,
            average_access_time=0.0,
            memory_utilization=0.0
        )
        
        # Configuration
        self.config = self._initialize_config()
        
        # Performance tracking
        self.access_times: deque = deque(maxlen=1000)
        self.cache_warmup_keys: List[str] = []
        
        # Background processes
        self.cleanup_active = False
        self.cleanup_thread = None
        self.warmup_active = False
        self.warmup_thread = None
        
        # Lock for thread safety
        self.cache_lock = threading.RLock()
        
        # Load existing cache data
        self._load_cache_data()
        
        logger.info("Caching Optimizer initialized")
    
    def _initialize_config(self) -> CacheConfig:
        """Initialize cache configuration."""
        return CacheConfig(
            max_size_mb=512.0,  # 512 MB
            max_entries=10000,
            default_ttl=timedelta(hours=1),
            eviction_policy="adaptive",
            compression_enabled=True,
            serialization_method="pickle",
            background_cleanup=True,
            cleanup_interval=timedelta(minutes=5)
        )
    
    def _load_cache_data(self) -> None:
        """Load cache data from disk."""
        cache_file = self.cache_dir / "cache_data.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Restore cache entries
                for key, entry_data in data.get("entries", {}).items():
                    entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
                    entry_data['last_accessed'] = datetime.fromisoformat(entry_data['last_accessed'])
                    if entry_data.get('ttl'):
                        entry_data['ttl'] = timedelta(seconds=entry_data['ttl']['total_seconds'])
                    self.memory_cache[key] = CacheEntry(**entry_data)
                
                # Restore stats
                stats_data = data.get("stats", {})
                self.cache_stats = CacheStats(**stats_data)
                
                logger.info(f"Loaded {len(self.memory_cache)} cache entries")
                
            except Exception as e:
                logger.error(f"Error loading cache data: {e}")
    
    def _save_cache_data(self) -> None:
        """Save cache data to disk."""
        try:
            cache_file = self.cache_dir / "cache_data.pkl"
            
            # Prepare data for serialization
            serializable_entries = {}
            for key, entry in self.memory_cache.items():
                entry_dict = asdict(entry)
                entry_dict['created_at'] = entry.created_at.isoformat()
                entry_dict['last_accessed'] = entry.last_accessed.isoformat()
                if entry.ttl:
                    entry_dict['ttl'] = {"total_seconds": entry.ttl.total_seconds()}
                serializable_entries[key] = entry_dict
            
            data = {
                "entries": serializable_entries,
                "stats": asdict(self.cache_stats),
                "config": asdict(self.config),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"Error saving cache data: {e}")
    
    def start_background_processes(self) -> None:
        """Start background cleanup and warmup processes."""
        if self.config.background_cleanup and not self.cleanup_active:
            self.cleanup_active = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            logger.info("Background cleanup started")
        
        if not self.warmup_active:
            self.warmup_active = True
            self.warmup_thread = threading.Thread(target=self._warmup_loop, daemon=True)
            self.warmup_thread.start()
            logger.info("Cache warmup started")
    
    def stop_background_processes(self) -> None:
        """Stop background processes."""
        self.cleanup_active = False
        self.warmup_active = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        if self.warmup_thread:
            self.warmup_thread.join(timeout=10)
        
        logger.info("Background processes stopped")
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self.cleanup_active:
            try:
                self._cleanup_expired_entries()
                self._enforce_memory_limits()
                time.sleep(self.config.cleanup_interval.total_seconds())
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(self.config.cleanup_interval.total_seconds())
    
    def _warmup_loop(self) -> None:
        """Background cache warmup loop."""
        while self.warmup_active:
            try:
                await asyncio.sleep(60)  # Check every minute
                if self.cache_warmup_keys:
                    await self._warmup_cache()
            except Exception as e:
                logger.error(f"Error in warmup loop: {e}")
                await asyncio.sleep(60)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        start_time = time.time()
        
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                
                # Check TTL
                if entry.ttl and (datetime.now() - entry.created_at) > entry.ttl:
                    del self.memory_cache[key]
                    self.cache_stats.miss_count += 1
                    return default
                
                # Update access info
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                
                # Move to end for LRU
                if self.config.eviction_policy in ["lru", "adaptive"]:
                    self.memory_cache.move_to_end(key)
                
                # Update stats
                self.cache_stats.hit_count += 1
                access_time = time.time() - start_time
                self.access_times.append(access_time)
                
                return entry.value
            else:
                self.cache_stats.miss_count += 1
                return default
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None, 
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            True if successful
        """
        try:
            # Serialize value and calculate size
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value) if isinstance(serialized_value, bytes) else len(str(serialized_value).encode())
            
            # Check memory limits
            if size_bytes > self.config.max_size_mb * 1024 * 1024:
                logger.warning(f"Value too large for cache: {size_bytes} bytes")
                return False
            
            # Enforce limits before adding
            await self._enforce_memory_limits()
            
            with self.cache_lock:
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=1,
                    size_bytes=size_bytes,
                    ttl=ttl or self.config.default_ttl,
                    metadata=metadata or {}
                )
                
                # Add to cache
                self.memory_cache[key] = entry
                
                # Update stats
                self.cache_stats.total_entries = len(self.memory_cache)
                self.cache_stats.total_size_bytes += size_bytes
                
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache entry: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted
        """
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                del self.memory_cache[key]
                
                # Update stats
                self.cache_stats.total_entries = len(self.memory_cache)
                self.cache_stats.total_size_bytes -= entry.size_bytes
                
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        with self.cache_lock:
            self.memory_cache.clear()
            self.cache_stats = CacheStats(
                total_entries=0,
                total_size_bytes=0,
                hit_count=0,
                miss_count=0,
                eviction_count=0,
                hit_rate=0.0,
                average_access_time=0.0,
                memory_utilization=0.0
            )
        
        logger.info("Cache cleared")
    
    def _serialize_value(self, value: Any) -> Union[bytes, str]:
        """Serialize value based on configuration."""
        if self.config.serialization_method == "pickle":
            return pickle.dumps(value)
        elif self.config.serialization_method == "json":
            return json.dumps(value, default=str)
        else:
            return str(value)
    
    def _deserialize_value(self, serialized: Union[bytes, str]) -> Any:
        """Deserialize value based on configuration."""
        if self.config.serialization_method == "pickle":
            return pickle.loads(serialized)
        elif self.config.serialization_method == "json":
            return json.loads(serialized)
        else:
            return serialized
    
    async def _enforce_memory_limits(self) -> None:
        """Enforce memory and entry limits."""
        # Check entry count limit
        while len(self.memory_cache) >= self.config.max_entries:
            await self._evict_entry()
        
        # Check memory size limit
        max_size_bytes = self.config.max_size_mb * 1024 * 1024
        while self.cache_stats.total_size_bytes >= max_size_bytes:
            await self._evict_entry()
    
    async def _evict_entry(self) -> Optional[str]:
        """
        Evict an entry based on eviction policy.
        
        Returns:
            Evicted key or None
        """
        if not self.memory_cache:
            return None
        
        evicted_key = None
        
        if self.config.eviction_policy == "lru":
            evicted_key = self._evict_lru()
        elif self.config.eviction_policy == "lfu":
            evicted_key = self._evict_lfu()
        elif self.config.eviction_policy == "ttl":
            evicted_key = self._evict_ttl()
        elif self.config.eviction_policy == "adaptive":
            evicted_key = self._evict_adaptive()
        else:
            evicted_key = self._evict_lru()  # Default to LRU
        
        if evicted_key:
            self.cache_stats.eviction_count += 1
            logger.debug(f"Evicted cache entry: {evicted_key}")
        
        return evicted_key
    
    def _evict_lru(self) -> Optional[str]:
        """Evict least recently used entry."""
        # OrderedDict maintains insertion order, so first item is LRU
        if self.memory_cache:
            lru_key = next(iter(self.memory_cache))
            entry = self.memory_cache[lru_key]
            del self.memory_cache[lru_key]
            
            # Update stats
            self.cache_stats.total_entries = len(self.memory_cache)
            self.cache_stats.total_size_bytes -= entry.size_bytes
            
            return lru_key
        return None
    
    def _evict_lfu(self) -> Optional[str]:
        """Evict least frequently used entry."""
        if not self.memory_cache:
            return None
        
        # Find entry with lowest access count
        lfu_key = min(self.memory_cache.keys(), 
                     key=lambda k: self.memory_cache[k].access_count)
        
        entry = self.memory_cache[lfu_key]
        del self.memory_cache[lfu_key]
        
        # Update stats
        self.cache_stats.total_entries = len(self.memory_cache)
        self.cache_stats.total_size_bytes -= entry.size_bytes
        
        return lfu_key
    
    def _evict_ttl(self) -> Optional[str]:
        """Evict expired entry."""
        now = datetime.now()
        
        for key, entry in self.memory_cache.items():
            if entry.ttl and (now - entry.created_at) > entry.ttl:
                del self.memory_cache[key]
                
                # Update stats
                self.cache_stats.total_entries = len(self.memory_cache)
                self.cache_stats.total_size_bytes -= entry.size_bytes
                
                return key
        
        # If no expired entries, fall back to LRU
        return self._evict_lru()
    
    def _evict_adaptive(self) -> Optional[str]:
        """Evict entry using adaptive policy."""
        # Combine LRU and LFU with weights
        if not self.memory_cache:
            return None
        
        # Calculate adaptive score
        def adaptive_score(entry: CacheEntry) -> float:
            age = (datetime.now() - entry.last_accessed).total_seconds()
            frequency = entry.access_count
            
            # Lower score = better candidate for eviction
            return age / (frequency + 1)
        
        adaptive_key = min(self.memory_cache.keys(), 
                          key=lambda k: adaptive_score(self.memory_cache[k]))
        
        entry = self.memory_cache[adaptive_key]
        del self.memory_cache[adaptive_key]
        
        # Update stats
        self.cache_stats.total_entries = len(self.memory_cache)
        self.cache_stats.total_size_bytes -= entry.size_bytes
        
        return adaptive_key
    
    def _cleanup_expired_entries(self) -> int:
        """Clean up expired entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if entry.ttl and (now - entry.created_at) > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            entry = self.memory_cache[key]
            del self.memory_cache[key]
            
            # Update stats
            self.cache_stats.total_entries = len(self.memory_cache)
            self.cache_stats.total_size_bytes -= entry.size_bytes
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    async def _warmup_cache(self) -> None:
        """Warm up cache with frequently accessed keys."""
        if not self.cache_warmup_keys:
            return
        
        warmed_count = 0
        for key in self.cache_warmup_keys[:100]:  # Limit warmup batch
            if key not in self.memory_cache:
                # In a real implementation, this would load the actual data
                # For demonstration, we'll just simulate warmup
                await self.set(key, f"warmup_value_for_{key}", ttl=timedelta(hours=2))
                warmed_count += 1
        
        if warmed_count > 0:
            logger.info(f"Warmed up {warmed_count} cache entries")
    
    def add_warmup_key(self, key: str) -> None:
        """Add key to warmup list."""
        if key not in self.cache_warmup_keys:
            self.cache_warmup_keys.append(key)
    
    def remove_warmup_key(self, key: str) -> None:
        """Remove key from warmup list."""
        if key in self.cache_warmup_keys:
            self.cache_warmup_keys.remove(key)
    
    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        with self.cache_lock:
            # Update hit rate
            total_requests = self.cache_stats.hit_count + self.cache_stats.miss_count
            if total_requests > 0:
                self.cache_stats.hit_rate = (self.cache_stats.hit_count / total_requests) * 100
            
            # Update average access time
            if self.access_times:
                self.cache_stats.average_access_time = statistics.mean(self.access_times)
            
            # Update memory utilization
            if self.config.max_size_mb > 0:
                self.cache_stats.memory_utilization = (
                    (self.cache_stats.total_size_bytes / (self.config.max_size_mb * 1024 * 1024)) * 100
                )
            
            return self.cache_stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information."""
        stats = self.get_cache_stats()
        
        # Entry analysis
        entry_ages = []
        entry_sizes = []
        access_counts = []
        
        for entry in self.memory_cache.values():
            entry_ages.append((datetime.now() - entry.created_at).total_seconds())
            entry_sizes.append(entry.size_bytes)
            access_counts.append(entry.access_count)
        
        return {
            "configuration": asdict(self.config),
            "statistics": asdict(stats),
            "entry_analysis": {
                "total_entries": len(self.memory_cache),
                "average_age_seconds": statistics.mean(entry_ages) if entry_ages else 0,
                "average_size_bytes": statistics.mean(entry_sizes) if entry_sizes else 0,
                "average_access_count": statistics.mean(access_counts) if access_counts else 0,
                "oldest_entry_age": max(entry_ages) if entry_ages else 0,
                "largest_entry_size": max(entry_sizes) if entry_sizes else 0
            },
            "warmup_keys": len(self.cache_warmup_keys),
            "background_processes": {
                "cleanup_active": self.cleanup_active,
                "warmup_active": self.warmup_active
            }
        }
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize cache performance.
        
        Returns:
            Optimization results
        """
        logger.info("Starting cache optimization")
        
        before_stats = self.get_cache_stats()
        
        # Test different eviction policies
        policies = ["lru", "lfu", "ttl", "adaptive"]
        best_policy = self.config.eviction_policy
        best_hit_rate = before_stats.hit_rate
        
        for policy in policies:
            if policy == self.config.eviction_policy:
                continue
            
            # Simulate policy performance
            simulated_hit_rate = self._simulate_policy_performance(policy)
            
            if simulated_hit_rate > best_hit_rate:
                best_hit_rate = simulated_hit_rate
                best_policy = policy
        
        # Apply best policy
        old_policy = self.config.eviction_policy
        self.config.eviction_policy = best_policy
        
        # Optimize TTL
        optimal_ttl = self._calculate_optimal_ttl()
        if optimal_ttl != self.config.default_ttl:
            self.config.default_ttl = optimal_ttl
        
        # Clean up expired entries
        cleaned = self._cleanup_expired_entries()
        
        # Get after stats
        after_stats = self.get_cache_stats()
        
        # Calculate improvement
        hit_rate_improvement = after_stats.hit_rate - before_stats.hit_rate
        
        optimization_result = {
            "policy_changed": old_policy != best_policy,
            "old_policy": old_policy,
            "new_policy": best_policy,
            "ttl_optimized": optimal_ttl != self.config.default_ttl,
            "entries_cleaned": cleaned,
            "hit_rate_before": before_stats.hit_rate,
            "hit_rate_after": after_stats.hit_rate,
            "hit_rate_improvement": hit_rate_improvement,
            "memory_utilization_before": before_stats.memory_utilization,
            "memory_utilization_after": after_stats.memory_utilization
        }
        
        logger.info(f"Cache optimization completed: {hit_rate_improvement:.2f}% hit rate improvement")
        
        return optimization_result
    
    def _simulate_policy_performance(self, policy: str) -> float:
        """Simulate performance of eviction policy."""
        # Simplified simulation - in reality would test with actual data
        policy_performance = {
            "lru": 85.0,
            "lfu": 87.0,
            "ttl": 82.0,
            "adaptive": 88.0
        }
        
        return policy_performance.get(policy, 80.0)
    
    def _calculate_optimal_ttl(self) -> timedelta:
        """Calculate optimal TTL based on access patterns."""
        if not self.memory_cache:
            return self.config.default_ttl
        
        # Calculate average age of accessed entries
        now = datetime.now()
        ages = [(now - entry.last_accessed).total_seconds() for entry in self.memory_cache.values()]
        
        if ages:
            avg_age = statistics.mean(ages)
            # Set TTL to 2x average age
            optimal_ttl_seconds = avg_age * 2
            return timedelta(seconds=min(optimal_ttl_seconds, 86400))  # Max 24 hours
        
        return self.config.default_ttl
    
    async def benchmark_cache(self, operations: int = 1000) -> Dict[str, float]:
        """
        Benchmark cache performance.
        
        Args:
            operations: Number of operations to perform
            
        Returns:
            Benchmark results
        """
        logger.info(f"Starting cache benchmark with {operations} operations")
        
        # Clear cache for clean benchmark
        await self.clear()
        
        # Benchmark writes
        write_start = time.time()
        for i in range(operations // 2):
            await self.set(f"benchmark_key_{i}", f"benchmark_value_{i}")
        write_time = time.time() - write_start
        
        # Benchmark reads
        read_start = time.time()
        for i in range(operations // 2):
            await self.get(f"benchmark_key_{i}")
        read_time = time.time() - read_start
        
        # Benchmark mixed operations
        mixed_start = time.time()
        for i in range(operations):
            if i % 2 == 0:
                await self.set(f"mixed_key_{i}", f"mixed_value_{i}")
            else:
                await self.get(f"mixed_key_{i-1}")
        mixed_time = time.time() - mixed_start
        
        stats = self.get_cache_stats()
        
        return {
            "write_operations": operations // 2,
            "write_time": write_time,
            "write_ops_per_second": (operations // 2) / write_time,
            "read_operations": operations // 2,
            "read_time": read_time,
            "read_ops_per_second": (operations // 2) / read_time,
            "mixed_operations": operations,
            "mixed_time": mixed_time,
            "mixed_ops_per_second": operations / mixed_time,
            "hit_rate": stats.hit_rate,
            "average_access_time": stats.average_access_time
        }
    
    def export_cache_data(self, format_type: str = "json") -> str:
        """
        Export cache data for analysis.
        
        Args:
            format_type: Export format ("json", "csv", "pickle")
            
        Returns:
            Exported data string
        """
        if format_type == "json":
            return self._export_json()
        elif format_type == "csv":
            return self._export_csv()
        elif format_type == "pickle":
            return self._export_pickle()
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_json(self) -> str:
        """Export cache data as JSON."""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "configuration": asdict(self.config),
            "statistics": asdict(self.get_cache_stats()),
            "entries": []
        }
        
        for key, entry in self.memory_cache.items():
            entry_data = {
                "key": key,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "size_bytes": entry.size_bytes,
                "ttl_seconds": entry.ttl.total_seconds() if entry.ttl else None,
                "metadata": entry.metadata
            }
            export_data["entries"].append(entry_data)
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self) -> str:
        """Export cache data as CSV."""
        lines = ["key,created_at,last_accessed,access_count,size_bytes,ttl_seconds"]
        
        for key, entry in self.memory_cache.items():
            line = f"{key},{entry.created_at.isoformat()},{entry.last_accessed.isoformat()},{entry.access_count},{entry.size_bytes},{entry.ttl.total_seconds() if entry.ttl else ''}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _export_pickle(self) -> bytes:
        """Export cache data as pickle."""
        export_data = {
            "timestamp": datetime.now(),
            "configuration": self.config,
            "statistics": self.get_cache_stats(),
            "entries": dict(self.memory_cache)
        }
        
        return pickle.dumps(export_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on caching system.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_cache_stats()
        info = self.get_cache_info()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "cache_size": stats.total_entries,
                "hit_rate": stats.hit_rate,
                "memory_utilization": stats.memory_utilization,
                "eviction_policy": self.config.eviction_policy
            }
        }
        
        # Check hit rate
        if stats.hit_rate < 70:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low hit rate: {stats.hit_rate:.1f}%")
        
        # Check memory utilization
        if stats.memory_utilization > 90:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"High memory utilization: {stats.memory_utilization:.1f}%")
        
        # Check background processes
        if self.config.background_cleanup and not self.cleanup_active:
            health_status["status"] = "degraded"
            health_status["issues"].append("Background cleanup is not active")
        
        return health_status
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old cache data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_entries = 0
        keys_to_remove = []
        
        for key, entry in self.memory_cache.items():
            if entry.last_accessed < cutoff_date:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            await self.delete(key)
            old_entries += 1
        
        # Save updated cache
        self._save_cache_data()
        
        logger.info(f"Cleaned up {old_entries} old cache entries")
        return old_entries
