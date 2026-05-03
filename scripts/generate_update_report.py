#!/usr/bin/env python3
"""
Script to generate comprehensive update reports for the data pipeline.
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import sys


def load_phase_results():
    """Load results from all phases."""
    results = {}
    
    # Load Phase 1 results
    phase1_file = Path("cache/phase1_results/collection_results.json")
    if phase1_file.exists():
        with open(phase1_file, 'r') as f:
            results["phase1"] = json.load(f)
    
    # Load Phase 2.1 results
    phase2_1_file = Path("cache/phase2_1_results/chunking_results.json")
    if phase2_1_file.exists():
        with open(phase2_1_file, 'r') as f:
            results["phase2_1"] = json.load(f)
    
    # Load Phase 2.2 results
    phase2_2_file = Path("cache/phase2_2_results/phase2_2_results.json")
    if phase2_2_file.exists():
        with open(phase2_2_file, 'r') as f:
            results["phase2_2"] = json.load(f)
    
    # Load Phase 2.3 results
    phase2_3_file = Path("cache/phase2_3_results/phase2_3_results.json")
    if phase2_3_file.exists():
        with open(phase2_3_file, 'r') as f:
            results["phase2_3"] = json.load(f)
    
    # Load validation results
    validation_dir = Path("cache/validation_results")
    if validation_dir.exists():
        validation_files = list(validation_dir.glob("validation_all_*.json"))
        if validation_files:
            latest_validation = max(validation_files, key=lambda f: f.stat().st_mtime)
            with open(latest_validation, 'r') as f:
                results["validation"] = json.load(f)
    
    # Load performance results
    performance_file = Path("performance_reports/latest_performance_report.json")
    if performance_file.exists():
        with open(performance_file, 'r') as f:
            results["performance"] = json.load(f)
    
    return results


def generate_markdown_report(results):
    """Generate a markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report = f"""# Mutual Fund Data Update Report

**Generated on**: {timestamp}  
**Pipeline Version**: 2.3.0

## 📊 Executive Summary

"""
    
    # Overall status
    overall_success = True
    success_count = 0
    total_phases = 0
    
    for phase_name, phase_data in results.items():
        if "phase" in phase_name or phase_name == "validation":
            total_phases += 1
            if phase_data.get("success", True) or phase_data.get("overall_status") == "passed":
                success_count += 1
            else:
                overall_success = False
    
    report += f"- **Overall Status**: {'✅ SUCCESS' if overall_success else '❌ FAILED'}\n"
    report += f"- **Phases Completed**: {success_count}/{total_phases}\n"
    report += f"- **Success Rate**: {(success_count/total_phases)*100:.1f}%\n\n"
    
    # Phase 1 Summary
    if "phase1" in results:
        phase1_data = results["phase1"]
        report += "## 🔍 Phase 1: Data Collection\n\n"
        report += f"- **Status**: {'✅ SUCCESS' if phase1_data.get('success', True) else '❌ FAILED'}\n"
        report += f"- **Documents Collected**: {phase1_data.get('documents_collected', 0)}\n"
        report += f"- **Funds Processed**: {len(phase1_data.get('fund_results', {}))}\n"
        report += f"- **Data Sources**: HDFC Mutual Fund, Groww\n"
        
        if "fund_results" in phase1_data:
            report += "\n### Fund Details:\n"
            for fund_name, fund_data in phase1_data["fund_results"].items():
                report += f"- **{fund_name}**: {fund_data.get('documents_found', 0)} documents\n"
        report += "\n"
    
    # Phase 2.1 Summary
    if "phase2_1" in results:
        phase2_1_data = results["phase2_1"]
        report += "## 📝 Phase 2.1: Document Processing & Chunking\n\n"
        report += f"- **Status**: {'✅ SUCCESS' if phase2_1_data.get('success', True) else '❌ FAILED'}\n"
        report += f"- **Documents Processed**: {phase2_1_data.get('documents_processed', 0)}\n"
        report += f"- **Chunks Generated**: {phase2_1_data.get('chunks_generated', 0)}\n"
        
        if "chunking_stats" in phase2_1_data:
            stats = phase2_1_data["chunking_stats"]
            report += f"- **Average Chunk Size**: {stats.get('average_chunk_size', 0):.0f} characters\n"
            report += f"- **Total Tokens**: {stats.get('total_tokens', 0):,}\n"
        report += "\n"
    
    # Phase 2.2 Summary
    if "phase2_2" in results:
        phase2_2_data = results["phase2_2"]
        report += "## 🔗 Phase 2.2: Vector Store Setup\n\n"
        report += f"- **Status**: {'✅ SUCCESS' if phase2_2_data.get('success', True) else '❌ FAILED'}\n"
        
        if "step_results" in phase2_2_data:
            step_results = phase2_2_data["step_results"]
            
            # Embedding generation
            if "embedding_generation" in step_results:
                embed_data = step_results["embedding_generation"]
                report += f"- **Embeddings Generated**: {embed_data.get('embeddings_generated', 0)}\n"
                report += f"- **Embedding Model**: {embed_data.get('model_info', {}).get('model_name', 'N/A')}\n"
            
            # Vector storage
            if "vector_storage" in step_results:
                storage_data = step_results["vector_storage"]
                report += f"- **Documents Stored**: {storage_data.get('documents_stored', 0)}\n"
                report += f"- **Collection**: {storage_data.get('collection_name', 'N/A')}\n"
            
            # Hierarchical indexing
            if "hierarchical_indexing" in step_results:
                index_data = step_results["hierarchical_indexing"]
                report += f"- **Funds Indexed**: {index_data.get('funds_indexed', 0)}\n"
                report += f"- **Fund Types**: {len(index_data.get('fund_types', []))}\n"
        
        report += "\n"
    
    # Phase 2.3 Summary
    if "phase2_3" in results:
        phase2_3_data = results["phase2_3"]
        report += "## 🔍 Phase 2.3: Retrieval System\n\n"
        report += f"- **Status**: {'✅ SUCCESS' if phase2_3_data.get('success', True) else '❌ FAILED'}\n"
        
        if "step_results" in phase2_3_data:
            step_results = phase2_3_data["step_results"]
            
            # Query processing
            if "query_processing" in step_results:
                query_data = step_results["query_processing"]
                validation = query_data.get("validation_results", {})
                report += f"- **Query Processing**: {validation.get('successful_processing', 0)}/{validation.get('total_queries', 0)} successful\n"
                report += f"- **Average Confidence**: {validation.get('average_confidence', 0):.2f}\n"
            
            # Search engine
            if "search_engine" in step_results:
                search_data = step_results["search_engine"]
                strategy_results = search_data.get("strategy_results", {})
                report += f"- **Search Strategies Tested**: {len(strategy_results)}\n"
                for strategy, data in strategy_results.items():
                    report += f"  - {strategy}: {data.get('average_similarity', 0):.3f} avg similarity\n"
            
            # Performance validation
            if "performance_validation" in step_results:
                perf_data = step_results["performance_validation"]
                overall = perf_data.get("overall_performance", {})
                report += f"- **Performance Targets Met**: {'✅ YES' if overall.get('all_requirements_met') else '❌ NO'}\n"
        
        report += "\n"
    
    # Performance Summary
    if "performance" in results:
        perf_data = results["performance"]
        report += "## ⚡ Performance Metrics\n\n"
        
        if "tests" in perf_data:
            tests = perf_data["tests"]
            
            for test_name, test_data in tests.items():
                if "overall" in test_data:
                    overall = test_data["overall"]
                    metric_name = test_name.replace("_", " ").title()
                    
                    if "average_search_time" in overall:
                        report += f"- **{metric_name}**: {overall['average_search_time']:.3f}s average\n"
                    elif "average_build_time" in overall:
                        report += f"- **{metric_name}**: {overall['average_build_time']:.3f}s average\n"
                    elif "average_processing_time" in overall:
                        report += f"- **{metric_name}**: {overall['average_processing_time']:.3f}s average\n"
                    elif "average_total_time" in overall:
                        report += f"- **{metric_name}**: {overall['average_total_time']:.3f}s average\n"
        
        if "summary" in perf_data:
            summary = perf_data["summary"]
            if "targets_met" in summary:
                report += "\n### Target Performance:\n"
                for target_name, target_data in summary["targets_met"].items():
                    status = "✅" if target_data["met"] else "❌"
                    report += f"- **{target_name.replace('_', ' ').title()}**: {status} {target_data['actual']:.3f}s (target: {target_data['target']:.1f}s)\n"
        
        report += "\n"
    
    # Validation Summary
    if "validation" in results:
        validation_data = results["validation"]
        report += "## ✅ Validation Results\n\n"
        
        if isinstance(validation_data, list):
            for phase_result in validation_data:
                phase_name = phase_result.get("phase", "unknown")
                status = phase_result.get("overall_status", "unknown")
                status_emoji = "✅" if status == "passed" else "❌"
                
                report += f"- **{phase_name.replace('_', ' ').title()}**: {status_emoji} {status.upper()}\n"
                
                if "checks" in phase_result:
                    for check_name, check_data in phase_result["checks"].items():
                        check_status = check_data.get("status", "unknown")
                        if check_status == "passed":
                            check_emoji = "✅"
                        elif check_status == "warning":
                            check_emoji = "⚠️"
                        else:
                            check_emoji = "❌"
                        report += f"  - {check_name.replace('_', ' ').title()}: {check_emoji}\n"
        
        report += "\n"
    
    # Data Quality Metrics
    report += "## 📈 Data Quality Metrics\n\n"
    
    # Calculate some quality metrics
    total_documents = 0
    total_chunks = 0
    total_embeddings = 0
    
    if "phase1" in results:
        total_documents = results["phase1"].get("documents_collected", 0)
    
    if "phase2_1" in results:
        total_chunks = results["phase2_1"].get("chunks_generated", 0)
    
    if "phase2_2" in results and "step_results" in results["phase2_2"]:
        embed_data = results["phase2_2"]["step_results"].get("embedding_generation", {})
        total_embeddings = embed_data.get("embeddings_generated", 0)
    
    report += f"- **Total Documents**: {total_documents:,}\n"
    report += f"- **Total Chunks**: {total_chunks:,}\n"
    report += f"- **Total Embeddings**: {total_embeddings:,}\n"
    
    if total_documents > 0:
        report += f"- **Chunks per Document**: {total_chunks/total_documents:.1f}\n"
    
    if total_chunks > 0:
        report += f"- **Embedding Coverage**: {(total_embeddings/total_chunks)*100:.1f}%\n"
    
    report += "\n"
    
    # Recommendations
    report += "## 💡 Recommendations\n\n"
    
    recommendations = []
    
    # Performance recommendations
    if "performance" in results and "summary" in results["performance"]:
        perf_summary = results["performance"]["summary"]
        if "recommendations" in perf_summary:
            recommendations.extend(perf_summary["recommendations"])
    
    # Data quality recommendations
    if total_documents < 20:
        recommendations.append("Consider expanding data sources to increase document coverage")
    
    if total_chunks < 100:
        recommendations.append("Consider adjusting chunking parameters for better granularity")
    
    if not overall_success:
        recommendations.append("Review failed phases and address issues before next update")
    
    if not recommendations:
        recommendations.append("System is performing well. Continue monitoring for any degradation.")
    
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"
    
    report += "\n"
    
    # Next Update Schedule
    report += "## 📅 Next Update Schedule\n\n"
    report += "- **Automatic Updates**: Daily at 2:00 AM IST\n"
    report += "- **Manual Updates**: Available via GitHub Actions workflow\n"
    report += "- **Force Update**: Use workflow dispatch with 'force_update=true'\n"
    report += "- **Incremental Updates**: Use 'incremental' type for faster updates\n\n"
    
    # Technical Details
    report += "## 🔧 Technical Details\n\n"
    report += f"- **Pipeline Version**: 2.3.0\n"
    report += f"- **Python Version**: 3.9+\n"
    report += f"- **Embedding Model**: BAAI/bge-small-en (384 dimensions)\n"
    report += f"- **Vector Database**: ChromaDB\n"
    report += f"- **Data Sources**: HDFC Mutual Fund, Groww\n"
    report += f"- **Update Frequency**: Daily\n\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate update report")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", 
                       help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    print("📊 Generating update report...")
    
    # Load all results
    results = load_phase_results()
    
    if not results:
        print("❌ No results found to generate report")
        sys.exit(1)
    
    # Generate report
    if args.format == "markdown":
        report = generate_markdown_report(results)
    else:
        report = json.dumps(results, indent=2)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path(f"update_report_{timestamp}.md" if args.format == "markdown" else f"update_report_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"✅ Report generated: {output_file}")
    
    # Also save latest
    latest_file = Path(f"latest_update_report.{args.format}")
    with open(latest_file, 'w') as f:
        f.write(report)
    
    print(f"✅ Latest report saved: {latest_file}")


if __name__ == "__main__":
    main()
