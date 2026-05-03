# Phase 2.4 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 2.4 - LLM Integration and Prompt Engineering of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. LLM Service Integration
- **File**: `src/rag/llm/llm_service.py`
- **Purpose**: Handle communication with OpenAI GPT-3.5-turbo
- **Key Features**:
  - Retry mechanisms with exponential backoff
  - Rate limiting handling
  - Performance monitoring and statistics
  - Health check functionality
  - Batch response generation

### 2. Prompt Engineering System
- **File**: `src/rag/llm/prompt_engine.py`
- **Purpose**: Design and manage facts-only prompts
- **Key Features**:
  - 5 query-type specific templates (factual, advisory, performance, procedural, general)
  - Length constraint enforcement (max 3 sentences)
  - Compliance instruction integration
  - Citation requirement enforcement
  - Prompt validation and optimization

### 3. Response Validator
- **File**: `src/rag/llm/response_validator.py`
- **Purpose**: Validate LLM responses for compliance
- **Key Features**:
  - Advisory content detection (8 patterns)
  - Response length validation
  - Citation requirement checking
  - Compliance scoring (0-1 scale)
  - Multi-criteria validation (compliance, length, content)

### 4. Response Formatter
- **File**: `src/rag/llm/response_formatter.py`
- **Purpose**: Format responses with citations and disclaimers
- **Key Features**:
  - Standardized response structure
  - Automatic disclaimer addition
  - Source citation formatting
  - JSON and UI output formats
  - Error response handling

### 5. Main Pipeline
- **File**: `src/rag/llm/main.py`
- **Purpose**: Orchestrate complete Phase 2.4 workflow
- **Key Features**:
  - Component initialization and testing
  - End-to-end response generation
  - Performance validation
  - Integration testing
  - Results export and reporting

## Data Flow

```
User Query → Query Processing → Prompt Generation → LLM Service → Response Validation → Response Formatting → Final Output
```

## Key Implementation Details

### LLM Service Configuration
```python
# Configuration
model: "gpt-3.5-turbo"
max_retries: 3
base_delay: 1.0s
max_delay: 60.0s
timeout: 30.0s

# Performance Targets
response_time: < 3 seconds
success_rate: > 95%
rate_limit_handling: exponential backoff
```

### Prompt Engineering Templates

#### Factual Queries
```python
system_prompt = "You are a factual information assistant for HDFC mutual funds. Provide only factual information based on the given context."
user_prompt = """Based on the following context, answer the question factually and concisely.

Context: {context}
Question: {query}

Provide a factual answer in maximum 3 sentences. Include only information from the context."""
```

#### Advisory Queries
```python
system_prompt = "You are a factual information assistant. Do not provide investment advice. Politely decline advisory questions and provide educational information."
user_prompt = """The user is asking for investment advice: {query}

Politely decline to provide investment advice. Instead:
1. State that you cannot provide investment advice
2. Provide factual information about the topic if available in context
3. Suggest consulting a financial advisor"""
```

### Response Validation Criteria

#### Advisory Content Patterns
- "I recommend", "we recommend"
- "you should", "you must", "you need to"
- "best fund", "top fund", "good fund"
- "invest in", "buy", "sell", "switch to"
- "guaranteed return", "sure shot", "safe bet"

#### Compliance Scoring
- **Compliance Score** (50% weight): Advisory content detection
- **Length Score** (30% weight): Sentence/word/character limits
- **Content Score** (20% weight): Factual language quality

#### Validation Thresholds
- Overall Score: > 0.7 (pass)
- Compliance Score: > 0.8 (pass)
- Length Limits: 3 sentences, 50 words, 300 characters

### Response Formatting Structure

#### Standard Format
```python
{
    "answer": "Concise factual response (max 3 sentences)",
    "source": "Single official source URL",
    "last_updated": "YYYY-MM-DD",
    "disclaimer": "Facts-only. No investment advice.",
    "query_type": "factual|advisory|performance|procedural|general",
    "confidence": 1.0,
    "response_time": 0.23,
    "citations": ["https://hdfcfund.com"],
    "metadata": {
        "format_version": "2.4.0",
        "generated_at": "2024-01-15T10:30:00Z"
    }
}
```

#### Disclaimers by Query Type
- **Factual**: "Facts-only. No investment advice provided."
- **Advisory**: "Facts-only. No investment advice provided. Please consult a financial advisor for personalized advice."
- **Performance**: "Facts-only. Past performance does not guarantee future results. No investment advice provided."
- **Procedural**: "Facts-only. No investment advice provided. Please verify with official sources."
- **General**: "Facts-only. No investment advice provided."

## Usage Instructions

### Running Phase 2.4

1. **Set OpenAI API Key**:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. **Install Required Dependencies**:
```bash
pip install openai backoff
```

3. **Run the Pipeline**:
```bash
python src/rag/llm/main.py
```

### Expected Pipeline Output

```
================================================================================
PHASE 2.4: LLM INTEGRATION AND PROMPT ENGINEERING
================================================================================

🔹 INITIALIZING PHASE 2.3 COMPONENTS:
  ✅ Phase 2.3 components initialized

🔹 TESTING LLM SERVICE:
  ✅ LLM Service: Connected

🔹 TESTING PROMPT ENGINEERING:
  ✅ Prompt Engineering: 5/5 templates tested

🔹 TESTING RESPONSE VALIDATION:
  ✅ Response Validation: 5/5 responses tested

🔹 TESTING RESPONSE FORMATTING:
  ✅ Response Formatting: 3/3 formats tested

🔹 TESTING END-TO-END RESPONSES:
  ✅ End-to-End: 4/4 queries tested

🔹 PERFORMANCE VALIDATION:
  ✅ Performance: All targets met

🔹 INTEGRATION TESTING:
  ✅ Integration: Passed

🔹 EXPORTING RESULTS:
  ✅ Export: Completed

================================================================================
PHASE 2.4 RESULTS: LLM Integration and Prompt Engineering
================================================================================
Success: ✅
Total Queries Tested: 4
Successful Responses: 4
Compliance Rate: 100.0%
Average Response Time: 0.45s
LLM Success Rate: 100.0%
Validation Success Rate: 5/5

📈 COMPONENT TESTS:
LLM Service: ✅
Prompt Engineering: ✅
Response Validation: ✅
Response Formatting: ✅
End-to-End: ✅
Performance: ✅
Integration: ✅

📊 PERFORMANCE TARGETS:
LLM Response Time: ✅ (<3s)
Validation Time: ✅ (<0.1s)
Formatting Time: ✅ (<0.1s)
Overall Time: ✅ (<3.5s)

🔧 INTEGRATION STATUS:
Phase 2.3 Integration: ✅
Component Integration: ✅
Data Flow Validation: ✅
Error Handling: ✅

================================================================================
```

## Configuration Options

### LLM Service
```python
# In src/rag/llm/llm_service.py
LLMService(
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)
# Configured with:
# - Retry logic with exponential backoff
# - Rate limiting handling
# - Performance monitoring
# - Health checks
```

### Prompt Engine
```python
# In src/rag/llm/prompt_engine.py
PromptEngine()
# Configured with:
# - 5 query-type templates
# - Compliance rules
# - Length constraints
# - Validation logic
```

### Response Validator
```python
# In src/rag/llm/response_validator.py
ResponseValidator()
# Configured with:
# - 8 advisory content patterns
# - 5 compliance patterns
# - Multi-criteria scoring
# - Length limits by query type
```

### Response Formatter
```python
# In src/rag/llm/response_formatter.py
ResponseFormatter()
# Configured with:
# - Standardized format structure
# - Automatic disclaimers
# - Source citation formatting
# - JSON/UI output options
```

## Performance Metrics

### Target Performance
- **LLM Response Time**: < 3 seconds
- **Validation Time**: < 0.1 seconds
- **Formatting Time**: < 0.1 seconds
- **Overall Pipeline Time**: < 3.5 seconds
- **Compliance Rate**: 100%
- **Success Rate**: > 95%

### Monitoring
```python
# Performance validation includes:
- LLM service response time
- Response validation processing time
- Response formatting time
- End-to-end pipeline latency
- Compliance validation accuracy
- Integration testing validation
```

## Testing

### Running Tests
```bash
# Run all Phase 2.4 tests
pytest tests/test_llm.py -v

# Run with coverage
pytest tests/test_llm.py --cov=src.rag.llm

# Run specific test class
pytest tests/test_llm.py::TestLLMService -v

# Run performance tests
pytest tests/test_llm.py::TestPerformance -v
```

### Test Coverage
- LLM service functionality and error handling
- Prompt engineering templates and validation
- Response validation compliance checking
- Response formatting and structure
- End-to-end pipeline integration
- Performance benchmarking
- Error handling and edge cases

## Error Handling

### Common Scenarios

1. **OpenAI API Errors**
   - Retry with exponential backoff
   - Graceful degradation to error responses
   - Rate limiting handling

2. **Validation Failures**
   - Advisory content detected
   - Length constraints exceeded
   - Compliance score too low

3. **Formatting Issues**
   - Missing required fields
   - Invalid citation formats
   - Date parsing errors

### Error Response Structure
```python
{
    "answer": "Unable to provide response: [error message]",
    "source": "Source information not available",
    "last_updated": "2024-01-15",
    "disclaimer": "Facts-only. No investment advice.",
    "query_type": "factual",
    "confidence": 0.0,
    "response_time": 0.0,
    "citations": [],
    "metadata": {
        "error": True,
        "error_message": "[error details]",
        "format_version": "2.4.0"
    }
}
```

## Integration with Phase 2.3

### Dependencies
- **Query Processor**: For query type and intent detection
- **Search Engine**: For context retrieval
- **Context Builder**: For assembling relevant context
- **Source Ranker**: For source prioritization

### Data Flow Integration
```
Phase 2.3 Output → Phase 2.4 Input
├── ProcessedQuery → PromptEngine.create_factual_prompt()
├── Context → PromptEngine context parameter
├── SearchResults → Context for LLM
└── RankedSources → ResponseFormatter citations
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Issues**
   - Check environment variable: `OPENAI_API_KEY`
   - Verify API key validity
   - Check API quota and billing

2. **Prompt Engineering Problems**
   - Verify template configuration
   - Check compliance rules
   - Validate prompt length constraints

3. **Response Validation Failures**
   - Check advisory content patterns
   - Verify length limits
   - Review compliance scoring logic

4. **Formatting Issues**
   - Verify required fields
   - Check citation URL format
   - Validate date parsing

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG python src/rag/llm/main.py
```

## Success Criteria

### Technical Success
- All LLM service tests passing
- Prompt engineering working for all query types
- Response validation achieving 100% compliance
- Response formatting producing consistent structure
- Performance targets met (<3.5s total)
- Integration tests passing

### Quality Success
- Zero advisory content in responses
- All responses within length limits
- Proper citations and disclaimers
- Consistent formatting across query types
- Error handling graceful for edge cases

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Integration testing successful
- Results exported successfully
- Monitoring and logging functional

## Next Steps

After completing Phase 2.4:

1. **Review Performance Metrics**: Ensure all targets met
2. **Validate Compliance**: Verify 100% facts-only responses
3. **Test Integration**: Confirm Phase 2.3 integration working
4. **Proceed to Phase 2.5**: Metadata and Source Management
5. **Set up Monitoring**: Implement production monitoring
6. **Document API**: Create API documentation for frontend

This implementation provides a robust LLM integration system that ensures facts-only responses with strict compliance while maintaining high performance and reliability.
