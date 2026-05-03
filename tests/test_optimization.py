"""
Comprehensive tests for Phase 2.6: Performance Optimization and Testing
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime, timedelta
import statistics

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rag.optimization.performance_optimizer import PerformanceOptimizer, PerformanceMetrics, Bottleneck
from src.rag.optimization.testing_framework import TestingFramework, TestResult, TestSuite
from src.rag.optimization.monitoring_analytics import MonitoringAnalytics, SystemMetrics, ApplicationMetrics
from src.rag.optimization.caching_optimizer import CachingOptimizer, CacheEntry, CacheConfig
from src.rag.optimization.load_testing import LoadTesting, LoadTestScenario, LoadTestResult
from src.rag.optimization.main import Phase26Pipeline, Phase26Results


class TestPerformanceOptimizer:
    """Test Performance Optimizer functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Create performance optimizer instance for testing."""
        return PerformanceOptimizer(cache_dir="test_cache/performance_optimizer")
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.cache_dir.exists()
        assert optimizer.monitoring_interval == 5.0
        assert optimizer.performance_thresholds is not None
        assert optimizer.optimization_strategies is not None
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, optimizer):
        """Test system metrics collection."""
        metrics = optimizer._collect_system_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert isinstance(metrics.timestamp, datetime)
        assert isinstance(metrics.cpu_usage, (int, float))
        assert isinstance(metrics.memory_usage, (int, float))
        assert isinstance(metrics.disk_usage, (int, float))
        assert isinstance(metrics.active_connections, int)
    
    @pytest.mark.asyncio
    async def test_detect_bottlenecks(self, optimizer):
        """Test bottleneck detection."""
        # Create test metrics with high CPU usage
        high_cpu_metrics = PerformanceMetrics(
            component_name="test_component",
            timestamp=datetime.now(),
            cpu_usage=95.0,
            memory_usage=70.0,
            response_time=1.0,
            throughput=100.0,
            error_rate=2.0,
            cache_hit_rate=85.0,
            queue_length=10,
            active_connections=5,
            metadata={}
        )
        
        metrics = {"test_component": high_cpu_metrics}
        optimizer._detect_bottlenecks(metrics)
        
        # Should detect critical CPU bottleneck
        critical_bottlenecks = [b for b in optimizer.bottlenecks if b.severity == "critical"]
        assert len(critical_bottlenecks) > 0
        assert critical_bottlenecks[0].bottleneck_type == "cpu"
    
    @pytest.mark.asyncio
    async def test_optimize_component(self, optimizer):
        """Test component optimization."""
        result = await optimizer.optimize_component("test_component", "cpu")
        
        assert isinstance(result, type(optimizer.optimization_history[0]))
        assert result.component == "test_component"
        assert result.optimization_type == "cpu"
    
    def test_get_performance_summary(self, optimizer):
        """Test performance summary retrieval."""
        # Add some test metrics
        optimizer.component_metrics["test"] = [
            PerformanceMetrics(
                component_name="test",
                timestamp=datetime.now(),
                cpu_usage=50.0,
                memory_usage=60.0,
                response_time=1.0,
                throughput=100.0,
                error_rate=2.0,
                cache_hit_rate=85.0,
                queue_length=10,
                active_connections=5,
                metadata={}
            )
        ]
        
        summary = optimizer.get_performance_summary()
        
        assert "current_metrics" in summary
        assert "bottleneck_summary" in summary
        assert "system_health" in summary
        assert summary["system_health"]["status"] in ["healthy", "degraded", "critical"]
    
    def test_get_performance_trends(self, optimizer):
        """Test performance trend analysis."""
        # Add test metrics over time
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(10):
            metric = PerformanceMetrics(
                component_name="test",
                timestamp=base_time + timedelta(minutes=i * 12),
                cpu_usage=50.0 + i * 2,
                memory_usage=60.0,
                response_time=1.0,
                throughput=100.0,
                error_rate=2.0,
                cache_hit_rate=85.0,
                queue_length=10,
                active_connections=5,
                metadata={}
            )
            optimizer.component_metrics["test"].append(metric)
        
        trends = optimizer.get_performance_trends("test", hours=2)
        
        assert "component" in trends
        assert "trends" in trends
        assert "averages" in trends
        assert trends["component"] == "test"
        assert trends["trends"]["cpu_usage"] in ["increasing", "decreasing", "stable"]


class TestTestingFramework:
    """Test Testing Framework functionality."""
    
    @pytest.fixture
    def framework(self):
        """Create testing framework instance for testing."""
        return TestingFramework(cache_dir="test_cache/testing_framework")
    
    def test_framework_initialization(self, framework):
        """Test framework initialization."""
        assert framework.cache_dir.exists()
        assert framework.test_timeout == 300
        assert framework.parallel_execution is True
        assert framework.max_workers == 4
        assert framework.coverage_threshold == 80.0
    
    def test_register_test_suite(self, framework):
        """Test test suite registration."""
        framework.register_test_suite(
            name="test_suite",
            description="Test suite for testing",
            tests=["test_1", "test_2"],
            tags=["unit", "integration"]
        )
        
        assert "test_suite" in framework.test_suites
        suite = framework.test_suites["test_suite"]
        assert suite.name == "test_suite"
        assert len(suite.tests) == 2
        assert "unit" in suite.tags
    
    def test_register_unit_test(self, framework):
        """Test unit test registration."""
        def test_function():
            return {"status": "passed", "assertions": 1}
        
        framework.register_unit_test("test_unit", test_function)
        
        assert "test_unit" in framework.unit_tests
        assert framework.unit_tests["test_unit"] == test_function
    
    @pytest.mark.asyncio
    async def test_run_unit_tests(self, framework):
        """Test unit test execution."""
        # Register a test function
        def test_function():
            return {"status": "passed", "assertions": 1, "coverage": 85.0}
        
        framework.register_unit_test("test_unit", test_function)
        
        # Run tests
        report = await framework.run_unit_tests()
        
        assert isinstance(report, type(framework.test_reports[0]))
        assert report.total_tests >= 1
        assert report.passed_tests >= 0
        assert report.coverage_percentage >= 0.0
    
    @pytest.mark.asyncio
    async def test_run_integration_tests(self, framework):
        """Test integration test execution."""
        # Register an integration test function
        def test_function():
            return {"status": "passed", "assertions": 2, "coverage": 90.0}
        
        framework.register_integration_test("test_integration", test_function)
        
        # Run tests
        report = await framework.run_integration_tests()
        
        assert isinstance(report, type(framework.test_reports[0]))
        assert report.total_tests >= 0
        assert report.passed_tests >= 0
    
    def test_get_test_summary(self, framework):
        """Test test summary retrieval."""
        # Add some test results
        framework.test_results = [
            TestResult(
                test_name="test_1",
                test_type="unit",
                status="passed",
                execution_time=0.5,
                error_message=None,
                assertions=5,
                coverage=85.0,
                timestamp=datetime.now(),
                metadata={}
            ),
            TestResult(
                test_name="test_2",
                test_type="unit",
                status="failed",
                execution_time=1.0,
                error_message="Test failed",
                assertions=3,
                coverage=75.0,
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        
        summary = framework.get_test_summary()
        
        assert "overall" in summary
        assert "by_type" in summary
        assert summary["overall"]["total_tests"] == 2
        assert summary["overall"]["passed_tests"] == 1
        assert summary["overall"]["failed_tests"] == 1
        assert summary["overall"]["success_rate"] == 50.0
    
    def test_generate_test_report(self, framework):
        """Test test report generation."""
        # Add test results
        framework.test_results = [
            TestResult(
                test_name="test_1",
                test_type="unit",
                status="passed",
                execution_time=0.5,
                error_message=None,
                assertions=5,
                coverage=85.0,
                timestamp=datetime.now(),
                metadata={}
            )
        ]
        
        # Generate JSON report
        json_report = framework.generate_test_report("json")
        assert isinstance(json_report, str)
        
        # Generate markdown report
        markdown_report = framework.generate_test_report("markdown")
        assert isinstance(markdown_report, str)
        assert "# Test Report" in markdown_report
        
        # Generate HTML report
        html_report = framework.generate_test_report("html")
        assert isinstance(html_report, str)
        assert "<html>" in html_report


class TestMonitoringAnalytics:
    """Test Monitoring and Analytics functionality."""
    
    @pytest.fixture
    def monitoring(self):
        """Create monitoring analytics instance for testing."""
        return MonitoringAnalytics(cache_dir="test_cache/monitoring_analytics")
    
    def test_monitoring_initialization(self, monitoring):
        """Test monitoring initialization."""
        assert monitoring.cache_dir.exists()
        assert monitoring.monitoring_interval == 30.0
        assert monitoring.alert_rules is not None
        assert monitoring.alert_handlers is not None
    
    def test_collect_system_metrics(self, monitoring):
        """Test system metrics collection."""
        metrics = monitoring._collect_system_metrics()
        
        assert isinstance(metrics, SystemMetrics)
        assert isinstance(metrics.timestamp, datetime)
        assert isinstance(metrics.cpu_usage, (int, float))
        assert isinstance(metrics.memory_usage, (int, float))
        assert isinstance(metrics.disk_usage, (int, float))
        assert isinstance(metrics.active_connections, int)
    
    def test_collect_application_metrics(self, monitoring):
        """Test application metrics collection."""
        metrics = monitoring._collect_application_metrics()
        
        assert isinstance(metrics, ApplicationMetrics)
        assert isinstance(metrics.timestamp, datetime)
        assert isinstance(metrics.requests_per_second, (int, float))
        assert isinstance(metrics.average_response_time, (int, float))
        assert isinstance(metrics.error_rate, (int, float))
        assert isinstance(metrics.active_users, int)
    
    def test_collect_business_metrics(self, monitoring):
        """Test business metrics collection."""
        metrics = monitoring._collect_business_metrics()
        
        assert isinstance(metrics.timestamp, datetime)
        assert isinstance(metrics.total_queries, int)
        assert isinstance(metrics.successful_queries, int)
        assert isinstance(metrics.unique_users, int)
        assert isinstance(metrics.popular_queries, list)
        assert isinstance(metrics.response_quality_score, (int, float))
    
    def test_evaluate_alert_condition(self, monitoring):
        """Test alert condition evaluation."""
        context = {"cpu_usage": 85.0, "memory_usage": 70.0}
        
        # Test CPU condition
        result = monitoring._evaluate_alert_condition("cpu_usage > 80", context)
        assert result is True
        
        result = monitoring._evaluate_alert_condition("cpu_usage > 90", context)
        assert result is False
        
        # Test memory condition
        result = monitoring._evaluate_alert_condition("memory_usage > 80", context)
        assert result is False
    
    def test_get_dashboard_data(self, monitoring):
        """Test dashboard data retrieval."""
        # Add some metrics
        monitoring.system_metrics.append(monitoring._collect_system_metrics())
        monitoring.application_metrics.append(monitoring._collect_application_metrics())
        monitoring.business_metrics.append(monitoring._collect_business_metrics())
        
        dashboard_data = monitoring.get_dashboard_data()
        
        assert "current_metrics" in dashboard_data
        assert "recent_alerts" in dashboard_data
        assert "trends" in dashboard_data
        assert "alert_summary" in dashboard_data
        assert "system_health" in dashboard_data
    
    def test_get_analytics_summary(self, monitoring):
        """Test analytics summary retrieval."""
        # Add some metrics
        now = datetime.now()
        for i in range(5):
            monitoring.system_metrics.append(monitoring._collect_system_metrics())
            monitoring.application_metrics.append(monitoring._collect_application_metrics())
            monitoring.business_metrics.append(monitoring._collect_business_metrics())
        
        summary = monitoring.get_analytics_summary(days=1)
        
        assert "period_days" in summary
        assert "metrics_summary" in summary
        assert "alerts_summary" in summary
        assert summary["period_days"] == 1
    
    def test_generate_periodic_report(self, monitoring):
        """Test periodic report generation."""
        # Add some metrics
        monitoring.system_metrics.append(monitoring._collect_system_metrics())
        monitoring.application_metrics.append(monitoring._collect_application_metrics())
        monitoring.business_metrics.append(monitoring._collect_business_metrics())
        
        # Generate report
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        
        report = asyncio.run(monitoring._generate_report("hourly", period_start, period_end))
        
        assert report.report_type == "hourly"
        assert isinstance(report.period_start, datetime)
        assert isinstance(report.period_end, datetime)
        assert isinstance(report.metrics, dict)
        assert isinstance(report.insights, list)
        assert isinstance(report.recommendations, list)


class TestCachingOptimizer:
    """Test Caching Optimizer functionality."""
    
    @pytest.fixture
    def cache_optimizer(self):
        """Create caching optimizer instance for testing."""
        return CachingOptimizer(cache_dir="test_cache/caching_optimizer")
    
    def test_cache_initialization(self, cache_optimizer):
        """Test cache initialization."""
        assert cache_optimizer.cache_dir.exists()
        assert isinstance(cache_optimizer.config, CacheConfig)
        assert cache_optimizer.config.max_size_mb > 0
        assert cache_optimizer.config.max_entries > 0
        assert cache_optimizer.config.eviction_policy in ["lru", "lfu", "ttl", "adaptive"]
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_optimizer):
        """Test cache set and get operations."""
        # Set a value
        success = await cache_optimizer.set("test_key", "test_value")
        assert success is True
        
        # Get the value
        value = await cache_optimizer.get("test_key")
        assert value == "test_value"
        
        # Get non-existent key
        value = await cache_optimizer.get("non_existent", "default")
        assert value == "default"
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_optimizer):
        """Test cache TTL functionality."""
        # Set a value with short TTL
        short_ttl = timedelta(milliseconds=100)
        await cache_optimizer.set("ttl_key", "ttl_value", ttl=short_ttl)
        
        # Should be available immediately
        value = await cache_optimizer.get("ttl_key")
        assert value == "ttl_value"
        
        # Wait for TTL to expire
        await asyncio.sleep(0.2)
        
        # Should be expired
        value = await cache_optimizer.get("ttl_key", "default")
        assert value == "default"
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_optimizer):
        """Test cache delete operation."""
        # Set a value
        await cache_optimizer.set("delete_key", "delete_value")
        
        # Verify it exists
        value = await cache_optimizer.get("delete_key")
        assert value == "delete_value"
        
        # Delete it
        success = await cache_optimizer.delete("delete_key")
        assert success is True
        
        # Verify it's gone
        value = await cache_optimizer.get("delete_key", "default")
        assert value == "default"
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_optimizer):
        """Test cache clear operation."""
        # Add some values
        await cache_optimizer.set("key1", "value1")
        await cache_optimizer.set("key2", "value2")
        
        # Verify they exist
        assert await cache_optimizer.get("key1") == "value1"
        assert await cache_optimizer.get("key2") == "value2"
        
        # Clear cache
        await cache_optimizer.clear()
        
        # Verify they're gone
        assert await cache_optimizer.get("key1", "default") == "default"
        assert await cache_optimizer.get("key2", "default") == "default"
    
    def test_get_cache_stats(self, cache_optimizer):
        """Test cache statistics retrieval."""
        # Add some entries
        asyncio.run(cache_optimizer.set("stat_key1", "stat_value1"))
        asyncio.run(cache_optimizer.set("stat_key2", "stat_value2"))
        
        stats = cache_optimizer.get_cache_stats()
        
        assert isinstance(stats.total_entries, int)
        assert isinstance(stats.total_size_bytes, int)
        assert isinstance(stats.hit_count, int)
        assert isinstance(stats.miss_count, int)
        assert isinstance(stats.hit_rate, (int, float))
        assert stats.total_entries >= 0
    
    def test_get_cache_info(self, cache_optimizer):
        """Test cache information retrieval."""
        info = cache_optimizer.get_cache_info()
        
        assert "configuration" in info
        assert "statistics" in info
        assert "entry_analysis" in info
        assert "warmup_keys" in info
        assert "background_processes" in info
    
    @pytest.mark.asyncio
    async def test_optimize_cache(self, cache_optimizer):
        """Test cache optimization."""
        # Add some entries
        for i in range(10):
            await cache_optimizer.set(f"opt_key_{i}", f"opt_value_{i}")
        
        # Run optimization
        result = await cache_optimizer.optimize_cache()
        
        assert "policy_changed" in result
        assert "hit_rate_before" in result
        assert "hit_rate_after" in result
        assert "hit_rate_improvement" in result
    
    @pytest.mark.asyncio
    async def test_benchmark_cache(self, cache_optimizer):
        """Test cache benchmarking."""
        result = await cache_optimizer.benchmark_cache(operations=100)
        
        assert "write_operations" in result
        assert "write_time" in result
        assert "write_ops_per_second" in result
        assert "read_operations" in result
        assert "read_time" in result
        assert "read_ops_per_second" in result
        assert "mixed_operations" in result
        assert "mixed_time" in result
        assert "mixed_ops_per_second" in result
    
    def test_export_cache_data(self, cache_optimizer):
        """Test cache data export."""
        # Add some data
        asyncio.run(cache_optimizer.set("export_key", "export_value"))
        
        # Export as JSON
        json_data = cache_optimizer.export_cache_data("json")
        assert isinstance(json_data, str)
        assert "timestamp" in json_data
        assert "configuration" in json_data
        assert "entries" in json_data
        
        # Export as CSV
        csv_data = cache_optimizer.export_cache_data("csv")
        assert isinstance(csv_data, str)
        assert "key" in csv_data
        assert "created_at" in csv_data


class TestLoadTesting:
    """Test Load Testing functionality."""
    
    @pytest.fixture
    def load_testing(self):
        """Create load testing instance for testing."""
        return LoadTesting(cache_dir="test_cache/load_testing")
    
    def test_load_testing_initialization(self, load_testing):
        """Test load testing initialization."""
        assert load_testing.cache_dir.exists()
        assert load_testing.max_concurrent_users > 0
        assert load_testing.default_timeout > 0
        assert load_testing.monitoring_interval > 0
        assert load_testing.query_templates is not None
    
    def test_create_scenario(self, load_testing):
        """Test load test scenario creation."""
        scenario = load_testing.create_scenario(
            name="test_scenario",
            description="Test scenario",
            concurrent_users=10,
            duration_seconds=60,
            ramp_up_time=10,
            requests_per_second=5,
            request_types={"factual": 0.6, "advisory": 0.4},
            think_time=1.0
        )
        
        assert isinstance(scenario, LoadTestScenario)
        assert scenario.name == "test_scenario"
        assert scenario.concurrent_users == 10
        assert scenario.duration_seconds == 60
        assert scenario.requests_per_second == 5
        assert "factual" in scenario.request_types
    
    def test_get_predefined_scenarios(self, load_testing):
        """Test predefined scenarios retrieval."""
        scenarios = load_testing.get_predefined_scenarios()
        
        assert isinstance(scenarios, dict)
        assert "light_load" in scenarios
        assert "moderate_load" in scenarios
        assert "heavy_load" in scenarios
        assert "stress_test" in scenarios
        assert "endurance_test" in scenarios
        
        # Verify scenario properties
        light_load = scenarios["light_load"]
        assert isinstance(light_load, LoadTestScenario)
        assert light_load.concurrent_users > 0
        assert light_load.duration_seconds > 0
    
    def test_generate_query(self, load_testing):
        """Test query generation."""
        request_types = {"factual": 0.6, "advisory": 0.4}
        
        query = load_testing._generate_query(request_types)
        
        assert isinstance(query, str)
        assert len(query) > 0
        
        # Should be one of the template queries
        all_queries = []
        for queries in load_testing.query_templates.values():
            all_queries.extend(queries)
        assert query in all_queries
    
    @pytest.mark.asyncio
    async def test_simulate_system_response(self, load_testing):
        """Test system response simulation."""
        query = "What is the expense ratio?"
        timeout = 5.0
        
        response = await load_testing._simulate_system_response(query, timeout)
        
        assert "status" in response
        assert "response_time" in response
        assert response["response_time"] > 0
        
        if response["status"] == "success":
            assert "query" in response
        else:
            assert "error" in response
    
    @pytest.mark.asyncio
    async def test_run_load_test(self, load_testing):
        """Test load test execution."""
        # Get predefined scenarios
        scenarios = load_testing.get_predefined_scenarios()
        
        # Run light load test
        result = await load_testing.run_load_test("light_load", simulate_system=False)
        
        assert isinstance(result, LoadTestResult)
        assert result.scenario_name == "light_load"
        assert isinstance(result.start_time, datetime)
        assert isinstance(result.end_time, datetime)
        assert result.total_requests >= 0
        assert result.successful_requests >= 0
        assert result.failed_requests >= 0
        assert isinstance(result.average_response_time, (int, float))
        assert isinstance(result.requests_per_second, (int, float))
        assert isinstance(result.error_rate, (int, float))
    
    def test_get_test_summary(self, load_testing):
        """Test test summary retrieval."""
        # Add a test result
        now = datetime.now()
        test_result = LoadTestResult(
            scenario_name="test_scenario",
            start_time=now - timedelta(seconds=60),
            end_time=now,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=1.5,
            min_response_time=0.5,
            max_response_time=3.0,
            p95_response_time=2.5,
            p99_response_time=2.8,
            requests_per_second=1.67,
            error_rate=5.0,
            cpu_usage=[50.0, 60.0],
            memory_usage=[70.0, 75.0],
            errors=["Error 1", "Error 2"]
        )
        
        load_testing.test_results = [test_result]
        
        summary = load_testing.get_test_summary()
        
        assert "summary" in summary
        assert "by_scenario" in summary
        assert summary["summary"]["total_tests"] == 1
        assert summary["summary"]["total_requests"] == 100
        assert summary["summary"]["successful_requests"] == 95
        assert summary["summary"]["overall_success_rate"] == 95.0
    
    def test_get_performance_report(self, load_testing):
        """Test performance report retrieval."""
        # Add a test result
        now = datetime.now()
        test_result = LoadTestResult(
            scenario_name="test_scenario",
            start_time=now - timedelta(seconds=60),
            end_time=now,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=1.5,
            min_response_time=0.5,
            max_response_time=3.0,
            p95_response_time=2.5,
            p99_response_time=2.8,
            requests_per_second=1.67,
            error_rate=5.0,
            cpu_usage=[50.0, 60.0],
            memory_usage=[70.0, 75.0],
            errors=["Error 1", "Error 2"]
        )
        
        load_testing.test_results = [test_result]
        
        report = load_testing.get_performance_report()
        
        assert "performance_metrics" in report
        assert "test_count" in report
        
        if "performance_metrics" in report:
            perf = report["performance_metrics"]
            assert "response_time" in perf
            assert "throughput" in perf
            assert "system_resources" in perf
    
    def test_generate_load_test_report(self, load_testing):
        """Test load test report generation."""
        # Add a test result
        now = datetime.now()
        test_result = LoadTestResult(
            scenario_name="test_scenario",
            start_time=now - timedelta(seconds=60),
            end_time=now,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=1.5,
            min_response_time=0.5,
            max_response_time=3.0,
            p95_response_time=2.5,
            p99_response_time=2.8,
            requests_per_second=1.67,
            error_rate=5.0,
            cpu_usage=[50.0, 60.0],
            memory_usage=[70.0, 75.0],
            errors=["Error 1", "Error 2"]
        )
        
        load_testing.test_results = [test_result]
        
        # Generate JSON report
        json_report = load_testing.generate_load_test_report("test_scenario", "json")
        assert isinstance(json_report, str)
        
        # Generate markdown report
        markdown_report = load_testing.generate_load_test_report("test_scenario", "markdown")
        assert isinstance(markdown_report, str)
        assert "# Load Test Report" in markdown_report
        
        # Generate HTML report
        html_report = load_testing.generate_load_test_report("test_scenario", "html")
        assert isinstance(html_report, str)
        assert "<html>" in html_report


class TestPhase26Pipeline:
    """Test Phase 2.6 Pipeline integration."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing."""
        return Phase26Pipeline()
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.performance_optimizer is not None
        assert pipeline.testing_framework is not None
        assert pipeline.monitoring_analytics is not None
        assert pipeline.caching_optimizer is not None
        assert pipeline.load_testing is not None
    
    @pytest.mark.asyncio
    async def test_performance_optimization_test(self, pipeline):
        """Test performance optimization component test."""
        result = await pipeline.test_performance_optimization()
        
        assert "success" in result
        assert "bottlenecks_detected" in result
        assert "optimizations_applied" in result
        assert "improvement_percentage" in result
        assert "performance_trends" in result
    
    @pytest.mark.asyncio
    async def test_comprehensive_testing_test(self, pipeline):
        """Test comprehensive testing component test."""
        result = await pipeline.test_comprehensive_testing()
        
        assert "success" in result
        assert "unit_tests_run" in result
        assert "unit_tests_passed" in result
        assert "integration_tests_run" in result
        assert "integration_tests_passed" in result
        assert "overall_coverage" in result
    
    @pytest.mark.asyncio
    async def test_monitoring_analytics_test(self, pipeline):
        """Test monitoring analytics component test."""
        result = await pipeline.test_monitoring_analytics()
        
        assert "success" in result
        assert "metrics_collected" in result
        assert "alerts_generated" in result
        assert "dashboard_data_available" in result
        assert "analytics_summary" in result
    
    @pytest.mark.asyncio
    async def test_caching_optimization_test(self, pipeline):
        """Test caching optimization component test."""
        result = await pipeline.test_caching_optimization()
        
        assert "success" in result
        assert "cache_operations" in result
        assert "cache_hit_rate" in result
        assert "optimization_applied" in result
        assert "benchmark_results" in result
    
    @pytest.mark.asyncio
    async def test_load_testing_test(self, pipeline):
        """Test load testing component test."""
        result = await pipeline.test_load_testing()
        
        assert "success" in result
        assert "scenarios_available" in result
        assert "load_test_completed" in result
        assert "load_test_results" in result
        assert "performance_report" in result
    
    @pytest.mark.asyncio
    async def test_integration_test(self, pipeline):
        """Test integration component test."""
        result = await pipeline.test_integration()
        
        assert "success" in result
        assert "performance_to_monitoring" in result
        assert "monitoring_to_caching" in result
        assert "caching_to_testing" in result
        assert "testing_to_load_testing" in result
        assert "end_to_end_workflow" in result
    
    @pytest.mark.asyncio
    async def test_performance_validation(self, pipeline):
        """Test performance validation."""
        result = await pipeline.run_performance_validation()
        
        assert "success" in result
        assert "optimization_performance" in result
        assert "testing_performance" in result
        assert "monitoring_performance" in result
        assert "caching_performance" in result
        assert "load_testing_performance" in result
        assert "overall_performance" in result
    
    def test_calculate_system_health(self, pipeline):
        """Test system health calculation."""
        health_score = pipeline._calculate_system_health()
        
        assert isinstance(health_score, (int, float))
        assert 0 <= health_score <= 100


# Performance tests
class TestPerformance:
    """Performance tests for Phase 2.6 components."""
    
    def test_performance_optimizer_performance(self):
        """Test performance optimizer performance."""
        optimizer = PerformanceOptimizer(cache_dir="test_cache/perf_optimizer")
        
        import time
        start_time = time.time()
        
        # Test metrics collection
        metrics = optimizer._collect_system_metrics()
        
        elapsed_time = time.time() - start_time
        
        # Should complete metrics collection in under 1 second
        assert elapsed_time < 1.0
        print(f"Performance optimizer collected metrics in {elapsed_time:.3f}s")
    
    def test_caching_optimizer_performance(self):
        """Test caching optimizer performance."""
        cache = CachingOptimizer(cache_dir="test_cache/perf_cache")
        
        import time
        start_time = time.time()
        
        # Test cache operations
        for i in range(100):
            asyncio.run(cache.set(f"perf_key_{i}", f"perf_value_{i}"))
        
        for i in range(100):
            asyncio.run(cache.get(f"perf_key_{i}"))
        
        elapsed_time = time.time() - start_time
        
        # Should complete 200 cache operations in under 2 seconds
        assert elapsed_time < 2.0
        print(f"Caching optimizer performed 200 operations in {elapsed_time:.3f}s")
    
    def test_testing_framework_performance(self):
        """Test testing framework performance."""
        framework = TestingFramework(cache_dir="test_cache/perf_testing")
        
        import time
        start_time = time.time()
        
        # Test result processing
        for i in range(100):
            result = TestResult(
                test_name=f"perf_test_{i}",
                test_type="unit",
                status="passed",
                execution_time=0.1,
                error_message=None,
                assertions=5,
                coverage=85.0,
                timestamp=datetime.now(),
                metadata={}
            )
            framework.test_results.append(result)
        
        # Generate summary
        summary = framework.get_test_summary()
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 result processing in under 1 second
        assert elapsed_time < 1.0
        print(f"Testing framework processed 100 results in {elapsed_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
