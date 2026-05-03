"""
Integration Testing Framework for Phase 3

Provides comprehensive integration testing for the complete query processing pipeline.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict
import statistics

from .query_classifier import QueryClassifier, QueryType
from .response_generator import ResponseGenerator, ResponseContext
from .response_formatter import ResponseFormatter, OutputFormat
from .compliance_safety import ComplianceSafetyLayer

logger = logging.getLogger(__name__)

@dataclass
class TestQuery:
    """Test query definition."""
    query_id: str
    query: str
    expected_type: QueryType
    expected_intent: str
    expected_response_type: str
    test_category: str
    priority: str

@dataclass
class TestResult:
    """Test result."""
    test_query: TestQuery
    classification_result: Dict[str, Any]
    generation_result: Dict[str, Any]
    formatting_result: Dict[str, Any]
    compliance_result: Dict[str, Any]
    overall_success: bool
    execution_time: float
    errors: List[str]
    timestamp: datetime

@dataclass
class BenchmarkResult:
    """Benchmark result."""
    metric_name: str
    value: float
    target: float
    passed: bool
    timestamp: datetime

class RAGIntegrationTests:
    """
    Integration testing framework for Phase 3 components.
    
    Features:
    - End-to-end pipeline testing
    - Performance benchmarking
    - Compliance validation
    - Error handling testing
    - Load testing simulation
    """
    
    def __init__(self, cache_dir: str = "cache/integration_tests"):
        """
        Initialize integration testing framework.
        
        Args:
            cache_dir: Directory for caching test data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.query_classifier = QueryClassifier()
        self.response_generator = ResponseGenerator()
        self.response_formatter = ResponseFormatter()
        self.compliance_safety = ComplianceSafetyLayer()
        
        # Test queries
        self.test_queries = self._initialize_test_queries()
        
        # Test results
        self.test_results: List[TestResult] = []
        self.benchmark_results: List[BenchmarkResult] = []
        
        # Performance targets
        self.performance_targets = {
            "query_response_time": 3.0,  # seconds
            "concurrent_qps": 100,  # queries per second
            "system_uptime": 99.0,  # percentage
            "classification_accuracy": 95.0,  # percentage
            "compliance_approval_rate": 90.0  # percentage
        }
        
        # Load existing data
        self._load_test_queries()
        self._load_results()
        
        logger.info("Integration Testing Framework initialized")
    
    def _initialize_test_queries(self) -> List[TestQuery]:
        """Initialize test queries."""
        return [
            # Factual queries
            TestQuery(
                query_id="factual_1",
                query="What is the expense ratio of HDFC Mid Cap Fund?",
                expected_type=QueryType.FACTUAL,
                expected_intent="get_expense_ratio",
                expected_response_type="factual",
                test_category="factual",
                priority="high"
            ),
            TestQuery(
                query_id="factual_2",
                query="What is the minimum SIP amount for HDFC Equity Fund?",
                expected_type=QueryType.FACTUAL,
                expected_intent="get_minimum_sip",
                expected_response_type="factual",
                test_category="factual",
                priority="high"
            ),
            TestQuery(
                query_id="factual_3",
                query="What is the current NAV of HDFC Focused Fund?",
                expected_type=QueryType.FACTUAL,
                expected_intent="get_nav",
                expected_response_type="factual",
                test_category="factual",
                priority="medium"
            ),
            
            # Advisory queries
            TestQuery(
                query_id="advisory_1",
                query="Should I invest in HDFC Mid Cap Fund?",
                expected_type=QueryType.ADVISORY,
                expected_intent="provide_investment_advice",
                expected_response_type="advisory",
                test_category="advisory",
                priority="high"
            ),
            TestQuery(
                query_id="advisory_2",
                query="Which HDFC fund is better for long-term investment?",
                expected_type=QueryType.ADVISORY,
                expected_intent="compare_funds",
                expected_response_type="advisory",
                test_category="advisory",
                priority="high"
            ),
            
            # Performance queries
            TestQuery(
                query_id="performance_1",
                query="What are the historical returns of HDFC Mid Cap Fund?",
                expected_type=QueryType.PERFORMANCE,
                expected_intent="get_historical_returns",
                expected_response_type="performance",
                test_category="performance",
                priority="high"
            ),
            TestQuery(
                query_id="performance_2",
                query="How has HDFC Equity Fund performed compared to its benchmark?",
                expected_type=QueryType.PERFORMANCE,
                expected_intent="compare_benchmark",
                expected_response_type="performance",
                test_category="performance",
                priority="medium"
            ),
            
            # Procedural queries
            TestQuery(
                query_id="procedural_1",
                query="How to start SIP in HDFC Mid Cap Fund?",
                expected_type=QueryType.PROCEDURAL,
                expected_intent="provide_investment_process",
                expected_response_type="procedural",
                test_category="procedural",
                priority="high"
            ),
            TestQuery(
                query_id="procedural_2",
                query="How to download account statement from HDFC Mutual Fund?",
                expected_type=QueryType.PROCEDURAL,
                expected_intent="provide_statement_download",
                expected_response_type="procedural",
                test_category="procedural",
                priority="medium"
            ),
            
            # General queries
            TestQuery(
                query_id="general_1",
                query="Tell me about HDFC Mutual Fund",
                expected_type=QueryType.GENERAL,
                expected_intent="general_inquiry",
                expected_response_type="general",
                test_category="general",
                priority="low"
            )
        ]
    
    def _load_test_queries(self) -> None:
        """Load test queries from cache."""
        queries_file = self.cache_dir / "test_queries.json"
        
        if queries_file.exists():
            try:
                with open(queries_file, 'r') as f:
                    data = json.load(f)
                
                self.test_queries = []
                for query_data in data:
                    query_data['expected_type'] = QueryType(query_data['expected_type'])
                    self.test_queries.append(TestQuery(**query_data))
                
                logger.info(f"Loaded {len(self.test_queries)} test queries")
                
            except Exception as e:
                logger.error(f"Error loading test queries: {e}")
    
    def _load_results(self) -> None:
        """Load test results from cache."""
        results_file = self.cache_dir / "results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                
                # Load test results
                self.test_results = []
                for result_data in data.get("test_results", []):
                    result_data['test_query']['expected_type'] = QueryType(result_data['test_query']['expected_type'])
                    result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                    self.test_results.append(TestResult(**result_data))
                
                # Load benchmark results
                self.benchmark_results = []
                for benchmark_data in data.get("benchmark_results", []):
                    benchmark_data['timestamp'] = datetime.fromisoformat(benchmark_data['timestamp'])
                    self.benchmark_results.append(BenchmarkResult(**benchmark_data))
                
                logger.info(f"Loaded {len(self.test_results)} test results")
                
            except Exception as e:
                logger.error(f"Error loading results: {e}")
    
    def _save_results(self) -> None:
        """Save test results to cache."""
        try:
            results_file = self.cache_dir / "results.json"
            
            # Serialize test results
            serializable_results = []
            for result in self.test_results:
                result_dict = asdict(result)
                result_dict['test_query']['expected_type'] = result.test_query.expected_type.value
                result_dict['timestamp'] = result.timestamp.isoformat()
                serializable_results.append(result_dict)
            
            # Serialize benchmark results
            serializable_benchmarks = []
            for benchmark in self.benchmark_results:
                benchmark_dict = asdict(benchmark)
                benchmark_dict['timestamp'] = benchmark.timestamp.isoformat()
                serializable_benchmarks.append(benchmark_dict)
            
            data = {
                "test_results": serializable_results,
                "benchmark_results": serializable_benchmarks,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(results_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    async def test_end_to_end_pipeline(self) -> Dict[str, Any]:
        """
        Test the complete end-to-end pipeline.
        
        Returns:
            Test results dictionary
        """
        logger.info("Running end-to-end pipeline tests")
        
        start_time = time.time()
        test_results = []
        
        for test_query in self.test_queries:
            try:
                result = await self._run_single_test(test_query)
                test_results.append(result)
            except Exception as e:
                logger.error(f"Error testing query {test_query.query_id}: {e}")
                test_results.append(TestResult(
                    test_query=test_query,
                    classification_result={"error": str(e)},
                    generation_result={"error": str(e)},
                    formatting_result={"error": str(e)},
                    compliance_result={"error": str(e)},
                    overall_success=False,
                    execution_time=0.0,
                    errors=[str(e)],
                    timestamp=datetime.now()
                ))
        
        # Calculate overall results
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.overall_success])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        execution_time = time.time() - start_time
        
        # Store results
        self.test_results.extend(test_results)
        self._save_results()
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "execution_time": execution_time,
            "detailed_results": test_results
        }
    
    async def _run_single_test(self, test_query: TestQuery) -> TestResult:
        """Run a single test query."""
        start_time = time.time()
        errors = []
        
        try:
            # Step 1: Query Classification
            classification_result = await self._test_classification(test_query)
            
            # Step 2: Response Generation
            generation_result = await self._test_response_generation(test_query, classification_result)
            
            # Step 3: Response Formatting
            formatting_result = await self._test_response_formatting(generation_result)
            
            # Step 4: Compliance Check
            compliance_result = await self._test_compliance(test_query, classification_result, generation_result)
            
            # Determine overall success
            overall_success = (
                classification_result.get("success", False) and
                generation_result.get("success", False) and
                formatting_result.get("success", False) and
                compliance_result.get("approved", False)
            )
            
            return TestResult(
                test_query=test_query,
                classification_result=classification_result,
                generation_result=generation_result,
                formatting_result=formatting_result,
                compliance_result=compliance_result,
                overall_success=overall_success,
                execution_time=time.time() - start_time,
                errors=errors,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            errors.append(str(e))
            return TestResult(
                test_query=test_query,
                classification_result={"error": str(e)},
                generation_result={"error": str(e)},
                formatting_result={"error": str(e)},
                compliance_result={"error": str(e)},
                overall_success=False,
                execution_time=time.time() - start_time,
                errors=errors,
                timestamp=datetime.now()
            )
    
    async def _test_classification(self, test_query: TestQuery) -> Dict[str, Any]:
        """Test query classification."""
        try:
            classification = self.query_classifier.classify_query(test_query.query)
            
            # Check if classification matches expected
            type_match = classification.query_type == test_query.expected_type
            intent_match = classification.intent == test_query.expected_intent
            
            success = type_match and intent_match and classification.confidence > 0.7
            
            return {
                "success": success,
                "classification": asdict(classification),
                "type_match": type_match,
                "intent_match": intent_match,
                "confidence": classification.confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_response_generation(self, test_query: TestQuery, 
                                       classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test response generation."""
        try:
            # Create response context
            context = ResponseContext(
                query=test_query.query,
                classification=classification_result["classification"],
                retrieved_chunks=[],  # Mock chunks for testing
                search_results=[],  # Mock search results
                user_context=None,
                session_context=None,
                metadata={"test_mode": True}
            )
            
            # Generate response
            response = await self.response_generator.generate_response(context)
            
            # Check if response type matches expected
            type_match = response.response_type == test_query.expected_response_type
            content_valid = len(response.content) > 0
            confidence_ok = response.confidence > 0.5
            
            success = type_match and content_valid and confidence_ok
            
            return {
                "success": success,
                "response": asdict(response),
                "type_match": type_match,
                "content_valid": content_valid,
                "confidence_ok": confidence_ok
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_response_formatting(self, generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test response formatting."""
        try:
            response_data = generation_result["response"]
            response = GeneratedResponse(**response_data)
            
            # Test different formats
            formats_to_test = [OutputFormat.JSON, OutputFormat.UI, OutputFormat.TEXT, OutputFormat.MARKDOWN]
            format_results = {}
            
            all_success = True
            
            for format_type in formats_to_test:
                try:
                    formatted = self.response_formatter.format_response(response, format_type)
                    format_success = len(formatted.formatted_content) > 0
                    format_results[format_type.value] = {
                        "success": format_success,
                        "content_length": len(formatted.formatted_content)
                    }
                    
                    if not format_success:
                        all_success = False
                        
                except Exception as e:
                    format_results[format_type.value] = {"success": False, "error": str(e)}
                    all_success = False
            
            return {
                "success": all_success,
                "format_results": format_results,
                "formats_tested": [f.value for f in formats_to_test]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_compliance(self, test_query: TestQuery, classification_result: Dict[str, Any],
                             generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test compliance and safety checks."""
        try:
            response_data = generation_result["response"]
            response = GeneratedResponse(**response_data)
            classification = classification_result["classification"]
            
            # Perform compliance check
            compliance_result = await self.compliance_safety.check_compliance(
                test_query.query, classification, response
            )
            
            success = compliance_result.approved and compliance_result.overall_risk.value in ["low", "medium"]
            
            return {
                "success": success,
                "compliance_result": asdict(compliance_result),
                "approved": compliance_result.approved,
                "risk_level": compliance_result.overall_risk.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def benchmark_performance(self) -> Dict[str, Any]:
        """
        Benchmark system performance.
        
        Returns:
            Performance benchmark results
        """
        logger.info("Running performance benchmarks")
        
        benchmarks = []
        
        # Query response time benchmark
        query_time_result = await self._benchmark_query_response_time()
        benchmarks.append(query_time_result)
        
        # Concurrent query handling benchmark
        concurrent_result = await self._benchmark_concurrent_queries()
        benchmarks.append(concurrent_result)
        
        # Classification accuracy benchmark
        accuracy_result = await self._benchmark_classification_accuracy()
        benchmarks.append(accuracy_result)
        
        # Compliance approval rate benchmark
        compliance_result = await self._benchmark_compliance_approval_rate()
        benchmarks.append(compliance_result)
        
        # Store benchmark results
        self.benchmark_results.extend(benchmarks)
        self._save_results()
        
        return {
            "benchmarks": [asdict(b) for b in benchmarks],
            "overall_performance": self._calculate_overall_performance(benchmarks)
        }
    
    async def _benchmark_query_response_time(self) -> BenchmarkResult:
        """Benchmark query response time."""
        test_query = self.test_queries[0]  # Use first test query
        target = self.performance_targets["query_response_time"]
        
        times = []
        for _ in range(10):  # Run 10 iterations
            start_time = time.time()
            
            # Run classification
            classification = self.query_classifier.classify_query(test_query.query)
            
            # Run response generation
            context = ResponseContext(
                query=test_query.query,
                classification=classification,
                retrieved_chunks=[],
                search_results=[],
                user_context=None,
                session_context=None,
                metadata={"benchmark": True}
            )
            response = await self.response_generator.generate_response(context)
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        passed = avg_time <= target
        
        return BenchmarkResult(
            metric_name="query_response_time",
            value=avg_time,
            target=target,
            passed=passed,
            timestamp=datetime.now()
        )
    
    async def _benchmark_concurrent_queries(self) -> BenchmarkResult:
        """Benchmark concurrent query handling."""
        target_qps = self.performance_targets["concurrent_qps"]
        
        # Simulate concurrent queries
        num_queries = 50
        start_time = time.time()
        
        tasks = []
        for i in range(num_queries):
            test_query = self.test_queries[i % len(self.test_queries)]
            task = self._run_single_test(test_query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        actual_qps = num_queries / total_time
        
        passed = actual_qps >= target_qps
        
        return BenchmarkResult(
            metric_name="concurrent_qps",
            value=actual_qps,
            target=target_qps,
            passed=passed,
            timestamp=datetime.now()
        )
    
    async def _benchmark_classification_accuracy(self) -> BenchmarkResult:
        """Benchmark classification accuracy."""
        target = self.performance_targets["classification_accuracy"]
        
        correct_classifications = 0
        total_classifications = len(self.test_queries)
        
        for test_query in self.test_queries:
            classification = self.query_classifier.classify_query(test_query.query)
            
            if (classification.query_type == test_query.expected_type and
                classification.intent == test_query.expected_intent):
                correct_classifications += 1
        
        accuracy = (correct_classifications / total_classifications * 100) if total_classifications > 0 else 0
        passed = accuracy >= target
        
        return BenchmarkResult(
            metric_name="classification_accuracy",
            value=accuracy,
            target=target,
            passed=passed,
            timestamp=datetime.now()
        )
    
    async def _benchmark_compliance_approval_rate(self) -> BenchmarkResult:
        """Benchmark compliance approval rate."""
        target = self.performance_targets["compliance_approval_rate"]
        
        approved_responses = 0
        total_responses = 0
        
        for test_query in self.test_queries:
            try:
                # Run classification
                classification = self.query_classifier.classify_query(test_query.query)
                
                # Generate response
                context = ResponseContext(
                    query=test_query.query,
                    classification=classification,
                    retrieved_chunks=[],
                    search_results=[],
                    user_context=None,
                    session_context=None,
                    metadata={"benchmark": True}
                )
                response = await self.response_generator.generate_response(context)
                
                # Check compliance
                compliance_result = await self.compliance_safety.check_compliance(
                    test_query.query, classification, response
                )
                
                total_responses += 1
                if compliance_result.approved:
                    approved_responses += 1
                    
            except Exception as e:
                logger.error(f"Error in compliance benchmark: {e}")
        
        approval_rate = (approved_responses / total_responses * 100) if total_responses > 0 else 0
        passed = approval_rate >= target
        
        return BenchmarkResult(
            metric_name="compliance_approval_rate",
            value=approval_rate,
            target=target,
            passed=passed,
            timestamp=datetime.now()
        )
    
    def _calculate_overall_performance(self, benchmarks: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calculate overall performance score."""
        passed_benchmarks = len([b for b in benchmarks if b.passed])
        total_benchmarks = len(benchmarks)
        
        overall_score = (passed_benchmarks / total_benchmarks * 100) if total_benchmarks > 0 else 0
        
        return {
            "overall_score": overall_score,
            "benchmarks_passed": passed_benchmarks,
            "total_benchmarks": total_benchmarks,
            "status": "excellent" if overall_score >= 90 else "good" if overall_score >= 75 else "needs_improvement"
        }
    
    async def validate_compliance(self) -> Dict[str, Any]:
        """
        Validate compliance across all test scenarios.
        
        Returns:
            Compliance validation results
        """
        logger.info("Running compliance validation")
        
        compliance_results = []
        
        for test_query in self.test_queries:
            try:
                # Run classification
                classification = self.query_classifier.classify_query(test_query.query)
                
                # Generate response
                context = ResponseContext(
                    query=test_query.query,
                    classification=classification,
                    retrieved_chunks=[],
                    search_results=[],
                    user_context=None,
                    session_context=None,
                    metadata={"compliance_test": True}
                )
                response = await self.response_generator.generate_response(context)
                
                # Check compliance
                compliance_result = await self.compliance_safety.check_compliance(
                    test_query.query, classification, response
                )
                
                compliance_results.append({
                    "query_id": test_query.query_id,
                    "query": test_query.query,
                    "approved": compliance_result.approved,
                    "risk_level": compliance_result.overall_risk.value,
                    "compliance_checks": len(compliance_result.compliance_checks),
                    "safety_checks": len(compliance_result.safety_checks),
                    "modifications": compliance_result.modifications
                })
                
            except Exception as e:
                logger.error(f"Error in compliance validation for {test_query.query_id}: {e}")
                compliance_results.append({
                    "query_id": test_query.query_id,
                    "error": str(e),
                    "approved": False
                })
        
        # Calculate compliance statistics
        total_validations = len(compliance_results)
        approved_validations = len([r for r in compliance_results if r.get("approved", False)])
        approval_rate = (approved_validations / total_validations * 100) if total_validations > 0 else 0
        
        return {
            "total_validations": total_validations,
            "approved_validations": approved_validations,
            "approval_rate": approval_rate,
            "detailed_results": compliance_results
        }
    
    async def verify_error_handling(self) -> Dict[str, Any]:
        """
        Verify error handling across components.
        
        Returns:
            Error handling verification results
        """
        logger.info("Verifying error handling")
        
        error_tests = []
        
        # Test with malformed queries
        malformed_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            "x" * 1000,  # Very long query
            "!@#$%^&*()",  # Special characters only
        ]
        
        for malformed_query in malformed_queries:
            try:
                # Test classification
                classification = self.query_classifier.classify_query(malformed_query)
                
                # Test response generation
                context = ResponseContext(
                    query=malformed_query,
                    classification=classification,
                    retrieved_chunks=[],
                    search_results=[],
                    user_context=None,
                    session_context=None,
                    metadata={"error_test": True}
                )
                response = await self.response_generator.generate_response(context)
                
                # Test compliance
                compliance_result = await self.compliance_safety.check_compliance(
                    malformed_query, classification, response
                )
                
                error_tests.append({
                    "query": malformed_query[:50] + "..." if len(malformed_query) > 50 else malformed_query,
                    "classification_success": True,
                    "generation_success": True,
                    "compliance_success": True,
                    "overall_success": True
                })
                
            except Exception as e:
                error_tests.append({
                    "query": malformed_query[:50] + "..." if len(malformed_query) > 50 else malformed_query,
                    "error": str(e),
                    "overall_success": False
                })
        
        # Calculate error handling statistics
        total_tests = len(error_tests)
        successful_tests = len([t for t in error_tests if t.get("overall_success", False)])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_error_tests": total_tests,
            "successful_error_tests": successful_tests,
            "error_handling_rate": success_rate,
            "detailed_results": error_tests
        }
    
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
        successful_tests = len([r for r in self.test_results if r.overall_success])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Execution time statistics
        execution_times = [r.execution_time for r in self.test_results]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0
        
        # Category breakdown
        category_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for result in self.test_results:
            category = result.test_query.test_category
            category_stats[category]["total"] += 1
            if result.overall_success:
                category_stats[category]["successful"] += 1
        
        # Benchmark summary
        benchmark_summary = {}
        if self.benchmark_results:
            benchmark_summary = {
                "total_benchmarks": len(self.benchmark_results),
                "passed_benchmarks": len([b for b in self.benchmark_results if b.passed]),
                "latest_results": [asdict(b) for b in self.benchmark_results[-5:]]
            }
        
        return {
            "overall": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time
            },
            "by_category": dict(category_stats),
            "benchmark_summary": benchmark_summary,
            "last_updated": max([r.timestamp for r in self.test_results]) if self.test_results else None
        }
    
    def add_test_query(self, query_id: str, query: str, expected_type: QueryType,
                      expected_intent: str, expected_response_type: str,
                      test_category: str = "custom", priority: str = "medium") -> None:
        """
        Add a custom test query.
        
        Args:
            query_id: Unique query identifier
            query: Query string
            expected_type: Expected query type
            expected_intent: Expected intent
            expected_response_type: Expected response type
            test_category: Test category
            priority: Test priority
        """
        test_query = TestQuery(
            query_id=query_id,
            query=query,
            expected_type=expected_type,
            expected_intent=expected_intent,
            expected_response_type=expected_response_type,
            test_category=test_category,
            priority=priority
        )
        
        self.test_queries.append(test_query)
        
        # Save updated queries
        queries_file = self.cache_dir / "test_queries.json"
        serializable_queries = []
        for query in self.test_queries:
            query_dict = asdict(query)
            query_dict['expected_type'] = query.expected_type.value
            serializable_queries.append(query_dict)
        
        with open(queries_file, 'w') as f:
            json.dump(serializable_queries, f, indent=2)
        
        logger.info(f"Added test query: {query_id}")
    
    def remove_test_query(self, query_id: str) -> bool:
        """
        Remove a test query.
        
        Args:
            query_id: Query identifier to remove
            
        Returns:
            True if query was removed
        """
        original_length = len(self.test_queries)
        self.test_queries = [q for q in self.test_queries if q.query_id != query_id]
        
        if len(self.test_queries) < original_length:
            # Save updated queries
            queries_file = self.cache_dir / "test_queries.json"
            serializable_queries = []
            for query in self.test_queries:
                query_dict = asdict(query)
                query_dict['expected_type'] = query.expected_type.value
                serializable_queries.append(query_dict)
            
            with open(queries_file, 'w') as f:
                json.dump(serializable_queries, f, indent=2)
            
            logger.info(f"Removed test query: {query_id}")
            return True
        
        return False
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old test data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old test results
        old_results = [
            result for result in self.test_results
            if result.timestamp < cutoff_date
        ]
        
        self.test_results = [
            result for result in self.test_results
            if result.timestamp >= cutoff_date
        ]
        
        # Clean up old benchmark results
        old_benchmarks = [
            benchmark for benchmark in self.benchmark_results
            if benchmark.timestamp < cutoff_date
        ]
        
        self.benchmark_results = [
            benchmark for benchmark in self.benchmark_results
            if benchmark.timestamp >= cutoff_date
        ]
        
        # Save updated data
        self._save_results()
        
        logger.info(f"Cleaned up {len(old_results) + len(old_benchmarks)} old test records")
        return len(old_results) + len(old_benchmarks)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on integration testing framework.
        
        Returns:
            Health status dictionary
        """
        summary = self.get_test_summary()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "test_queries": len(self.test_queries),
                "test_results": summary.get("overall", {}).get("total_tests", 0),
                "success_rate": summary.get("overall", {}).get("success_rate", 0),
                "benchmark_results": len(self.benchmark_results)
            }
        }
        
        # Check if we have enough test queries
        if len(self.test_queries) < 5:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient test queries")
        
        # Check success rate
        success_rate = summary.get("overall", {}).get("success_rate", 0)
        if success_rate < 80:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Low success rate: {success_rate:.1f}%")
        
        return health_status
