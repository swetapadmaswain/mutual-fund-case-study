"""
Monitoring and metrics collection for Phase 1.
"""
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from src.config.settings import settings
from src.utils.logger import logger


@dataclass
class PipelineMetrics:
    """Metrics for pipeline execution."""
    start_time: float
    end_time: float
    duration: float
    total_urls: int
    successful_fetches: int
    failed_fetches: int
    total_documents: int
    new_documents: int
    duplicate_documents: int
    processed_documents: int
    failed_documents: int
    validation_errors: int
    ssl_enabled_count: int
    avg_content_length: float
    unique_funds: int


class Monitoring:
    """Monitoring system for Phase 1 pipeline."""
    
    def __init__(self):
        """Initialize monitoring system."""
        self.metrics_dir = Path("cache/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_metrics: List[PipelineMetrics] = []
        self.session_start_time = time.time()
    
    def start_pipeline_session(self) -> str:
        """
        Start a new pipeline monitoring session.
        
        Returns:
            Session ID
        """
        session_id = f"phase1_{int(time.time())}"
        logger.info(f"Starting monitoring session: {session_id}")
        return session_id
    
    def record_pipeline_metrics(self, results: Dict[str, Any]) -> PipelineMetrics:
        """
        Record pipeline execution metrics.
        
        Args:
            results: Pipeline execution results
            
        Returns:
            PipelineMetrics object
        """
        try:
            # Extract metrics from results
            metrics = PipelineMetrics(
                start_time=results.get('start_time', 0),
                end_time=results.get('end_time', 0),
                duration=results.get('duration', 0),
                total_urls=results.get('collection_results', {}).get('total_urls', 0),
                successful_fetches=results.get('collection_results', {}).get('successful_fetches', 0),
                failed_fetches=results.get('collection_results', {}).get('failed_fetches', 0),
                total_documents=results.get('processing_results', {}).get('total_documents', 0),
                new_documents=results.get('processing_results', {}).get('new_documents', 0),
                duplicate_documents=results.get('processing_results', {}).get('duplicate_documents', 0),
                processed_documents=results.get('processing_results', {}).get('processed_documents', 0),
                failed_documents=results.get('processing_results', {}).get('failed_documents', 0),
                validation_errors=results.get('validation_results', {}).get('invalid_urls', 0),
                ssl_enabled_count=results.get('validation_results', {}).get('summary', {}).get('ssl_enabled', 0),
                avg_content_length=results.get('final_summary', {}).get('processing_stats', {}).get('avg_content_length', 0),
                unique_funds=results.get('final_summary', {}).get('unique_funds', 0)
            )
            
            self.current_metrics.append(metrics)
            
            # Save metrics to file
            self._save_metrics()
            
            logger.info(f"Recorded pipeline metrics: duration={metrics.duration:.2f}s, "
                       f"success_rate={metrics.successful_fetches}/{metrics.total_urls}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
            raise
    
    def _save_metrics(self) -> None:
        """Save current metrics to file."""
        try:
            metrics_file = self.metrics_dir / "phase1_metrics.json"
            
            # Convert metrics to serializable format
            metrics_data = [asdict(metric) for metric in self.current_metrics]
            
            # Add metadata
            metrics_with_metadata = {
                'session_info': {
                    'start_time': self.session_start_time,
                    'last_updated': time.time(),
                    'total_sessions': len(self.current_metrics)
                },
                'metrics': metrics_data
            }
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_with_metadata, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary from recorded metrics.
        
        Returns:
            Performance summary dictionary
        """
        if not self.current_metrics:
            return {
                'total_sessions': 0,
                'avg_duration': 0,
                'avg_success_rate': 0,
                'total_documents_processed': 0,
                'avg_content_length': 0
            }
        
        total_sessions = len(self.current_metrics)
        total_duration = sum(m.duration for m in self.current_metrics)
        total_urls = sum(m.total_urls for m in self.current_metrics)
        total_successful = sum(m.successful_fetches for m in self.current_metrics)
        total_documents = sum(m.processed_documents for m in self.current_metrics)
        avg_content_length = sum(m.avg_content_length for m in self.current_metrics) / total_sessions
        
        return {
            'total_sessions': total_sessions,
            'avg_duration': total_duration / total_sessions,
            'avg_success_rate': (total_successful / total_urls * 100) if total_urls > 0 else 0,
            'total_documents_processed': total_documents,
            'avg_content_length': avg_content_length,
            'last_updated': datetime.now().isoformat()
        }
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check system health based on metrics.
        
        Returns:
            Health check result
        """
        health_status = {
            'status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check recent performance
            if self.current_metrics:
                latest_metrics = self.current_metrics[-1]
                
                # Success rate check
                success_rate = (latest_metrics.successful_fetches / latest_metrics.total_urls * 100) if latest_metrics.total_urls > 0 else 0
                health_status['checks']['success_rate'] = success_rate
                
                if success_rate < 80:
                    health_status['status'] = 'unhealthy'
                    health_status['errors'].append(f"Low success rate: {success_rate:.1f}%")
                elif success_rate < 95:
                    health_status['status'] = 'warning'
                    health_status['warnings'].append(f"Moderate success rate: {success_rate:.1f}%")
                
                # Duration check
                health_status['checks']['duration'] = latest_metrics.duration
                if latest_metrics.duration > 300:  # 5 minutes
                    health_status['status'] = 'warning'
                    health_status['warnings'].append(f"Long execution time: {latest_metrics.duration:.2f}s")
                
                # Document processing check
                processing_rate = (latest_metrics.processed_documents / latest_metrics.total_urls * 100) if latest_metrics.total_urls > 0 else 0
                health_status['checks']['processing_rate'] = processing_rate
                
                if processing_rate < 80:
                    health_status['status'] = 'warning'
                    health_status['warnings'].append(f"Low processing rate: {processing_rate:.1f}%")
            
            # Check file system health
            cache_dir = Path(settings.cache_dir)
            if cache_dir.exists():
                cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                health_status['checks']['cache_size_mb'] = cache_size / (1024 * 1024)
                
                if cache_size > 1024 * 1024 * 1024:  # 1GB
                    health_status['warnings'].append("Large cache size: consider cleanup")
            
            # Check configuration
            health_status['checks']['configuration'] = {
                'allowed_domains': len(settings.allowed_domains),
                'hdfc_urls': len(settings.hdfc_fund_urls),
                'timeout_seconds': settings.timeout_seconds,
                'max_retries': settings.max_retries
            }
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['errors'].append(f"Health check failed: {e}")
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    def export_metrics_report(self, output_path: str) -> None:
        """
        Export comprehensive metrics report.
        
        Args:
            output_path: Path to save the report
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'performance_summary': self.get_performance_summary(),
                'health_check': self.check_health(),
                'detailed_metrics': [asdict(m) for m in self.current_metrics],
                'configuration': {
                    'allowed_domains': settings.allowed_domains,
                    'hdfc_fund_urls': settings.hdfc_fund_urls,
                    'data_collection_delay': settings.data_collection_delay,
                    'timeout_seconds': settings.timeout_seconds,
                    'max_retries': settings.max_retries
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Metrics report exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics report: {e}")
            raise


# Global monitoring instance
monitoring = Monitoring()
