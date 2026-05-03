"""
Comprehensive tests for Phase 3: Query Processing and Response Generation
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rag.query_processing.query_classifier import QueryClassifier, QueryType, QueryClassification
from src.rag.query_processing.response_generator import ResponseGenerator, ResponseContext, GeneratedResponse
from src.rag.query_processing.response_formatter import ResponseFormatter, OutputFormat, FormattedResponse
from src.rag.query_processing.compliance_safety import ComplianceSafetyLayer, RiskLevel, ComplianceResult
from src.rag.query_processing.integration_tests import RAGIntegrationTests, TestQuery, TestResult
from src.rag.query_processing.main import Phase3Pipeline, Phase3Results


class TestQueryClassifier:
    """Test Query Classifier functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create query classifier instance for testing."""
        return QueryClassifier(cache_dir="test_cache/query_classifier")
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initialization."""
        assert classifier.cache_dir.exists()
        assert len(classifier.patterns) > 0
        assert classifier.classification_stats is not None
        assert classifier.query_history is not None
    
    def test_classify_factual_query(self, classifier):
        """Test classification of factual queries."""
        query = "What is the expense ratio of HDFC Mid Cap Fund?"
        classification = classifier.classify_query(query)
        
        assert isinstance(classification, QueryClassification)
        assert classification.query == query
        assert classification.query_type == QueryType.FACTUAL
        assert classification.confidence > 0.0
        assert classification.intent in ["get_expense_ratio", "general_inquiry"]
    
    def test_classify_advisory_query(self, classifier):
        """Test classification of advisory queries."""
        query = "Should I invest in HDFC Equity Fund?"
        classification = classifier.classify_query(query)
        
        assert classification.query_type == QueryType.ADVISORY
        assert classification.intent in ["provide_investment_advice", "compare_funds"]
        assert classification.confidence > 0.0
    
    def test_classify_performance_query(self, classifier):
        """Test classification of performance queries."""
        query = "What are the historical returns of HDFC Mid Cap Fund?"
        classification = classifier.classify_query(query)
        
        assert classification.query_type == QueryType.PERFORMANCE
        assert classification.intent in ["get_historical_returns", "compare_benchmark"]
        assert classification.confidence > 0.0
    
    def test_classify_procedural_query(self, classifier):
        """Test classification of procedural queries."""
        query = "How to start SIP in HDFC Mutual Fund?"
        classification = classifier.classify_query(query)
        
        assert classification.query_type == QueryType.PROCEDURAL
        assert classification.intent in ["provide_investment_process", "provide_statement_download"]
        assert classification.confidence > 0.0
    
    def test_classify_general_query(self, classifier):
        """Test classification of general queries."""
        query = "Tell me about HDFC Mutual Fund"
        classification = classifier.classify_query(query)
        
        assert classification.query_type == QueryType.GENERAL
        assert classification.intent == "general_inquiry"
        assert classification.confidence > 0.0
    
    def test_extract_keywords(self, classifier):
        """Test keyword extraction."""
        query = "What is the minimum SIP amount and expense ratio?"
        keywords = classifier._extract_keywords(query)
        
        assert "minimum" in keywords
        assert "sip" in keywords
        assert "expense" in keywords
        assert "ratio" in keywords
    
    def test_extract_entities(self, classifier):
        """Test entity extraction."""
        query = "What is the NAV of HDFC Mid Cap Fund?"
        entities = classifier._extract_entities(query)
        
        assert "nav" in entities
        assert "hdfc" in entities
        assert "fund" in entities
    
    def test_get_classification_stats(self, classifier):
        """Test classification statistics retrieval."""
        # Add some test classifications
        classifier.classify_query("What is the expense ratio?")
        classifier.classify_query("Should I invest in HDFC?")
        classifier.classify_query("How to start SIP?")
        
        stats = classifier.get_classification_stats()
        
        assert "total_classifications" in stats
        assert "distribution" in stats
        assert "patterns_available" in stats
        assert stats["total_classifications"] >= 3
    
    def test_add_custom_pattern(self, classifier):
        """Test adding custom classification pattern."""
        classifier.add_custom_pattern(
            name="test_pattern",
            query_type=QueryType.FACTUAL,
            patterns=[r"test.*pattern"],
            keywords=["test", "pattern"],
            entities=["test"],
            intent="test_intent"
        )
        
        assert "test_pattern" in [p.name for p in classifier.patterns]
    
    def test_remove_pattern(self, classifier):
        """Test removing classification pattern."""
        # Add a pattern first
        classifier.add_custom_pattern(
            name="temp_pattern",
            query_type=QueryType.FACTUAL,
            patterns=[r"temp.*pattern"],
            keywords=["temp", "pattern"],
            entities=["temp"],
            intent="temp_intent"
        )
        
        # Remove it
        success = classifier.remove_pattern("temp_pattern")
        assert success is True
        assert "temp_pattern" not in [p.name for p in classifier.patterns]
    
    def test_batch_classify(self, classifier):
        """Test batch classification."""
        queries = [
            "What is the expense ratio?",
            "Should I invest?",
            "How to start SIP?"
        ]
        
        classifications = classifier.batch_classify(queries)
        
        assert len(classifications) == len(queries)
        for classification in classifications:
            assert isinstance(classification, QueryClassification)
    
    def test_validate_classification(self, classifier):
        """Test classification validation."""
        # Create a valid classification
        valid_classification = QueryClassification(
            query="test query",
            query_type=QueryType.FACTUAL,
            confidence=0.8,
            keywords=["test"],
            entities=["test"],
            intent="test_intent",
            subcategory="test",
            metadata={}
        )
        
        assert classifier.validate_classification(valid_classification) is True
        
        # Create an invalid classification
        invalid_classification = QueryClassification(
            query="",
            query_type=QueryType.FACTUAL,
            confidence=1.5,  # Invalid confidence > 1.0
            keywords=[],
            entities=[],
            intent="",
            subcategory=None,
            metadata={}
        )
        
        assert classifier.validate_classification(invalid_classification) is False


class TestResponseGenerator:
    """Test Response Generator functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create response generator instance for testing."""
        return ResponseGenerator(cache_dir="test_cache/response_generator")
    
    def test_generator_initialization(self, generator):
        """Test generator initialization."""
        assert generator.cache_dir.exists()
        assert generator.templates is not None
        assert generator.response_stats is not None
        assert generator.response_history is not None
    
    @pytest.mark.asyncio
    async def test_generate_factual_response(self, generator):
        """Test factual response generation."""
        from .query_classifier import QueryClassification, QueryType
        
        classification = QueryClassification(
            query="What is the expense ratio?",
            query_type=QueryType.FACTUAL,
            confidence=0.9,
            keywords=["expense", "ratio"],
            entities=["hdfc", "fund"],
            intent="get_expense_ratio",
            subcategory="fund_metrics",
            metadata={}
        )
        
        context = ResponseContext(
            query="What is the expense ratio?",
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context=None,
            session_context=None,
            metadata={"test_mode": True}
        )
        
        response = await generator.generate_response(context)
        
        assert isinstance(response, GeneratedResponse)
        assert response.query == "What is the expense ratio?"
        assert response.response_type == "factual"
        assert len(response.content) > 0
        assert response.confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_generate_advisory_response(self, generator):
        """Test advisory response generation."""
        from .query_classifier import QueryClassification, QueryType
        
        classification = QueryClassification(
            query="Should I invest in HDFC?",
            query_type=QueryType.ADVISORY,
            confidence=0.8,
            keywords=["should", "invest"],
            entities=["hdfc"],
            intent="provide_investment_advice",
            subcategory="investment_guidance",
            metadata={}
        )
        
        context = ResponseContext(
            query="Should I invest in HDFC?",
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context=None,
            session_context=None,
            metadata={"test_mode": True}
        )
        
        response = await generator.generate_response(context)
        
        assert response.response_type == "advisory"
        assert "cannot provide investment advice" in response.content.lower()
        assert "disclaimer" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_generate_performance_response(self, generator):
        """Test performance response generation."""
        from .query_classifier import QueryClassification, QueryType
        
        classification = QueryClassification(
            query="What are the historical returns?",
            query_type=QueryType.PERFORMANCE,
            confidence=0.8,
            keywords=["historical", "returns"],
            entities=["fund"],
            intent="get_historical_returns",
            subcategory="performance_metrics",
            metadata={}
        )
        
        context = ResponseContext(
            query="What are the historical returns?",
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context=None,
            session_context=None,
            metadata={"test_mode": True}
        )
        
        response = await generator.generate_response(context)
        
        assert response.response_type == "performance"
        assert len(response.content) > 0
    
    @pytest.mark.asyncio
    async def test_generate_procedural_response(self, generator):
        """Test procedural response generation."""
        from .query_classifier import QueryClassification, QueryType
        
        classification = QueryClassification(
            query="How to start SIP?",
            query_type=QueryType.PROCEDURAL,
            confidence=0.8,
            keywords=["how", "sip"],
            entities=["sip"],
            intent="provide_investment_process",
            subcategory="investment_procedure",
            metadata={}
        )
        
        context = ResponseContext(
            query="How to start SIP?",
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context=None,
            session_context=None,
            metadata={"test_mode": True}
        )
        
        response = await generator.generate_response(context)
        
        assert response.response_type == "procedural"
        assert len(response.content) > 0
    
    def test_extract_relevant_info(self, generator):
        """Test relevant information extraction."""
        chunks = [
            {
                "content": "The expense ratio of HDFC Mid Cap Fund is 1.5%.",
                "source_url": "https://example.com"
            },
            {
                "content": "This fund has performed well in the past year.",
                "source_url": "https://example.com"
            }
        ]
        
        query = "What is the expense ratio?"
        relevant_info = generator._extract_relevant_info(chunks, query)
        
        assert len(relevant_info) > 0
        assert any("expense ratio" in info.lower() for info in relevant_info)
    
    def test_extract_sources(self, generator):
        """Test source extraction."""
        chunks = [
            {
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund",
                "fund_name": "HDFC Mid Cap",
                "document_type": "factsheet",
                "content_type": "expense_ratio",
                "last_updated": "2024-01-15"
            }
        ]
        
        sources = generator._extract_sources(chunks)
        
        assert len(sources) == 1
        assert sources[0]["source_url"] == "https://hdfcfund.com"
        assert sources[0]["source_title"] == "HDFC Fund"
    
    def test_get_response_stats(self, generator):
        """Test response statistics retrieval."""
        # Add some test responses
        from .query_classifier import QueryClassification, QueryType
        
        classification = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            confidence=0.8,
            keywords=[],
            entities=[],
            intent="test",
            subcategory=None,
            metadata={}
        )
        
        context = ResponseContext(
            query="test",
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context=None,
            session_context=None,
            metadata={}
        )
        
        # Simulate generating a response
        response = GeneratedResponse(
            query="test",
            response_type="factual",
            content="test response",
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        generator.response_history.append(response)
        
        stats = generator.get_response_stats()
        
        assert "total_responses" in stats
        assert "distribution" in stats
        assert "average_confidence" in stats
        assert "templates_available" in stats
    
    def test_add_custom_template(self, generator):
        """Test adding custom response template."""
        generator.add_custom_template(
            response_type="custom",
            template_name="test_template",
            template="Custom response: {content}"
        )
        
        assert "custom" in generator.templates
        assert "test_template" in generator.templates["custom"]
    
    def test_validate_response(self, generator):
        """Test response validation."""
        # Create a valid response
        valid_response = GeneratedResponse(
            query="test query",
            response_type="factual",
            content="test content",
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        assert generator.validate_response(valid_response) is True
        
        # Create an invalid response
        invalid_response = GeneratedResponse(
            query="",  # Empty query
            response_type="factual",
            content="test content",
            sources=[],
            confidence=1.5,  # Invalid confidence
            response_time=0.5,
            metadata={}
        )
        
        assert generator.validate_response(invalid_response) is False


class TestResponseFormatter:
    """Test Response Formatter functionality."""
    
    @pytest.fixture
    def formatter(self):
        """Create response formatter instance for testing."""
        return ResponseFormatter(cache_dir="test_cache/response_formatter")
    
    def test_formatter_initialization(self, formatter):
        """Test formatter initialization."""
        assert formatter.cache_dir.exists()
        assert formatter.templates is not None
        assert formatter.formatting_stats is not None
        assert formatter.format_history is not None
    
    def test_format_as_json(self, formatter):
        """Test JSON formatting."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.JSON)
        
        assert isinstance(formatted, FormattedResponse)
        assert formatted.output_format == OutputFormat.JSON
        assert "query" in formatted.formatted_content
        assert "response_type" in formatted.formatted_content
        assert "content" in formatted.formatted_content
        
        # Verify it's valid JSON
        parsed = json.loads(formatted.formatted_content)
        assert parsed["query"] == "What is the expense ratio?"
    
    def test_format_as_ui(self, formatter):
        """Test UI formatting."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.UI)
        
        assert formatted.output_format == OutputFormat.UI
        assert "Answer:" in formatted.formatted_content
        assert "Sources:" in formatted.formatted_content
        assert "Confidence:" in formatted.formatted_content
    
    def test_format_as_text(self, formatter):
        """Test text formatting."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.TEXT)
        
        assert formatted.output_format == OutputFormat.TEXT
        assert "Answer:" in formatted.formatted_content
        assert "Sources:" in formatted.formatted_content
    
    def test_format_as_markdown(self, formatter):
        """Test Markdown formatting."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.MARKDOWN)
        
        assert formatted.output_format == OutputFormat.MARKDOWN
        assert "## Answer" in formatted.formatted_content
        assert "### Sources" in formatted.formatted_content
    
    def test_format_as_html(self, formatter):
        """Test HTML formatting."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.HTML)
        
        assert formatted.output_format == OutputFormat.HTML
        assert "<div class='response'>" in formatted.formatted_content
        assert "<h3>Answer</h3>" in formatted.formatted_content
    
    def test_format_multiple_responses(self, formatter):
        """Test formatting multiple responses."""
        from .response_generator import GeneratedResponse
        
        responses = [
            GeneratedResponse(
                query="Query 1",
                response_type="factual",
                content="Response 1",
                sources=[],
                confidence=0.8,
                response_time=0.5,
                metadata={}
            ),
            GeneratedResponse(
                query="Query 2",
                response_type="advisory",
                content="Response 2",
                sources=[],
                confidence=0.7,
                response_time=0.6,
                metadata={}
            )
        ]
        
        formatted_responses = formatter.format_multiple_responses(responses, OutputFormat.JSON)
        
        assert len(formatted_responses) == len(responses)
        for formatted in formatted_responses:
            assert isinstance(formatted, FormattedResponse)
            assert formatted.output_format == OutputFormat.JSON
    
    def test_get_formatting_stats(self, formatter):
        """Test formatting statistics retrieval."""
        # Add some test formatted responses
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="test",
            response_type="factual",
            content="test content",
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.JSON)
        
        stats = formatter.get_formatting_stats()
        
        assert "total_formatted" in stats
        assert "distribution" in stats
        assert "formats_available" in stats
        assert stats["total_formatted"] >= 1
    
    def test_add_custom_template(self, formatter):
        """Test adding custom formatting template."""
        formatter.add_custom_template(
            output_format="custom",
            response_type="test",
            template_name="test_template",
            template="Custom: {content}",
            source_format="Source: {source_title}"
        )
        
        assert "custom" in formatter.templates
        assert "test" in formatter.templates["custom"]
    
    def test_validate_formatted_response(self, formatter):
        """Test formatted response validation."""
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="test query",
            response_type="factual",
            content="test content",
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        formatted = formatter.format_response(response, OutputFormat.JSON)
        
        assert formatter.validate_formatted_response(formatted) is True


class TestComplianceSafetyLayer:
    """Test Compliance and Safety Layer functionality."""
    
    @pytest.fixture
    def compliance_layer(self):
        """Create compliance safety layer instance for testing."""
        return ComplianceSafetyLayer(cache_dir="test_cache/compliance_safety")
    
    def test_compliance_initialization(self, compliance_layer):
        """Test compliance layer initialization."""
        assert compliance_layer.cache_dir.exists()
        assert len(compliance_layer.compliance_rules) > 0
        assert len(compliance_layer.safety_rules) > 0
        assert len(compliance_layer.blocked_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_compliance_check_factual_query(self, compliance_layer):
        """Test compliance check for factual queries."""
        from .query_classifier import QueryClassification, QueryType
        from .response_generator import GeneratedResponse
        
        classification = QueryClassification(
            query="What is the expense ratio?",
            query_type=QueryType.FACTUAL,
            confidence=0.9,
            keywords=["expense", "ratio"],
            entities=["hdfc", "fund"],
            intent="get_expense_ratio",
            subcategory="fund_metrics",
            metadata={}
        )
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5% for HDFC Mid Cap Fund.",
            sources=[],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        result = await compliance_layer.check_compliance(
            "What is the expense ratio?", classification, response
        )
        
        assert isinstance(result, ComplianceResult)
        assert result.query == "What is the expense ratio?"
        assert result.approved is True  # Factual queries should be approved
        assert result.overall_risk in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_compliance_check_advisory_query(self, compliance_layer):
        """Test compliance check for advisory queries."""
        from .query_classifier import QueryClassification, QueryType
        from .response_generator import GeneratedResponse
        
        classification = QueryClassification(
            query="Should I invest in HDFC?",
            query_type=QueryType.ADVISORY,
            confidence=0.8,
            keywords=["should", "invest"],
            entities=["hdfc"],
            intent="provide_investment_advice",
            subcategory="investment_guidance",
            metadata={}
        )
        
        response = GeneratedResponse(
            query="Should I invest in HDFC?",
            response_type="advisory",
            content="I cannot provide investment advice. Please consult a qualified financial advisor.",
            sources=[],
            confidence=1.0,
            response_time=0.5,
            metadata={}
        )
        
        result = await compliance_layer.check_compliance(
            "Should I invest in HDFC?", classification, response
        )
        
        assert result.approved is True  # Should be approved with proper refusal
        assert result.overall_risk in [RiskLevel.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_compliance_check_blocked_content(self, compliance_layer):
        """Test compliance check for blocked content."""
        from .query_classifier import QueryClassification, QueryType
        from .response_generator import GeneratedResponse
        
        classification = QueryClassification(
            query="Guaranteed returns?",
            query_type=QueryType.FACTUAL,
            confidence=0.8,
            keywords=["guaranteed", "returns"],
            entities=[],
            intent="general_inquiry",
            subcategory=None,
            metadata={}
        )
        
        response = GeneratedResponse(
            query="Guaranteed returns?",
            response_type="factual",
            content="We guarantee 15% annual returns with no risk.",
            sources=[],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        result = await compliance_layer.check_compliance(
            "Guaranteed returns?", classification, response
        )
        
        assert result.approved is False  # Should be blocked
        assert result.overall_risk == RiskLevel.CRITICAL
    
    def test_get_compliance_stats(self, compliance_layer):
        """Test compliance statistics retrieval."""
        # Add some test results
        from .query_classifier import QueryClassification, QueryType
        from .response_generator import GeneratedResponse
        
        classification = QueryClassification(
            query="test",
            query_type=QueryType.FACTUAL,
            confidence=0.8,
            keywords=[],
            entities=[],
            intent="test",
            subcategory=None,
            metadata={}
        )
        
        response = GeneratedResponse(
            query="test",
            response_type="factual",
            content="test content",
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        # Simulate compliance check
        result = ComplianceResult(
            query="test",
            classification=classification,
            response=response,
            compliance_checks=[],
            safety_checks=[],
            overall_risk=RiskLevel.LOW,
            approved=True,
            modifications=[],
            timestamp=datetime.now()
        )
        
        compliance_layer.compliance_history.append(result)
        
        stats = compliance_layer.get_compliance_stats()
        
        assert "total_checks" in stats
        assert "risk_distribution" in stats
        assert "approval_rate" in stats
        assert "compliance_rules_count" in stats
    
    def test_add_compliance_rule(self, compliance_layer):
        """Test adding custom compliance rule."""
        compliance_layer.add_compliance_rule(
            rule_name="test_rule",
            description="Test rule",
            patterns=[r"test.*pattern"],
            risk_level=RiskLevel.MEDIUM,
            action="block",
            allowed_responses=[]
        )
        
        assert "test_rule" in compliance_layer.compliance_rules
        assert compliance_layer.compliance_rules["test_rule"]["risk_level"] == RiskLevel.MEDIUM
    
    def test_remove_compliance_rule(self, compliance_layer):
        """Test removing compliance rule."""
        # Add a rule first
        compliance_layer.add_compliance_rule(
            rule_name="temp_rule",
            description="Temp rule",
            patterns=[r"temp.*pattern"],
            risk_level=RiskLevel.LOW,
            action="block",
            allowed_responses=[]
        )
        
        # Remove it
        success = compliance_layer.remove_compliance_rule("temp_rule")
        assert success is True
        assert "temp_rule" not in compliance_layer.compliance_rules


class TestRAGIntegrationTests:
    """Test RAG Integration Tests functionality."""
    
    @pytest.fixture
    def integration_tests(self):
        """Create integration tests instance for testing."""
        return RAGIntegrationTests(cache_dir="test_cache/integration_tests")
    
    def test_integration_tests_initialization(self, integration_tests):
        """Test integration tests initialization."""
        assert integration_tests.cache_dir.exists()
        assert len(integration_tests.test_queries) > 0
        assert integration_tests.query_classifier is not None
        assert integration_tests.response_generator is not None
        assert integration_tests.response_formatter is not None
        assert integration_tests.compliance_safety is not None
    
    def test_initialize_test_queries(self, integration_tests):
        """Test test queries initialization."""
        test_queries = integration_tests.test_queries
        
        assert len(test_queries) > 0
        
        # Check different query types are present
        query_types = set(q.expected_type for q in test_queries)
        assert QueryType.FACTUAL in query_types
        assert QueryType.ADVISORY in query_types
        assert QueryType.PERFORMANCE in query_types
        assert QueryType.PROCEDURAL in query_types
    
    @pytest.mark.asyncio
    async def test_run_single_test(self, integration_tests):
        """Test running a single test."""
        test_query = integration_tests.test_queries[0]
        
        result = await integration_tests._run_single_test(test_query)
        
        assert isinstance(result, TestResult)
        assert result.test_query == test_query
        assert "classification_result" in result.__dict__
        assert "generation_result" in result.__dict__
        assert "formatting_result" in result.__dict__
        assert "compliance_result" in result.__dict__
        assert "overall_success" in result.__dict__
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self, integration_tests):
        """Test end-to-end pipeline."""
        result = await integration_tests.test_end_to_end_pipeline()
        
        assert "total_tests" in result
        assert "successful_tests" in result
        assert "success_rate" in result
        assert "execution_time" in result
        assert "detailed_results" in result
        
        assert result["total_tests"] > 0
        assert result["success_rate"] >= 0
    
    @pytest.mark.asyncio
    async def test_benchmark_performance(self, integration_tests):
        """Test performance benchmarking."""
        result = await integration_tests.benchmark_performance()
        
        assert "benchmarks" in result
        assert "overall_performance" in result
        
        assert len(result["benchmarks"]) > 0
        assert "overall_score" in result["overall_performance"]
    
    @pytest.mark.asyncio
    async def test_validate_compliance(self, integration_tests):
        """Test compliance validation."""
        result = await integration_tests.validate_compliance()
        
        assert "total_validations" in result
        assert "approved_validations" in result
        assert "approval_rate" in result
        assert "detailed_results" in result
        
        assert result["total_validations"] > 0
    
    @pytest.mark.asyncio
    async def test_verify_error_handling(self, integration_tests):
        """Test error handling verification."""
        result = await integration_tests.verify_error_handling()
        
        assert "total_error_tests" in result
        assert "successful_error_tests" in result
        assert "error_handling_rate" in result
        assert "detailed_results" in result
    
    def test_get_test_summary(self, integration_tests):
        """Test test summary retrieval."""
        # Add some test results
        from .query_classifier import QueryClassification, QueryType
        from .response_generator import GeneratedResponse
        from .response_formatter import OutputFormat
        from .compliance_safety import ComplianceResult, RiskLevel
        
        test_query = integration_tests.test_queries[0]
        
        test_result = TestResult(
            test_query=test_query,
            classification_result={"success": True},
            generation_result={"success": True},
            formatting_result={"success": True},
            compliance_result={"approved": True},
            overall_success=True,
            execution_time=1.0,
            errors=[],
            timestamp=datetime.now()
        )
        
        integration_tests.test_results.append(test_result)
        
        summary = integration_tests.get_test_summary()
        
        assert "overall" in summary
        assert "by_category" in summary
        assert "benchmark_summary" in summary
        assert summary["overall"]["total_tests"] >= 1
    
    def test_add_test_query(self, integration_tests):
        """Test adding custom test query."""
        integration_tests.add_test_query(
            query_id="custom_test",
            query="Custom test query",
            expected_type=QueryType.GENERAL,
            expected_intent="general_inquiry",
            expected_response_type="general",
            test_category="custom",
            priority="low"
        )
        
        added_query = next((q for q in integration_tests.test_queries if q.query_id == "custom_test"), None)
        assert added_query is not None
        assert added_query.query == "Custom test query"
    
    def test_remove_test_query(self, integration_tests):
        """Test removing test query."""
        # Add a test query first
        integration_tests.add_test_query(
            query_id="temp_test",
            query="Temp test query",
            expected_type=QueryType.GENERAL,
            expected_intent="general_inquiry",
            expected_response_type="general",
            test_category="temp",
            priority="low"
        )
        
        # Remove it
        success = integration_tests.remove_test_query("temp_test")
        assert success is True
        
        removed_query = next((q for q in integration_tests.test_queries if q.query_id == "temp_test"), None)
        assert removed_query is None


class TestPhase3Pipeline:
    """Test Phase 3 Pipeline integration."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing."""
        return Phase3Pipeline()
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.query_classifier is not None
        assert pipeline.response_generator is not None
        assert pipeline.response_formatter is not None
        assert pipeline.compliance_safety is not None
        assert pipeline.integration_tests is not None
    
    @pytest.mark.asyncio
    async def test_query_classification_test(self, pipeline):
        """Test query classification component test."""
        result = await pipeline.test_query_classification()
        
        assert "success" in result
        assert "total_classifications" in result
        assert "accuracy_percentage" in result
        assert "confidence_distribution" in result
    
    @pytest.mark.asyncio
    async def test_response_generation_test(self, pipeline):
        """Test response generation component test."""
        result = await pipeline.test_response_generation()
        
        assert "success" in result
        assert "total_generations" in result
        assert "success_percentage" in result
        assert "response_types" in result
    
    @pytest.mark.asyncio
    async def test_response_formatting_test(self, pipeline):
        """Test response formatting component test."""
        result = await pipeline.test_response_formatting()
        
        assert "success" in result
        assert "total_formats" in result
        assert "successful_formats" in result
        assert "format_coverage" in result
    
    @pytest.mark.asyncio
    async def test_compliance_safety_test(self, pipeline):
        """Test compliance safety component test."""
        result = await pipeline.test_compliance_safety()
        
        assert "success" in result
        assert "total_checks" in result
        assert "approved_checks" in result
        assert "approval_rate" in result
        assert "risk_distribution" in result
    
    @pytest.mark.asyncio
    async def test_integration_test(self, pipeline):
        """Test integration component test."""
        result = await pipeline.test_integration()
        
        assert "success" in result
        assert "classification_to_generation" in result
        assert "generation_to_formatting" in result
        assert "generation_to_compliance" in result
        assert "end_to_end_workflow" in result
        assert "data_flow_consistent" in result
    
    @pytest.mark.asyncio
    async def test_performance_validation(self, pipeline):
        """Test performance validation."""
        result = await pipeline.run_performance_validation()
        
        assert "success" in result
        assert "classification_performance" in result
        assert "generation_performance" in result
        assert "formatting_performance" in result
        assert "overall_performance" in result
    
    def test_calculate_system_health(self, pipeline):
        """Test system health calculation."""
        health_score = pipeline._calculate_system_health()
        
        assert isinstance(health_score, (int, float))
        assert 0 <= health_score <= 100


# Performance tests
class TestPerformance:
    """Performance tests for Phase 3 components."""
    
    def test_query_classifier_performance(self):
        """Test query classifier performance."""
        classifier = QueryClassifier(cache_dir="test_cache/perf_classifier")
        
        import time
        start_time = time.time()
        
        # Test multiple classifications
        queries = [
            "What is the expense ratio?",
            "Should I invest?",
            "How to start SIP?",
            "Historical returns?",
            "Tell me about HDFC"
        ]
        
        for query in queries:
            classifier.classify_query(query)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 5 classifications in under 1 second
        assert elapsed_time < 1.0
        print(f"Query classifier processed 5 queries in {elapsed_time:.3f}s")
    
    def test_response_formatter_performance(self):
        """Test response formatter performance."""
        formatter = ResponseFormatter(cache_dir="test_cache/perf_formatter")
        
        import time
        from .response_generator import GeneratedResponse
        
        response = GeneratedResponse(
            query="What is the expense ratio?",
            response_type="factual",
            content="The expense ratio is 1.5%.",
            sources=[{
                "source_url": "https://hdfcfund.com",
                "source_title": "HDFC Fund"
            }],
            confidence=0.9,
            response_time=0.5,
            metadata={}
        )
        
        start_time = time.time()
        
        # Test multiple format conversions
        for _ in range(20):
            formatter.format_response(response, OutputFormat.JSON)
        
        elapsed_time = time.time() - start_time
        
        # Should complete 20 format conversions in under 0.5 seconds
        assert elapsed_time < 0.5
        print(f"Response formatter performed 20 conversions in {elapsed_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
