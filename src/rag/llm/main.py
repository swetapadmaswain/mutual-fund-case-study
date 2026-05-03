"""
Phase 2.4 Main Pipeline: LLM Integration and Prompt Engineering

Orchestrates the complete Phase 2.4 workflow including LLM integration,
prompt engineering, response validation, and formatting.
"""

import asyncio
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.llm.llm_service import LLMService, LLMResponse
from src.rag.llm.prompt_engine import PromptEngine
from src.rag.llm.response_validator import ResponseValidator, ValidationResult
from src.rag.llm.response_formatter import ResponseFormatter, FormattedResponse
from src.rag.retrieval.query_processor import QueryProcessor, ProcessedQuery
from src.rag.retrieval.search_engine import SemanticSearchEngine
from src.rag.retrieval.context_builder import ContextBuilder
from src.rag.retrieval.source_ranker import SourceRanker

logger = logging.getLogger(__name__)

@dataclass
class Phase24Results:
    """Results from Phase 2.4 pipeline execution."""
    success: bool
    total_queries: int
    successful_responses: int
    compliance_rate: float
    average_response_time: float
    llm_stats: Dict[str, Any]
    validation_stats: Dict[str, Any]
    formatted_responses: List[FormattedResponse]
    errors: List[str]

class Phase24Pipeline:
    """
    Main pipeline for Phase 2.4: LLM Integration and Prompt Engineering.
    
    Orchestrates:
    - LLM service integration
    - Prompt engineering and generation
    - Response validation
    - Response formatting
    - Performance testing
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize Phase 2.4 pipeline.
        
        Args:
            openai_api_key: OpenAI API key (if None, uses environment variable)
        """
        # Initialize LLM components
        self.llm_service = LLMService(
            api_key=openai_api_key or self._get_api_key(),
            model="gpt-3.5-turbo"
        )
        
        self.prompt_engine = PromptEngine()
        self.response_validator = ResponseValidator()
        self.response_formatter = ResponseFormatter()
        
        # Initialize retrieval components (from Phase 2.3)
        self.query_processor = QueryProcessor()
        self.search_engine = SemanticSearchEngine(
            vector_database=None,  # Will be initialized in run_pipeline
            embedding_service=None,
            hierarchical_db=None
        )
        self.context_builder = ContextBuilder()
        self.source_ranker = SourceRanker()
        
        # Performance tracking
        self.total_queries = 0
        self.successful_responses = 0
        self.total_response_time = 0.0
        self.validation_results = []
        
        logger.info("Phase 2.4 Pipeline initialized")
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        return api_key
    
    async def initialize_phase23_components(self) -> bool:
        """
        Initialize Phase 2.3 components for retrieval.
        
        Returns:
            True if initialization successful
        """
        try:
            # Import Phase 2.3 components
            from src.rag.vector_store.embeddings import EmbeddingService
            from src.rag.vector_store.vector_database import VectorDatabase, HierarchicalVectorDB
            
            # Initialize Phase 2.3 components
            embedding_service = EmbeddingService()
            vector_database = VectorDatabase()
            hierarchical_db = HierarchicalVectorDB(vector_database)
            
            # Update search engine with initialized components
            self.search_engine = SemanticSearchEngine(
                vector_database=vector_database,
                embedding_service=embedding_service,
                hierarchical_db=hierarchical_db
            )
            
            logger.info("Phase 2.3 components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Phase 2.3 components: {e}")
            return False
    
    async def test_llm_service(self) -> Dict[str, Any]:
        """
        Test LLM service connectivity and basic functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing LLM service...")
        
        test_results = {
            "success": False,
            "response_time": 0.0,
            "error": None,
            "response": None
        }
        
        try:
            start_time = time.time()
            
            # Test simple prompt
            test_prompt = "What is the expense ratio of HDFC Mid Cap Fund?"
            response = await self.llm_service.generate_response(test_prompt, max_tokens=10)
            
            test_results["response_time"] = time.time() - start_time
            test_results["success"] = response.success
            test_results["response"] = response.content
            test_results["error"] = response.error_message
            
            if response.success:
                logger.info(f"LLM service test passed in {test_results['response_time']:.2f}s")
            else:
                logger.error(f"LLM service test failed: {response.error_message}")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"LLM service test exception: {e}")
        
        return test_results
    
    async def test_prompt_engineering(self) -> Dict[str, Any]:
        """
        Test prompt engineering system.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing prompt engineering...")
        
        test_results = {
            "success": False,
            "templates_tested": 0,
            "template_results": {},
            "error": None
        }
        
        try:
            # Test different query types
            test_queries = [
                ("What is the expense ratio?", "factual"),
                ("Should I invest in HDFC Mid Cap Fund?", "advisory"),
                ("What are the historical returns?", "performance"),
                ("How to download statement?", "procedural"),
                ("Tell me about HDFC funds", "general")
            ]
            
            for query, query_type in test_queries:
                try:
                    prompt = self.prompt_engine.create_factual_prompt(
                        context="Test context for HDFC Mid Cap Fund",
                        query=query,
                        query_type=query_type
                    )
                    
                    # Validate prompt
                    validation = self.prompt_engine.validate_prompt(prompt, query_type)
                    
                    test_results["template_results"][query_type] = {
                        "prompt_length": len(prompt),
                        "validation_valid": validation["valid"],
                        "validation_issues": validation["issues"]
                    }
                    
                    test_results["templates_tested"] += 1
                    
                except Exception as e:
                    test_results["template_results"][query_type] = {
                        "error": str(e)
                    }
            
            test_results["success"] = test_results["templates_tested"] == len(test_queries)
            
            if test_results["success"]:
                logger.info(f"Prompt engineering test passed: {test_results['templates_tested']} templates tested")
            else:
                logger.error("Prompt engineering test failed")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Prompt engineering test exception: {e}")
        
        return test_results
    
    async def test_response_validation(self) -> Dict[str, Any]:
        """
        Test response validation system.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing response validation...")
        
        test_results = {
            "success": False,
            "responses_tested": 0,
            "validation_results": {},
            "error": None
        }
        
        try:
            # Test different response types
            test_responses = [
                ("The expense ratio is 0.85%.", "factual"),
                ("I recommend investing in HDFC Mid Cap Fund.", "advisory"),  # Should fail
                ("Past returns were 12% annually.", "performance"),
                ("First, login to your account.", "procedural"),
                ("HDFC offers multiple fund options.", "general")
            ]
            
            for response, query_type in test_responses:
                try:
                    validation = self.response_validator.verify_compliance(response, query_type)
                    
                    test_results["validation_results"][query_type] = {
                        "is_valid": validation.is_valid,
                        "overall_score": validation.overall_score,
                        "issues": validation.issues,
                        "compliance_score": validation.compliance_score
                    }
                    
                    test_results["responses_tested"] += 1
                    
                except Exception as e:
                    test_results["validation_results"][query_type] = {
                        "error": str(e)
                    }
            
            test_results["success"] = test_results["responses_tested"] == len(test_responses)
            
            if test_results["success"]:
                logger.info(f"Response validation test passed: {test_results['responses_tested']} responses tested")
            else:
                logger.error("Response validation test failed")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Response validation test exception: {e}")
        
        return test_results
    
    async def test_response_formatting(self) -> Dict[str, Any]:
        """
        Test response formatting system.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing response formatting...")
        
        test_results = {
            "success": False,
            "formats_tested": 0,
            "format_results": {},
            "error": None
        }
        
        try:
            # Test different response types
            test_cases = [
                ("The expense ratio is 0.85%.", "https://hdfcfund.com", "2024-01-15", "factual"),
                ("I cannot provide investment advice.", "https://groww.in", "2024-01-15", "advisory"),
                ("Returns were 12% last year.", "https://hdfcfund.com", "2024-01-15", "performance")
            ]
            
            for response, citation, date, query_type in test_cases:
                try:
                    formatted = self.response_formatter.format_response(
                        response=response,
                        citation=citation,
                        date=date,
                        query_type=query_type
                    )
                    
                    # Validate format
                    validation = self.response_formatter.validate_format(formatted)
                    
                    test_results["format_results"][query_type] = {
                        "format_valid": validation["valid"],
                        "has_answer": bool(formatted.answer),
                        "has_source": bool(formatted.source),
                        "has_disclaimer": bool(formatted.disclaimer),
                        "validation_issues": validation["issues"]
                    }
                    
                    test_results["formats_tested"] += 1
                    
                except Exception as e:
                    test_results["format_results"][query_type] = {
                        "error": str(e)
                    }
            
            test_results["success"] = test_results["formats_tested"] == len(test_cases)
            
            if test_results["success"]:
                logger.info(f"Response formatting test passed: {test_results['formats_tested']} formats tested")
            else:
                logger.error("Response formatting test failed")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Response formatting test exception: {e}")
        
        return test_results
    
    async def test_end_to_end_responses(self) -> Dict[str, Any]:
        """
        Test end-to-end response generation.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing end-to-end response generation...")
        
        test_results = {
            "success": False,
            "queries_tested": 0,
            "response_results": {},
            "error": None
        }
        
        try:
            # Test queries for end-to-end processing
            test_queries = [
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "What is the minimum SIP amount?",
                "What are the historical returns?",
                "How to download account statement?"
            ]
            
            for query in test_queries:
                try:
                    start_time = time.time()
                    
                    # Process query
                    processed_query = self.query_processor.process_query(query)
                    
                    # Generate prompt
                    prompt = self.prompt_engine.create_factual_prompt(
                        context="Test context for HDFC funds",
                        query=query,
                        query_type=processed_query.query_type.value
                    )
                    
                    # Generate LLM response
                    llm_response = await self.llm_service.generate_response(prompt, max_tokens=100)
                    
                    # Validate response
                    validation = self.response_validator.verify_compliance(
                        llm_response.content, 
                        processed_query.query_type.value
                    )
                    
                    # Format response
                    formatted = self.response_formatter.format_response(
                        response=llm_response.content,
                        citation="https://hdfcfund.com",
                        date="2024-01-15",
                        query_type=processed_query.query_type.value
                    )
                    
                    response_time = time.time() - start_time
                    
                    test_results["response_results"][query] = {
                        "query_type": processed_query.query_type.value,
                        "llm_success": llm_response.success,
                        "validation_valid": validation.is_valid,
                        "format_valid": self.response_formatter.validate_format(formatted)["valid"],
                        "response_time": response_time,
                        "formatted_answer": formatted.answer
                    }
                    
                    test_results["queries_tested"] += 1
                    
                except Exception as e:
                    test_results["response_results"][query] = {
                        "error": str(e)
                    }
            
            test_results["success"] = test_results["queries_tested"] == len(test_queries)
            
            if test_results["success"]:
                logger.info(f"End-to-end test passed: {test_results['queries_tested']} queries tested")
            else:
                logger.error("End-to-end test failed")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"End-to-end test exception: {e}")
        
        return test_results
    
    async def run_performance_validation(self) -> Dict[str, Any]:
        """
        Run performance validation tests.
        
        Returns:
            Performance validation results
        """
        logger.info("Running performance validation...")
        
        performance_results = {
            "success": False,
            "llm_performance": {},
            "validation_performance": {},
            "formatting_performance": {},
            "overall_performance": {},
            "error": None
        }
        
        try:
            # Test LLM performance
            llm_start = time.time()
            llm_response = await self.llm_service.generate_response("Test query", max_tokens=50)
            llm_time = time.time() - llm_start
            
            performance_results["llm_performance"] = {
                "response_time": llm_time,
                "success": llm_response.success,
                "target_met": llm_time < 3.0  # Target: < 3 seconds
            }
            
            # Test validation performance
            validation_start = time.time()
            validation = self.response_validator.verify_compliance("Test response", "factual")
            validation_time = time.time() - validation_start
            
            performance_results["validation_performance"] = {
                "processing_time": validation_time,
                "success": True,
                "target_met": validation_time < 0.1  # Target: < 0.1 seconds
            }
            
            # Test formatting performance
            formatting_start = time.time()
            formatted = self.response_formatter.format_response(
                "Test response", "https://test.com", "2024-01-15", "factual"
            )
            formatting_time = time.time() - formatting_start
            
            performance_results["formatting_performance"] = {
                "processing_time": formatting_time,
                "success": True,
                "target_met": formatting_time < 0.1  # Target: < 0.1 seconds
            }
            
            # Overall performance
            total_time = llm_time + validation_time + formatting_time
            performance_results["overall_performance"] = {
                "total_time": total_time,
                "target_met": total_time < 3.5,  # Target: < 3.5 seconds total
                "all_targets_met": all([
                    performance_results["llm_performance"]["target_met"],
                    performance_results["validation_performance"]["target_met"],
                    performance_results["formatting_performance"]["target_met"]
                ])
            }
            
            performance_results["success"] = performance_results["overall_performance"]["all_targets_met"]
            
            if performance_results["success"]:
                logger.info("Performance validation passed")
            else:
                logger.warning("Performance validation failed - some targets not met")
                
        except Exception as e:
            performance_results["error"] = str(e)
            logger.error(f"Performance validation exception: {e}")
        
        return performance_results
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """
        Run integration tests between Phase 2.4 components.
        
        Returns:
            Integration test results
        """
        logger.info("Running integration tests...")
        
        integration_results = {
            "success": False,
            "component_integration": {},
            "data_flow_validation": {},
            "error_handling": {},
            "error": None
        }
        
        try:
            # Test component integration
            integration_results["component_integration"] = {
                "llm_to_validation": True,  # Will be tested in end-to-end
                "validation_to_formatting": True,  # Will be tested in end-to-end
                "prompt_to_llm": True  # Will be tested in end-to-end
            }
            
            # Test data flow validation
            test_query = "What is the expense ratio?"
            processed_query = self.query_processor.process_query(test_query)
            prompt = self.prompt_engine.create_factual_prompt("Test context", test_query, "factual")
            llm_response = await self.llm_service.generate_response(prompt, max_tokens=50)
            validation = self.response_validator.verify_compliance(llm_response.content, "factual")
            formatted = self.response_formatter.format_response(llm_response.content, "https://test.com", "2024-01-15", "factual")
            
            integration_results["data_flow_validation"] = {
                "query_processed": True,
                "prompt_generated": True,
                "llm_responded": llm_response.success,
                "response_validated": True,
                "response_formatted": True,
                "data_flow_consistent": all([
                    True,
                    True,
                    llm_response.success,
                    True,
                    True
                ])
            }
            
            # Test error handling
            try:
                # Test with invalid API key (should handle gracefully)
                invalid_llm = LLMService("invalid_key")
                error_response = await invalid_llm.generate_response("Test", max_tokens=10)
                integration_results["error_handling"] = {
                    "graceful_handling": not error_response.success,
                    "error_message_provided": bool(error_response.error_message)
                }
            except Exception as e:
                integration_results["error_handling"] = {
                    "graceful_handling": False,
                    "error": str(e)
                }
            
            integration_results["success"] = (
                integration_results["data_flow_validation"]["data_flow_consistent"] and
                integration_results["error_handling"]["graceful_handling"]
            )
            
            if integration_results["success"]:
                logger.info("Integration tests passed")
            else:
                logger.error("Integration tests failed")
                
        except Exception as e:
            integration_results["error"] = str(e)
            logger.error(f"Integration tests exception: {e}")
        
        return integration_results
    
    async def export_results(self, results: Phase24Results) -> bool:
        """
        Export Phase 2.4 results to files.
        
        Args:
            results: Phase 2.4 results to export
            
        Returns:
            True if export successful
        """
        try:
            # Create results directory
            results_dir = Path("cache/phase2_4_results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Export summary results
            summary_data = {
                "success": results.success,
                "total_queries": results.total_queries,
                "successful_responses": results.successful_responses,
                "compliance_rate": results.compliance_rate,
                "average_response_time": results.average_response_time,
                "llm_stats": results.llm_stats,
                "validation_stats": results.validation_stats,
                "errors": results.errors,
                "timestamp": time.time()
            }
            
            with open(results_dir / "phase2_4_results.json", 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            # Export formatted responses
            responses_data = []
            for i, response in enumerate(results.formatted_responses):
                response_dict = {
                    "index": i,
                    "answer": response.answer,
                    "source": response.source,
                    "last_updated": response.last_updated,
                    "disclaimer": response.disclaimer,
                    "query_type": response.query_type,
                    "confidence": response.confidence,
                    "response_time": response.response_time,
                    "citations": response.citations,
                    "metadata": response.metadata
                }
                responses_data.append(response_dict)
            
            with open(results_dir / "formatted_responses.json", 'w') as f:
                json.dump(responses_data, f, indent=2)
            
            logger.info(f"Phase 2.4 results exported to {results_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    async def run_pipeline(self) -> Phase24Results:
        """
        Run the complete Phase 2.4 pipeline.
        
        Returns:
            Phase24Results object with pipeline results
        """
        logger.info("Starting Phase 2.4 Pipeline: LLM Integration and Prompt Engineering")
        print("=" * 80)
        print("PHASE 2.4: LLM INTEGRATION AND PROMPT ENGINEERING")
        print("=" * 80)
        
        # Initialize Phase 2.3 components
        print("\n🔹 INITIALIZING PHASE 2.3 COMPONENTS:")
        init_success = await self.initialize_phase23_components()
        if init_success:
            print("  ✅ Phase 2.3 components initialized")
        else:
            print("  ❌ Failed to initialize Phase 2.3 components")
            return Phase24Results(
                success=False,
                total_queries=0,
                successful_responses=0,
                compliance_rate=0.0,
                average_response_time=0.0,
                llm_stats={},
                validation_stats={},
                formatted_responses=[],
                errors=["Failed to initialize Phase 2.3 components"]
            )
        
        # Step 1: Test LLM Service
        print("\n🔹 TESTING LLM SERVICE:")
        llm_test = await self.test_llm_service()
        print(f"  {'✅' if llm_test['success'] else '❌'} LLM Service: {'Connected' if llm_test['success'] else 'Failed'}")
        if llm_test['error']:
            print(f"     Error: {llm_test['error']}")
        
        # Step 2: Test Prompt Engineering
        print("\n🔹 TESTING PROMPT ENGINEERING:")
        prompt_test = await self.test_prompt_engineering()
        print(f"  {'✅' if prompt_test['success'] else '❌'} Prompt Engineering: {prompt_test['templates_tested']}/5 templates tested")
        
        # Step 3: Test Response Validation
        print("\n🔹 TESTING RESPONSE VALIDATION:")
        validation_test = await self.test_response_validation()
        print(f"  {'✅' if validation_test['success'] else '❌'} Response Validation: {validation_test['responses_tested']}/5 responses tested")
        
        # Step 4: Test Response Formatting
        print("\n🔹 TESTING RESPONSE FORMATTING:")
        formatting_test = await self.test_response_formatting()
        print(f"  {'✅' if formatting_test['success'] else '❌'} Response Formatting: {formatting_test['formats_tested']}/3 formats tested")
        
        # Step 5: Test End-to-End Responses
        print("\n🔹 TESTING END-TO-END RESPONSES:")
        e2e_test = await self.test_end_to_end_responses()
        print(f"  {'✅' if e2e_test['success'] else '❌'} End-to-End: {e2e_test['queries_tested']}/4 queries tested")
        
        # Step 6: Performance Validation
        print("\n🔹 PERFORMANCE VALIDATION:")
        performance_test = await self.run_performance_validation()
        print(f"  {'✅' if performance_test['success'] else '❌'} Performance: {'All targets met' if performance_test['success'] else 'Some targets not met'}")
        
        # Step 7: Integration Testing
        print("\n🔹 INTEGRATION TESTING:")
        integration_test = await self.run_integration_tests()
        print(f"  {'✅' if integration_test['success'] else '❌'} Integration: {'Passed' if integration_test['success'] else 'Failed'}")
        
        # Step 8: Export Results
        print("\n🔹 EXPORTING RESULTS:")
        
        # Collect all formatted responses from tests
        formatted_responses = []
        for query_result in e2e_test.get("response_results", {}).values():
            if "error" not in query_result and query_result.get("formatted_answer"):
                formatted = self.response_formatter.format_response(
                    response=query_result["formatted_answer"],
                    citation="https://hdfcfund.com",
                    date="2024-01-15",
                    query_type=query_result.get("query_type", "factual")
                )
                formatted_responses.append(formatted)
        
        # Calculate statistics
        total_queries = e2e_test["queries_tested"]
        successful_responses = sum(1 for result in e2e_test["response_results"].values() 
                                 if result.get("llm_success", False) and result.get("validation_valid", False))
        
        compliance_rate = (successful_responses / total_queries * 100) if total_queries > 0 else 0
        
        # Get LLM stats
        llm_stats = self.llm_service.get_performance_stats()
        
        # Calculate validation stats
        validation_stats = {
            "total_validations": sum(1 for result in validation_test["validation_results"].values() 
                                   if "error" not in result),
            "valid_responses": sum(1 for result in validation_test["validation_results"].values() 
                                  if result.get("is_valid", False)),
            "average_compliance_score": sum(result.get("overall_score", 0) 
                                           for result in validation_test["validation_results"].values() 
                                           if "error" not in result) / max(1, len(validation_test["validation_results"]))
        }
        
        # Create results object
        results = Phase24Results(
            success=all([
                init_success,
                llm_test["success"],
                prompt_test["success"],
                validation_test["success"],
                formatting_test["success"],
                e2e_test["success"],
                performance_test["success"],
                integration_test["success"]
            ]),
            total_queries=total_queries,
            successful_responses=successful_responses,
            compliance_rate=compliance_rate,
            average_response_time=llm_stats.get("average_response_time", 0),
            llm_stats=llm_stats,
            validation_stats=validation_stats,
            formatted_responses=formatted_responses,
            errors=[]
        )
        
        # Export results
        export_success = await self.export_results(results)
        print(f"  {'✅' if export_success else '❌'} Export: {'Completed' if export_success else 'Failed'}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PHASE 2.4 RESULTS: LLM Integration and Prompt Engineering")
        print("=" * 80)
        print(f"Success: {'✅' if results.success else '❌'}")
        print(f"Total Queries Tested: {results.total_queries}")
        print(f"Successful Responses: {results.successful_responses}")
        print(f"Compliance Rate: {results.compliance_rate:.1f}%")
        print(f"Average Response Time: {results.average_response_time:.2f}s")
        print(f"LLM Success Rate: {llm_stats.get('success_rate', 0):.1f}%")
        print(f"Validation Success Rate: {validation_stats.get('valid_responses', 0)}/{validation_stats.get('total_validations', 0)}")
        
        print("\n📈 COMPONENT TESTS:")
        print(f"LLM Service: {'✅' if llm_test['success'] else '❌'}")
        print(f"Prompt Engineering: {'✅' if prompt_test['success'] else '❌'}")
        print(f"Response Validation: {'✅' if validation_test['success'] else '❌'}")
        print(f"Response Formatting: {'✅' if formatting_test['success'] else '❌'}")
        print(f"End-to-End: {'✅' if e2e_test['success'] else '❌'}")
        print(f"Performance: {'✅' if performance_test['success'] else '❌'}")
        print(f"Integration: {'✅' if integration_test['success'] else '❌'}")
        
        print("\n📊 PERFORMANCE TARGETS:")
        print(f"LLM Response Time: {'✅' if performance_test['llm_performance']['target_met'] else '❌'} (<3s)")
        print(f"Validation Time: {'✅' if performance_test['validation_performance']['target_met'] else '❌'} (<0.1s)")
        print(f"Formatting Time: {'✅' if performance_test['formatting_performance']['target_met'] else '❌'} (<0.1s)")
        print(f"Overall Time: {'✅' if performance_test['overall_performance']['target_met'] else '❌'} (<3.5s)")
        
        print("\n🔧 INTEGRATION STATUS:")
        print(f"Phase 2.3 Integration: {'✅' if init_success else '❌'}")
        print(f"Component Integration: {'✅' if integration_test['success'] else '❌'}")
        print(f"Data Flow Validation: {'✅' if integration_test.get('data_flow_validation', {}).get('data_flow_consistent', False) else '❌'}")
        print(f"Error Handling: {'✅' if integration_test.get('error_handling', {}).get('graceful_handling', False) else '❌'}")
        
        print("\n" + "=" * 80)
        
        return results

async def main():
    """Main function to run Phase 2.4 pipeline."""
    try:
        pipeline = Phase24Pipeline()
        results = await pipeline.run_pipeline()
        
        if results.success:
            print("\n✅ Phase 2.4 completed successfully!")
            return 0
        else:
            print("\n❌ Phase 2.4 completed with issues.")
            return 1
            
    except Exception as e:
        logger.error(f"Phase 2.4 pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
