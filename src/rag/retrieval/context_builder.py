"""
Context builder module for Phase 2.3 - Retrieval System Development.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
from src.rag.retrieval.search_engine import SearchResult


@dataclass
class ContextWindow:
    """Represents a context window with token management."""
    content: str
    tokens: int
    metadata: Dict[str, Any]
    source_info: Dict[str, Any]
    relevance_score: float


@dataclass
class BuiltContext:
    """Represents a built context for LLM consumption."""
    query: ProcessedQuery
    context_text: str
    sources: List[Dict[str, Any]]
    total_tokens: int
    context_windows: List[ContextWindow]
    building_metadata: Dict[str, Any]


class ContextBuilder:
    """Assembles relevant context from search results for LLM consumption."""
    
    def __init__(self, 
                 max_context_tokens: int = 4000,
                 window_overlap_tokens: int = 100,
                 min_relevance_threshold: float = 0.5):
        """
        Initialize the context builder.
        
        Args:
            max_context_tokens: Maximum tokens in context
            window_overlap_tokens: Overlap between context windows
            min_relevance_threshold: Minimum relevance score for inclusion
        """
        self.max_context_tokens = max_context_tokens
        self.window_overlap_tokens = window_overlap_tokens
        self.min_relevance_threshold = min_relevance_threshold
        
        # Context building strategies
        self.context_strategies = {
            'relevance_first': self._build_by_relevance_first,
            'chronological': self._build_by_chronological,
            'fund_grouped': self._build_by_fund_grouped,
            'content_grouped': self._build_by_content_grouped,
            'hybrid': self._build_hybrid_context
        }
        
        # Token estimation
        self.token_ratio = 1.3  # Approximate tokens per character
        
        logger.info("Initialized ContextBuilder")
    
    def build_context(self, 
                     search_results: List[SearchResult], 
                     query: ProcessedQuery,
                     max_tokens: int = None,
                     strategy: str = 'hybrid') -> BuiltContext:
        """
        Build context from search results.
        
        Args:
            search_results: List of search results
            query: Original processed query
            max_tokens: Maximum tokens for context
            strategy: Context building strategy
            
        Returns:
            BuiltContext object
        """
        logger.info(f"Building context for query: {query.original_query}")
        
        try:
            # Set max tokens
            max_tokens = max_tokens or self.max_context_tokens
            
            # Filter results by relevance
            filtered_results = self._filter_by_relevance(search_results)
            
            if not filtered_results:
                logger.warning("No results passed relevance threshold")
                return self._create_empty_context(query, max_tokens)
            
            # Select context building strategy
            strategy_func = self.context_strategies.get(strategy, self._build_hybrid_context)
            
            # Build context windows
            context_windows = strategy_func(filtered_results, query, max_tokens)
            
            # Assemble final context
            context_text, total_tokens = self._assemble_context_text(context_windows, max_tokens)
            
            # Extract source information
            sources = self._extract_source_info(context_windows)
            
            # Create building metadata
            building_metadata = self._create_building_metadata(
                query, filtered_results, context_windows, total_tokens, strategy
            )
            
            built_context = BuiltContext(
                query=query,
                context_text=context_text,
                sources=sources,
                total_tokens=total_tokens,
                context_windows=context_windows,
                building_metadata=building_metadata
            )
            
            logger.info(f"Built context: {total_tokens} tokens from {len(context_windows)} windows")
            return built_context
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            raise DataCollectionError(f"Context building failed: {e}")
    
    def _filter_by_relevance(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Filter search results by relevance threshold.
        
        Args:
            results: Search results to filter
            
        Returns:
            Filtered results
        """
        filtered_results = []
        
        for result in results:
            # Use similarity score as relevance
            relevance_score = result.similarity_score
            
            # Also consider ranking score if available
            if 'final_ranking_score' in result.retrieval_metadata:
                ranking_score = result.retrieval_metadata['final_ranking_score']
                relevance_score = (relevance_score + ranking_score) / 2
            
            if relevance_score >= self.min_relevance_threshold:
                # Update the effective relevance score
                result.retrieval_metadata['effective_relevance'] = relevance_score
                filtered_results.append(result)
        
        # Sort by effective relevance
        filtered_results.sort(key=lambda x: x.retrieval_metadata['effective_relevance'], reverse=True)
        
        return filtered_results
    
    def _build_by_relevance_first(self, results: List[SearchResult], query: ProcessedQuery, max_tokens: int) -> List[ContextWindow]:
        """Build context by prioritizing most relevant results."""
        context_windows = []
        current_tokens = 0
        
        for result in results:
            # Estimate tokens for this result
            content_tokens = self._estimate_tokens(result.content)
            
            # Check if we can add this result
            if current_tokens + content_tokens > max_tokens:
                break
            
            # Create context window
            window = ContextWindow(
                content=result.content,
                tokens=content_tokens,
                metadata=result.metadata,
                source_info=self._create_source_info(result),
                relevance_score=result.retrieval_metadata.get('effective_relevance', result.similarity_score)
            )
            
            context_windows.append(window)
            current_tokens += content_tokens
        
        return context_windows
    
    def _build_by_chronological(self, results: List[SearchResult], query: ProcessedQuery, max_tokens: int) -> List[ContextWindow]:
        """Build context by chronological order."""
        # Sort by timestamp if available
        results_with_time = []
        results_without_time = []
        
        for result in results:
            if 'added_at' in result.metadata:
                results_with_time.append(result)
            else:
                results_without_time.append(result)
        
        # Sort chronological results
        results_with_time.sort(key=lambda x: x.metadata['added_at'], reverse=True)
        
        # Combine: recent first, then others by relevance
        sorted_results = results_with_time + results_without_time
        
        return self._build_by_relevance_first(sorted_results, query, max_tokens)
    
    def _build_by_fund_grouped(self, results: List[SearchResult], query: ProcessedQuery, max_tokens: int) -> List[ContextWindow]:
        """Build context grouped by fund."""
        # Group results by fund
        fund_groups = {}
        
        for result in results:
            fund_name = result.metadata.get('hierarchical_fund', 'unknown')
            if fund_name not in fund_groups:
                fund_groups[fund_name] = []
            fund_groups[fund_name].append(result)
        
        # Sort groups by relevance (highest scoring result in each group)
        sorted_groups = sorted(
            fund_groups.items(),
            key=lambda x: max(r.retrieval_metadata.get('effective_relevance', r.similarity_score) for r in x[1]),
            reverse=True
        )
        
        context_windows = []
        current_tokens = 0
        
        # Add results from each group
        for fund_name, group_results in sorted_groups:
            # Sort results within group by relevance
            group_results.sort(key=lambda x: x.retrieval_metadata.get('effective_relevance', x.similarity_score), reverse=True)
            
            for result in group_results:
                content_tokens = self._estimate_tokens(result.content)
                
                if current_tokens + content_tokens > max_tokens:
                    break
                
                window = ContextWindow(
                    content=result.content,
                    tokens=content_tokens,
                    metadata=result.metadata,
                    source_info=self._create_source_info(result),
                    relevance_score=result.retrieval_metadata.get('effective_relevance', result.similarity_score)
                )
                
                context_windows.append(window)
                current_tokens += content_tokens
            
            if current_tokens >= max_tokens:
                break
        
        return context_windows
    
    def _build_by_content_grouped(self, results: List[SearchResult], query: ProcessedQuery, max_tokens: int) -> List[ContextWindow]:
        """Build context grouped by content type."""
        # Group results by content type
        content_groups = {}
        
        for result in results:
            content_type = result.metadata.get('hierarchical_content', 'general')
            if content_type not in content_groups:
                content_groups[content_type] = []
            content_groups[content_type].append(result)
        
        # Prioritize content types based on query intent
        intent_priority = {
            QueryIntent.EXPENSE_RATIO: 1,
            QueryIntent.EXIT_LOAD: 1,
            QueryIntent.NAV: 1,
            QueryIntent.SIP: 1,
            QueryIntent.AUM: 2,
            QueryIntent.RISK: 2,
            QueryIntent.BENCHMARK: 2,
            QueryIntent.PERFORMANCE_RETURNS: 3,
            QueryIntent.INVESTMENT_OBJECTIVE: 3,
            QueryIntent.GENERAL_INFO: 4
        }
        
        # Sort groups by query intent priority
        query_intent = query.query_intent
        sorted_groups = sorted(
            content_groups.items(),
            key=lambda x: intent_priority.get(query_intent, 5) if x[0] == query_intent.value else 5
        )
        
        context_windows = []
        current_tokens = 0
        
        for content_type, group_results in sorted_groups:
            # Sort results within group by relevance
            group_results.sort(key=lambda x: x.retrieval_metadata.get('effective_relevance', x.similarity_score), reverse=True)
            
            for result in group_results:
                content_tokens = self._estimate_tokens(result.content)
                
                if current_tokens + content_tokens > max_tokens:
                    break
                
                window = ContextWindow(
                    content=result.content,
                    tokens=content_tokens,
                    metadata=result.metadata,
                    source_info=self._create_source_info(result),
                    relevance_score=result.retrieval_metadata.get('effective_relevance', result.similarity_score)
                )
                
                context_windows.append(window)
                current_tokens += content_tokens
            
            if current_tokens >= max_tokens:
                break
        
        return context_windows
    
    def _build_hybrid_context(self, results: List[SearchResult], query: ProcessedQuery, max_tokens: int) -> List[ContextWindow]:
        """Build context using hybrid approach."""
        # Start with relevance-based selection
        relevance_windows = self._build_by_relevance_first(results, query, max_tokens)
        
        # If we have room, add diversity
        if sum(w.tokens for w in relevance_windows) < max_tokens * 0.8:
            remaining_tokens = max_tokens - sum(w.tokens for w in relevance_windows)
            
            # Add content diversity
            content_windows = self._build_by_content_grouped(results, query, remaining_tokens)
            
            # Merge windows, avoiding duplicates
            seen_content = set(w.content for w in relevance_windows)
            
            for window in content_windows:
                if window.content not in seen_content:
                    relevance_windows.append(window)
                    seen_content.add(window.content)
        
        # Ensure we don't exceed max tokens
        final_windows = []
        current_tokens = 0
        
        for window in relevance_windows:
            if current_tokens + window.tokens > max_tokens:
                break
            final_windows.append(window)
            current_tokens += window.tokens
        
        return final_windows
    
    def _assemble_context_text(self, context_windows: List[ContextWindow], max_tokens: int) -> Tuple[str, int]:
        """
        Assemble context text from windows.
        
        Args:
            context_windows: List of context windows
            max_tokens: Maximum tokens for final context
            
        Returns:
            Tuple of (context_text, total_tokens)
        """
        context_parts = []
        current_tokens = 0
        
        for window in context_windows:
            # Add window separator
            if context_parts:
                separator = "\n\n---\n\n"
                separator_tokens = self._estimate_tokens(separator)
                if current_tokens + separator_tokens + window.tokens > max_tokens:
                    break
                context_parts.append(separator)
                current_tokens += separator_tokens
            
            # Add window content
            if current_tokens + window.tokens <= max_tokens:
                context_parts.append(window.content)
                current_tokens += window.tokens
            else:
                # Truncate content to fit
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 50:  # Minimum meaningful content
                    truncated_content = self._truncate_content(window.content, remaining_tokens)
                    context_parts.append(truncated_content)
                    current_tokens += self._estimate_tokens(truncated_content)
                break
        
        context_text = "".join(context_parts)
        return context_text, current_tokens
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """
        Truncate content to fit within token limit.
        
        Args:
            content: Content to truncate
            max_tokens: Maximum tokens
            
        Returns:
            Truncated content
        """
        # Estimate character limit
        char_limit = int(max_tokens / self.token_ratio)
        
        if len(content) <= char_limit:
            return content
        
        # Try to truncate at sentence boundary
        sentences = re.split(r'(?<=[.!?])\s+', content)
        truncated = ""
        
        for sentence in sentences:
            if len(truncated) + len(sentence) <= char_limit:
                truncated += sentence + " "
            else:
                break
        
        # If no sentence boundary works, truncate at word boundary
        if not truncated:
            words = content.split()
            truncated = ""
            for word in words:
                if len(truncated) + len(word) + 1 <= char_limit:
                    truncated += word + " "
                else:
                    break
        
        return truncated.strip()
    
    def _extract_source_info(self, context_windows: List[ContextWindow]) -> List[Dict[str, Any]]:
        """
        Extract source information from context windows.
        
        Args:
            context_windows: List of context windows
            
        Returns:
            List of source information dictionaries
        """
        sources = []
        seen_sources = set()
        
        for window in context_windows:
            source_info = window.source_info
            
            # Create unique source identifier
            source_id = f"{source_info.get('fund_name', 'unknown')}_{source_info.get('document_id', 'unknown')}"
            
            if source_id not in seen_sources:
                sources.append({
                    'fund_name': source_info.get('fund_name', ''),
                    'document_id': source_info.get('document_id', ''),
                    'source_url': source_info.get('source_url', ''),
                    'chunk_ids': [source_info.get('chunk_id', '')],
                    'relevance_score': window.relevance_score,
                    'content_types': list(set(window.metadata.get('hierarchical_keys', [])))
                })
                seen_sources.add(source_id)
            else:
                # Update existing source
                for source in sources:
                    if source['fund_name'] == source_info.get('fund_name', ''):
                        source['chunk_ids'].append(source_info.get('chunk_id', ''))
                        source['content_types'].extend(window.metadata.get('hierarchical_keys', []))
                        break
        
        # Remove duplicates in content_types
        for source in sources:
            source['content_types'] = list(set(source['content_types']))
        
        return sources
    
    def _create_source_info(self, result: SearchResult) -> Dict[str, Any]:
        """Create source information from search result."""
        metadata = result.metadata
        citation_info = metadata.get('citation_info', {})
        
        return {
            'fund_name': metadata.get('hierarchical_fund', ''),
            'document_id': result.document_id,
            'chunk_id': result.chunk_id,
            'source_url': citation_info.get('source_url', ''),
            'last_updated': citation_info.get('last_updated', ''),
            'similarity_score': result.similarity_score,
            'rank': result.rank
        }
    
    def _create_building_metadata(self, 
                                query: ProcessedQuery,
                                filtered_results: List[SearchResult],
                                context_windows: List[ContextWindow],
                                total_tokens: int,
                                strategy: str) -> Dict[str, Any]:
        """Create metadata about the context building process."""
        return {
            'query_info': {
                'original_query': query.original_query,
                'query_type': query.query_type.value,
                'query_intent': query.query_intent.value,
                'query_confidence': query.confidence
            },
            'results_info': {
                'total_results': len(filtered_results),
                'used_results': len(context_windows),
                'average_relevance': sum(w.relevance_score for w in context_windows) / len(context_windows) if context_windows else 0,
                'relevance_range': {
                    'min': min(w.relevance_score for w in context_windows) if context_windows else 0,
                    'max': max(w.relevance_score for w in context_windows) if context_windows else 0
                }
            },
            'context_info': {
                'total_tokens': total_tokens,
                'max_tokens': self.max_context_tokens,
                'token_utilization': total_tokens / self.max_context_tokens,
                'windows_count': len(context_windows),
                'building_strategy': strategy,
                'average_window_tokens': sum(w.tokens for w in context_windows) / len(context_windows) if context_windows else 0
            },
            'source_info': {
                'unique_sources': len(set(w.source_info.get('fund_name', '') for w in context_windows)),
                'source_distribution': self._get_source_distribution(context_windows)
            },
            'building_timestamp': datetime.now().isoformat()
        }
    
    def _get_source_distribution(self, context_windows: List[ContextWindow]) -> Dict[str, int]:
        """Get distribution of sources in context."""
        distribution = {}
        
        for window in context_windows:
            fund_name = window.source_info.get('fund_name', 'unknown')
            distribution[fund_name] = distribution.get(fund_name, 0) + 1
        
        return distribution
    
    def _create_empty_context(self, query: ProcessedQuery, max_tokens: int) -> BuiltContext:
        """Create an empty context when no relevant results are found."""
        return BuiltContext(
            query=query,
            context_text="No relevant information found for your query.",
            sources=[],
            total_tokens=0,
            context_windows=[],
            building_metadata={
                'query_info': {
                    'original_query': query.original_query,
                    'query_type': query.query_type.value,
                    'query_intent': query.query_intent.value
                },
                'results_info': {
                    'total_results': 0,
                    'used_results': 0,
                    'message': 'No results passed relevance threshold'
                },
                'context_info': {
                    'total_tokens': 0,
                    'max_tokens': max_tokens,
                    'token_utilization': 0.0,
                    'windows_count': 0
                },
                'building_timestamp': datetime.now().isoformat()
            }
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Simple estimation: characters / token_ratio
        return int(len(text) / self.token_ratio)
    
    def maintain_coherence(self, context_windows: List[ContextWindow]) -> List[ContextWindow]:
        """
        Maintain coherence across context windows.
        
        Args:
            context_windows: List of context windows
            
        Returns:
            Coherent context windows
        """
        if len(context_windows) <= 1:
            return context_windows
        
        coherent_windows = []
        
        for i, window in enumerate(context_windows):
            # Check for coherence with previous window
            if i > 0:
                prev_window = coherent_windows[-1]
                coherence_score = self._calculate_coherence(prev_window.content, window.content)
                
                # If coherence is low, add transition
                if coherence_score < 0.3:
                    transition = self._create_transition(prev_window, window)
                    if transition:
                        coherent_windows.append(transition)
            
            coherent_windows.append(window)
        
        return coherent_windows
    
    def _calculate_coherence(self, content1: str, content2: str) -> float:
        """
        Calculate coherence score between two content pieces.
        
        Args:
            content1: First content piece
            content2: Second content piece
            
        Returns:
            Coherence score (0.0-1.0)
        """
        # Simple coherence based on shared keywords
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _create_transition(self, prev_window: ContextWindow, current_window: ContextWindow) -> Optional[ContextWindow]:
        """Create transition between context windows."""
        # Check if same fund
        prev_fund = prev_window.source_info.get('fund_name', '')
        current_fund = current_window.source_info.get('fund_name', '')
        
        if prev_fund == current_fund:
            return None  # No transition needed for same fund
        
        # Create fund transition
        transition_text = f"Additionally, regarding {current_fund}:"
        
        return ContextWindow(
            content=transition_text,
            tokens=self._estimate_tokens(transition_text),
            metadata={'transition': True},
            source_info={'fund_name': current_fund},
            relevance_score=0.5
        )
    
    def handle_context_window_limitations(self, context_windows: List[ContextWindow], max_tokens: int) -> List[ContextWindow]:
        """
        Handle context window limitations gracefully.
        
        Args:
            context_windows: List of context windows
            max_tokens: Maximum allowed tokens
            
        Returns:
            Adjusted context windows
        """
        total_tokens = sum(w.tokens for w in context_windows)
        
        if total_tokens <= max_tokens:
            return context_windows
        
        # Need to truncate
        adjusted_windows = []
        current_tokens = 0
        
        for window in context_windows:
            if current_tokens + window.tokens <= max_tokens:
                adjusted_windows.append(window)
                current_tokens += window.tokens
            else:
                # Try to include partial content
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 50:  # Minimum meaningful content
                    truncated_content = self._truncate_content(window.content, remaining_tokens)
                    truncated_window = ContextWindow(
                        content=truncated_content,
                        tokens=self._estimate_tokens(truncated_content),
                        metadata=window.metadata.copy(),
                        source_info=window.source_info,
                        relevance_score=window.relevance_score * 0.8  # Slightly lower relevance for truncated content
                    )
                    adjusted_windows.append(truncated_window)
                break
        
        return adjusted_windows
    
    def preserve_source_citations(self, context_windows: List[ContextWindow]) -> List[ContextWindow]:
        """
        Ensure proper source citations are preserved.
        
        Args:
            context_windows: List of context windows
            
        Returns:
            Context windows with preserved citations
        """
        for window in context_windows:
            # Ensure citation info is in metadata
            if 'citation_info' not in window.metadata:
                citation_info = {
                    'source_url': window.source_info.get('source_url', ''),
                    'fund_name': window.source_info.get('fund_name', ''),
                    'chunk_id': window.source_info.get('chunk_id', ''),
                    'last_updated': window.metadata.get('processed_at', '')
                }
                window.metadata['citation_info'] = citation_info
        
        return context_windows
