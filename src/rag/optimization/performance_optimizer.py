"""
Performance Optimization System for Phase 2.6

Optimizes system performance, identifies bottlenecks, and implements performance improvements.
"""

import asyncio
import time
import psutil
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import json
import threading
import concurrent.futures

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for system components."""
    component_name: str
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    response_time: float
    throughput: float
    error_rate: float
    cache_hit_rate: float
    queue_length: int
    active_connections: int
    metadata: Dict[str, Any]

@dataclass
class Bottleneck:
    """Represents a performance bottleneck."""
    component: str
    bottleneck_type: str  # "cpu", "memory", "io", "network", "queue"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    impact_score: float
    recommendations: List[str]
    detected_at: datetime

@dataclass
class OptimizationResult:
    """Result of performance optimization."""
    optimization_type: str
    component: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percentage: float
    success: bool
    timestamp: datetime
    details: Dict[str, Any]

class PerformanceOptimizer:
    """
    Optimizes system performance and identifies bottlenecks.
    
    Features:
    - Real-time performance monitoring
    - Bottleneck detection and analysis
    - Performance optimization recommendations
    - Automated optimization implementations
    - Performance trend analysis
    """
    
    def __init__(self, cache_dir: str = "cache/performance_optimizer"):
        """
        Initialize performance optimizer.
        
        Args:
            cache_dir: Directory for caching performance data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance monitoring
        self.metrics_history: deque = deque(maxlen=1000)
        self.component_metrics: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.bottlenecks: List[Bottleneck] = []
        
        # Configuration
        self.monitoring_interval = 5.0  # seconds
        self.performance_thresholds = self._initialize_thresholds()
        self.optimization_strategies = self._initialize_optimization_strategies()
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Performance optimization
        self.optimization_history: List[OptimizationResult] = []
        self.active_optimizations: Dict[str, Any] = {}
        
        # Load existing data
        self._load_metrics()
        self._load_bottlenecks()
        self._load_optimization_history()
        
        logger.info("Performance Optimizer initialized")
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds."""
        return {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 5.0, "critical": 10.0},
            "cache_hit_rate": {"warning": 80.0, "critical": 60.0},
            "queue_length": {"warning": 100, "critical": 500},
            "throughput": {"warning": 50.0, "critical": 20.0}
        }
    
    def _initialize_optimization_strategies(self) -> Dict[str, List[str]]:
        """Initialize optimization strategies."""
        return {
            "cpu": [
                "enable_parallel_processing",
                "optimize_algorithms",
                "reduce_computational_complexity",
                "implement_caching"
            ],
            "memory": [
                "implement_memory_pooling",
                "optimize_data_structures",
                "enable_garbage_collection",
                "reduce_memory_footprint"
            ],
            "io": [
                "implement_async_operations",
                "optimize_database_queries",
                "enable_batch_processing",
                "compress_data"
            ],
            "network": [
                "implement_connection_pooling",
                "enable_compression",
                "optimize_api_calls",
                "implement_cdn"
            ],
            "queue": [
                "increase_queue_capacity",
                "implement_priority_queue",
                "enable_batch_processing",
                "optimize_consumer_threads"
            ]
        }
    
    def _load_metrics(self) -> None:
        """Load metrics from cache."""
        metrics_file = self.cache_dir / "metrics.json"
        
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                
                for component, metrics_list in data.items():
                    for metric_data in metrics_list:
                        metric_data['timestamp'] = datetime.fromisoformat(metric_data['timestamp'])
                        metric = PerformanceMetrics(**metric_data)
                        self.component_metrics[component].append(metric)
                
                logger.info(f"Loaded metrics for {len(self.component_metrics)} components")
                
            except Exception as e:
                logger.error(f"Error loading metrics: {e}")
    
    def _load_bottlenecks(self) -> None:
        """Load bottlenecks from cache."""
        bottlenecks_file = self.cache_dir / "bottlenecks.json"
        
        if bottlenecks_file.exists():
            try:
                with open(bottlenecks_file, 'r') as f:
                    data = json.load(f)
                
                self.bottlenecks = []
                for bottleneck_data in data:
                    bottleneck_data['detected_at'] = datetime.fromisoformat(bottleneck_data['detected_at'])
                    self.bottlenecks.append(Bottleneck(**bottleneck_data))
                
                logger.info(f"Loaded {len(self.bottlenecks)} bottlenecks")
                
            except Exception as e:
                logger.error(f"Error loading bottlenecks: {e}")
    
    def _load_optimization_history(self) -> None:
        """Load optimization history from cache."""
        history_file = self.cache_dir / "optimization_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                
                self.optimization_history = []
                for result_data in data:
                    result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                    self.optimization_history.append(OptimizationResult(**result_data))
                
                logger.info(f"Loaded {len(self.optimization_history)} optimization results")
                
            except Exception as e:
                logger.error(f"Error loading optimization history: {e}")
    
    def _save_metrics(self) -> None:
        """Save metrics to cache."""
        try:
            metrics_file = self.cache_dir / "metrics.json"
            
            serializable_metrics = {}
            for component, metrics_list in self.component_metrics.items():
                serializable_metrics[component] = []
                for metric in metrics_list:
                    metric_dict = asdict(metric)
                    metric_dict['timestamp'] = metric.timestamp.isoformat()
                    serializable_metrics[component].append(metric_dict)
            
            with open(metrics_file, 'w') as f:
                json.dump(serializable_metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _save_bottlenecks(self) -> None:
        """Save bottlenecks to cache."""
        try:
            bottlenecks_file = self.cache_dir / "bottlenecks.json"
            
            serializable_bottlenecks = []
            for bottleneck in self.bottlenecks:
                bottleneck_dict = asdict(bottleneck)
                bottleneck_dict['detected_at'] = bottleneck.detected_at.isoformat()
                serializable_bottlenecks.append(bottleneck_dict)
            
            with open(bottlenecks_file, 'w') as f:
                json.dump(serializable_bottlenecks, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving bottlenecks: {e}")
    
    def _save_optimization_history(self) -> None:
        """Save optimization history to cache."""
        try:
            history_file = self.cache_dir / "optimization_history.json"
            
            serializable_history = []
            for result in self.optimization_history:
                result_dict = asdict(result)
                result_dict['timestamp'] = result.timestamp.isoformat()
                serializable_history.append(result_dict)
            
            with open(history_file, 'w') as f:
                json.dump(serializable_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving optimization history: {e}")
    
    def start_monitoring(self) -> None:
        """Start performance monitoring in background."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Store metrics
                for component, metric in metrics.items():
                    self.component_metrics[component].append(metric)
                
                # Detect bottlenecks
                self._detect_bottlenecks(metrics)
                
                # Save metrics periodically
                if len(self.metrics_history) % 100 == 0:
                    self._save_metrics()
                    self._save_bottlenecks()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_system_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Collect performance metrics for all components."""
        now = datetime.now()
        
        # System-wide metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Component-specific metrics (simulated for demonstration)
        components = {
            "query_processor": {
                "cpu_usage": cpu_percent * 0.3,
                "memory_usage": memory.percent * 0.2,
                "response_time": 0.8,
                "throughput": 120.0,
                "error_rate": 2.0,
                "cache_hit_rate": 85.0,
                "queue_length": 15,
                "active_connections": 8
            },
            "search_engine": {
                "cpu_usage": cpu_percent * 0.4,
                "memory_usage": memory.percent * 0.3,
                "response_time": 0.5,
                "throughput": 200.0,
                "error_rate": 1.5,
                "cache_hit_rate": 90.0,
                "queue_length": 25,
                "active_connections": 12
            },
            "llm_service": {
                "cpu_usage": cpu_percent * 0.2,
                "memory_usage": memory.percent * 0.25,
                "response_time": 2.5,
                "throughput": 40.0,
                "error_rate": 3.0,
                "cache_hit_rate": 75.0,
                "queue_length": 50,
                "active_connections": 5
            },
            "citation_system": {
                "cpu_usage": cpu_percent * 0.1,
                "memory_usage": memory.percent * 0.15,
                "response_time": 0.3,
                "throughput": 150.0,
                "error_rate": 1.0,
                "cache_hit_rate": 95.0,
                "queue_length": 10,
                "active_connections": 3
            }
        }
        
        metrics = {}
        for component, data in components.items():
            metrics[component] = PerformanceMetrics(
                component_name=component,
                timestamp=now,
                cpu_usage=data["cpu_usage"],
                memory_usage=data["memory_usage"],
                response_time=data["response_time"],
                throughput=data["throughput"],
                error_rate=data["error_rate"],
                cache_hit_rate=data["cache_hit_rate"],
                queue_length=data["queue_length"],
                active_connections=data["active_connections"],
                metadata={}
            )
        
        return metrics
    
    def _detect_bottlenecks(self, metrics: Dict[str, PerformanceMetrics]) -> None:
        """Detect performance bottlenecks."""
        new_bottlenecks = []
        
        for component, metric in metrics.items():
            # Check each metric against thresholds
            bottlenecks = self._check_metric_thresholds(component, metric)
            new_bottlenecks.extend(bottlenecks)
        
        # Add new bottlenecks
        for bottleneck in new_bottlenecks:
            if not self._is_duplicate_bottleneck(bottleneck):
                self.bottlenecks.append(bottleneck)
                logger.warning(f"Bottleneck detected: {bottleneck.component} - {bottleneck.description}")
        
        # Clean up old bottlenecks
        self._cleanup_old_bottlenecks()
    
    def _check_metric_thresholds(self, component: str, metric: PerformanceMetrics) -> List[Bottleneck]:
        """Check metrics against thresholds and identify bottlenecks."""
        bottlenecks = []
        
        # CPU usage
        if metric.cpu_usage >= self.performance_thresholds["cpu_usage"]["critical"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="cpu",
                severity="critical",
                description=f"Critical CPU usage: {metric.cpu_usage:.1f}%",
                impact_score=0.9,
                recommendations=self.optimization_strategies["cpu"],
                detected_at=datetime.now()
            ))
        elif metric.cpu_usage >= self.performance_thresholds["cpu_usage"]["warning"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="cpu",
                severity="medium",
                description=f"High CPU usage: {metric.cpu_usage:.1f}%",
                impact_score=0.6,
                recommendations=self.optimization_strategies["cpu"],
                detected_at=datetime.now()
            ))
        
        # Memory usage
        if metric.memory_usage >= self.performance_thresholds["memory_usage"]["critical"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="memory",
                severity="critical",
                description=f"Critical memory usage: {metric.memory_usage:.1f}%",
                impact_score=0.8,
                recommendations=self.optimization_strategies["memory"],
                detected_at=datetime.now()
            ))
        elif metric.memory_usage >= self.performance_thresholds["memory_usage"]["warning"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="memory",
                severity="medium",
                description=f"High memory usage: {metric.memory_usage:.1f}%",
                impact_score=0.5,
                recommendations=self.optimization_strategies["memory"],
                detected_at=datetime.now()
            ))
        
        # Response time
        if metric.response_time >= self.performance_thresholds["response_time"]["critical"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="io",
                severity="critical",
                description=f"Critical response time: {metric.response_time:.2f}s",
                impact_score=0.85,
                recommendations=self.optimization_strategies["io"],
                detected_at=datetime.now()
            ))
        elif metric.response_time >= self.performance_thresholds["response_time"]["warning"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="io",
                severity="medium",
                description=f"High response time: {metric.response_time:.2f}s",
                impact_score=0.6,
                recommendations=self.optimization_strategies["io"],
                detected_at=datetime.now()
            ))
        
        # Error rate
        if metric.error_rate >= self.performance_thresholds["error_rate"]["critical"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="network",
                severity="critical",
                description=f"Critical error rate: {metric.error_rate:.1f}%",
                impact_score=0.95,
                recommendations=self.optimization_strategies["network"],
                detected_at=datetime.now()
            ))
        elif metric.error_rate >= self.performance_thresholds["error_rate"]["warning"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="network",
                severity="medium",
                description=f"High error rate: {metric.error_rate:.1f}%",
                impact_score=0.7,
                recommendations=self.optimization_strategies["network"],
                detected_at=datetime.now()
            ))
        
        # Queue length
        if metric.queue_length >= self.performance_thresholds["queue_length"]["critical"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="queue",
                severity="critical",
                description=f"Critical queue length: {metric.queue_length}",
                impact_score=0.8,
                recommendations=self.optimization_strategies["queue"],
                detected_at=datetime.now()
            ))
        elif metric.queue_length >= self.performance_thresholds["queue_length"]["warning"]:
            bottlenecks.append(Bottleneck(
                component=component,
                bottleneck_type="queue",
                severity="medium",
                description=f"High queue length: {metric.queue_length}",
                impact_score=0.5,
                recommendations=self.optimization_strategies["queue"],
                detected_at=datetime.now()
            ))
        
        return bottlenecks
    
    def _is_duplicate_bottleneck(self, new_bottleneck: Bottleneck) -> bool:
        """Check if bottleneck is a duplicate of existing one."""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for existing in self.bottlenecks:
            if (existing.component == new_bottleneck.component and
                existing.bottleneck_type == new_bottleneck.bottleneck_type and
                existing.detected_at > cutoff_time):
                return True
        
        return False
    
    def _cleanup_old_bottlenecks(self) -> None:
        """Clean up old bottlenecks."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.bottlenecks = [
            bottleneck for bottleneck in self.bottlenecks
            if bottleneck.detected_at > cutoff_time
        ]
    
    async def optimize_component(self, component: str, optimization_type: str) -> OptimizationResult:
        """
        Optimize a specific component.
        
        Args:
            component: Component to optimize
            optimization_type: Type of optimization to apply
            
        Returns:
            OptimizationResult object
        """
        logger.info(f"Optimizing {component} with {optimization_type}")
        
        # Get before metrics
        before_metrics = self._get_component_metrics(component)
        
        # Apply optimization
        success = await self._apply_optimization(component, optimization_type)
        
        # Get after metrics
        after_metrics = self._get_component_metrics(component)
        
        # Calculate improvement
        improvement = self._calculate_improvement(before_metrics, after_metrics)
        
        result = OptimizationResult(
            optimization_type=optimization_type,
            component=component,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement_percentage=improvement,
            success=success,
            timestamp=datetime.now(),
            details={"optimization_applied": optimization_type}
        )
        
        # Store result
        self.optimization_history.append(result)
        self._save_optimization_history()
        
        return result
    
    def _get_component_metrics(self, component: str) -> Dict[str, float]:
        """Get current metrics for a component."""
        if component not in self.component_metrics or not self.component_metrics[component]:
            return {}
        
        latest_metric = self.component_metrics[component][-1]
        return {
            "cpu_usage": latest_metric.cpu_usage,
            "memory_usage": latest_metric.memory_usage,
            "response_time": latest_metric.response_time,
            "throughput": latest_metric.throughput,
            "error_rate": latest_metric.error_rate,
            "cache_hit_rate": latest_metric.cache_hit_rate
        }
    
    async def _apply_optimization(self, component: str, optimization_type: str) -> bool:
        """Apply optimization to component."""
        try:
            # Simulate optimization application
            await asyncio.sleep(0.1)
            
            # In a real implementation, this would apply actual optimizations
            # For demonstration, we'll just mark it as successful
            logger.info(f"Applied {optimization_type} optimization to {component}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return False
    
    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """Calculate improvement percentage."""
        if not before or not after:
            return 0.0
        
        improvements = []
        
        for metric in ["response_time", "cpu_usage", "memory_usage", "error_rate"]:
            if metric in before and metric in after:
                if metric in ["response_time", "cpu_usage", "memory_usage", "error_rate"]:
                    # Lower is better
                    if before[metric] > 0:
                        improvement = (before[metric] - after[metric]) / before[metric] * 100
                        improvements.append(improvement)
                else:
                    # Higher is better
                    if before[metric] > 0:
                        improvement = (after[metric] - before[metric]) / before[metric] * 100
                        improvements.append(improvement)
        
        return statistics.mean(improvements) if improvements else 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Performance summary dictionary
        """
        # Current metrics
        current_metrics = {}
        for component, metrics_list in self.component_metrics.items():
            if metrics_list:
                current_metrics[component] = metrics_list[-1]
        
        # Bottleneck summary
        bottleneck_summary = {
            "total_bottlenecks": len(self.bottlenecks),
            "critical_bottlenecks": len([b for b in self.bottlenecks if b.severity == "critical"]),
            "by_type": defaultdict(int),
            "by_component": defaultdict(int)
        }
        
        for bottleneck in self.bottlenecks:
            bottleneck_summary["by_type"][bottleneck.bottleneck_type] += 1
            bottleneck_summary["by_component"][bottleneck.component] += 1
        
        # Optimization summary
        optimization_summary = {
            "total_optimizations": len(self.optimization_history),
            "successful_optimizations": len([o for o in self.optimization_history if o.success]),
            "average_improvement": 0.0
        }
        
        if self.optimization_history:
            improvements = [o.improvement_percentage for o in self.optimization_history]
            optimization_summary["average_improvement"] = statistics.mean(improvements)
        
        # System health
        system_health = self._calculate_system_health(current_metrics)
        
        return {
            "current_metrics": {
                component: asdict(metric) for component, metric in current_metrics.items()
            },
            "bottleneck_summary": bottleneck_summary,
            "optimization_summary": optimization_summary,
            "system_health": system_health,
            "monitoring_status": {
                "active": self.monitoring_active,
                "components_monitored": len(self.component_metrics),
                "metrics_collected": sum(len(metrics) for metrics in self.component_metrics.values())
            }
        }
    
    def _calculate_system_health(self, current_metrics: Dict[str, PerformanceMetrics]) -> Dict[str, Any]:
        """Calculate overall system health."""
        if not current_metrics:
            return {"status": "unknown", "score": 0.0, "issues": []}
        
        health_score = 100.0
        issues = []
        
        for component, metric in current_metrics.items():
            # Check each metric
            if metric.cpu_usage >= self.performance_thresholds["cpu_usage"]["critical"]:
                health_score -= 20
                issues.append(f"{component}: Critical CPU usage")
            elif metric.cpu_usage >= self.performance_thresholds["cpu_usage"]["warning"]:
                health_score -= 10
                issues.append(f"{component}: High CPU usage")
            
            if metric.memory_usage >= self.performance_thresholds["memory_usage"]["critical"]:
                health_score -= 20
                issues.append(f"{component}: Critical memory usage")
            elif metric.memory_usage >= self.performance_thresholds["memory_usage"]["warning"]:
                health_score -= 10
                issues.append(f"{component}: High memory usage")
            
            if metric.response_time >= self.performance_thresholds["response_time"]["critical"]:
                health_score -= 15
                issues.append(f"{component}: Critical response time")
            elif metric.response_time >= self.performance_thresholds["response_time"]["warning"]:
                health_score -= 8
                issues.append(f"{component}: High response time")
            
            if metric.error_rate >= self.performance_thresholds["error_rate"]["critical"]:
                health_score -= 25
                issues.append(f"{component}: Critical error rate")
            elif metric.error_rate >= self.performance_thresholds["error_rate"]["warning"]:
                health_score -= 12
                issues.append(f"{component}: High error rate")
        
        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "degraded"
        else:
            status = "critical"
        
        return {
            "status": status,
            "score": max(0, health_score),
            "issues": issues
        }
    
    def get_bottleneck_recommendations(self) -> Dict[str, List[str]]:
        """
        Get recommendations for addressing bottlenecks.
        
        Returns:
            Dictionary of recommendations by component
        """
        recommendations = defaultdict(list)
        
        for bottleneck in self.bottlenecks:
            recommendations[bottleneck.component].extend(bottleneck.recommendations)
        
        # Remove duplicates
        for component in recommendations:
            recommendations[component] = list(set(recommendations[component]))
        
        return dict(recommendations)
    
    def get_performance_trends(self, component: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trends for a component.
        
        Args:
            component: Component to analyze
            hours: Number of hours to analyze
            
        Returns:
            Performance trends dictionary
        """
        if component not in self.component_metrics:
            return {"error": f"Component {component} not found"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            metric for metric in self.component_metrics[component]
            if metric.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": f"No recent metrics for {component}"}
        
        # Calculate trends
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
        response_trend = self._calculate_trend([m.response_time for m in recent_metrics])
        throughput_trend = self._calculate_trend([m.throughput for m in recent_metrics])
        error_trend = self._calculate_trend([m.error_rate for m in recent_metrics])
        
        return {
            "component": component,
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "trends": {
                "cpu_usage": cpu_trend,
                "memory_usage": memory_trend,
                "response_time": response_trend,
                "throughput": throughput_trend,
                "error_rate": error_trend
            },
            "averages": {
                "cpu_usage": statistics.mean([m.cpu_usage for m in recent_metrics]),
                "memory_usage": statistics.mean([m.memory_usage for m in recent_metrics]),
                "response_time": statistics.mean([m.response_time for m in recent_metrics]),
                "throughput": statistics.mean([m.throughput for m in recent_metrics]),
                "error_rate": statistics.mean([m.error_rate for m in recent_metrics])
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    async def run_optimization_cycle(self) -> List[OptimizationResult]:
        """
        Run a complete optimization cycle.
        
        Returns:
            List of optimization results
        """
        logger.info("Starting optimization cycle")
        
        results = []
        
        # Get current bottlenecks
        critical_bottlenecks = [
            b for b in self.bottlenecks
            if b.severity == "critical"
        ]
        
        # Optimize critical bottlenecks
        for bottleneck in critical_bottlenecks:
            result = await self.optimize_component(
                bottleneck.component,
                bottleneck.bottleneck_type
            )
            results.append(result)
        
        logger.info(f"Optimization cycle completed: {len(results)} optimizations applied")
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on performance optimizer.
        
        Returns:
            Health status dictionary
        """
        summary = self.get_performance_summary()
        
        health_status = {
            "status": summary["system_health"]["status"],
            "issues": summary["system_health"]["issues"],
            "details": {
                "monitoring_active": self.monitoring_active,
                "components_monitored": len(self.component_metrics),
                "bottlenecks_detected": len(self.bottlenecks),
                "optimizations_applied": len(self.optimization_history)
            }
        }
        
        return health_status
