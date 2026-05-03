"""
Query Classification System for Phase 3

Classifies user queries into different types to determine appropriate response generation strategies.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query type enumeration."""
    FACTUAL = "factual"
    ADVISORY = "advisory"
    PERFORMANCE = "performance"
    PROCEDURAL = "procedural"
    GENERAL = "general"

@dataclass
class QueryClassification:
    """Query classification result."""
    query: str
    query_type: QueryType
    confidence: float
    keywords: List[str]
    entities: List[str]
    intent: str
    subcategory: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class ClassificationPattern:
    """Pattern for query classification."""
    name: str
    query_type: QueryType
    patterns: List[str]
    keywords: List[str]
    entities: List[str]
    intent: str
    subcategory: Optional[str]
    weight: float

class QueryClassifier:
    """
    Classifies user queries into different types for appropriate response generation.
    
    Features:
    - Multi-level query classification
    - Pattern-based classification
    - Keyword and entity extraction
    - Intent recognition
    - Confidence scoring
    """
    
    def __init__(self, cache_dir: str = "cache/query_classifier"):
        """
        Initialize query classifier.
        
        Args:
            cache_dir: Directory for caching classification data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Classification patterns
        self.patterns = self._initialize_patterns()
        
        # Classification statistics
        self.classification_stats = defaultdict(int)
        self.query_history: List[QueryClassification] = []
        
        # Load existing data
        self._load_patterns()
        self._load_stats()
        
        logger.info("Query Classifier initialized")
    
    def _initialize_patterns(self) -> List[ClassificationPattern]:
        """Initialize classification patterns."""
        patterns = []
        
        # Factual query patterns
        factual_patterns = ClassificationPattern(
            name="expense_ratio",
            query_type=QueryType.FACTUAL,
            patterns=[
                r"what.*expense.*ratio",
                r"expense.*ratio.*what",
                r"how.*much.*expense",
                r"total.*expense.*ratio",
                r"annual.*expense.*ratio"
            ],
            keywords=["expense", "ratio", "fees", "cost", "charges"],
            entities=["fund", "scheme", "plan"],
            intent="get_expense_ratio",
            subcategory="fund_metrics",
            weight=1.0
        )
        patterns.append(factual_patterns)
        
        factual_patterns = ClassificationPattern(
            name="minimum_sip",
            query_type=QueryType.FACTUAL,
            patterns=[
                r"minimum.*sip.*amount",
                r"what.*minimum.*sip",
                r"how.*much.*minimum.*sip",
                r"sip.*minimum.*investment",
                r"lowest.*sip.*amount"
            ],
            keywords=["minimum", "sip", "amount", "investment", "installment"],
            entities=["fund", "scheme", "plan"],
            intent="get_minimum_sip",
            subcategory="investment_requirements",
            weight=1.0
        )
        patterns.append(factual_patterns)
        
        factual_patterns = ClassificationPattern(
            name="nav",
            query_type=QueryType.FACTUAL,
            patterns=[
                r"what.*nav",
                r"nav.*what",
                r"current.*nav",
                r"latest.*nav",
                r"today.*nav"
            ],
            keywords=["nav", "net", "asset", "value", "price"],
            entities=["fund", "scheme", "plan"],
            intent="get_nav",
            subcategory="fund_metrics",
            weight=1.0
        )
        patterns.append(factual_patterns)
        
        factual_patterns = ClassificationPattern(
            name="aum",
            query_type=QueryType.FACTUAL,
            patterns=[
                r"what.*aum",
                r"aum.*what",
                r"assets.*under.*management",
                r"total.*assets",
                r"fund.*size"
            ],
            keywords=["aum", "assets", "size", "corpus", "management"],
            entities=["fund", "scheme", "plan"],
            intent="get_aum",
            subcategory="fund_metrics",
            weight=1.0
        )
        patterns.append(factual_patterns)
        
        factual_patterns = ClassificationPattern(
            name="risk_level",
            query_type=QueryType.FACTUAL,
            patterns=[
                r"what.*risk.*level",
                r"risk.*level.*what",
                r"how.*risky",
                r"risk.*profile",
                r"risk.*category"
            ],
            keywords=["risk", "level", "profile", "category", "conservative", "aggressive"],
            entities=["fund", "scheme", "plan"],
            intent="get_risk_level",
            subcategory="risk_metrics",
            weight=1.0
        )
        patterns.append(factual_patterns)
        
        # Advisory query patterns
        advisory_patterns = ClassificationPattern(
            name="investment_advice",
            query_type=QueryType.ADVISORY,
            patterns=[
                r"should.*invest",
                r"invest.*should.*i",
                r"recommend.*fund",
                r"which.*fund.*better",
                r"good.*investment"
            ],
            keywords=["should", "recommend", "better", "good", "advice", "suggest"],
            entities=["fund", "scheme", "plan", "investment"],
            intent="provide_investment_advice",
            subcategory="investment_guidance",
            weight=1.0
        )
        patterns.append(advisory_patterns)
        
        advisory_patterns = ClassificationPattern(
            name="comparison",
            query_type=QueryType.ADVISORY,
            patterns=[
                r"compare.*fund",
                r"fund.*compare",
                r"which.*better.*fund",
                r"fund.*vs.*fund",
                r"difference.*between"
            ],
            keywords=["compare", "better", "vs", "versus", "difference"],
            entities=["fund", "scheme", "plan"],
            intent="compare_funds",
            subcategory="fund_comparison",
            weight=1.0
        )
        patterns.append(advisory_patterns)
        
        # Performance query patterns
        performance_patterns = ClassificationPattern(
            name="historical_returns",
            query_type=QueryType.PERFORMANCE,
            patterns=[
                r"historical.*returns",
                r"past.*performance",
                r"returns.*history",
                r"how.*performed",
                r"track.*record"
            ],
            keywords=["returns", "performance", "historical", "past", "track", "record"],
            entities=["fund", "scheme", "plan"],
            intent="get_historical_returns",
            subcategory="performance_metrics",
            weight=1.0
        )
        patterns.append(performance_patterns)
        
        performance_patterns = ClassificationPattern(
            name="benchmark_comparison",
            query_type=QueryType.PERFORMANCE,
            patterns=[
                r"compare.*benchmark",
                r"benchmark.*performance",
                r"outperform.*benchmark",
                r"beat.*index",
                r"relative.*performance"
            ],
            keywords=["benchmark", "index", "outperform", "beat", "relative"],
            entities=["fund", "scheme", "plan", "benchmark", "index"],
            intent="compare_benchmark",
            subcategory="performance_comparison",
            weight=1.0
        )
        patterns.append(performance_patterns)
        
        # Procedural query patterns
        procedural_patterns = ClassificationPattern(
            name="investment_process",
            query_type=QueryType.PROCEDURAL,
            patterns=[
                r"how.*invest",
                r"invest.*how",
                r"steps.*invest",
                r"process.*invest",
                r"start.*investment"
            ],
            keywords=["how", "steps", "process", "start", "begin", "invest"],
            entities=["fund", "scheme", "plan", "sip", "investment"],
            intent="provide_investment_process",
            subcategory="investment_procedure",
            weight=1.0
        )
        patterns.append(procedural_patterns)
        
        procedural_patterns = ClassificationPattern(
            name="redemption_process",
            query_type=QueryType.PROCEDURAL,
            patterns=[
                r"how.*redeem",
                r"redeem.*how",
                r"withdraw.*money",
                r"sell.*units",
                r"exit.*fund"
            ],
            keywords=["redeem", "withdraw", "sell", "exit", "withdrawal"],
            entities=["fund", "scheme", "plan", "units"],
            intent="provide_redemption_process",
            subcategory="redemption_procedure",
            weight=1.0
        )
        patterns.append(procedural_patterns)
        
        procedural_patterns = ClassificationPattern(
            name="statement_download",
            query_type=QueryType.PROCEDURAL,
            patterns=[
                r"download.*statement",
                r"statement.*download",
                r"get.*account.*statement",
                r"portfolio.*statement",
                r"transaction.*statement"
            ],
            keywords=["download", "statement", "account", "portfolio", "transaction"],
            entities=["statement", "account", "portfolio"],
            intent="provide_statement_download",
            subcategory="document_procedure",
            weight=1.0
        )
        patterns.append(procedural_patterns)
        
        procedural_patterns = ClassificationPattern(
            name="kyc_process",
            query_type=QueryType.PROCEDURAL,
            patterns=[
                r"kyc.*process",
                r"how.*kyc",
                r"complete.*kyc",
                r"kyc.*requirements",
                r"know.*your.*customer"
            ],
            keywords=["kyc", "know", "customer", "verification", "identity"],
            entities=["kyc", "verification", "identity"],
            intent="provide_kyc_process",
            subcategory="compliance_procedure",
            weight=1.0
        )
        patterns.append(procedural_patterns)
        
        return patterns
    
    def _load_patterns(self) -> None:
        """Load patterns from cache."""
        patterns_file = self.cache_dir / "patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                
                self.patterns = []
                for pattern_data in data:
                    pattern_data['query_type'] = QueryType(pattern_data['query_type'])
                    self.patterns.append(ClassificationPattern(**pattern_data))
                
                logger.info(f"Loaded {len(self.patterns)} classification patterns")
                
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
    
    def _load_stats(self) -> None:
        """Load classification statistics from cache."""
        stats_file = self.cache_dir / "stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                self.classification_stats = defaultdict(int, data.get("classification_stats", {}))
                
                # Load query history
                history_data = data.get("query_history", [])
                self.query_history = []
                for item in history_data:
                    item['query_type'] = QueryType(item['query_type'])
                    self.query_history.append(QueryClassification(**item))
                
                logger.info(f"Loaded classification statistics")
                
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
    
    def _save_patterns(self) -> None:
        """Save patterns to cache."""
        try:
            patterns_file = self.cache_dir / "patterns.json"
            
            serializable_patterns = []
            for pattern in self.patterns:
                pattern_dict = asdict(pattern)
                pattern_dict['query_type'] = pattern.query_type.value
                serializable_patterns.append(pattern_dict)
            
            with open(patterns_file, 'w') as f:
                json.dump(serializable_patterns, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
    
    def _save_stats(self) -> None:
        """Save classification statistics to cache."""
        try:
            stats_file = self.cache_dir / "stats.json"
            
            serializable_history = []
            for classification in self.query_history:
                classification_dict = asdict(classification)
                classification_dict['query_type'] = classification.query_type.value
                serializable_history.append(classification_dict)
            
            data = {
                "classification_stats": dict(self.classification_stats),
                "query_history": serializable_history[-1000]  # Keep last 1000
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def classify_query(self, query: str) -> QueryClassification:
        """
        Classify a query into appropriate type.
        
        Args:
            query: User query string
            
        Returns:
            QueryClassification object
        """
        logger.info(f"Classifying query: {query[:100]}...")
        
        # Preprocess query
        processed_query = self._preprocess_query(query)
        
        # Pattern matching
        pattern_matches = self._match_patterns(processed_query)
        
        # Keyword extraction
        keywords = self._extract_keywords(processed_query)
        
        # Entity extraction
        entities = self._extract_entities(processed_query)
        
        # Determine best match
        best_match = self._determine_best_match(pattern_matches, keywords, entities)
        
        # Create classification
        classification = QueryClassification(
            query=query,
            query_type=best_match.query_type if best_match else QueryType.GENERAL,
            confidence=best_match.weight if best_match else 0.5,
            keywords=keywords,
            entities=entities,
            intent=best_match.intent if best_match else "general_inquiry",
            subcategory=best_match.subcategory if best_match else None,
            metadata={
                "processed_query": processed_query,
                "pattern_matches": len(pattern_matches),
                "classification_time": datetime.now().isoformat()
            }
        )
        
        # Update statistics
        self.classification_stats[classification.query_type.value] += 1
        self.query_history.append(classification)
        
        # Save updated stats
        if len(self.query_history) % 10 == 0:
            self._save_stats()
        
        logger.info(f"Query classified as: {classification.query_type.value} (confidence: {classification.confidence:.2f})")
        
        return classification
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for classification."""
        # Convert to lowercase
        processed = query.lower()
        
        # Remove special characters
        processed = re.sub(r'[^\w\s]', ' ', processed)
        
        # Normalize whitespace
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        return processed
    
    def _match_patterns(self, query: str) -> List[Tuple[ClassificationPattern, float]]:
        """Match query against classification patterns."""
        matches = []
        
        for pattern in self.patterns:
            match_score = 0.0
            
            # Check regex patterns
            for regex_pattern in pattern.patterns:
                if re.search(regex_pattern, query, re.IGNORECASE):
                    match_score += 1.0
            
            # Check keyword matches
            keyword_matches = sum(1 for keyword in pattern.keywords if keyword in query)
            if keyword_matches > 0:
                match_score += keyword_matches / len(pattern.keywords)
            
            # Check entity matches
            entity_matches = sum(1 for entity in pattern.entities if entity in query)
            if entity_matches > 0:
                match_score += entity_matches / len(pattern.entities)
            
            # Apply pattern weight
            weighted_score = match_score * pattern.weight
            
            if weighted_score > 0:
                matches.append((pattern, weighted_score))
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Define keyword sets
        factual_keywords = ["expense", "ratio", "nav", "aum", "risk", "minimum", "sip", "amount"]
        advisory_keywords = ["should", "recommend", "better", "good", "advice", "suggest", "compare"]
        performance_keywords = ["returns", "performance", "historical", "past", "track", "record", "benchmark"]
        procedural_keywords = ["how", "steps", "process", "download", "redeem", "withdraw", "kyc", "statement"]
        
        all_keywords = factual_keywords + advisory_keywords + performance_keywords + procedural_keywords
        
        # Extract keywords that appear in query
        found_keywords = []
        for keyword in all_keywords:
            if keyword in query:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query."""
        # Common mutual fund entities
        fund_entities = [
            "hdfc", "fund", "scheme", "plan", "equity", "debt", "hybrid", "elss", "liquid",
            "mid", "cap", "small", "cap", "large", "cap", "focused", "balanced", "growth"
        ]
        
        # Financial entities
        financial_entities = [
            "sip", "systematic", "investment", "plan", "nav", "aum", "expense", "ratio",
            "benchmark", "index", "nifty", "sensex", "bse", "nse"
        ]
        
        all_entities = fund_entities + financial_entities
        
        # Extract entities that appear in query
        found_entities = []
        for entity in all_entities:
            if entity in query:
                found_entities.append(entity)
        
        return found_entities
    
    def _determine_best_match(self, pattern_matches: List[Tuple[ClassificationPattern, float]], 
                             keywords: List[str], entities: List[str]) -> Optional[ClassificationPattern]:
        """Determine the best pattern match."""
        if not pattern_matches:
            return None
        
        # Get top matches
        top_matches = pattern_matches[:3]  # Consider top 3 matches
        
        # Choose the one with highest score
        best_pattern = top_matches[0][0]
        
        # If there are multiple matches with similar scores, prefer more specific patterns
        if len(top_matches) > 1:
            top_score = top_matches[0][1]
            second_score = top_matches[1][1]
            
            # If scores are close (within 10%), check specificity
            if abs(top_score - second_score) < 0.1:
                # Prefer patterns with more keywords and entities
                best_pattern = max(top_matches[:2], key=lambda x: len(x[0].keywords) + len(x[0].entities))[0]
        
        return best_pattern
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """
        Get classification statistics.
        
        Returns:
            Classification statistics dictionary
        """
        total_classifications = sum(self.classification_stats.values())
        
        # Calculate distribution
        distribution = {}
        for query_type, count in self.classification_stats.items():
            distribution[query_type] = {
                "count": count,
                "percentage": (count / total_classifications * 100) if total_classifications > 0 else 0
            }
        
        # Recent trends (last 100 classifications)
        recent_classifications = self.query_history[-100:] if self.query_history else []
        recent_distribution = defaultdict(int)
        for classification in recent_classifications:
            recent_distribution[classification.query_type.value] += 1
        
        recent_trends = {}
        for query_type, count in recent_distribution.items():
            recent_trends[query_type] = (count / len(recent_classifications) * 100) if recent_classifications else 0
        
        return {
            "total_classifications": total_classifications,
            "distribution": distribution,
            "recent_trends": recent_trends,
            "patterns_available": len(self.patterns),
            "query_history_size": len(self.query_history)
        }
    
    def get_patterns_by_type(self, query_type: QueryType) -> List[ClassificationPattern]:
        """
        Get patterns by query type.
        
        Args:
            query_type: Query type to filter by
            
        Returns:
            List of ClassificationPattern objects
        """
        return [pattern for pattern in self.patterns if pattern.query_type == query_type]
    
    def add_custom_pattern(self, name: str, query_type: QueryType, patterns: List[str],
                          keywords: List[str], entities: List[str], intent: str,
                          subcategory: Optional[str] = None, weight: float = 1.0) -> None:
        """
        Add a custom classification pattern.
        
        Args:
            name: Pattern name
            query_type: Query type
            patterns: Regex patterns
            keywords: Keywords list
            entities: Entities list
            intent: Intent description
            subcategory: Subcategory
            weight: Pattern weight
        """
        pattern = ClassificationPattern(
            name=name,
            query_type=query_type,
            patterns=patterns,
            keywords=keywords,
            entities=entities,
            intent=intent,
            subcategory=subcategory,
            weight=weight
        )
        
        self.patterns.append(pattern)
        self._save_patterns()
        
        logger.info(f"Added custom pattern: {name}")
    
    def remove_pattern(self, name: str) -> bool:
        """
        Remove a classification pattern.
        
        Args:
            name: Pattern name to remove
            
        Returns:
            True if pattern was removed
        """
        original_length = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.name != name]
        
        if len(self.patterns) < original_length:
            self._save_patterns()
            logger.info(f"Removed pattern: {name}")
            return True
        
        return False
    
    def batch_classify(self, queries: List[str]) -> List[QueryClassification]:
        """
        Classify multiple queries.
        
        Args:
            queries: List of query strings
            
        Returns:
            List of QueryClassification objects
        """
        classifications = []
        
        for query in queries:
            classification = self.classify_query(query)
            classifications.append(classification)
        
        return classifications
    
    def get_query_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get query suggestions based on partial input.
        
        Args:
            partial_query: Partial query string
            limit: Maximum suggestions to return
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        # Find similar queries from history
        for classification in self.query_history[-100:]:  # Check recent history
            if partial_query.lower() in classification.query.lower():
                suggestions.append(classification.query)
                if len(suggestions) >= limit:
                    break
        
        # If no matches, provide generic suggestions
        if not suggestions:
            generic_suggestions = [
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "What is the minimum SIP amount?",
                "How to start investing in mutual funds?",
                "What are the historical returns?",
                "How to download account statement?"
            ]
            
            suggestions = [s for s in generic_suggestions if partial_query.lower() in s.lower()]
            suggestions.extend(generic_suggestions[:limit])
        
        return suggestions[:limit]
    
    def validate_classification(self, classification: QueryClassification) -> bool:
        """
        Validate a classification result.
        
        Args:
            classification: QueryClassification to validate
            
        Returns:
            True if classification is valid
        """
        # Check required fields
        if not classification.query or not classification.query_type:
            return False
        
        # Check confidence range
        if not 0.0 <= classification.confidence <= 1.0:
            return False
        
        # Check if query type is valid
        if not isinstance(classification.query_type, QueryType):
            return False
        
        # Check if intent is provided
        if not classification.intent:
            return False
        
        return True
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old classification data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old query history
        old_classifications = [
            classification for classification in self.query_history
            if datetime.fromisoformat(classification.metadata.get("classification_time", "1970-01-01")) < cutoff_date
        ]
        
        self.query_history = [
            classification for classification in self.query_history
            if datetime.fromisoformat(classification.metadata.get("classification_time", "1970-01-01")) >= cutoff_date
        ]
        
        # Save updated data
        self._save_stats()
        
        logger.info(f"Cleaned up {len(old_classifications)} old classification records")
        return len(old_classifications)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on query classifier.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_classification_stats()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "patterns_available": len(self.patterns),
                "total_classifications": stats["total_classifications"],
                "query_history_size": stats["query_history_size"],
                "classification_stats": dict(stats["distribution"])
            }
        }
        
        # Check if we have enough patterns
        if len(self.patterns) < 10:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient classification patterns")
        
        # Check if we have enough classification data
        if stats["total_classifications"] < 100:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient classification data")
        
        # Check classification distribution
        if stats["distribution"]:
            max_percentage = max([d["percentage"] for d in stats["distribution"].values()])
            if max_percentage > 80:
                health_status["status"] = "degraded"
                health_status["issues"].append("Classification distribution is skewed")
        
        return health_status
