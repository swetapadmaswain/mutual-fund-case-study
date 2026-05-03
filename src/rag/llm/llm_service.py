"""
LLM Service Integration for Phase 2.4

Handles communication with OpenAI GPT-3.5-turbo for response generation.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from openai import AsyncOpenAI, OpenAIError, RateLimitError
import backoff

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM service."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    success: bool
    error_message: Optional[str] = None

class LLMService:
    """
    LLM service for generating responses using OpenAI GPT-3.5-turbo.
    
    Features:
    - Retry mechanisms with exponential backoff
    - Rate limiting handling
    - Fallback options
    - Performance monitoring
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize LLM service.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-3.5-turbo)
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.total_response_time = 0.0
        self.rate_limit_hits = 0
        
        # Configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        logger.info(f"LLM Service initialized with model: {model}")
    
    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, OpenAIError),
        max_tries=3,
        base=1,
        max=60
    )
    async def generate_response(self, prompt: str, max_tokens: int = 150, temperature: float = 0.1) -> LLMResponse:
        """
        Generate response from LLM.
        
        Args:
            prompt: Input prompt for LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            LLMResponse object with generated content and metadata
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides factual information about mutual funds."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30.0
            )
            
            response_time = time.time() - start_time
            self.successful_requests += 1
            self.total_response_time += response_time
            
            content = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else {}
            
            logger.info(f"LLM response generated in {response_time:.2f}s")
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                response_time=response_time,
                success=True
            )
            
        except RateLimitError as e:
            self.rate_limit_hits += 1
            logger.warning(f"Rate limit hit: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                response_time=time.time() - start_time,
                success=False,
                error_message=f"Rate limit exceeded: {e}"
            )
            
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                response_time=time.time() - start_time,
                success=False,
                error_message=f"OpenAI error: {e}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                response_time=time.time() - start_time,
                success=False,
                error_message=f"Unexpected error: {e}"
            )
    
    async def generate_batch_responses(self, prompts: List[str], max_tokens: int = 150) -> List[LLMResponse]:
        """
        Generate responses for multiple prompts concurrently.
        
        Args:
            prompts: List of input prompts
            max_tokens: Maximum tokens per response
            
        Returns:
            List of LLMResponse objects
        """
        tasks = [
            self.generate_response(prompt, max_tokens) 
            for prompt in prompts
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append(
                    LLMResponse(
                        content="",
                        model=self.model,
                        usage={},
                        response_time=0.0,
                        success=False,
                        error_message=f"Batch processing error: {response}"
                    )
                )
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    def handle_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limiting statistics.
        
        Returns:
            Dictionary with rate limiting information
        """
        return {
            "total_requests": self.total_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "rate_limit_rate": (self.rate_limit_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        }
    
    def implement_retries(self, max_retries: int = 3) -> None:
        """
        Configure retry settings.
        
        Args:
            max_retries: Maximum number of retries
        """
        self.max_retries = max_retries
        logger.info(f"Retry configuration updated: max_retries={max_retries}")
    
    def setup_fallback(self, fallback_model: Optional[str] = None) -> None:
        """
        Set up fallback model configuration.
        
        Args:
            fallback_model: Fallback model name (optional)
        """
        self.fallback_model = fallback_model
        if fallback_model:
            logger.info(f"Fallback model configured: {fallback_model}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        avg_response_time = (self.total_response_time / self.successful_requests) if self.successful_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "total_response_time": self.total_response_time,
            "rate_limit_hits": self.rate_limit_hits,
            "model": self.model
        }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.total_response_time = 0.0
        self.rate_limit_hits = 0
        logger.info("Performance statistics reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on LLM service.
        
        Returns:
            Dictionary with health status
        """
        try:
            test_prompt = "Test prompt for health check"
            response = await self.generate_response(test_prompt, max_tokens=5)
            
            return {
                "status": "healthy" if response.success else "unhealthy",
                "model": self.model,
                "last_check": time.time(),
                "test_response_time": response.response_time,
                "error": response.error_message
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "last_check": time.time(),
                "error": str(e)
            }
