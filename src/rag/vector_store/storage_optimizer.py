"""
Storage optimization module for Phase 2.2 - Vector compression and management.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import json
import gzip
from datetime import datetime, timedelta
import shutil

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError


class StorageOptimizer:
    """Optimizes vector storage for efficiency and performance."""
    
    def __init__(self, 
                 storage_path: str = "cache/vector_storage",
                 compression_enabled: bool = True,
                 backup_enabled: bool = True):
        """
        Initialize storage optimizer.
        
        Args:
            storage_path: Path to storage directory
            compression_enabled: Whether to enable compression
            backup_enabled: Whether to enable automatic backups
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.compression_enabled = compression_enabled
        self.backup_enabled = backup_enabled
        
        # Compression settings
        self.compression_threshold_mb = 100  # Compress files larger than 100MB
        self.backup_retention_days = 30
        
        logger.info(f"Initialized StorageOptimizer with compression: {compression_enabled}")
    
    def compress_vectors(self, vectors: List[np.ndarray], compression_ratio: float = 0.8) -> List[np.ndarray]:
        """
        Compress vectors using dimensionality reduction.
        
        Args:
            vectors: List of vectors to compress
            compression_ratio: Target compression ratio (0.0-1.0)
            
        Returns:
            List of compressed vectors
        """
        if not vectors or compression_ratio >= 1.0:
            return vectors
        
        try:
            from sklearn.decomposition import PCA
            
            logger.info(f"Compressing {len(vectors)} vectors with ratio {compression_ratio}")
            
            # Convert to numpy array
            vector_matrix = np.array(vectors)
            original_dim = vector_matrix.shape[1]
            target_dim = int(original_dim * compression_ratio)
            
            # Apply PCA for dimensionality reduction
            pca = PCA(n_components=target_dim)
            compressed_vectors = pca.fit_transform(vector_matrix)
            
            # Calculate compression quality
            explained_variance = pca.explained_variance_ratio_.sum()
            
            logger.info(f"Compressed from {original_dim} to {target_dim} dimensions "
                       f"(variance retained: {explained_variance:.3f})")
            
            return compressed_vectors.tolist()
            
        except ImportError:
            logger.warning("scikit-learn not available, skipping compression")
            return vectors
        except Exception as e:
            logger.error(f"Vector compression failed: {e}")
            return vectors
    
    def quantize_vectors(self, vectors: List[np.ndarray], bits: int = 8) -> List[np.ndarray]:
        """
        Quantize vectors to reduce storage size.
        
        Args:
            vectors: List of vectors to quantize
            bits: Number of bits for quantization (8, 16, or 32)
            
        Returns:
            List of quantized vectors
        """
        if bits not in [8, 16, 32]:
            raise ValueError("Bits must be 8, 16, or 32")
        
        try:
            logger.info(f"Quantizing {len(vectors)} vectors to {bits} bits")
            
            quantized_vectors = []
            
            for vector in vectors:
                vector_array = np.array(vector)
                
                if bits == 8:
                    quantized = np.round(vector_array * 127).astype(np.int8) / 127.0
                elif bits == 16:
                    quantized = np.round(vector_array * 32767).astype(np.int16) / 32767.0
                else:  # 32 bits
                    quantized = vector_array.astype(np.float32)
                
                quantized_vectors.append(quantized)
            
            logger.info(f"Quantized vectors to {bits} bits")
            return quantized_vectors
            
        except Exception as e:
            logger.error(f"Vector quantization failed: {e}")
            return vectors
    
    def compress_file(self, file_path: Path) -> Optional[Path]:
        """
        Compress a file using gzip.
        
        Args:
            file_path: Path to file to compress
            
        Returns:
            Path to compressed file or None if failed
        """
        try:
            if not file_path.exists():
                return None
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb < self.compression_threshold_mb:
                logger.debug(f"File {file_path} is below compression threshold")
                return None
            
            # Create compressed file path
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            # Compress file
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Calculate compression ratio
            original_size = file_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            compression_ratio = compressed_size / original_size
            
            logger.info(f"Compressed {file_path}: {original_size/(1024*1024):.1f}MB → "
                       f"{compressed_size/(1024*1024):.1f}MB (ratio: {compression_ratio:.3f})")
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"Failed to compress file {file_path}: {e}")
            return None
    
    def decompress_file(self, compressed_path: Path) -> Optional[Path]:
        """
        Decompress a gzip file.
        
        Args:
            compressed_path: Path to compressed file
            
        Returns:
            Path to decompressed file or None if failed
        """
        try:
            if not compressed_path.exists() or not compressed_path.suffix == '.gz':
                return None
            
            # Create decompressed file path
            decompressed_path = compressed_path.with_suffix('')
            
            # Decompress file
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Decompressed {compressed_path} to {decompressed_path}")
            return decompressed_path
            
        except Exception as e:
            logger.error(f"Failed to decompress file {compressed_path}: {e}")
            return None
    
    def setup_backup_procedures(self) -> Dict[str, Any]:
        """
        Setup automatic backup procedures.
        
        Returns:
            Backup configuration
        """
        backup_config = {
            "backup_enabled": self.backup_enabled,
            "backup_directory": self.storage_path / "backups",
            "backup_retention_days": self.backup_retention_days,
            "backup_schedule": "daily",
            "backup_types": ["full", "incremental"],
            "compression_enabled": self.compression_enabled
        }
        
        if self.backup_enabled:
            backup_dir = Path(backup_config["backup_directory"])
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup script
            backup_script = backup_dir / "backup_config.json"
            with open(backup_script, 'w', encoding='utf-8') as f:
                json.dump(backup_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup procedures configured at {backup_dir}")
        
        return backup_config
    
    def create_backup(self, source_path: str, backup_name: str = None) -> Optional[Path]:
        """
        Create a backup of the specified path.
        
        Args:
            source_path: Path to backup
            backup_name: Optional backup name
            
        Returns:
            Path to backup or None if failed
        """
        if not self.backup_enabled:
            return None
        
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Source path does not exist: {source_path}")
                return None
            
            # Generate backup name
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            backup_dir = self.storage_path / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / backup_name
            
            # Create backup
            if source.is_file():
                backup_path = backup_path.with_suffix(source.suffix)
                shutil.copy2(source, backup_path)
            else:
                shutil.copytree(source, backup_path, dirs_exist_ok=True)
            
            # Compress backup if enabled
            if self.compression_enabled:
                compressed_backup = self.compress_file(backup_path)
                if compressed_backup:
                    # Remove uncompressed backup
                    if backup_path.is_file():
                        backup_path.unlink()
                    elif backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    backup_path = compressed_backup
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def configure_retention_policies(self) -> Dict[str, Any]:
        """
        Configure data retention policies.
        
        Returns:
            Retention policy configuration
        """
        retention_config = {
            "backup_retention_days": self.backup_retention_days,
            "cache_retention_days": 7,
            "log_retention_days": 30,
            "temp_retention_hours": 24,
            "compression_retention_days": 90,
            "policies": {
                "backups": {
                    "max_age_days": self.backup_retention_days,
                    "max_count": 10,
                    "cleanup_action": "delete"
                },
                "cache": {
                    "max_age_days": 7,
                    "max_size_mb": 1000,
                    "cleanup_action": "delete"
                },
                "logs": {
                    "max_age_days": 30,
                    "max_size_mb": 500,
                    "cleanup_action": "compress"
                },
                "temp": {
                    "max_age_hours": 24,
                    "cleanup_action": "delete"
                }
            }
        }
        
        # Save retention configuration
        retention_file = self.storage_path / "retention_policy.json"
        with open(retention_file, 'w', encoding='utf-8') as f:
            json.dump(retention_config, f, indent=2, ensure_ascii=False)
        
        logger.info("Configured retention policies")
        return retention_config
    
    def apply_retention_policies(self) -> Dict[str, Any]:
        """
        Apply retention policies to clean up old data.
        
        Returns:
            Cleanup results
        """
        logger.info("Applying retention policies")
        
        cleanup_results = {
            "backups_cleaned": 0,
            "cache_cleaned": 0,
            "logs_cleaned": 0,
            "temp_cleaned": 0,
            "space_freed_mb": 0.0,
            "errors": []
        }
        
        try:
            # Get retention policies
            retention_config = self.configure_retention_policies()
            policies = retention_config["policies"]
            
            # Clean old backups
            backup_dir = self.storage_path / "backups"
            if backup_dir.exists():
                cleanup_results["backups_cleaned"] = self._cleanup_directory(
                    backup_dir, 
                    policies["backups"]["max_age_days"],
                    policies["backups"]["max_count"]
                )
            
            # Clean cache
            cache_dir = self.storage_path.parent / "cache"
            if cache_dir.exists():
                cleanup_results["cache_cleaned"] = self._cleanup_directory(
                    cache_dir,
                    policies["cache"]["max_age_days"],
                    None
                )
            
            # Clean logs
            logs_dir = self.storage_path.parent / "logs"
            if logs_dir.exists():
                cleanup_results["logs_cleaned"] = self._cleanup_directory(
                    logs_dir,
                    policies["logs"]["max_age_days"],
                    None
                )
            
            # Clean temp files
            temp_dir = self.storage_path / "temp"
            if temp_dir.exists():
                cleanup_results["temp_cleaned"] = self._cleanup_directory(
                    temp_dir,
                    policies["temp"]["max_age_hours"] / 24,  # Convert to days
                    None
                )
            
            logger.info(f"Retention cleanup completed: {cleanup_results}")
            
        except Exception as e:
            logger.error(f"Failed to apply retention policies: {e}")
            cleanup_results["errors"].append(str(e))
        
        return cleanup_results
    
    def _cleanup_directory(self, directory: Path, max_age_days: float, max_count: Optional[int]) -> int:
        """
        Clean up directory based on age and count limits.
        
        Args:
            directory: Directory to clean
            max_age_days: Maximum age in days
            max_count: Maximum number of files to keep
            
        Returns:
            Number of items cleaned
        """
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        try:
            # Get all items with their modification times
            items = []
            for item in directory.iterdir():
                if item.is_file() or item.is_dir():
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    items.append((item, mod_time))
            
            # Sort by modification time (oldest first)
            items.sort(key=lambda x: x[1])
            
            # Remove items older than cutoff or exceeding count limit
            for i, (item, mod_time) in enumerate(items):
                should_remove = False
                
                if mod_time < cutoff_time:
                    should_remove = True
                elif max_count and i >= len(items) - max_count:
                    should_remove = True
                
                if should_remove:
                    try:
                        if item.is_file():
                            item.unlink()
                        else:
                            shutil.rmtree(item)
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {item}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to clean directory {directory}: {e}")
        
        return cleaned_count
    
    def monitor_storage_usage(self) -> Dict[str, Any]:
        """
        Monitor storage usage and statistics.
        
        Returns:
            Storage usage statistics
        """
        usage_stats = {
            "total_size_mb": 0.0,
            "file_count": 0,
            "directory_count": 0,
            "compression_ratio": 0.0,
            "largest_files": [],
            "file_type_distribution": {},
            "age_distribution": {
                "less_than_1_day": 0,
                "1_to_7_days": 0,
                "7_to_30_days": 0,
                "more_than_30_days": 0
            },
            "monitoring_timestamp": datetime.now().isoformat()
        }
        
        try:
            now = datetime.now()
            file_sizes = []
            
            for item in self.storage_path.rglob("*"):
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    usage_stats["total_size_mb"] += size_mb
                    usage_stats["file_count"] += 1
                    file_sizes.append((item, size_mb))
                    
                    # File type distribution
                    suffix = item.suffix.lower() or "no_extension"
                    usage_stats["file_type_distribution"][suffix] = \
                        usage_stats["file_type_distribution"].get(suffix, 0) + 1
                    
                    # Age distribution
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    age_days = (now - mod_time).days
                    
                    if age_days < 1:
                        usage_stats["age_distribution"]["less_than_1_day"] += 1
                    elif age_days < 7:
                        usage_stats["age_distribution"]["1_to_7_days"] += 1
                    elif age_days < 30:
                        usage_stats["age_distribution"]["7_to_30_days"] += 1
                    else:
                        usage_stats["age_distribution"]["more_than_30_days"] += 1
                    
                elif item.is_dir():
                    usage_stats["directory_count"] += 1
            
            # Find largest files
            file_sizes.sort(key=lambda x: x[1], reverse=True)
            usage_stats["largest_files"] = [
                {"path": str(item), "size_mb": size_mb} 
                for item, size_mb in file_sizes[:10]
            ]
            
            # Calculate compression ratio
            compressed_files = [f for f in file_sizes if f[0].suffix == '.gz']
            if compressed_files:
                compressed_size = sum(size for _, size in compressed_files)
                original_size = 0
                for file_path, _ in compressed_files:
                    original_path = file_path.with_suffix('')
                    if original_path.exists():
                        original_size += original_path.stat().st_size / (1024 * 1024)
                
                if original_size > 0:
                    usage_stats["compression_ratio"] = compressed_size / original_size
            
            logger.info(f"Storage usage: {usage_stats['total_size_mb']:.1f}MB, "
                       f"{usage_stats['file_count']} files")
            
        except Exception as e:
            logger.error(f"Failed to monitor storage usage: {e}")
            usage_stats["error"] = str(e)
        
        return usage_stats
    
    def optimize_storage(self) -> Dict[str, Any]:
        """
        Run comprehensive storage optimization.
        
        Returns:
            Optimization results
        """
        logger.info("Starting storage optimization")
        
        optimization_results = {
            "original_usage": self.monitor_storage_usage(),
            "optimizations_applied": [],
            "compression_results": {},
            "cleanup_results": {},
            "final_usage": {},
            "optimization_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Apply compression
            if self.compression_enabled:
                compression_results = self._apply_compression()
                optimization_results["compression_results"] = compression_results
                optimization_results["optimizations_applied"].append("compression")
            
            # Apply retention policies
            cleanup_results = self.apply_retention_policies()
            optimization_results["cleanup_results"] = cleanup_results
            optimization_results["optimizations_applied"].append("cleanup")
            
            # Create backup
            if self.backup_enabled:
                backup_path = self.create_backup(str(self.storage_path))
                if backup_path:
                    optimization_results["optimizations_applied"].append("backup")
            
            # Final usage statistics
            optimization_results["final_usage"] = self.monitor_storage_usage()
            
            # Calculate space saved
            original_size = optimization_results["original_usage"].get("total_size_mb", 0)
            final_size = optimization_results["final_usage"].get("total_size_mb", 0)
            space_saved = original_size - final_size
            
            optimization_results["space_saved_mb"] = space_saved
            optimization_results["space_saved_percentage"] = (space_saved / original_size * 100) if original_size > 0 else 0
            
            logger.info(f"Storage optimization completed. Space saved: {space_saved:.1f}MB")
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    def _apply_compression(self) -> Dict[str, Any]:
        """
        Apply compression to eligible files.
        
        Returns:
            Compression results
        """
        compression_results = {
            "files_compressed": 0,
            "original_size_mb": 0.0,
            "compressed_size_mb": 0.0,
            "compression_ratio": 0.0,
            "errors": []
        }
        
        try:
            for file_path in self.storage_path.rglob("*"):
                if file_path.is_file() and not file_path.suffix == '.gz':
                    original_size = file_path.stat().st_size / (1024 * 1024)
                    compression_results["original_size_mb"] += original_size
                    
                    compressed_path = self.compress_file(file_path)
                    if compressed_path:
                        compressed_size = compressed_path.stat().st_size / (1024 * 1024)
                        compression_results["compressed_size_mb"] += compressed_size
                        compression_results["files_compressed"] += 1
                        
                        # Remove original file
                        file_path.unlink()
            
            if compression_results["original_size_mb"] > 0:
                compression_results["compression_ratio"] = \
                    compression_results["compressed_size_mb"] / compression_results["original_size_mb"]
            
            logger.info(f"Compressed {compression_results['files_compressed']} files "
                       f"(ratio: {compression_results['compression_ratio']:.3f})")
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            compression_results["errors"].append(str(e))
        
        return compression_results
