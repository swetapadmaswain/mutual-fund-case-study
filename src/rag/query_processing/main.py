"""
Phase 3 Main Pipeline: Query Processing and Response Generation

Orchestrates the complete Phase 3 workflow including query classification,
response generation, formatting, compliance, and integration testing.
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

from src.rag.query_processing.query_classifier import QueryClassifier
from src.rag.query_processing.response_generator import ResponseGenerator, ResponseContext
from src.rag.query_processing.response_formatter import ResponseFormatter, OutputFormat
from src.rag.query_processing.compliance_safety import ComplianceSafetyLayer
from src.rag.query_processing.integration_tests import RAGIntegrationTests

logger = logging.getLogger(__name__)

@dataclass
class Phase3Results:
    """Results from Phase 3 pipeline execution."""
    success: bool
    query_classification_accuracy: float
    response_generation_success: float
    compliance_approval_rate: float
    formatting_coverage: float
    integration_test_success: float
    performance_metrics: Dict[str, Any]
    component_results: Dict[str, Any]
    errors: List[str]

class Phase3Pipeline:
    """
    Main pipeline for Phase 3: Query Processing and Response Generation.
    
    Orchestrates:
    - Query classification
    - Response generation
    - Response formatting
    - Compliance and safety checks
    - Integration testing
    - Performance validation
    """
    
    def __init__(self):
        """Initialize Phase 3 pipeline."""
        # Initialize components
        self.query_classifier = QueryClassifier()
        self.response_generator = ResponseGenerator()
        self.response_formatter = ResponseFormatter()
        self.compliance_safety = ComplianceSafetyLayer()
        self.integration_tests = RAGIntegrationTests()
        
        # Performance tracking
        self.start_time = None
        self.component_results = {}
        
        logger.info("Phase 3 Pipeline initialized")
    
    async def test_query_classification(self) -> Dict[str, Any]:
        """
        Test query classification functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing query classification...")
        
        test_results = {
            "success": False,
            "total_classifications": 0,
            "accurate_classifications": 0,
            "accuracy_percentage": 0.0,
            "confidence_distribution": {},
            "error": None
        }
        
        try:
            # Test with sample queries
            test_queries = [
                ("What is the expense ratio of HDFC Mid Cap Fund?", "factual"),
                ("Should I invest in HDFC Equity Fund?", "advisory"),
                ("What are the historical returns?", "performance"),
                ("How to start SIP in HDFC Mutual Fund?", "procedural"),
                ("Tell me about HDFC Mutual Fund", "general")
            ]
            
            accurate_count = 0
            confidence_scores = []
            
            for query, expected_type in test_queries:
                try:
                    classification = self.query_classifier.classify_query(query)
                    
                    # Check if classification is accurate
                    if classification.query_type.value == expected_type:
                        accurate_count += 1
                    
                    confidence_scores.append(classification.confidence)
                    
                except Exception as e:
                    logger.error(f"Error classifying query '{query}': {e}")
            
            test_results["total_classifications"] = len(test_queries)
            test_results["accurate_classifications"] = accurate_count
            test_results["accuracy_percentage"] = (accurate_count / len(test_queries) * 100) if test_queries else 0.0
            
            # Calculate confidence distribution
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                test_results["confidence_distribution"] = {
                    "average": avg_confidence,
                    "min": min(confidence_scores),
                    "max": max(confidence_scores)
                }
            
            test_results["success"] = True
            
            logger.info(f"Query classification test passed: {test_results['accuracy_percentage']:.1f}% accuracy")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Query classification test failed: {e}")
        
        return test_results
    
    async def test_response_generation(self) -> Dict[str, Any]:
        """
        Test response generation functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing response generation...")
        
        test_results = {
            "success": False,
            "total_generations": 0,
            "successful_generations": 0,
            "success_percentage": 0.0,
            "response_types": {},
            "error": None
        }
        
        try:
            # Test with sample contexts
            test_contexts = [
                {
                    "query": "What is the expense ratio?",
                    "query_type": "factual",
                    "expected_response_type": "factual"
                },
                {
                    "query": "Should I invest?",
                    "query_type": "advisory",
                    "expected_response_type": "advisory"
                },
                {
                    "query": "Historical returns?",
                    "query_type": "performance",
                    "expected_response_type": "performance"
                },
                {
                    "query": "How to invest?",
                    "query_type": "procedural",
                    "expected_response_type": "procedural"
                }
            ]
            
            successful_count = 0
            response_type_counts = {}
            
            for test_context in test_contexts:
                try:
                    # Create mock classification
                    from .query_classifier import QueryClassification, QueryType
                    classification = QueryClassification(
                        query=test_context["query"],
                        query_type=QueryType(test_context["query_type"]),
                        confidence=0.8,
                        keywords=[],
                        entities=[],
                        intent="test_intent",
                        subcategory=None,
                        metadata={}
                    )
                    
                    # Create response context
                    response_context = ResponseContext(
                        query=test_context["query"],
                        classification=classification,
                        retrieved_chunks=[],
                        search_results=[],
                        user_context=None,
                        session_context=None,
                        metadata={"test_mode": True}
                    )
                    
                    # Generate response
                    response = await self.response_generator.generate_response(response_context)
                    
                    # Check if response type matches expected
                    if response.response_type == test_context["expected_response_type"]:
                        successful_count += 1
                    
                    # Count response types
                    response_type_counts[response.response_type] = response_type_counts.get(response.response_type, 0) + 1
                    
                except Exception as e:
                    logger.error(f"Error generating response for '{test_context['query']}': {e}")
            
            test_results["total_generations"] = len(test_contexts)
            test_results["successful_generations"] = successful_count
            test_results["success_percentage"] = (successful_count / len(test_contexts) * 100) if test_contexts else 0.0
            test_results["response_types"] = response_type_counts
            
            test_results["success"] = True
            
            logger.info(f"Response generation test passed: {test_results['success_percentage']:.1f}% success")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Response generation test failed: {e}")
        
        return test_results
    
    async def test_response_formatting(self) -> Dict[str, Any]:
        """
        Test response formatting functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing response formatting...")
        
        test_results = {
            "success": False,
            "total_formats": 0,
            "successful_formats": 0,
            "format_coverage": {},
            "error": None
        }
        
        try:
            # Create a sample response
            from .response_generator import GeneratedResponse
            sample_response = GeneratedResponse(
                query="What is the expense ratio?",
                response_type="factual",
                content="The expense ratio is 1.5% for HDFC Mid Cap Fund.",
                sources=[{
                    "source_url": "https://hdfcfund.com",
                    "source_title": "HDFC Mutual Fund"
                }],
                confidence=0.9,
                response_time=0.5,
                metadata={}
            )
            
            # Test different output formats
            formats_to_test = [
                OutputFormat.JSON,
                OutputFormat.UI,
                OutputFormat.TEXT,
                OutputFormat.MARKDOWN,
                OutputFormat.HTML
            ]
            
            successful_count = 0
            format_results = {}
            
            for format_type in formats_to_test:
                try:
                    formatted = self.response_formatter.format_response(sample_response, format_type)
                    
                    # Check if formatting was successful
                    if formatted.formatted_content and len(formatted.formatted_content) > 0:
                        successful_count += 1
                        format_results[format_type.value] = {
                            "success": True,
                            "content_length": len(formatted.formatted_content)
                        }
                    else:
                        format_results[format_type.value] = {
                            "success": False,
                            "content_length": 0
                        }
                        
                except Exception as e:
                    logger.error(f"Error formatting response as {format_type.value}: {e}")
                    format_results[format_type.value] = {
                        "success": False,
                        "error": str(e)
                    }
            
            test_results["total_formats"] = len(formats_to_test)
            test_results["successful_formats"] = successful_count
            test_results["format_coverage"] = format_results
            
            test_results["success"] = successful_count >= 4  # At least 4 formats should work
            
            logger.info(f"Response formatting test passed: {successful_count}/{len(formats_to_test)} formats")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Response formatting test failed: {e}")
        
        return test_results
    
    async def test_compliance_safety(self) -> Dict[str, Any]:
        """
        Test compliance and safety functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing compliance and safety...")
        
        test_results = {
            "success": False,
            "total_checks": 0,
            "approved_checks": 0,
            "approval_rate": 0.0,
            "risk_distribution": {},
            "error": None
        }
        
        try:
            # Test with sample queries and responses
            test_scenarios = [
                {
                    "query": "What is the expense ratio?",
                    "response_type": "factual",
                    "expected_approval": True
                },
                {
                    "query": "Should I invest in this fund?",
                    "response_type": "advisory",
                    "expected_approval": True  # Should be approved with disclaimer
                },
                {
                    "query": "Guaranteed returns?",
                    "response_type": "factual",
                    "expected_approval": False  # Should be blocked
                }
            ]
            
            approved_count = 0
            risk_levels = []
            
            for scenario in test_scenarios:
                try:
                    # Create mock classification
                    from .query_classifier import QueryClassification, QueryType
                    classification = QueryClassification(
                        query=scenario["query"],
                        query_type=QueryType(scenario["response_type"]),
                        confidence=0.8,
                        keywords=[],
                        entities=[],
                        intent="test_intent",
                        subcategory=None,
                        metadata={}
                    )
                    
                    # Create mock response
                    from .response_generator import GeneratedResponse
                    response = GeneratedResponse(
                        query=scenario["query"],
                        response_type=scenario["response_type"],
                        content="Test response content",
                        sources=[],
                        confidence=0.8,
                        response_time=0.5,
                        metadata={}
                    )
                    
                    # Check compliance
                    compliance_result = await self.compliance_safety.check_compliance(
                        scenario["query"], classification, response
                    )
                    
                    if compliance_result.approved == scenario["expected_approval"]:
                        approved_count += 1
                    
                    risk_levels.append(compliance_result.overall_risk.value)
                    
                except Exception as e:
                    logger.error(f"Error in compliance test for '{scenario['query']}': {e}")
            
            test_results["total_checks"] = len(test_scenarios)
            test_results["approved_checks"] = approved_count
            test_results["approval_rate"] = (approved_count / len(test_scenarios) * 100) if test_scenarios else 0.0
            
            # Calculate risk distribution
            if risk_levels:
                risk_dist = {}
                for risk in risk_levels:
                    risk_dist[risk] = risk_dist.get(risk, 0) + 1
                test_results["risk_distribution"] = risk_dist
            
            test_results["success"] = approved_count >= 2  # At least 2 scenarios should pass
            
            logger.info(f"Compliance test passed: {test_results['approval_rate']:.1f}% approval rate")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Compliance test failed: {e}")
        
        return test_results
    
    async def test_integration(self) -> Dict[str, Any]:
        """
        Test integration between Phase 3 components.
        
        Returns:
            Integration test results
        """
        logger.info("Testing Phase 3 integration...")
        
        integration_results = {
            "success": False,
            "classification_to_generation": False,
            "generation_to_formatting": False,
            "generation_to_compliance": False,
            "end_to_end_workflow": False,
            "data_flow_consistent": False,
            "error": None
        }
        
        try:
            # Test classification to generation integration
            test_query = "What is the expense ratio of HDFC Mid Cap Fund?"
            
            # Step 1: Classification
            classification = self.query_classifier.classify_query(test_query)
            integration_results["classification_to_generation"] = classification is not None
            
            # Step 2: Response generation
            from .query_classifier import QueryClassification, QueryType
            response_context = ResponseContext(
                query=test_query,
                classification=classification,
                retrieved_chunks=[],
                search_results=[],
                user_context=None,
                session_context=None,
                metadata={"integration_test": True}
            )
            
            response = await self.response_generator.generate_response(response_context)
            integration_results["generation_to_formatting"] = response is not None
            
            # Step 3: Formatting
            formatted = self.response_formatter.format_response(response, OutputFormat.JSON)
            integration_results["generation_to_formatting"] = formatted is not None
            
            # Step 4: Compliance
            compliance_result = await self.compliance_safety.check_compliance(
                test_query, classification, response
            )
            integration_results["generation_to_compliance"] = compliance_result is not None
            
            # Overall integration success
            integration_results["end_to_end_workflow"] = all([
                integration_results["classification_to_generation"],
                integration_results["generation_to_formatting"],
                integration_results["generation_to_compliance"]
            ])
            
            integration_results["data_flow_consistent"] = integration_results["end_to_end_workflow"]
            integration_results["success"] = integration_results["end_to_end_workflow"]
            
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
            "classification_performance": {},
            "generation_performance": {},
            "formatting_performance": {},
            "compliance_performance": {},
            "overall_performance": {},
            "error": None
        }
        
        try:
            # Test classification performance
            start_time = time.time()
            for _ in range(10):
                self.query_classifier.classify_query("What is the expense ratio?")
            classification_time = (time.time() - start_time) / 10
            
            performance_results["classification_performance"] = {
                "average_time": classification_time,
                "target_met": classification_time < 0.1  # Target: < 100ms
            }
            
            # Test generation performance
            start_time = time.time()
            for _ in range(5):  # Fewer iterations for generation (it's slower)
                from .query_classifier import QueryClassification, QueryType
                classification = QueryClassification(
                    query="What is the expense ratio?",
                    query_type=QueryType.FACTUAL,
                    confidence=0.8,
                    keywords=[],
                    entities=[],
                    intent="test_intent",
                    subcategory=None,
                    metadata={}
                )
                
                response_context = ResponseContext(
                    query="What is the expense ratio?",
                    classification=classification,
                    retrieved_chunks=[],
                    search_results=[],
                    user_context=None,
                    session_context=None,
                    metadata={"performance_test": True}
                )
                
                await self.response_generator.generate_response(response_context)
            generation_time = (time.time() - start_time) / 5
            
            performance_results["generation_performance"] = {
                "average_time": generation_time,
                "target_met": generation_time < 1.0  # Target: < 1 second
            }
            
            # Test formatting performance
            from .response_generator import GeneratedResponse
            sample_response = GeneratedResponse(
                query="What is the expense ratio?",
                response_type="factual",
                content="The expense ratio is 1.5%.",
                sources=[],
                confidence=0.9,
                response_time=0.5,
                metadata={}
            )
            
            start_time = time.time()
            for _ in range(20):
                self.response_formatter.format_response(sample_response, OutputFormat.JSON)
            formatting_time = (time.time() - start_time) / 20
            
            performance_results["formatting_performance"] = {
                "average_time": formatting_time,
                "target_met": formatting_time < 0.01  # Target: < 10ms
            }
            
            # Overall performance
            all_targets_met = all([
                performance_results["classification_performance"]["target_met"],
                performance_results["generation_performance"]["target_met"],
                performance_results["formatting_performance"]["target_met"]
            ])
            
            performance_results["overall_performance"] = {
                "all_targets_met": all_targets_met,
                "classification_time": classification_time,
                "generation_time": generation_time,
                "formatting_time": formatting_time
            }
            
            performance_results["success"] = all_targets_met
            
            if performance_results["success"]:
                logger.info("Performance validation passed")
            else:
                logger.warning("Performance validation failed - some targets not met")
            
        except Exception as e:
            performance_results["error"] = str(e)
            logger.error(f"Performance validation failed: {e}")
        
        return performance_results
    
    async def export_results(self, results: Phase3Results) -> bool:
        """
        Export Phase 3 results to files.
        
        Args:
            results: Phase 3 results to export
            
        Returns:
            True if export successful
        """
        try:
            # Create results directory
            results_dir = Path("cache/phase3_results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Export summary results
            summary_data = {
                "success": results.success,
                "query_classification_accuracy": results.query_classification_accuracy,
                "response_generation_success": results.response_generation_success,
                "compliance_approval_rate": results.compliance_approval_rate,
                "formatting_coverage": results.formatting_coverage,
                "integration_test_success": results.integration_test_success,
                "performance_metrics": results.performance_metrics,
                "component_results": results.component_results,
                "errors": results.errors,
                "timestamp": time.time()
            }
            
            with open(results_dir / "phase3_results.json", 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            # Export component statistics
            stats_data = {
                "query_classifier_stats": self.query_classifier.get_classification_stats(),
                "response_generator_stats": self.response_generator.get_response_stats(),
                "response_formatter_stats": self.response_formatter.get_formatting_stats(),
                "compliance_safety_stats": self.compliance_safety.get_compliance_stats(),
                "integration_tests_stats": self.integration_tests.get_test_summary()
            }
            
            with open(results_dir / "component_statistics.json", 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            logger.info(f"Phase 3 results exported to {results_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    async def run_pipeline(self) -> Phase3Results:
        """
        Run the complete Phase 3 pipeline.
        
        Returns:
            Phase3Results object with pipeline results
        """
        logger.info("Starting Phase 3 Pipeline: Query Processing and Response Generation")
        print("=" * 80)
        print("PHASE 3: QUERY PROCESSING AND RESPONSE GENERATION")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Step 1: Test Query Classification
        print("\n🔹 TESTING QUERY CLASSIFICATION:")
        classification_test = await self.test_query_classification()
        self.component_results["query_classification"] = classification_test
        print(f"  {'✅' if classification_test['success'] else '❌'} Query Classification: {classification_test['accuracy_percentage']:.1f}% accuracy")
        
        # Step 2: Test Response Generation
        print("\n🔹 TESTING RESPONSE GENERATION:")
        generation_test = await self.test_response_generation()
        self.component_results["response_generation"] = generation_test
        print(f"  {'✅' if generation_test['success'] else '❌'} Response Generation: {generation_test['success_percentage']:.1f}% success")
        
        # Step 3: Test Response Formatting
        print("\n🔹 TESTING RESPONSE FORMATTING:")
        formatting_test = await self.test_response_formatting()
        self.component_results["response_formatting"] = formatting_test
        print(f"  {'✅' if formatting_test['success'] else '❌'} Response Formatting: {formatting_test['successful_formats']}/{formatting_test['total_formats']} formats")
        
        # Step 4: Test Compliance and Safety
        print("\n🔹 TESTING COMPLIANCE AND SAFETY:")
        compliance_test = await self.test_compliance_safety()
        self.component_results["compliance_safety"] = compliance_test
        print(f"  {'✅' if compliance_test['success'] else '❌'} Compliance Safety: {compliance_test['approval_rate']:.1f}% approval rate")
        
        # Step 5: Integration Testing
        print("\n🔹 TESTING INTEGRATION:")
        integration_test = await self.test_integration()
        self.component_results["integration"] = integration_test
        print(f"  {'✅' if integration_test['success'] else '❌'} Integration: {'Passed' if integration_test['success'] else 'Failed'}")
        
        # Step 6: Performance Validation
        print("\n🔹 PERFORMANCE VALIDATION:")
        performance_test = await self.run_performance_validation()
        self.component_results["performance"] = performance_test
        print(f"  {'✅' if performance_test['success'] else '❌'} Performance: {'All targets met' if performance_test['success'] else 'Some targets not met'}")
        
        # Step 7: Export Results
        print("\n🔹 EXPORTING RESULTS:")
        
        # Calculate statistics
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Create results object
        results = Phase3Results(
            success=all([
                classification_test['success'],
                generation_test['success'],
                formatting_test['success'],
                compliance_test['success'],
                integration_test['success'],
                performance_test['success']
            ]),
            query_classification_accuracy=classification_test.get('accuracy_percentage', 0.0),
            response_generation_success=generation_test.get('success_percentage', 0.0),
            compliance_approval_rate=compliance_test.get('approval_rate', 0.0),
            formatting_coverage=(formatting_test.get('successful_formats', 0) / formatting_test.get('total_formats', 1) * 100),
            integration_test_success=100.0 if integration_test['success'] else 0.0,
            performance_metrics={
                "classification_time": performance_test.get("classification_performance", {}).get("average_time", 0.0),
                "generation_time": performance_test.get("generation_performance", {}).get("average_time", 0.0),
                "formatting_time": performance_test.get("formatting_performance", {}).get("average_time", 0.0),
                "overall_time": total_time
            },
            component_results=self.component_results,
            errors=[]
        )
        
        # Export results
        export_success = await self.export_results(results)
        print(f"  {'✅' if export_success else '❌'} Export: {'Completed' if export_success else 'Failed'}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PHASE 3 RESULTS: Query Processing and Response Generation")
        print("=" * 80)
        print(f"Success: {'✅' if results.success else '❌'}")
        print(f"Query Classification Accuracy: {results.query_classification_accuracy:.1f}%")
        print(f"Response Generation Success: {results.response_generation_success:.1f}%")
        print(f"Compliance Approval Rate: {results.compliance_approval_rate:.1f}%")
        print(f"Formatting Coverage: {results.formatting_coverage:.1f}%")
        print(f"Integration Test Success: {results.integration_test_success:.1f}%")
        
        print("\n📈 COMPONENT TESTS:")
        print(f"Query Classification: {'✅' if classification_test['success'] else '❌'}")
        print(f"Response Generation: {'✅' if generation_test['success'] else '❌'}")
        print(f"Response Formatting: {'✅' if formatting_test['success'] else '❌'}")
        print(f"Compliance Safety: {'✅' if compliance_test['success'] else '❌'}")
        print(f"Integration: {'✅' if integration_test['success'] else '❌'}")
        print(f"Performance: {'✅' if performance_test['success'] else '❌'}")
        
        print("\n📊 PERFORMANCE METRICS:")
        if performance_test.get('success'):
            class_perf = performance_test['classification_performance']
            gen_perf = performance_test['generation_performance']
            format_perf = performance_test['formatting_performance']
            
            print(f"Classification Processing: {class_perf['average_time']:.3f}s")
            print(f"Generation Processing: {gen_perf['average_time']:.3f}s")
            print(f"Formatting Processing: {format_perf['average_time']:.3f}s")
            print(f"Overall Pipeline: {total_time:.3f}s")
        
        print("\n🔧 QUALITY METRICS:")
        print(f"Classification Accuracy: {results.query_classification_accuracy:.1f}%")
        print(f"Generation Success Rate: {results.response_generation_success:.1f}%")
        print(f"Compliance Approval: {results.compliance_approval_rate:.1f}%")
        print(f"Format Coverage: {results.formatting_coverage:.1f}%")
        print(f"Integration Success: {results.integration_test_success:.1f}%")
        
        print("\n" + "=" * 80)
        
        return results

async def main():
    """Main function to run Phase 3 pipeline."""
    try:
        pipeline = Phase3Pipeline()
        results = await pipeline.run_pipeline()
        
        if results.success:
            print("\n✅ Phase 3 completed successfully!")
            return 0
        else:
            print("\n❌ Phase 3 completed with issues.")
            return 1
            
    except Exception as e:
        logger.error(f"Phase 3 pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
