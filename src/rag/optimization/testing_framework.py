"""
Comprehensive Testing Framework for Phase 2.6

Provides comprehensive testing capabilities including unit tests, integration tests, performance tests, and quality assurance.
"""

import asyncio
import time
import pytest
import unittest
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import json
import traceback
import statistics
import concurrent.futures

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a test execution."""
    test_name: str
    test_type: str  # "unit", "integration", "performance", "load"
    status: str  # "passed", "failed", "skipped", "error"
    execution_time: float
    error_message: Optional[str]
    assertions: int
    coverage: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class TestSuite:
    """Collection of related tests."""
    name: str
    description: str
    tests: List[str]
    setup_function: Optional[str]
    teardown_function: Optional[str]
    dependencies: List[str]
    tags: List[str]

@dataclass
class TestReport:
    """Comprehensive test report."""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_time: float
    average_time: float
    coverage_percentage: float
    performance_metrics: Dict[str, float]
    timestamp: datetime
    test_results: List[TestResult]

class TestingFramework:
    """
    Comprehensive testing framework for all system components.
    
    Features:
    - Unit testing with pytest integration
    - Integration testing capabilities
    - Performance benchmarking
    - Load testing simulation
    - Test coverage analysis
    - Automated test execution
    - Test result reporting
    """
    
    def __init__(self, cache_dir: str = "cache/testing_framework"):
        """
        Initialize testing framework.
        
        Args:
            cache_dir: Directory for caching test data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Test storage
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_results: List[TestResult] = []
        self.test_reports: List[TestReport] = []
        
        # Configuration
        self.test_timeout = 300  # 5 minutes
        self.parallel_execution = True
        self.max_workers = 4
        self.coverage_threshold = 80.0
        
        # Test registry
        self.unit_tests: Dict[str, Callable] = {}
        self.integration_tests: Dict[str, Callable] = {}
        self.performance_tests: Dict[str, Callable] = {}
        self.load_tests: Dict[str, Callable] = {}
        
        # Initialize built-in tests
        self._initialize_builtin_tests()
        
        # Load existing data
        self._load_test_suites()
        self._load_test_results()
        
        logger.info("Testing Framework initialized")
    
    def _initialize_builtin_tests(self) -> None:
        """Initialize built-in test suites."""
        # Unit test suites
        self.register_test_suite("phase2_1_unit", "Phase 2.1 Unit Tests", [
            "test_chunking_functionality",
            "test_metadata_extraction",
            "test_content_processing"
        ])
        
        self.register_test_suite("phase2_2_unit", "Phase 2.2 Unit Tests", [
            "test_embedding_generation",
            "test_vector_storage",
            "test_similarity_search"
        ])
        
        self.register_test_suite("phase2_3_unit", "Phase 2.3 Unit Tests", [
            "test_query_processing",
            "test_search_engine",
            "test_context_building"
        ])
        
        self.register_test_suite("phase2_4_unit", "Phase 2.4 Unit Tests", [
            "test_llm_service",
            "test_prompt_engineering",
            "test_response_validation"
        ])
        
        self.register_test_suite("phase2_5_unit", "Phase 2.5 Unit Tests", [
            "test_source_management",
            "test_metadata_consistency",
            "test_citation_system"
        ])
        
        # Integration test suites
        self.register_test_suite("end_to_end", "End-to-End Integration Tests", [
            "test_complete_pipeline",
            "test_data_flow",
            "test_error_handling"
        ])
        
        self.register_test_suite("api_integration", "API Integration Tests", [
            "test_api_endpoints",
            "test_request_response",
            "test_error_codes"
        ])
        
        # Performance test suites
        self.register_test_suite("performance_benchmarks", "Performance Benchmarks", [
            "test_query_latency",
            "test_throughput",
            "test_memory_usage"
        ])
        
        # Load test suites
        self.register_test_suite("load_testing", "Load Testing", [
            "test_concurrent_users",
            "test_system_stress",
            "test_resource_limits"
        ])
    
    def _load_test_suites(self) -> None:
        """Load test suites from cache."""
        suites_file = self.cache_dir / "test_suites.json"
        
        if suites_file.exists():
            try:
                with open(suites_file, 'r') as f:
                    data = json.load(f)
                
                for suite_name, suite_data in data.items():
                    self.test_suites[suite_name] = TestSuite(**suite_data)
                
                logger.info(f"Loaded {len(self.test_suites)} test suites")
                
            except Exception as e:
                logger.error(f"Error loading test suites: {e}")
    
    def _load_test_results(self) -> None:
        """Load test results from cache."""
        results_file = self.cache_dir / "test_results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                
                self.test_results = []
                for result_data in data:
                    result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                    self.test_results.append(TestResult(**result_data))
                
                logger.info(f"Loaded {len(self.test_results)} test results")
                
            except Exception as e:
                logger.error(f"Error loading test results: {e}")
    
    def _save_test_suites(self) -> None:
        """Save test suites to cache."""
        try:
            suites_file = self.cache_dir / "test_suites.json"
            
            serializable_suites = {}
            for suite_name, suite in self.test_suites.items():
                serializable_suites[suite_name] = asdict(suite)
            
            with open(suites_file, 'w') as f:
                json.dump(serializable_suites, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving test suites: {e}")
    
    def _save_test_results(self) -> None:
        """Save test results to cache."""
        try:
            results_file = self.cache_dir / "test_results.json"
            
            serializable_results = []
            for result in self.test_results:
                result_dict = asdict(result)
                result_dict['timestamp'] = result.timestamp.isoformat()
                serializable_results.append(result_dict)
            
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
    
    def register_test_suite(self, name: str, description: str, tests: List[str], 
                           setup: Optional[str] = None, teardown: Optional[str] = None,
                           dependencies: List[str] = None, tags: List[str] = None) -> None:
        """
        Register a test suite.
        
        Args:
            name: Suite name
            description: Suite description
            tests: List of test names
            setup: Setup function name
            teardown: Teardown function name
            dependencies: List of dependencies
            tags: List of tags
        """
        suite = TestSuite(
            name=name,
            description=description,
            tests=tests,
            setup_function=setup,
            teardown_function=teardown,
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        self.test_suites[name] = suite
        self._save_test_suites()
        
        logger.info(f"Registered test suite: {name}")
    
    def register_unit_test(self, name: str, test_function: Callable) -> None:
        """Register a unit test."""
        self.unit_tests[name] = test_function
        logger.debug(f"Registered unit test: {name}")
    
    def register_integration_test(self, name: str, test_function: Callable) -> None:
        """Register an integration test."""
        self.integration_tests[name] = test_function
        logger.debug(f"Registered integration test: {name}")
    
    def register_performance_test(self, name: str, test_function: Callable) -> None:
        """Register a performance test."""
        self.performance_tests[name] = test_function
        logger.debug(f"Registered performance test: {name}")
    
    def register_load_test(self, name: str, test_function: Callable) -> None:
        """Register a load test."""
        self.load_tests[name] = test_function
        logger.debug(f"Registered load test: {name}")
    
    async def run_unit_tests(self, suite_name: Optional[str] = None) -> TestReport:
        """
        Run unit tests.
        
        Args:
            suite_name: Specific suite to run (optional)
            
        Returns:
            TestReport with results
        """
        logger.info(f"Running unit tests for suite: {suite_name or 'all'}")
        
        start_time = time.time()
        test_results = []
        
        # Determine which tests to run
        if suite_name and suite_name in self.test_suites:
            suite = self.test_suites[suite_name]
            tests_to_run = [test for test in suite.tests if test in self.unit_tests]
        else:
            tests_to_run = list(self.unit_tests.keys())
        
        # Run tests
        if self.parallel_execution and len(tests_to_run) > 1:
            test_results = await self._run_tests_parallel(tests_to_run, "unit")
        else:
            test_results = await self._run_tests_sequential(tests_to_run, "unit")
        
        # Create report
        total_time = time.time() - start_time
        report = self._create_test_report(suite_name or "unit_tests", test_results, total_time)
        
        self.test_reports.append(report)
        return report
    
    async def run_integration_tests(self, suite_name: Optional[str] = None) -> TestReport:
        """
        Run integration tests.
        
        Args:
            suite_name: Specific suite to run (optional)
            
        Returns:
            TestReport with results
        """
        logger.info(f"Running integration tests for suite: {suite_name or 'all'}")
        
        start_time = time.time()
        test_results = []
        
        # Determine which tests to run
        if suite_name and suite_name in self.test_suites:
            suite = self.test_suites[suite_name]
            tests_to_run = [test for test in suite.tests if test in self.integration_tests]
        else:
            tests_to_run = list(self.integration_tests.keys())
        
        # Run tests (integration tests usually run sequentially)
        test_results = await self._run_tests_sequential(tests_to_run, "integration")
        
        # Create report
        total_time = time.time() - start_time
        report = self._create_test_report(suite_name or "integration_tests", test_results, total_time)
        
        self.test_reports.append(report)
        return report
    
    async def run_performance_tests(self, suite_name: Optional[str] = None) -> TestReport:
        """
        Run performance tests.
        
        Args:
            suite_name: Specific suite to run (optional)
            
        Returns:
            TestReport with results
        """
        logger.info(f"Running performance tests for suite: {suite_name or 'all'}")
        
        start_time = time.time()
        test_results = []
        
        # Determine which tests to run
        if suite_name and suite_name in self.test_suites:
            suite = self.test_suites[suite_name]
            tests_to_run = [test for test in suite.tests if test in self.performance_tests]
        else:
            tests_to_run = list(self.performance_tests.keys())
        
        # Run tests (performance tests usually run sequentially)
        test_results = await self._run_tests_sequential(tests_to_run, "performance")
        
        # Create report
        total_time = time.time() - start_time
        report = self._create_test_report(suite_name or "performance_tests", test_results, total_time)
        
        self.test_reports.append(report)
        return report
    
    async def run_load_tests(self, suite_name: Optional[str] = None) -> TestReport:
        """
        Run load tests.
        
        Args:
            suite_name: Specific suite to run (optional)
            
        Returns:
            TestReport with results
        """
        logger.info(f"Running load tests for suite: {suite_name or 'all'}")
        
        start_time = time.time()
        test_results = []
        
        # Determine which tests to run
        if suite_name and suite_name in self.test_suites:
            suite = self.test_suites[suite_name]
            tests_to_run = [test for test in suite.tests if test in self.load_tests]
        else:
            tests_to_run = list(self.load_tests.keys())
        
        # Run tests (load tests usually run sequentially)
        test_results = await self._run_tests_sequential(tests_to_run, "load")
        
        # Create report
        total_time = time.time() - start_time
        report = self._create_test_report(suite_name or "load_tests", test_results, total_time)
        
        self.test_reports.append(report)
        return report
    
    async def _run_tests_parallel(self, test_names: List[str], test_type: str) -> List[TestResult]:
        """Run tests in parallel."""
        test_results = []
        test_functions = self._get_test_functions(test_names, test_type)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self._run_single_test, test_name, test_func): test_name
                for test_name, test_func in test_functions.items()
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_test, timeout=self.test_timeout):
                test_name = future_to_test[future]
                try:
                    result = future.result()
                    test_results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = TestResult(
                        test_name=test_name,
                        test_type=test_type,
                        status="error",
                        execution_time=0.0,
                        error_message=str(e),
                        assertions=0,
                        coverage=0.0,
                        timestamp=datetime.now(),
                        metadata={"traceback": traceback.format_exc()}
                    )
                    test_results.append(error_result)
        
        return test_results
    
    async def _run_tests_sequential(self, test_names: List[str], test_type: str) -> List[TestResult]:
        """Run tests sequentially."""
        test_results = []
        test_functions = self._get_test_functions(test_names, test_type)
        
        for test_name, test_func in test_functions.items():
            try:
                result = await self._run_single_test(test_name, test_func)
                test_results.append(result)
            except Exception as e:
                # Create error result
                error_result = TestResult(
                    test_name=test_name,
                    test_type=test_type,
                    status="error",
                    execution_time=0.0,
                    error_message=str(e),
                    assertions=0,
                    coverage=0.0,
                    timestamp=datetime.now(),
                    metadata={"traceback": traceback.format_exc()}
                )
                test_results.append(error_result)
        
        return test_results
    
    def _get_test_functions(self, test_names: List[str], test_type: str) -> Dict[str, Callable]:
        """Get test functions by type."""
        test_functions = {}
        
        if test_type == "unit":
            test_registry = self.unit_tests
        elif test_type == "integration":
            test_registry = self.integration_tests
        elif test_type == "performance":
            test_registry = self.performance_tests
        elif test_type == "load":
            test_registry = self.load_tests
        else:
            return {}
        
        for test_name in test_names:
            if test_name in test_registry:
                test_functions[test_name] = test_registry[test_name]
        
        return test_functions
    
    async def _run_single_test(self, test_name: str, test_function: Callable) -> TestResult:
        """Run a single test."""
        start_time = time.time()
        
        try:
            # Run the test
            if asyncio.iscoroutinefunction(test_function):
                result = await test_function()
            else:
                result = test_function()
            
            execution_time = time.time() - start_time
            
            # Extract test result information
            if isinstance(result, dict):
                status = result.get("status", "passed")
                assertions = result.get("assertions", 1)
                coverage = result.get("coverage", 0.0)
                error_message = result.get("error_message")
            else:
                status = "passed"
                assertions = 1
                coverage = 0.0
                error_message = None
            
            return TestResult(
                test_name=test_name,
                test_type=self._get_test_type(test_name),
                status=status,
                execution_time=execution_time,
                error_message=error_message,
                assertions=assertions,
                coverage=coverage,
                timestamp=datetime.now(),
                metadata={}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_name,
                test_type=self._get_test_type(test_name),
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                assertions=0,
                coverage=0.0,
                timestamp=datetime.now(),
                metadata={"traceback": traceback.format_exc()}
            )
    
    def _get_test_type(self, test_name: str) -> str:
        """Get test type by test name."""
        if test_name in self.unit_tests:
            return "unit"
        elif test_name in self.integration_tests:
            return "integration"
        elif test_name in self.performance_tests:
            return "performance"
        elif test_name in self.load_tests:
            return "load"
        else:
            return "unknown"
    
    def _create_test_report(self, suite_name: str, test_results: List[TestResult], total_time: float) -> TestReport:
        """Create a test report."""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == "passed"])
        failed_tests = len([r for r in test_results if r.status == "failed"])
        skipped_tests = len([r for r in test_results if r.status == "skipped"])
        error_tests = len([r for r in test_results if r.status == "error"])
        
        average_time = total_time / total_tests if total_tests > 0 else 0.0
        coverage_percentage = statistics.mean([r.coverage for r in test_results]) if test_results else 0.0
        
        # Performance metrics
        performance_metrics = {
            "fastest_test": min([r.execution_time for r in test_results]) if test_results else 0.0,
            "slowest_test": max([r.execution_time for r in test_results]) if test_results else 0.0,
            "total_assertions": sum([r.assertions for r in test_results]),
            "tests_per_second": total_tests / total_time if total_time > 0 else 0.0
        }
        
        report = TestReport(
            suite_name=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            total_time=total_time,
            average_time=average_time,
            coverage_percentage=coverage_percentage,
            performance_metrics=performance_metrics,
            timestamp=datetime.now(),
            test_results=test_results
        )
        
        # Store results
        self.test_results.extend(test_results)
        self._save_test_results()
        
        return report
    
    async def run_all_tests(self) -> Dict[str, TestReport]:
        """
        Run all test suites.
        
        Returns:
            Dictionary of test reports by suite
        """
        logger.info("Running all test suites")
        
        reports = {}
        
        # Run unit tests
        reports["unit"] = await self.run_unit_tests()
        
        # Run integration tests
        reports["integration"] = await self.run_integration_tests()
        
        # Run performance tests
        reports["performance"] = await self.run_performance_tests()
        
        # Run load tests
        reports["load"] = await self.run_load_tests()
        
        return reports
    
    def get_test_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive test summary.
        
        Returns:
            Test summary dictionary
        """
        if not self.test_results:
            return {"message": "No test results available"}
        
        # Overall statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "passed"])
        failed_tests = len([r for r in self.test_results if r.status == "failed"])
        skipped_tests = len([r for r in self.test_results if r.status == "skipped"])
        error_tests = len([r for r in self.test_results if r.status == "error"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        # Performance statistics
        execution_times = [r.execution_time for r in self.test_results]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0
        
        # Coverage statistics
        coverage_scores = [r.coverage for r in self.test_results if r.coverage > 0]
        avg_coverage = statistics.mean(coverage_scores) if coverage_scores else 0.0
        
        # Test type breakdown
        test_types = defaultdict(int)
        test_type_success = defaultdict(int)
        
        for result in self.test_results:
            test_types[result.test_type] += 1
            if result.status == "passed":
                test_type_success[result.test_type] += 1
        
        # Recent test trends
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_results = [r for r in self.test_results if r.timestamp > recent_cutoff]
        
        recent_success_rate = (
            len([r for r in recent_results if r.status == "passed"]) / len(recent_results) * 100
            if recent_results else 0.0
        )
        
        return {
            "overall": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "error_tests": error_tests,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "average_coverage": avg_coverage
            },
            "by_type": {
                test_type: {
                    "total": test_types[test_type],
                    "passed": test_type_success[test_type],
                    "success_rate": (test_type_success[test_type] / test_types[test_type] * 100) 
                                   if test_types[test_type] > 0 else 0.0
                }
                for test_type in test_types.keys()
            },
            "recent_trends": {
                "last_7_days": {
                    "total_tests": len(recent_results),
                    "success_rate": recent_success_rate
                }
            },
            "test_suites": len(self.test_suites),
            "last_updated": max([r.timestamp for r in self.test_results]) if self.test_results else None
        }
    
    def get_failed_tests(self) -> List[TestResult]:
        """
        Get list of failed tests.
        
        Returns:
            List of failed test results
        """
        return [r for r in self.test_results if r.status in ["failed", "error"]]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report for all tests.
        
        Returns:
            Performance report dictionary
        """
        performance_results = [r for r in self.test_results if r.test_type == "performance"]
        
        if not performance_results:
            return {"message": "No performance test results available"}
        
        # Performance metrics
        execution_times = [r.execution_time for r in performance_results]
        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # Performance by test
        performance_by_test = {}
        for result in performance_results:
            if result.test_name not in performance_by_test:
                performance_by_test[result.test_name] = []
            performance_by_test[result.test_name].append(result.execution_time)
        
        test_performance = {}
        for test_name, times in performance_by_test.items():
            test_performance[test_name] = {
                "average_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "runs": len(times)
            }
        
        return {
            "summary": {
                "total_performance_tests": len(performance_results),
                "average_execution_time": avg_time,
                "fastest_test": min_time,
                "slowest_test": max_time
            },
            "by_test": test_performance,
            "trends": {
                "improving_tests": [],
                "degrading_tests": []
            }
        }
    
    def generate_test_report(self, format_type: str = "json") -> str:
        """
        Generate comprehensive test report.
        
        Args:
            format_type: Format type ("json", "html", "markdown")
            
        Returns:
            Formatted report string
        """
        summary = self.get_test_summary()
        failed_tests = self.get_failed_tests()
        performance_report = self.get_performance_report()
        
        if format_type == "json":
            report_data = {
                "summary": summary,
                "failed_tests": [asdict(test) for test in failed_tests],
                "performance_report": performance_report,
                "generated_at": datetime.now().isoformat()
            }
            return json.dumps(report_data, indent=2, default=str)
        
        elif format_type == "markdown":
            return self._generate_markdown_report(summary, failed_tests, performance_report)
        
        elif format_type == "html":
            return self._generate_html_report(summary, failed_tests, performance_report)
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _generate_markdown_report(self, summary: Dict[str, Any], failed_tests: List[TestResult], 
                                 performance_report: Dict[str, Any]) -> str:
        """Generate markdown test report."""
        report = []
        
        # Header
        report.append("# Test Report")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        overall = summary["overall"]
        report.append(f"- **Total Tests**: {overall['total_tests']}")
        report.append(f"- **Passed**: {overall['passed_tests']}")
        report.append(f"- **Failed**: {overall['failed_tests']}")
        report.append(f"- **Success Rate**: {overall['success_rate']:.1f}%")
        report.append(f"- **Average Execution Time**: {overall['average_execution_time']:.3f}s")
        report.append(f"- **Average Coverage**: {overall['average_coverage']:.1f}%")
        report.append("")
        
        # Test Types
        report.append("## Test Types")
        for test_type, stats in summary["by_type"].items():
            report.append(f"### {test_type.title()}")
            report.append(f"- Total: {stats['total']}")
            report.append(f"- Passed: {stats['passed']}")
            report.append(f"- Success Rate: {stats['success_rate']:.1f}%")
            report.append("")
        
        # Failed Tests
        if failed_tests:
            report.append("## Failed Tests")
            for test in failed_tests[:10]:  # Limit to first 10
                report.append(f"### {test.test_name}")
                report.append(f"- **Status**: {test.status}")
                report.append(f"- **Type**: {test.test_type}")
                report.append(f"- **Error**: {test.error_message}")
                report.append(f"- **Execution Time**: {test.execution_time:.3f}s")
                report.append("")
        
        # Performance Report
        if "summary" in performance_report:
            report.append("## Performance Tests")
            perf_summary = performance_report["summary"]
            report.append(f"- **Total Performance Tests**: {perf_summary['total_performance_tests']}")
            report.append(f"- **Average Time**: {perf_summary['average_execution_time']:.3f}s")
            report.append(f"- **Fastest Test**: {perf_summary['fastest_test']:.3f}s")
            report.append(f"- **Slowest Test**: {perf_summary['slowest_test']:.3f}s")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_html_report(self, summary: Dict[str, Any], failed_tests: List[TestResult], 
                             performance_report: Dict[str, Any]) -> str:
        """Generate HTML test report."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
        .passed { color: green; }
        .failed { color: red; }
        .skipped { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <p>Generated on: {timestamp}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {total_tests}</p>
        <p><strong>Passed:</strong> <span class="passed">{passed_tests}</span></p>
        <p><strong>Failed:</strong> <span class="failed">{failed_tests}</span></p>
        <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
        <p><strong>Average Execution Time:</strong> {avg_time:.3f}s</p>
        <p><strong>Average Coverage:</strong> {avg_coverage:.1f}%</p>
    </div>
    
    <h2>Test Types</h2>
    <table>
        <tr><th>Type</th><th>Total</th><th>Passed</th><th>Success Rate</th></tr>
        {test_types_table}
    </table>
    
    {failed_tests_section}
    
    {performance_section}
    
</body>
</html>
        """.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tests=summary["overall"]["total_tests"],
            passed_tests=summary["overall"]["passed_tests"],
            failed_tests=summary["overall"]["failed_tests"],
            success_rate=summary["overall"]["success_rate"],
            avg_time=summary["overall"]["average_execution_time"],
            avg_coverage=summary["overall"]["average_coverage"],
            test_types_table=self._generate_test_types_table(summary["by_type"]),
            failed_tests_section=self._generate_failed_tests_html(failed_tests),
            performance_section=self._generate_performance_html(performance_report)
        )
        
        return html
    
    def _generate_test_types_table(self, test_types: Dict[str, Any]) -> str:
        """Generate HTML table for test types."""
        rows = []
        for test_type, stats in test_types.items():
            rows.append(f"<tr><td>{test_type.title()}</td><td>{stats['total']}</td>"
                       f"<td>{stats['passed']}</td><td>{stats['success_rate']:.1f}%</td></tr>")
        return "\n".join(rows)
    
    def _generate_failed_tests_html(self, failed_tests: List[TestResult]) -> str:
        """Generate HTML section for failed tests."""
        if not failed_tests:
            return ""
        
        html = "<h2>Failed Tests</h2><table><tr><th>Test Name</th><th>Type</th><th>Status</th><th>Error</th><th>Time</th></tr>"
        
        for test in failed_tests[:10]:
            html += f"<tr><td>{test.test_name}</td><td>{test.test_type}</td>"
            html += f"<td class='failed'>{test.status}</td><td>{test.error_message}</td>"
            html += f"<td>{test.execution_time:.3f}s</td></tr>"
        
        html += "</table>"
        return html
    
    def _generate_performance_html(self, performance_report: Dict[str, Any]) -> str:
        """Generate HTML section for performance report."""
        if "summary" not in performance_report:
            return ""
        
        summary = performance_report["summary"]
        html = "<h2>Performance Tests</h2>"
        html += f"<p><strong>Total Performance Tests:</strong> {summary['total_performance_tests']}</p>"
        html += f"<p><strong>Average Time:</strong> {summary['average_execution_time']:.3f}s</p>"
        html += f"<p><strong>Fastest Test:</strong> {summary['fastest_test']:.3f}s</p>"
        html += f"<p><strong>Slowest Test:</strong> {summary['slowest_test']:.3f}s</p>"
        
        return html
    
    async def cleanup_old_results(self, days: int = 30) -> int:
        """
        Clean up old test results.
        
        Args:
            days: Number of days to keep results
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_results = [
            result for result in self.test_results
            if result.timestamp < cutoff_date
        ]
        
        # Remove old results
        self.test_results = [
            result for result in self.test_results
            if result.timestamp >= cutoff_date
        ]
        
        # Save updated results
        self._save_test_results()
        
        logger.info(f"Cleaned up {len(old_results)} old test results")
        return len(old_results)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on testing framework.
        
        Returns:
            Health status dictionary
        """
        summary = self.get_test_summary()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "test_suites": len(self.test_suites),
                "total_results": len(self.test_results),
                "last_test_run": summary.get("last_updated"),
                "success_rate": summary.get("overall", {}).get("success_rate", 0)
            }
        }
        
        # Check success rate
        success_rate = summary.get("overall", {}).get("success_rate", 0)
        if success_rate < 80:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low success rate: {success_rate:.1f}%")
        
        # Check for recent test runs
        last_test = summary.get("last_updated")
        if last_test and (datetime.now() - last_test) > timedelta(days=7):
            health_status["status"] = "degraded"
            health_status["issues"].append("No recent test runs")
        
        return health_status
