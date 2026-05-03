"""
Response Formatter for Phase 2.4

Formats LLM responses with citations, disclaimers, and consistent structure.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class FormattedResponse:
    """Formatted response with all required components."""
    answer: str
    source: str
    last_updated: str
    disclaimer: str
    query_type: str
    confidence: float
    response_time: float
    citations: List[str]
    metadata: Dict[str, Any]

class ResponseFormatter:
    """
    Formats responses with citations, disclaimers, and consistent structure.
    
    Features:
    - Response formatting with citations
    - Required disclaimers
    - Last updated dates
    - Consistent formatting
    - JSON output support
    """
    
    def __init__(self):
        """Initialize response formatter."""
        self.disclaimers = self._initialize_disclaimers()
        self.source_templates = self._initialize_source_templates()
        self.format_templates = self._initialize_format_templates()
        
        logger.info("Response Formatter initialized with templates")
    
    def _initialize_disclaimers(self) -> Dict[str, str]:
        """Initialize disclaimers for different query types."""
        return {
            "factual": "Facts-only. No investment advice provided.",
            "advisory": "Facts-only. No investment advice provided. Please consult a financial advisor for personalized advice.",
            "performance": "Facts-only. Past performance does not guarantee future results. No investment advice provided.",
            "procedural": "Facts-only. No investment advice provided. Please verify with official sources.",
            "general": "Facts-only. No investment advice provided."
        }
    
    def _initialize_source_templates(self) -> Dict[str, str]:
        """Initialize source citation templates."""
        return {
            "official": "Source: {url}",
            "multiple": "Sources: {urls}",
            "unavailable": "Source information not available",
            "context": "Based on official HDFC Mutual Fund information"
        }
    
    def _initialize_format_templates(self) -> Dict[str, str]:
        """Initialize response format templates."""
        return {
            "standard": "{answer}\n\n{source}\n\n{disclaimer}",
            "with_date": "{answer}\n\n{source}\nLast updated: {date}\n\n{disclaimer}",
            "minimal": "{answer}\n\n{disclaimer}",
            "json": "json_format"
        }
    
    def format_response(self, response: str, citation: str, date: str, query_type: str = "factual", 
                       confidence: float = 1.0, response_time: float = 0.0) -> FormattedResponse:
        """
        Format response with all required components.
        
        Args:
            response: Raw response from LLM
            citation: Source citation
            date: Last updated date
            query_type: Type of query
            confidence: Confidence score
            response_time: Response generation time
            
        Returns:
            FormattedResponse object
        """
        # Clean and format the answer
        cleaned_answer = self._clean_answer(response)
        
        # Format citation
        formatted_citation = self._format_citation(citation)
        
        # Get appropriate disclaimer
        disclaimer = self.disclaimers.get(query_type, self.disclaimers["general"])
        
        # Format last updated date
        formatted_date = self._format_date(date)
        
        # Generate citations list
        citations = self._extract_citations(citation)
        
        # Create metadata
        metadata = {
            "query_type": query_type,
            "confidence": confidence,
            "response_time": response_time,
            "format_version": "2.4.0",
            "generated_at": datetime.now().isoformat()
        }
        
        return FormattedResponse(
            answer=cleaned_answer,
            source=formatted_citation,
            last_updated=formatted_date,
            disclaimer=disclaimer,
            query_type=query_type,
            confidence=confidence,
            response_time=response_time,
            citations=citations,
            metadata=metadata
        )
    
    def _clean_answer(self, answer: str) -> str:
        """Clean and format the answer text."""
        # Remove extra whitespace
        answer = ' '.join(answer.split())
        
        # Ensure proper capitalization
        if answer and len(answer) > 0:
            answer = answer[0].upper() + answer[1:]
        
        # Ensure proper ending punctuation
        if answer and not answer.endswith(('.', '!', '?')):
            answer += '.'
        
        return answer
    
    def _format_citation(self, citation: str) -> str:
        """Format source citation."""
        if not citation or citation.lower() == "unavailable":
            return self.source_templates["unavailable"]
        
        if citation.startswith("http"):
            return self.source_templates["official"].format(url=citation)
        
        return citation
    
    def _format_date(self, date: str) -> str:
        """Format last updated date."""
        if not date:
            return datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Try to parse and reformat date
            if len(date) == 10 and date[4] == '-' and date[7] == '-':
                # Already in YYYY-MM-DD format
                return date
            else:
                # Try to parse other formats
                parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                return parsed_date.strftime("%Y-%m-%d")
        except:
            # If parsing fails, return current date
            return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_citations(self, citation: str) -> List[str]:
        """Extract citation URLs from citation string."""
        citations = []
        
        if citation and citation.startswith("http"):
            citations.append(citation)
        
        return citations
    
    def add_disclaimer(self, response: str, query_type: str = "factual") -> str:
        """
        Add disclaimer to response.
        
        Args:
            response: Response text
            query_type: Type of query
            
        Returns:
            Response with disclaimer
        """
        disclaimer = self.disclaimers.get(query_type, self.disclaimers["general"])
        
        if disclaimer not in response:
            return f"{response}\n\n{disclaimer}"
        
        return response
    
    def include_last_updated(self, response: str, date: str) -> str:
        """
        Include last updated date in response.
        
        Args:
            response: Response text
            date: Last updated date
            
        Returns:
            Response with last updated date
        """
        formatted_date = self._format_date(date)
        date_line = f"Last updated: {formatted_date}"
        
        if date_line not in response:
            return f"{response}\n\n{date_line}"
        
        return response
    
    def ensure_consistency(self, response: str) -> str:
        """
        Ensure consistent formatting across responses.
        
        Args:
            response: Response text
            
        Returns:
            Consistently formatted response
        """
        # Clean up multiple newlines
        response = '\n'.join(line for line in response.split('\n') if line.strip())
        
        # Ensure proper spacing after punctuation
        response = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', response)
        
        # Remove extra spaces
        response = ' '.join(response.split())
        
        return response
    
    def format_as_json(self, formatted_response: FormattedResponse) -> str:
        """
        Format response as JSON.
        
        Args:
            formatted_response: FormattedResponse object
            
        Returns:
            JSON string representation
        """
        response_dict = {
            "answer": formatted_response.answer,
            "source": formatted_response.source,
            "last_updated": formatted_response.last_updated,
            "disclaimer": formatted_response.disclaimer,
            "query_type": formatted_response.query_type,
            "confidence": formatted_response.confidence,
            "response_time": formatted_response.response_time,
            "citations": formatted_response.citations,
            "metadata": formatted_response.metadata
        }
        
        return json.dumps(response_dict, indent=2)
    
    def format_for_ui(self, formatted_response: FormattedResponse) -> Dict[str, Any]:
        """
        Format response for UI display.
        
        Args:
            formatted_response: FormattedResponse object
            
        Returns:
            UI-ready dictionary
        """
        return {
            "answer": formatted_response.answer,
            "source": formatted_response.source,
            "last_updated": formatted_response.last_updated,
            "disclaimer": formatted_response.disclaimer,
            "confidence": formatted_response.confidence,
            "query_type": formatted_response.query_type,
            "citations": formatted_response.citations,
            "metadata": {
                "response_time": formatted_response.response_time,
                "generated_at": formatted_response.metadata.get("generated_at")
            }
        }
    
    def create_error_response(self, error_message: str, query_type: str = "factual") -> FormattedResponse:
        """
        Create formatted error response.
        
        Args:
            error_message: Error message
            query_type: Type of query
            
        Returns:
            Formatted error response
        """
        disclaimer = self.disclaimers.get(query_type, self.disclaimers["general"])
        
        return FormattedResponse(
            answer=f"Unable to provide response: {error_message}",
            source=self.source_templates["unavailable"],
            last_updated=datetime.now().strftime("%Y-%m-%d"),
            disclaimer=disclaimer,
            query_type=query_type,
            confidence=0.0,
            response_time=0.0,
            citations=[],
            metadata={
                "error": True,
                "error_message": error_message,
                "format_version": "2.4.0"
            }
        )
    
    def create_advisory_refusal_response(self, query: str, citation: str = "") -> FormattedResponse:
        """
        Create formatted advisory refusal response.
        
        Args:
            query: Original query
            citation: Source citation (optional)
            
        Returns:
            Formatted refusal response
        """
        answer = "I cannot provide investment advice. For personalized investment guidance, please consult a qualified financial advisor."
        
        formatted_citation = self._format_citation(citation) if citation else self.source_templates["context"]
        disclaimer = self.disclaimers["advisory"]
        
        return FormattedResponse(
            answer=answer,
            source=formatted_citation,
            last_updated=datetime.now().strftime("%Y-%m-%d"),
            disclaimer=disclaimer,
            query_type="advisory",
            confidence=1.0,
            response_time=0.0,
            citations=self._extract_citations(citation) if citation else [],
            metadata={
                "refusal_type": "advisory",
                "original_query": query,
                "format_version": "2.4.0"
            }
        )
    
    def create_performance_response(self, performance_data: str, citation: str, date: str) -> FormattedResponse:
        """
        Create formatted performance response with disclaimers.
        
        Args:
            performance_data: Performance information
            citation: Source citation
            date: Last updated date
            
        Returns:
            Formatted performance response
        """
        answer = f"{performance_data} Past performance does not guarantee future results."
        
        formatted_citation = self._format_citation(citation)
        formatted_date = self._format_date(date)
        disclaimer = self.disclaimers["performance"]
        
        return FormattedResponse(
            answer=answer,
            source=formatted_citation,
            last_updated=formatted_date,
            disclaimer=disclaimer,
            query_type="performance",
            confidence=1.0,
            response_time=0.0,
            citations=self._extract_citations(citation),
            metadata={
                "includes_performance_disclaimer": True,
                "format_version": "2.4.0"
            }
        )
    
    def validate_format(self, formatted_response: FormattedResponse) -> Dict[str, Any]:
        """
        Validate formatted response structure.
        
        Args:
            formatted_response: FormattedResponse to validate
            
        Returns:
            Validation results
        """
        issues = []
        
        # Check required fields
        if not formatted_response.answer:
            issues.append("Missing answer")
        
        if not formatted_response.disclaimer:
            issues.append("Missing disclaimer")
        
        if not formatted_response.query_type:
            issues.append("Missing query type")
        
        # Check format consistency
        if formatted_response.answer and len(formatted_response.answer.strip()) == 0:
            issues.append("Empty answer")
        
        # Check citation format
        if formatted_response.source and formatted_response.source.startswith("http"):
            if not formatted_response.source.startswith(("http://", "https://")):
                issues.append("Invalid citation URL")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "response_type": formatted_response.query_type
        }
    
    def batch_format_responses(self, responses: List[str], citations: List[str], 
                              dates: List[str], query_types: List[str]) -> List[FormattedResponse]:
        """
        Format multiple responses in batch.
        
        Args:
            responses: List of response texts
            citations: List of citations
            dates: List of dates
            query_types: List of query types
            
        Returns:
            List of FormattedResponse objects
        """
        if len(responses) != len(citations) or len(responses) != len(dates) or len(responses) != len(query_types):
            raise ValueError("All input lists must have the same length")
        
        formatted_responses = []
        for response, citation, date, query_type in zip(responses, citations, dates, query_types):
            formatted = self.format_response(response, citation, date, query_type)
            formatted_responses.append(formatted)
        
        return formatted_responses
