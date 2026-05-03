"""
Response Formatting System for Phase 3

Formats responses for different output types and ensures consistent presentation.
"""

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from enum import Enum

from .response_generator import GeneratedResponse

logger = logging.getLogger(__name__)

class OutputFormat(Enum):
    """Output format enumeration."""
    JSON = "json"
    UI = "ui"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"

@dataclass
class FormattedResponse:
    """Formatted response object."""
    original_response: GeneratedResponse
    output_format: OutputFormat
    formatted_content: str
    metadata: Dict[str, Any]
    timestamp: datetime

class ResponseFormatter:
    """
    Formats responses for different output types and ensures consistent presentation.
    
    Features:
    - Multiple output formats (JSON, UI, Text, Markdown, HTML)
    - Consistent citation formatting
    - Response validation
    - Template-based formatting
    - Custom format support
    """
    
    def __init__(self, cache_dir: str = "cache/response_formatter"):
        """
        Initialize response formatter.
        
        Args:
            cache_dir: Directory for caching formatting data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Formatting templates
        self.templates = self._initialize_templates()
        
        # Formatting statistics
        self.formatting_stats = {}
        self.format_history: List[FormattedResponse] = []
        
        # Configuration
        self.max_content_length = 1000
        self.default_format = OutputFormat.JSON
        
        # Load existing data
        self._load_templates()
        self._load_stats()
        
        logger.info("Response Formatter initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize formatting templates."""
        return {
            "ui": {
                "factual": {
                    "template": "Answer: {content}\n\nSources: {sources}\n\nConfidence: {confidence:.1%}",
                    "source_format": "• {source_title} ({source_url})"
                },
                "advisory": {
                    "template": "Response: {content}\n\n⚠️ Disclaimer: This is not investment advice.",
                    "source_format": ""
                },
                "performance": {
                    "template": "Information: {content}\n\nSource: {sources}",
                    "source_format": "Official Factsheet: {source_url}"
                },
                "procedural": {
                    "template": "Instructions: {content}\n\nSources: {sources}",
                    "source_format": "• {source_title}"
                },
                "general": {
                    "template": "Information: {content}\n\nSources: {sources}",
                    "source_format": "• {source_title}"
                }
            },
            "text": {
                "factual": {
                    "template": "Answer: {content}\n\nSources: {sources}\nConfidence: {confidence:.1%}",
                    "source_format": "- {source_title} ({source_url})"
                },
                "advisory": {
                    "template": "Response: {content}\n\nDisclaimer: This is not investment advice.",
                    "source_format": ""
                },
                "performance": {
                    "template": "Information: {content}\n\nSource: {sources}",
                    "source_format": "Official Factsheet: {source_url}"
                },
                "procedural": {
                    "template": "Instructions: {content}\n\nSources: {sources}",
                    "source_format": "- {source_title}"
                },
                "general": {
                    "template": "Information: {content}\n\nSources: {sources}",
                    "source_format": "- {source_title}"
                }
            },
            "markdown": {
                "factual": {
                    "template": "## Answer\n{content}\n\n### Sources\n{sources}\n\n**Confidence:** {confidence:.1%}",
                    "source_format": "- [{source_title}]({source_url})"
                },
                "advisory": {
                    "template": "## Response\n{content}\n\n> ⚠️ **Disclaimer:** This is not investment advice.",
                    "source_format": ""
                },
                "performance": {
                    "template": "## Information\n{content}\n\n### Source\n{sources}",
                    "source_format": "[Official Factsheet]({source_url})"
                },
                "procedural": {
                    "template": "## Instructions\n{content}\n\n### Sources\n{sources}",
                    "source_format": "- [{source_title}]({source_url})"
                },
                "general": {
                    "template": "## Information\n{content}\n\n### Sources\n{sources}",
                    "source_format": "- [{source_title}]({source_url})"
                }
            },
            "html": {
                "factual": {
                    "template": "<div class='response'><div class='answer'><h3>Answer</h3><p>{content}</p></div><div class='sources'><h4>Sources</h4><ul>{sources}</ul></div><div class='confidence'><strong>Confidence:</strong> {confidence:.1%}</div></div>",
                    "source_format": "<li><a href='{source_url}'>{source_title}</a></li>"
                },
                "advisory": {
                    "template": "<div class='response'><div class='answer'><h3>Response</h3><p>{content}</p></div><div class='disclaimer'><p>⚠️ <strong>Disclaimer:</strong> This is not investment advice.</p></div></div>",
                    "source_format": ""
                },
                "performance": {
                    "template": "<div class='response'><div class='answer'><h3>Information</h3><p>{content}</p></div><div class='sources'><h4>Source</h4><ul>{sources}</ul></div></div>",
                    "source_format": "<li><a href='{source_url}'>Official Factsheet</a></li>"
                },
                "procedural": {
                    "template": "<div class='response'><div class='answer'><h3>Instructions</h3><p>{content}</p></div><div class='sources'><h4>Sources</h4><ul>{sources}</ul></div></div>",
                    "source_format": "<li><a href='{source_url}'>{source_title}</a></li>"
                },
                "general": {
                    "template": "<div class='response'><div class='answer'><h3>Information</h3><p>{content}</p></div><div class='sources'><h4>Sources</h4><ul>{sources}</ul></div></div>",
                    "source_format": "<li><a href='{source_url}'>{source_title}</a></li>"
                }
            }
        }
    
    def _load_templates(self) -> None:
        """Load templates from cache."""
        templates_file = self.cache_dir / "templates.json"
        
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    self.templates = json.load(f)
                
                logger.info(f"Loaded formatting templates")
                
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
    
    def _load_stats(self) -> None:
        """Load formatting statistics from cache."""
        stats_file = self.cache_dir / "stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                self.formatting_stats = data.get("formatting_stats", {})
                
                # Load format history
                history_data = data.get("format_history", [])
                self.format_history = []
                for item in history_data:
                    item['output_format'] = OutputFormat(item['output_format'])
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    self.format_history.append(FormattedResponse(**item))
                
                logger.info(f"Loaded formatting statistics")
                
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
        """Save formatting statistics to cache."""
        try:
            stats_file = self.cache_dir / "stats.json"
            
            serializable_history = []
            for formatted in self.format_history:
                formatted_dict = asdict(formatted)
                formatted_dict['output_format'] = formatted.output_format.value
                formatted_dict['timestamp'] = formatted.timestamp.isoformat()
                serializable_history.append(formatted_dict)
            
            data = {
                "formatting_stats": self.formatting_stats,
                "format_history": serializable_history[-1000]  # Keep last 1000
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def format_response(self, response: GeneratedResponse, output_format: Union[str, OutputFormat] = None) -> FormattedResponse:
        """
        Format a response according to specified output format.
        
        Args:
            response: GeneratedResponse object to format
            output_format: Output format (string or enum)
            
        Returns:
            FormattedResponse object
        """
        # Convert string format to enum if needed
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format.lower())
            except ValueError:
                output_format = self.default_format
        elif output_format is None:
            output_format = self.default_format
        
        logger.info(f"Formatting response as: {output_format.value}")
        
        try:
            # Format based on output type
            if output_format == OutputFormat.JSON:
                formatted_content = self._format_as_json(response)
            elif output_format == OutputFormat.UI:
                formatted_content = self._format_as_ui(response)
            elif output_format == OutputFormat.TEXT:
                formatted_content = self._format_as_text(response)
            elif output_format == OutputFormat.MARKDOWN:
                formatted_content = self._format_as_markdown(response)
            elif output_format == OutputFormat.HTML:
                formatted_content = self._format_as_html(response)
            else:
                formatted_content = self._format_as_json(response)
                output_format = OutputFormat.JSON
            
            # Create formatted response
            formatted_response = FormattedResponse(
                original_response=response,
                output_format=output_format,
                formatted_content=formatted_content,
                metadata={
                    "content_length": len(formatted_content),
                    "sources_count": len(response.sources),
                    "formatting_time": datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )
            
            # Update statistics
            format_key = output_format.value
            self.formatting_stats[format_key] = self.formatting_stats.get(format_key, 0) + 1
            self.format_history.append(formatted_response)
            
            # Save updated stats
            if len(self.format_history) % 10 == 0:
                self._save_stats()
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            
            # Return error response
            error_response = FormattedResponse(
                original_response=response,
                output_format=OutputFormat.JSON,
                formatted_content=json.dumps({
                    "error": "Formatting error",
                    "message": str(e),
                    "original_content": response.content
                }),
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
            
            return error_response
    
    def _format_as_json(self, response: GeneratedResponse) -> str:
        """Format response as JSON."""
        sources = []
        for source in response.sources:
            sources.append({
                "source_url": source.get('source_url', ''),
                "source_title": source.get('source_title', ''),
                "fund_name": source.get('fund_name', ''),
                "document_type": source.get('document_type', ''),
                "content_type": source.get('content_type', ''),
                "last_updated": source.get('last_updated', '')
            })
        
        json_response = {
            "query": response.query,
            "response_type": response.response_type,
            "content": response.content,
            "sources": sources,
            "confidence": response.confidence,
            "response_time": response.response_time,
            "metadata": response.metadata
        }
        
        return json.dumps(json_response, indent=2)
    
    def _format_as_ui(self, response: GeneratedResponse) -> str:
        """Format response for UI display."""
        # Get template for response type
        templates = self.templates.get("ui", {})
        template_info = templates.get(response.response_type, templates.get("general", {}))
        
        template = template_info.get("template", "{content}")
        source_format = template_info.get("source_format", "• {source_title}")
        
        # Format sources
        sources_text = ""
        if response.sources:
            sources = []
            for source in response.sources[:3]:  # Limit to 3 sources
                source_title = source.get('source_title', 'Source')
                sources.append(source_format.format(
                    source_title=source_title,
                    source_url=source.get('source_url', ''),
                    fund_name=source.get('fund_name', ''),
                    document_type=source.get('document_type', ''),
                    content_type=source.get('content_type', ''),
                    last_updated=source.get('last_updated', '')
                ))
            sources_text = "\n".join(sources)
        
        # Format response
        formatted = template.format(
            content=response.content,
            sources=sources_text,
            confidence=response.confidence,
            response_time=response.response_time
        )
        
        return formatted
    
    def _format_as_text(self, response: GeneratedResponse) -> str:
        """Format response as plain text."""
        # Get template for response type
        templates = self.templates.get("text", {})
        template_info = templates.get(response.response_type, templates.get("general", {}))
        
        template = template_info.get("template", "{content}")
        source_format = template_info.get("source_format", "- {source_title}")
        
        # Format sources
        sources_text = ""
        if response.sources:
            sources = []
            for source in response.sources[:3]:  # Limit to 3 sources
                source_title = source.get('source_title', 'Source')
                sources.append(source_format.format(
                    source_title=source_title,
                    source_url=source.get('source_url', ''),
                    fund_name=source.get('fund_name', ''),
                    document_type=source.get('document_type', ''),
                    content_type=source.get('content_type', ''),
                    last_updated=source.get('last_updated', '')
                ))
            sources_text = "\n".join(sources)
        
        # Format response
        formatted = template.format(
            content=response.content,
            sources=sources_text,
            confidence=response.confidence,
            response_time=response.response_time
        )
        
        return formatted
    
    def _format_as_markdown(self, response: GeneratedResponse) -> str:
        """Format response as Markdown."""
        # Get template for response type
        templates = self.templates.get("markdown", {})
        template_info = templates.get(response.response_type, templates.get("general", {}))
        
        template = template_info.get("template", "## Information\n{content}")
        source_format = template_info.get("source_format", "- [{source_title}]({source_url})")
        
        # Format sources
        sources_text = ""
        if response.sources:
            sources = []
            for source in response.sources[:3]:  # Limit to 3 sources
                source_title = source.get('source_title', 'Source')
                sources.append(source_format.format(
                    source_title=source_title,
                    source_url=source.get('source_url', ''),
                    fund_name=source.get('fund_name', ''),
                    document_type=source.get('document_type', ''),
                    content_type=source.get('content_type', ''),
                    last_updated=source.get('last_updated', '')
                ))
            sources_text = "\n".join(sources)
        
        # Format response
        formatted = template.format(
            content=response.content,
            sources=sources_text,
            confidence=response.confidence,
            response_time=response.response_time
        )
        
        return formatted
    
    def _format_as_html(self, response: GeneratedResponse) -> str:
        """Format response as HTML."""
        # Get template for response type
        templates = self.templates.get("html", {})
        template_info = templates.get(response.response_type, templates.get("general", {}))
        
        template = template_info.get("template", "<div class='response'><p>{content}</p></div>")
        source_format = template_info.get("source_format", "<li><a href='{source_url}'>{source_title}</a></li>")
        
        # Format sources
        sources_text = ""
        if response.sources:
            sources = []
            for source in response.sources[:3]:  # Limit to 3 sources
                source_title = source.get('source_title', 'Source')
                sources.append(source_format.format(
                    source_title=source_title,
                    source_url=source.get('source_url', ''),
                    fund_name=source.get('fund_name', ''),
                    document_type=source.get('document_type', ''),
                    content_type=source.get('content_type', ''),
                    last_updated=source.get('last_updated', '')
                ))
            sources_text = "".join(sources)
        
        # Format response
        formatted = template.format(
            content=response.content,
            sources=sources_text,
            confidence=response.confidence,
            response_time=response.response_time
        )
        
        return formatted
    
    def format_multiple_responses(self, responses: List[GeneratedResponse], 
                                output_format: Union[str, OutputFormat] = None) -> List[FormattedResponse]:
        """
        Format multiple responses.
        
        Args:
            responses: List of GeneratedResponse objects
            output_format: Output format for all responses
            
        Returns:
            List of FormattedResponse objects
        """
        formatted_responses = []
        
        for response in responses:
            formatted = self.format_response(response, output_format)
            formatted_responses.append(formatted)
        
        return formatted_responses
    
    def get_formatting_stats(self) -> Dict[str, Any]:
        """
        Get formatting statistics.
        
        Returns:
            Formatting statistics dictionary
        """
        total_formatted = sum(self.formatting_stats.values())
        
        # Calculate distribution
        distribution = {}
        for format_type, count in self.formatting_stats.items():
            distribution[format_type] = {
                "count": count,
                "percentage": (count / total_formatted * 100) if total_formatted > 0 else 0
            }
        
        # Calculate average content length
        if self.format_history:
            content_lengths = [f.metadata.get("content_length", 0) for f in self.format_history]
            avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            avg_sources_count = sum(f.original_response.sources for f in self.format_history) / len(self.format_history)
        else:
            avg_content_length = 0
            avg_sources_count = 0
        
        return {
            "total_formatted": total_formatted,
            "distribution": distribution,
            "average_content_length": avg_content_length,
            "average_sources_count": avg_sources_count,
            "formats_available": len(self.templates),
            "format_history_size": len(self.format_history)
        }
    
    def get_formatted_responses_by_format(self, output_format: Union[str, OutputFormat]) -> List[FormattedResponse]:
        """
        Get formatted responses by format type.
        
        Args:
            output_format: Output format to filter by
            
        Returns:
            List of FormattedResponse objects
        """
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format.lower())
            except ValueError:
                return []
        
        return [f for f in self.format_history if f.output_format == output_format]
    
    def add_custom_template(self, output_format: str, response_type: str, 
                           template_name: str, template: str, source_format: str = "") -> None:
        """
        Add a custom formatting template.
        
        Args:
            output_format: Output format category
            response_type: Response type
            template_name: Template name
            template: Template string with placeholders
            source_format: Source formatting string
        """
        if output_format not in self.templates:
            self.templates[output_format] = {}
        
        if response_type not in self.templates[output_format]:
            self.templates[output_format][response_type] = {}
        
        self.templates[output_format][response_type][template_name] = {
            "template": template,
            "source_format": source_format
        }
        
        self._save_templates()
        
        logger.info(f"Added custom template: {output_format}.{response_type}.{template_name}")
    
    def remove_template(self, output_format: str, response_type: str, 
                        template_name: str) -> bool:
        """
        Remove a formatting template.
        
        Args:
            output_format: Output format category
            response_type: Response type
            template_name: Template name to remove
            
        Returns:
            True if template was removed
        """
        if (output_format in self.templates and 
            response_type in self.templates[output_format] and
            template_name in self.templates[output_format][response_type]):
            del self.templates[output_format][response_type][template_name]
            self._save_templates()
            
            logger.info(f"Removed template: {output_format}.{response_type}.{template_name}")
            return True
        
        return False
    
    def validate_formatted_response(self, formatted_response: FormattedResponse) -> bool:
        """
        Validate a formatted response.
        
        Args:
            formatted_response: FormattedResponse to validate
            
        Returns:
            True if formatted response is valid
        """
        # Check required fields
        if not formatted_response.original_response or not formatted_response.output_format:
            return False
        
        # Check formatted content
        if not formatted_response.formatted_content:
            return False
        
        # Check content length
        if len(formatted_response.formatted_content) > self.max_content_length * 2:
            return False
        
        return True
    
    def get_template_for_response(self, response: GeneratedResponse, 
                                  output_format: Union[str, OutputFormat]) -> Dict[str, str]:
        """
        Get the template used for a specific response and format.
        
        Args:
            response: GeneratedResponse object
            output_format: Output format
            
        Returns:
            Template dictionary
        """
        if isinstance(output_format, str):
            try:
                output_format = OutputFormat(output_format.lower())
            except ValueError:
                output_format = self.default_format
        
        templates = self.templates.get(output_format.value, {})
        template_info = templates.get(response.response_type, templates.get("general", {}))
        
        return template_info
    
    def preview_format(self, response: GeneratedResponse, output_format: Union[str, OutputFormat]) -> str:
        """
        Preview how a response would be formatted without saving it.
        
        Args:
            response: GeneratedResponse object
            output_format: Output format to preview
            
        Returns:
            Formatted content string
        """
        # Temporarily format without saving to history
        original_history = self.format_history.copy()
        original_stats = self.formatting_stats.copy()
        
        try:
            formatted = self.format_response(response, output_format)
            return formatted.formatted_content
        finally:
            # Restore original state
            self.format_history = original_history
            self.formatting_stats = original_stats
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old formatting data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old format history
        old_formatted = [
            formatted for formatted in self.format_history
            if formatted.timestamp < cutoff_date
        ]
        
        self.format_history = [
            formatted for formatted in self.format_history
            if formatted.timestamp >= cutoff_date
        ]
        
        # Save updated data
        self._save_stats()
        
        logger.info(f"Cleaned up {len(old_formatted)} old formatted responses")
        return len(old_formatted)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on response formatter.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_formatting_stats()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "formats_available": stats["formats_available"],
                "total_formatted": stats["total_formatted"],
                "average_content_length": stats["average_content_length"],
                "formatting_stats": dict(stats["distribution"])
            }
        }
        
        # Check if we have enough formats
        if stats["formats_available"] < 3:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient output formats")
        
        # Check if we have enough formatting data
        if stats["total_formatted"] < 10:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient formatting data")
        
        return health_status
