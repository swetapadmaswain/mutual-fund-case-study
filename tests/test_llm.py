"""
Comprehensive tests for Phase 2.4: LLM Integration and Prompt Engineering
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rag.llm.llm_service import LLMService, LLMResponse
from src.rag.llm.prompt_engine import PromptEngine
from src.rag.llm.response_validator import ResponseValidator, ValidationResult
from src.rag.llm.response_formatter import ResponseFormatter, FormattedResponse
from src.rag.llm.main import Phase24Pipeline, Phase24Results


class TestLLMService:
    """Test LLM Service functionality."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance for testing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            return LLMService(api_key='test_key')
    
    @pytest.mark.asyncio
    async def test_llm_service_initialization(self, llm_service):
        """Test LLM service initialization."""
        assert llm_service.api_key == 'test_key'
        assert llm_service.model == 'gpt-3.5-turbo'
        assert llm_service.max_retries == 3
        assert llm_service.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service):
        """Test successful response generation."""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = Mock()
        mock_response.usage.model_dump.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        
        with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            response = await llm_service.generate_response("Test prompt")
            
            assert response.success is True
            assert response.content == "Test response"
            assert response.model == 'gpt-3.5-turbo'
            assert response.response_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_failure(self, llm_service):
        """Test response generation failure."""
        with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            response = await llm_service.generate_response("Test prompt")
            
            assert response.success is False
            assert response.content == ""
            assert "API Error" in response.error_message
    
    @pytest.mark.asyncio
    async def test_batch_responses(self, llm_service):
        """Test batch response generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Batch response"
        mock_response.usage = Mock()
        mock_response.usage.model_dump.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        
        with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            responses = await llm_service.generate_batch_responses(["Prompt 1", "Prompt 2"])
            
            assert len(responses) == 2
            assert all(r.success for r in responses)
    
    def test_performance_stats(self, llm_service):
        """Test performance statistics."""
        # Simulate some requests
        llm_service.total_requests = 10
        llm_service.successful_requests = 8
        llm_service.total_response_time = 5.0
        
        stats = llm_service.get_performance_stats()
        
        assert stats["total_requests"] == 10
        assert stats["successful_requests"] == 8
        assert stats["success_rate"] == 80.0
        assert stats["average_response_time"] == 0.625
    
    @pytest.mark.asyncio
    async def test_health_check(self, llm_service):
        """Test health check functionality."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Health check"
        mock_response.usage = Mock()
        mock_response.usage.model_dump.return_value = {"prompt_tokens": 5, "completion_tokens": 2}
        
        with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            health = await llm_service.health_check()
            
            assert health["status"] == "healthy"
            assert health["model"] == 'gpt-3.5-turbo'


class TestPromptEngine:
    """Test Prompt Engine functionality."""
    
    @pytest.fixture
    def prompt_engine(self):
        """Create prompt engine instance for testing."""
        return PromptEngine()
    
    def test_initialization(self, prompt_engine):
        """Test prompt engine initialization."""
        assert len(prompt_engine.templates) == 5
        assert "factual" in prompt_engine.templates
        assert "advisory" in prompt_engine.templates
        assert len(prompt_engine.compliance_rules) == 5
        assert len(prompt_engine.length_constraints) == 5
    
    def test_create_factual_prompt(self, prompt_engine):
        """Test factual prompt creation."""
        context = "HDFC Mid Cap Fund has expense ratio of 0.85%"
        query = "What is the expense ratio?"
        
        prompt = prompt_engine.create_factual_prompt(context, query, "factual")
        
        assert context in prompt
        assert query in prompt
        assert "factual information" in prompt.lower()
        assert "maximum 3 sentences" in prompt
    
    def test_create_advisory_prompt(self, prompt_engine):
        """Test advisory prompt creation."""
        query = "Should I invest in HDFC Mid Cap Fund?"
        
        prompt = prompt_engine.create_factual_prompt("", query, "advisory")
        
        assert query in prompt
        assert "cannot provide investment advice" in prompt.lower()
        assert "financial advisor" in prompt.lower()
    
    def test_enforce_length_limit(self, prompt_engine):
        """Test length limit enforcement."""
        long_prompt = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5."
        
        limited = prompt_engine.enforce_length_limit(long_prompt, 3)
        
        sentences = limited.split('.')
        assert len([s.strip() for s in sentences if s.strip()]) <= 3
    
    def test_require_citations(self, prompt_engine):
        """Test citation requirement addition."""
        prompt = "Test prompt"
        
        with_citations = prompt_engine.require_citations(prompt)
        
        assert "based only on the provided context" in with_citations.lower()
    
    def test_validate_prompt(self, prompt_engine):
        """Test prompt validation."""
        # Valid prompt
        valid_prompt = "Short response. Two sentences."
        result = prompt_engine.validate_prompt(valid_prompt, "factual")
        assert result["valid"] is True
        
        # Invalid prompt (too long)
        long_prompt = ". ".join([f"Sentence {i}" for i in range(10)]) + "."
        result = prompt_engine.validate_prompt(long_prompt, "factual")
        assert result["valid"] is False
        assert "Too many sentences" in result["issues"][0]
    
    def test_get_template_info(self, prompt_engine):
        """Test template information retrieval."""
        info = prompt_engine.get_template_info("factual")
        
        assert info["name"] == "factual"
        assert "constraints" in info
        assert "max_sentences" in info
        assert info["max_sentences"] == 3


class TestResponseValidator:
    """Test Response Validator functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create response validator instance for testing."""
        return ResponseValidator()
    
    def test_initialization(self, validator):
        """Test validator initialization."""
        assert len(validator.advisory_patterns) > 0
        assert len(validator.compliance_patterns) > 0
        assert len(validator.length_limits) == 5
        assert "compliance" in validator.scoring_weights
    
    def test_validate_length_valid(self, validator):
        """Test valid length validation."""
        response = "Short response."
        
        result = validator.validate_length(response, 3, 20, 100)
        assert result is True
    
    def test_validate_length_invalid(self, validator):
        """Test invalid length validation."""
        long_response = ". ".join([f"Sentence {i}" for i in range(10)]) + "."
        
        result = validator.validate_length(long_response, 3, 20, 100)
        assert result is False
    
    def test_check_advisory_content_clean(self, validator):
        """Test advisory content check with clean response."""
        response = "The expense ratio is 0.85%."
        
        is_advisory, phrases = validator.check_advisory_content(response)
        assert is_advisory is False
        assert len(phrases) == 0
    
    def test_check_advisory_content_detected(self, validator):
        """Test advisory content detection."""
        response = "I recommend investing in this fund."
        
        is_advisory, phrases = validator.check_advisory_content(response)
        assert is_advisory is True
        assert len(phrases) > 0
        assert "recommend" in phrases[0].lower()
    
    def test_ensure_citation_with_context(self, validator):
        """Test citation requirement with context."""
        response = "According to the context, the fund has good performance."
        
        result = validator.ensure_citation(response, has_context=True)
        assert result is True
    
    def test_verify_compliance_valid(self, validator):
        """Test compliance verification for valid response."""
        response = "The expense ratio is 0.85%."
        
        result = validator.verify_compliance(response, "factual")
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.compliance_score > 0.8
        assert result.overall_score > 0.7
    
    def test_verify_compliance_invalid(self, validator):
        """Test compliance verification for invalid response."""
        response = "I recommend you invest in this fund as it's the best choice."
        
        result = validator.verify_compliance(response, "factual")
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert "Advisory content" in " ".join(result.issues)
    
    def test_validate_response_batch(self, validator):
        """Test batch response validation."""
        responses = [
            "The expense ratio is 0.85%.",
            "I recommend investing here.",
            "Past returns were 12%."
        ]
        query_types = ["factual", "advisory", "performance"]
        
        results = validator.validate_response_batch(responses, query_types)
        
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert isinstance(results[2], ValidationResult)
    
    def test_get_compliance_report(self, validator):
        """Test compliance report generation."""
        result = validator.verify_compliance("Test response", "factual")
        report = validator.get_compliance_report(result)
        
        assert "overall_valid" in report
        assert "overall_score" in report
        assert "component_scores" in report
        assert "issues" in report
        assert "recommendations" in report


class TestResponseFormatter:
    """Test Response Formatter functionality."""
    
    @pytest.fixture
    def formatter(self):
        """Create response formatter instance for testing."""
        return ResponseFormatter()
    
    def test_initialization(self, formatter):
        """Test formatter initialization."""
        assert len(formatter.disclaimers) == 5
        assert "factual" in formatter.disclaimers
        assert len(formatter.source_templates) == 4
        assert len(formatter.format_templates) == 4
    
    def test_format_response(self, formatter):
        """Test response formatting."""
        response = "The expense ratio is 0.85%."
        citation = "https://hdfcfund.com"
        date = "2024-01-15"
        
        formatted = formatter.format_response(response, citation, date, "factual")
        
        assert isinstance(formatted, FormattedResponse)
        assert formatted.answer == "The expense ratio is 0.85%."
        assert formatted.source == "Source: https://hdfcfund.com"
        assert formatted.last_updated == "2024-01-15"
        assert "Facts-only" in formatted.disclaimer
        assert formatted.query_type == "factual"
    
    def test_clean_answer(self, formatter):
        """Test answer cleaning."""
        dirty_answer = "  the expense ratio is 0.85%  "
        
        clean = formatter._clean_answer(dirty_answer)
        
        assert clean == "The expense ratio is 0.85%."
    
    def test_format_citation(self, formatter):
        """Test citation formatting."""
        # Test URL citation
        url_citation = formatter._format_citation("https://hdfcfund.com")
        assert url_citation == "Source: https://hdfcfund.com"
        
        # Test unavailable citation
        unavailable = formatter._format_citation("unavailable")
        assert unavailable == "Source information not available"
    
    def test_format_date(self, formatter):
        """Test date formatting."""
        # Test valid date
        valid_date = formatter._format_date("2024-01-15")
        assert valid_date == "2024-01-15"
        
        # Test invalid date
        invalid_date = formatter._format_date("invalid")
        assert len(invalid_date) == 10  # Should return current date in YYYY-MM-DD format
    
    def test_add_disclaimer(self, formatter):
        """Test disclaimer addition."""
        response = "Test response."
        
        with_disclaimer = formatter.add_disclaimer(response, "factual")
        
        assert "Facts-only" in with_disclaimer
        assert "No investment advice" in with_disclaimer
    
    def test_format_as_json(self, formatter):
        """Test JSON formatting."""
        formatted = formatter.format_response("Test", "https://test.com", "2024-01-15", "factual")
        
        json_str = formatter.format_as_json(formatted)
        
        # Parse JSON to verify structure
        parsed = json.loads(json_str)
        assert "answer" in parsed
        assert "source" in parsed
        assert "last_updated" in parsed
        assert "disclaimer" in parsed
        assert "query_type" in parsed
    
    def test_create_error_response(self, formatter):
        """Test error response creation."""
        error = formatter.create_error_response("API error", "factual")
        
        assert isinstance(error, FormattedResponse)
        assert "Unable to provide response" in error.answer
        assert error.confidence == 0.0
        assert error.query_type == "factual"
    
    def test_create_advisory_refusal_response(self, formatter):
        """Test advisory refusal response creation."""
        refusal = formatter.create_advisory_refusal_response("Should I invest?")
        
        assert isinstance(refusal, FormattedResponse)
        assert "cannot provide investment advice" in refusal.answer.lower()
        assert "financial advisor" in refusal.answer.lower()
        assert refusal.query_type == "advisory"
    
    def test_validate_format(self, formatter):
        """Test format validation."""
        formatted = formatter.format_response("Test", "https://test.com", "2024-01-15", "factual")
        
        validation = formatter.validate_format(formatted)
        
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
    
    def test_batch_format_responses(self, formatter):
        """Test batch response formatting."""
        responses = ["Response 1", "Response 2"]
        citations = ["https://test1.com", "https://test2.com"]
        dates = ["2024-01-15", "2024-01-16"]
        query_types = ["factual", "general"]
        
        formatted_list = formatter.batch_format_responses(responses, citations, dates, query_types)
        
        assert len(formatted_list) == 2
        assert all(isinstance(f, FormattedResponse) for f in formatted_list)


class TestPhase24Pipeline:
    """Test Phase 2.4 Pipeline integration."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            return Phase24Pipeline()
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.llm_service is not None
        assert pipeline.prompt_engine is not None
        assert pipeline.response_validator is not None
        assert pipeline.response_formatter is not None
        assert pipeline.query_processor is not None
    
    @pytest.mark.asyncio
    async def test_initialize_phase23_components_success(self, pipeline):
        """Test successful Phase 2.3 component initialization."""
        with patch('src.rag.llm.main.EmbeddingService'), \
             patch('src.rag.llm.main.VectorDatabase'), \
             patch('src.rag.llm.main.HierarchicalVectorDB'):
            
            result = await pipeline.initialize_phase23_components()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_initialize_phase23_components_failure(self, pipeline):
        """Test failed Phase 2.3 component initialization."""
        with patch('src.rag.llm.main.EmbeddingService', side_effect=Exception("Import error")):
            result = await pipeline.initialize_phase23_components()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_test_llm_service_success(self, pipeline):
        """Test successful LLM service test."""
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Test response"
        mock_response.response_time = 0.5
        mock_response.error_message = None
        
        with patch.object(pipeline.llm_service, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response
            
            result = await pipeline.test_llm_service()
            
            assert result["success"] is True
            assert result["response_time"] == 0.5
            assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_test_prompt_engineering_success(self, pipeline):
        """Test successful prompt engineering test."""
        result = await pipeline.test_prompt_engineering()
        
        assert result["success"] is True
        assert result["templates_tested"] == 5
        assert len(result["template_results"]) == 5
    
    @pytest.mark.asyncio
    async def test_test_response_validation_success(self, pipeline):
        """Test successful response validation test."""
        result = await pipeline.test_response_validation()
        
        assert result["success"] is True
        assert result["responses_tested"] == 5
        assert len(result["validation_results"]) == 5
    
    @pytest.mark.asyncio
    async def test_test_response_formatting_success(self, pipeline):
        """Test successful response formatting test."""
        result = await pipeline.test_response_formatting()
        
        assert result["success"] is True
        assert result["formats_tested"] == 3
        assert len(result["format_results"]) == 3
    
    @pytest.mark.asyncio
    async def test_run_performance_validation_success(self, pipeline):
        """Test successful performance validation."""
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Test"
        
        with patch.object(pipeline.llm_service, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response
            
            result = await pipeline.run_performance_validation()
            
            assert "success" in result
            assert "llm_performance" in result
            assert "validation_performance" in result
            assert "formatting_performance" in result
            assert "overall_performance" in result
    
    @pytest.mark.asyncio
    async def test_export_results_success(self, pipeline):
        """Test successful results export."""
        # Create test results
        formatted = pipeline.response_formatter.format_response(
            "Test", "https://test.com", "2024-01-15", "factual"
        )
        
        results = Phase24Results(
            success=True,
            total_queries=1,
            successful_responses=1,
            compliance_rate=100.0,
            average_response_time=0.5,
            llm_stats={"success_rate": 100.0},
            validation_stats={"total_validations": 1, "valid_responses": 1},
            formatted_responses=[formatted],
            errors=[]
        )
        
        with patch('pathlib.Path.mkdir'):
            export_success = await pipeline.export_results(results)
            assert export_success is True
    
    def test_get_api_key_from_environment(self, pipeline):
        """Test API key retrieval from environment."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env_key'}):
            api_key = pipeline._get_api_key()
            assert api_key == 'env_key'
    
    def test_get_api_key_missing(self, pipeline):
        """Test API key retrieval when missing."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                pipeline._get_api_key()


class TestIntegration:
    """Integration tests for Phase 2.4 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_response_generation(self):
        """Test end-to-end response generation flow."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create components
            llm_service = LLMService(api_key='test_key')
            prompt_engine = PromptEngine()
            validator = ResponseValidator()
            formatter = ResponseFormatter()
            
            # Mock LLM response
            mock_response = Mock()
            mock_response.success = True
            mock_response.content = "The expense ratio is 0.85%."
            mock_response.usage = Mock()
            mock_response.usage.model_dump.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
            
            with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_response
                
                # End-to-end flow
                query = "What is the expense ratio?"
                context = "HDFC Mid Cap Fund information"
                
                # 1. Generate prompt
                prompt = prompt_engine.create_factual_prompt(context, query, "factual")
                
                # 2. Generate LLM response
                llm_response = await llm_service.generate_response(prompt)
                
                # 3. Validate response
                validation = validator.verify_compliance(llm_response.content, "factual")
                
                # 4. Format response
                formatted = formatter.format_response(
                    llm_response.content,
                    "https://hdfcfund.com",
                    "2024-01-15",
                    "factual"
                )
                
                # Verify end-to-end success
                assert llm_response.success is True
                assert validation.is_valid is True
                assert isinstance(formatted, FormattedResponse)
                assert formatted.answer == "The expense ratio is 0.85%."
                assert "Source: https://hdfcfund.com" == formatted.source
    
    @pytest.mark.asyncio
    async def test_advisory_query_handling(self):
        """Test advisory query handling with refusal."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            llm_service = LLMService(api_key='test_key')
            prompt_engine = PromptEngine()
            validator = ResponseValidator()
            formatter = ResponseFormatter()
            
            # Mock LLM response for advisory query
            mock_response = Mock()
            mock_response.success = True
            mock_response.content = "I cannot provide investment advice. Please consult a financial advisor."
            mock_response.usage = Mock()
            mock_response.usage.model_dump.return_value = {"prompt_tokens": 10, "completion_tokens": 8}
            
            with patch.object(llm_service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_response
                
                # Advisory query flow
                query = "Should I invest in HDFC Mid Cap Fund?"
                
                # 1. Generate advisory prompt
                prompt = prompt_engine.create_factual_prompt("", query, "advisory")
                
                # 2. Generate LLM response
                llm_response = await llm_service.generate_response(prompt)
                
                # 3. Validate response
                validation = validator.verify_compliance(llm_response.content, "advisory")
                
                # 4. Format response
                formatted = formatter.format_response(
                    llm_response.content,
                    "https://groww.in",
                    "2024-01-15",
                    "advisory"
                )
                
                # Verify advisory handling
                assert llm_response.success is True
                assert validation.is_valid is True
                assert "cannot provide investment advice" in formatted.answer.lower()
                assert "financial advisor" in formatted.answer.lower()
                assert formatted.query_type == "advisory"


# Performance tests
class TestPerformance:
    """Performance tests for Phase 2.4 components."""
    
    @pytest.mark.asyncio
    async def test_prompt_generation_performance(self):
        """Test prompt generation performance."""
        prompt_engine = PromptEngine()
        
        import time
        start_time = time.time()
        
        # Generate 100 prompts
        for i in range(100):
            prompt = prompt_engine.create_factual_prompt(
                f"Test context {i}",
                f"Test query {i}",
                "factual"
            )
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 prompts in under 1 second
        assert elapsed_time < 1.0
        print(f"Generated 100 prompts in {elapsed_time:.3f}s")
    
    def test_validation_performance(self):
        """Test response validation performance."""
        validator = ResponseValidator()
        
        import time
        start_time = time.time()
        
        # Validate 100 responses
        for i in range(100):
            validation = validator.verify_compliance(
                f"Test response {i}.",
                "factual"
            )
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 validations in under 0.5 seconds
        assert elapsed_time < 0.5
        print(f"Validated 100 responses in {elapsed_time:.3f}s")
    
    def test_formatting_performance(self):
        """Test response formatting performance."""
        formatter = ResponseFormatter()
        
        import time
        start_time = time.time()
        
        # Format 100 responses
        for i in range(100):
            formatted = formatter.format_response(
                f"Response {i}.",
                f"https://test{i}.com",
                "2024-01-15",
                "factual"
            )
        
        elapsed_time = time.time() - start_time
        
        # Should complete 100 formats in under 0.5 seconds
        assert elapsed_time < 0.5
        print(f"Formatted 100 responses in {elapsed_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
