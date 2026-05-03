#!/usr/bin/env python3
"""
Script to run performance benchmarks for the retrieval system.
"""
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
import sys
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rag.retrieval.query_processor import QueryProcessor
from src.rag.retrieval.search_engine import SemanticSearchEngine
from src.rag.retrieval.context_builder import ContextBuilder
from src.rag.retrieval.source_ranker import SourceRanker
from src.rag.vector_store.embeddings import EmbeddingService
from src.rag.vector_store.vector_database import VectorDatabase, HierarchicalVectorDB


class PerformanceTestSuite:
    """Performance testing suite for the retrieval system."""
    
    def __init__(self):
        """Initialize the performance test suite."""
        self.results = {
            "test_run": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # Test queries
        self.test_queries = [
            "What is the expense ratio of HDFC Mid Cap Fund?",
            "HDFC Large Cap Fund SIP details",
            "Risk level of ELSS funds",
            "Current NAV of HDFC Equity Fund",
            "Which fund has better performance?",
            "How to invest in HDFC Focused Fund?",
            "What is the minimum SIP amount?",
            "Exit load for HDFC funds",
            "HDFC fund investment objectives",
            "Performance comparison HDFC vs other funds"
        ]
        
        # Initialize components
        try:
            self.query_processor = QueryProcessor()
            self.embedding_service = EmbeddingService()
            self.vector_database = VectorDatabase()
            self.hierarchical_db = HierarchicalVectorDB(self.vector_database)
            self.search_engine = SemanticSearchEngine(
                self.vector_database,
                self.embedding_service,
                self.hierarchical_db
            )
            self.context_builder = ContextBuilder()
            self.source_ranker = SourceRanker()
            
            print("✅ Components initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            raise
    
    async def run_query_processing_tests(self):
        """Run query processing performance tests."""
        print("\n🔍 Running Query Processing Performance Tests")
        
        test_results = {
            "total_queries": len(self.test_queries),
            "processing_times": [],
            "confidence_scores": [],
            "entity_counts": [],
            "keyword_counts": []
        }
        
        for query in self.test_queries:
            start_time = time.time()
            
            try:
                processed_query = self.query_processor.process_query(query)
                processing_time = time.time() - start_time
                
                test_results["processing_times"].append(processing_time)
                test_results["confidence_scores"].append(processed_query.confidence)
                test_results["entity_counts"].append(len(processed_query.entities))
                test_results["keyword_counts"].append(len(processed_query.keywords))
                
            except Exception as e:
                print(f"❌ Error processing query '{query}': {e}")
                test_results["processing_times"].append(float('inf'))
        
        # Calculate statistics
        valid_times = [t for t in test_results["processing_times"] if t != float('inf')]
        
        if valid_times:
            test_results["statistics"] = {
                "average_processing_time": sum(valid_times) / len(valid_times),
                "min_processing_time": min(valid_times),
                "max_processing_time": max(valid_times),
                "queries_per_second": len(valid_times) / sum(valid_times),
                "average_confidence": sum(test_results["confidence_scores"]) / len(test_results["confidence_scores"]),
                "success_rate": len(valid_times) / len(self.test_queries)
            }
        else:
            test_results["statistics"] = {
                "average_processing_time": 0,
                "min_processing_time": 0,
                "max_processing_time": 0,
                "queries_per_second": 0,
                "average_confidence": 0,
                "success_rate": 0
            }
        
        self.results["tests"]["query_processing"] = test_results
        
        print(f"✅ Query Processing: {test_results['statistics']['average_processing_time']:.3f}s avg, "
              f"{test_results['statistics']['queries_per_second']:.1f} queries/sec")
    
    async def run_search_engine_tests(self):
        """Run search engine performance tests."""
        print("\n🔍 Running Search Engine Performance Tests")
        
        test_results = {
            "strategies": {},
            "overall": {}
        }
        
        strategies = ["semantic", "fund_focused", "content_focused", "hybrid"]
        
        for strategy in strategies:
            strategy_results = {
                "search_times": [],
                "result_counts": [],
                "similarity_scores": []
            }
            
            for query in self.test_queries[:5]:  # Test first 5 queries
                try:
                    processed_query = self.query_processor.process_query(query)
                    
                    start_time = time.time()
                    search_results = await self.search_engine.search(
                        processed_query,
                        search_strategy=strategy,
                        max_results=5
                    )
                    search_time = time.time() - start_time
                    
                    strategy_results["search_times"].append(search_time)
                    strategy_results["result_counts"].append(len(search_results))
                    
                    if search_results:
                        avg_similarity = sum(r.similarity_score for r in search_results) / len(search_results)
                        strategy_results["similarity_scores"].append(avg_similarity)
                    else:
                        strategy_results["similarity_scores"].append(0.0)
                        
                except Exception as e:
                    print(f"❌ Error in {strategy} search for '{query}': {e}")
                    strategy_results["search_times"].append(float('inf'))
            
            # Calculate strategy statistics
            valid_times = [t for t in strategy_results["search_times"] if t != float('inf')]
            
            if valid_times:
                test_results["strategies"][strategy] = {
                    "average_search_time": sum(valid_times) / len(valid_times),
                    "min_search_time": min(valid_times),
                    "max_search_time": max(valid_times),
                    "average_result_count": sum(strategy_results["result_counts"]) / len(strategy_results["result_counts"]),
                    "average_similarity": sum(strategy_results["similarity_scores"]) / len(strategy_results["similarity_scores"]),
                    "success_rate": len(valid_times) / len(self.test_queries[:5])
                }
            else:
                test_results["strategies"][strategy] = {
                    "average_search_time": 0,
                    "min_search_time": 0,
                    "max_search_time": 0,
                    "average_result_count": 0,
                    "average_similarity": 0,
                    "success_rate": 0
                }
        
        # Overall statistics
        all_times = []
        all_similarities = []
        
        for strategy_data in test_results["strategies"].values():
            if strategy_data["average_search_time"] > 0:
                all_times.append(strategy_data["average_search_time"])
                all_similarities.append(strategy_data["average_similarity"])
        
        if all_times:
            test_results["overall"] = {
                "average_search_time": sum(all_times) / len(all_times),
                "average_similarity": sum(all_similarities) / len(all_similarities),
                "best_strategy": min(test_results["strategies"].keys(), 
                                    key=lambda s: test_results["strategies"][s]["average_search_time"])
            }
        
        self.results["tests"]["search_engine"] = test_results
        
        print(f"✅ Search Engine: {test_results['overall'].get('average_search_time', 0):.3f}s avg, "
              f"Best strategy: {test_results['overall'].get('best_strategy', 'N/A')}")
    
    async def run_context_builder_tests(self):
        """Run context builder performance tests."""
        print("\n🔍 Running Context Builder Performance Tests")
        
        test_results = {
            "strategies": {},
            "overall": {}
        }
        
        strategies = ["relevance_first", "fund_grouped", "content_grouped", "hybrid"]
        
        for strategy in strategies:
            strategy_results = {
                "build_times": [],
                "token_counts": [],
                "window_counts": [],
                "source_counts": []
            }
            
            for query in self.test_queries[:3]:  # Test first 3 queries
                try:
                    processed_query = self.query_processor.process_query(query)
                    search_results = await self.search_engine.search(processed_query, max_results=5)
                    
                    start_time = time.time()
                    built_context = self.context_builder.build_context(
                        search_results=search_results,
                        query=processed_query,
                        strategy=strategy,
                        max_tokens=2000
                    )
                    build_time = time.time() - start_time
                    
                    strategy_results["build_times"].append(build_time)
                    strategy_results["token_counts"].append(built_context.total_tokens)
                    strategy_results["window_counts"].append(len(built_context.context_windows))
                    strategy_results["source_counts"].append(len(built_context.sources))
                    
                except Exception as e:
                    print(f"❌ Error in {strategy} context building for '{query}': {e}")
                    strategy_results["build_times"].append(float('inf'))
            
            # Calculate strategy statistics
            valid_times = [t for t in strategy_results["build_times"] if t != float('inf')]
            
            if valid_times:
                test_results["strategies"][strategy] = {
                    "average_build_time": sum(valid_times) / len(valid_times),
                    "min_build_time": min(valid_times),
                    "max_build_time": max(valid_times),
                    "average_token_count": sum(strategy_results["token_counts"]) / len(strategy_results["token_counts"]),
                    "average_window_count": sum(strategy_results["window_counts"]) / len(strategy_results["window_counts"]),
                    "average_source_count": sum(strategy_results["source_counts"]) / len(strategy_results["source_counts"]),
                    "success_rate": len(valid_times) / len(self.test_queries[:3])
                }
            else:
                test_results["strategies"][strategy] = {
                    "average_build_time": 0,
                    "min_build_time": 0,
                    "max_build_time": 0,
                    "average_token_count": 0,
                    "average_window_count": 0,
                    "average_source_count": 0,
                    "success_rate": 0
                }
        
        # Overall statistics
        all_times = []
        all_tokens = []
        
        for strategy_data in test_results["strategies"].values():
            if strategy_data["average_build_time"] > 0:
                all_times.append(strategy_data["average_build_time"])
                all_tokens.append(strategy_data["average_token_count"])
        
        if all_times:
            test_results["overall"] = {
                "average_build_time": sum(all_times) / len(all_times),
                "average_token_count": sum(all_tokens) / len(all_tokens),
                "best_strategy": min(test_results["strategies"].keys(), 
                                    key=lambda s: test_results["strategies"][s]["average_build_time"])
            }
        
        self.results["tests"]["context_builder"] = test_results
        
        print(f"✅ Context Builder: {test_results['overall'].get('average_build_time', 0):.3f}s avg, "
              f"Best strategy: {test_results['overall'].get('best_strategy', 'N/A')}")
    
    async def run_end_to_end_tests(self):
        """Run end-to-end performance tests."""
        print("\n🔍 Running End-to-End Performance Tests")
        
        test_results = {
            "total_processing_times": [],
            "query_types": {},
            "query_intents": {}
        }
        
        for query in self.test_queries:
            start_time = time.time()
            
            try:
                # Full pipeline
                processed_query = self.query_processor.process_query(query)
                search_results = await self.search_engine.search(processed_query, max_results=5)
                ranked_sources = self.source_ranker.rank_sources(search_results, processed_query)
                built_context = self.context_builder.build_context(search_results, processed_query)
                
                total_time = time.time() - start_time
                test_results["total_processing_times"].append(total_time)
                
                # Track by query type
                query_type = processed_query.query_type.value
                if query_type not in test_results["query_types"]:
                    test_results["query_types"][query_type] = []
                test_results["query_types"][query_type].append(total_time)
                
                # Track by query intent
                query_intent = processed_query.query_intent.value
                if query_intent not in test_results["query_intents"]:
                    test_results["query_intents"][query_intent] = []
                test_results["query_intents"][query_intent].append(total_time)
                
            except Exception as e:
                print(f"❌ Error in end-to-end test for '{query}': {e}")
                test_results["total_processing_times"].append(float('inf'))
        
        # Calculate statistics
        valid_times = [t for t in test_results["total_processing_times"] if t != float('inf')]
        
        if valid_times:
            test_results["statistics"] = {
                "average_total_time": sum(valid_times) / len(valid_times),
                "min_total_time": min(valid_times),
                "max_total_time": max(valid_times),
                "queries_per_second": len(valid_times) / sum(valid_times),
                "success_rate": len(valid_times) / len(self.test_queries)
            }
            
            # Type-specific statistics
            for query_type, times in test_results["query_types"].items():
                valid_type_times = [t for t in times if t != float('inf')]
                if valid_type_times:
                    test_results["query_types"][query_type] = {
                        "average_time": sum(valid_type_times) / len(valid_type_times),
                        "count": len(valid_type_times)
                    }
            
            # Intent-specific statistics
            for query_intent, times in test_results["query_intents"].items():
                valid_intent_times = [t for t in times if t != float('inf')]
                if valid_intent_times:
                    test_results["query_intents"][query_intent] = {
                        "average_time": sum(valid_intent_times) / len(valid_intent_times),
                        "count": len(valid_intent_times)
                    }
        
        else:
            test_results["statistics"] = {
                "average_total_time": 0,
                "min_total_time": 0,
                "max_total_time": 0,
                "queries_per_second": 0,
                "success_rate": 0
            }
        
        self.results["tests"]["end_to_end"] = test_results
        
        print(f"✅ End-to-End: {test_results['statistics']['average_total_time']:.3f}s avg, "
              f"{test_results['statistics']['queries_per_second']:.1f} queries/sec")
    
    def generate_summary(self):
        """Generate performance summary."""
        print("\n📊 Generating Performance Summary")
        
        summary = {
            "overall_performance": "unknown",
            "targets_met": {},
            "recommendations": []
        }
        
        # Performance targets
        targets = {
            "query_processing": 1.0,  # 1 second
            "search_engine": 0.5,    # 0.5 seconds
            "context_builder": 0.5,  # 0.5 seconds
            "end_to_end": 2.0        # 2 seconds total
        }
        
        # Check targets
        for test_name, target_time in targets.items():
            if test_name in self.results["tests"]:
                actual_time = self.results["tests"][test_name].get("overall", {}).get("average_" + 
                    ("search_time" if test_name == "search_engine" else 
                     "build_time" if test_name == "context_builder" else 
                     "processing_time" if test_name == "query_processing" else 
                     "total_time"), 0)
                
                target_met = actual_time <= target_time and actual_time > 0
                summary["targets_met"][test_name] = {
                    "target": target_time,
                    "actual": actual_time,
                    "met": target_met
                }
        
        # Overall performance assessment
        all_targets_met = all(result["met"] for result in summary["targets_met"].values())
        summary["overall_performance"] = "excellent" if all_targets_met else "needs_improvement"
        
        # Recommendations
        if not all_targets_met:
            for test_name, result in summary["targets_met"].items():
                if not result["met"]:
                    summary["recommendations"].append(
                        f"{test_name.replace('_', ' ').title()} is too slow "
                        f"({result['actual']:.3f}s vs target {result['target']:.1f}s)"
                    )
        
        # Success rates
        success_rates = {}
        for test_name, test_data in self.results["tests"].items():
            if "statistics" in test_data:
                success_rates[test_name] = test_data["statistics"].get("success_rate", 0)
        
        summary["success_rates"] = success_rates
        
        self.results["summary"] = summary
        
        print(f"✅ Overall Performance: {summary['overall_performance'].upper()}")
        
        if summary["recommendations"]:
            print("⚠️  Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   - {rec}")
    
    def save_results(self):
        """Save performance test results."""
        results_dir = Path("performance_reports")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"performance_report_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Performance report saved to: {results_file}")
        
        # Also save latest
        latest_file = results_dir / "latest_performance_report.json"
        with open(latest_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    async def run_all_tests(self):
        """Run all performance tests."""
        print("🚀 Starting Performance Test Suite")
        print("=" * 60)
        
        try:
            await self.run_query_processing_tests()
            await self.run_search_engine_tests()
            await self.run_context_builder_tests()
            await self.run_end_to_end_tests()
            
            self.generate_summary()
            self.save_results()
            
            print("\n" + "=" * 60)
            print("✅ Performance Test Suite Completed Successfully")
            
        except Exception as e:
            print(f"\n❌ Performance Test Suite Failed: {e}")
            print(traceback.format_exc())
            sys.exit(1)


async def main():
    """Main function to run performance tests."""
    test_suite = PerformanceTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
