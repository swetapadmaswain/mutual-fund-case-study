"""
Semantic search engine module for Phase 2.3 - Retrieval System Development.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum
import time

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
from src.rag.vector_store.embeddings import EmbeddingService
from src.rag.vector_store.vector_database import VectorDatabase, HierarchicalVectorDB


class SearchStrategy(Enum):
    """Search strategy types."""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    FUND_FOCUSED = "fund_focused"
    CONTENT_FOCUSED = "content_focused"
    TYPE_FOCUSED = "type_focused"


@dataclass
class SearchResult:
    """Represents a search result with metadata."""
    document_id: str
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    distance: float
    rank: int
    search_strategy: str
    retrieval_metadata: Dict[str, Any]


@dataclass
class SearchContext:
    """Context for search operations."""
    query: ProcessedQuery
    embedding: np.ndarray
    filters: Dict[str, Any]
    search_strategy: SearchStrategy
    max_results: int
    similarity_threshold: float
    retrieval_metadata: Dict[str, Any]


class SemanticSearchEngine:
    """Implements semantic similarity search with multiple strategies."""
    
    def __init__(self, 
                 vector_database: VectorDatabase,
                 embedding_service: EmbeddingService,
                 hierarchical_db: HierarchicalVectorDB):
        """
        Initialize the semantic search engine.
        
        Args:
            vector_database: Base vector database
            embedding_service: Embedding generation service
            hierarchical_db: Hierarchical vector database
        """
        self.vector_database = vector_database
        self.embedding_service = embedding_service
        self.hierarchical_db = hierarchical_db
        
        # Search configuration
        self.default_similarity_threshold = 0.7
        self.default_max_results = 5
        self.enable_hierarchical_search = True
        self.enable_result_reranking = True
        
        # Search strategy weights
        self.strategy_weights = {
            SearchStrategy.SEMANTIC: 1.0,
            SearchStrategy.HYBRID: 0.8,
            SearchStrategy.FUND_FOCUSED: 0.9,
            SearchStrategy.CONTENT_FOCUSED: 0.9,
            SearchStrategy.TYPE_FOCUSED: 0.8
        }
        
        logger.info("Initialized SemanticSearchEngine")
    
    async def search(self, 
                   query: ProcessedQuery,
                   max_results: int = None,
                   similarity_threshold: float = None,
                   search_strategy: SearchStrategy = None) -> List[SearchResult]:
        """
        Perform semantic search on the query.
        
        Args:
            query: Processed query object
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity threshold
            search_strategy: Search strategy to use
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for query: {query.original_query}")
        
        try:
            # Set defaults
            max_results = max_results or self.default_max_results
            similarity_threshold = similarity_threshold or self.default_similarity_threshold
            search_strategy = search_strategy or self._determine_search_strategy(query)
            
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_texts_async([query.cleaned_query])
            embedding = query_embedding[0]
            
            # Create search context
            context = SearchContext(
                query=query,
                embedding=embedding,
                filters=query.filters,
                search_strategy=search_strategy,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                retrieval_metadata={}
            )
            
            # Execute search based on strategy
            start_time = time.time()
            raw_results = await self._execute_search(context)
            search_time = time.time() - start_time
            
            # Filter by similarity threshold
            filtered_results = self._filter_by_similarity(raw_results, similarity_threshold)
            
            # Rank results
            ranked_results = self._rank_results(filtered_results, context)
            
            # Add search metadata
            final_results = self._add_search_metadata(ranked_results, context, search_time)
            
            logger.info(f"Search completed: {len(final_results)} results in {search_time:.3f}s")
            return final_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise DataCollectionError(f"Search operation failed: {e}")
    
    def _determine_search_strategy(self, query: ProcessedQuery) -> SearchStrategy:
        """
        Determine the best search strategy based on query characteristics.
        
        Args:
            query: Processed query
            
        Returns:
            Search strategy enum
        """
        # Fund-specific queries
        if 'fund_names' in query.filters and query.filters['fund_names']:
            return SearchStrategy.FUND_FOCUSED
        
        # Content-specific queries
        if 'content_types' in query.filters and query.filters['content_types']:
            return SearchStrategy.CONTENT_FOCUSED
        
        # Type-specific queries
        if 'fund_types' in query.filters and query.filters['fund_types']:
            return SearchStrategy.TYPE_FOCUSED
        
        # Advisory queries (use hybrid for better coverage)
        if query.query_type == QueryType.ADVISORY:
            return SearchStrategy.HYBRID
        
        # Default to semantic search
        return SearchStrategy.SEMANTIC
    
    async def _execute_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """
        Execute search based on the selected strategy.
        
        Args:
            context: Search context
            
        Returns:
            Raw search results from database
        """
        strategy = context.search_strategy
        
        if strategy == SearchStrategy.SEMANTIC:
            return await self._semantic_search(context)
        elif strategy == SearchStrategy.HYBRID:
            return await self._hybrid_search(context)
        elif strategy == SearchStrategy.FUND_FOCUSED:
            return await self._fund_focused_search(context)
        elif strategy == SearchStrategy.CONTENT_FOCUSED:
            return await self._content_focused_search(context)
        elif strategy == SearchStrategy.TYPE_FOCUSED:
            return await self._type_focused_search(context)
        else:
            return await self._semantic_search(context)
    
    async def _semantic_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """Perform basic semantic search."""
        # Build metadata filters
        where_filter = self._build_metadata_filters(context.filters)
        
        # Execute search
        results = self.vector_database.search(
            query_embedding=context.embedding,
            top_k=context.max_results,
            where_filter=where_filter
        )
        
        return results
    
    async def _hybrid_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """Perform hybrid search combining multiple strategies."""
        all_results = []
        seen_ids = set()
        
        # Semantic search (primary)
        semantic_results = await self._semantic_search(context)
        for result in semantic_results:
            if result['id'] not in seen_ids:
                result['search_source'] = 'semantic'
                all_results.append(result)
                seen_ids.add(result['id'])
        
        # Fund-focused search (if applicable)
        if 'fund_names' in context.filters:
            fund_results = await self._fund_focused_search(context)
            for result in fund_results:
                if result['id'] not in seen_ids:
                    result['search_source'] = 'fund_focused'
                    all_results.append(result)
                    seen_ids.add(result['id'])
        
        # Content-focused search (if applicable)
        if 'content_types' in context.filters:
            content_results = await self._content_focused_search(context)
            for result in content_results:
                if result['id'] not in seen_ids:
                    result['search_source'] = 'content_focused'
                    all_results.append(result)
                    seen_ids.add(result['id'])
        
        # Sort by similarity and limit results
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:context.max_results]
    
    async def _fund_focused_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """Perform fund-focused search."""
        fund_names = context.filters.get('fund_names', [])
        
        if not fund_names:
            return await self._semantic_search(context)
        
        all_results = []
        
        # Search within each fund
        for fund_name in fund_names:
            fund_filter = {'hierarchical_fund': fund_name}
            
            # Add other filters
            combined_filter = fund_filter.copy()
            if 'content_types' in context.filters:
                combined_filter['hierarchical_content'] = {'$in': context.filters['content_types']}
            
            results = self.vector_database.search(
                query_embedding=context.embedding,
                top_k=context.max_results,
                where_filter=combined_filter
            )
            
            # Add fund context
            for result in results:
                result['search_context'] = 'fund_focused'
                result['target_fund'] = fund_name
            
            all_results.extend(results)
        
        # Sort and limit
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:context.max_results]
    
    async def _content_focused_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """Perform content-focused search."""
        content_types = context.filters.get('content_types', [])
        
        if not content_types:
            return await self._semantic_search(context)
        
        all_results = []
        
        # Search for each content type
        for content_type in content_types:
            content_filter = {'hierarchical_content': content_type}
            
            # Add fund filters if available
            if 'fund_names' in context.filters:
                content_filter['hierarchical_fund'] = {'$in': context.filters['fund_names']}
            
            results = self.vector_database.search(
                query_embedding=context.embedding,
                top_k=context.max_results,
                where_filter=content_filter
            )
            
            # Add content context
            for result in results:
                result['search_context'] = 'content_focused'
                result['target_content'] = content_type
            
            all_results.extend(results)
        
        # Sort and limit
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:context.max_results]
    
    async def _type_focused_search(self, context: SearchContext) -> List[Dict[str, Any]]:
        """Perform type-focused search."""
        fund_types = context.filters.get('fund_types', [])
        
        if not fund_types:
            return await self._semantic_search(context)
        
        all_results = []
        
        # Search for each fund type
        for fund_type in fund_types:
            type_filter = {'hierarchical_type': fund_type}
            
            results = self.vector_database.search(
                query_embedding=context.embedding,
                top_k=context.max_results,
                where_filter=type_filter
            )
            
            # Add type context
            for result in results:
                result['search_context'] = 'type_focused'
                result['target_type'] = fund_type
            
            all_results.extend(results)
        
        # Sort and limit
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:context.max_results]
    
    def _build_metadata_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build metadata filters for vector database search.
        
        Args:
            filters: Query filters
            
        Returns:
            Metadata filter dictionary
        """
        metadata_filter = {}
        
        # Fund name filters
        if 'fund_names' in filters:
            fund_names = filters['fund_names']
            if len(fund_names) == 1:
                metadata_filter['hierarchical_fund'] = fund_names[0]
            else:
                metadata_filter['hierarchical_fund'] = {'$in': fund_names}
        
        # Fund type filters
        if 'fund_types' in filters:
            fund_types = filters['fund_types']
            if len(fund_types) == 1:
                metadata_filter['hierarchical_type'] = fund_types[0]
            else:
                metadata_filter['hierarchical_type'] = {'$in': fund_types}
        
        # Content type filters
        if 'content_types' in filters:
            content_types = filters['content_types']
            if len(content_types) == 1:
                metadata_filter['hierarchical_content'] = content_types[0]
            else:
                metadata_filter['hierarchical_content'] = {'$in': content_types}
        
        return metadata_filter
    
    def _filter_by_similarity(self, results: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
        """
        Filter results by similarity threshold.
        
        Args:
            results: Raw search results
            threshold: Minimum similarity threshold
            
        Returns:
            Filtered results
        """
        filtered_results = []
        
        for result in results:
            similarity = result.get('similarity', 0.0)
            if similarity >= threshold:
                filtered_results.append(result)
        
        return filtered_results
    
    def _rank_results(self, results: List[Dict[str, Any]], context: SearchContext) -> List[Dict[str, Any]]:
        """
        Rank and re-rank search results.
        
        Args:
            results: Search results
            context: Search context
            
        Returns:
            Ranked results
        """
        if not self.enable_result_reranking:
            return results
        
        # Calculate ranking scores
        ranked_results = []
        
        for i, result in enumerate(results):
            # Base similarity score
            base_score = result.get('similarity', 0.0)
            
            # Strategy weight
            strategy_weight = self.strategy_weights.get(context.search_strategy, 1.0)
            
            # Position penalty (earlier results get bonus)
            position_penalty = 1.0 - (i * 0.05)
            
            # Content relevance bonus
            content_bonus = self._calculate_content_relevance(result, context)
            
            # Fund relevance bonus
            fund_bonus = self._calculate_fund_relevance(result, context)
            
            # Final score
            final_score = base_score * strategy_weight * position_penalty + content_bonus + fund_bonus
            
            result['ranking_score'] = final_score
            ranked_results.append(result)
        
        # Sort by ranking score
        ranked_results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked_results
    
    def _calculate_content_relevance(self, result: Dict[str, Any], context: SearchContext) -> float:
        """Calculate content relevance bonus."""
        bonus = 0.0
        
        metadata = result.get('metadata', {})
        query_intent = context.query.query_intent
        
        # Content type matching
        if 'content_type' in metadata and metadata['content_type'] == query_intent.value:
            bonus += 0.1
        
        # Financial data presence
        if 'financial_data' in metadata and metadata['financial_data']:
            bonus += 0.05
        
        # Quality score bonus
        quality_score = metadata.get('quality_score', 0.0)
        bonus += quality_score * 0.05
        
        return bonus
    
    def _calculate_fund_relevance(self, result: Dict[str, Any], context: SearchContext) -> float:
        """Calculate fund relevance bonus."""
        bonus = 0.0
        
        metadata = result.get('metadata', {})
        filters = context.filters
        
        # Fund name matching
        if 'fund_names' in filters:
            result_fund = metadata.get('hierarchical_fund', '')
            if result_fund in filters['fund_names']:
                bonus += 0.1
        
        # Fund type matching
        if 'fund_types' in filters:
            result_type = metadata.get('hierarchical_type', '')
            if result_type in filters['fund_types']:
                bonus += 0.05
        
        return bonus
    
    def _add_search_metadata(self, results: List[Dict[str, Any]], context: SearchContext, search_time: float) -> List[SearchResult]:
        """
        Add search metadata and convert to SearchResult objects.
        
        Args:
            results: Ranked search results
            context: Search context
            search_time: Search execution time
            
        Returns:
            List of SearchResult objects
        """
        search_results = []
        
        for i, result in enumerate(results):
            search_result = SearchResult(
                document_id=result.get('id', ''),
                chunk_id=result.get('metadata', {}).get('chunk_id', ''),
                content=result.get('document', ''),
                metadata=result.get('metadata', {}),
                similarity_score=result.get('similarity', 0.0),
                distance=result.get('distance', 0.0),
                rank=i + 1,
                search_strategy=context.search_strategy.value,
                retrieval_metadata={
                    'search_time': search_time,
                    'search_context': result.get('search_context', ''),
                    'ranking_score': result.get('ranking_score', 0.0),
                    'query_intent': context.query.query_intent.value,
                    'query_type': context.query.query_type.value,
                    'similarity_threshold': context.similarity_threshold,
                    'total_results': len(results)
                }
            )
            search_results.append(search_result)
        
        return search_results
    
    def configure_similarity_threshold(self, threshold: float = 0.7) -> None:
        """
        Configure similarity threshold for search results.
        
        Args:
            threshold: Minimum similarity threshold (0.0-1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        
        self.default_similarity_threshold = threshold
        logger.info(f"Configured similarity threshold: {threshold}")
    
    def multi_strategy_search(self, query: ProcessedQuery) -> List[SearchResult]:
        """
        Perform search using multiple strategies and combine results.
        
        Args:
            query: Processed query
            
        Returns:
            Combined search results
        """
        logger.info(f"Performing multi-strategy search for: {query.original_query}")
        
        strategies = [
            SearchStrategy.SEMANTIC,
            SearchStrategy.FUND_FOCUSED,
            SearchStrategy.CONTENT_FOCUSED
        ]
        
        all_results = []
        seen_ids = set()
        
        # Execute each strategy
        for strategy in strategies:
            try:
                strategy_results = asyncio.run(self.search(
                    query=query,
                    search_strategy=strategy,
                    max_results=3  # Fewer results per strategy
                ))
                
                for result in strategy_results:
                    if result.document_id not in seen_ids:
                        result.retrieval_metadata['search_strategy'] = strategy.value
                        all_results.append(result)
                        seen_ids.add(result.document_id)
                
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")
        
        # Sort by similarity and limit
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return all_results[:self.default_max_results]
    
    def rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Re-rank search results using advanced scoring.
        
        Args:
            results: Search results to rank
            
        Returns:
            Re-ranked results
        """
        if not results:
            return results
        
        # Calculate advanced ranking scores
        for i, result in enumerate(results):
            # Base similarity score
            base_score = result.similarity_score
            
            # Position factor
            position_factor = 1.0 - (i * 0.02)
            
            # Quality factor
            quality_factor = result.metadata.get('quality_score', 0.0) * 0.1
            
            # Recency factor (if timestamp available)
            recency_factor = 0.0
            if 'added_at' in result.metadata:
                # More recent content gets slight bonus
                recency_factor = 0.05
            
            # Final ranking score
            final_score = base_score * position_factor + quality_factor + recency_factor
            
            # Store ranking score
            result.retrieval_metadata['final_ranking_score'] = final_score
        
        # Sort by final ranking score
        ranked_results = sorted(results, key=lambda x: x.retrieval_metadata['final_ranking_score'], reverse=True)
        
        # Update ranks
        for i, result in enumerate(ranked_results):
            result.rank = i + 1
        
        return ranked_results
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get search engine statistics.
        
        Returns:
            Search statistics dictionary
        """
        # Get vector database stats
        db_stats = self.vector_database.get_collection_stats()
        
        # Get hierarchical stats
        hierarchy_stats = self.hierarchical_db.get_hierarchy_stats()
        
        return {
            'vector_database': {
                'total_documents': db_stats.get('document_count', 0),
                'collection_name': db_stats.get('collection_name', ''),
                'embedding_dimension': db_stats.get('embedding_dimension', 0)
            },
            'hierarchical_index': {
                'total_funds': hierarchy_stats.get('total_funds', 0),
                'fund_types': hierarchy_stats.get('fund_types', []),
                'total_documents': hierarchy_stats.get('total_documents', 0)
            },
            'search_configuration': {
                'similarity_threshold': self.default_similarity_threshold,
                'max_results': self.default_max_results,
                'hierarchical_search_enabled': self.enable_hierarchical_search,
                'result_reranking_enabled': self.enable_result_reranking
            },
            'supported_strategies': [strategy.value for strategy in SearchStrategy]
        }
