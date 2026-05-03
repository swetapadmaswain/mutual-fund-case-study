"""
Tests for Phase 2.1 chunking components.
"""
import pytest
from unittest.mock import Mock, patch
from src.rag.chunking.document_processor import TextPreprocessor, ProcessedDocument
from src.rag.chunking.chunker import SemanticChunker, Chunk, ChunkingPipeline
from src.rag.chunking.metadata_enricher import MetadataEnricher, MetadataEnrichmentPipeline
from src.rag.chunking.chunk_validator import ChunkValidator, ValidationStatus


class TestTextPreprocessor:
    """Test cases for TextPreprocessor class."""
    
    @pytest.fixture
    def preprocessor(self):
        """Create a preprocessor instance for testing."""
        return TextPreprocessor()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        <html>
        <body>
        <h1>HDFC Mid Cap Fund</h1>
        <p>This fund has an expense ratio of 0.85% and exit load of 1%.</p>
        <p>Minimum SIP amount is Rs. 500.</p>
        <script>alert('test');</script>
        <style>body {color: red;}</style>
        </body>
        </html>
        """
    
    def test_clean_text(self, preprocessor, sample_content):
        """Test text cleaning functionality."""
        cleaned = preprocessor.clean_text(sample_content)
        
        assert 'HDFC Mid Cap Fund' in cleaned
        assert '0.85%' in cleaned
        assert '1%' in cleaned
        assert '₹500' in cleaned
        assert '<script>' not in cleaned
        assert '<style>' not in cleaned
        assert '<html>' not in cleaned
    
    def test_normalize_financial_symbols(self, preprocessor):
        """Test financial symbol normalization."""
        test_cases = [
            ("Rs. 500", "₹500"),
            ("INR 1000", "₹1000"),
            ("Rupee 750", "₹750"),
            ("0.85 %", "0.85%"),
            ("1.5%", "1.5%")
        ]
        
        for input_text, expected in test_cases:
            result = preprocessor._normalize_financial_symbols(input_text)
            assert expected in result
    
    def test_extract_financial_data(self, preprocessor):
        """Test financial data extraction."""
        text = "Expense ratio is 0.85% and exit load is 1%. SIP amount is ₹500."
        data = preprocessor.extract_financial_data(text)
        
        assert '0.85%' in data.get('expense_ratios', [])
        assert '1%' in data.get('exit_loads', [])
        assert '500' in data.get('sip_amounts', [])
    
    def test_process_document(self, preprocessor, sample_content):
        """Test complete document processing."""
        metadata = {'fund_name': 'HDFC Mid Cap Fund', 'url': 'https://example.com'}
        
        processed_doc = preprocessor.process_document(sample_content, metadata)
        
        assert isinstance(processed_doc, ProcessedDocument)
        assert processed_doc.original_content == sample_content
        assert processed_doc.cleaned_content != sample_content
        assert processed_doc.content_hash is not None
        assert processed_doc.processing_stats is not None
        assert 'fund_name' in processed_doc.metadata


class TestSemanticChunker:
    """Test cases for SemanticChunker class."""
    
    @pytest.fixture
    def chunker(self):
        """Create a chunker instance for testing."""
        return SemanticChunker(min_chunk_size=50, max_chunk_size=200, overlap_tokens=20)
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample processed document."""
        content = """
        HDFC Mid Cap Fund is a mutual fund scheme. The expense ratio is 0.85%. 
        The exit load is 1% if redeemed within 365 days. Minimum SIP amount is ₹500.
        The fund invests in mid-cap companies. The benchmark is Nifty Midcap 100.
        Risk level is moderately high. NAV is ₹145.67 as of today.
        """
        
        metadata = {
            'fund_name': 'HDFC Mid Cap Fund',
            'url': 'https://example.com',
            'content_hash': 'abc123'
        }
        
        return ProcessedDocument(
            original_content=content,
            cleaned_content=content,
            metadata=metadata,
            processing_stats={'compression_ratio': 0.9},
            content_hash='abc123'
        )
    
    def test_create_chunks(self, chunker, sample_document):
        """Test chunk creation."""
        chunks = chunker.create_chunks(sample_document)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.metadata for chunk in chunks)
        assert all(chunk.chunk_id for chunk in chunks)
    
    def test_split_into_sentences(self, chunker):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = chunker._split_into_sentences(text)
        
        assert len(sentences) == 4
        assert all(sentence.strip() for sentence in sentences)
    
    def test_estimate_tokens(self, chunker):
        """Test token estimation."""
        text = "This is a test sentence with some words."
        tokens = chunker._estimate_tokens(text)
        
        assert tokens > 0
        assert tokens <= len(text)  # Tokens should be less than characters
    
    def test_has_financial_context(self, chunker):
        """Test financial context detection."""
        financial_text = "The expense ratio is 0.85% and NAV is ₹145.67"
        non_financial_text = "This is just a regular text about weather."
        
        assert chunker._has_financial_context(financial_text) is True
        assert chunker._has_financial_context(non_financial_text) is False
    
    def test_optimize_chunk_size(self, chunker):
        """Test chunk size optimization."""
        # Create test chunks
        small_chunk = Mock()
        small_chunk.token_count = 30
        small_chunk.metadata = {}
        
        large_chunk = Mock()
        large_chunk.token_count = 250
        large_chunk.metadata = {}
        
        optimal_chunk = Mock()
        optimal_chunk.token_count = 150
        optimal_chunk.metadata = {}
        
        chunks = [small_chunk, large_chunk, optimal_chunk]
        optimized = chunker.optimize_chunk_size(chunks)
        
        assert len(optimized) == 3
        assert optimized[0].metadata['size_optimization'] == 'too_small'
        assert optimized[1].metadata['size_optimization'] == 'too_large'
        assert optimized[2].metadata['size_optimization'] == 'optimal'


class TestMetadataEnricher:
    """Test cases for MetadataEnricher class."""
    
    @pytest.fixture
    def enricher(self):
        """Create an enricher instance for testing."""
        return MetadataEnricher()
    
    @pytest.fixture
    def sample_chunk(self):
        """Create a sample chunk."""
        content = "HDFC Mid Cap Fund has expense ratio of 0.85% and exit load of 1%."
        
        metadata = {
            'chunk_id': 'test_chunk_1',
            'chunk_index': 0,
            'total_chunks': 1,
            'token_count': 15,
            'source_document_id': 'doc123'
        }
        
        return Chunk(
            chunk_id='test_chunk_1',
            content=content,
            metadata=metadata,
            chunk_index=0,
            total_chunks=1,
            token_count=15,
            source_document_id='doc123'
        )
    
    @pytest.fixture
    def source_metadata(self):
        """Sample source metadata."""
        return {
            'fund_name': 'HDFC Mid Cap Fund',
            'url': 'https://example.com',
            'title': 'HDFC Mid Cap Fund Information'
        }
    
    def test_enrich_chunk_metadata(self, enricher, sample_chunk, source_metadata):
        """Test chunk metadata enrichment."""
        enriched_chunk = enricher.enrich_chunk_metadata(sample_chunk, source_metadata)
        
        assert 'hierarchical_keys' in enriched_chunk.metadata
        assert 'content_type' in enriched_chunk.metadata
        assert 'financial_data' in enriched_chunk.metadata
        assert 'citation_info' in enriched_chunk.metadata
        assert 'retrieval_tags' in enriched_chunk.metadata
        assert 'quality_score' in enriched_chunk.metadata
        assert enriched_chunk.metadata['quality_score'] >= 0.0
        assert enriched_chunk.metadata['quality_score'] <= 1.0
    
    def test_create_hierarchical_keys(self, enricher, sample_chunk, source_metadata):
        """Test hierarchical key creation."""
        keys = enricher._create_hierarchical_keys(sample_chunk, source_metadata)
        
        assert len(keys) > 0
        assert any('fund:' in key for key in keys)
        assert any('chunk:' in key for key in keys)
    
    def test_determine_content_type(self, enricher):
        """Test content type determination."""
        expense_text = "The expense ratio is 0.85%"
        nav_text = "Current NAV is ₹145.67"
        general_text = "This is general information"
        
        assert enricher._determine_content_type(expense_text) == 'expense_ratio'
        assert enricher._determine_content_type(nav_text) == 'nav'
        assert enricher._determine_content_type(general_text) == 'general'
    
    def test_extract_financial_data(self, enricher):
        """Test financial data extraction."""
        text = "Expense ratio: 0.85%, Exit load: 1%, NAV: ₹145.67, SIP: ₹500"
        data = enricher._extract_financial_data(text)
        
        assert '0.85%' in data.get('expense_ratios', [])
        assert '1%' in data.get('exit_loads', [])
        assert '145.67' in data.get('nav_values', [])
        assert '500' in data.get('sip_amounts', [])
    
    def test_generate_retrieval_tags(self, enricher):
        """Test retrieval tag generation."""
        performance_text = "The fund returns are good and performance is stable"
        tags = enricher._generate_retrieval_tags(performance_text, 'performance')
        
        assert 'performance' in tags
        assert 'returns' in tags
    
    def test_calculate_quality_score(self, enricher, sample_chunk):
        """Test quality score calculation."""
        enriched_metadata = sample_chunk.metadata.copy()
        enriched_metadata.update({
            'financial_data': {'expense_ratios': ['0.85%']},
            'has_financial_context': True,
            'retrieval_tags': ['fund_info', 'fees_charges'],
            'citation_info': {'source_url': 'https://example.com', 'fund_name': 'HDFC'}
        })
        
        score = enricher._calculate_quality_score(sample_chunk, enriched_metadata)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a good score with all the metadata


class TestChunkValidator:
    """Test cases for ChunkValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return ChunkValidator()
    
    @pytest.fixture
    def valid_chunk(self):
        """Create a valid chunk for testing."""
        content = "HDFC Mid Cap Fund has expense ratio of 0.85% and minimum SIP of ₹500."
        
        metadata = {
            'chunk_id': 'valid_chunk_1',
            'source_document_id': 'doc123',
            'chunk_index': 0,
            'total_chunks': 1,
            'content_type': 'expense_ratio',
            'citation_info': {
                'source_url': 'https://example.com',
                'fund_name': 'HDFC Mid Cap Fund'
            },
            'retrieval_tags': ['fund_info', 'fees_charges'],
            'quality_score': 0.8
        }
        
        return Chunk(
            chunk_id='valid_chunk_1',
            content=content,
            metadata=metadata,
            chunk_index=0,
            total_chunks=1,
            token_count=15,
            source_document_id='doc123'
        )
    
    @pytest.fixture
    def invalid_chunk(self):
        """Create an invalid chunk for testing."""
        content = "You should invest in this fund as it's the best option."
        
        metadata = {
            'chunk_id': 'invalid_chunk_1',
            'source_document_id': 'doc123',
            'chunk_index': 0,
            'total_chunks': 1
        }
        
        return Chunk(
            chunk_id='invalid_chunk_1',
            content=content,
            metadata=metadata,
            chunk_index=0,
            total_chunks=1,
            token_count=10,
            source_document_id='doc123'
        )
    
    def test_validate_chunk_valid(self, validator, valid_chunk):
        """Test validation of a valid chunk."""
        result = validator.validate_chunk(valid_chunk)
        
        assert result.status == ValidationStatus.VALID
        assert result.score > 0.7
        assert len(result.errors) == 0
        assert len(result.warnings) <= 1
    
    def test_validate_chunk_invalid(self, validator, invalid_chunk):
        """Test validation of an invalid chunk."""
        result = validator.validate_chunk(invalid_chunk)
        
        assert result.status == ValidationStatus.INVALID
        assert result.score < 0.5
        assert len(result.errors) > 0
        # Should detect advisory language
        assert any('advisory' in error.lower() for error in result.errors)
    
    def test_validate_content(self, validator):
        """Test content validation."""
        # Valid financial content
        valid_content = "Expense ratio is 0.85% and NAV is ₹145.67."
        result = validator._validate_content(valid_content)
        
        assert len(result['errors']) == 0
        assert result['score_adjustment'] >= 0
        
        # Invalid content (empty)
        empty_content = ""
        result = validator._validate_content(empty_content)
        
        assert len(result['errors']) > 0
        assert result['score_adjustment'] < 0
    
    def test_validate_metadata(self, validator, valid_chunk, invalid_chunk):
        """Test metadata validation."""
        # Valid metadata
        result = validator._validate_metadata(valid_chunk.metadata)
        assert len(result['errors']) == 0
        
        # Invalid metadata (missing required fields)
        result = validator._validate_metadata(invalid_chunk.metadata)
        assert len(result['errors']) > 0
    
    def test_validate_compliance(self, validator):
        """Test compliance validation."""
        # Compliant content
        compliant_content = "The fund has expense ratio of 0.85%."
        result = validator._validate_compliance(compliant_content)
        
        assert len(result['errors']) == 0
        assert result['score_adjustment'] >= 0
        
        # Non-compliant content (advisory)
        non_compliant_content = "You should invest in this fund."
        result = validator._validate_compliance(non_compliant_content)
        
        assert len(result['errors']) > 0
        assert result['score_adjustment'] < 0
    
    def test_validate_chunks_batch(self, validator, valid_chunk, invalid_chunk):
        """Test batch validation."""
        chunks = [valid_chunk, invalid_chunk]
        results = validator.validate_chunks_batch(chunks)
        
        assert len(results) == 2
        assert results[0].status == ValidationStatus.VALID
        assert results[1].status == ValidationStatus.INVALID
    
    def test_filter_chunks_by_quality(self, validator, valid_chunk, invalid_chunk):
        """Test quality filtering."""
        chunks = [valid_chunk, invalid_chunk]
        high_quality, low_quality = validator.filter_chunks_by_quality(chunks, min_score=0.5)
        
        assert len(high_quality) == 1
        assert len(low_quality) == 1
        assert high_quality[0].chunk_id == valid_chunk.chunk_id
        assert low_quality[0].chunk_id == invalid_chunk.chunk_id


class TestIntegration:
    """Integration tests for Phase 2.1 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_chunking_pipeline(self):
        """Test end-to-end chunking pipeline."""
        from src.rag.chunking.main import Phase21Pipeline
        
        # Create mock Phase 1 data
        phase1_data = [{
            'cleaned_content': 'HDFC Mid Cap Fund has expense ratio of 0.85%.',
            'metadata': {
                'fund_name': 'HDFC Mid Cap Fund',
                'url': 'https://example.com'
            }
        }]
        
        # Mock the data loading
        with patch.object(Phase21Pipeline, 'load_phase1_data', return_value=phase1_data):
            pipeline = Phase21Pipeline()
            
            # Run the pipeline
            results = await pipeline.run_pipeline()
            
            assert results['success'] is True
            assert 'step_results' in results
            assert 'final_summary' in results
            
            # Check that all steps completed
            expected_steps = ['data_loading', 'document_processing', 'chunking', 
                            'metadata_enrichment', 'validation', 'quality_filtering', 'export']
            for step in expected_steps:
                assert step in results['step_results']
                assert results['step_results'][step]['success'] is True


if __name__ == "__main__":
    pytest.main([__file__])
