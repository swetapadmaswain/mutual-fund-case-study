"""
Response Validator for Phase 2.4

Validates LLM responses for compliance, length, and content requirements.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    compliance_score: float
    length_score: float
    content_score: float
    overall_score: float

class ResponseValidator:
    """
    Validates LLM responses for compliance with facts-only requirements.
    
    Features:
    - Response length validation
    - Advisory content detection
    - Citation requirement checking
    - Compliance verification
    - Performance scoring
    """
    
    def __init__(self):
        """Initialize response validator."""
        self.advisory_patterns = self._initialize_advisory_patterns()
        self.compliance_patterns = self._initialize_compliance_patterns()
        self.length_limits = self._initialize_length_limits()
        self.scoring_weights = self._initialize_scoring_weights()
        
        logger.info("Response Validator initialized with compliance rules")
    
    def _initialize_advisory_patterns(self) -> List[str]:
        """Initialize patterns that indicate advisory content."""
        return [
            r'\b(i recommend|we recommend|recommend)\b',
            r'\b(you should|you must|you need to)\b',
            r'\b(best fund|top fund|good fund|better fund)\b',
            r'\b(invest in|buy|sell|switch to)\b',
            r'\b(guaranteed return|sure shot|safe bet)\b',
            r'\b(will perform|expected to|likely to)\b',
            r'\b(consider investing|think about)\b',
            r'\b(perfect for|ideal for|best choice)\b'
        ]
    
    def _initialize_compliance_patterns(self) -> List[str]:
        """Initialize patterns for compliance checking."""
        return [
            r'\b(cannot provide|unable to provide|not able to provide)\b.*\b(advice|recommendation)\b',
            r'\b(consult|speak to|talk to)\b.*\b(financial advisor|expert|professional)\b',
            r'\b(past performance|historical returns)\b.*\b(not guarantee|does not guarantee)\b',
            r'\b(for informational purposes only|educational purposes only)\b',
            r'\b(do your own research|due diligence)\b'
        ]
    
    def _initialize_length_limits(self) -> Dict[str, Dict[str, int]]:
        """Initialize length limits for different response types."""
        return {
            "factual": {"max_sentences": 3, "max_words": 50, "max_characters": 300},
            "advisory": {"max_sentences": 3, "max_words": 50, "max_characters": 300},
            "performance": {"max_sentences": 3, "max_words": 50, "max_characters": 300},
            "procedural": {"max_sentences": 4, "max_words": 60, "max_characters": 350},
            "general": {"max_sentences": 3, "max_words": 50, "max_characters": 300}
        }
    
    def _initialize_scoring_weights(self) -> Dict[str, float]:
        """Initialize scoring weights for validation metrics."""
        return {
            "compliance": 0.5,
            "length": 0.3,
            "content": 0.2
        }
    
    def validate_length(self, response: str, max_sentences: int = 3, max_words: int = 50, max_characters: int = 300) -> bool:
        """
        Validate response length constraints.
        
        Args:
            response: Response text to validate
            max_sentences: Maximum allowed sentences
            max_words: Maximum allowed words
            max_characters: Maximum allowed characters
            
        Returns:
            True if length constraints are met
        """
        # Count sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count words
        words = response.split()
        
        # Count characters
        characters = len(response)
        
        length_valid = (
            len(sentences) <= max_sentences and
            len(words) <= max_words and
            characters <= max_characters
        )
        
        if not length_valid:
            logger.warning(f"Length validation failed: {len(sentences)} sentences, {len(words)} words, {characters} chars")
        
        return length_valid
    
    def check_advisory_content(self, response: str) -> Tuple[bool, List[str]]:
        """
        Check for advisory content in response.
        
        Args:
            response: Response text to check
            
        Returns:
            Tuple of (is_advisory, list of problematic phrases)
        """
        problematic_phrases = []
        
        for pattern in self.advisory_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                problematic_phrases.extend(matches)
        
        is_advisory = len(problematic_phrases) > 0
        
        if is_advisory:
            logger.warning(f"Advisory content detected: {problematic_phrases}")
        
        return is_advisory, problematic_phrases
    
    def ensure_citation(self, response: str, has_context: bool = True) -> bool:
        """
        Ensure response includes proper citations.
        
        Args:
            response: Response text to check
            has_context: Whether context was provided for the response
            
        Returns:
            True if citation requirements are met
        """
        if not has_context:
            # If no context, response should indicate this
            no_context_phrases = [
                "don't have information",
                "not available in context",
                "cannot find in context",
                "context does not contain"
            ]
            
            return any(phrase in response.lower() for phrase in no_context_phrases)
        
        # If context was provided, response should be based on it
        context_based_phrases = [
            "according to",
            "based on",
            "as per",
            "from the context"
        ]
        
        return any(phrase in response.lower() for phrase in context_based_phrases)
    
    def verify_compliance(self, response: str, query_type: str = "factual") -> ValidationResult:
        """
        Verify overall compliance of response.
        
        Args:
            response: Response text to validate
            query_type: Type of query that generated the response
            
        Returns:
            ValidationResult with detailed analysis
        """
        issues = []
        suggestions = []
        
        # Get length limits for query type
        limits = self.length_limits.get(query_type, self.length_limits["general"])
        
        # Validate length
        length_valid = self.validate_length(
            response, 
            limits["max_sentences"], 
            limits["max_words"], 
            limits["max_characters"]
        )
        
        if not length_valid:
            issues.append("Response exceeds length limits")
            suggestions.append(f"Limit to {limits['max_sentences']} sentences, {limits['max_words']} words")
        
        # Check advisory content
        is_advisory, advisory_phrases = self.check_advisory_content(response)
        
        if is_advisory:
            issues.append("Advisory content detected")
            suggestions.append("Remove investment advice language")
            suggestions.append("Focus on factual information only")
        
        # Check for compliance patterns
        compliance_score = self._calculate_compliance_score(response, query_type)
        length_score = self._calculate_length_score(response, limits)
        content_score = self._calculate_content_score(response, query_type)
        
        # Calculate overall score
        weights = self.scoring_weights
        overall_score = (
            compliance_score * weights["compliance"] +
            length_score * weights["length"] +
            content_score * weights["content"]
        )
        
        is_valid = (
            length_valid and
            not is_advisory and
            compliance_score >= 0.8 and
            overall_score >= 0.7
        )
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            compliance_score=compliance_score,
            length_score=length_score,
            content_score=content_score,
            overall_score=overall_score
        )
    
    def _calculate_compliance_score(self, response: str, query_type: str) -> float:
        """Calculate compliance score for response."""
        score = 1.0
        
        # Check for advisory content
        is_advisory, _ = self.check_advisory_content(response)
        if is_advisory:
            score -= 0.5
        
        # Check for compliance patterns
        compliance_matches = 0
        for pattern in self.compliance_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                compliance_matches += 1
        
        # Bonus for compliance patterns
        if query_type == "advisory":
            if compliance_matches >= 1:
                score += 0.2
        elif query_type == "performance":
            if compliance_matches >= 1:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_length_score(self, response: str, limits: Dict[str, int]) -> float:
        """Calculate length score for response."""
        sentences = len([s.strip() for s in re.split(r'[.!?]+', response) if s.strip()])
        words = len(response.split())
        characters = len(response)
        
        sentence_score = 1.0 - max(0, sentences - limits["max_sentences"]) / limits["max_sentences"]
        word_score = 1.0 - max(0, words - limits["max_words"]) / limits["max_words"]
        char_score = 1.0 - max(0, characters - limits["max_characters"]) / limits["max_characters"]
        
        return (sentence_score + word_score + char_score) / 3.0
    
    def _calculate_content_score(self, response: str, query_type: str) -> float:
        """Calculate content quality score for response."""
        score = 1.0
        
        # Check for factual language
        if query_type == "factual":
            factual_indicators = ["is", "are", "was", "were", "has", "have", "according to", "based on"]
            factual_count = sum(1 for indicator in factual_indicators if indicator in response.lower())
            score += min(0.2, factual_count * 0.05)
        
        # Check for refusal in advisory
        if query_type == "advisory":
            refusal_phrases = ["cannot provide", "unable to provide", "not provide advice"]
            if any(phrase in response.lower() for phrase in refusal_phrases):
                score += 0.3
        
        # Check for disclaimer in performance
        if query_type == "performance":
            disclaimer_phrases = ["past performance", "does not guarantee", "for informational"]
            if any(phrase in response.lower() for phrase in disclaimer_phrases):
                score += 0.2
        
        # Check for procedural steps
        if query_type == "procedural":
            step_indicators = ["first", "then", "next", "finally", "step"]
            step_count = sum(1 for indicator in step_indicators if indicator in response.lower())
            score += min(0.2, step_count * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def validate_response_batch(self, responses: List[str], query_types: List[str]) -> List[ValidationResult]:
        """
        Validate multiple responses.
        
        Args:
            responses: List of response texts
            query_types: List of corresponding query types
            
        Returns:
            List of ValidationResult objects
        """
        if len(responses) != len(query_types):
            raise ValueError("Responses and query types must have same length")
        
        results = []
        for response, query_type in zip(responses, query_types):
            result = self.verify_compliance(response, query_type)
            results.append(result)
        
        return results
    
    def get_compliance_report(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Generate detailed compliance report.
        
        Args:
            validation_result: ValidationResult object
            
        Returns:
            Detailed compliance report
        """
        return {
            "overall_valid": validation_result.is_valid,
            "overall_score": validation_result.overall_score,
            "component_scores": {
                "compliance": validation_result.compliance_score,
                "length": validation_result.length_score,
                "content": validation_result.content_score
            },
            "issues": validation_result.issues,
            "suggestions": validation_result.suggestions,
            "recommendations": self._generate_recommendations(validation_result)
        }
    
    def _generate_recommendations(self, validation_result: ValidationResult) -> List[str]:
        """Generate specific recommendations based on validation result."""
        recommendations = []
        
        if validation_result.compliance_score < 0.8:
            recommendations.append("Review for advisory content and remove investment advice")
            recommendations.append("Add compliance statements and disclaimers")
        
        if validation_result.length_score < 0.8:
            recommendations.append("Shorten response to meet length constraints")
            recommendations.append("Focus on key information only")
        
        if validation_result.content_score < 0.8:
            recommendations.append("Improve factual content quality")
            recommendations.append("Add more specific information from context")
        
        if validation_result.overall_score < 0.7:
            recommendations.append("Major revision needed for compliance")
            recommendations.append("Consider regenerating response with stricter constraints")
        
        return recommendations
    
    def reset_statistics(self) -> None:
        """Reset validation statistics."""
        logger.info("Response validator statistics reset")
