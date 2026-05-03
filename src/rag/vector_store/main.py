"""
Main entry point for Phase 2.2 - Vector Store Setup and Configuration.
"""
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.chunker import Chunk
from src.rag.vector_store.embeddings import EmbeddingService
from src.rag.vector_store.vector_database import VectorDatabase, HierarchicalVectorDB
from src.rag.vector_store.hierarchical_indexing import HierarchicalIndexer
from src.rag.vector_store.storage_optimizer import StorageOptimizer


class Phase22Pipeline:
    """Main pipeline for Phase 2.2 - Vector Store Setup and Configuration."""
    
    def __init__(self):
        """Initialize the Phase 2.2 pipeline."""
        # Initialize components
        self.embedding_service = EmbeddingService(
            model_name="BAAI/bge-small-en",
            device="cpu",
            batch_size=32,
            enable_cache=True
        )
        
        self.vector_database = VectorDatabase(
            collection_name="mutual_fund_chunks",
            persist_directory="cache/vector_db",
            embedding_dimension=384
        )
        
        self.hierarchical_indexer = HierarchicalIndexer()
        self.storage_optimizer = StorageOptimizer(
            storage_path="cache/vector_storage",
            compression_enabled=True,
            backup_enabled=True
        )
        
        # Results storage
        self.chunks: List[Chunk] = []
        self.embeddings: List = []
        self.document_ids: List[str] = []
        
        logger.info("Initialized Phase 2.2 Pipeline")
    
    def load_phase21_data(self, data_path: str = "cache/phase2_1_results/enriched_chunks.json") -> List[Chunk]:
        """
        Load enriched chunks from Phase 2.1.
        
        Args:
            data_path: Path to Phase 2.1 enriched chunks
            
        Returns:
            List of chunks
        """
        logger.info(f"Loading Phase 2.1 data from {data_path}")
        
        try:
            data_file = Path(data_path)
            if not data_file.exists():
                raise FileNotFoundError(f"Phase 2.1 data file not found: {data_path}")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to Chunk objects
            chunks = []
            chunk_data = data.get("chunks", [])
            
            for chunk_dict in chunk_data:
                chunk = Chunk(
                    chunk_id=chunk_dict["chunk_id"],
                    content=chunk_dict["content"],
                    metadata=chunk_dict["metadata"],
                    chunk_index=chunk_dict["chunk_index"],
                    total_chunks=chunk_dict["total_chunks"],
                    token_count=chunk_dict["token_count"],
                    source_document_id=chunk_dict["source_document_id"],
                    chunk_type=chunk_dict.get("chunk_type", "semantic"),
                    overlap_info=chunk_dict.get("overlap_info")
                )
                chunks.append(chunk)
            
            logger.info(f"Loaded {len(chunks)} chunks from Phase 2.1")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to load Phase 2.1 data: {e}")
            raise DataCollectionError(f"Failed to load Phase 2.1 data: {e}")
    
    async def run_pipeline(self, phase21_data_path: str = None) -> Dict[str, Any]:
        """
        Run the complete Phase 2.2 pipeline.
        
        Args:
            phase21_data_path: Path to Phase 2.1 data (optional)
            
        Returns:
            Pipeline execution results
        """
        logger.info("Starting Phase 2.2: Vector Store Setup and Configuration Pipeline")
        
        results = {
            'phase': 'Phase 2.2 - Vector Store Setup and Configuration',
            'start_time': None,
            'end_time': None,
            'step_results': {},
            'final_summary': {},
            'success': False,
            'errors': []
        }
        
        try:
            import time
            results['start_time'] = time.time()
            
            # Step 1: Load Phase 2.1 data
            logger.info("Step 1: Loading Phase 2.1 enriched chunks")
            if phase21_data_path:
                self.chunks = self.load_phase21_data(phase21_data_path)
            else:
                self.chunks = self.load_phase21_data()
            
            results['step_results']['data_loading'] = {
                'chunks_loaded': len(self.chunks),
                'success': len(self.chunks) > 0
            }
            
            if not self.chunks:
                raise DataCollectionError("No chunks loaded from Phase 2.1")
            
            # Step 2: Generate embeddings
            logger.info("Step 2: Generating embeddings for chunks")
            chunk_texts = [chunk.content for chunk in self.chunks]
            self.embeddings = await self.embedding_service.embed_texts_async(chunk_texts)
            
            results['step_results']['embedding_generation'] = {
                'chunks_processed': len(self.chunks),
                'embeddings_generated': len(self.embeddings),
                'embedding_dimension': len(self.embeddings[0]) if self.embeddings else 0,
                'model_info': self.embedding_service.get_service_info(),
                'success': len(self.embeddings) > 0
            }
            
            # Step 3: Store in vector database
            logger.info("Step 3: Storing chunks and embeddings in vector database")
            self.document_ids = self.vector_database.add_chunks(self.chunks, self.embeddings)
            
            results['step_results']['vector_storage'] = {
                'documents_stored': len(self.document_ids),
                'collection_name': self.vector_database.collection_name,
                'embedding_dimension': self.vector_database.embedding_dimension,
                'success': len(self.document_ids) > 0
            }
            
            # Step 4: Build hierarchical index
            logger.info("Step 4: Building hierarchical indexing system")
            self.hierarchical_indexer.build_index(self.chunks)
            
            hierarchy_stats = self.hierarchical_indexer.get_fund_statistics()
            results['step_results']['hierarchical_indexing'] = {
                'funds_indexed': hierarchy_stats['total_funds'],
                'fund_types': hierarchy_stats['fund_types'],
                'content_types': hierarchy_stats['content_types'],
                'total_documents': hierarchy_stats['total_documents'],
                'success': hierarchy_stats['total_funds'] > 0
            }
            
            # Step 5: Setup hierarchical vector database
            logger.info("Step 5: Setting up hierarchical vector database")
            hierarchical_db = HierarchicalVectorDB(self.vector_database)
            
            hierarchy_summary = hierarchical_db.get_hierarchy_stats()
            results['step_results']['hierarchical_db_setup'] = {
                'total_funds': hierarchy_summary['total_funds'],
                'fund_types': hierarchy_summary['fund_types'],
                'total_documents': hierarchy_summary['total_documents'],
                'success': hierarchy_summary['total_funds'] > 0
            }
            
            # Step 6: Configure metadata filters
            logger.info("Step 6: Configuring metadata filters")
            metadata_filters = self.hierarchical_indexer.setup_metadata_filters()
            
            results['step_results']['metadata_filters'] = {
                'fund_filters_count': len(metadata_filters['fund_filters']),
                'type_filters_count': len(metadata_filters['type_filters']),
                'content_filters_count': len(metadata_filters['content_filters']),
                'combined_filters_count': len(metadata_filters['combined_filters']),
                'success': True
            }
            
            # Step 7: Setup storage optimization
            logger.info("Step 7: Setting up storage optimization")
            backup_config = self.storage_optimizer.setup_backup_procedures()
            retention_config = self.storage_optimizer.configure_retention_policies()
            
            results['step_results']['storage_optimization'] = {
                'backup_configured': backup_config['backup_enabled'],
                'retention_configured': len(retention_config['policies']) > 0,
                'compression_enabled': self.storage_optimizer.compression_enabled,
                'success': True
            }
            
            # Step 8: Test query routing
            logger.info("Step 8: Testing query routing system")
            test_queries = [
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "HDFC Large Cap Fund SIP details",
                "Risk level of ELSS funds",
                "General mutual fund information"
            ]
            
            routing_results = []
            for query in test_queries:
                routing_info = self.hierarchical_indexer.route_queries(query)
                routing_results.append({
                    'query': query,
                    'query_type': routing_info['query_type'],
                    'search_strategy': routing_info['search_strategy'],
                    'target_funds': routing_info['target_funds'],
                    'target_types': routing_info['target_types']
                })
            
            results['step_results']['query_routing_test'] = {
                'queries_tested': len(test_queries),
                'routing_results': routing_results,
                'success': len(routing_results) > 0
            }
            
            # Step 9: Performance validation
            logger.info("Step 9: Validating performance metrics")
            performance_results = self._validate_performance()
            
            results['step_results']['performance_validation'] = performance_results
            
            # Step 10: Export results and configuration
            logger.info("Step 10: Exporting results and configuration")
            self._export_configuration()
            
            results['step_results']['export'] = {
                'configuration_exported': True,
                'results_exported': True,
                'success': True
            }
            
            # Generate final summary
            results['final_summary'] = self._generate_final_summary()
            results['success'] = True
            
            logger.info("Phase 2.2 pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 2.2 pipeline failed: {e}")
            results['errors'].append(str(e))
            results['success'] = False
        
        finally:
            import time
            results['end_time'] = time.time()
            if results['start_time']:
                results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    def _validate_performance(self) -> Dict[str, Any]:
        """Validate performance metrics against requirements."""
        logger.info("Validating performance metrics")
        
        performance_results = {
            'query_latency_test': {},
            'storage_efficiency_test': {},
            'index_structure_test': {},
            'overall_performance': {},
            'success': True,
            'errors': []
        }
        
        try:
            # Test query latency
            import time
            
            # Generate test embedding
            test_query = "What is the expense ratio?"
            test_embedding = await self.embedding_service.embed_texts_async([test_query])
            
            # Measure query time
            start_time = time.time()
            search_results = self.vector_database.search(test_embedding[0], top_k=5)
            query_time = time.time() - start_time
            
            performance_results['query_latency_test'] = {
                'query_time_ms': query_time * 1000,
                'target_latency_ms': 100,
                'meets_requirement': query_time < 0.1,  # < 100ms
                'results_returned': len(search_results)
            }
            
            # Test storage efficiency
            storage_usage = self.storage_optimizer.monitor_storage_usage()
            total_size_mb = storage_usage.get('total_size_mb', 0)
            
            # Estimate storage efficiency (simplified)
            expected_size_mb = len(self.chunks) * 384 * 4 / (1024 * 1024)  # Rough estimate
            efficiency = expected_size_mb / total_size_mb if total_size_mb > 0 else 0
            
            performance_results['storage_efficiency_test'] = {
                'total_size_mb': total_size_mb,
                'estimated_raw_size_mb': expected_size_mb,
                'storage_efficiency': efficiency,
                'target_efficiency': 0.8,
                'meets_requirement': efficiency > 0.8
            }
            
            # Test index structure
            hierarchy_stats = self.hierarchical_indexer.get_fund_statistics()
            
            performance_results['index_structure_test'] = {
                'funds_indexed': hierarchy_stats['total_funds'],
                'fund_types': len(hierarchy_stats['fund_types']),
                'content_types': len(hierarchy_stats['content_types']),
                'average_chunks_per_fund': hierarchy_stats['average_chunks_per_fund'],
                'meets_requirement': hierarchy_stats['total_funds'] > 0
            }
            
            # Overall performance assessment
            latency_ok = performance_results['query_latency_test']['meets_requirement']
            storage_ok = performance_results['storage_efficiency_test']['meets_requirement']
            index_ok = performance_results['index_structure_test']['meets_requirement']
            
            performance_results['overall_performance'] = {
                'all_requirements_met': latency_ok and storage_ok and index_ok,
                'latency_ok': latency_ok,
                'storage_ok': storage_ok,
                'index_ok': index_ok
            }
            
            performance_results['success'] = performance_results['overall_performance']['all_requirements_met']
            
            logger.info(f"Performance validation: {'PASS' if performance_results['success'] else 'FAIL'}")
            
        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            performance_results['errors'].append(str(e))
            performance_results['success'] = False
        
        return performance_results
    
    def _export_configuration(self) -> None:
        """Export configuration and results."""
        try:
            export_dir = Path("cache/phase2_2_results")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export vector database stats
            db_stats = self.vector_database.get_collection_stats()
            with open(export_dir / "vector_database_stats.json", 'w', encoding='utf-8') as f:
                json.dump(db_stats, f, indent=2, ensure_ascii=False)
            
            # Export hierarchical index
            hierarchy_stats = self.hierarchical_indexer.get_fund_statistics()
            with open(export_dir / "hierarchical_index_stats.json", 'w', encoding='utf-8') as f:
                json.dump(hierarchy_stats, f, indent=2, ensure_ascii=False)
            
            # Export embedding service info
            embedding_info = self.embedding_service.get_service_info()
            with open(export_dir / "embedding_service_info.json", 'w', encoding='utf-8') as f:
                json.dump(embedding_info, f, indent=2, ensure_ascii=False)
            
            # Export storage optimization stats
            storage_stats = self.storage_optimizer.monitor_storage_usage()
            with open(export_dir / "storage_optimization_stats.json", 'w', encoding='utf-8') as f:
                json.dump(storage_stats, f, indent=2, ensure_ascii=False)
            
            # Export metadata filters
            metadata_filters = self.hierarchical_indexer.setup_metadata_filters()
            with open(export_dir / "metadata_filters.json", 'w', encoding='utf-8') as f:
                json.dump(metadata_filters, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported configuration to {export_dir}")
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise DataCollectionError(f"Configuration export failed: {e}")
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """Generate final summary of pipeline execution."""
        summary = {
            'pipeline_version': '2.2.0',
            'execution_timestamp': datetime.now().isoformat(),
            'chunks_processed': len(self.chunks),
            'embeddings_generated': len(self.embeddings),
            'documents_stored': len(self.document_ids),
            'vector_database': {},
            'hierarchical_indexing': {},
            'embedding_service': {},
            'storage_optimization': {},
            'performance_metrics': {}
        }
        
        # Vector database summary
        db_stats = self.vector_database.get_collection_stats()
        summary['vector_database'] = {
            'collection_name': db_stats['collection_name'],
            'document_count': db_stats['document_count'],
            'embedding_dimension': db_stats['embedding_dimension'],
            'persist_directory': db_stats['persist_directory']
        }
        
        # Hierarchical indexing summary
        hierarchy_stats = self.hierarchical_indexer.get_fund_statistics()
        summary['hierarchical_indexing'] = {
            'total_funds': hierarchy_stats['total_funds'],
            'fund_types': hierarchy_stats['fund_types'],
            'content_types': hierarchy_stats['content_types'],
            'total_documents': hierarchy_stats['total_documents'],
            'average_chunks_per_fund': hierarchy_stats['average_chunks_per_fund']
        }
        
        # Embedding service summary
        embedding_info = self.embedding_service.get_service_info()
        summary['embedding_service'] = {
            'model_name': embedding_info['model_name'],
            'embedding_dimension': embedding_info['embedding_dimension'],
            'cache_enabled': embedding_info['cache_enabled'],
            'device': embedding_info['device']
        }
        
        # Storage optimization summary
        storage_stats = self.storage_optimizer.monitor_storage_usage()
        summary['storage_optimization'] = {
            'total_size_mb': storage_stats['total_size_mb'],
            'file_count': storage_stats['file_count'],
            'compression_ratio': storage_stats.get('compression_ratio', 0),
            'compression_enabled': self.storage_optimizer.compression_enabled,
            'backup_enabled': self.storage_optimizer.backup_enabled
        }
        
        return summary


def print_results(results: Dict[str, Any]) -> None:
    """Print pipeline results in a formatted way."""
    print("\n" + "="*80)
    print(f"PHASE 2.2 RESULTS: {results['phase']}")
    print("="*80)
    
    print(f"Success: {'✅' if results['success'] else '❌'}")
    
    if results.get('duration'):
        print(f"Duration: {results['duration']:.2f} seconds")
    
    print("\n📊 STEP RESULTS:")
    for step_name, step_result in results['step_results'].items():
        print(f"\n🔹 {step_name.upper().replace('_', ' ')}:")
        for key, value in step_result.items():
            if key == 'success':
                status = '✅' if value else '❌'
                print(f"  Success: {status}")
            elif isinstance(value, dict):
                print(f"  {key.title()}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            elif isinstance(value, list) and len(value) > 0:
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
    
    print("\n📈 FINAL SUMMARY:")
    summary = results['final_summary']
    print(f"  Chunks Processed: {summary['chunks_processed']}")
    print(f"  Embeddings Generated: {summary['embeddings_generated']}")
    print(f"  Documents Stored: {summary['documents_stored']}")
    
    if 'vector_database' in summary:
        db_info = summary['vector_database']
        print(f"  Collection: {db_info['collection_name']}")
        print(f"  Document Count: {db_info['document_count']}")
        print(f"  Embedding Dimension: {db_info['embedding_dimension']}")
    
    if 'hierarchical_indexing' in summary:
        hierarchy_info = summary['hierarchical_indexing']
        print(f"  Funds Indexed: {hierarchy_info['total_funds']}")
        print(f"  Fund Types: {len(hierarchy_info['fund_types'])}")
        print(f"  Content Types: {len(hierarchy_info['content_types'])}")
    
    if 'embedding_service' in summary:
        embedding_info = summary['embedding_service']
        print(f"  Model: {embedding_info['model_name']}")
        print(f"  Cache Enabled: {embedding_info['cache_enabled']}")
    
    if 'storage_optimization' in summary:
        storage_info = summary['storage_optimization']
        print(f"  Storage Size: {storage_info['total_size_mb']:.1f}MB")
        print(f"  Compression: {'✅' if storage_info['compression_enabled'] else '❌'}")
        print(f"  Backup: {'✅' if storage_info['backup_enabled'] else '❌'}")
    
    if results['errors']:
        print("\n❌ ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*80)


async def main():
    """Main function to run Phase 2.2 pipeline."""
    try:
        # Create necessary directories
        Path("cache").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Create and run pipeline
        pipeline = Phase22Pipeline()
        results = await pipeline.run_pipeline()
        
        # Print results
        print_results(results)
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
