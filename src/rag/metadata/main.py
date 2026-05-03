"""
Phase 2.5 Main Pipeline: Metadata and Source Management

Orchestrates the complete Phase 2.5 workflow including source management,
metadata consistency, citation system, and version control.
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

from src.rag.metadata.source_manager import SourceManager, Source, BrokenLink
from src.rag.metadata.metadata_manager import MetadataManager, ValidationResult
from src.rag.metadata.citation_system import CitationSystem, Citation
from src.rag.metadata.version_control import VersionControl, DocumentVersion

logger = logging.getLogger(__name__)

@dataclass
class Phase25Results:
    """Results from Phase 2.5 pipeline execution."""
    success: bool
    total_sources: int
    valid_sources: int
    broken_links: int
    metadata_consistency_score: float
    citations_generated: int
    versions_tracked: int
    component_results: Dict[str, Any]
    errors: List[str]

class Phase25Pipeline:
    """
    Main pipeline for Phase 2.5: Metadata and Source Management.
    
    Orchestrates:
    - Source link management
    - Metadata consistency
    - Citation system
    - Version control
    - Performance testing
    """
    
    def __init__(self):
        """Initialize Phase 2.5 pipeline."""
        # Initialize components
        self.source_manager = SourceManager()
        self.metadata_manager = MetadataManager()
        self.citation_system = CitationSystem()
        self.version_control = VersionControl()
        
        # Performance tracking
        self.start_time = None
        self.component_results = {}
        
        logger.info("Phase 2.5 Pipeline initialized")
    
    async def test_source_management(self) -> Dict[str, Any]:
        """
        Test source management functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing source management...")
        
        test_results = {
            "success": False,
            "sources_validated": 0,
            "broken_links_found": 0,
            "link_rot_detected": 0,
            "sources_versioned": 0,
            "error": None
        }
        
        try:
            # Create test sources
            test_sources = [
                {"url": "https://hdfcfund.com", "title": "HDFC Mutual Fund Home"},
                {"url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund", "title": "HDFC Mid Cap Fund"},
                {"url": "https://groww.in/mutual-funds/hdfc-equity-fund", "title": "HDFC Equity Fund"},
                {"url": "https://invalid-url-that-does-not-exist.com", "title": "Invalid URL"},
                {"url": "https://hdfcfund.com/funds", "title": "HDFC Funds Page"}
            ]
            
            # Test source validation
            validated_sources = await self.source_manager.validate_source_links(test_sources)
            test_results["sources_validated"] = len(validated_sources)
            
            # Test link rot detection
            broken_links = await self.source_manager.detect_link_rot(validated_sources)
            test_results["broken_links_found"] = len(broken_links)
            
            # Test source versioning
            versioned_sources = await self.source_manager.version_sources(validated_sources)
            test_results["sources_versioned"] = len(versioned_sources)
            
            test_results["success"] = True
            
            logger.info(f"Source management test passed: {len(validated_sources)} sources validated")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Source management test failed: {e}")
        
        return test_results
    
    async def test_metadata_consistency(self) -> Dict[str, Any]:
        """
        Test metadata consistency functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing metadata consistency...")
        
        test_results = {
            "success": False,
            "chunks_processed": 0,
            "consistency_issues": 0,
            "updates_applied": 0,
            "relationships_created": 0,
            "average_consistency_score": 0.0,
            "error": None
        }
        
        try:
            # Create test chunks with metadata
            test_chunks = [
                {
                    "chunk_id": "test_chunk_1",
                    "source_url": "https://hdfcfund.com",
                    "fund_name": "HDFC Mid Cap Fund",
                    "content_type": "expense_ratio",
                    "document_type": "factsheet",
                    "last_updated": "2024-01-15",
                    "chunk_index": 0,
                    "confidence_score": 0.9,
                    "quality_score": 0.8
                },
                {
                    "chunk_id": "test_chunk_2",
                    "source_url": "https://groww.in",
                    "fund_name": "HDFC Equity Fund",
                    "content_type": "nav",
                    "document_type": "factsheet",
                    "last_updated": "2024-01-15",
                    "chunk_index": 1,
                    "confidence_score": 0.85
                    # Missing quality_score - should be added
                },
                {
                    "chunk_id": "test_chunk_3",
                    "source_url": "https://hdfcfund.com",
                    "fund_name": "HDFC Focused Fund",
                    "content_type": "sip",
                    "document_type": "prospectus",
                    "last_updated": "2024-01-15",
                    "chunk_index": 2
                    # Missing confidence_score and quality_score
                }
            ]
            
            # Test consistency enforcement
            consistent_chunks = self.metadata_manager.ensure_consistency(test_chunks)
            test_results["chunks_processed"] = len(consistent_chunks)
            
            # Calculate consistency issues
            consistency_issues = 0
            for chunk in consistent_chunks:
                validation = self.metadata_manager.validate_formats(chunk)
                if not validation.is_valid:
                    consistency_issues += len(validation.issues)
            
            test_results["consistency_issues"] = consistency_issues
            
            # Test relationship management
            relationships = self.metadata_manager.manage_relationships(consistent_chunks)
            test_results["relationships_created"] = len(relationships.parent_child) + len(relationships.siblings)
            
            # Calculate average consistency score
            if consistent_chunks:
                scores = [
                    self.metadata_manager.validate_formats(chunk).consistency_score
                    for chunk in consistent_chunks
                ]
                test_results["average_consistency_score"] = sum(scores) / len(scores)
            
            test_results["success"] = True
            
            logger.info(f"Metadata consistency test passed: {len(consistent_chunks)} chunks processed")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Metadata consistency test failed: {e}")
        
        return test_results
    
    async def test_citation_system(self) -> Dict[str, Any]:
        """
        Test citation system functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing citation system...")
        
        test_results = {
            "success": False,
            "citations_generated": 0,
            "formats_tested": 0,
            "multi_source_citations": 0,
            "usage_tracking_works": False,
            "average_confidence": 0.0,
            "error": None
        }
        
        try:
            # Create test chunks for citation
            test_chunks = [
                {
                    "chunk_id": "cite_chunk_1",
                    "source_url": "https://hdfcfund.com",
                    "fund_name": "HDFC Mid Cap Fund",
                    "document_type": "factsheet",
                    "content_type": "expense_ratio",
                    "last_updated": "2024-01-15",
                    "confidence_score": 0.9
                },
                {
                    "chunk_id": "cite_chunk_2",
                    "source_url": "https://groww.in",
                    "fund_name": "HDFC Equity Fund",
                    "document_type": "factsheet",
                    "content_type": "nav",
                    "last_updated": "2024-01-15",
                    "confidence_score": 0.85
                }
            ]
            
            # Test single source citations
            citations = []
            formats = ["hdfc_standard", "academic", "simple", "minimal"]
            
            for chunk in test_chunks:
                for format_name in formats:
                    citation = self.citation_system.generate_citation(chunk, format_name)
                    citations.append(citation)
                    test_results["formats_tested"] += 1
            
            test_results["citations_generated"] = len(citations)
            
            # Test multi-source citations
            multi_citation = self.citation_system.handle_multiple_sources(test_chunks, "hdfc_standard")
            test_results["multi_source_citations"] = 1
            
            # Test citation validation
            validation_results = []
            for citation in citations:
                is_valid = self.citation_system.validate_format(citation)
                validation_results.append(is_valid)
            
            # Test usage tracking
            for i, citation in enumerate(citations[:3]):
                self.citation_system.track_usage(
                    citation.citation_id,
                    f"query_type_{i}",
                    f"response_type_{i}",
                    0.8 + (i * 0.1)
                )
            
            test_results["usage_tracking_works"] = True
            
            # Calculate average confidence
            if citations:
                confidences = [c.confidence_score for c in citations]
                test_results["average_confidence"] = sum(confidences) / len(confidences)
            
            test_results["success"] = True
            
            logger.info(f"Citation system test passed: {len(citations)} citations generated")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Citation system test failed: {e}")
        
        return test_results
    
    async def test_version_control(self) -> Dict[str, Any]:
        """
        Test version control functionality.
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing version control...")
        
        test_results = {
            "success": False,
            "versions_tracked": 0,
            "relationships_created": 0,
            "rollback_tested": False,
            "version_comparison_works": False,
            "lineage_tracked": False,
            "error": None
        }
        
        try:
            # Create test documents
            test_documents = [
                {
                    "document_id": "doc_1",
                    "content": "This is the first version of document 1",
                    "metadata": {"title": "Document 1", "author": "system"},
                    "chunk_count": 5
                },
                {
                    "document_id": "doc_2",
                    "content": "This is the first version of document 2",
                    "metadata": {"title": "Document 2", "author": "system"},
                    "chunk_count": 3
                }
            ]
            
            # Test version tracking
            versions = self.version_control.track_document_versions(test_documents)
            test_results["versions_tracked"] = len(versions)
            
            # Test relationship management
            relationships = self.version_control.manage_version_relationships(versions)
            test_results["relationships_created"] = len(relationships)
            
            # Test content updates
            updates = [
                {
                    "document_id": "doc_1",
                    "content": "This is the updated version of document 1",
                    "metadata": {"title": "Document 1 Updated", "author": "system"},
                    "chunk_count": 6
                }
            ]
            
            update_versions = self.version_control.handle_content_updates(updates)
            test_results["versions_tracked"] += len(update_versions)
            
            # Test rollback
            if versions:
                rollback_version = self.version_control.implement_rollback_capabilities(
                    "doc_1",
                    versions[0].version_id
                )
                test_results["rollback_tested"] = rollback_version is not None
            
            # Test version comparison
            if len(versions) >= 2:
                comparison = self.version_control.compare_versions(
                    versions[0].version_id,
                    versions[1].version_id
                )
                test_results["version_comparison_works"] = comparison is not None
            
            # Test lineage tracking
            lineage = self.version_control.get_document_lineage("doc_1")
            test_results["lineage_tracked"] = len(lineage) > 0
            
            test_results["success"] = True
            
            logger.info(f"Version control test passed: {len(versions)} versions tracked")
            
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Version control test failed: {e}")
        
        return test_results
    
    async def test_integration(self) -> Dict[str, Any]:
        """
        Test integration between Phase 2.5 components.
        
        Returns:
            Integration test results
        """
        logger.info("Testing Phase 2.5 integration...")
        
        integration_results = {
            "success": False,
            "source_to_citation": False,
            "metadata_to_citation": False,
            "version_to_metadata": False,
            "end_to_end_workflow": False,
            "data_flow_consistent": False,
            "error": None
        }
        
        try:
            # Test source to citation integration
            test_sources = [
                {"url": "https://hdfcfund.com", "title": "HDFC Mutual Fund"}
            ]
            
            validated_sources = await self.source_manager.validate_source_links(test_sources)
            
            if validated_sources:
                # Convert to chunk format for citation
                chunks = [
                    {
                        "chunk_id": f"chunk_{i}",
                        "source_url": source.source_url,
                        "source_title": source.title,
                        "fund_name": "HDFC Test Fund",
                        "document_type": "factsheet",
                        "content_type": "general",
                        "last_updated": "2024-01-15"
                    }
                    for i, source in enumerate(validated_sources)
                ]
                
                citations = [self.citation_system.generate_citation(chunk) for chunk in chunks]
                integration_results["source_to_citation"] = len(citations) > 0
            
            # Test metadata to citation integration
            test_chunks = [
                {
                    "chunk_id": "meta_chunk_1",
                    "source_url": "https://hdfcfund.com",
                    "fund_name": "HDFC Mid Cap Fund",
                    "document_type": "factsheet",
                    "content_type": "expense_ratio",
                    "last_updated": "2024-01-15"
                }
            ]
            
            consistent_chunks = self.metadata_manager.ensure_consistency(test_chunks)
            
            if consistent_chunks:
                citations = [self.citation_system.generate_citation(chunk) for chunk in consistent_chunks]
                integration_results["metadata_to_citation"] = len(citations) > 0
            
            # Test version to metadata integration
            test_documents = [
                {
                    "document_id": "version_test_doc",
                    "content": "Test document content",
                    "metadata": {"title": "Test Document"},
                    "chunk_count": 1
                }
            ]
            
            versions = self.version_control.track_document_versions(test_documents)
            
            if versions:
                # Extract metadata from version and test consistency
                version_metadata = versions[0].metadata
                validation = self.metadata_manager.validate_formats(version_metadata)
                integration_results["version_to_metadata"] = validation.is_valid
            
            # Test end-to-end workflow
            end_to_end_success = (
                integration_results["source_to_citation"] and
                integration_results["metadata_to_citation"] and
                integration_results["version_to_metadata"]
            )
            
            integration_results["end_to_end_workflow"] = end_to_end_success
            integration_results["data_flow_consistent"] = end_to_end_success
            integration_results["success"] = end_to_end_success
            
            if end_to_end_success:
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
            "source_management_performance": {},
            "metadata_consistency_performance": {},
            "citation_system_performance": {},
            "version_control_performance": {},
            "overall_performance": {},
            "error": None
        }
        
        try:
            # Test source management performance
            start_time = time.time()
            test_sources = [{"url": f"https://test{i}.com", "title": f"Test {i}"} for i in range(10)]
            await self.source_manager.validate_source_links(test_sources)
            source_time = time.time() - start_time
            
            performance_results["source_management_performance"] = {
                "processing_time": source_time,
                "sources_per_second": len(test_sources) / source_time,
                "target_met": source_time < 10.0  # Target: < 10 seconds for 10 sources
            }
            
            # Test metadata consistency performance
            start_time = time.time()
            test_chunks = [
                {
                    "chunk_id": f"perf_chunk_{i}",
                    "source_url": f"https://test{i}.com",
                    "fund_name": f"Test Fund {i}",
                    "content_type": "general",
                    "document_type": "factsheet",
                    "last_updated": "2024-01-15",
                    "chunk_index": i
                }
                for i in range(50)
            ]
            
            self.metadata_manager.ensure_consistency(test_chunks)
            metadata_time = time.time() - start_time
            
            performance_results["metadata_consistency_performance"] = {
                "processing_time": metadata_time,
                "chunks_per_second": len(test_chunks) / metadata_time,
                "target_met": metadata_time < 5.0  # Target: < 5 seconds for 50 chunks
            }
            
            # Test citation system performance
            start_time = time.time()
            for chunk in test_chunks[:20]:
                self.citation_system.generate_citation(chunk)
            citation_time = time.time() - start_time
            
            performance_results["citation_system_performance"] = {
                "processing_time": citation_time,
                "citations_per_second": 20 / citation_time,
                "target_met": citation_time < 2.0  # Target: < 2 seconds for 20 citations
            }
            
            # Test version control performance
            start_time = time.time()
            test_documents = [
                {
                    "document_id": f"perf_doc_{i}",
                    "content": f"Test content {i}",
                    "metadata": {"title": f"Test Document {i}"},
                    "chunk_count": 1
                }
                for i in range(10)
            ]
            
            self.version_control.track_document_versions(test_documents)
            version_time = time.time() - start_time
            
            performance_results["version_control_performance"] = {
                "processing_time": version_time,
                "documents_per_second": len(test_documents) / version_time,
                "target_met": version_time < 3.0  # Target: < 3 seconds for 10 documents
            }
            
            # Overall performance
            total_time = source_time + metadata_time + citation_time + version_time
            performance_results["overall_performance"] = {
                "total_time": total_time,
                "target_met": total_time < 20.0,  # Target: < 20 seconds total
                "all_targets_met": all([
                    performance_results["source_management_performance"]["target_met"],
                    performance_results["metadata_consistency_performance"]["target_met"],
                    performance_results["citation_system_performance"]["target_met"],
                    performance_results["version_control_performance"]["target_met"]
                ])
            }
            
            performance_results["success"] = performance_results["overall_performance"]["all_targets_met"]
            
            if performance_results["success"]:
                logger.info("Performance validation passed")
            else:
                logger.warning("Performance validation failed - some targets not met")
            
        except Exception as e:
            performance_results["error"] = str(e)
            logger.error(f"Performance validation failed: {e}")
        
        return performance_results
    
    async def export_results(self, results: Phase25Results) -> bool:
        """
        Export Phase 2.5 results to files.
        
        Args:
            results: Phase 2.5 results to export
            
        Returns:
            True if export successful
        """
        try:
            # Create results directory
            results_dir = Path("cache/phase2_5_results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Export summary results
            summary_data = {
                "success": results.success,
                "total_sources": results.total_sources,
                "valid_sources": results.valid_sources,
                "broken_links": results.broken_links,
                "metadata_consistency_score": results.metadata_consistency_score,
                "citations_generated": results.citations_generated,
                "versions_tracked": results.versions_tracked,
                "component_results": results.component_results,
                "errors": results.errors,
                "timestamp": time.time()
            }
            
            with open(results_dir / "phase2_5_results.json", 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            # Export component statistics
            stats_data = {
                "source_manager_stats": self.source_manager.get_source_statistics(),
                "metadata_manager_stats": self.metadata_manager.get_metadata_statistics(),
                "citation_analytics": self.citation_system.get_citation_analytics(),
                "version_control_stats": self.version_control.get_version_statistics()
            }
            
            with open(results_dir / "component_statistics.json", 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            logger.info(f"Phase 2.5 results exported to {results_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    async def run_pipeline(self) -> Phase25Results:
        """
        Run the complete Phase 2.5 pipeline.
        
        Returns:
            Phase25Results object with pipeline results
        """
        logger.info("Starting Phase 2.5 Pipeline: Metadata and Source Management")
        print("=" * 80)
        print("PHASE 2.5: METADATA AND SOURCE MANAGEMENT")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Step 1: Test Source Management
        print("\n🔹 TESTING SOURCE MANAGEMENT:")
        source_test = await self.test_source_management()
        self.component_results["source_management"] = source_test
        print(f"  {'✅' if source_test['success'] else '❌'} Source Management: {source_test['sources_validated']} sources validated")
        if source_test['error']:
            print(f"     Error: {source_test['error']}")
        
        # Step 2: Test Metadata Consistency
        print("\n🔹 TESTING METADATA CONSISTENCY:")
        metadata_test = await self.test_metadata_consistency()
        self.component_results["metadata_consistency"] = metadata_test
        print(f"  {'✅' if metadata_test['success'] else '❌'} Metadata Consistency: {metadata_test['chunks_processed']} chunks processed")
        print(f"     Average consistency score: {metadata_test['average_consistency_score']:.2f}")
        
        # Step 3: Test Citation System
        print("\n🔹 TESTING CITATION SYSTEM:")
        citation_test = await self.test_citation_system()
        self.component_results["citation_system"] = citation_test
        print(f"  {'✅' if citation_test['success'] else '❌'} Citation System: {citation_test['citations_generated']} citations generated")
        print(f"     Average confidence: {citation_test['average_confidence']:.2f}")
        
        # Step 4: Test Version Control
        print("\n🔹 TESTING VERSION CONTROL:")
        version_test = await self.test_version_control()
        self.component_results["version_control"] = version_test
        print(f"  {'✅' if version_test['success'] else '❌'} Version Control: {version_test['versions_tracked']} versions tracked")
        print(f"     Rollback tested: {'✅' if version_test['rollback_tested'] else '❌'}")
        
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
        results = Phase25Results(
            success=all([
                source_test['success'],
                metadata_test['success'],
                citation_test['success'],
                version_test['success'],
                integration_test['success'],
                performance_test['success']
            ]),
            total_sources=source_test.get('sources_validated', 0),
            valid_sources=source_test.get('sources_validated', 0) - source_test.get('broken_links_found', 0),
            broken_links=source_test.get('broken_links_found', 0),
            metadata_consistency_score=metadata_test.get('average_consistency_score', 0),
            citations_generated=citation_test.get('citations_generated', 0),
            versions_tracked=version_test.get('versions_tracked', 0),
            component_results=self.component_results,
            errors=[]
        )
        
        # Export results
        export_success = await self.export_results(results)
        print(f"  {'✅' if export_success else '❌'} Export: {'Completed' if export_success else 'Failed'}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PHASE 2.5 RESULTS: Metadata and Source Management")
        print("=" * 80)
        print(f"Success: {'✅' if results.success else '❌'}")
        print(f"Total Sources: {results.total_sources}")
        print(f"Valid Sources: {results.valid_sources}")
        print(f"Broken Links: {results.broken_links}")
        print(f"Metadata Consistency Score: {results.metadata_consistency_score:.2f}")
        print(f"Citations Generated: {results.citations_generated}")
        print(f"Versions Tracked: {results.versions_tracked}")
        
        print("\n📈 COMPONENT TESTS:")
        print(f"Source Management: {'✅' if source_test['success'] else '❌'}")
        print(f"Metadata Consistency: {'✅' if metadata_test['success'] else '❌'}")
        print(f"Citation System: {'✅' if citation_test['success'] else '❌'}")
        print(f"Version Control: {'✅' if version_test['success'] else '❌'}")
        print(f"Integration: {'✅' if integration_test['success'] else '❌'}")
        print(f"Performance: {'✅' if performance_test['success'] else '❌'}")
        
        print("\n📊 PERFORMANCE METRICS:")
        if performance_test.get('success'):
            source_perf = performance_test['source_management_performance']
            metadata_perf = performance_test['metadata_consistency_performance']
            citation_perf = performance_test['citation_system_performance']
            version_perf = performance_test['version_control_performance']
            
            print(f"Source Management: {source_perf['sources_per_second']:.1f} sources/sec")
            print(f"Metadata Consistency: {metadata_perf['chunks_per_second']:.1f} chunks/sec")
            print(f"Citation System: {citation_perf['citations_per_second']:.1f} citations/sec")
            print(f"Version Control: {version_perf['documents_per_second']:.1f} documents/sec")
        
        print("\n🔧 QUALITY METRICS:")
        print(f"Source Link Accuracy: {(results.valid_sources/results.total_sources*100):.1f}%")
        print(f"Metadata Consistency: {results.metadata_consistency_score:.1%}")
        print(f"Citation Confidence: {citation_test.get('average_confidence', 0):.2f}")
        print(f"Version Tracking: {'✅' if version_test['success'] else '❌'}")
        
        print("\n" + "=" * 80)
        
        return results

async def main():
    """Main function to run Phase 2.5 pipeline."""
    try:
        pipeline = Phase25Pipeline()
        results = await pipeline.run_pipeline()
        
        if results.success:
            print("\n✅ Phase 2.5 completed successfully!")
            return 0
        else:
            print("\n❌ Phase 2.5 completed with issues.")
            return 1
            
    except Exception as e:
        logger.error(f"Phase 2.5 pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
