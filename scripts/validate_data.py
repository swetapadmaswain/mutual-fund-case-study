#!/usr/bin/env python3
"""
Script to validate data at different phases of the pipeline.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import traceback


def validate_data_collection():
    """Validate Phase 1: Data Collection"""
    print("🔍 Validating Phase 1: Data Collection")
    
    validation_results = {
        "phase": "data_collection",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "overall_status": "passed"
    }
    
    # Check raw data directory
    raw_data_dir = Path("data/raw")
    if not raw_data_dir.exists():
        validation_results["checks"]["raw_data_directory"] = {
            "status": "failed",
            "message": "Raw data directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        raw_files = list(raw_data_dir.rglob("*.json"))
        validation_results["checks"]["raw_data_directory"] = {
            "status": "passed",
            "count": len(raw_files),
            "message": f"Found {len(raw_files)} raw data files"
        }
        
        # Check file sizes
        total_size = sum(f.stat().st_size for f in raw_files)
        validation_results["checks"]["raw_data_size"] = {
            "status": "passed",
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "message": f"Total raw data size: {total_size / (1024 * 1024):.2f} MB"
        }
    
    # Check processed data directory
    processed_data_dir = Path("data/processed")
    if not processed_data_dir.exists():
        validation_results["checks"]["processed_data_directory"] = {
            "status": "failed",
            "message": "Processed data directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        processed_files = list(processed_data_dir.rglob("*.json"))
        validation_results["checks"]["processed_data_directory"] = {
            "status": "passed",
            "count": len(processed_files),
            "message": f"Found {len(processed_files)} processed data files"
        }
    
    # Check Phase 1 results
    phase1_results = Path("cache/phase1_results")
    if not phase1_results.exists():
        validation_results["checks"]["phase1_results"] = {
            "status": "failed",
            "message": "Phase 1 results directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        results_file = phase1_results / "collection_results.json"
        if not results_file.exists():
            validation_results["checks"]["phase1_results"] = {
                "status": "failed",
                "message": "Phase 1 results file does not exist"
            }
            validation_results["overall_status"] = "failed"
        else:
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                validation_results["checks"]["phase1_results"] = {
                    "status": "passed",
                    "documents_collected": results.get("documents_collected", 0),
                    "funds_processed": len(results.get("fund_results", {})),
                    "message": f"Collected {results.get('documents_collected', 0)} documents from {len(results.get('fund_results', {}))} funds"
                }
                
                # Check minimum thresholds
                if results.get("documents_collected", 0) < 10:
                    validation_results["checks"]["phase1_results"]["status"] = "warning"
                    validation_results["checks"]["phase1_results"]["message"] += " (WARNING: Low document count)"
                    
            except Exception as e:
                validation_results["checks"]["phase1_results"] = {
                    "status": "failed",
                    "message": f"Error reading Phase 1 results: {e}"
                }
                validation_results["overall_status"] = "failed"
    
    return validation_results


def validate_chunking():
    """Validate Phase 2.1: Document Processing and Chunking"""
    print("🔍 Validating Phase 2.1: Document Processing and Chunking")
    
    validation_results = {
        "phase": "chunking",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "overall_status": "passed"
    }
    
    # Check documents directory
    documents_dir = Path("data/documents")
    if not documents_dir.exists():
        validation_results["checks"]["documents_directory"] = {
            "status": "failed",
            "message": "Documents directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        doc_files = list(documents_dir.rglob("*.json"))
        validation_results["checks"]["documents_directory"] = {
            "status": "passed",
            "count": len(doc_files),
            "message": f"Found {len(doc_files)} document files"
        }
    
    # Check Phase 2.1 results
    phase2_1_results = Path("cache/phase2_1_results")
    if not phase2_1_results.exists():
        validation_results["checks"]["phase2_1_results"] = {
            "status": "failed",
            "message": "Phase 2.1 results directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        chunks_file = phase2_1_results / "enriched_chunks.json"
        if not chunks_file.exists():
            validation_results["checks"]["phase2_1_results"] = {
                "status": "failed",
                "message": "Enriched chunks file does not exist"
            }
            validation_results["overall_status"] = "failed"
        else:
            try:
                with open(chunks_file, 'r') as f:
                    chunks = json.load(f)
                
                chunk_count = len(chunks)
                validation_results["checks"]["phase2_1_results"] = {
                    "status": "passed",
                    "chunk_count": chunk_count,
                    "message": f"Generated {chunk_count} chunks"
                }
                
                # Check chunk quality
                avg_chunk_size = sum(len(chunk.get("content", "")) for chunk in chunks) / chunk_count if chunk_count > 0 else 0
                
                if avg_chunk_size < 100:
                    validation_results["checks"]["phase2_1_results"]["status"] = "warning"
                    validation_results["checks"]["phase2_1_results"]["message"] += " (WARNING: Small average chunk size)"
                elif avg_chunk_size > 2000:
                    validation_results["checks"]["phase2_1_results"]["status"] = "warning"
                    validation_results["checks"]["phase2_1_results"]["message"] += " (WARNING: Large average chunk size)"
                
                validation_results["checks"]["chunk_quality"] = {
                    "status": "passed",
                    "average_chunk_size": round(avg_chunk_size, 0),
                    "message": f"Average chunk size: {avg_chunk_size:.0f} characters"
                }
                
                # Check metadata completeness
                chunks_with_metadata = sum(1 for chunk in chunks if chunk.get("metadata"))
                metadata_completeness = chunks_with_metadata / chunk_count if chunk_count > 0 else 0
                
                validation_results["checks"]["metadata_completeness"] = {
                    "status": "passed" if metadata_completeness > 0.8 else "warning",
                    "completeness": round(metadata_completeness, 2),
                    "message": f"Metadata completeness: {metadata_completeness:.2%}"
                }
                
            except Exception as e:
                validation_results["checks"]["phase2_1_results"] = {
                    "status": "failed",
                    "message": f"Error reading enriched chunks: {e}"
                }
                validation_results["overall_status"] = "failed"
    
    return validation_results


def validate_vector_store():
    """Validate Phase 2.2: Vector Store Setup"""
    print("🔍 Validating Phase 2.2: Vector Store Setup")
    
    validation_results = {
        "phase": "vector_store",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "overall_status": "passed"
    }
    
    # Check vector database directory
    vector_db_dir = Path("cache/vector_db")
    if not vector_db_dir.exists():
        validation_results["checks"]["vector_db_directory"] = {
            "status": "failed",
            "message": "Vector database directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        db_files = list(vector_db_dir.rglob("*"))
        validation_results["checks"]["vector_db_directory"] = {
            "status": "passed",
            "file_count": len(db_files),
            "message": f"Vector database contains {len(db_files)} files"
        }
    
    # Check Phase 2.2 results
    phase2_2_results = Path("cache/phase2_2_results")
    if not phase2_2_results.exists():
        validation_results["checks"]["phase2_2_results"] = {
            "status": "failed",
            "message": "Phase 2.2 results directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        results_file = phase2_2_results / "phase2_2_results.json"
        if not results_file.exists():
            validation_results["checks"]["phase2_2_results"] = {
                "status": "failed",
                "message": "Phase 2.2 results file does not exist"
            }
            validation_results["overall_status"] = "failed"
        else:
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                step_results = results.get("step_results", {})
                
                # Check embedding generation
                embedding_results = step_results.get("embedding_generation", {})
                validation_results["checks"]["embedding_generation"] = {
                    "status": "passed" if embedding_results.get("Success") else "failed",
                    "chunks_processed": embedding_results.get("chunks_processed", 0),
                    "embeddings_generated": embedding_results.get("embeddings_generated", 0),
                    "message": f"Generated {embedding_results.get('embeddings_generated', 0)} embeddings"
                }
                
                # Check vector storage
                storage_results = step_results.get("vector_storage", {})
                validation_results["checks"]["vector_storage"] = {
                    "status": "passed" if storage_results.get("Success") else "failed",
                    "documents_stored": storage_results.get("documents_stored", 0),
                    "collection_name": storage_results.get("collection_name", ""),
                    "message": f"Stored {storage_results.get('documents_stored', 0)} documents in {storage_results.get('collection_name', '')}"
                }
                
                # Check hierarchical indexing
                indexing_results = step_results.get("hierarchical_indexing", {})
                validation_results["checks"]["hierarchical_indexing"] = {
                    "status": "passed" if indexing_results.get("Success") else "failed",
                    "funds_indexed": indexing_results.get("funds_indexed", 0),
                    "fund_types": len(indexing_results.get("fund_types", [])),
                    "message": f"Indexed {indexing_results.get('funds_indexed', 0)} funds with {len(indexing_results.get('fund_types', []))} types"
                }
                
            except Exception as e:
                validation_results["checks"]["phase2_2_results"] = {
                    "status": "failed",
                    "message": f"Error reading Phase 2.2 results: {e}"
                }
                validation_results["overall_status"] = "failed"
    
    return validation_results


def validate_retrieval():
    """Validate Phase 2.3: Retrieval System"""
    print("🔍 Validating Phase 2.3: Retrieval System")
    
    validation_results = {
        "phase": "retrieval",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "overall_status": "passed"
    }
    
    # Check Phase 2.3 results
    phase2_3_results = Path("cache/phase2_3_results")
    if not phase2_3_results.exists():
        validation_results["checks"]["phase2_3_results"] = {
            "status": "failed",
            "message": "Phase 2.3 results directory does not exist"
        }
        validation_results["overall_status"] = "failed"
    else:
        results_file = phase2_3_results / "phase2_3_results.json"
        if not results_file.exists():
            validation_results["checks"]["phase2_3_results"] = {
                "status": "failed",
                "message": "Phase 2.3 results file does not exist"
            }
            validation_results["overall_status"] = "failed"
        else:
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                step_results = results.get("step_results", {})
                
                # Check query processing
                query_results = step_results.get("query_processing", {})
                validation_results["checks"]["query_processing"] = {
                    "status": "passed" if query_results.get("success") else "failed",
                    "validation_results": query_results.get("validation_results", {}),
                    "message": f"Query processing: {'✅' if query_results.get('success') else '❌'}"
                }
                
                # Check search engine
                search_results = step_results.get("search_engine", {})
                validation_results["checks"]["search_engine"] = {
                    "status": "passed" if search_results.get("success") else "failed",
                    "strategy_results": search_results.get("strategy_results", {}),
                    "message": f"Search engine: {'✅' if search_results.get('success') else '❌'}"
                }
                
                # Check context builder
                context_results = step_results.get("context_builder", {})
                validation_results["checks"]["context_builder"] = {
                    "status": "passed" if context_results.get("success") else "failed",
                    "strategy_results": context_results.get("strategy_results", {}),
                    "message": f"Context builder: {'✅' if context_results.get('success') else '❌'}"
                }
                
                # Check performance validation
                performance_results = step_results.get("performance_validation", {})
                validation_results["checks"]["performance_validation"] = {
                    "status": "passed" if performance_results.get("success") else "failed",
                    "overall_performance": performance_results.get("overall_performance", {}),
                    "message": f"Performance validation: {'✅' if performance_results.get('success') else '❌'}"
                }
                
            except Exception as e:
                validation_results["checks"]["phase2_3_results"] = {
                    "status": "failed",
                    "message": f"Error reading Phase 2.3 results: {e}"
                }
                validation_results["overall_status"] = "failed"
    
    return validation_results


def main():
    parser = argparse.ArgumentParser(description="Validate data at different phases")
    parser.add_argument("--phase", choices=["data_collection", "chunking", "vector_store", "retrieval", "all"], 
                       default="all", help="Phase to validate")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting validation for phase: {args.phase}")
    print("=" * 60)
    
    all_results = []
    
    if args.phase in ["data_collection", "all"]:
        result = validate_data_collection()
        all_results.append(result)
        print(f"✅ Phase 1: {result['overall_status'].upper()}")
    
    if args.phase in ["chunking", "all"]:
        result = validate_chunking()
        all_results.append(result)
        print(f"✅ Phase 2.1: {result['overall_status'].upper()}")
    
    if args.phase in ["vector_store", "all"]:
        result = validate_vector_store()
        all_results.append(result)
        print(f"✅ Phase 2.2: {result['overall_status'].upper()}")
    
    if args.phase in ["retrieval", "all"]:
        result = validate_retrieval()
        all_results.append(result)
        print(f"✅ Phase 2.3: {result['overall_status'].upper()}")
    
    # Save validation results
    results_dir = Path("cache/validation_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"validation_{args.phase}_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📊 Validation results saved to: {results_file}")
    
    # Overall status
    failed_phases = [r for r in all_results if r["overall_status"] == "failed"]
    warning_phases = [r for r in all_results if r["overall_status"] == "warning"]
    
    if failed_phases:
        print(f"\n❌ Validation FAILED for phases: {[r['phase'] for r in failed_phases]}")
        sys.exit(1)
    elif warning_phases:
        print(f"\n⚠️  Validation completed with WARNINGS for phases: {[r['phase'] for r in warning_phases]}")
        sys.exit(0)
    else:
        print(f"\n✅ All validations PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
