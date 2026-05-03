"""
Prompt Engineering System for Phase 2.4

Designs and manages prompts for facts-only responses with compliance constraints.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """Template for structured prompts."""
    name: str
    system_prompt: str
    user_prompt_template: str
    constraints: List[str]
    max_sentences: int = 3
    temperature: float = 0.1

class PromptEngine:
    """
    Prompt engineering system for facts-only mutual fund responses.
    
    Features:
    - Facts-only prompt design
    - Response length constraints
    - Citation requirements
    - Compliance instructions
    - Query-type specific prompts
    """
    
    def __init__(self):
        """Initialize prompt engine with templates."""
        self.templates = self._initialize_templates()
        self.compliance_rules = self._initialize_compliance_rules()
        self.length_constraints = self._initialize_length_constraints()
        
        logger.info("Prompt Engine initialized with facts-only templates")
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates for different query types."""
        return {
            "factual": PromptTemplate(
                name="factual",
                system_prompt="You are a factual information assistant for HDFC mutual funds. Provide only factual information based on the given context. Do not give investment advice.",
                user_prompt_template="""Based on the following context, answer the question factually and concisely.

Context: {context}

Question: {query}

Provide a factual answer in maximum {max_sentences} sentences. Include only information from the context.""",
                constraints=[
                    "Only factual information",
                    "No investment advice",
                    "Maximum 3 sentences",
                    "Based on context only"
                ]
            ),
            
            "advisory": PromptTemplate(
                name="advisory",
                system_prompt="You are a factual information assistant. Do not provide investment advice. Politely decline advisory questions and provide educational information.",
                user_prompt_template="""The user is asking for investment advice: {query}

Politely decline to provide investment advice. Instead:
1. State that you cannot provide investment advice
2. Provide factual information about the topic if available in context
3. Suggest consulting a financial advisor

Context: {context}

Response in maximum {max_sentences} sentences.""",
                constraints=[
                    "No investment advice",
                    "Polite refusal",
                    "Educational information only",
                    "Suggest professional advisor"
                ]
            ),
            
            "performance": PromptTemplate(
                name="performance",
                system_prompt="You are a factual information assistant for mutual fund performance. Provide only factual performance data from official sources.",
                user_prompt_template="""Based on the following context, provide factual performance information.

Context: {context}

Question: {query}

Provide factual performance data in maximum {max_sentences} sentences. If specific performance data is not available, state that and direct to official factsheet.""",
                constraints=[
                    "Only factual performance data",
                    "No future predictions",
                    "Direct to official sources",
                    "Maximum 3 sentences"
                ]
            ),
            
            "procedural": PromptTemplate(
                name="procedural",
                system_prompt="You are a procedural information assistant. Provide step-by-step guidance for mutual fund procedures.",
                user_prompt_template="""Based on the following context, provide step-by-step guidance.

Context: {context}

Question: {query}

Provide procedural guidance in maximum {max_sentences} sentences. Include only factual steps from official sources.""",
                constraints=[
                    "Step-by-step guidance",
                    "Factual procedures only",
                    "Official source information",
                    "Maximum 3 sentences"
                ]
            ),
            
            "general": PromptTemplate(
                name="general",
                system_prompt="You are a factual information assistant for HDFC mutual funds. Provide helpful but factual information.",
                user_prompt_template="""Based on the following context, answer the question factually.

Context: {context}

Question: {query}

Provide a helpful factual answer in maximum {max_sentences} sentences.""",
                constraints=[
                    "Factual information only",
                    "Helpful but not advisory",
                    "Maximum 3 sentences",
                    "Based on context"
                ]
            )
        }
    
    def _initialize_compliance_rules(self) -> Dict[str, List[str]]:
        """Initialize compliance rules for different query types."""
        return {
            "factual": [
                "Do not provide investment advice",
                "Do not predict future performance",
                "Do not recommend specific funds",
                "Do not suggest buying/selling"
            ],
            "advisory": [
                "Must refuse to provide advice",
                "Must suggest professional advisor",
                "Can provide educational information",
                "Must be polite but firm"
            ],
            "performance": [
                "Only provide historical data",
                "Do not predict future returns",
                "Include disclaimers about past performance",
                "Direct to official sources"
            ],
            "procedural": [
                "Provide official procedures only",
                "Do not suggest shortcuts",
                "Include official source references",
                "Be accurate and step-by-step"
            ],
            "general": [
                "No investment advice",
                "No recommendations",
                "Factual information only",
                "Helpful but conservative"
            ]
        }
    
    def _initialize_length_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Initialize length constraints for different query types."""
        return {
            "factual": {
                "max_sentences": 3,
                "max_words": 50,
                "max_characters": 300
            },
            "advisory": {
                "max_sentences": 3,
                "max_words": 50,
                "max_characters": 300
            },
            "performance": {
                "max_sentences": 3,
                "max_words": 50,
                "max_characters": 300
            },
            "procedural": {
                "max_sentences": 4,
                "max_words": 60,
                "max_characters": 350
            },
            "general": {
                "max_sentences": 3,
                "max_words": 50,
                "max_characters": 300
            }
        }
    
    def create_factual_prompt(self, context: str, query: str, query_type: str = "factual") -> str:
        """
        Create a facts-only prompt for the given context and query.
        
        Args:
            context: Retrieved context from search
            query: User query
            query_type: Type of query (factual, advisory, performance, procedural, general)
            
        Returns:
            Formatted prompt string
        """
        template = self.templates.get(query_type, self.templates["general"])
        
        # Apply length constraints
        constraints = self.length_constraints.get(query_type, self.length_constraints["general"])
        max_sentences = constraints["max_sentences"]
        
        # Format the prompt
        user_prompt = template.user_prompt_template.format(
            context=context,
            query=query,
            max_sentences=max_sentences
        )
        
        # Add compliance instructions
        compliance_text = self._get_compliance_instructions(query_type)
        
        full_prompt = f"{template.system_prompt}\n\n{compliance_text}\n\n{user_prompt}"
        
        logger.debug(f"Created {query_type} prompt with {len(full_prompt)} characters")
        
        return full_prompt
    
    def enforce_length_limit(self, prompt: str, max_sentences: int = 3) -> str:
        """
        Enforce length limit on prompt.
        
        Args:
            prompt: Input prompt
            max_sentences: Maximum number of sentences
            
        Returns:
            Length-limited prompt
        """
        # Count sentences
        sentences = re.split(r'[.!?]+', prompt)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return prompt
        
        # Truncate to max sentences
        limited_prompt = '. '.join(sentences[:max_sentences]) + '.'
        
        logger.info(f"Prompt truncated from {len(sentences)} to {max_sentences} sentences")
        
        return limited_prompt
    
    def require_citations(self, prompt: str) -> str:
        """
        Add citation requirements to prompt.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Prompt with citation requirements
        """
        citation_instruction = """
IMPORTANT: Your response must be based only on the provided context. 
Do not include information from outside sources. 
If the context doesn't contain the answer, state that clearly.
"""
        
        return f"{prompt}\n{citation_instruction}"
    
    def add_compliance_instructions(self, prompt: str, query_type: str = "factual") -> str:
        """
        Add compliance instructions to prompt.
        
        Args:
            prompt: Input prompt
            query_type: Type of query
            
        Returns:
            Prompt with compliance instructions
        """
        compliance_rules = self.compliance_rules.get(query_type, self.compliance_rules["general"])
        
        compliance_text = "COMPLIANCE REQUIREMENTS:\n"
        for i, rule in enumerate(compliance_rules, 1):
            compliance_text += f"{i}. {rule}\n"
        
        return f"{prompt}\n\n{compliance_text}"
    
    def _get_compliance_instructions(self, query_type: str) -> str:
        """Get compliance instructions for query type."""
        rules = self.compliance_rules.get(query_type, self.compliance_rules["general"])
        
        instructions = "COMPLIANCE REQUIREMENTS:\n"
        for i, rule in enumerate(rules, 1):
            instructions += f"{i}. {rule}\n"
        
        return instructions
    
    def create_advisory_refusal_prompt(self, query: str) -> str:
        """
        Create prompt for advisory query refusal.
        
        Args:
            query: User query asking for advice
            
        Returns:
            Formatted refusal prompt
        """
        template = self.templates["advisory"]
        
        user_prompt = template.user_prompt_template.format(
            context="",
            query=query,
            max_sentences=template.max_sentences
        )
        
        return f"{template.system_prompt}\n\n{user_prompt}"
    
    def create_performance_disclaimer_prompt(self, context: str, query: str) -> str:
        """
        Create prompt for performance queries with disclaimers.
        
        Args:
            context: Retrieved context
            query: User query about performance
            
        Returns:
            Prompt with performance disclaimers
        """
        template = self.templates["performance"]
        
        disclaimer = """
DISCLAIMER: Past performance does not guarantee future results. 
Performance data is for informational purposes only.
"""
        
        user_prompt = template.user_prompt_template.format(
            context=context,
            query=query,
            max_sentences=template.max_sentences
        )
        
        return f"{template.system_prompt}\n{disclaimer}\n\n{user_prompt}"
    
    def validate_prompt(self, prompt: str, query_type: str) -> Dict[str, Any]:
        """
        Validate prompt for compliance and constraints.
        
        Args:
            prompt: Prompt to validate
            query_type: Type of query
            
        Returns:
            Validation results
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # Check length
        constraints = self.length_constraints.get(query_type, self.length_constraints["general"])
        sentences = re.split(r'[.!?]+', prompt)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > constraints["max_sentences"]:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Too many sentences: {len(sentences)} > {constraints['max_sentences']}")
            validation_result["suggestions"].append(f"Reduce to {constraints['max_sentences']} sentences")
        
        # Check for prohibited content
        prohibited_phrases = ["I recommend", "you should", "best fund", "guaranteed return"]
        for phrase in prohibited_phrases:
            if phrase.lower() in prompt.lower():
                validation_result["valid"] = False
                validation_result["issues"].append(f"Prohibited phrase found: {phrase}")
                validation_result["suggestions"].append("Remove investment advice language")
        
        return validation_result
    
    def get_template_info(self, query_type: str) -> Dict[str, Any]:
        """
        Get information about a specific template.
        
        Args:
            query_type: Type of query
            
        Returns:
            Template information
        """
        template = self.templates.get(query_type)
        if not template:
            return {"error": f"Template not found for query type: {query_type}"}
        
        return {
            "name": template.name,
            "constraints": template.constraints,
            "max_sentences": template.max_sentences,
            "temperature": template.temperature,
            "compliance_rules": self.compliance_rules.get(query_type, []),
            "length_constraints": self.length_constraints.get(query_type, {})
        }
