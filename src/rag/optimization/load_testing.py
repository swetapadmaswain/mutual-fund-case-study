"""
Load Testing Tools for Phase 2.6

Provides comprehensive load testing capabilities to simulate real-world usage patterns and identify system limits.
"""

import asyncio
import time
import json
import random
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

logger = logging.getLogger(__name__)

@dataclass
class LoadTestScenario:
    """Load test scenario definition."""
    name: str
    description: str
    concurrent_users: int
    duration_seconds: int
    ramp_up_time: int
    requests_per_second: int
    request_types: Dict[str, float]  # query_type -> percentage
    think_time: float  # seconds between requests
    timeout: float  # request timeout

@dataclass
class LoadTestResult:
    """Results of a load test."""
    scenario_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    cpu_usage: List[float]
    memory_usage: List[float]
    errors: List[str]

@dataclass
class UserSession:
    """Simulated user session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    requests_made: int
    successful_requests: int
    failed_requests: int
    total_response_time: float
    errors: List[str]

class LoadTesting:
    """
    Comprehensive load testing framework.
    
    Features:
    - Multiple load test scenarios
    - Realistic user simulation
    - Performance metrics collection
    - System resource monitoring
    - Stress testing capabilities
    - Load pattern analysis
    """
    
    def __init__(self, cache_dir: str = "cache/load_testing"):
        """
        Initialize load testing framework.
        
        Args:
            cache_dir: Directory for caching test data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Test storage
        self.scenarios: Dict[str, LoadTestScenario] = {}
        self.test_results: List[LoadTestResult] = []
        self.active_sessions: Dict[str, UserSession] = {}
        
        # Configuration
        self.max_concurrent_users = 1000
        self.default_timeout = 30.0
        self.monitoring_interval = 1.0  # seconds
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.system_metrics: deque = deque(maxlen=3600)  # 1 hour of data
        
        # Query templates for testing
        self.query_templates = self._initialize_query_templates()
        
        # Load existing data
        self._load_scenarios()
        self._load_results()
        
        logger.info("Load Testing framework initialized")
    
    def _initialize_query_templates(self) -> Dict[str, List[str]]:
        """Initialize query templates for testing."""
        return {
            "factual": [
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "What is the minimum SIP amount for HDFC Equity Fund?",
                "What is the NAV of HDFC Focused Fund?",
                "What is the AUM of HDFC Hybrid Fund?",
                "What is the risk level of HDFC Small Cap Fund?"
            ],
            "advisory": [
                "Should I invest in HDFC Mid Cap Fund?",
                "Is HDFC Equity Fund a good investment?",
                "Which HDFC fund should I choose for retirement?",
                "Should I increase my SIP amount?",
                "Is it the right time to invest in mutual funds?"
            ],
            "performance": [
                "What are the historical returns of HDFC Mid Cap Fund?",
                "How has HDFC Equity Fund performed over the last 5 years?",
                "What is the benchmark performance of HDFC Focused Fund?",
                "Compare the performance of HDFC Hybrid vs HDFC Equity",
                "What are the quarterly returns of HDFC Small Cap Fund?"
            ],
            "procedural": [
                "How to start SIP in HDFC Mid Cap Fund?",
                "What is the process to redeem HDFC Equity Fund units?",
                "How to download account statement from HDFC Mutual Fund?",
                "What are the KYC requirements for HDFC Mutual Fund?",
                "How to switch between HDFC Mutual Fund schemes?"
            ],
            "general": [
                "Tell me about HDFC Mutual Fund",
                "What are the different types of HDFC funds?",
                "How does HDFC Mutual Fund work?",
                "What is the history of HDFC Mutual Fund?",
                "Who manages HDFC Mutual Fund?"
            ]
        }
    
    def _load_scenarios(self) -> None:
        """Load test scenarios from cache."""
        scenarios_file = self.cache_dir / "scenarios.json"
        
        if scenarios_file.exists():
            try:
                with open(scenarios_file, 'r') as f:
                    data = json.load(f)
                
                for scenario_name, scenario_data in data.items():
                    self.scenarios[scenario_name] = LoadTestScenario(**scenario_data)
                
                logger.info(f"Loaded {len(self.scenarios)} load test scenarios")
                
            except Exception as e:
                logger.error(f"Error loading scenarios: {e}")
    
    def _load_results(self) -> None:
        """Load test results from cache."""
        results_file = self.cache_dir / "results.json"
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                
                self.test_results = []
                for result_data in data:
                    result_data['start_time'] = datetime.fromisoformat(result_data['start_time'])
                    result_data['end_time'] = datetime.fromisoformat(result_data['end_time'])
                    self.test_results.append(LoadTestResult(**result_data))
                
                logger.info(f"Loaded {len(self.test_results)} test results")
                
            except Exception as e:
                logger.error(f"Error loading results: {e}")
    
    def _save_scenarios(self) -> None:
        """Save test scenarios to cache."""
        try:
            scenarios_file = self.cache_dir / "scenarios.json"
            
            serializable_scenarios = {}
            for scenario_name, scenario in self.scenarios.items():
                serializable_scenarios[scenario_name] = asdict(scenario)
            
            with open(scenarios_file, 'w') as f:
                json.dump(serializable_scenarios, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scenarios: {e}")
    
    def _save_results(self) -> None:
        """Save test results to cache."""
        try:
            results_file = self.cache_dir / "results.json"
            
            serializable_results = []
            for result in self.test_results:
                result_dict = asdict(result)
                result_dict['start_time'] = result.start_time.isoformat()
                result_dict['end_time'] = result.end_time.isoformat()
                serializable_results.append(result_dict)
            
            with open(results_file, 'w') as f:
                json.dump(serializable_results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def create_scenario(self, name: str, description: str, concurrent_users: int,
                       duration_seconds: int, ramp_up_time: int, requests_per_second: int,
                       request_types: Dict[str, float], think_time: float = 1.0,
                       timeout: float = 30.0) -> LoadTestScenario:
        """
        Create a load test scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration in seconds
            ramp_up_time: Ramp up time in seconds
            requests_per_second: Target requests per second
            request_types: Distribution of request types
            think_time: Time between requests
            timeout: Request timeout
            
        Returns:
            Created LoadTestScenario
        """
        scenario = LoadTestScenario(
            name=name,
            description=description,
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            ramp_up_time=ramp_up_time,
            requests_per_second=requests_per_second,
            request_types=request_types,
            think_time=think_time,
            timeout=timeout
        )
        
        self.scenarios[name] = scenario
        self._save_scenarios()
        
        logger.info(f"Created load test scenario: {name}")
        return scenario
    
    def get_predefined_scenarios(self) -> Dict[str, LoadTestScenario]:
        """Get predefined load test scenarios."""
        return {
            "light_load": self.create_scenario(
                name="light_load",
                description="Light load test with 10 concurrent users",
                concurrent_users=10,
                duration_seconds=60,
                ramp_up_time=10,
                requests_per_second=5,
                request_types={"factual": 0.6, "advisory": 0.1, "performance": 0.2, "procedural": 0.1}
            ),
            "moderate_load": self.create_scenario(
                name="moderate_load",
                description="Moderate load test with 50 concurrent users",
                concurrent_users=50,
                duration_seconds=300,
                ramp_up_time=30,
                requests_per_second=25,
                request_types={"factual": 0.5, "advisory": 0.15, "performance": 0.25, "procedural": 0.1}
            ),
            "heavy_load": self.create_scenario(
                name="heavy_load",
                description="Heavy load test with 200 concurrent users",
                concurrent_users=200,
                duration_seconds=600,
                ramp_up_time=60,
                requests_per_second=100,
                request_types={"factual": 0.4, "advisory": 0.2, "performance": 0.3, "procedural": 0.1}
            ),
            "stress_test": self.create_scenario(
                name="stress_test",
                description="Stress test with 500 concurrent users",
                concurrent_users=500,
                duration_seconds=300,
                ramp_up_time=120,
                requests_per_second=250,
                request_types={"factual": 0.3, "advisory": 0.25, "performance": 0.35, "procedural": 0.1}
            ),
            "endurance_test": self.create_scenario(
                name="endurance_test",
                description="Endurance test for 1 hour",
                concurrent_users=100,
                duration_seconds=3600,
                ramp_up_time=300,
                requests_per_second=50,
                request_types={"factual": 0.45, "advisory": 0.15, "performance": 0.3, "procedural": 0.1}
            )
        }
    
    async def run_load_test(self, scenario_name: str, simulate_system: bool = True) -> LoadTestResult:
        """
        Run a load test scenario.
        
        Args:
            scenario_name: Name of scenario to run
            simulate_system: Whether to simulate system responses
            
        Returns:
            LoadTestResult with test results
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario not found: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        logger.info(f"Starting load test: {scenario_name}")
        
        # Start monitoring
        self.start_monitoring()
        
        # Initialize test state
        start_time = datetime.now()
        self.active_sessions.clear()
        
        try:
            # Execute load test
            await self._execute_load_test(scenario, simulate_system)
            
        except Exception as e:
            logger.error(f"Load test failed: {e}")
            raise
        
        finally:
            # Stop monitoring
            self.stop_monitoring()
        
        end_time = datetime.now()
        
        # Calculate results
        result = self._calculate_test_results(scenario_name, start_time, end_time)
        
        # Store result
        self.test_results.append(result)
        self._save_results()
        
        logger.info(f"Load test completed: {scenario_name}")
        return result
    
    async def _execute_load_test(self, scenario: LoadTestScenario, simulate_system: bool) -> None:
        """Execute the load test."""
        # Create user sessions
        session_tasks = []
        
        for user_id in range(scenario.concurrent_users):
            session_id = f"session_{scenario.name}_{user_id}"
            session = UserSession(
                session_id=session_id,
                start_time=datetime.now(),
                end_time=None,
                requests_made=0,
                successful_requests=0,
                failed_requests=0,
                total_response_time=0.0,
                errors=[]
            )
            
            self.active_sessions[session_id] = session
            
            # Create task for this user
            task = asyncio.create_task(
                self._simulate_user_session(session, scenario, simulate_system)
            )
            session_tasks.append(task)
            
            # Ramp up delay
            if scenario.ramp_up_time > 0:
                await asyncio.sleep(scenario.ramp_up_time / scenario.concurrent_users)
        
        # Wait for all sessions to complete
        await asyncio.gather(*session_tasks, return_exceptions=True)
    
    async def _simulate_user_session(self, session: UserSession, scenario: LoadTestScenario, 
                                   simulate_system: bool) -> None:
        """Simulate a single user session."""
        end_time = session.start_time + timedelta(seconds=scenario.duration_seconds)
        
        while datetime.now() < end_time:
            try:
                # Generate request
                query = self._generate_query(scenario.request_types)
                
                # Make request
                start_request = time.time()
                
                if simulate_system:
                    response = await self._simulate_system_response(query, scenario.timeout)
                else:
                    # Simulate response time
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                    response = {"status": "success", "response_time": time.time() - start_request}
                
                # Update session stats
                session.requests_made += 1
                session.total_response_time += response.get("response_time", 0.0)
                
                if response.get("status") == "success":
                    session.successful_requests += 1
                else:
                    session.failed_requests += 1
                    session.errors.append(response.get("error", "Unknown error"))
                
                # Think time
                await asyncio.sleep(scenario.think_time)
                
            except Exception as e:
                session.failed_requests += 1
                session.errors.append(str(e))
                await asyncio.sleep(1.0)  # Brief pause on error
        
        session.end_time = datetime.now()
    
    def _generate_query(self, request_types: Dict[str, float]) -> str:
        """Generate a random query based on request type distribution."""
        # Select query type based on distribution
        query_type = random.choices(
            list(request_types.keys()),
            weights=list(request_types.values())
        )[0]
        
        # Select random query from that type
        queries = self.query_templates.get(query_type, ["Default query"])
        return random.choice(queries)
    
    async def _simulate_system_response(self, query: str, timeout: float) -> Dict[str, Any]:
        """Simulate system response to a query."""
        try:
            # Simulate processing time based on query complexity
            processing_time = random.uniform(0.3, 2.5)
            
            if processing_time > timeout:
                return {
                    "status": "error",
                    "error": "Request timeout",
                    "response_time": timeout
                }
            
            # Simulate occasional errors
            if random.random() < 0.05:  # 5% error rate
                return {
                    "status": "error",
                    "error": "Simulated system error",
                    "response_time": processing_time
                }
            
            await asyncio.sleep(processing_time)
            
            return {
                "status": "success",
                "response_time": processing_time,
                "query": query
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": 0.0
            }
    
    def _calculate_test_results(self, scenario_name: str, start_time: datetime, 
                               end_time: datetime) -> LoadTestResult:
        """Calculate test results from session data."""
        total_requests = sum(session.requests_made for session in self.active_sessions.values())
        successful_requests = sum(session.successful_requests for session in self.active_sessions.values())
        failed_requests = sum(session.failed_requests for session in self.active_sessions.values())
        
        # Response time statistics
        all_response_times = []
        for session in self.active_sessions.values():
            if session.successful_requests > 0:
                avg_time = session.total_response_time / session.successful_requests
                all_response_times.extend([avg_time] * session.successful_requests)
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(all_response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0.0
        
        # Calculate requests per second
        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0.0
        
        # Error rate
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
        
        # System metrics
        cpu_usage = [metric["cpu"] for metric in self.system_metrics] if self.system_metrics else []
        memory_usage = [metric["memory"] for metric in self.system_metrics] if self.system_metrics else []
        
        # Collect all errors
        all_errors = []
        for session in self.active_sessions.values():
            all_errors.extend(session.errors)
        
        return LoadTestResult(
            scenario_name=scenario_name,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            errors=all_errors[:100]  # Limit to first 100 errors
        )
    
    def start_monitoring(self) -> None:
        """Start system monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("System monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                
                metric = {
                    "timestamp": datetime.now(),
                    "cpu": cpu_percent,
                    "memory": memory_percent
                }
                
                self.system_metrics.append(metric)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_test_summary(self, scenario_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of test results.
        
        Args:
            scenario_name: Specific scenario to summarize (optional)
            
        Returns:
            Test summary dictionary
        """
        results = self.test_results
        
        if scenario_name:
            results = [r for r in results if r.scenario_name == scenario_name]
        
        if not results:
            return {"message": "No test results available"}
        
        # Calculate aggregates
        total_requests = sum(r.total_requests for r in results)
        successful_requests = sum(r.successful_requests for r in results)
        failed_requests = sum(r.failed_requests for r in results)
        
        response_times = [r.average_response_time for r in results]
        requests_per_second = [r.requests_per_second for r in results]
        error_rates = [r.error_rate for r in results]
        
        return {
            "summary": {
                "total_tests": len(results),
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "overall_success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "average_response_time": statistics.mean(response_times) if response_times else 0.0,
                "average_requests_per_second": statistics.mean(requests_per_second) if requests_per_second else 0.0,
                "average_error_rate": statistics.mean(error_rates) if error_rates else 0.0
            },
            "by_scenario": {
                scenario_name: {
                    "tests": len([r for r in self.test_results if r.scenario_name == scenario_name]),
                    "avg_response_time": statistics.mean([r.average_response_time for r in self.test_results if r.scenario_name == scenario_name]),
                    "avg_requests_per_second": statistics.mean([r.requests_per_second for r in self.test_results if r.scenario_name == scenario_name]),
                    "avg_error_rate": statistics.mean([r.error_rate for r in self.test_results if r.scenario_name == scenario_name])
                }
                for scenario_name in set(r.scenario_name for r in self.test_results)
            }
        }
    
    def get_performance_report(self, scenario_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed performance report.
        
        Args:
            scenario_name: Specific scenario to report on (optional)
            
        Returns:
            Performance report dictionary
        """
        results = self.test_results
        
        if scenario_name:
            results = [r for r in results if r.scenario_name == scenario_name]
        
        if not results:
            return {"message": "No test results available"}
        
        # Performance metrics
        response_times = [r.average_response_time for r in results]
        p95_times = [r.p95_response_time for r in results]
        p99_times = [r.p99_response_time for r in results]
        rps_values = [r.requests_per_second for r in results]
        
        # System resource usage
        all_cpu = []
        all_memory = []
        for result in results:
            all_cpu.extend(result.cpu_usage)
            all_memory.extend(result.memory_usage)
        
        return {
            "performance_metrics": {
                "response_time": {
                    "average": statistics.mean(response_times) if response_times else 0.0,
                    "min": min(response_times) if response_times else 0.0,
                    "max": max(response_times) if response_times else 0.0,
                    "p95": statistics.mean(p95_times) if p95_times else 0.0,
                    "p99": statistics.mean(p99_times) if p99_times else 0.0
                },
                "throughput": {
                    "average_rps": statistics.mean(rps_values) if rps_values else 0.0,
                    "min_rps": min(rps_values) if rps_values else 0.0,
                    "max_rps": max(rps_values) if rps_values else 0.0
                },
                "system_resources": {
                    "cpu_usage": {
                        "average": statistics.mean(all_cpu) if all_cpu else 0.0,
                        "max": max(all_cpu) if all_cpu else 0.0,
                        "min": min(all_cpu) if all_cpu else 0.0
                    },
                    "memory_usage": {
                        "average": statistics.mean(all_memory) if all_memory else 0.0,
                        "max": max(all_memory) if all_memory else 0.0,
                        "min": min(all_memory) if all_memory else 0.0
                    }
                }
            },
            "test_count": len(results),
            "last_updated": max([r.end_time for r in results]) if results else None
        }
    
    def compare_scenarios(self, scenario_names: List[str]) -> Dict[str, Any]:
        """
        Compare performance between scenarios.
        
        Args:
            scenario_names: List of scenario names to compare
            
        Returns:
            Comparison report
        """
        comparison = {}
        
        for scenario_name in scenario_names:
            results = [r for r in self.test_results if r.scenario_name == scenario_name]
            
            if results:
                comparison[scenario_name] = {
                    "avg_response_time": statistics.mean([r.average_response_time for r in results]),
                    "avg_requests_per_second": statistics.mean([r.requests_per_second for r in results]),
                    "avg_error_rate": statistics.mean([r.error_rate for r in results]),
                    "total_requests": sum([r.total_requests for r in results])
                }
        
        # Find best and worst performers
        if comparison:
            best_response_time = min(comparison.items(), key=lambda x: x[1]["avg_response_time"])
            worst_response_time = max(comparison.items(), key=lambda x: x[1]["avg_response_time"])
            
            best_throughput = max(comparison.items(), key=lambda x: x[1]["avg_requests_per_second"])
            worst_throughput = min(comparison.items(), key=lambda x: x[1]["avg_requests_per_second"])
            
            return {
                "scenarios": comparison,
                "rankings": {
                    "fastest_response": best_response_time[0],
                    "slowest_response": worst_response_time[0],
                    "highest_throughput": best_throughput[0],
                    "lowest_throughput": worst_throughput[0]
                }
            }
        
        return {"message": "No comparison data available"}
    
    def generate_load_test_report(self, scenario_name: str, format_type: str = "json") -> str:
        """
        Generate comprehensive load test report.
        
        Args:
            scenario_name: Scenario name
            format_type: Format type ("json", "html", "markdown")
            
        Returns:
            Formatted report string
        """
        results = [r for r in self.test_results if r.scenario_name == scenario_name]
        
        if not results:
            return f"No results found for scenario: {scenario_name}"
        
        summary = self.get_test_summary(scenario_name)
        performance = self.get_performance_report(scenario_name)
        
        if format_type == "json":
            report_data = {
                "scenario": scenario_name,
                "summary": summary,
                "performance": performance,
                "detailed_results": [asdict(result) for result in results],
                "generated_at": datetime.now().isoformat()
            }
            return json.dumps(report_data, indent=2, default=str)
        
        elif format_type == "markdown":
            return self._generate_markdown_report(scenario_name, summary, performance, results)
        
        elif format_type == "html":
            return self._generate_html_report(scenario_name, summary, performance, results)
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _generate_markdown_report(self, scenario_name: str, summary: Dict[str, Any], 
                                   performance: Dict[str, Any], results: List[LoadTestResult]) -> str:
        """Generate markdown load test report."""
        report = []
        
        # Header
        report.append(f"# Load Test Report: {scenario_name}")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        summary_data = summary["summary"]
        report.append(f"- **Total Tests**: {summary_data['total_tests']}")
        report.append(f"- **Total Requests**: {summary_data['total_requests']}")
        report.append(f"- **Successful Requests**: {summary_data['successful_requests']}")
        report.append(f"- **Failed Requests**: {summary_data['failed_requests']}")
        report.append(f"- **Success Rate**: {summary_data['overall_success_rate']:.1f}%")
        report.append(f"- **Average Response Time**: {summary_data['average_response_time']:.3f}s")
        report.append(f"- **Average Requests/sec**: {summary_data['average_requests_per_second']:.1f}")
        report.append(f"- **Average Error Rate**: {summary_data['average_error_rate']:.1f}%")
        report.append("")
        
        # Performance Metrics
        if "performance_metrics" in performance:
            perf = performance["performance_metrics"]
            report.append("## Performance Metrics")
            
            # Response Time
            rt = perf["response_time"]
            report.append("### Response Time")
            report.append(f"- **Average**: {rt['average']:.3f}s")
            report.append(f"- **Min**: {rt['min']:.3f}s")
            report.append(f"- **Max**: {rt['max']:.3f}s")
            report.append(f"- **95th Percentile**: {rt['p95']:.3f}s")
            report.append(f"- **99th Percentile**: {rt['p99']:.3f}s")
            report.append("")
            
            # Throughput
            tp = perf["throughput"]
            report.append("### Throughput")
            report.append(f"- **Average RPS**: {tp['average_rps']:.1f}")
            report.append(f"- **Min RPS**: {tp['min_rps']:.1f}")
            report.append(f"- **Max RPS**: {tp['max_rps']:.1f}")
            report.append("")
            
            # System Resources
            sr = perf["system_resources"]
            report.append("### System Resources")
            report.append(f"- **CPU Usage**: Avg {sr['cpu_usage']['average']:.1f}%, Max {sr['cpu_usage']['max']:.1f}%")
            report.append(f"- **Memory Usage**: Avg {sr['memory_usage']['average']:.1f}%, Max {sr['memory_usage']['max']:.1f}%")
            report.append("")
        
        # Individual Test Results
        report.append("## Individual Test Results")
        for i, result in enumerate(results[:5]):  # Limit to first 5
            report.append(f"### Test {i+1}")
            report.append(f"- **Start Time**: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"- **End Time**: {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"- **Total Requests**: {result.total_requests}")
            report.append(f"- **Success Rate**: {(result.successful_requests / result.total_requests * 100):.1f}%")
            report.append(f"- **Avg Response Time**: {result.average_response_time:.3f}s")
            report.append(f"- **Requests/sec**: {result.requests_per_second:.1f}")
            report.append(f"- **Error Rate**: {result.error_rate:.1f}%")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_html_report(self, scenario_name: str, summary: Dict[str, Any], 
                             performance: Dict[str, Any], results: List[LoadTestResult]) -> str:
        """Generate HTML load test report."""
        summary_data = summary["summary"]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report: {scenario_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ margin: 10px 0; }}
        .metric-value {{ font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Load Test Report: {scenario_name}</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric"><span class="metric-value">Total Tests:</span> {summary_data['total_tests']}</div>
        <div class="metric"><span class="metric-value">Total Requests:</span> {summary_data['total_requests']}</div>
        <div class="metric"><span class="metric-value">Successful Requests:</span> {summary_data['successful_requests']}</div>
        <div class="metric"><span class="metric-value">Success Rate:</span> {summary_data['overall_success_rate']:.1f}%</div>
        <div class="metric"><span class="metric-value">Average Response Time:</span> {summary_data['average_response_time']:.3f}s</div>
        <div class="metric"><span class="metric-value">Average Requests/sec:</span> {summary_data['average_requests_per_second']:.1f}</div>
        <div class="metric"><span class="metric-value">Average Error Rate:</span> {summary_data['average_error_rate']:.1f}%</div>
    </div>
    
    {self._generate_performance_html(performance)}
    
    <h2>Test Results</h2>
    <table>
        <tr><th>Test #</th><th>Start Time</th><th>End Time</th><th>Requests</th><th>Success Rate</th><th>Avg Response Time</th><th>Requests/sec</th><th>Error Rate</th></tr>
        {self._generate_results_table_html(results)}
    </table>
    
</body>
</html>
        """
        
        return html
    
    def _generate_performance_html(self, performance: Dict[str, Any]) -> str:
        """Generate HTML section for performance metrics."""
        if "performance_metrics" not in performance:
            return ""
        
        perf = performance["performance_metrics"]
        
        html = "<h2>Performance Metrics</h2>"
        
        # Response Time
        rt = perf["response_time"]
        html += "<h3>Response Time</h3>"
        html += f"<p><strong>Average:</strong> {rt['average']:.3f}s</p>"
        html += f"<p><strong>Min:</strong> {rt['min']:.3f}s</p>"
        html += f"<p><strong>Max:</strong> {rt['max']:.3f}s</p>"
        html += f"<p><strong>95th Percentile:</strong> {rt['p95']:.3f}s</p>"
        html += f"<p><strong>99th Percentile:</strong> {rt['p99']:.3f}s</p>"
        
        # Throughput
        tp = perf["throughput"]
        html += "<h3>Throughput</h3>"
        html += f"<p><strong>Average RPS:</strong> {tp['average_rps']:.1f}</p>"
        html += f"<p><strong>Min RPS:</strong> {tp['min_rps']:.1f}</p>"
        html += f"<p><strong>Max RPS:</strong> {tp['max_rps']:.1f}</p>"
        
        # System Resources
        sr = perf["system_resources"]
        html += "<h3>System Resources</h3>"
        html += f"<p><strong>CPU Usage:</strong> Avg {sr['cpu_usage']['average']:.1f}%, Max {sr['cpu_usage']['max']:.1f}%</p>"
        html += f"<p><strong>Memory Usage:</strong> Avg {sr['memory_usage']['average']:.1f}%, Max {sr['memory_usage']['max']:.1f}%</p>"
        
        return html
    
    def _generate_results_table_html(self, results: List[LoadTestResult]) -> str:
        """Generate HTML table for test results."""
        rows = []
        
        for i, result in enumerate(results[:10]):  # Limit to first 10
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            row = f"<tr><td>{i+1}</td><td>{result.start_time.strftime('%Y-%m-%d %H:%M:%S')}</td>"
            row += f"<td>{result.end_time.strftime('%Y-%m-%d %H:%M:%S')}</td><td>{result.total_requests}</td>"
            row += f"<td>{success_rate:.1f}%</td><td>{result.average_response_time:.3f}s</td>"
            row += f"<td>{result.requests_per_second:.1f}</td><td>{result.error_rate:.1f}%</td></tr>"
            rows.append(row)
        
        return "\n".join(rows)
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old test data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_results = [
            result for result in self.test_results
            if result.end_time < cutoff_date
        ]
        
        # Remove old results
        self.test_results = [
            result for result in self.test_results
            if result.end_time >= cutoff_date
        ]
        
        # Save updated results
        self._save_results()
        
        logger.info(f"Cleaned up {len(old_results)} old test results")
        return len(old_results)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on load testing system.
        
        Returns:
            Health status dictionary
        """
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "scenarios_available": len(self.scenarios),
                "test_results": len(self.test_results),
                "monitoring_active": self.monitoring_active,
                "system_metrics_collected": len(self.system_metrics)
            }
        }
        
        # Check if we have scenarios
        if not self.scenarios:
            health_status["status"] = "degraded"
            health_status["issues"].append("No load test scenarios available")
        
        # Check if monitoring is working
        if self.monitoring_active and len(self.system_metrics) == 0:
            health_status["status"] = "degraded"
            health_status["issues"].append("Monitoring is active but no metrics collected")
        
        return health_status
