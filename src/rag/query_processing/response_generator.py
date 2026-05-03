"""
Response Generation Pipeline for Phase 3

Generates appropriate responses based on query classification and retrieval results.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict

from .query_classifier import QueryClassification, QueryType

logger = logging.getLogger(__name__)

@dataclass
class ResponseContext:
    """Context for response generation."""
    query: str
    classification: QueryClassification
    retrieved_chunks: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    user_context: Optional[Dict[str, Any]]
    session_context: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class GeneratedResponse:
    """Generated response object."""
    query: str
    response_type: str
    content: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_time: float
    metadata: Dict[str, Any]

class ResponseGenerator:
    """
    Generates responses based on query classification and retrieved information.
    
    Features:
    - Type-specific response generation
    - Factual query responses
    - Advisory query handling
    - Performance query responses
    - Procedural query guidance
    - Response confidence scoring
    """
    
    def __init__(self, cache_dir: str = "cache/response_generator"):
        """
        Initialize response generator.
        
        Args:
            cache_dir: Directory for caching response data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Response templates
        self.templates = self._initialize_templates()
        
        # Response statistics
        self.response_stats = defaultdict(int)
        self.response_history: List[GeneratedResponse] = []
        
        # Configuration
        self.max_response_length = 500
        self.confidence_threshold = 0.7
        self.max_sources = 3
        
        # Load existing data
        self._load_templates()
        self._load_stats()
        
        logger.info("Response Generator initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize response templates."""
        return {
            "factual": {
                "direct_answer": "Based on the available information, {answer}.",
                "with_sources": "According to {sources}, {answer}.",
                "detailed": "Here are the details about {topic}: {answer}.",
                "no_data": "I don't have specific information about {topic} in the current data."
            },
            "advisory": {
                "refusal": "I cannot provide investment advice. Please consult a qualified financial advisor.",
                "educational": "For investment guidance, it's best to consult with a qualified financial advisor who can provide personalized recommendations based on your financial situation and goals.",
                "general_info": "Here's some general information about {topic}: {answer}",
                "disclaimer": "This information is for educational purposes only and should not be considered as investment advice."
            },
            "performance": {
                "link_only": "For performance information, please refer to the official factsheet: {source_url}",
                "general": "Performance data is available in the official fund documents: {answer}",
                "no_data": "Performance information is not available in the current data."
            },
            "procedural": {
                "step_by_step": "Here's how to {action}: {steps}",
                "guidance": "To {action}, follow these steps: {steps}",
                "with_sources": "According to {sources}, here's how to {action}: {steps}",
                "no_data": "I don't have specific procedural information for {action}."
            },
            "general": {
                "helpful": "Here's what I can tell you about {topic}: {answer}",
                "no_data": "I don't have specific information about {topic}.",
                "clarification": "Could you please provide more details about {topic}?"
            }
        }
    
    def _load_templates(self) -> None:
        """Load templates from cache."""
        templates_file = self.cache_dir / "templates.json"
        
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    self.templates = json.load(f)
                
                logger.info(f"Loaded response templates")
                
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
    
    def _load_stats(self) -> None:
        """Load response statistics from cache."""
        stats_file = self.cache_dir / "stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                self.response_stats = defaultdict(int, data.get("response_stats", {}))
                
                # Load response history
                history_data = data.get("response_history", [])
                self.response_history = []
                for item in history_data:
                    item['generated_at'] = datetime.fromisoformat(item['generated_at'])
                    self.response_history.append(GeneratedResponse(**item))
                
                logger.info(f"Loaded response statistics")
                
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
    
    def _save_templates(self) -> None:
        """Save templates to cache."""
        try:
            templates_file = self.cache_dir / "templates.json"
            
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
    
    def _save_stats(self) -> None:
        """Save response statistics to cache."""
        try:
            stats_file = self.cache_dir / "stats.json"
            
            serializable_history = []
            for response in self.response_history:
                response_dict = asdict(response)
                response_dict['generated_at'] = response.generated_at.isoformat()
                serializable_history.append(response_dict)
            
            data = {
                "response_stats": dict(self.response_stats),
                "response_history": serializable_history[-1000]  # Keep last 1000
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    async def generate_response(self, context: ResponseContext) -> GeneratedResponse:
        """
        Generate response based on query classification and context.
        
        Args:
            context: Response context with query and retrieved data
            
        Returns:
            GeneratedResponse object
        """
        start_time = datetime.now()
        
        logger.info(f"Generating response for: {context.query[:100]}...")
        
        try:
            # Determine response strategy based on query type
            if context.classification.query_type == QueryType.FACTUAL:
                response = await self._generate_factual_response(context)
            elif context.classification.query_type == QueryType.ADVISORY:
                response = await self._generate_advisory_response(context)
            elif context.classification.query_type == QueryType.PERFORMANCE:
                response = await self._generate_performance_response(context)
            elif context.classification.query_type == QueryType.PROCEDURAL:
                response = await self._generate_procedural_response(context)
            else:
                response = await self._generate_general_response(context)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            response.response_time = response_time
            
            # Update statistics
            self.response_stats[response.response_type] += 1
            self.response_history.append(response)
            
            # Save updated stats
            if len(self.response_history) % 10 == 0:
                self._save_stats()
            
            logger.info(f"Response generated: {response.response_type} (confidence: {response.confidence:.2f})")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            
            # Return error response
            return GeneratedResponse(
                query=context.query,
                response_type="error",
                content="I apologize, but I encountered an error while generating a response. Please try again.",
                sources=[],
                confidence=0.0,
                response_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error": str(e)}
            )
    
    async def _generate_factual_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate response for factual queries."""
        # Extract relevant information from retrieved chunks
        relevant_info = self._extract_relevant_info(context.retrieved_chunks, context.query)
        
        if relevant_info:
            # Generate direct answer
            answer = self._format_factual_answer(relevant_info)
            content = self.templates["factual"]["direct_answer"].format(answer=answer)
            
            # Add sources
            sources = self._extract_sources(context.retrieved_chunks[:self.max_sources])
            
            return GeneratedResponse(
                query=context.query,
                response_type="factual",
                content=content,
                sources=sources,
                confidence=self._calculate_confidence(relevant_info),
                response_time=0.0,  # Will be set by caller
                metadata={
                    "method": "direct_answer",
                    "chunks_used": len(context.retrieved_chunks),
                    "relevant_info_count": len(relevant_info)
                }
            )
        else:
            # No data available
            topic = self._extract_topic(context.query)
            content = self.templates["factual"]["no_data"].format(topic=topic)
            
            return GeneratedResponse(
                query=context.query,
                response_type="factual",
                content=content,
                sources=[],
                confidence=0.3,
                response_time=0.0,
                metadata={
                    "method": "no_data",
                    "chunks_used": 0
                }
            )
    
    async def _generate_advisory_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate response for advisory queries."""
        # For advisory queries, we must refuse to give investment advice
        content = self.templates["advisory"]["refusal"]
        
        # Add educational information if available
        if context.retrieved_chunks:
            educational_info = self._extract_educational_info(context.retrieved_chunks)
            if educational_info:
                topic = self._extract_topic(context.query)
                educational_content = self.templates["advisory"]["general_info"].format(
                    topic=topic, answer=educational_info
                )
                content = f"{content}\n\n{educational_content}"
        
        # Add disclaimer
        disclaimer = self.templates["advisory"]["disclaimer"]
        content = f"{content}\n\n{disclaimer}"
        
        return GeneratedResponse(
            query=context.query,
            response_type="advisory",
            content=content,
            sources=[],
            confidence=1.0,  # High confidence for refusal
            response_time=0.0,
            metadata={
                "method": "refusal_with_education",
                "chunks_used": len(context.retrieved_chunks)
            }
        )
    
    async def _generate_performance_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate response for performance queries."""
        # For performance queries, provide link to official factsheet
        if context.retrieved_chunks:
            # Extract source URLs from chunks
            sources = self._extract_sources(context.retrieved_chunks)
            
            if sources:
                source_url = sources[0].get('source_url', '')
                if source_url:
                    content = self.templates["performance"]["link_only"].format(source_url=source_url)
                    
                    return GeneratedResponse(
                        query=context.query,
                        response_type="performance",
                        content=content,
                        sources=sources,
                        confidence=0.9,
                        response_time=0.0,
                        metadata={
                            "method": "link_only",
                            "chunks_used": len(context.retrieved_chunks)
                        }
                    )
        
        # Fallback to general information
        topic = self._extract_topic(context.query)
        content = self.templates["performance"]["no_data"].format(topic=topic)
        
        return GeneratedResponse(
            query=context.query,
            response_type="performance",
            content=content,
            sources=[],
            confidence=0.5,
            response_time=0.0,
            metadata={
                "method": "no_data",
                "chunks_used": 0
            }
        )
    
    async def _generate_procedural_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate response for procedural queries."""
        # Extract procedural steps from retrieved chunks
        steps = self._extract_procedural_steps(context.retrieved_chunks, context.query)
        
        if steps:
            action = self._extract_action(context.query)
            steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            
            # Choose template
            if context.retrieved_chunks:
                sources = self._extract_sources(context.retrieved_chunks[:self.max_sources])
                source_names = ", ".join([s.get('source_title', 'Source') for s in sources])
                content = self.templates["procedural"]["with_sources"].format(
                    action=action, steps=steps_text, sources=source_names
                )
            else:
                content = self.templates["procedural"]["step_by_step"].format(
                    action=action, steps=steps_text
                )
            
            return GeneratedResponse(
                query=context.query,
                response_type="procedural",
                content=content,
                sources=sources if context.retrieved_chunks else [],
                confidence=self._calculate_confidence(steps),
                response_time=0.0,
                metadata={
                    "method": "step_by_step",
                    "chunks_used": len(context.retrieved_chunks),
                    "steps_count": len(steps)
                }
            )
        else:
            # No procedural information available
            action = self._extract_action(context.query)
            content = self.templates["procedural"]["no_data"].format(action=action)
            
            return GeneratedResponse(
                query=context.query,
                response_type="procedural",
                content=content,
                sources=[],
                confidence=0.3,
                response_time=0.0,
                metadata={
                    "method": "no_data",
                    "chunks_used": 0
                }
            )
    
    async def _generate_general_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate response for general queries."""
        # Try to extract helpful information
        relevant_info = self._extract_relevant_info(context.retrieved_chunks, context.query)
        
        if relevant_info:
            topic = self._extract_topic(context.query)
            answer = self._format_factual_answer(relevant_info)
            content = self.templates["general"]["helpful"].format(topic=topic, answer=answer)
            
            sources = self._extract_sources(context.retrieved_chunks[:self.max_sources])
            
            return GeneratedResponse(
                query=context.query,
                response_type="general",
                content=content,
                sources=sources,
                confidence=self._calculate_confidence(relevant_info),
                response_time=0.0,
                metadata={
                    "method": "helpful_info",
                    "chunks_used": len(context.retrieved_chunks)
                }
            )
        else:
            # No specific information available
            topic = self._extract_topic(context.query)
            content = self.templates["general"]["no_data"].format(topic=topic)
            
            return GeneratedResponse(
                query=context.query,
                response_type="general",
                content=content,
                sources=[],
                confidence=0.3,
                response_time=0.0,
                metadata={
                    "method": "no_data",
                    "chunks_used": 0
                }
            )
    
    def _extract_relevant_info(self, chunks: List[Dict[str, Any]], query: str) -> List[str]:
        """Extract relevant information from chunks."""
        relevant_info = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # Simple keyword matching for relevance
            query_words = query.lower().split()
            content_words = content.lower().split()
            
            # Calculate overlap
            overlap = len(set(query_words) & set(content_words))
            
            # If there's significant overlap, consider it relevant
            if overlap >= 2 or (len(query_words) > 0 and overlap / len(query_words) > 0.3):
                # Extract a meaningful snippet
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20 and any(word in sentence.lower() for word in query_words):
                        relevant_info.append(sentence)
                        if len(relevant_info) >= 3:  # Limit to 3 pieces of info
                            break
        
        return relevant_info
    
    def _extract_educational_info(self, chunks: List[Dict[str, Any]]) -> Optional[str]:
        """Extract educational information from chunks."""
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # Look for educational content patterns
            educational_patterns = [
                "what is", "how does", "types of", "benefits of", "risks of",
                "definition", "meaning", "purpose", "objective"
            ]
            
            if any(pattern in content.lower() for pattern in educational_patterns):
                # Return first meaningful sentence
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 30:
                        return sentence
        
        return None
    
    def _extract_procedural_steps(self, chunks: List[Dict[str, Any]], query: str) -> List[str]:
        """Extract procedural steps from chunks."""
        steps = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # Look for procedural patterns
            procedural_patterns = [
                "step", "how to", "process", "procedure", "follow",
                "first", "second", "third", "then", "next", "finally"
            ]
            
            if any(pattern in content.lower() for pattern in procedural_patterns):
                # Extract numbered or sequential steps
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Check if line looks like a step
                    if (line and 
                        (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                         line.lower().startswith(('step', 'first', 'second', 'third', 'then', 'next')))):
                        steps.append(line)
                        if len(steps) >= 5:  # Limit to 5 steps
                            break
        
        return steps
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from chunks."""
        sources = []
        
        for chunk in chunks:
            source_info = {
                'source_url': chunk.get('source_url', ''),
                'source_title': chunk.get('source_title', ''),
                'fund_name': chunk.get('fund_name', ''),
                'document_type': chunk.get('document_type', ''),
                'content_type': chunk.get('content_type', ''),
                'last_updated': chunk.get('last_updated', '')
            }
            sources.append(source_info)
        
        return sources
    
    def _format_factual_answer(self, relevant_info: List[str]) -> str:
        """Format factual answer from relevant information."""
        if not relevant_info:
            return ""
        
        # Combine relevant information
        if len(relevant_info) == 1:
            return relevant_info[0]
        else:
            # Join multiple pieces of information
            return " ".join(relevant_info[:2])  # Limit to 2 pieces
    
    def _extract_topic(self, query: str) -> str:
        """Extract main topic from query."""
        # Simple topic extraction - in practice, this could be more sophisticated
        words = query.lower().split()
        
        # Remove common words
        stop_words = {'what', 'how', 'when', 'where', 'why', 'is', 'are', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'with', 'by'}
        topic_words = [word for word in words if word not in stop_words]
        
        if topic_words:
            return " ".join(topic_words[:3])  # Return first 3 relevant words
        
        return "the requested information"
    
    def _extract_action(self, query: str) -> str:
        """Extract action from procedural query."""
        # Look for action verbs
        action_patterns = [
            "download", "redeem", "withdraw", "invest", "start", "begin",
            "complete", "get", "obtain", "access", "view", "check", "verify"
        ]
        
        query_lower = query.lower()
        for pattern in action_patterns:
            if pattern in query_lower:
                return pattern
        
        return "perform the requested action"
    
    def _calculate_confidence(self, data: List[str]) -> float:
        """Calculate confidence score based on data quality."""
        if not data:
            return 0.3
        
        # Base confidence on data availability
        confidence = 0.7
        
        # Adjust based on data quality
        if len(data) >= 2:
            confidence += 0.2
        if len(data) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_response_stats(self) -> Dict[str, Any]:
        """
        Get response generation statistics.
        
        Returns:
            Response statistics dictionary
        """
        total_responses = sum(self.response_stats.values())
        
        # Calculate distribution
        distribution = {}
        for response_type, count in self.response_stats.items():
            distribution[response_type] = {
                "count": count,
                "percentage": (count / total_responses * 100) if total_responses > 0 else 0
            }
        
        # Calculate average confidence
        if self.response_history:
            confidences = [r.confidence for r in self.response_history]
            avg_confidence = sum(confidences) / len(confidences)
            avg_response_time = sum(r.response_time for r in self.response_history) / len(self.response_history)
        else:
            avg_confidence = 0.0
            avg_response_time = 0.0
        
        return {
            "total_responses": total_responses,
            "distribution": distribution,
            "average_confidence": avg_confidence,
            "average_response_time": avg_response_time,
            "templates_available": len(self.templates),
            "response_history_size": len(self.response_history)
        }
    
    def get_responses_by_type(self, response_type: str) -> List[GeneratedResponse]:
        """
        Get responses by type.
        
        Args:
            response_type: Response type to filter by
            
        Returns:
            List of GeneratedResponse objects
        """
        return [r for r in self.response_history if r.response_type == response_type]
    
    def add_custom_template(self, response_type: str, template_name: str, template: str) -> None:
        """
        Add a custom response template.
        
        Args:
            response_type: Response type category
            template_name: Template name
            template: Template string with placeholders
        """
        if response_type not in self.templates:
            self.templates[response_type] = {}
        
        self.templates[response_type][template_name] = template
        self._save_templates()
        
        logger.info(f"Added custom template: {response_type}.{template_name}")
    
    def remove_template(self, response_type: str, template_name: str) -> bool:
        """
        Remove a response template.
        
        Args:
            response_type: Response type category
            template_name: Template name to remove
            
        Returns:
            True if template was removed
        """
        if (response_type in self.templates and 
            template_name in self.templates[response_type]):
            del self.templates[response_type][template_name]
            self._save_templates()
            
            logger.info(f"Removed template: {response_type}.{template_name}")
            return True
        
        return False
    
    async def batch_generate_responses(self, contexts: List[ResponseContext]) -> List[GeneratedResponse]:
        """
        Generate responses for multiple contexts.
        
        Args:
            contexts: List of ResponseContext objects
            
        Returns:
            List of GeneratedResponse objects
        """
        responses = []
        
        for context in contexts:
            response = await self.generate_response(context)
            responses.append(response)
        
        return responses
    
    def get_response_suggestions(self, query: str, limit: int = 3) -> List[str]:
        """
        Get response suggestions based on similar queries.
        
        Args:
            query: Query string
            limit: Maximum suggestions to return
            
        Returns:
            List of suggested responses
        """
        suggestions = []
        
        # Find similar queries from history
        for response in self.response_history[-50:]:  # Check recent history
            if query.lower() in response.query.lower():
                suggestions.append(response.content)
                if len(suggestions) >= limit:
                    break
        
        return suggestions[:limit]
    
    def validate_response(self, response: GeneratedResponse) -> bool:
        """
        Validate a generated response.
        
        Args:
            response: GeneratedResponse to validate
            
        Returns:
            True if response is valid
        """
        # Check required fields
        if not response.query or not response.response_type or not response.content:
            return False
        
        # Check confidence range
        if not 0.0 <= response.confidence <= 1.0:
            return False
        
        # Check response time
        if response.response_time < 0:
            return False
        
        # Check content length
        if len(response.content) > self.max_response_length * 2:  # Allow some flexibility
            return False
        
        return True
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old response data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old response history
        old_responses = [
            response for response in self.response_history
            if response.generated_at < cutoff_date
        ]
        
        self.response_history = [
            response for response in self.response_history
            if response.generated_at >= cutoff_date
        ]
        
        # Save updated data
        self._save_stats()
        
        logger.info(f"Cleaned up {len(old_responses)} old response records")
        return len(old_responses)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on response generator.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_response_stats()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "templates_available": stats["templates_available"],
                "total_responses": stats["total_responses"],
                "average_confidence": stats["average_confidence"],
                "average_response_time": stats["average_response_time"],
                "response_stats": dict(stats["distribution"])
            }
        }
        
        # Check if we have enough templates
        if stats["templates_available"] < 5:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient response templates")
        
        # Check if we have enough response data
        if stats["total_responses"] < 10:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient response data")
        
        # Check average confidence
        if stats["average_confidence"] < 0.5:
            health_status["status"] = "degraded"
            health_status["issues"].append("Low average confidence")
        
        return health_status
