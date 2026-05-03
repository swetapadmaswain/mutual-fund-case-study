"""
Main entry point for Phase 1 data collection pipeline.
"""
import asyncio
import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logger import logger
from src.data_collection.document_loader import fetch_multiple_pages
from src.data_collection.source_validator import validate_sources_batch
from src.data_collection.data_processor import DataProcessor
from src.utils.exceptions import MutualFundFAQException


async def run_phase1_pipeline() -> dict:
    """
    Run the complete Phase 1 data collection pipeline.
    
    Returns:
        Pipeline execution results
    """
    logger.info("Starting Phase 1: Foundation and Data Collection Pipeline")
    
    results = {
        'phase': 'Phase 1 - Foundation and Data Collection',
        'start_time': None,
        'end_time': None,
        'validation_results': None,
        'collection_results': None,
        'processing_results': None,
        'final_summary': None,
        'success': False,
        'errors': []
    }
    
    try:
        import time
        results['start_time'] = time.time()
        
        # Step 1: Validate all source URLs
        logger.info("Step 1: Validating source URLs")
        validation_results = validate_sources_batch(settings.hdfc_fund_urls)
        results['validation_results'] = validation_results
        
        if validation_results['invalid_urls'] > 0:
            logger.error(f"Validation failed for {validation_results['invalid_urls']} URLs")
            results['errors'].append(f"URL validation failed: {validation_results['invalid_urls']} invalid URLs")
            return results
        
        logger.info(f"URL validation passed: {validation_results['valid_urls']}/{validation_results['total_urls']} valid")
        
        # Step 2: Fetch data from validated URLs
        logger.info("Step 2: Fetching data from URLs")
        collection_results = await fetch_multiple_pages(settings.hdfc_fund_urls)
        results['collection_results'] = {
            'total_urls': len(settings.hdfc_fund_urls),
            'successful_fetches': len(collection_results),
            'failed_fetches': len(settings.hdfc_fund_urls) - len(collection_results)
        }
        
        if len(collection_results) == 0:
            logger.error("No data was successfully fetched")
            results['errors'].append("No data fetched from any URL")
            return results
        
        logger.info(f"Successfully fetched data from {len(collection_results)} URLs")
        
        # Step 3: Process and store the collected data
        logger.info("Step 3: Processing and storing data")
        processor = DataProcessor()
        processing_results = processor.process_documents(collection_results)
        results['processing_results'] = processing_results
        
        # Step 4: Generate final summary
        logger.info("Step 4: Generating final summary")
        summary = processor.get_processing_summary()
        results['final_summary'] = summary
        
        # Export data to CSV for review
        try:
            csv_path = Path("cache/hdfc_fund_data_export.csv")
            processor.export_to_csv(str(csv_path))
            logger.info(f"Data exported to {csv_path}")
        except Exception as e:
            logger.warning(f"CSV export failed: {e}")
            results['errors'].append(f"CSV export failed: {e}")
        
        results['success'] = True
        logger.info("Phase 1 pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 1 pipeline failed: {e}")
        results['errors'].append(str(e))
        results['success'] = False
    
    finally:
        import time
        results['end_time'] = time.time()
        if results['start_time']:
            results['duration'] = results['end_time'] - results['start_time']
    
    return results


def print_results(results: dict) -> None:
    """
    Print pipeline results in a formatted way.
    
    Args:
        results: Pipeline results dictionary
    """
    print("\n" + "="*80)
    print(f"PHASE 1 RESULTS: {results['phase']}")
    print("="*80)
    
    print(f"Success: {'✅' if results['success'] else '❌'}")
    
    if results.get('duration'):
        print(f"Duration: {results['duration']:.2f} seconds")
    
    print("\n📊 VALIDATION RESULTS:")
    if results['validation_results']:
        val = results['validation_results']
        print(f"  Total URLs: {val['total_urls']}")
        print(f"  Valid URLs: {val['valid_urls']}")
        print(f"  Invalid URLs: {val['invalid_urls']}")
        print(f"  SSL Enabled: {val['summary']['ssl_enabled']}")
        print(f"  Allowed Domains: {val['summary']['allowed_domains']}")
    
    print("\n🌐 COLLECTION RESULTS:")
    if results['collection_results']:
        col = results['collection_results']
        print(f"  Total URLs: {col['total_urls']}")
        print(f"  Successful Fetches: {col['successful_fetches']}")
        print(f"  Failed Fetches: {col['failed_fetches']}")
    
    print("\n⚙️ PROCESSING RESULTS:")
    if results['processing_results']:
        proc = results['processing_results']
        print(f"  Total Documents: {proc['total_documents']}")
        print(f"  New Documents: {proc['new_documents']}")
        print(f"  Duplicate Documents: {proc['duplicate_documents']}")
        print(f"  Processed Documents: {proc['processed_documents']}")
        print(f"  Failed Documents: {proc['failed_documents']}")
    
    print("\n📈 FINAL SUMMARY:")
    if results['final_summary']:
        summary = results['final_summary']
        print(f"  Total Documents: {summary['total_documents']}")
        print(f"  Unique Funds: {summary['unique_funds']}")
        print(f"  Last Updated: {summary['last_updated']}")
        if summary.get('processing_stats'):
            stats = summary['processing_stats']
            print(f"  Avg Content Length: {stats.get('avg_content_length', 0):.1f} characters")
            print(f"  Funds Processed: {stats.get('funds_processed', 0)}")
    
    if results['errors']:
        print("\n❌ ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*80)


async def main():
    """Main function to run Phase 1 pipeline."""
    try:
        # Create necessary directories
        Path("cache").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # Run the pipeline
        results = await run_phase1_pipeline()
        
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
