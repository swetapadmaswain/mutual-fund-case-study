"""
Monitoring and Analytics System for Phase 2.6

Provides comprehensive monitoring, analytics, and reporting capabilities for system performance and usage.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System-level metrics."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    uptime: float
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """Application-level metrics."""
    timestamp: datetime
    requests_per_second: float
    average_response_time: float
    error_rate: float
    active_users: int
    cache_hit_rate: float
    database_connections: float
    queue_length: int
    component_health: Dict[str, bool]

@dataclass
class BusinessMetrics:
    """Business-level metrics."""
    timestamp: datetime
    total_queries: int
    successful_queries: int
    unique_users: int
    popular_queries: List[Dict[str, Any]]
    response_quality_score: float
    user_satisfaction: float
    system_utilization: float

@dataclass
class Alert:
    """System alert."""
    id: str
    severity: str  # "info", "warning", "error", "critical"
    component: str
    message: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class AnalyticsReport:
    """Analytics report."""
    report_type: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime

class MonitoringAnalytics:
    """
    Comprehensive monitoring and analytics system.
    
    Features:
    - Real-time system monitoring
    - Application performance tracking
    - Business metrics collection
    - Alert management
    - Analytics reporting
    - Trend analysis
    """
    
    def __init__(self, cache_dir: str = "cache/monitoring_analytics"):
        """
        Initialize monitoring and analytics system.
        
        Args:
            cache_dir: Directory for caching monitoring data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.system_metrics: deque = deque(maxlen=1000)
        self.application_metrics: deque = deque(maxlen=1000)
        self.business_metrics: deque = deque(maxlen=1000)
        
        # Alert management
        self.alerts: List[Alert] = []
        self.alert_rules = self._initialize_alert_rules()
        self.alert_handlers = self._initialize_alert_handlers()
        
        # Configuration
        self.monitoring_interval = 30.0  # seconds
        self.data_retention_days = 30
        self.report_generation_interval = 3600.0  # 1 hour
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.analytics_thread = None
        
        # Analytics storage
        self.analytics_reports: List[AnalyticsReport] = []
        
        # Load existing data
        self._load_metrics()
        self._load_alerts()
        self._load_reports()
        
        logger.info("Monitoring and Analytics system initialized")
    
    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert rules."""
        return {
            "high_cpu": {
                "condition": "cpu_usage > 80",
                "severity": "warning",
                "message": "High CPU usage detected: {cpu_usage:.1f}%"
            },
            "critical_cpu": {
                "condition": "cpu_usage > 95",
                "severity": "critical",
                "message": "Critical CPU usage: {cpu_usage:.1f}%"
            },
            "high_memory": {
                "condition": "memory_usage > 85",
                "severity": "warning",
                "message": "High memory usage: {memory_usage:.1f}%"
            },
            "critical_memory": {
                "condition": "memory_usage > 95",
                "severity": "critical",
                "message": "Critical memory usage: {memory_usage:.1f}%"
            },
            "high_response_time": {
                "condition": "average_response_time > 3.0",
                "severity": "warning",
                "message": "High response time: {average_response_time:.2f}s"
            },
            "critical_response_time": {
                "condition": "average_response_time > 5.0",
                "severity": "critical",
                "message": "Critical response time: {average_response_time:.2f}s"
            },
            "high_error_rate": {
                "condition": "error_rate > 5.0",
                "severity": "warning",
                "message": "High error rate: {error_rate:.1f}%"
            },
            "critical_error_rate": {
                "condition": "error_rate > 10.0",
                "severity": "critical",
                "message": "Critical error rate: {error_rate:.1f}%"
            },
            "low_cache_hit_rate": {
                "condition": "cache_hit_rate < 70",
                "severity": "warning",
                "message": "Low cache hit rate: {cache_hit_rate:.1f}%"
            },
            "component_down": {
                "condition": "component_health contains false",
                "severity": "error",
                "message": "Component {component} is down"
            }
        }
    
    def _initialize_alert_handlers(self) -> Dict[str, callable]:
        """Initialize alert handlers."""
        return {
            "info": self._handle_info_alert,
            "warning": self._handle_warning_alert,
            "error": self._handle_error_alert,
            "critical": self._handle_critical_alert
        }
    
    def _load_metrics(self) -> None:
        """Load metrics from cache."""
        metrics_file = self.cache_dir / "metrics.json"
        
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                
                # Load system metrics
                for metric_data in data.get("system_metrics", []):
                    metric_data['timestamp'] = datetime.fromisoformat(metric_data['timestamp'])
                    self.system_metrics.append(SystemMetrics(**metric_data))
                
                # Load application metrics
                for metric_data in data.get("application_metrics", []):
                    metric_data['timestamp'] = datetime.fromisoformat(metric_data['timestamp'])
                    self.application_metrics.append(ApplicationMetrics(**metric_data))
                
                # Load business metrics
                for metric_data in data.get("business_metrics", []):
                    metric_data['timestamp'] = datetime.fromisoformat(metric_data['timestamp'])
                    self.business_metrics.append(BusinessMetrics(**metric_data))
                
                logger.info(f"Loaded metrics from cache")
                
            except Exception as e:
                logger.error(f"Error loading metrics: {e}")
    
    def _load_alerts(self) -> None:
        """Load alerts from cache."""
        alerts_file = self.cache_dir / "alerts.json"
        
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    data = json.load(f)
                
                self.alerts = []
                for alert_data in data:
                    alert_data['timestamp'] = datetime.fromisoformat(alert_data['timestamp'])
                    if alert_data.get('resolved_at'):
                        alert_data['resolved_at'] = datetime.fromisoformat(alert_data['resolved_at'])
                    self.alerts.append(Alert(**alert_data))
                
                logger.info(f"Loaded {len(self.alerts)} alerts")
                
            except Exception as e:
                logger.error(f"Error loading alerts: {e}")
    
    def _load_reports(self) -> None:
        """Load analytics reports from cache."""
        reports_file = self.cache_dir / "reports.json"
        
        if reports_file.exists():
            try:
                with open(reports_file, 'r') as f:
                    data = json.load(f)
                
                self.analytics_reports = []
                for report_data in data:
                    report_data['period_start'] = datetime.fromisoformat(report_data['period_start'])
                    report_data['period_end'] = datetime.fromisoformat(report_data['period_end'])
                    report_data['generated_at'] = datetime.fromisoformat(report_data['generated_at'])
                    self.analytics_reports.append(AnalyticsReport(**report_data))
                
                logger.info(f"Loaded {len(self.analytics_reports)} reports")
                
            except Exception as e:
                logger.error(f"Error loading reports: {e}")
    
    def _save_metrics(self) -> None:
        """Save metrics to cache."""
        try:
            metrics_file = self.cache_dir / "metrics.json"
            
            data = {
                "system_metrics": [
                    asdict(metric) for metric in self.system_metrics
                ],
                "application_metrics": [
                    asdict(metric) for metric in self.application_metrics
                ],
                "business_metrics": [
                    asdict(metric) for metric in self.business_metrics
                ]
            }
            
            # Convert datetime objects to strings
            for category in data:
                for metric in data[category]:
                    metric['timestamp'] = metric['timestamp'].isoformat()
            
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _save_alerts(self) -> None:
        """Save alerts to cache."""
        try:
            alerts_file = self.cache_dir / "alerts.json"
            
            serializable_alerts = []
            for alert in self.alerts:
                alert_dict = asdict(alert)
                alert_dict['timestamp'] = alert.timestamp.isoformat()
                if alert.resolved_at:
                    alert_dict['resolved_at'] = alert.resolved_at.isoformat()
                serializable_alerts.append(alert_dict)
            
            with open(alerts_file, 'w') as f:
                json.dump(serializable_alerts, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
    
    def _save_reports(self) -> None:
        """Save analytics reports to cache."""
        try:
            reports_file = self.cache_dir / "reports.json"
            
            serializable_reports = []
            for report in self.analytics_reports:
                report_dict = asdict(report)
                report_dict['period_start'] = report.period_start.isoformat()
                report_dict['period_end'] = report.period_end.isoformat()
                report_dict['generated_at'] = report.generated_at.isoformat()
                serializable_reports.append(report_dict)
            
            with open(reports_file, 'w') as f:
                json.dump(serializable_reports, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving reports: {e}")
    
    def start_monitoring(self) -> None:
        """Start monitoring in background."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
        
        self.monitoring_thread.start()
        self.analytics_thread.start()
        
        logger.info("Monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        if self.analytics_thread:
            self.analytics_thread.join(timeout=10)
        
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                system_metrics = self._collect_system_metrics()
                application_metrics = self._collect_application_metrics()
                business_metrics = self._collect_business_metrics()
                
                # Store metrics
                self.system_metrics.append(system_metrics)
                self.application_metrics.append(application_metrics)
                self.business_metrics.append(business_metrics)
                
                # Check for alerts
                self._check_alerts(system_metrics, application_metrics, business_metrics)
                
                # Save metrics periodically
                if len(self.system_metrics) % 10 == 0:
                    self._save_metrics()
                    self._save_alerts()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _analytics_loop(self) -> None:
        """Background analytics loop."""
        while self.monitoring_active:
            try:
                # Generate periodic reports
                await asyncio.sleep(self.report_generation_interval)
                
                if self.monitoring_active:
                    await self._generate_periodic_reports()
                
            except Exception as e:
                logger.error(f"Error in analytics loop: {e}")
                await asyncio.sleep(self.report_generation_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics."""
        try:
            import psutil
            
            # CPU metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            load_average = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Connections
            connections = len(psutil.net_connections())
            
            # Uptime (simplified)
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                uptime=uptime,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                active_connections=0,
                uptime=0.0,
                load_average=[0.0, 0.0, 0.0]
            )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-level metrics."""
        # Simulated application metrics
        # In a real implementation, these would come from actual application monitoring
        
        return ApplicationMetrics(
            timestamp=datetime.now(),
            requests_per_second=25.5,
            average_response_time=0.8,
            error_rate=2.1,
            active_users=150,
            cache_hit_rate=87.3,
            database_connections=12.0,
            queue_length=8,
            component_health={
                "query_processor": True,
                "search_engine": True,
                "llm_service": True,
                "citation_system": True,
                "source_manager": True
            }
        )
    
    def _collect_business_metrics(self) -> BusinessMetrics:
        """Collect business-level metrics."""
        # Simulated business metrics
        # In a real implementation, these would come from actual business intelligence
        
        return BusinessMetrics(
            timestamp=datetime.now(),
            total_queries=1250,
            successful_queries=1225,
            unique_users=75,
            popular_queries=[
                {"query": "What is the expense ratio?", "count": 45},
                {"query": "What is the minimum SIP amount?", "count": 38},
                {"query": "What are the historical returns?", "count": 32}
            ],
            response_quality_score=4.2,
            user_satisfaction=4.5,
            system_utilization=65.8
        )
    
    def _check_alerts(self, system_metrics: SystemMetrics, application_metrics: ApplicationMetrics, 
                     business_metrics: BusinessMetrics) -> None:
        """Check for alert conditions."""
        # Combine metrics for evaluation
        metrics_context = {
            "cpu_usage": system_metrics.cpu_usage,
            "memory_usage": system_metrics.memory_usage,
            "disk_usage": system_metrics.disk_usage,
            "average_response_time": application_metrics.average_response_time,
            "error_rate": application_metrics.error_rate,
            "cache_hit_rate": application_metrics.cache_hit_rate,
            "component_health": application_metrics.component_health
        }
        
        # Check each alert rule
        for rule_name, rule in self.alert_rules.items():
            if self._evaluate_alert_condition(rule["condition"], metrics_context):
                # Create alert
                alert = Alert(
                    id=f"alert_{int(time.time())}_{rule_name}",
                    severity=rule["severity"],
                    component=self._get_component_from_rule(rule_name),
                    message=rule["message"].format(**metrics_context),
                    timestamp=datetime.now(),
                    resolved=False,
                    resolved_at=None,
                    metadata={"rule": rule_name, "metrics": metrics_context}
                )
                
                # Check if similar alert already exists
                if not self._is_duplicate_alert(alert):
                    self.alerts.append(alert)
                    logger.warning(f"Alert triggered: {alert.message}")
                    
                    # Handle alert
                    handler = self.alert_handlers.get(rule["severity"])
                    if handler:
                        handler(alert)
    
    def _evaluate_alert_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate alert condition."""
        try:
            # Simple condition evaluation
            # In a real implementation, this would use a more sophisticated expression parser
            
            if "cpu_usage >" in condition:
                threshold = float(condition.split(">")[1].strip())
                return context["cpu_usage"] > threshold
            elif "memory_usage >" in condition:
                threshold = float(condition.split(">")[1].strip())
                return context["memory_usage"] > threshold
            elif "average_response_time >" in condition:
                threshold = float(condition.split(">")[1].strip())
                return context["average_response_time"] > threshold
            elif "error_rate >" in condition:
                threshold = float(condition.split(">")[1].strip())
                return context["error_rate"] > threshold
            elif "cache_hit_rate <" in condition:
                threshold = float(condition.split("<")[1].strip())
                return context["cache_hit_rate"] < threshold
            elif "component_health contains false" in condition:
                return not all(context["component_health"].values())
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    def _get_component_from_rule(self, rule_name: str) -> str:
        """Get component name from alert rule."""
        if "cpu" in rule_name or "memory" in rule_name:
            return "system"
        elif "response_time" in rule_name or "error_rate" in rule_name or "cache" in rule_name:
            return "application"
        elif "component" in rule_name:
            return "components"
        else:
            return "unknown"
    
    def _is_duplicate_alert(self, new_alert: Alert) -> bool:
        """Check if alert is a duplicate of existing one."""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for existing in self.alerts:
            if (not existing.resolved and
                existing.severity == new_alert.severity and
                existing.component == new_alert.component and
                existing.timestamp > cutoff_time):
                return True
        
        return False
    
    def _handle_info_alert(self, alert: Alert) -> None:
        """Handle info-level alert."""
        logger.info(f"INFO: {alert.message}")
    
    def _handle_warning_alert(self, alert: Alert) -> None:
        """Handle warning-level alert."""
        logger.warning(f"WARNING: {alert.message}")
        # Could send email, Slack notification, etc.
    
    def _handle_error_alert(self, alert: Alert) -> None:
        """Handle error-level alert."""
        logger.error(f"ERROR: {alert.message}")
        # Could trigger pager duty, create incident, etc.
    
    def _handle_critical_alert(self, alert: Alert) -> None:
        """Handle critical-level alert."""
        logger.critical(f"CRITICAL: {alert.message}")
        # Could trigger emergency response, etc.
    
    async def _generate_periodic_reports(self) -> None:
        """Generate periodic analytics reports."""
        now = datetime.now()
        
        # Hourly report
        period_start = now - timedelta(hours=1)
        hourly_report = await self._generate_report("hourly", period_start, now)
        
        # Daily report (at start of day)
        if now.hour == 0:
            period_start = now - timedelta(days=1)
            daily_report = await self._generate_report("daily", period_start, now)
    
    async def _generate_report(self, report_type: str, period_start: datetime, 
                               period_end: datetime) -> AnalyticsReport:
        """Generate analytics report."""
        logger.info(f"Generating {report_type} report for {period_start} to {period_end}")
        
        # Collect metrics for the period
        period_metrics = self._get_period_metrics(period_start, period_end)
        
        # Generate insights
        insights = self._generate_insights(period_metrics, report_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(period_metrics, insights)
        
        # Create report
        report = AnalyticsReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            metrics=period_metrics,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        # Store report
        self.analytics_reports.append(report)
        self._save_reports()
        
        return report
    
    def _get_period_metrics(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Get metrics for a specific period."""
        # Filter metrics by period
        period_system = [
            m for m in self.system_metrics 
            if period_start <= m.timestamp <= period_end
        ]
        period_application = [
            m for m in self.application_metrics 
            if period_start <= m.timestamp <= period_end
        ]
        period_business = [
            m for m in self.business_metrics 
            if period_start <= m.timestamp <= period_end
        ]
        
        # Calculate aggregates
        metrics = {}
        
        if period_system:
            metrics["system"] = {
                "avg_cpu_usage": statistics.mean([m.cpu_usage for m in period_system]),
                "max_cpu_usage": max([m.cpu_usage for m in period_system]),
                "avg_memory_usage": statistics.mean([m.memory_usage for m in period_system]),
                "max_memory_usage": max([m.memory_usage for m in period_system]),
                "avg_active_connections": statistics.mean([m.active_connections for m in period_system])
            }
        
        if period_application:
            metrics["application"] = {
                "avg_requests_per_second": statistics.mean([m.requests_per_second for m in period_application]),
                "avg_response_time": statistics.mean([m.average_response_time for m in period_application]),
                "max_response_time": max([m.average_response_time for m in period_application]),
                "avg_error_rate": statistics.mean([m.error_rate for m in period_application]),
                "avg_cache_hit_rate": statistics.mean([m.cache_hit_rate for m in period_application]),
                "avg_active_users": statistics.mean([m.active_users for m in period_application])
            }
        
        if period_business:
            total_queries = sum([m.total_queries for m in period_business])
            successful_queries = sum([m.successful_queries for m in period_business])
            
            metrics["business"] = {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "avg_unique_users": statistics.mean([m.unique_users for m in period_business]),
                "avg_response_quality": statistics.mean([m.response_quality_score for m in period_business]),
                "avg_user_satisfaction": statistics.mean([m.user_satisfaction for m in period_business])
            }
        
        return metrics
    
    def _generate_insights(self, metrics: Dict[str, Any], report_type: str) -> List[str]:
        """Generate insights from metrics."""
        insights = []
        
        # System insights
        if "system" in metrics:
            sys_metrics = metrics["system"]
            if sys_metrics["avg_cpu_usage"] > 70:
                insights.append("High average CPU usage detected")
            if sys_metrics["avg_memory_usage"] > 80:
                insights.append("High average memory usage detected")
            if sys_metrics["avg_active_connections"] > 100:
                insights.append("High number of active connections")
        
        # Application insights
        if "application" in metrics:
            app_metrics = metrics["application"]
            if app_metrics["avg_response_time"] > 2.0:
                insights.append("Response times are above target")
            if app_metrics["avg_error_rate"] > 5.0:
                insights.append("Error rate is above acceptable threshold")
            if app_metrics["avg_cache_hit_rate"] < 80:
                insights.append("Cache hit rate could be improved")
        
        # Business insights
        if "business" in metrics:
            biz_metrics = metrics["business"]
            if biz_metrics["success_rate"] < 95:
                insights.append("Query success rate is below target")
            if biz_metrics["avg_response_quality"] < 4.0:
                insights.append("Response quality scores are declining")
            if biz_metrics["avg_user_satisfaction"] < 4.0:
                insights.append("User satisfaction needs improvement")
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict[str, Any], insights: List[str]) -> List[str]:
        """Generate recommendations based on metrics and insights."""
        recommendations = []
        
        for insight in insights:
            if "CPU usage" in insight:
                recommendations.append("Consider scaling up CPU resources or optimizing CPU-intensive operations")
            elif "memory usage" in insight:
                recommendations.append("Consider increasing memory allocation or optimizing memory usage")
            elif "Response times" in insight:
                recommendations.append("Optimize database queries and implement caching strategies")
            elif "Error rate" in insight:
                recommendations.append("Investigate root causes of errors and implement better error handling")
            elif "Cache hit rate" in insight:
                recommendations.append("Review caching strategy and increase cache size or optimize cache keys")
            elif "success rate" in insight:
                recommendations.append("Improve query processing and response generation accuracy")
            elif "Response quality" in insight:
                recommendations.append("Enhance LLM prompts and improve context relevance")
            elif "User satisfaction" in insight:
                recommendations.append("Gather user feedback and improve response quality and speed")
        
        return recommendations
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for monitoring dashboard.
        
        Returns:
            Dashboard data dictionary
        """
        # Get latest metrics
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        latest_application = self.application_metrics[-1] if self.application_metrics else None
        latest_business = self.business_metrics[-1] if self.business_metrics else None
        
        # Get recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if not alert.resolved and (datetime.now() - alert.timestamp) < timedelta(hours=24)
        ]
        
        # Get metrics trends (last hour)
        hour_ago = datetime.now() - timedelta(hours=1)
        
        recent_system = [m for m in self.system_metrics if m.timestamp > hour_ago]
        recent_application = [m for m in self.application_metrics if m.timestamp > hour_ago]
        
        # Calculate trends
        cpu_trend = self._calculate_metric_trend([m.cpu_usage for m in recent_system]) if recent_system else "stable"
        memory_trend = self._calculate_metric_trend([m.memory_usage for m in recent_system]) if recent_system else "stable"
        response_trend = self._calculate_metric_trend([m.average_response_time for m in recent_application]) if recent_application else "stable"
        
        return {
            "current_metrics": {
                "system": asdict(latest_system) if latest_system else None,
                "application": asdict(latest_application) if latest_application else None,
                "business": asdict(latest_business) if latest_business else None
            },
            "recent_alerts": [asdict(alert) for alert in recent_alerts[:10]],
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "response_time": response_trend
            },
            "alert_summary": {
                "total_alerts": len(self.alerts),
                "active_alerts": len(recent_alerts),
                "critical_alerts": len([a for a in recent_alerts if a.severity == "critical"])
            },
            "system_health": self._calculate_system_health(latest_system, latest_application)
        }
    
    def _calculate_metric_trend(self, values: List[float]) -> str:
        """Calculate metric trend direction."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        recent_avg = statistics.mean(values[-5:]) if len(values) >= 5 else statistics.mean(values)
        older_avg = statistics.mean(values[:5]) if len(values) >= 10 else statistics.mean(values[:len(values)//2])
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_system_health(self, system_metrics: Optional[SystemMetrics], 
                                application_metrics: Optional[ApplicationMetrics]) -> Dict[str, Any]:
        """Calculate overall system health."""
        health_score = 100
        issues = []
        
        if system_metrics:
            if system_metrics.cpu_usage > 80:
                health_score -= 20
                issues.append("High CPU usage")
            if system_metrics.memory_usage > 85:
                health_score -= 20
                issues.append("High memory usage")
        
        if application_metrics:
            if application_metrics.average_response_time > 3.0:
                health_score -= 15
                issues.append("High response time")
            if application_metrics.error_rate > 5.0:
                health_score -= 25
                issues.append("High error rate")
            if application_metrics.cache_hit_rate < 70:
                health_score -= 10
                issues.append("Low cache hit rate")
        
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
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get analytics summary for specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter metrics
        period_system = [m for m in self.system_metrics if m.timestamp > cutoff_date]
        period_application = [m for m in self.application_metrics if m.timestamp > cutoff_date]
        period_business = [m for m in self.business_metrics if m.timestamp > cutoff_date]
        
        # Filter alerts
        period_alerts = [a for a in self.alerts if a.timestamp > cutoff_date]
        
        # Calculate summary
        summary = {
            "period_days": days,
            "metrics_summary": {
                "system_metrics_count": len(period_system),
                "application_metrics_count": len(period_application),
                "business_metrics_count": len(period_business)
            },
            "alerts_summary": {
                "total_alerts": len(period_alerts),
                "critical_alerts": len([a for a in period_alerts if a.severity == "critical"]),
                "error_alerts": len([a for a in period_alerts if a.severity == "error"]),
                "warning_alerts": len([a for a in period_alerts if a.severity == "warning"])
            },
            "performance_summary": {}
        }
        
        # Performance summary
        if period_application:
            summary["performance_summary"] = {
                "avg_response_time": statistics.mean([m.average_response_time for m in period_application]),
                "max_response_time": max([m.average_response_time for m in period_application]),
                "avg_error_rate": statistics.mean([m.error_rate for m in period_application]),
                "avg_cache_hit_rate": statistics.mean([m.cache_hit_rate for m in period_application]),
                "total_requests": int(sum([m.requests_per_second * self.monitoring_interval for m in period_application]))
            }
        
        if period_business:
            total_queries = sum([m.total_queries for m in period_business])
            successful_queries = sum([m.successful_queries for m in period_business])
            
            summary["business_summary"] = {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "avg_unique_users": statistics.mean([m.unique_users for m in period_business])
            }
        
        return summary
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old monitoring data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old metrics
        old_system = len([m for m in self.system_metrics if m.timestamp < cutoff_date])
        old_application = len([m for m in self.application_metrics if m.timestamp < cutoff_date])
        old_business = len([m for m in self.business_metrics if m.timestamp < cutoff_date])
        
        self.system_metrics = deque(
            [m for m in self.system_metrics if m.timestamp >= cutoff_date],
            maxlen=self.system_metrics.maxlen
        )
        self.application_metrics = deque(
            [m for m in self.application_metrics if m.timestamp >= cutoff_date],
            maxlen=self.application_metrics.maxlen
        )
        self.business_metrics = deque(
            [m for m in self.business_metrics if m.timestamp >= cutoff_date],
            maxlen=self.business_metrics.maxlen
        )
        
        # Clean up old alerts
        old_alerts = len([a for a in self.alerts if a.timestamp < cutoff_date and a.resolved])
        self.alerts = [
            a for a in self.alerts
            if a.timestamp >= cutoff_date or not a.resolved
        ]
        
        # Clean up old reports
        old_reports = len([r for r in self.analytics_reports if r.generated_at < cutoff_date])
        self.analytics_reports = [
            r for r in self.analytics_reports
            if r.generated_at >= cutoff_date
        ]
        
        # Save cleaned data
        self._save_metrics()
        self._save_alerts()
        self._save_reports()
        
        total_cleaned = old_system + old_application + old_business + old_alerts + old_reports
        logger.info(f"Cleaned up {total_cleaned} old monitoring items")
        
        return total_cleaned
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on monitoring system.
        
        Returns:
            Health status dictionary
        """
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        latest_application = self.application_metrics[-1] if self.application_metrics else None
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "monitoring_active": self.monitoring_active,
                "metrics_collected": len(self.system_metrics) + len(self.application_metrics) + len(self.business_metrics),
                "alerts_active": len([a for a in self.alerts if not a.resolved]),
                "reports_generated": len(self.analytics_reports),
                "last_metrics": (latest_system.timestamp if latest_system else None)
            }
        }
        
        # Check if monitoring is active
        if not self.monitoring_active:
            health_status["status"] = "degraded"
            health_status["issues"].append("Monitoring is not active")
        
        # Check if metrics are recent
        if latest_system and (datetime.now() - latest_system.timestamp) > timedelta(minutes=5):
            health_status["status"] = "degraded"
            health_status["issues"].append("Metrics are stale")
        
        # Check for critical alerts
        critical_alerts = [a for a in self.alerts if a.severity == "critical" and not a.resolved]
        if critical_alerts:
            health_status["status"] = "critical"
            health_status["issues"].append(f"{len(critical_alerts)} critical alerts active")
        
        return health_status
