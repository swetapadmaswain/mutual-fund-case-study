"""
Main entry point for Phase 2.1 - Document Processing and Chunking pipeline.
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
from src.rag.chunking.document_processor import DocumentProcessor, ProcessedDocument
from src.rag.chunking.chunker import ChunkingPipeline, Chunk
from src.rag.chunking.metadata_enricher import MetadataEnrichmentPipeline
from src.rag.chunking.chunk_validator import ChunkValidator, ValidationStatus


class Phase21Pipeline:
    """Main pipeline for Phase 2.1 - Document Processing and Chunking."""
    
    def __init__(self):
        """Initialize the Phase 2.1 pipeline."""
        self.document_processor = DocumentProcessor()
        self.chunking_pipeline = ChunkingPipeline()
        self.metadata_enrichment_pipeline = MetadataEnrichmentPipeline()
        self.chunk_validator = ChunkValidator()
        
        # Results storage
        self.processed_documents: List[ProcessedDocument] = []
        self.chunks: List[Chunk] = []
        self.enriched_chunks: List[Chunk] = []
        self.validation_results: List = []
        
        logger.info("Initialized Phase 2.1 Pipeline")
    
    def load_phase1_data(self, data_path: str = "cache/hdfc_fund_data.json") -> List[Dict[str, Any]]:
        """
        Load data from Phase 1.
        
        Args:
            data_path: Path to Phase 1 data file
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Loading Phase 1 data from {data_path}")
        
        try:
            data_file = Path(data_path)
            if not data_file.exists():
                raise FileNotFoundError(f"Phase 1 data file not found: {data_path}")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"Loaded {len(documents)} documents from Phase 1")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load Phase 1 data: {e}")
            raise DataCollectionError(f"Failed to load Phase 1 data: {e}")
    
    async def run_pipeline(self, phase1_data_path: str = None) -> Dict[str, Any]:
        """
        Run the complete Phase 2.1 pipeline.
        
        Args:
            phase1_data_path: Path to Phase 1 data (optional)
            
        Returns:
            Pipeline execution results
        """
        logger.info("Starting Phase 2.1: Document Processing and Chunking Pipeline")
        
        results = {
            'phase': 'Phase 2.1 - Document Processing and Chunking',
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
            
            # Step 1: Load Phase 1 data
            logger.info("Step 1: Loading Phase 1 data")
            if phase1_data_path:
                phase1_documents = self.load_phase1_data(phase1_data_path)
            else:
                # Try default path
                phase1_documents = self.load_phase1_data()
            
            results['step_results']['data_loading'] = {
                'phase1_documents_loaded': len(phase1_documents),
                'success': True
            }
            
            # Step 2: Document processing
            logger.info("Step 2: Processing documents")
            self.processed_documents = self.document_processor.process_documents(phase1_documents)
            
            processing_summary = self.document_processor.get_processing_summary()
            results['step_results']['document_processing'] = {
                'documents_processed': len(self.processed_documents),
                'total_words': processing_summary['total_words'],
                'avg_compression_ratio': processing_summary['avg_compression_ratio'],
                'financial_data_extracted': processing_summary['financial_data_extracted'],
                'success': len(self.processed_documents) > 0
            }
            
            if not self.processed_documents:
                raise DataCollectionError("No documents were successfully processed")
            
            # Step 3: Chunking
            logger.info("Step 3: Creating chunks")
            self.chunks = self.chunking_pipeline.process_documents(self.processed_documents)
            
            chunking_summary = self.chunking_pipeline.get_chunking_summary()
            results['step_results']['chunking'] = {
                'total_chunks': len(self.chunks),
                'avg_chunk_size': chunking_summary['avg_chunk_size'],
                'size_distribution': chunking_summary['size_distribution'],
                'context_coverage': chunking_summary['context_coverage'],
                'success': len(self.chunks) > 0
            }
            
            if not self.chunks:
                raise DataCollectionError("No chunks were created")
            
            # Step 4: Metadata enrichment
            logger.info("Step 4: Enriching metadata")
            # Use metadata from first document as source metadata
            source_metadata = self.processed_documents[0].metadata if self.processed_documents else {}
            self.enriched_chunks = self.metadata_enrichment_pipeline.enrich_chunks(self.chunks, source_metadata)
            
            enrichment_summary = self.metadata_enrichment_pipeline.get_enrichment_summary()
            results['step_results']['metadata_enrichment'] = {
                'chunks_enriched': len(self.enriched_chunks),
                'avg_quality_score': enrichment_summary['avg_quality_score'],
                'content_types': enrichment_summary['content_types'],
                'financial_coverage': enrichment_summary['financial_coverage'],
                'citation_completeness': enrichment_summary['citation_completeness'],
                'success': len(self.enriched_chunks) > 0
            }
            
            # Step 5: Validation
            logger.info("Step 5: Validating chunks")
            self.validation_results = self.chunk_validator.validate_chunks_batch(self.enriched_chunks)
            
            validation_summary = self.chunk_validator.get_validation_summary(self.validation_results)
            results['step_results']['validation'] = {
                'total_validated': len(self.validation_results),
                'valid_chunks': validation_summary['valid_chunks'],
                'invalid_chunks': validation_summary['invalid_chunks'],
                'warning_chunks': validation_summary['warning_chunks'],
                'avg_score': validation_summary['avg_score'],
                'validation_rate': validation_summary['validation_rate'],
                'success': validation_summary['validation_rate'] > 0.8
            }
            
            # Step 6: Quality filtering
            logger.info("Step 6: Filtering by quality")
            high_quality_chunks, low_quality_chunks = self.chunk_validator.filter_chunks_by_quality(
                self.enriched_chunks, min_score=0.5
            )
            
            results['step_results']['quality_filtering'] = {
                'high_quality_chunks': len(high_quality_chunks),
                'low_quality_chunks': len(low_quality_chunks),
                'quality_retention_rate': len(high_quality_chunks) / len(self.enriched_chunks) if self.enriched_chunks else 0,
                'success': len(high_quality_chunks) > 0
            }
            
            # Step 7: Export results
            logger.info("Step 7: Exporting results")
            self._export_results()
            
            results['step_results']['export'] = {
                'processed_documents_exported': len(self.processed_documents),
                'chunks_exported': len(self.enriched_chunks),
                'validation_results_exported': len(self.validation_results),
                'success': True
            }
            
            # Generate final summary
            results['final_summary'] = self._generate_final_summary()
            results['success'] = True
            
            logger.info("Phase 2.1 pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Phase 2.1 pipeline failed: {e}")
            results['errors'].append(str(e))
            results['success'] = False
        
        finally:
            import time
            results['end_time'] = time.time()
            if results['start_time']:
                results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    def _export_results(self) -> None:
        """Export all results to files."""
        try:
            # Create export directory
            export_dir = Path("cache/phase2_1_results")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export processed documents
            if self.processed_documents:
                self.document_processor.export_processed_documents(
                    str(export_dir / "processed_documents.json")
                )
            
            # Export chunks
            if self.enriched_chunks:
                self.chunking_pipeline.export_chunks(
                    str(export_dir / "enriched_chunks.json")
                )
            
            # Export enriched chunks
            if self.enriched_chunks:
                self.metadata_enrichment_pipeline.export_enriched_chunks(
                    str(export_dir / "enriched_chunks.json")
                )
            
            # Export validation results
            if self.validation_results:
                self._export_validation_results(export_dir / "validation_results.json")
            
            logger.info(f"Results exported to {export_dir}")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise DataCollectionError(f"Export failed: {e}")
    
    def _export_validation_results(self, output_path: Path) -> None:
        """Export validation results to JSON file."""
        validation_data = []
        
        for i, result in enumerate(self.validation_results):
            validation_dict = {
                'chunk_index': i,
                'status': result.status.value,
                'score': result.score,
                'errors': result.errors,
                'warnings': result.warnings,
                'metadata': result.metadata
            }
            validation_data.append(validation_dict)
        
        # Add summary
        summary = self.chunk_validator.get_validation_summary(self.validation_results)
        
        export_data = {
            'summary': summary,
            'validation_results': validation_data,
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """Generate final summary of pipeline execution."""
        summary = {
            'pipeline_version': '2.1.0',
            'execution_timestamp': datetime.now().isoformat(),
            'documents_processed': len(self.processed_documents),
            'chunks_created': len(self.chunks),
            'chunks_enriched': len(self.enriched_chunks),
            'chunks_validated': len(self.validation_results),
            'processing_statistics': {},
            'chunking_statistics': {},
            'enrichment_statistics': {},
            'validation_statistics': {},
            'quality_metrics': {}
        }
        
        # Processing statistics
        if self.processed_documents:
            processing_summary = self.document_processor.get_processing_summary()
            summary['processing_statistics'] = processing_summary
        
        # Chunking statistics
        if self.chunks:
            chunking_summary = self.chunking_pipeline.get_chunking_summary()
            summary['chunking_statistics'] = chunking_summary
        
        # Enrichment statistics
        if self.enriched_chunks:
            enrichment_summary = self.metadata_enrichment_pipeline.get_enrichment_summary()
            summary['enrichment_statistics'] = enrichment_summary
        
        # Validation statistics
        if self.validation_results:
            validation_summary = self.chunk_validator.get_validation_summary(self.validation_results)
            summary['validation_statistics'] = validation_summary
        
        # Quality metrics
        if self.validation_results:
            scores = [result.score for result in self.validation_results]
            summary['quality_metrics'] = {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'high_quality_chunks': sum(1 for score in scores if score >= 0.7),
                'medium_quality_chunks': sum(1 for score in scores if 0.5 <= score < 0.7),
                'low_quality_chunks': sum(1 for score in scores if score < 0.5)
            }
        
        return summary


def print_results(results: Dict[str, Any]) -> None:
    """Print pipeline results in a formatted way."""
    print("\n" + "="*80)
    print(f"PHASE 2.1 RESULTS: {results['phase']}")
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
            else:
                print(f"  {key}: {value}")
    
    print("\n📈 FINAL SUMMARY:")
    summary = results['final_summary']
    print(f"  Documents Processed: {summary['documents_processed']}")
    print(f"  Chunks Created: {summary['chunks_created']}")
    print(f"  Chunks Enriched: {summary['chunks_enriched']}")
    print(f"  Chunks Validated: {summary['chunks_validated']}")
    
    if 'quality_metrics' in summary:
        quality = summary['quality_metrics']
        print(f"  Average Quality Score: {quality['average_score']:.2f}")
        print(f"  High Quality Chunks: {quality['high_quality_chunks']}")
        print(f"  Medium Quality Chunks: {quality['medium_quality_chunks']}")
        print(f"  Low Quality Chunks: {quality['low_quality_chunks']}")
    
    if 'validation_statistics' in summary:
        validation = summary['validation_statistics']
        print(f"  Validation Rate: {validation['validation_rate']:.2%}")
        print(f"  Valid Chunks: {validation['valid_chunks']}")
        print(f"  Invalid Chunks: {validation['invalid_chunks']}")
        print(f"  Warning Chunks: {validation['warning_chunks']}")
    
    if results['errors']:
        print("\n❌ ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*80)


async def main():
    """Main function to run Phase 2.1 pipeline."""
    try:
        # Create necessary directories
        Path("cache").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Create and run pipeline
        pipeline = Phase21Pipeline()
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
