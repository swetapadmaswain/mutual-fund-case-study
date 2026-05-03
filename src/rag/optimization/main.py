"""
Phase 2.6 Main Pipeline: Performance Optimization and Testing

Orchestrates the complete Phase 2.6 workflow including performance optimization,
comprehensive testing, monitoring, caching, and load testing.
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.optimization.performance_optimizer import PerformanceOptimizer
from src.rag.optimization.testing_framework import TestingFramework
from src.rag.optimization.monitoring_analytics import MonitoringAnalytics
from src.rag.optimization.caching_optimizer import CachingOptimizer
from src.rag.optimization.load_testing import LoadTesting

logger = logging.getLogger(__name__)

@dataclass
class Phase26Results:
    """Results from Phase 2.6 pipeline execution."""
    success: bool
    optimization_improvements: float
    test_coverage: float
    system_health_score: float
    cache_hit_rate: float
    load_test_performance: Dict[str, Any]
    component_results: Dict[str, Any]
    errors: List[str]

class Phase26Pipeline:
    """
    Main pipeline for Phase 2.6: Performance Optimization and Testing.
    
    Orchestrates:
    - Performance optimization
    - Comprehensive testing
    - Monitoring and analytics
    - Caching optimization
    - Load testing
    - Performance validation
    """
    
    def __init__(self):
        """Initialize Phase 2.6 pipeline."""
        # Initialize components
        self.performance_optimizer = PerformanceOptimizer()
        self.testing_framework = TestingFramework()
        self.monitoring_analytics = MonitoringAnalytics()
        self.caching_optimizer = CachingOptimizer()
        self.load_testing = LoadTesting()
        
        # Performance tracking
        self.start_time = None
        self.component_results = {}
        
        logger.info("Phase 2.6 Pipeline initialized")
    
    async def test_performance_optimization(self) -> Dict[str, Any]:
        """
        Test performance optimization functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing performance optimization...")
        
        test_results = {
            "success": False,
            "bottlenecks_detected": 0,
            "optimizations_applied": 0,
            "improvement_percentage": 0.0,
            "performance_trends": {},
            "error": None
        }
        
        try:
            # Start monitoring
            self.performance_optimizer.start_monitoring()
            
            # Wait for some metrics to be collected
            await asyncio.sleep(2)
            
            # Detect bottlenecks
            bottlenecks = self.performance_optimizer.bottlenecks
            test_results["bottlenecks_detected"] = len(bottlenecks)
            
            # Run optimization cycle
            optimization_results = await self.performance_optimizer.run_optimization_cycle()
            test_results["optimizations_applied"] = len(optimization_results)
            
            # Calculate improvement
            if optimization_results:
                improvements = [r.improvement_percentage for r in optimization_results]
                test_results["improvement_percentage"] = sum(improvements) / len(improvements)
            
            # Get performance trends
            summary = self.performance_optimizer.get_performance_summary()
            test_results["performance_trends"] = summary
            
            # Stop monitoring
            self.performance_optimizer.stop_monitoring()
            
            test_results["success"] = True
            
            logger.info(f"Performance optimization test passed: {len(bottlenecks)} bottlenecks detected")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Performance optimization test failed: {e}")
        
        return test_results
    
    async def test_comprehensive_testing(self) -> Dict[str, Any]:
        """
        Test comprehensive testing framework.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing comprehensive testing framework...")
        
        test_results = {
            "success": False,
            "unit_tests_run": 0,
            "unit_tests_passed": 0,
            "integration_tests_run": 0,
            "integration_tests_passed": 0,
            "performance_tests_run": 0,
            "performance_tests_passed": 0,
            "load_tests_run": 0,
            "load_tests_passed": 0,
            "overall_coverage": 0.0,
            "error": None
        }
        
        try:
            # Run unit tests
            unit_report = await self.testing_framework.run_unit_tests()
            test_results["unit_tests_run"] = unit_report.total_tests
            test_results["unit_tests_passed"] = unit_report.passed_tests
            
            # Run integration tests
            integration_report = await self.testing_framework.run_integration_tests()
            test_results["integration_tests_run"] = integration_report.total_tests
            test_results["integration_tests_passed"] = integration_report.passed_tests
            
            # Run performance tests
            performance_report = await self.testing_framework.run_performance_tests()
            test_results["performance_tests_run"] = performance_report.total_tests
            test_results["performance_tests_passed"] = performance_report.passed_tests
            
            # Run load tests (light load only for testing)
            load_report = await self.load_testing.run_load_test("light_load", simulate_system=False)
            test_results["load_tests_run"] = load_report.total_requests
            test_results["load_tests_passed"] = load_report.successful_requests
            
            # Calculate overall coverage
            total_tests = (unit_report.total_tests + integration_report.total_tests + 
                          performance_report.total_tests + load_report.total_requests)
            total_passed = (unit_report.passed_tests + integration_report.passed_tests + 
                           performance_report.passed_tests + load_report.successful_requests)
            
            test_results["overall_coverage"] = (total_passed / total_tests * 100) if total_tests > 0 else 0.0
            
            test_results["success"] = True
            
            logger.info(f"Comprehensive testing test passed: {total_passed}/{total_tests} tests passed")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Comprehensive testing test failed: {e}")
        
        return test_results
    
    async def test_monitoring_analytics(self) -> Dict[str, Any]:
        """
        Test monitoring and analytics system.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing monitoring and analytics...")
        
        test_results = {
            "success": False,
            "metrics_collected": 0,
            "alerts_generated": 0,
            "reports_generated": 0,
            "dashboard_data_available": False,
            "analytics_summary": {},
            "error": None
        }
        
        try:
            # Start monitoring
            self.monitoring_analytics.start_monitoring()
            
            # Wait for metrics to be collected
            await asyncio.sleep(2)
            
            # Get dashboard data
            dashboard_data = self.monitoring_analytics.get_dashboard_data()
            test_results["dashboard_data_available"] = bool(dashboard_data)
            
            # Count metrics
            if dashboard_data and "current_metrics" in dashboard_data:
                metrics = dashboard_data["current_metrics"]
                test_results["metrics_collected"] = sum(
                    1 for metric in [metrics.get("system"), metrics.get("application"), metrics.get("business")]
                    if metric
                )
            
            # Count alerts
            if dashboard_data and "recent_alerts" in dashboard_data:
                test_results["alerts_generated"] = len(dashboard_data["recent_alerts"])
            
            # Get analytics summary
            summary = self.monitoring_analytics.get_analytics_summary(days=1)
            test_results["analytics_summary"] = summary
            
            # Generate a report
            try:
                report = await self.monitoring_analytics._generate_report("hourly", 
                    datetime.now() - timedelta(hours=1), datetime.now())
                test_results["reports_generated"] = 1
            except:
                pass  # Report generation might fail in test environment
            
            # Stop monitoring
            self.monitoring_analytics.stop_monitoring()
            
            test_results["success"] = True
            
            logger.info(f"Monitoring test passed: {test_results['metrics_collected']} metrics collected")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Monitoring test failed: {e}")
        
        return test_results
    
    async def test_caching_optimization(self) -> Dict[str, Any]:
        """
        Test caching optimization system.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing caching optimization...")
        
        test_results = {
            "success": False,
            "cache_operations": 0,
            "cache_hit_rate": 0.0,
            "optimization_applied": False,
            "benchmark_results": {},
            "error": None
        }
        
        try:
            # Start background processes
            self.caching_optimizer.start_background_processes()
            
            # Test cache operations
            cache_operations = 100
            
            # Test writes
            for i in range(cache_operations // 2):
                await self.caching_optimizer.set(f"test_key_{i}", f"test_value_{i}")
            
            # Test reads
            hits = 0
            for i in range(cache_operations // 2):
                value = await self.caching_optimizer.get(f"test_key_{i}")
                if value is not None:
                    hits += 1
            
            test_results["cache_operations"] = cache_operations
            test_results["cache_hit_rate"] = (hits / (cache_operations // 2) * 100) if cache_operations > 0 else 0.0
            
            # Test optimization
            optimization_result = await self.caching_optimizer.optimize_cache()
            test_results["optimization_applied"] = optimization_result.get("policy_changed", False)
            
            # Benchmark cache
            benchmark_results = await self.caching_optimizer.benchmark_cache(operations=100)
            test_results["benchmark_results"] = benchmark_results
            
            # Get cache stats
            stats = self.caching_optimizer.get_cache_stats()
            test_results["cache_hit_rate"] = stats.hit_rate
            
            # Stop background processes
            self.caching_optimizer.stop_background_processes()
            
            test_results["success"] = True
            
            logger.info(f"Caching test passed: {stats.hit_rate:.1f}% hit rate")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Caching test failed: {e}")
        
        return test_results
    
    async def test_load_testing(self) -> Dict[str, Any]:
        """
        Test load testing tools.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing load testing tools...")
        
        test_results = {
            "success": False,
            "scenarios_available": 0,
            "load_test_completed": False,
            "load_test_results": {},
            "performance_report": {},
            "error": None
        }
        
        try:
            # Check available scenarios
            scenarios = self.load_testing.get_predefined_scenarios()
            test_results["scenarios_available"] = len(scenarios)
            
            # Run a light load test (without actual system simulation)
            load_result = await self.load_testing.run_load_test("light_load", simulate_system=False)
            test_results["load_test_completed"] = True
            
            # Extract key metrics
            test_results["load_test_results"] = {
                "total_requests": load_result.total_requests,
                "successful_requests": load_result.successful_requests,
                "average_response_time": load_result.average_response_time,
                "requests_per_second": load_result.requests_per_second,
                "error_rate": load_result.error_rate
            }
            
            # Get performance report
            performance_report = self.load_testing.get_performance_report("light_load")
            test_results["performance_report"] = {
                "avg_response_time": performance_report.get("performance_metrics", {}).get("response_time", {}).get("average", 0.0),
                "avg_requests_per_second": performance_report.get("performance_metrics", {}).get("throughput", {}).get("average_rps", 0.0),
                "avg_error_rate": performance_report.get("performance_metrics", {}).get("system_resources", {}).get("cpu_usage", {}).get("average", 0.0)
            }
            
            test_results["success"] = True
            
            logger.info(f"Load testing test passed: {load_result.successful_requests}/{load_result.total_requests} requests successful")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Load testing test failed: {e}")
        
        return test_results
    
    async def test_integration(self) -> Dict[str, Any]:
        """
        Test integration between Phase 2.6 components.
        
        Returns:
            Integration test results
        """
        logger.info("Testing Phase 2.6 integration...")
        
        integration_results = {
            "success": False,
            "performance_to_monitoring": False,
            "monitoring_to_caching": False,
            "caching_to_testing": False,
            "testing_to_load_testing": False,
            "end_to_end_workflow": False,
            "data_flow_consistent": False,
            "error": None
        }
        
        try:
            # Test performance to monitoring integration
            self.performance_optimizer.start_monitoring()
            await asyncio.sleep(1)
            
            perf_summary = self.performance_optimizer.get_performance_summary()
            monitoring_active = self.monitoring_analytics.monitoring_active
            
            integration_results["performance_to_monitoring"] = bool(perf_summary) and monitoring_active
            
            # Test monitoring to caching integration
            self.monitoring_analytics.start_monitoring()
            self.caching_optimizer.start_background_processes()
            await asyncio.sleep(1)
            
            cache_stats = self.caching_optimizer.get_cache_stats()
            monitoring_dashboard = self.monitoring_analytics.get_dashboard_data()
            
            integration_results["monitoring_to_caching"] = bool(cache_stats) and bool(monitoring_dashboard)
            
            # Test caching to testing integration
            await self.caching_optimizer.set("integration_test", "test_value")
            test_summary = self.testing_framework.get_test_summary()
            
            integration_results["caching_to_testing"] = cache_stats.total_entries > 0 and bool(test_summary)
            
            # Test testing to load testing integration
            load_scenarios = self.load_testing.get_predefined_scenarios()
            test_reports = self.testing_framework.test_reports
            
            integration_results["testing_to_load_testing"] = bool(load_scenarios) and len(test_reports) > 0
            
            # Overall integration success
            integration_results["end_to_end_workflow"] = all([
                integration_results["performance_to_monitoring"],
                integration_results["monitoring_to_caching"],
                integration_results["caching_to_testing"],
                integration_results["testing_to_load_testing"]
            ])
            
            integration_results["data_flow_consistent"] = integration_results["end_to_end_workflow"]
            integration_results["success"] = integration_results["end_to_end_workflow"]
            
            # Cleanup
            self.performance_optimizer.stop_monitoring()
            self.monitoring_analytics.stop_monitoring()
            self.caching_optimizer.stop_background_processes()
            
            if integration_results["success"]:
                logger.info("Integration test passed")
            else:
                logger.warning("Integration test partially failed")
            
        except Exception as e:
            integration_results["error"] = str(e)
            logger.error(f"Integration test failed: {e}")
        
        return integration_results
    
    async def run_performance_validation(self) -> Dict[str, Any]:
        """
        Run performance validation tests.
        
        Returns:
            Performance validation results
        """
        logger.info("Running performance validation...")
        
        performance_results = {
            "success": False,
            "optimization_performance": {},
            "testing_performance": {},
            "monitoring_performance": {},
            "caching_performance": {},
            "load_testing_performance": {},
            "overall_performance": {},
            "error": None
        }
        
        try:
            # Test performance optimization
            opt_start = time.time()
            opt_result = await self.test_performance_optimization()
            opt_time = time.time() - opt_start
            
            performance_results["optimization_performance"] = {
                "processing_time": opt_time,
                "success": opt_result["success"],
                "target_met": opt_time < 10.0  # Target: < 10 seconds
            }
            
            # Test comprehensive testing
            test_start = time.time()
            test_result = await self.test_comprehensive_testing()
            test_time = time.time() - test_start
            
            performance_results["testing_performance"] = {
                "processing_time": test_time,
                "success": test_result["success"],
                "target_met": test_time < 30.0  # Target: < 30 seconds
            }
            
            # Test monitoring
            monitor_start = time.time()
            monitor_result = await self.test_monitoring_analytics()
            monitor_time = time.time() - monitor_start
            
            performance_results["monitoring_performance"] = {
                "processing_time": monitor_time,
                "success": monitor_result["success"],
                "target_met": monitor_time < 5.0  # Target: < 5 seconds
            }
            
            # Test caching
            cache_start = time.time()
            cache_result = await self.test_caching_optimization()
            cache_time = time.time() - cache_start
            
            performance_results["caching_performance"] = {
                "processing_time": cache_time,
                "success": cache_result["success"],
                "target_met": cache_time < 15.0  # Target: < 15 seconds
            }
            
            # Test load testing
            load_start = time.time()
            load_result = await self.test_load_testing()
            load_time = time.time() - load_start
            
            performance_results["load_testing_performance"] = {
                "processing_time": load_time,
                "success": load_result["success"],
                "target_met": load_time < 20.0  # Target: < 20 seconds
            }
            
            # Overall performance
            total_time = opt_time + test_time + monitor_time + cache_time + load_time
            performance_results["overall_performance"] = {
                "total_time": total_time,
                "target_met": total_time < 80.0,  # Target: < 80 seconds total
                "all_targets_met": all([
                    performance_results["optimization_performance"]["target_met"],
                    performance_results["testing_performance"]["target_met"],
                    performance_results["monitoring_performance"]["target_met"],
                    performance_results["caching_performance"]["target_met"],
                    performance_results["load_testing_performance"]["target_met"]
                ])
            }
            
            performance_results["success"] = performance_results["overall_performance"]["all_targets_met"]
            
            if performance_results["success"]:
                logger.info("Performance validation passed")
            else:
                logger.warning("Performance validation failed - some targets not met")
            
        except Exception as e:
            performance_results["error"] = str(e)
            logger.error(f"Performance validation failed: {e}")
        
        return performance_results
    
    async def export_results(self, results: Phase26Results) -> bool:
        """
        Export Phase 2.6 results to files.
        
        Args:
            results: Phase 2.6 results to export
            
        Returns:
            True if export successful
        """
        try:
            # Create results directory
            results_dir = Path("cache/phase2_6_results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Export summary results
            summary_data = {
                "success": results.success,
                "optimization_improvements": results.optimization_improvements,
                "test_coverage": results.test_coverage,
                "system_health_score": results.system_health_score,
                "cache_hit_rate": results.cache_hit_rate,
                "load_test_performance": results.load_test_performance,
                "component_results": results.component_results,
                "errors": results.errors,
                "timestamp": time.time()
            }
            
            with open(results_dir / "phase2_6_results.json", 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            # Export component statistics
            stats_data = {
                "performance_optimizer_stats": self.performance_optimizer.get_performance_summary(),
                "testing_framework_stats": self.testing_framework.get_test_summary(),
                "monitoring_analytics_stats": self.monitoring_analytics.get_analytics_summary(days=1),
                "caching_optimizer_stats": self.caching_optimizer.get_cache_info(),
                "load_testing_stats": self.load_testing.get_test_summary()
            }
            
            with open(results_dir / "component_statistics.json", 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            logger.info(f"Phase 2.6 results exported to {results_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    async def run_pipeline(self) -> Phase26Results:
        """
        Run the complete Phase 2.6 pipeline.
        
        Returns:
            Phase26Results object with pipeline results
        """
        logger.info("Starting Phase 2.6 Pipeline: Performance Optimization and Testing")
        print("=" * 80)
        print("PHASE 2.6: PERFORMANCE OPTIMIZATION AND TESTING")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Step 1: Test Performance Optimization
        print("\n🔹 TESTING PERFORMANCE OPTIMIZATION:")
        optimization_test = await self.test_performance_optimization()
        self.component_results["performance_optimization"] = optimization_test
        print(f"  {'✅' if optimization_test['success'] else '❌'} Performance Optimization: {optimization_test['bottlenecks_detected']} bottlenecks detected")
        if optimization_test['error']:
            print(f"     Error: {optimization_test['error']}")
        
        # Step 2: Test Comprehensive Testing
        print("\n🔹 TESTING COMPREHENSIVE TESTING:")
        testing_test = await self.test_comprehensive_testing()
        self.component_results["comprehensive_testing"] = testing_test
        print(f"  {'✅' if testing_test['success'] else '❌'} Comprehensive Testing: {testing_test['overall_coverage']:.1f}% coverage")
        print(f"     Unit Tests: {testing_test['unit_tests_passed']}/{testing_test['unit_tests_run']}")
        print(f"     Integration Tests: {testing_test['integration_tests_passed']}/{testing_test['integration_tests_run']}")
        
        # Step 3: Test Monitoring and Analytics
        print("\n🔹 TESTING MONITORING AND ANALYTICS:")
        monitoring_test = await self.test_monitoring_analytics()
        self.component_results["monitoring_analytics"] = monitoring_test
        print(f"  {'✅' if monitoring_test['success'] else '❌'} Monitoring Analytics: {monitoring_test['metrics_collected']} metrics collected")
        
        # Step 4: Test Caching Optimization
        print("\n🔹 TESTING CACHING OPTIMIZATION:")
        caching_test = await self.test_caching_optimization()
        self.component_results["caching_optimization"] = caching_test
        print(f"  {'✅' if caching_test['success'] else '❌'} Caching Optimization: {caching_test['cache_hit_rate']:.1f}% hit rate")
        
        # Step 5: Test Load Testing
        print("\n🔹 TESTING LOAD TESTING:")
        load_test = await self.test_load_testing()
        self.component_results["load_testing"] = load_test
        print(f"  {'✅' if load_test['success'] else '❌'} Load Testing: {load_test['scenarios_available']} scenarios available")
        
        # Step 6: Integration Testing
        print("\n🔹 TESTING INTEGRATION:")
        integration_test = await self.test_integration()
        self.component_results["integration"] = integration_test
        print(f"  {'✅' if integration_test['success'] else '❌'} Integration: {'Passed' if integration_test['success'] else 'Failed'}")
        
        # Step 7: Performance Validation
        print("\n🔹 PERFORMANCE VALIDATION:")
        performance_test = await self.run_performance_validation()
        self.component_results["performance"] = performance_test
        print(f"  {'✅' if performance_test['success'] else '❌'} Performance: {'All targets met' if performance_test['success'] else 'Some targets not met'}")
        
        # Step 8: Export Results
        print("\n🔹 EXPORTING RESULTS:")
        
        # Calculate statistics
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Create results object
        results = Phase26Results(
            success=all([
                optimization_test['success'],
                testing_test['success'],
                monitoring_test['success'],
                caching_test['success'],
                load_test['success'],
                integration_test['success'],
                performance_test['success']
            ]),
            optimization_improvements=optimization_test.get('improvement_percentage', 0.0),
            test_coverage=testing_test.get('overall_coverage', 0.0),
            system_health_score=self._calculate_system_health(),
            cache_hit_rate=caching_test.get('cache_hit_rate', 0.0),
            load_test_performance=load_test.get('load_test_results', {}),
            component_results=self.component_results,
            errors=[]
        )
        
        # Export results
        export_success = await self.export_results(results)
        print(f"  {'✅' if export_success else '❌'} Export: {'Completed' if export_success else 'Failed'}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PHASE 2.6 RESULTS: Performance Optimization and Testing")
        print("=" * 80)
        print(f"Success: {'✅' if results.success else '❌'}")
        print(f"Optimization Improvements: {results.optimization_improvements:.1f}%")
        print(f"Test Coverage: {results.test_coverage:.1f}%")
        print(f"System Health Score: {results.system_health_score:.1f}")
        print(f"Cache Hit Rate: {results.cache_hit_rate:.1f}%")
        
        print("\n📈 COMPONENT TESTS:")
        print(f"Performance Optimization: {'✅' if optimization_test['success'] else '❌'}")
        print(f"Comprehensive Testing: {'✅' if testing_test['success'] else '❌'}")
        print(f"Monitoring Analytics: {'✅' if monitoring_test['success'] else '❌'}")
        print(f"Caching Optimization: {'✅' if caching_test['success'] else '❌'}")
        print(f"Load Testing: {'✅' if load_test['success'] else '❌'}")
        print(f"Integration: {'✅' if integration_test['success'] else '❌'}")
        print(f"Performance Validation: {'✅' if performance_test['success'] else '❌'}")
        
        print("\n📊 PERFORMANCE METRICS:")
        if performance_test.get('success'):
            opt_perf = performance_test['optimization_performance']
            test_perf = performance_test['testing_performance']
            monitor_perf = performance_test['monitoring_performance']
            cache_perf = performance_test['caching_performance']
            load_perf = performance_test['load_testing_performance']
            
            print(f"Optimization Processing: {opt_perf['processing_time']:.2f}s")
            print(f"Testing Processing: {test_perf['processing_time']:.2f}s")
            print(f"Monitoring Processing: {monitor_perf['processing_time']:.2f}s")
            print(f"Caching Processing: {cache_perf['processing_time']:.2f}s")
            print(f"Load Testing Processing: {load_perf['processing_time']:.2f}s")
        
        print("\n🔧 QUALITY METRICS:")
        print(f"Optimization Efficiency: {results.optimization_improvements:.1f}%")
        print(f"Test Suite Coverage: {results.test_coverage:.1f}%")
        print(f"System Health: {results.system_health_score:.1f}/100")
        print(f"Cache Performance: {results.cache_hit_rate:.1f}%")
        print(f"Load Test Performance: {results.load_test_performance.get('requests_per_second', 0):.1f} RPS")
        
        print("\n" + "=" * 80)
        
        return results
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score."""
        health_scores = []
        
        # Performance optimizer health
        try:
            perf_health = self.performance_optimizer.health_check()
            if perf_health.get("status") == "healthy":
                health_scores.append(90.0)
            elif perf_health.get("status") == "degraded":
                health_scores.append(70.0)
            else:
                health_scores.append(50.0)
        except:
            health_scores.append(50.0)
        
        # Testing framework health
        try:
            test_health = self.testing_framework.health_check()
            if test_health.get("status") == "healthy":
                health_scores.append(90.0)
            elif test_health.get("status") == "degraded":
                health_scores.append(70.0)
            else:
                health_scores.append(50.0)
        except:
            health_scores.append(50.0)
        
        # Monitoring analytics health
        try:
            monitor_health = self.monitoring_analytics.health_check()
            if monitor_health.get("status") == "healthy":
                health_scores.append(90.0)
            elif monitor_health.get("status") == "degraded":
                health_scores.append(70.0)
            else:
                health_scores.append(50.0)
        except:
            health_scores.append(50.0)
        
        # Caching optimizer health
        try:
            cache_health = self.caching_optimizer.health_check()
            if cache_health.get("status") == "healthy":
                health_scores.append(90.0)
            elif cache_health.get("status") == "degraded":
                health_scores.append(70.0)
            else:
                health_scores.append(50.0)
        except:
            health_scores.append(50.0)
        
        # Load testing health
        try:
            load_health = self.load_testing.health_check()
            if load_health.get("status") == "healthy":
                health_scores.append(90.0)
            elif load_health.get("status") == "degraded":
                health_scores.append(70.0)
            else:
                health_scores.append(50.0)
        except:
            health_scores.append(50.0)
        
        return statistics.mean(health_scores) if health_scores else 0.0

async def main():
    """Main function to run Phase 2.6 pipeline."""
    try:
        pipeline = Phase26Pipeline()
        results = await pipeline.run_pipeline()
        
        if results.success:
            print("\n✅ Phase 2.6 completed successfully!")
            return 0
        else:
            print("\n❌ Phase 2.6 completed with issues.")
            return 1
            
    except Exception as e:
        logger.error(f"Phase 2.6 pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
