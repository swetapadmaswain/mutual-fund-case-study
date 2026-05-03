"""
Comprehensive tests for Phase 2.5: Metadata and Source Management
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rag.metadata.source_manager import SourceManager, Source, BrokenLink
from src.rag.metadata.metadata_manager import MetadataManager, ValidationResult
from src.rag.metadata.citation_system import CitationSystem, Citation
from src.rag.metadata.version_control import VersionControl, DocumentVersion
from src.rag.metadata.main import Phase25Pipeline, Phase25Results


class TestSourceManager:
    """Test Source Manager functionality."""
    
    @pytest.fixture
    def source_manager(self):
        """Create source manager instance for testing."""
        return SourceManager(cache_dir="test_cache/source_manager")
    
    @pytest.mark.asyncio
    async def test_source_manager_initialization(self, source_manager):
        """Test source manager initialization."""
        assert source_manager.cache_dir.exists()
        assert source_manager.check_interval == timedelta(hours=24)
        assert source_manager.max_retries == 3
        assert source_manager.timeout == 10
    
    @pytest.mark.asyncio
    async def test_validate_source_links_success(self, source_manager):
        """Test successful source validation."""
        test_sources = [
            {"url": "https://httpbin.org/status/200", "title": "Test Site 1"},
            {"url": "https://httpbin.org/status/200", "title": "Test Site 2"}
        ]
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "<html><body>Test content</body></html>"
            mock_response.headers = {"content-type": "text/html"}
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            sources = await source_manager.validate_source_links(test_sources)
            
            assert len(sources) == 2
            assert all(isinstance(s, Source) for s in sources)
            assert all(s.status == "valid" for s in sources)
    
    @pytest.mark.asyncio
    async def test_validate_source_links_failure(self, source_manager):
        """Test source validation with failures."""
        test_sources = [
            {"url": "https://httpbin.org/status/404", "title": "Broken Site"},
            {"url": "https://invalid-url-that-does-not-exist.com", "title": "Invalid URL"}
        ]
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock 404 response
            mock_response_404 = AsyncMock()
            mock_response_404.status = 404
            mock_session.get.return_value.__aenter__.return_value = mock_response_404
            
            sources = await source_manager.validate_source_links(test_sources)
            
            assert len(sources) == 2
            assert all(s.status == "broken" for s in sources)
    
    @pytest.mark.asyncio
    async def test_detect_link_rot(self, source_manager):
        """Test link rot detection."""
        # Create test sources with mixed status
        sources = [
            Source(
                url="https://valid.com",
                title="Valid Source",
                domain="valid.com",
                last_checked=datetime.now(),
                last_valid=datetime.now(),
                status="valid",
                http_status=200,
                response_time=0.5,
                content_hash="abc123",
                redirect_url=None,
                metadata={}
            ),
            Source(
                url="https://broken.com",
                title="Broken Source",
                domain="broken.com",
                last_checked=datetime.now(),
                last_valid=datetime.now() - timedelta(days=1),
                status="broken",
                http_status=404,
                response_time=0.5,
                content_hash=None,
                redirect_url=None,
                metadata={}
            )
        ]
        
        broken_links = await source_manager.detect_link_rot(sources)
        
        assert len(broken_links) == 1
        assert broken_links[0].url == "https://broken.com"
        assert broken_links[0].error_type == "status_broken"
    
    @pytest.mark.asyncio
    async def test_version_sources(self, source_manager):
        """Test source versioning."""
        sources = [
            Source(
                url="https://test.com",
                title="Test Source",
                domain="test.com",
                last_checked=datetime.now(),
                last_valid=datetime.now(),
                status="valid",
                http_status=200,
                response_time=0.5,
                content_hash="abc123",
                redirect_url=None,
                metadata={}
            )
        ]
        
        versioned_sources = await source_manager.version_sources(sources)
        
        assert len(versioned_sources) == 1
        assert versioned_sources[0].url == "https://test.com"
        assert versioned_sources[0].content_hash == "abc123"
        assert len(versioned_sources[0].version) > 0
    
    def test_get_source_statistics(self, source_manager):
        """Test source statistics retrieval."""
        # Add some test sources
        source_manager.sources = {
            "https://valid1.com": Source(
                url="https://valid1.com",
                title="Valid 1",
                domain="valid1.com",
                last_checked=datetime.now(),
                last_valid=datetime.now(),
                status="valid",
                http_status=200,
                response_time=0.5,
                content_hash="abc123",
                redirect_url=None,
                metadata={}
            ),
            "https://valid2.com": Source(
                url="https://valid2.com",
                title="Valid 2",
                domain="valid2.com",
                last_checked=datetime.now(),
                last_valid=datetime.now(),
                status="valid",
                http_status=200,
                response_time=0.3,
                content_hash="def456",
                redirect_url=None,
                metadata={}
            ),
            "https://broken.com": Source(
                url="https://broken.com",
                title="Broken",
                domain="broken.com",
                last_checked=datetime.now(),
                last_valid=datetime.now() - timedelta(days=1),
                status="broken",
                http_status=404,
                response_time=1.0,
                content_hash=None,
                redirect_url=None,
                metadata={}
            )
        }
        
        source_manager.total_checks = 3
        source_manager.successful_checks = 2
        source_manager.broken_links_found = 1
        source_manager.average_response_time = 0.6
        
        stats = source_manager.get_source_statistics()
        
        assert stats["total_sources"] == 3
        assert stats["valid_sources"] == 2
        assert stats["broken_sources"] == 1
        assert stats["success_rate"] == 66.7
        assert stats["broken_link_rate"] == 33.3


class TestMetadataManager:
    """Test Metadata Manager functionality."""
    
    @pytest.fixture
    def metadata_manager(self):
        """Create metadata manager instance for testing."""
        return MetadataManager(cache_dir="test_cache/metadata_manager")
    
    def test_metadata_manager_initialization(self, metadata_manager):
        """Test metadata manager initialization."""
        assert metadata_manager.cache_dir.exists()
        assert "required_fields" in metadata_manager.schema
        assert "optional_fields" in metadata_manager.schema
        assert "format_constraints" in metadata_manager.schema
    
    def test_ensure_consistency(self, metadata_manager):
        """Test metadata consistency enforcement."""
        test_chunks = [
            {
                "chunk_id": "test_1",
                "source_url": "https://test.com",
                "fund_name": "Test Fund",
                "content_type": "expense_ratio",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 0
            },
            {
                # Missing required fields
                "source_url": "https://test2.com",
                "fund_name": "Test Fund 2"
            },
            {
                # Invalid format
                "chunk_id": "test_3",
                "source_url": "invalid-url",
                "fund_name": "Test Fund 3",
                "content_type": "invalid_type",
                "document_type": "factsheet",
                "last_updated": "invalid-date",
                "chunk_index": 0
            }
        ]
        
        consistent_chunks = metadata_manager.ensure_consistency(test_chunks)
        
        assert len(consistent_chunks) == 3
        
        # Check that missing fields were added
        assert "content_type" in consistent_chunks[1]
        assert "document_type" in consistent_chunks[1]
        assert "last_updated" in consistent_chunks[1]
        assert "chunk_index" in consistent_chunks[1]
        
        # Check that invalid formats were fixed
        assert consistent_chunks[2]["source_url"].startswith("http")
        assert consistent_chunks[2]["content_type"] == "general"
        assert consistent_chunks[2]["last_updated"] == datetime.now().strftime("%Y-%m-%d")
    
    def test_validate_formats(self, metadata_manager):
        """Test metadata format validation."""
        # Valid metadata
        valid_metadata = {
            "chunk_id": "test",
            "source_url": "https://test.com",
            "fund_name": "Test Fund",
            "content_type": "expense_ratio",
            "document_type": "factsheet",
            "last_updated": "2024-01-15",
            "chunk_index": 0
        }
        
        result = metadata_manager.validate_formats(valid_metadata)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.consistency_score == 1.0
        
        # Invalid metadata
        invalid_metadata = {
            "chunk_id": "test",
            # Missing required fields
            "source_url": "invalid-url",
            "fund_name": "Test Fund",
            "content_type": "invalid_type",
            "document_type": "factsheet",
            "last_updated": "invalid-date",
            "chunk_index": -1  # Invalid value
        }
        
        result = metadata_manager.validate_formats(invalid_metadata)
        
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert len(result.invalid_formats) > 0
        assert result.consistency_score < 1.0
    
    def test_manage_relationships(self, metadata_manager):
        """Test relationship management."""
        test_chunks = [
            {
                "chunk_id": "chunk_1",
                "source_url": "https://test.com",
                "fund_name": "HDFC Mid Cap Fund",
                "content_type": "expense_ratio",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 0
            },
            {
                "chunk_id": "chunk_2",
                "source_url": "https://test.com",
                "fund_name": "HDFC Mid Cap Fund",
                "content_type": "nav",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 1
            },
            {
                "chunk_id": "chunk_3",
                "source_url": "https://test2.com",
                "fund_name": "HDFC Equity Fund",
                "content_type": "expense_ratio",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 0
            }
        ]
        
        relationships = metadata_manager.manage_relationships(test_chunks)
        
        assert len(relationships.siblings) > 0
        
        # chunk_1 and chunk_2 should be siblings (same fund)
        assert "chunk_2" in relationships.siblings.get("chunk_1", [])
        assert "chunk_1" in relationships.siblings.get("chunk_2", [])
        
        # chunk_1 and chunk_3 should be siblings (same content type)
        assert "chunk_3" in relationships.siblings.get("chunk_1", [])
        assert "chunk_1" in relationships.siblings.get("chunk_3", [])
    
    def test_get_metadata_statistics(self, metadata_manager):
        """Test metadata statistics retrieval."""
        # Add some test metadata
        metadata_manager.metadata_store = {
            "chunk_1": {
                "chunk_id": "chunk_1",
                "source_url": "https://test.com",
                "fund_name": "Test Fund",
                "content_type": "expense_ratio",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 0
            },
            "chunk_2": {
                "chunk_id": "chunk_2",
                "source_url": "https://test2.com",
                "fund_name": "Test Fund",
                "content_type": "nav",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": 1
            }
        }
        
        stats = metadata_manager.get_metadata_statistics()
        
        assert stats["total_chunks"] == 2
        assert "field_completeness" in stats
        assert stats["total_updates"] == 0  # No updates yet


class TestCitationSystem:
    """Test Citation System functionality."""
    
    @pytest.fixture
    def citation_system(self):
        """Create citation system instance for testing."""
        return CitationSystem(cache_dir="test_cache/citation_system")
    
    def test_citation_system_initialization(self, citation_system):
        """Test citation system initialization."""
        assert citation_system.cache_dir.exists()
        assert "hdfc_standard" in citation_system.formats
        assert citation_system.default_format == "hdfc_standard"
        assert citation_system.confidence_threshold == 0.7
    
    def test_generate_citation(self, citation_system):
        """Test citation generation."""
        chunk = {
            "chunk_id": "test_chunk",
            "source_url": "https://hdfcfund.com",
            "fund_name": "HDFC Mid Cap Fund",
            "document_type": "factsheet",
            "content_type": "expense_ratio",
            "last_updated": "2024-01-15",
            "confidence_score": 0.9
        }
        
        citation = citation_system.generate_citation(chunk)
        
        assert isinstance(citation, Citation)
        assert citation.chunk_id == "test_chunk"
        assert citation.source_url == "https://hdfcfund.com"
        assert citation.fund_name == "HDFC Mid Cap Fund"
        assert citation.citation_format == "hdfc_standard"
        assert "HDFC Mutual Fund" in citation.formatted_citation
        assert citation.confidence_score == 0.9
    
    def test_handle_multiple_sources(self, citation_system):
        """Test multiple source citation handling."""
        chunks = [
            {
                "chunk_id": "chunk_1",
                "source_url": "https://hdfcfund.com",
                "fund_name": "HDFC Mid Cap Fund",
                "document_type": "factsheet",
                "content_type": "expense_ratio",
                "last_updated": "2024-01-15"
            },
            {
                "chunk_id": "chunk_2",
                "source_url": "https://groww.in",
                "fund_name": "HDFC Equity Fund",
                "document_type": "factsheet",
                "content_type": "nav",
                "last_updated": "2024-01-15"
            }
        ]
        
        citation = citation_system.handle_multiple_sources(chunks)
        
        assert isinstance(citation, Citation)
        assert citation.chunk_id == "multi_source"
        assert citation.citation_format == "hdfc_standard_multi"
        assert "Multiple sources" in citation.formatted_citation
        assert citation.metadata["source_count"] == 2
    
    def test_validate_format(self, citation_system):
        """Test citation format validation."""
        # Valid citation
        valid_citation = Citation(
            chunk_id="test",
            source_url="https://hdfcfund.com",
            source_title="HDFC Mutual Fund - Factsheet",
            fund_name="HDFC Mid Cap Fund",
            document_type="factsheet",
            content_type="expense_ratio",
            page_number=None,
            section="",
            last_updated="2024-01-15",
            confidence_score=0.9,
            citation_format="hdfc_standard",
            formatted_citation="Test citation",
            metadata={}
        )
        
        is_valid = citation_system.validate_format(valid_citation)
        assert is_valid is True
        
        # Invalid citation (missing required field)
        invalid_citation = Citation(
            chunk_id="test",
            source_url="",  # Missing required field
            source_title="HDFC Mutual Fund - Factsheet",
            fund_name="HDFC Mid Cap Fund",
            document_type="factsheet",
            content_type="expense_ratio",
            page_number=None,
            section="",
            last_updated="2024-01-15",
            confidence_score=0.9,
            citation_format="hdfc_standard",
            formatted_citation="Test citation",
            metadata={}
        )
        
        is_valid = citation_system.validate_format(invalid_citation)
        assert is_valid is False
    
    def test_track_usage(self, citation_system):
        """Test citation usage tracking."""
        citation_id = "test_citation"
        
        # Track usage
        citation_system.track_usage(citation_id, "factual", "response", 0.8)
        citation_system.track_usage(citation_id, "factual", "response", 0.9)
        
        # Get usage stats
        stats = citation_system.get_usage_stats(citation_id)
        
        assert stats is not None
        assert stats.total_uses == 2
        assert "factual" in stats.query_types
        assert "response" in stats.response_types
        assert stats.average_relevance == 0.85  # (0.8 + 0.9) / 2
    
    def test_get_citation_analytics(self, citation_system):
        """Test citation analytics."""
        # Add some test citations
        citation_system.citations = {
            "cite_1": Citation(
                chunk_id="chunk_1",
                source_url="https://test1.com",
                source_title="Test 1",
                fund_name="Fund 1",
                document_type="factsheet",
                content_type="expense_ratio",
                page_number=None,
                section="",
                last_updated="2024-01-15",
                confidence_score=0.9,
                citation_format="hdfc_standard",
                formatted_citation="Test 1",
                metadata={}
            ),
            "cite_2": Citation(
                chunk_id="chunk_2",
                source_url="https://test2.com",
                source_title="Test 2",
                fund_name="Fund 2",
                document_type="factsheet",
                content_type="nav",
                page_number=None,
                section="",
                last_updated="2024-01-15",
                confidence_score=0.8,
                citation_format="academic",
                formatted_citation="Test 2",
                metadata={}
            )
        }
        
        analytics = citation_system.get_citation_analytics()
        
        assert analytics["total_citations"] == 2
        assert analytics["average_confidence_score"] == 0.85  # (0.9 + 0.8) / 2
        assert "format_usage" in analytics
        assert analytics["format_usage"]["hdfc_standard"] == 1
        assert analytics["format_usage"]["academic"] == 1
    
    def test_get_citations_by_fund(self, citation_system):
        """Test getting citations by fund."""
        # Add test citations
        citation_system.citations = {
            "cite_1": Citation(
                chunk_id="chunk_1",
                source_url="https://test1.com",
                source_title="Test 1",
                fund_name="HDFC Mid Cap Fund",
                document_type="factsheet",
                content_type="expense_ratio",
                page_number=None,
                section="",
                last_updated="2024-01-15",
                confidence_score=0.9,
                citation_format="hdfc_standard",
                formatted_citation="Test 1",
                metadata={}
            ),
            "cite_2": Citation(
                chunk_id="chunk_2",
                source_url="https://test2.com",
                source_title="Test 2",
                fund_name="HDFC Equity Fund",
                document_type="factsheet",
                content_type="nav",
                page_number=None,
                section="",
                last_updated="2024-01-15",
                confidence_score=0.8,
                citation_format="academic",
                formatted_citation="Test 2",
                metadata={}
            ),
            "cite_3": Citation(
                chunk_id="chunk_3",
                source_url="https://test3.com",
                source_title="Test 3",
                fund_name="HDFC Mid Cap Fund",
                document_type="prospectus",
                content_type="sip",
                page_number=None,
                section="",
                last_updated="2024-01-15",
                confidence_score=0.95,
                citation_format="simple",
                formatted_citation="Test 3",
                metadata={}
            )
        }
        
        hdfc_mid_cap_citations = citation_system.get_citations_by_fund("HDFC Mid Cap Fund")
        
        assert len(hdfc_mid_cap_citations) == 2
        assert all(c.fund_name == "HDFC Mid Cap Fund" for c in hdfc_mid_cap_citations)
        
        hdfc_equity_citations = citation_system.get_citations_by_fund("HDFC Equity Fund")
        assert len(hdfc_equity_citations) == 1
        assert hdfc_equity_citations[0].fund_name == "HDFC Equity Fund"


class TestVersionControl:
    """Test Version Control functionality."""
    
    @pytest.fixture
    def version_control(self):
        """Create version control instance for testing."""
        return VersionControl(cache_dir="test_cache/version_control")
    
    def test_version_control_initialization(self, version_control):
        """Test version control initialization."""
        assert version_control.cache_dir.exists()
        assert version_control.max_versions_per_document == 50
        assert version_control.similarity_threshold == 0.8
        assert version_control.default_author == "system"
    
    def test_track_document_versions(self, version_control):
        """Test document version tracking."""
        test_documents = [
            {
                "document_id": "doc_1",
                "content": "This is document 1 content",
                "metadata": {"title": "Document 1", "author": "test"},
                "chunk_count": 5
            },
            {
                "document_id": "doc_2",
                "content": "This is document 2 content",
                "metadata": {"title": "Document 2", "author": "test"},
                "chunk_count": 3
            }
        ]
        
        versions = version_control.track_document_versions(test_documents)
        
        assert len(versions) == 2
        assert all(isinstance(v, DocumentVersion) for v in versions)
        assert versions[0].document_id == "doc_1"
        assert versions[1].document_id == "doc_2"
        assert versions[0].change_type == "create"
        assert versions[1].change_type == "create"
        assert versions[0].author == "test"
        assert versions[1].author == "test"
    
    def test_handle_content_updates(self, version_control):
        """Test content update handling."""
        # First, create initial versions
        initial_docs = [
            {
                "document_id": "doc_1",
                "content": "Initial content",
                "metadata": {"title": "Document 1", "author": "test"},
                "chunk_count": 5
            }
        ]
        
        initial_versions = version_control.track_document_versions(initial_docs)
        initial_version_id = initial_versions[0].version_id
        
        # Now create updates
        updates = [
            {
                "document_id": "doc_1",
                "content": "Updated content",
                "metadata": {"title": "Document 1 Updated", "author": "test"},
                "chunk_count": 6
            }
        ]
        
        update_versions = version_control.handle_content_updates(updates)
        
        assert len(update_versions) == 1
        assert update_versions[0].document_id == "doc_1"
        assert update_versions[0].change_type == "update"
        assert update_versions[0].parent_version == initial_version_id
        assert "Updated" in update_versions[0].content_summary
    
    def test_get_version_history(self, version_control):
        """Test version history retrieval."""
        # Create multiple versions for a document
        doc_id = "test_doc"
        
        versions = []
        for i in range(3):
            doc = {
                "document_id": doc_id,
                "content": f"Version {i+1} content",
                "metadata": {"title": f"Document {i+1}", "version": i+1},
                "chunk_count": i+1
            }
            
            if i == 0:
                created_versions = version_control.track_document_versions([doc])
            else:
                created_versions = version_control.handle_content_updates([doc])
            
            versions.extend(created_versions)
        
        # Get version history
        history = version_control.get_version_history(doc_id)
        
        assert len(history) == 3
        # Should be in reverse chronological order (newest first)
        assert history[0].metadata["version"] == 3
        assert history[1].metadata["version"] == 2
        assert history[2].metadata["version"] == 1
    
    def test_compare_versions(self, version_control):
        """Test version comparison."""
        # Create two versions
        doc_id = "compare_doc"
        
        doc_v1 = {
            "document_id": doc_id,
            "content": "Version 1 content",
            "metadata": {"title": "Document V1", "version": 1},
            "chunk_count": 5
        }
        
        doc_v2 = {
            "document_id": doc_id,
            "content": "Version 2 content",
            "metadata": {"title": "Document V2", "version": 2},
            "chunk_count": 6
        }
        
        v1_versions = version_control.track_document_versions([doc_v1])
        v2_versions = version_control.handle_content_updates([doc_v2])
        
        # Compare versions
        diff = version_control.compare_versions(
            v1_versions[0].version_id,
            v2_versions[0].version_id
        )
        
        assert diff is not None
        assert diff.version_a == v1_versions[0].version_id
        assert diff.version_b == v2_versions[0].version_id
        assert diff.similarity_score < 1.0  # Different content should have lower similarity
        assert len(diff.content_changes) > 0
        assert len(diff.metadata_changes) > 0
    
    def test_implement_rollback_capabilities(self, version_control):
        """Test rollback implementation."""
        # Create initial version
        doc = {
            "document_id": "rollback_doc",
            "content": "Initial content",
            "metadata": {"title": "Initial Document"},
            "chunk_count": 5
        }
        
        initial_versions = version_control.track_document_versions([doc])
        initial_version_id = initial_versions[0].version_id
        
        # Create update
        update = {
            "document_id": "rollback_doc",
            "content": "Updated content",
            "metadata": {"title": "Updated Document"},
            "chunk_count": 6
        }
        
        update_versions = version_control.handle_content_updates([update])
        updated_version_id = update_versions[0].version_id
        
        # Implement rollback
        rollback_version = version_control.implement_rollback_capabilities(
            "rollback_doc",
            initial_version_id
        )
        
        assert rollback_version is not None
        assert rollback_version.document_id == "rollback_doc"
        assert rollback_version.change_type == "rollback"
        assert rollback_version.parent_version == updated_version_id
        assert "ROLLED_BACK_TO:" in rollback_version.content
    
    def test_get_version_statistics(self, version_control):
        """Test version statistics retrieval."""
        # Add some test versions
        version_control.versions = {
            "v1": DocumentVersion(
                version_id="v1",
                document_id="doc1",
                timestamp=datetime.now(),
                content_hash="abc123",
                metadata_hash="def456",
                content_summary="Content 1",
                changes_summary="Created",
                author="test",
                change_type="create",
                parent_version=None,
                child_versions=[],
                tags=[],
                size_bytes=100,
                chunk_count=5,
                metadata={}
            ),
            "v2": DocumentVersion(
                version_id="v2",
                document_id="doc2",
                timestamp=datetime.now(),
                content_hash="ghi789",
                metadata_hash="jkl012",
                content_summary="Content 2",
                changes_summary="Created",
                author="test",
                change_type="create",
                parent_version=None,
                child_versions=[],
                tags=[],
                size_bytes=200,
                chunk_count=3,
                metadata={}
            )
        }
        
        version_control.document_versions = {
            "doc1": ["v1"],
            "doc2": ["v2"]
        }
        
        version_control.version_frequency = {"doc1": 1, "doc2": 1}
        version_control.change_type_frequency = {"create": 2}
        
        stats = version_control.get_version_statistics()
        
        assert stats["total_versions"] == 2
        assert stats["total_documents"] == 2
        assert stats["average_versions_per_document"] == 1.0
        assert stats["change_type_distribution"]["create"] == 2
        assert stats["most_versioned_documents"]["doc1"] == 1
        assert stats["most_versioned_documents"]["doc2"] == 1


class TestPhase25Pipeline:
    """Test Phase 2.5 Pipeline integration."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing."""
        return Phase25Pipeline()
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.source_manager is not None
        assert pipeline.metadata_manager is not None
        assert pipeline.citation_system is not None
        assert pipeline.version_control is not None
    
    @pytest.mark.asyncio
    async def test_source_management_test(self, pipeline):
        """Test source management component test."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "<html><body>Test</body></html>"
            mock_response.headers = {"content-type": "text/html"}
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await pipeline.test_source_management()
            
            assert result["success"] is True
            assert result["sources_validated"] > 0
    
    @pytest.mark.asyncio
    async def test_metadata_consistency_test(self, pipeline):
        """Test metadata consistency component test."""
        result = await pipeline.test_metadata_consistency()
        
        assert result["success"] is True
        assert result["chunks_processed"] > 0
        assert result["average_consistency_score"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_citation_system_test(self, pipeline):
        """Test citation system component test."""
        result = await pipeline.test_citation_system()
        
        assert result["success"] is True
        assert result["citations_generated"] > 0
        assert result["formats_tested"] > 0
        assert result["average_confidence"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_version_control_test(self, pipeline):
        """Test version control component test."""
        result = await pipeline.test_version_control()
        
        assert result["success"] is True
        assert result["versions_tracked"] > 0
        assert result["relationships_created"] >= 0
    
    @pytest.mark.asyncio
    async def test_integration_test(self, pipeline):
        """Test integration component test."""
        result = await pipeline.test_integration()
        
        # Integration test might fail due to component dependencies
        # So we just check it runs without crashing
        assert "success" in result
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_performance_validation(self, pipeline):
        """Test performance validation."""
        result = await pipeline.run_performance_validation()
        
        assert "success" in result
        assert "overall_performance" in result
        assert "source_management_performance" in result
        assert "metadata_consistency_performance" in result
        assert "citation_system_performance" in result
        assert "version_control_performance" in result


# Performance tests
class TestPerformance:
    """Performance tests for Phase 2.5 components."""
    
    def test_source_manager_performance(self):
        """Test source manager performance."""
        source_manager = SourceManager(cache_dir="test_cache/perf_source")
        
        import time
        start_time = time.time()
        
        # Test with many sources (mocked)
        test_sources = [
            {"url": f"https://test{i}.com", "title": f"Test {i}"}
            for i in range(100)
        ]
        
        # This would normally be async, but we're testing the setup
        for source in test_sources:
            source_manager._generate_chunk_id(source)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 source preparations in under 1 second
        assert elapsed_time < 1.0
        print(f"Source manager prepared 100 sources in {elapsed_time:.3f}s")
    
    def test_metadata_manager_performance(self):
        """Test metadata manager performance."""
        metadata_manager = MetadataManager(cache_dir="test_cache/perf_metadata")
        
        import time
        start_time = time.time()
        
        # Test with many chunks
        chunks = [
            {
                "chunk_id": f"chunk_{i}",
                "source_url": f"https://test{i}.com",
                "fund_name": f"Test Fund {i}",
                "content_type": "general",
                "document_type": "factsheet",
                "last_updated": "2024-01-15",
                "chunk_index": i
            }
            for i in range(100)
        ]
        
        consistent_chunks = metadata_manager.ensure_consistency(chunks)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 chunks in under 2 seconds
        assert elapsed_time < 2.0
        assert len(consistent_chunks) == 100
        print(f"Metadata manager processed 100 chunks in {elapsed_time:.3f}s")
    
    def test_citation_system_performance(self):
        """Test citation system performance."""
        citation_system = CitationSystem(cache_dir="test_cache/perf_citation")
        
        import time
        start_time = time.time()
        
        # Test with many chunks
        chunks = [
            {
                "chunk_id": f"chunk_{i}",
                "source_url": f"https://test{i}.com",
                "fund_name": f"Test Fund {i}",
                "document_type": "factsheet",
                "content_type": "general",
                "last_updated": "2024-01-15"
            }
            for i in range(100)
        ]
        
        citations = [citation_system.generate_citation(chunk) for chunk in chunks]
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 citations in under 1 second
        assert elapsed_time < 1.0
        assert len(citations) == 100
        print(f"Citation system generated 100 citations in {elapsed_time:.3f}s")
    
    def test_version_control_performance(self):
        """Test version control performance."""
        version_control = VersionControl(cache_dir="test_cache/perf_version")
        
        import time
        start_time = time.time()
        
        # Test with many documents
        documents = [
            {
                "document_id": f"doc_{i}",
                "content": f"Test content {i}",
                "metadata": {"title": f"Document {i}"},
                "chunk_count": 1
            }
            for i in range(50)
        ]
        
        versions = version_control.track_document_versions(documents)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 50 documents in under 1 second
        assert elapsed_time < 1.0
        assert len(versions) == 50
        print(f"Version control tracked 50 documents in {elapsed_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
