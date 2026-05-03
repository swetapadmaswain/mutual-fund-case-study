"""
Source ranking system module for Phase 2.3 - Retrieval System Development.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime, timedelta

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.retrieval.query_processor import ProcessedQuery, QueryType, QueryIntent
from src.rag.retrieval.search_engine import SearchResult


class RankingCriteria(Enum):
    """Source ranking criteria."""
    RELEVANCE = "relevance"
    RECENCY = "recency"
    QUALITY = "quality"
    COMPLETENESS = "completeness"
    AUTHORITY = "authority"
    COVERAGE = "coverage"


@dataclass
class RankingScore:
    """Represents a ranking score with breakdown."""
    overall_score: float
    criteria_scores: Dict[RankingCriteria, float]
    ranking_metadata: Dict[str, Any]


@dataclass
class RankedSource:
    """Represents a ranked source with detailed scoring."""
    source_info: Dict[str, Any]
    ranking_score: RankingScore
    search_results: List[SearchResult]
    source_metadata: Dict[str, Any]


class SourceRanker:
    """Prioritizes official sources and ranks search results."""
    
    def __init__(self):
        """Initialize the source ranker."""
        # Official source domains (highest priority)
        self.official_domains = [
            'groww.in',
            'hdfcfund.com',
            'hdfcmutual.com'
        ]
        
        # Source authority weights
        self.authority_weights = {
            'official': 1.0,      # Official fund sites
            'primary': 0.9,        # Primary financial platforms
            'secondary': 0.7,      # Secondary financial sites
            'general': 0.5         # General information sites
        }
        
        # Ranking criteria weights
        self.criteria_weights = {
            RankingCriteria.RELEVANCE: 0.4,
            RankingCriteria.QUALITY: 0.2,
            RankingCriteria.RECENCY: 0.15,
            RankingCriteria.COMPLETENESS: 0.1,
            RankingCriteria.AUTHORITY: 0.1,
            RankingCriteria.COVERAGE: 0.05
        }
        
        # Content quality indicators
        self.quality_indicators = {
            'financial_data': r'(expense\s*ratio|exit\s*load|nav|sip|aum|risk|benchmark)',
            'structured_info': r'(\d+\.?\d*%|₹\d+|\d+\s*years?)',
            'complete_sentences': r'[A-Z][^.!?]*[.!?]',
            'no_duplicates': r'(?!(\b\w+\b)(?:\s+\b\1\b)+)',
            'coherent_text': r'\w+\s+\w+\s+\w+'
        }
        
        logger.info("Initialized SourceRanker")
    
    def rank_sources(self, 
                    search_results: List[SearchResult], 
                    query: ProcessedQuery) -> List[RankedSource]:
        """
        Rank sources based on multiple criteria.
        
        Args:
            search_results: List of search results
            query: Processed query
            
        Returns:
            List of ranked sources
        """
        logger.info(f"Ranking sources for query: {query.original_query}")
        
        try:
            # Group results by source
            source_groups = self._group_by_source(search_results)
            
            # Rank each source
            ranked_sources = []
            
            for source_id, group_results in source_groups.items():
                # Calculate ranking score
                ranking_score = self._calculate_ranking_score(group_results, query)
                
                # Create source info
                source_info = self._create_source_info(group_results)
                
                # Create source metadata
                source_metadata = self._create_source_metadata(group_results, query)
                
                ranked_source = RankedSource(
                    source_info=source_info,
                    ranking_score=ranking_score,
                    search_results=group_results,
                    source_metadata=source_metadata
                )
                
                ranked_sources.append(ranked_source)
            
            # Sort by overall score
            ranked_sources.sort(key=lambda x: x.ranking_score.overall_score, reverse=True)
            
            logger.info(f"Ranked {len(ranked_sources)} sources")
            return ranked_sources
            
        except Exception as e:
            logger.error(f"Source ranking failed: {e}")
            raise DataCollectionError(f"Source ranking failed: {e}")
    
    def _group_by_source(self, search_results: List[SearchResult]) -> Dict[str, List[SearchResult]]:
        """Group search results by source."""
        source_groups = {}
        
        for result in search_results:
            # Create source identifier
            source_url = result.metadata.get('citation_info', {}).get('source_url', '')
            fund_name = result.metadata.get('hierarchical_fund', '')
            
            # Use fund name as primary grouping, URL as secondary
            if fund_name:
                source_id = f"fund_{fund_name}"
            elif source_url:
                # Extract domain from URL
                domain = self._extract_domain(source_url)
                source_id = f"domain_{domain}"
            else:
                source_id = f"unknown_{result.document_id}"
            
            if source_id not in source_groups:
                source_groups[source_id] = []
            
            source_groups[source_id].append(result)
        
        return source_groups
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return 'unknown'
        
        # Simple domain extraction
        match = re.search(r'https?://([^/]+)', url)
        if match:
            domain = match.group(1)
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain)
            return domain
        
        return 'unknown'
    
    def _calculate_ranking_score(self, results: List[SearchResult], query: ProcessedQuery) -> RankingScore:
        """Calculate comprehensive ranking score for a source."""
        criteria_scores = {}
        
        # Relevance score
        criteria_scores[RankingCriteria.RELEVANCE] = self._calculate_relevance_score(results, query)
        
        # Quality score
        criteria_scores[RankingCriteria.QUALITY] = self._calculate_quality_score(results)
        
        # Recency score
        criteria_scores[RankingCriteria.RECENCY] = self._calculate_recency_score(results)
        
        # Completeness score
        criteria_scores[RankingCriteria.COMPLETENESS] = self._calculate_completeness_score(results)
        
        # Authority score
        criteria_scores[RankingCriteria.AUTHORITY] = self._calculate_authority_score(results)
        
        # Coverage score
        criteria_scores[RankingCriteria.COVERAGE] = self._calculate_coverage_score(results, query)
        
        # Calculate overall score
        overall_score = 0.0
        for criteria, score in criteria_scores.items():
            weight = self.criteria_weights.get(criteria, 0.0)
            overall_score += score * weight
        
        # Create ranking metadata
        ranking_metadata = {
            'result_count': len(results),
            'average_similarity': sum(r.similarity_score for r in results) / len(results),
            'highest_similarity': max(r.similarity_score for r in results),
            'lowest_similarity': min(r.similarity_score for r in results),
            'ranking_timestamp': datetime.now().isoformat()
        }
        
        return RankingScore(
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            ranking_metadata=ranking_metadata
        )
    
    def _calculate_relevance_score(self, results: List[SearchResult], query: ProcessedQuery) -> float:
        """Calculate relevance score based on query-match."""
        if not results:
            return 0.0
        
        # Average similarity score
        avg_similarity = sum(r.similarity_score for r in results) / len(results)
        
        # Bonus for query intent matching
        intent_bonus = 0.0
        query_intent = query.query_intent
        
        for result in results:
            metadata = result.metadata
            
            # Check content type matching
            if 'content_type' in metadata and metadata['content_type'] == query_intent.value:
                intent_bonus += 0.1
            
            # Check financial data relevance
            if 'financial_data' in metadata and metadata['financial_data']:
                intent_bonus += 0.05
        
        intent_bonus = min(intent_bonus, 0.2)  # Cap bonus
        
        return min(avg_similarity + intent_bonus, 1.0)
    
    def _calculate_quality_score(self, results: List[SearchResult]) -> float:
        """Calculate quality score based on content quality."""
        if not results:
            return 0.0
        
        total_quality = 0.0
        
        for result in results:
            metadata = result.metadata
            content = result.content
            quality_score = 0.0
            
            # Base quality from metadata
            if 'quality_score' in metadata:
                quality_score += metadata['quality_score'] * 0.5
            
            # Financial data presence
            if 'financial_data' in metadata and metadata['financial_data']:
                quality_score += 0.1
            
            # Content length (not too short, not too long)
            content_length = len(content)
            if 100 <= content_length <= 1000:
                quality_score += 0.1
            elif 50 <= content_length <= 2000:
                quality_score += 0.05
            
            # Structured information
            structured_matches = len(re.findall(self.quality_indicators['structured_info'], content))
            if structured_matches >= 2:
                quality_score += 0.1
            elif structured_matches >= 1:
                quality_score += 0.05
            
            # Sentence structure
            sentence_matches = len(re.findall(self.quality_indicators['complete_sentences'], content))
            if sentence_matches >= 3:
                quality_score += 0.1
            elif sentence_matches >= 1:
                quality_score += 0.05
            
            # Coherence
            coherent_matches = len(re.findall(self.quality_indicators['coherent_text'], content))
            if coherent_matches >= 2:
                quality_score += 0.05
            
            total_quality += min(quality_score, 1.0)
        
        return min(total_quality / len(results), 1.0)
    
    def _calculate_recency_score(self, results: List[SearchResult]) -> float:
        """Calculate recency score based on content freshness."""
        if not results:
            return 0.0
        
        total_recency = 0.0
        current_time = datetime.now()
        
        for result in results:
            metadata = result.metadata
            recency_score = 0.5  # Default score
            
            # Check for timestamp
            timestamp_str = None
            if 'last_updated' in metadata:
                timestamp_str = metadata['last_updated']
            elif 'processed_at' in metadata:
                timestamp_str = metadata['processed_at']
            elif 'citation_info' in metadata:
                timestamp_str = metadata['citation_info'].get('last_updated', '')
            
            if timestamp_str:
                try:
                    # Parse timestamp
                    if 'T' in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        # Try different date formats
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
                    
                    # Calculate age in days
                    age_days = (current_time - timestamp).days
                    
                    # Score based on recency (more recent = higher score)
                    if age_days <= 7:
                        recency_score = 1.0
                    elif age_days <= 30:
                        recency_score = 0.8
                    elif age_days <= 90:
                        recency_score = 0.6
                    elif age_days <= 365:
                        recency_score = 0.4
                    else:
                        recency_score = 0.2
                        
                except (ValueError, TypeError):
                    # If parsing fails, use default score
                    pass
            
            total_recency += recency_score
        
        return total_recency / len(results)
    
    def _calculate_completeness_score(self, results: List[SearchResult]) -> float:
        """Calculate completeness score based on metadata completeness."""
        if not results:
            return 0.0
        
        total_completeness = 0.0
        
        for result in results:
            metadata = result.metadata
            completeness_score = 0.0
            
            # Required fields
            required_fields = ['chunk_id', 'source_document_id', 'content_type', 'citation_info']
            present_fields = sum(1 for field in required_fields if field in metadata and metadata[field])
            completeness_score += (present_fields / len(required_fields)) * 0.5
            
            # Optional but important fields
            optional_fields = ['financial_data', 'hierarchical_keys', 'retrieval_tags', 'quality_score']
            present_optional = sum(1 for field in optional_fields if field in metadata and metadata[field])
            completeness_score += (present_optional / len(optional_fields)) * 0.3
            
            # Citation completeness
            citation_info = metadata.get('citation_info', {})
            citation_fields = ['source_url', 'fund_name', 'last_updated']
            present_citation = sum(1 for field in citation_fields if field in citation_info and citation_info[field])
            if citation_fields:
                completeness_score += (present_citation / len(citation_fields)) * 0.2
            
            total_completeness += min(completeness_score, 1.0)
        
        return total_completeness / len(results)
    
    def _calculate_authority_score(self, results: List[SearchResult]) -> float:
        """Calculate authority score based on source credibility."""
        if not results:
            return 0.0
        
        total_authority = 0.0
        
        for result in results:
            metadata = result.metadata
            authority_score = 0.0
            
            # Check source URL
            source_url = metadata.get('citation_info', {}).get('source_url', '')
            if source_url:
                domain = self._extract_domain(source_url)
                
                # Official domains get highest score
                if domain in self.official_domains:
                    authority_score = 1.0
                # Known financial platforms
                elif any(financial in domain for financial in ['moneycontrol', 'economic', 'financial', 'invest']):
                    authority_score = 0.8
                # Other domains
                else:
                    authority_score = 0.5
            else:
                # No URL, lower authority
                authority_score = 0.3
            
            # Bonus for official fund mentions
            if 'hdfc' in metadata.get('hierarchical_fund', '').lower():
                authority_score += 0.1
            
            total_authority += min(authority_score, 1.0)
        
        return total_authority / len(results)
    
    def _calculate_coverage_score(self, results: List[SearchResult], query: ProcessedQuery) -> float:
        """Calculate coverage score based on query coverage."""
        if not results:
            return 0.0
        
        # Check if results cover different aspects of the query
        content_types = set()
        fund_types = set()
        financial_aspects = set()
        
        for result in results:
            metadata = result.metadata
            
            # Content types
            if 'content_type' in metadata:
                content_types.add(metadata['content_type'])
            
            # Fund types
            if 'hierarchical_type' in metadata:
                fund_types.add(metadata['hierarchical_type'])
            
            # Financial aspects
            financial_data = metadata.get('financial_data', {})
            for aspect in financial_data.keys():
                financial_aspects.add(aspect)
        
        # Calculate coverage based on diversity
        coverage_score = 0.0
        
        # Content type diversity
        content_diversity = len(content_types) / max(len(query.filters.get('content_types', [1])), 1)
        coverage_score += content_diversity * 0.4
        
        # Fund type diversity
        fund_diversity = len(fund_types) / max(len(query.filters.get('fund_types', [1])), 1)
        coverage_score += fund_diversity * 0.3
        
        # Financial aspect diversity
        financial_diversity = len(financial_aspects) / 5  # Assuming max 5 aspects
        coverage_score += financial_diversity * 0.3
        
        return min(coverage_score, 1.0)
    
    def _create_source_info(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Create source information from grouped results."""
        if not results:
            return {}
        
        first_result = results[0]
        metadata = first_result.metadata
        citation_info = metadata.get('citation_info', {})
        
        return {
            'source_id': self._create_source_id(results),
            'source_url': citation_info.get('source_url', ''),
            'fund_name': metadata.get('hierarchical_fund', ''),
            'domain': self._extract_domain(citation_info.get('source_url', '')),
            'result_count': len(results),
            'average_similarity': sum(r.similarity_score for r in results) / len(results),
            'highest_similarity': max(r.similarity_score for r in results),
            'content_types': list(set(r.metadata.get('content_type', 'general') for r in results)),
            'last_updated': citation_info.get('last_updated', '')
        }
    
    def _create_source_id(self, results: List[SearchResult]) -> str:
        """Create unique source identifier."""
        if not results:
            return 'unknown'
        
        first_result = results[0]
        metadata = first_result.metadata
        
        # Use fund name as primary identifier
        fund_name = metadata.get('hierarchical_fund', '')
        if fund_name:
            return f"fund_{fund_name.lower().replace(' ', '_')}"
        
        # Use domain as secondary identifier
        source_url = metadata.get('citation_info', {}).get('source_url', '')
        if source_url:
            domain = self._extract_domain(source_url)
            return f"domain_{domain}"
        
        # Use document ID as fallback
        return f"doc_{first_result.document_id[:8]}"
    
    def _create_source_metadata(self, results: List[SearchResult], query: ProcessedQuery) -> Dict[str, Any]:
        """Create metadata for the source."""
        if not results:
            return {}
        
        # Aggregate metadata from all results
        all_metadata = {}
        for result in results:
            for key, value in result.metadata.items():
                if key not in all_metadata:
                    all_metadata[key] = []
                all_metadata[key].append(value)
        
        # Create summary metadata
        source_metadata = {
            'query_intent': query.query_intent.value,
            'query_type': query.query_type.value,
            'result_count': len(results),
            'unique_content_types': len(set(r.metadata.get('content_type', 'general') for r in results)),
            'unique_fund_types': len(set(r.metadata.get('hierarchical_type', '') for r in results)),
            'has_financial_data': any(r.metadata.get('financial_data') for r in results),
            'average_quality_score': sum(r.metadata.get('quality_score', 0) for r in results) / len(results),
            'source_authority': self._determine_source_authority(results),
            'creation_timestamp': datetime.now().isoformat()
        }
        
        return source_metadata
    
    def _determine_source_authority(self, results: List[SearchResult]) -> str:
        """Determine source authority level."""
        if not results:
            return 'unknown'
        
        first_result = results[0]
        source_url = first_result.metadata.get('citation_info', {}).get('source_url', '')
        
        if not source_url:
            return 'unknown'
        
        domain = self._extract_domain(source_url)
        
        if domain in self.official_domains:
            return 'official'
        elif any(financial in domain for financial in ['moneycontrol', 'economic', 'financial', 'invest']):
            return 'primary'
        elif any(general in domain for general in ['wikipedia', 'blog', 'news']):
            return 'secondary'
        else:
            return 'general'
    
    def prioritize_official_sources(self, ranked_sources: List[RankedSource]) -> List[RankedSource]:
        """Prioritize official sources in the ranked list."""
        official_sources = []
        other_sources = []
        
        for source in ranked_sources:
            if source.source_metadata.get('source_authority') == 'official':
                official_sources.append(source)
            else:
                other_sources.append(source)
        
        # Combine: official sources first, then others
        return official_sources + other_sources
    
    def get_ranking_summary(self, ranked_sources: List[RankedSource]) -> Dict[str, Any]:
        """Get summary of ranking results."""
        if not ranked_sources:
            return {
                'total_sources': 0,
                'average_score': 0.0,
                'authority_distribution': {},
                'top_source': None
            }
        
        # Calculate statistics
        total_sources = len(ranked_sources)
        average_score = sum(source.ranking_score.overall_score for source in ranked_sources) / total_sources
        
        # Authority distribution
        authority_dist = {}
        for source in ranked_sources:
            authority = source.source_metadata.get('source_authority', 'unknown')
            authority_dist[authority] = authority_dist.get(authority, 0) + 1
        
        # Top source
        top_source = ranked_sources[0] if ranked_sources else None
        
        return {
            'total_sources': total_sources,
            'average_score': average_score,
            'highest_score': ranked_sources[0].ranking_score.overall_score if ranked_sources else 0.0,
            'lowest_score': ranked_sources[-1].ranking_score.overall_score if ranked_sources else 0.0,
            'authority_distribution': authority_dist,
            'top_source': {
                'source_id': top_source.source_info.get('source_id', '') if top_source else '',
                'score': top_source.ranking_score.overall_score if top_source else 0.0,
                'authority': top_source.source_metadata.get('source_authority', '') if top_source else ''
            },
            'ranking_timestamp': datetime.now().isoformat()
        }
    
    def adjust_ranking_weights(self, criteria_weights: Dict[str, float]) -> None:
        """
        Adjust ranking criteria weights.
        
        Args:
            criteria_weights: New weights for criteria
        """
        for criteria_name, weight in criteria_weights.items():
            try:
                criteria_enum = RankingCriteria(criteria_name)
                if 0.0 <= weight <= 1.0:
                    self.criteria_weights[criteria_enum] = weight
                    logger.info(f"Updated weight for {criteria_name}: {weight}")
                else:
                    logger.warning(f"Invalid weight for {criteria_name}: {weight}")
            except ValueError:
                logger.warning(f"Unknown criteria: {criteria_name}")
        
        # Normalize weights
        total_weight = sum(self.criteria_weights.values())
        if total_weight > 0:
            for criteria in self.criteria_weights:
                self.criteria_weights[criteria] /= total_weight
        
        logger.info(f"Normalized ranking weights: {self.criteria_weights}")
    
    def get_ranking_statistics(self) -> Dict[str, Any]:
        """Get ranking system statistics."""
        return {
            'official_domains': self.official_domains,
            'authority_weights': self.authority_weights,
            'criteria_weights': {k.value: v for k, v in self.criteria_weights.items()},
            'quality_indicators': list(self.quality_indicators.keys()),
            'supported_criteria': [criteria.value for criteria in RankingCriteria]
        }
