"""
Query processing module for Phase 2.3 - Retrieval System Development.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import unicodedata

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError


class QueryType(Enum):
    """Query classification types."""
    FACTUAL = "factual"
    ADVISORY = "advisory"
    PERFORMANCE = "performance"
    PROCEDURAL = "procedural"
    GENERAL = "general"


class QueryIntent(Enum):
    """Query intent classifications."""
    EXPENSE_RATIO = "expense_ratio"
    EXIT_LOAD = "exit_load"
    NAV = "nav"
    SIP = "sip"
    AUM = "aum"
    RISK = "risk"
    BENCHMARK = "benchmark"
    PERFORMANCE_RETURNS = "performance_returns"
    INVESTMENT_OBJECTIVE = "investment_objective"
    FUND_COMPARISON = "fund_comparison"
    INVESTMENT_GUIDANCE = "investment_guidance"
    PROCEDURAL_HELP = "procedural_help"
    GENERAL_INFO = "general_info"


@dataclass
class ProcessedQuery:
    """Represents a processed query with analysis."""
    original_query: str
    cleaned_query: str
    query_type: QueryType
    query_intent: QueryIntent
    entities: List[str]
    keywords: List[str]
    filters: Dict[str, Any]
    confidence: float
    processing_metadata: Dict[str, Any]


class QueryProcessor:
    """Processes and analyzes user queries for retrieval system."""
    
    def __init__(self):
        """Initialize the query processor."""
        # Financial entity patterns
        self.entity_patterns = {
            'fund_names': [
                r'\bhdfc\s+(mid\s+cap|large\s+cap|equity|focused|elss\s+tax\s+saver)\s+fund\b',
                r'\bhdfc\s+(midcap|largecap|equity|focused|elss)\b',
                r'\b(mid\s+cap|large\s+cap|equity|focused|elss)\s+fund\b'
            ],
            'fund_types': [
                r'\b(mid\s+cap|large\s+cap|small\s+cap|multi\s+cap|flexi\s+cap|equity|debt|hybrid|focused|arbitrage|elss)\b'
            ],
            'financial_terms': [
                r'\b(expense\s+ratio|exit\s+load|nav|sip|aum|risk|benchmark|returns|performance)\b',
                r'\b(net\s+asset\s+value|systematic\s+investment\s+plan|assets\s+under\s+management)\b'
            ],
            'amounts': [
                r'\b₹?\d+(,\d{3})*(.\d+)?\s*(rs|rupees|inr)?\b',
                r'\b\d+(,\d{3})*(.\d+)?\s*%\b'
            ],
            'time_periods': [
                r'\b(\d+\s*(year|month|day)s?|1y|3y|5y|10y)\b',
                r'\b(daily|monthly|quarterly|annually|yearly)\b'
            ]
        }
        
        # Query type patterns
        self.query_type_patterns = {
            QueryType.ADVISORY: [
                r'\b(should|must|recommend|suggest|advise)\s+(i|we|one)\s+(invest|buy|sell|choose|select)\b',
                r'\b(which\s+fund\s+is\s+better|best\s+fund|top\s+fund|recommended\s+fund)\b',
                r'\b(is\s+it\s+(good|bad|worthwhile|advisable)\s+to\s+invest\b',
                r'\b(should\s+i\s+(invest|put\s+money)|how\s+much\s+to\s+invest)\b'
            ],
            QueryType.PERFORMANCE: [
                r'\b(performance|returns|growth|profit|gain|loss)\b',
                r'\b(historical|past|previous)\s+(returns|performance)\b',
                r'\b(compared\s+to|better\s+than|worse\s+than)\b',
                r'\b(\d+%\s+returns?|\d+\s*year\s+returns?)\b'
            ],
            QueryType.PROCEDURAL: [
                r'\b(how\s+to|what\s+is\s+the\s+process|steps\s+to|procedure\s+for)\b',
                r'\b(download|get|obtain|apply|register|invest)\b',
                r'\b(statement|account|kyc|pan|nominee)\b',
                r'\b(withdraw|redeem|switch|exit)\b'
            ],
            QueryType.FACTUAL: [
                r'\b(what|when|where|who)\s+(is|are|was|were)\b',
                r'\b(expense\s+ratio|exit\s+load|nav|sip|aum|risk|benchmark)\b',
                r'\b(minimum|maximum|amount|limit|duration)\b'
            ]
        }
        
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.EXPENSE_RATIO: [
                r'\b(expense\s+ratio|charges|fees|annual\s+charges|management\s+fees)\b'
            ],
            QueryIntent.EXIT_LOAD: [
                r'\b(exit\s+load|withdrawal\s+load|redemption\s+charges|exit\s+charges)\b'
            ],
            QueryIntent.NAV: [
                r'\b(nav|net\s+asset\s+value|current\s+nav|nav\s+value)\b'
            ],
            QueryIntent.SIP: [
                r'\b(sip|systematic\s+investment\s+plan|monthly\s+investment|regular\s+investment)\b'
            ],
            QueryIntent.AUM: [
                r'\b(aum|assets\s+under\s+management|fund\s+size|total\s+assets)\b'
            ],
            QueryIntent.RISK: [
                r'\b(risk|riskometer|risk\s+level|risk\s+profile|volatility)\b'
            ],
            QueryIntent.BENCHMARK: [
                r'\b(benchmark|index|comparison|nifty|sensex)\b'
            ],
            QueryIntent.PERFORMANCE_RETURNS: [
                r'\b(returns|performance|growth|profit|gain|historical\s+returns)\b'
            ],
            QueryIntent.INVESTMENT_OBJECTIVE: [
                r'\b(objective|goal|strategy|purpose|investment\s+aim)\b'
            ],
            QueryIntent.FUND_COMPARISON: [
                r'\b(compare|comparison|vs|versus|better\s+than|worse\s+than)\b'
            ],
            QueryIntent.INVESTMENT_GUIDANCE: [
                r'\b(should|must|recommend|suggest|advise)\s+(i|we|one)\s+(invest|buy|sell)\b'
            ],
            QueryIntent.PROCEDURAL_HELP: [
                r'\b(how\s+to|what\s+is\s+the\s+process|steps\s+to|procedure\s+for)\b'
            ],
            QueryIntent.GENERAL_INFO: [
                r'\b(what|when|where|who|information|details|about)\b'
            ]
        }
        
        logger.info("Initialized QueryProcessor")
    
    def process_query(self, query: str) -> ProcessedQuery:
        """
        Process and analyze a user query.
        
        Args:
            query: Raw user query
            
        Returns:
            ProcessedQuery object with analysis results
        """
        logger.debug(f"Processing query: {query}")
        
        try:
            # Step 1: Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Step 2: Extract entities
            entities = self._extract_entities(cleaned_query)
            
            # Step 3: Extract keywords
            keywords = self._extract_keywords(cleaned_query)
            
            # Step 4: Classify query type
            query_type = self._classify_query_type(cleaned_query)
            
            # Step 5: Determine query intent
            query_intent = self._determine_query_intent(cleaned_query)
            
            # Step 6: Generate filters
            filters = self._generate_filters(entities, keywords, query_intent)
            
            # Step 7: Calculate confidence
            confidence = self._calculate_confidence(query_type, query_intent, entities, keywords)
            
            # Step 8: Create processing metadata
            processing_metadata = self._create_processing_metadata(query, cleaned_query)
            
            processed_query = ProcessedQuery(
                original_query=query,
                cleaned_query=cleaned_query,
                query_type=query_type,
                query_intent=query_intent,
                entities=entities,
                keywords=keywords,
                filters=filters,
                confidence=confidence,
                processing_metadata=processing_metadata
            )
            
            logger.debug(f"Processed query: type={query_type.value}, intent={query_intent.value}, confidence={confidence:.2f}")
            return processed_query
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise DataCollectionError(f"Query processing failed: {e}")
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize the query text.
        
        Args:
            query: Raw query text
            
        Returns:
            Cleaned query text
        """
        if not query:
            return ""
        
        # Normalize Unicode characters
        query = unicodedata.normalize('NFKC', query)
        
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Remove special characters but keep important financial symbols
        query = re.sub(r'[^\w\s₹%.,-]', ' ', query)
        
        # Normalize financial symbols
        query = re.sub(r'rs\.?|rupees?|inr', '₹', query)
        query = re.sub(r'percent|percentage', '%', query)
        
        # Strip leading/trailing whitespace
        query = query.strip()
        
        return query
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities from the query.
        
        Args:
            query: Cleaned query text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract fund names
        for pattern in self.entity_patterns['fund_names']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract fund types
        for pattern in self.entity_patterns['fund_types']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract financial terms
        for pattern in self.entity_patterns['financial_terms']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract amounts
        for pattern in self.entity_patterns['amounts']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract time periods
        for pattern in self.entity_patterns['time_periods']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates and normalize
        entities = list(set([entity.strip().lower() for entity in entities if entity.strip()]))
        
        return entities
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract relevant keywords from the query.
        
        Args:
            query: Cleaned query text
            
        Returns:
            List of keywords
        """
        # Define important keywords
        important_keywords = {
            'fund': 'fund',
            'mutual': 'mutual',
            'investment': 'investment',
            'invest': 'invest',
            'money': 'money',
            'return': 'return',
            'risk': 'risk',
            'performance': 'performance',
            'expense': 'expense',
            'ratio': 'ratio',
            'load': 'load',
            'exit': 'exit',
            'sip': 'sip',
            'nav': 'nav',
            'aum': 'aum',
            'benchmark': 'benchmark',
            'index': 'index',
            'growth': 'growth',
            'profit': 'profit',
            'loss': 'loss',
            'gain': 'gain',
            'compare': 'compare',
            'comparison': 'comparison',
            'better': 'better',
            'best': 'best',
            'top': 'top',
            'recommend': 'recommend',
            'suggest': 'suggest',
            'advise': 'advise',
            'should': 'should',
            'must': 'must',
            'how': 'how',
            'what': 'what',
            'when': 'when',
            'where': 'where',
            'why': 'why',
            'procedure': 'procedure',
            'process': 'process',
            'step': 'step',
            'guide': 'guide',
            'help': 'help',
            'download': 'download',
            'apply': 'apply',
            'register': 'register',
            'account': 'account',
            'statement': 'statement',
            'kyc': 'kyc',
            'pan': 'pan'
        }
        
        # Tokenize query
        tokens = query.split()
        
        # Filter keywords
        keywords = []
        for token in tokens:
            if token in important_keywords:
                keywords.append(important_keywords[token])
            elif len(token) > 2 and token.isalpha():
                # Include meaningful words longer than 2 characters
                keywords.append(token)
        
        # Remove duplicates
        keywords = list(set(keywords))
        
        return keywords
    
    def _classify_query_type(self, query: str) -> QueryType:
        """
        Classify the query type.
        
        Args:
            query: Cleaned query text
            
        Returns:
            QueryType enum value
        """
        # Check each query type pattern
        for query_type, patterns in self.query_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return query_type
        
        # Default to general if no pattern matches
        return QueryType.GENERAL
    
    def _determine_query_intent(self, query: str) -> QueryIntent:
        """
        Determine the query intent.
        
        Args:
            query: Cleaned query text
            
        Returns:
            QueryIntent enum value
        """
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        
        # Default to general info if no pattern matches
        return QueryIntent.GENERAL_INFO
    
    def _generate_filters(self, entities: List[str], keywords: List[str], intent: QueryIntent) -> Dict[str, Any]:
        """
        Generate search filters based on entities and intent.
        
        Args:
            entities: Extracted entities
            keywords: Extracted keywords
            intent: Query intent
            
        Returns:
            Dictionary of search filters
        """
        filters = {}
        
        # Fund name filters
        fund_names = []
        for entity in entities:
            if 'hdfc' in entity and ('fund' in entity or 'midcap' in entity or 'largecap' in entity):
                # Normalize fund names
                if 'mid' in entity:
                    fund_names.append('hdfc_mid_cap_fund')
                elif 'large' in entity:
                    fund_names.append('hdfc_large_cap_fund')
                elif 'equity' in entity:
                    fund_names.append('hdfc_equity_fund')
                elif 'focused' in entity:
                    fund_names.append('hdfc_focused_fund')
                elif 'elss' in entity or 'tax' in entity:
                    fund_names.append('hdfc_elss_tax_saver_fund')
        
        if fund_names:
            filters['fund_names'] = fund_names
        
        # Fund type filters
        fund_types = []
        for entity in entities:
            if entity in ['mid cap', 'midcap', 'mid_cap']:
                fund_types.append('mid_cap')
            elif entity in ['large cap', 'largecap', 'large_cap']:
                fund_types.append('large_cap')
            elif entity in ['equity']:
                fund_types.append('equity')
            elif entity in ['focused']:
                fund_types.append('focused')
            elif entity in ['elss', 'tax saver']:
                fund_types.append('elss')
        
        if fund_types:
            filters['fund_types'] = fund_types
        
        # Content type filters based on intent
        content_type_mapping = {
            QueryIntent.EXPENSE_RATIO: 'expense_ratio',
            QueryIntent.EXIT_LOAD: 'exit_load',
            QueryIntent.NAV: 'nav',
            QueryIntent.SIP: 'sip',
            QueryIntent.AUM: 'aum',
            QueryIntent.RISK: 'risk',
            QueryIntent.BENCHMARK: 'benchmark',
            QueryIntent.PERFORMANCE_RETURNS: 'performance',
            QueryIntent.INVESTMENT_OBJECTIVE: 'objective',
            QueryIntent.GENERAL_INFO: 'general'
        }
        
        if intent in content_type_mapping:
            filters['content_types'] = [content_type_mapping[intent]]
        
        # Amount filters
        amounts = []
        for entity in entities:
            # Extract numeric amounts
            amount_match = re.search(r'₹?\d+(,\d{3})*(.\d+)?', entity)
            if amount_match:
                amounts.append(amount_match.group())
        
        if amounts:
            filters['amounts'] = amounts
        
        return filters
    
    def _calculate_confidence(self, query_type: QueryType, query_intent: QueryIntent, 
                            entities: List[str], keywords: List[str]) -> float:
        """
        Calculate confidence score for the query processing.
        
        Args:
            query_type: Classified query type
            query_intent: Determined query intent
            entities: Extracted entities
            keywords: Extracted keywords
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # Base confidence
        confidence += 0.3
        
        # Entity confidence
        if entities:
            entity_score = min(len(entities) * 0.1, 0.3)
            confidence += entity_score
        
        # Keyword confidence
        if keywords:
            keyword_score = min(len(keywords) * 0.05, 0.2)
            confidence += keyword_score
        
        # Intent confidence (specific intents get higher scores)
        intent_scores = {
            QueryIntent.EXPENSE_RATIO: 0.15,
            QueryIntent.EXIT_LOAD: 0.15,
            QueryIntent.NAV: 0.15,
            QueryIntent.SIP: 0.15,
            QueryIntent.AUM: 0.1,
            QueryIntent.RISK: 0.1,
            QueryIntent.BENCHMARK: 0.1,
            QueryIntent.PERFORMANCE_RETURNS: 0.1,
            QueryIntent.INVESTMENT_OBJECTIVE: 0.1,
            QueryIntent.FUND_COMPARISON: 0.05,
            QueryIntent.INVESTMENT_GUIDANCE: 0.05,
            QueryIntent.PROCEDURAL_HELP: 0.05,
            QueryIntent.GENERAL_INFO: 0.05
        }
        
        confidence += intent_scores.get(query_intent, 0.05)
        
        # Query type confidence
        if query_type != QueryType.GENERAL:
            confidence += 0.1
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))
    
    def _create_processing_metadata(self, original_query: str, cleaned_query: str) -> Dict[str, Any]:
        """
        Create processing metadata.
        
        Args:
            original_query: Original query text
            cleaned_query: Cleaned query text
            
        Returns:
            Processing metadata dictionary
        """
        return {
            'query_length': len(original_query),
            'cleaned_length': len(cleaned_query),
            'word_count': len(cleaned_query.split()),
            'has_amounts': bool(re.search(r'₹?\d+(,\d{3})*(.\d+)?', cleaned_query)),
            'has_fund_reference': bool(re.search(r'hdfc|fund', cleaned_query)),
            'has_financial_terms': bool(re.search(r'expense|nav|sip|risk|aum', cleaned_query)),
            'processing_timestamp': str(datetime.now())
        }
    
    def batch_process_queries(self, queries: List[str]) -> List[ProcessedQuery]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of query strings
            
        Returns:
            List of ProcessedQuery objects
        """
        logger.info(f"Batch processing {len(queries)} queries")
        
        processed_queries = []
        
        for i, query in enumerate(queries):
            try:
                processed_query = self.process_query(query)
                processed_queries.append(processed_query)
                logger.debug(f"Processed query {i+1}/{len(queries)}")
            except Exception as e:
                logger.error(f"Failed to process query {i+1}: {e}")
                # Create a fallback processed query
                fallback_query = ProcessedQuery(
                    original_query=query,
                    cleaned_query=self._clean_query(query),
                    query_type=QueryType.GENERAL,
                    query_intent=QueryIntent.GENERAL_INFO,
                    entities=[],
                    keywords=[],
                    filters={},
                    confidence=0.1,
                    processing_metadata={'error': str(e)}
                )
                processed_queries.append(fallback_query)
        
        logger.info(f"Batch processed {len(processed_queries)} queries")
        return processed_queries
    
    def get_query_statistics(self, processed_queries: List[ProcessedQuery]) -> Dict[str, Any]:
        """
        Get statistics about processed queries.
        
        Args:
            processed_queries: List of processed queries
            
        Returns:
            Query statistics dictionary
        """
        if not processed_queries:
            return {
                'total_queries': 0,
                'query_types': {},
                'query_intents': {},
                'average_confidence': 0.0,
                'entity_coverage': 0.0
            }
        
        # Query type distribution
        type_counts = {}
        for query in processed_queries:
            type_name = query.query_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Intent distribution
        intent_counts = {}
        for query in processed_queries:
            intent_name = query.query_intent.value
            intent_counts[intent_name] = intent_counts.get(intent_name, 0) + 1
        
        # Average confidence
        avg_confidence = sum(query.confidence for query in processed_queries) / len(processed_queries)
        
        # Entity coverage
        queries_with_entities = sum(1 for query in processed_queries if query.entities)
        entity_coverage = queries_with_entities / len(processed_queries)
        
        return {
            'total_queries': len(processed_queries),
            'query_types': type_counts,
            'query_intents': intent_counts,
            'average_confidence': avg_confidence,
            'entity_coverage': entity_coverage,
            'average_query_length': sum(query.processing_metadata['query_length'] for query in processed_queries) / len(processed_queries),
            'high_confidence_queries': sum(1 for query in processed_queries if query.confidence > 0.7)
        }


# Import datetime for timestamp
from datetime import datetime
