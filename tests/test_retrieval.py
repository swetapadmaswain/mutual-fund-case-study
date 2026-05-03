"""
Tests for Phase 2.3 retrieval system components.
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.rag.retrieval.query_processor import QueryProcessor, ProcessedQuery, QueryType, QueryIntent
from src.rag.retrieval.search_engine import SemanticSearchEngine, SearchStrategy, SearchResult, SearchContext
from src.rag.retrieval.context_builder import ContextBuilder, BuiltContext, ContextWindow
from src.rag.retrieval.source_ranker import SourceRanker, RankedSource, RankingScore, RankingCriteria


class TestQueryProcessor:
    """Test cases for QueryProcessor class."""
    
    @pytest.fixture
    def query_processor(self):
        """Create a query processor instance for testing."""
        return QueryProcessor()
    
    @pytest.fixture
    def sample_queries(self):
        """Sample queries for testing."""
        return [
            "What is the expense ratio of HDFC Mid Cap Fund?",
            "HDFC Large Cap Fund SIP details",
            "Which fund should I invest in?",
            "How to download my fund statement?",
            "Current NAV of HDFC Equity Fund",
            "Risk level of ELSS funds"
        ]
    
    def test_initialization(self, query_processor):
        """Test query processor initialization."""
        assert query_processor.entity_patterns is not None
        assert 'fund_names' in query_processor.entity_patterns
        assert 'financial_terms' in query_processor.entity_patterns
        assert query_processor.query_type_patterns is not None
        assert query_processor.intent_patterns is not None
    
    def test_clean_query(self, query_processor):
        """Test query cleaning."""
        # Normal text
        query = "What is the expense ratio?"
        cleaned = query_processor._clean_query(query)
        assert cleaned == "what is the expense ratio?"
        
        # Text with special characters
        query = "What is the expense ratio? (HDFC Fund) ₹1000"
        cleaned = query_processor._clean_query(query)
        assert "what is the expense ratio hdfc fund ₹1000" in cleaned
        
        # Empty text
        cleaned = query_processor._clean_query("")
        assert cleaned == ""
        
        # Text with extra whitespace
        query = "What   is   the   expense   ratio?"
        cleaned = query_processor._clean_query(query)
        assert cleaned == "what is the expense ratio?"
    
    def test_extract_entities(self, query_processor):
        """Test entity extraction."""
        query = "HDFC Mid Cap Fund expense ratio is 0.85%"
        entities = query_processor._extract_entities(query)
        
        assert len(entities) > 0
        assert any('hdfc' in entity.lower() for entity in entities)
        assert any('mid' in entity.lower() for entity in entities)
        assert any('expense' in entity.lower() for entity in entities)
    
    def test_extract_keywords(self, query_processor):
        """Test keyword extraction."""
        query = "HDFC Mid Cap Fund expense ratio investment details"
        keywords = query_processor._extract_keywords(query)
        
        assert len(keywords) > 0
        assert 'fund' in keywords
        assert 'investment' in keywords
        assert 'expense' in keywords
        assert 'ratio' in keywords
    
    def test_classify_query_type(self, query_processor):
        """Test query type classification."""
        # Advisory query
        query = "Should I invest in HDFC Mid Cap Fund?"
        query_type = query_processor._classify_query_type(query)
        assert query_type == QueryType.ADVISORY
        
        # Performance query
        query = "HDFC fund performance and returns"
        query_type = query_processor._classify_query_type(query)
        assert query_type == QueryType.PERFORMANCE
        
        # Procedural query
        query = "How to download fund statement?"
        query_type = query_processor._classify_query_type(query)
        assert query_type == QueryType.PROCEDURAL
        
        # Factual query
        query = "What is the expense ratio?"
        query_type = query_processor._classify_query_type(query)
        assert query_type == QueryType.FACTUAL
    
    def test_determine_query_intent(self, query_processor):
        """Test query intent determination."""
        # Expense ratio intent
        query = "What is the expense ratio of HDFC Mid Cap Fund?"
        intent = query_processor._determine_query_intent(query)
        assert intent == QueryIntent.EXPENSE_RATIO
        
        # SIP intent
        query = "HDFC Large Cap Fund SIP details"
        intent = query_processor._determine_query_intent(query)
        assert intent == QueryIntent.SIP
        
        # NAV intent
        query = "Current NAV of HDFC Equity Fund"
        intent = query_processor._determine_query_intent(query)
        assert intent == QueryIntent.NAV
        
        # Investment guidance intent
        query = "Should I invest in mutual funds?"
        intent = query_processor._determine_query_intent(query)
        assert intent == QueryIntent.INVESTMENT_GUIDANCE
    
    def test_generate_filters(self, query_processor):
        """Test filter generation."""
        entities = ["hdfc mid cap fund", "expense ratio", "0.85%"]
        keywords = ["fund", "expense", "ratio"]
        intent = QueryIntent.EXPENSE_RATIO
        
        filters = query_processor._generate_filters(entities, keywords, intent)
        
        assert 'fund_names' in filters
        assert 'content_types' in filters
        assert 'expense_ratio' in filters['content_types']
    
    def test_calculate_confidence(self, query_processor):
        """Test confidence calculation."""
        query_type = QueryType.FACTUAL
        query_intent = QueryIntent.EXPENSE_RATIO
        entities = ["hdfc", "expense", "ratio"]
        keywords = ["fund", "expense", "ratio", "what"]
        
        confidence = query_processor._calculate_confidence(query_type, query_intent, entities, keywords)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have good confidence with these inputs
    
    def test_process_query(self, query_processor):
        """Test complete query processing."""
        query = "What is the expense ratio of HDFC Mid Cap Fund?"
        
        processed_query = query_processor.process_query(query)
        
        assert isinstance(processed_query, ProcessedQuery)
        assert processed_query.original_query == query
        assert processed_query.cleaned_query == "what is the expense ratio of hdfc mid cap fund?"
        assert processed_query.query_type == QueryType.FACTUAL
        assert processed_query.query_intent == QueryIntent.EXPENSE_RATIO
        assert len(processed_query.entities) > 0
        assert len(processed_query.keywords) > 0
        assert 0.0 <= processed_query.confidence <= 1.0
    
    def test_batch_process_queries(self, query_processor, sample_queries):
        """Test batch query processing."""
        processed_queries = query_processor.batch_process_queries(sample_queries)
        
        assert len(processed_queries) == len(sample_queries)
        assert all(isinstance(pq, ProcessedQuery) for pq in processed_queries)
        
        # Check that advisory queries are identified
        advisory_queries = [pq for pq in processed_queries if pq.query_type == QueryType.ADVISORY]
        assert len(advisory_queries) > 0
    
    def test_get_query_statistics(self, query_processor, sample_queries):
        """Test query statistics."""
        processed_queries = query_processor.batch_process_queries(sample_queries)
        stats = query_processor.get_query_statistics(processed_queries)
        
        assert 'total_queries' in stats
        assert 'query_types' in stats
        assert 'query_intents' in stats
        assert 'average_confidence' in stats
        assert 'entity_coverage' in stats
        
        assert stats['total_queries'] == len(sample_queries)
        assert 0.0 <= stats['average_confidence'] <= 1.0


class TestSemanticSearchEngine:
    """Test cases for SemanticSearchEngine class."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_vector_db = Mock()
        mock_embedding_service = Mock()
        mock_hierarchical_db = Mock()
        
        return {
            'vector_database': mock_vector_db,
            'embedding_service': mock_embedding_service,
            'hierarchical_db': mock_hierarchical_db
        }
    
    @pytest.fixture
    def search_engine(self, mock_components):
        """Create a search engine instance for testing."""
        return SemanticSearchEngine(
            vector_database=mock_components['vector_database'],
            embedding_service=mock_components['embedding_service'],
            hierarchical_db=mock_components['hierarchical_db']
        )
    
    @pytest.fixture
    def sample_processed_query(self):
        """Create a sample processed query."""
        from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
        
        return ProcessedQuery(
            original_query="HDFC Mid Cap Fund expense ratio",
            cleaned_query="hdfc mid cap fund expense ratio",
            query_type=QueryType.FACTUAL,
            query_intent=QueryIntent.EXPENSE_RATIO,
            entities=["hdfc mid cap fund", "expense ratio"],
            keywords=["fund", "expense", "ratio"],
            filters={"fund_names": ["hdfc_mid_cap_fund"], "content_types": ["expense_ratio"]},
            confidence=0.85,
            processing_metadata={}
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results."""
        results = []
        for i in range(3):
            result = {
                'id': f'doc_{i}',
                'document': f'Content about HDFC Mid Cap Fund expense ratio {i}',
                'metadata': {
                    'chunk_id': f'chunk_{i}',
                    'hierarchical_fund': 'hdfc_mid_cap_fund',
                    'content_type': 'expense_ratio',
                    'quality_score': 0.8
                },
                'distance': 0.1 + i * 0.1,
                'similarity': 0.9 - i * 0.1
            }
            results.append(result)
        return results
    
    def test_initialization(self, search_engine, mock_components):
        """Test search engine initialization."""
        assert search_engine.vector_database == mock_components['vector_database']
        assert search_engine.embedding_service == mock_components['embedding_service']
        assert search_engine.hierarchical_db == mock_components['hierarchical_db']
        assert search_engine.default_similarity_threshold == 0.7
        assert search_engine.default_max_results == 5
    
    def test_determine_search_strategy(self, search_engine, sample_processed_query):
        """Test search strategy determination."""
        # Fund-focused query
        strategy = search_engine._determine_search_strategy(sample_processed_query)
        assert strategy == SearchStrategy.FUND_FOCUSED
        
        # Content-focused query
        sample_processed_query.filters = {'content_types': ['expense_ratio']}
        strategy = search_engine._determine_search_strategy(sample_processed_query)
        assert strategy == SearchStrategy.CONTENT_FOCUSED
        
        # Advisory query
        sample_processed_query.query_type = QueryType.ADVISORY
        strategy = search_engine._determine_search_strategy(sample_processed_query)
        assert strategy == SearchStrategy.HYBRID
        
        # General query
        sample_processed_query.filters = {}
        sample_processed_query.query_type = QueryType.GENERAL
        strategy = search_engine._determine_search_strategy(sample_processed_query)
        assert strategy == SearchStrategy.SEMANTIC
    
    @pytest.mark.asyncio
    async def test_search(self, search_engine, sample_processed_query, sample_search_results):
        """Test search functionality."""
        # Mock embedding service
        search_engine.embedding_service.embed_texts_async = Mock(return_value=[np.array([0.1, 0.2, 0.3])])
        
        # Mock vector database
        search_engine.vector_database.search = Mock(return_value=sample_search_results)
        
        # Execute search
        results = await search_engine.search(sample_processed_query)
        
        assert len(results) == 3
        assert all(isinstance(result, SearchResult) for result in results)
        assert results[0].similarity_score > results[1].similarity_score
        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3
    
    def test_build_metadata_filters(self, search_engine):
        """Test metadata filter building."""
        filters = {
            'fund_names': ['hdfc_mid_cap_fund'],
            'fund_types': ['mid_cap'],
            'content_types': ['expense_ratio']
        }
        
        metadata_filter = search_engine._build_metadata_filters(filters)
        
        assert 'hierarchical_fund' in metadata_filter
        assert 'hierarchical_type' in metadata_filter
        assert 'hierarchical_content' in metadata_filter
    
    def test_filter_by_similarity(self, search_engine, sample_search_results):
        """Test similarity filtering."""
        # Convert to SearchResult objects
        search_results = []
        for i, result in enumerate(sample_search_results):
            search_result = SearchResult(
                document_id=result['id'],
                chunk_id=result['metadata']['chunk_id'],
                content=result['document'],
                metadata=result['metadata'],
                similarity_score=result['similarity'],
                distance=result['distance'],
                rank=i + 1,
                search_strategy='semantic',
                retrieval_metadata={}
            )
            search_results.append(search_result)
        
        # Filter with high threshold
        filtered = search_engine._filter_by_similarity(search_results, 0.85)
        assert len(filtered) == 1  # Only the first result
        
        # Filter with low threshold
        filtered = search_engine._filter_by_similarity(search_results, 0.7)
        assert len(filtered) == 3  # All results
    
    def test_rank_results(self, search_engine, sample_search_results):
        """Test result ranking."""
        # Convert to SearchResult objects
        search_results = []
        for i, result in enumerate(sample_search_results):
            search_result = SearchResult(
                document_id=result['id'],
                chunk_id=result['metadata']['chunk_id'],
                content=result['document'],
                metadata=result['metadata'],
                similarity_score=result['similarity'],
                distance=result['distance'],
                rank=i + 1,
                search_strategy='semantic',
                retrieval_metadata={}
            )
            search_results.append(search_result)
        
        # Rank results
        ranked = search_engine.rank_results(search_results)
        
        assert len(ranked) == len(search_results)
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2
        assert ranked[2].rank == 3
        assert all('final_ranking_score' in result.retrieval_metadata for result in ranked)
    
    def test_configure_similarity_threshold(self, search_engine):
        """Test similarity threshold configuration."""
        # Valid threshold
        search_engine.configure_similarity_threshold(0.8)
        assert search_engine.default_similarity_threshold == 0.8
        
        # Invalid threshold
        with pytest.raises(ValueError):
            search_engine.configure_similarity_threshold(1.5)
    
    def test_get_search_statistics(self, search_engine, mock_components):
        """Test search statistics."""
        # Mock component stats
        mock_components['vector_database'].get_collection_stats.return_value = {
            'document_count': 100,
            'collection_name': 'test_collection',
            'embedding_dimension': 384
        }
        
        mock_components['hierarchical_db'].get_hierarchy_stats.return_value = {
            'total_funds': 5,
            'fund_types': ['mid_cap', 'large_cap'],
            'total_documents': 100
        }
        
        stats = search_engine.get_search_statistics()
        
        assert 'vector_database' in stats
        assert 'hierarchical_index' in stats
        assert 'search_configuration' in stats
        assert 'supported_strategies' in stats


class TestContextBuilder:
    """Test cases for ContextBuilder class."""
    
    @pytest.fixture
    def context_builder(self):
        """Create a context builder instance for testing."""
        return ContextBuilder(
            max_context_tokens=2000,
            window_overlap_tokens=50,
            min_relevance_threshold=0.5
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results."""
        results = []
        for i in range(3):
            result = SearchResult(
                document_id=f'doc_{i}',
                chunk_id=f'chunk_{i}',
                content=f'Content about HDFC Mid Cap Fund expense ratio {i}. This is test content.',
                metadata={
                    'hierarchical_fund': 'hdfc_mid_cap_fund',
                    'content_type': 'expense_ratio',
                    'quality_score': 0.8,
                    'citation_info': {
                        'source_url': 'https://groww.in/funds/hdfc-mid-cap',
                        'fund_name': 'HDFC Mid Cap Fund'
                    }
                },
                similarity_score=0.9 - i * 0.1,
                distance=0.1 + i * 0.1,
                rank=i + 1,
                search_strategy='semantic',
                retrieval_metadata={'effective_relevance': 0.9 - i * 0.1}
            )
            results.append(result)
        return results
    
    @pytest.fixture
    def sample_processed_query(self):
        """Create a sample processed query."""
        from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
        
        return ProcessedQuery(
            original_query="HDFC Mid Cap Fund expense ratio",
            cleaned_query="hdfc mid cap fund expense ratio",
            query_type=QueryType.FACTUAL,
            query_intent=QueryIntent.EXPENSE_RATIO,
            entities=["hdfc mid cap fund", "expense ratio"],
            keywords=["fund", "expense", "ratio"],
            filters={"fund_names": ["hdfc_mid_cap_fund"], "content_types": ["expense_ratio"]},
            confidence=0.85,
            processing_metadata={}
        )
    
    def test_initialization(self, context_builder):
        """Test context builder initialization."""
        assert context_builder.max_context_tokens == 2000
        assert context_builder.window_overlap_tokens == 50
        assert context_builder.min_relevance_threshold == 0.5
        assert 'relevance_first' in context_builder.context_strategies
        assert 'hybrid' in context_builder.context_strategies
    
    def test_filter_by_relevance(self, context_builder, sample_search_results):
        """Test relevance filtering."""
        # All results above threshold
        filtered = context_builder._filter_by_relevance(sample_search_results)
        assert len(filtered) == 3
        
        # High threshold
        context_builder.min_relevance_threshold = 0.85
        filtered = context_builder._filter_by_relevance(sample_search_results)
        assert len(filtered) == 1  # Only first result
        
        # Reset threshold
        context_builder.min_relevance_threshold = 0.5
    
    def test_build_by_relevance_first(self, context_builder, sample_search_results, sample_processed_query):
        """Test relevance-first context building."""
        context = SearchContext(
            query=sample_processed_query,
            embedding=np.array([0.1, 0.2, 0.3]),
            filters=sample_processed_query.filters,
            search_strategy=SearchStrategy.SEMANTIC,
            max_results=5,
            similarity_threshold=0.5,
            retrieval_metadata={}
        )
        
        windows = context_builder._build_by_relevance_first(sample_search_results, sample_processed_query, 2000)
        
        assert len(windows) == 3
        assert all(isinstance(window, ContextWindow) for window in windows)
        assert windows[0].relevance_score >= windows[1].relevance_score
        assert windows[1].relevance_score >= windows[2].relevance_score
    
    def test_build_by_fund_grouped(self, context_builder, sample_search_results, sample_processed_query):
        """Test fund-grouped context building."""
        context = SearchContext(
            query=sample_processed_query,
            embedding=np.array([0.1, 0.2, 0.3]),
            filters=sample_processed_query.filters,
            search_strategy=SearchStrategy.FUND_FOCUSED,
            max_results=5,
            similarity_threshold=0.5,
            retrieval_metadata={}
        )
        
        windows = context_builder._build_by_fund_grouped(sample_search_results, sample_processed_query, 2000)
        
        assert len(windows) == 3
        assert all(window.source_info.get('fund_name') == 'hdfc_mid_cap_fund' for window in windows)
    
    def test_build_by_content_grouped(self, context_builder, sample_search_results, sample_processed_query):
        """Test content-grouped context building."""
        context = SearchContext(
            query=sample_processed_query,
            embedding=np.array([0.1, 0.2, 0.3]),
            filters=sample_processed_query.filters,
            search_strategy=SearchStrategy.CONTENT_FOCUSED,
            max_results=5,
            similarity_threshold=0.5,
            retrieval_metadata={}
        )
        
        windows = context_builder._build_by_content_grouped(sample_search_results, sample_processed_query, 2000)
        
        assert len(windows) == 3
        assert all('expense_ratio' in str(window.metadata) for window in windows)
    
    def test_assemble_context_text(self, context_builder):
        """Test context text assembly."""
        windows = [
            ContextWindow(
                content="First content",
                tokens=50,
                metadata={},
                source_info={},
                relevance_score=0.9
            ),
            ContextWindow(
                content="Second content",
                tokens=50,
                metadata={},
                source_info={},
                relevance_score=0.8
            )
        ]
        
        context_text, total_tokens = context_builder._assemble_context_text(windows, 200)
        
        assert "First content" in context_text
        assert "Second content" in context_text
        assert "---" in context_text  # Separator
        assert total_tokens == 100
    
    def test_truncate_content(self, context_builder):
        """Test content truncation."""
        long_content = "This is a very long content that needs to be truncated. " * 20
        
        # Truncate to fit within limit
        truncated = context_builder._truncate_content(long_content, 50)
        
        assert len(truncated) <= len(long_content)
        assert len(truncated) > 0
        # Should end cleanly, not mid-word
        assert truncated.rstrip().endswith('.')
    
    def test_extract_source_info(self, context_builder, sample_search_results):
        """Test source information extraction."""
        windows = [
            ContextWindow(
                content="Test content",
                tokens=50,
                metadata=result.metadata,
                source_info=context_builder._create_source_info(result),
                relevance_score=0.9
            )
            for result in sample_search_results
        ]
        
        sources = context_builder._extract_source_info(windows)
        
        assert len(sources) == 1  # All from same fund
        assert sources[0]['fund_name'] == 'hdfc_mid_cap_fund'
        assert sources[0]['source_url'] == 'https://groww.in/funds/hdfc-mid-cap'
        assert len(sources[0]['chunk_ids']) == 3
    
    def test_build_context(self, context_builder, sample_search_results, sample_processed_query):
        """Test complete context building."""
        built_context = context_builder.build_context(
            search_results=sample_search_results,
            query=sample_processed_query,
            max_tokens=1000,
            strategy='hybrid'
        )
        
        assert isinstance(built_context, BuiltContext)
        assert built_context.query == sample_processed_query
        assert len(built_context.context_text) > 0
        assert built_context.total_tokens <= 1000
        assert len(built_context.context_windows) > 0
        assert len(built_context.sources) > 0
        assert 'building_metadata' in built_context.__dict__
    
    def test_create_empty_context(self, context_builder, sample_processed_query):
        """Test empty context creation."""
        empty_context = context_builder._create_empty_context(sample_processed_query, 1000)
        
        assert isinstance(empty_context, BuiltContext)
        assert empty_context.context_text == "No relevant information found for your query."
        assert empty_context.total_tokens == 0
        assert len(empty_context.context_windows) == 0
        assert len(empty_context.sources) == 0
    
    def test_estimate_tokens(self, context_builder):
        """Test token estimation."""
        text = "This is a test text for token estimation."
        tokens = context_builder._estimate_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_maintain_coherence(self, context_builder):
        """Test coherence maintenance."""
        windows = [
            ContextWindow(
                content="Content about HDFC Mid Cap Fund",
                tokens=50,
                metadata={'hierarchical_fund': 'hdfc_mid_cap_fund'},
                source_info={'fund_name': 'hdfc_mid_cap_fund'},
                relevance_score=0.9
            ),
            ContextWindow(
                content="Content about HDFC Large Cap Fund",
                tokens=50,
                metadata={'hierarchical_fund': 'hdfc_large_cap_fund'},
                source_info={'fund_name': 'hdfc_large_cap_fund'},
                relevance_score=0.8
            )
        ]
        
        coherent_windows = context_builder.maintain_coherence(windows)
        
        assert len(coherent_windows) >= len(windows)
        # Should have transition between different funds
        transition_windows = [w for w in coherent_windows if w.metadata.get('transition')]
        assert len(transition_windows) >= 1


class TestSourceRanker:
    """Test cases for SourceRanker class."""
    
    @pytest.fixture
    def source_ranker(self):
        """Create a source ranker instance for testing."""
        return SourceRanker()
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results."""
        results = []
        
        # Official source result
        result1 = SearchResult(
            document_id='doc_1',
            chunk_id='chunk_1',
            content='HDFC Mid Cap Fund expense ratio is 0.85%',
            metadata={
                'hierarchical_fund': 'hdfc_mid_cap_fund',
                'content_type': 'expense_ratio',
                'quality_score': 0.9,
                'citation_info': {
                    'source_url': 'https://hdfcfund.com/mid-cap',
                    'fund_name': 'HDFC Mid Cap Fund',
                    'last_updated': '2024-01-15'
                },
                'financial_data': {'expense_ratio': '0.85%'}
            },
            similarity_score=0.95,
            distance=0.05,
            rank=1,
            search_strategy='semantic',
            retrieval_metadata={}
        )
        results.append(result1)
        
        # Secondary source result
        result2 = SearchResult(
            document_id='doc_2',
            chunk_id='chunk_2',
            content='HDFC Mid Cap Fund performance details',
            metadata={
                'hierarchical_fund': 'hdfc_mid_cap_fund',
                'content_type': 'performance',
                'quality_score': 0.7,
                'citation_info': {
                    'source_url': 'https://moneycontrol.com/funds/hdfc-mid-cap',
                    'fund_name': 'HDFC Mid Cap Fund',
                    'last_updated': '2024-01-10'
                }
            },
            similarity_score=0.85,
            distance=0.15,
            rank=2,
            search_strategy='semantic',
            retrieval_metadata={}
        )
        results.append(result2)
        
        return results
    
    @pytest.fixture
    def sample_processed_query(self):
        """Create a sample processed query."""
        from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
        
        return ProcessedQuery(
            original_query="HDFC Mid Cap Fund expense ratio",
            cleaned_query="hdfc mid cap fund expense ratio",
            query_type=QueryType.FACTUAL,
            query_intent=QueryIntent.EXPENSE_RATIO,
            entities=["hdfc mid cap fund", "expense ratio"],
            keywords=["fund", "expense", "ratio"],
            filters={"fund_names": ["hdfc_mid_cap_fund"], "content_types": ["expense_ratio"]},
            confidence=0.85,
            processing_metadata={}
        )
    
    def test_initialization(self, source_ranker):
        """Test source ranker initialization."""
        assert len(source_ranker.official_domains) > 0
        assert 'groww.in' in source_ranker.official_domains
        assert len(source_ranker.authority_weights) == 4
        assert len(source_ranker.criteria_weights) == 6
        assert len(source_ranker.quality_indicators) == 5
    
    def test_group_by_source(self, source_ranker, sample_search_results):
        """Test source grouping."""
        source_groups = source_ranker._group_by_source(sample_search_results)
        
        assert len(source_groups) == 1  # All from same fund
        assert 'fund_hdfc_mid_cap_fund' in source_groups
        assert len(source_groups['fund_hdfc_mid_cap_fund']) == 2
    
    def test_extract_domain(self, source_ranker):
        """Test domain extraction."""
        url = "https://groww.in/mutual-funds/hdfc-mid-cap"
        domain = source_ranker._extract_domain(url)
        assert domain == "groww.in"
        
        url = "https://www.hdfcfund.com/funds"
        domain = source_ranker._extract_domain(url)
        assert domain == "hdfcfund.com"
        
        url = ""
        domain = source_ranker._extract_domain(url)
        assert domain == "unknown"
    
    def test_calculate_relevance_score(self, source_ranker, sample_search_results, sample_processed_query):
        """Test relevance score calculation."""
        relevance_score = source_ranker._calculate_relevance_score(sample_search_results, sample_processed_query)
        
        assert 0.0 <= relevance_score <= 1.0
        assert relevance_score > 0.5  # Should have good relevance
    
    def test_calculate_quality_score(self, source_ranker, sample_search_results):
        """Test quality score calculation."""
        quality_score = source_ranker._calculate_quality_score(sample_search_results)
        
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.5  # Should have decent quality
    
    def test_calculate_authority_score(self, source_ranker, sample_search_results):
        """Test authority score calculation."""
        authority_score = source_ranker._calculate_authority_score(sample_search_results)
        
        assert 0.0 <= authority_score <= 1.0
        # First result is from official domain, should have higher authority
        assert authority_score > 0.5
    
    def test_calculate_ranking_score(self, source_ranker, sample_search_results, sample_processed_query):
        """Test comprehensive ranking score calculation."""
        ranking_score = source_ranker._calculate_ranking_score(sample_search_results, sample_processed_query)
        
        assert isinstance(ranking_score, RankingScore)
        assert 0.0 <= ranking_score.overall_score <= 1.0
        assert len(ranking_score.criteria_scores) == 6
        assert 'ranking_metadata' in ranking_score.__dict__
    
    def test_create_source_info(self, source_ranker, sample_search_results):
        """Test source information creation."""
        source_info = source_ranker._create_source_info(sample_search_results)
        
        assert 'source_id' in source_info
        assert 'source_url' in source_info
        assert 'fund_name' in source_info
        assert 'result_count' in source_info
        assert 'average_similarity' in source_info
        assert source_info['result_count'] == 2
    
    def test_determine_source_authority(self, source_ranker, sample_search_results):
        """Test source authority determination."""
        authority = source_ranker._determine_source_authority(sample_search_results)
        
        assert authority in ['official', 'primary', 'secondary', 'general', 'unknown']
        # First result is from official domain
        assert authority == 'official'
    
    def test_rank_sources(self, source_ranker, sample_search_results, sample_processed_query):
        """Test source ranking."""
        ranked_sources = source_ranker.rank_sources(sample_search_results, sample_processed_query)
        
        assert len(ranked_sources) == 1  # One source group
        assert isinstance(ranked_sources[0], RankedSource)
        assert isinstance(ranked_sources[0].ranking_score, RankingScore)
        assert len(ranked_sources[0].search_results) == 2
    
    def test_prioritize_official_sources(self, source_ranker):
        """Test official source prioritization."""
        # Create mixed sources
        official_source = Mock()
        official_source.source_metadata = {'source_authority': 'official'}
        
        secondary_source = Mock()
        secondary_source.source_metadata = {'source_authority': 'secondary'}
        
        general_source = Mock()
        general_source.source_metadata = {'source_authority': 'general'}
        
        ranked_sources = [secondary_source, official_source, general_source]
        
        prioritized = source_ranker.prioritize_official_sources(ranked_sources)
        
        assert prioritized[0].source_metadata['source_authority'] == 'official'
        assert prioritized[-1].source_metadata['source_authority'] == 'general'
    
    def test_get_ranking_summary(self, source_ranker, sample_search_results, sample_processed_query):
        """Test ranking summary."""
        ranked_sources = source_ranker.rank_sources(sample_search_results, sample_processed_query)
        summary = source_ranker.get_ranking_summary(ranked_sources)
        
        assert 'total_sources' in summary
        assert 'average_score' in summary
        assert 'authority_distribution' in summary
        assert 'top_source' in summary
        assert summary['total_sources'] == 1
    
    def test_get_ranking_statistics(self, source_ranker):
        """Test ranking statistics."""
        stats = source_ranker.get_ranking_statistics()
        
        assert 'official_domains' in stats
        assert 'authority_weights' in stats
        assert 'criteria_weights' in stats
        assert 'quality_indicators' in stats
        assert 'supported_criteria' in stats


class TestIntegration:
    """Integration tests for Phase 2.3 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(self):
        """Test end-to-end query processing pipeline."""
        query_processor = QueryProcessor()
        
        # Test query
        query = "What is the expense ratio of HDFC Mid Cap Fund?"
        
        # Process query
        processed_query = query_processor.process_query(query)
        
        # Verify processing
        assert processed_query.original_query == query
        assert processed_query.query_type == QueryType.FACTUAL
        assert processed_query.query_intent == QueryIntent.EXPENSE_RATIO
        assert len(processed_query.entities) > 0
        assert len(processed_query.keywords) > 0
        assert processed_query.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_query_to_search_integration(self):
        """Test query to search integration."""
        # Create mock components
        mock_vector_db = Mock()
        mock_embedding_service = Mock()
        mock_hierarchical_db = Mock()
        
        # Mock embedding service
        mock_embedding_service.embed_texts_async = Mock(return_value=[np.array([0.1, 0.2, 0.3])])
        
        # Mock vector database
        mock_results = [{
            'id': 'doc_1',
            'document': 'HDFC Mid Cap Fund expense ratio is 0.85%',
            'metadata': {'hierarchical_fund': 'hdfc_mid_cap_fund'},
            'distance': 0.1,
            'similarity': 0.9
        }]
        mock_vector_db.search = Mock(return_value=mock_results)
        
        # Create components
        query_processor = QueryProcessor()
        search_engine = SemanticSearchEngine(mock_vector_db, mock_embedding_service, mock_hierarchical_db)
        
        # Process query
        query = "HDFC Mid Cap Fund expense ratio"
        processed_query = query_processor.process_query(query)
        
        # Search
        results = await search_engine.search(processed_query)
        
        # Verify integration
        assert len(results) == 1
        assert results[0].similarity_score == 0.9
        assert 'hdfc_mid_cap_fund' in results[0].metadata['hierarchical_fund']
    
    @pytest.mark.asyncio
    async def test_search_to_context_integration(self):
        """Test search to context building integration."""
        # Create sample search results
        search_results = [
            SearchResult(
                document_id='doc_1',
                chunk_id='chunk_1',
                content='HDFC Mid Cap Fund expense ratio is 0.85%',
                metadata={
                    'hierarchical_fund': 'hdfc_mid_cap_fund',
                    'content_type': 'expense_ratio',
                    'citation_info': {
                        'source_url': 'https://groww.in/funds/hdfc-mid-cap',
                        'fund_name': 'HDFC Mid Cap Fund'
                    }
                },
                similarity_score=0.9,
                distance=0.1,
                rank=1,
                search_strategy='semantic',
                retrieval_metadata={}
            )
        ]
        
        # Create processed query
        processed_query = ProcessedQuery(
            original_query="HDFC Mid Cap Fund expense ratio",
            cleaned_query="hdfc mid cap fund expense ratio",
            query_type=QueryType.FACTUAL,
            query_intent=QueryIntent.EXPENSE_RATIO,
            entities=["hdfc mid cap fund", "expense ratio"],
            keywords=["fund", "expense", "ratio"],
            filters={"fund_names": ["hdfc_mid_cap_fund"], "content_types": ["expense_ratio"]},
            confidence=0.85,
            processing_metadata={}
        )
        
        # Build context
        context_builder = ContextBuilder()
        built_context = context_builder.build_context(search_results, processed_query)
        
        # Verify integration
        assert isinstance(built_context, BuiltContext)
        assert len(built_context.context_text) > 0
        assert len(built_context.sources) == 1
        assert built_context.sources[0]['fund_name'] == 'hdfc_mid_cap_fund'
    
    @pytest.mark.asyncio
    async def test_context_to_ranking_integration(self):
        """Test context to source ranking integration."""
        # Create sample search results
        search_results = [
            SearchResult(
                document_id='doc_1',
                chunk_id='chunk_1',
                content='HDFC Mid Cap Fund expense ratio is 0.85%',
                metadata={
                    'hierarchical_fund': 'hdfc_mid_cap_fund',
                    'content_type': 'expense_ratio',
                    'quality_score': 0.9,
                    'citation_info': {
                        'source_url': 'https://hdfcfund.com/mid-cap',
                        'fund_name': 'HDFC Mid Cap Fund'
                    }
                },
                similarity_score=0.9,
                distance=0.1,
                rank=1,
                search_strategy='semantic',
                retrieval_metadata={}
            )
        ]
        
        # Create processed query
        processed_query = ProcessedQuery(
            original_query="HDFC Mid Cap Fund expense ratio",
            cleaned_query="hdfc mid cap fund expense ratio",
            query_type=QueryType.FACTUAL,
            query_intent=QueryIntent.EXPENSE_RATIO,
            entities=["hdfc mid cap fund", "expense ratio"],
            keywords=["fund", "expense", "ratio"],
            filters={"fund_names": ["hdfc_mid_cap_fund"], "content_types": ["expense_ratio"]},
            confidence=0.85,
            processing_metadata={}
        )
        
        # Rank sources
        source_ranker = SourceRanker()
        ranked_sources = source_ranker.rank_sources(search_results, processed_query)
        
        # Verify integration
        assert len(ranked_sources) == 1
        assert isinstance(ranked_sources[0], RankedSource)
        assert ranked_sources[0].ranking_score.overall_score > 0.5
        assert ranked_sources[0].source_metadata['source_authority'] == 'official'
    
    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self):
        """Test full retrieval pipeline integration."""
        # Create mock components
        mock_vector_db = Mock()
        mock_embedding_service = Mock()
        mock_hierarchical_db = Mock()
        
        # Mock embedding service
        mock_embedding_service.embed_texts_async = Mock(return_value=[np.array([0.1, 0.2, 0.3])])
        
        # Mock vector database
        mock_results = [{
            'id': 'doc_1',
            'document': 'HDFC Mid Cap Fund expense ratio is 0.85%',
            'metadata': {
                'hierarchical_fund': 'hdfc_mid_cap_fund',
                'content_type': 'expense_ratio',
                'quality_score': 0.9,
                'citation_info': {
                    'source_url': 'https://hdfcfund.com/mid-cap',
                    'fund_name': 'HDFC Mid Cap Fund'
                }
            },
            'distance': 0.1,
            'similarity': 0.9
        }]
        mock_vector_db.search = Mock(return_value=mock_results)
        
        # Create all components
        query_processor = QueryProcessor()
        search_engine = SemanticSearchEngine(mock_vector_db, mock_embedding_service, mock_hierarchical_db)
        context_builder = ContextBuilder()
        source_ranker = SourceRanker()
        
        # Full pipeline
        query = "What is the expense ratio of HDFC Mid Cap Fund?"
        
        # Step 1: Process query
        processed_query = query_processor.process_query(query)
        assert processed_query.query_intent == QueryIntent.EXPENSE_RATIO
        
        # Step 2: Search
        search_results = await search_engine.search(processed_query)
        assert len(search_results) == 1
        
        # Step 3: Rank sources
        ranked_sources = source_ranker.rank_sources(search_results, processed_query)
        assert len(ranked_sources) == 1
        
        # Step 4: Build context
        built_context = context_builder.build_context(search_results, processed_query)
        assert len(built_context.context_text) > 0
        assert len(built_context.sources) == 1
        
        # Verify full integration
        assert processed_query.original_query == query
        assert search_results[0].similarity_score == 0.9
        assert ranked_sources[0].ranking_score.overall_score > 0.5
        assert built_context.query == processed_query


if __name__ == "__main__":
    pytest.main([__file__])
