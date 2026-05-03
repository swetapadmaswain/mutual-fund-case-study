# Phase 3 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 3 - Query Processing and Response Generation of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. Query Classification System
- **File**: `src/rag/query_processing/query_classifier.py`
- **Purpose**: Classifies user queries into different types to determine appropriate response generation strategies
- **Key Features**:
  - Multi-level query classification (FACTUAL, ADVISORY, PERFORMANCE, PROCEDURAL, GENERAL)
  - Pattern-based classification with regex matching
  - Keyword and entity extraction
  - Intent recognition and confidence scoring
  - Query history and statistics tracking

### 2. Response Generation Pipeline
- **File**: `src/rag/query_processing/response_generator.py`
- **Purpose**: Generates appropriate responses based on query classification and retrieved information
- **Key Features**:
  - Type-specific response generation strategies
  - Factual query responses with direct answers
  - Advisory query handling with polite refusal and educational content
  - Performance query responses with links to official documents
  - Procedural query responses with step-by-step guidance
  - Response confidence scoring and validation

### 3. Response Formatting System
- **File**: `src/rag/query_processing/response_formatter.py`
- **Purpose**: Formats responses for different output types and ensures consistent presentation
- **Key Features**:
  - Multiple output formats (JSON, UI, Text, Markdown, HTML)
  - Consistent citation formatting across all formats
  - Template-based formatting with customizable templates
  - Response validation and content length management
  - Format-specific source citation handling

### 4. Compliance and Safety Layer
- **File**: `src/rag/query_processing/compliance_safety.py`
- **Purpose**: Ensures regulatory compliance and safety in query processing and response generation
- **Key Features**:
  - Regulatory compliance checks (investment advice prevention, financial guarantees, etc.)
  - Content safety validation (personal information protection, inappropriate content blocking)
  - Risk assessment with four levels (LOW, MEDIUM, HIGH, CRITICAL)
  - Content filtering and modification capabilities
  - Audit trail maintenance and compliance reporting

### 5. Integration Testing Framework
- **File**: `src/rag/query_processing/integration_tests.py`
- **Purpose**: Provides comprehensive integration testing for the complete query processing pipeline
- **Key Features**:
  - End-to-end pipeline testing with real-world scenarios
  - Performance benchmarking against defined targets
  - Compliance validation across all test scenarios
  - Error handling verification with malformed inputs
  - Load testing simulation for concurrent query handling

### 6. Main Pipeline
- **File**: `src/rag/query_processing/main.py`
- **Purpose**: Orchestrates the complete Phase 3 workflow
- **Key Features**:
  - Component initialization and testing
  - End-to-end workflow validation
  - Performance benchmarking and validation
  - Integration testing and results export
  - Comprehensive reporting and analytics

## Data Flow

```
User Query → Query Classification → Response Generation → Compliance Check → Response Formatting → Final Response
```

## Key Implementation Details

### Query Classification Configuration
```python
# Query types and their characteristics
QueryType.FACTUAL:
  - Examples: "What is the expense ratio?", "What is the minimum SIP amount?"
  - Intent: Get specific factual information
  - Response: Direct answer with sources

QueryType.ADVISORY:
  - Examples: "Should I invest in HDFC?", "Which fund is better?"
  - Intent: Seek investment advice or recommendations
  - Response: Polite refusal + educational content + disclaimer

QueryType.PERFORMANCE:
  - Examples: "What are the historical returns?", "How has it performed?"
  - Intent: Get performance information
  - Response: Link to official factsheet only

QueryType.PROCEDURAL:
  - Examples: "How to start SIP?", "How to download statement?"
  - Intent: Get step-by-step instructions
  - Response: Detailed procedural guidance with sources

QueryType.GENERAL:
  - Examples: "Tell me about HDFC Mutual Fund"
  - Intent: General information request
  - Response: Helpful information with sources
```

### Classification Pattern Matching
```python
# Pattern matching algorithm
def match_patterns(query, patterns):
    matches = []
    
    for pattern in patterns:
        # Check regex patterns
        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, query, re.IGNORECASE):
                matches.append((pattern, 1.0))
        
        # Check keyword matches
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword in query)
        if keyword_matches > 0:
            match_score = keyword_matches / len(pattern.keywords)
            matches.append((pattern, match_score))
        
        # Check entity matches
        entity_matches = sum(1 for entity in pattern.entities if entity in query)
        if entity_matches > 0:
            match_score = entity_matches / len(pattern.entities)
            matches.append((pattern, match_score))
    
    # Sort by score and return best match
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches
```

### Response Generation Strategies
```python
# Response generation by query type
factual_strategy:
  - Extract relevant information from retrieved chunks
  - Format direct answer with confidence scoring
  - Include source citations
  - Validate content accuracy

advisory_strategy:
  - Always refuse to provide investment advice
  - Provide educational information about topic
  - Include disclaimer about not being financial advice
  - Suggest consulting qualified financial advisor

performance_strategy:
  - Never provide performance numbers or comparisons
  - Always link to official factsheet
  - Include source URL for verification
  - Provide general information about performance data

procedural_strategy:
  - Extract step-by-step instructions from chunks
  - Format as numbered or sequential steps
  - Include source citations for each step
  - Validate procedural accuracy
```

### Compliance Rules
```python
# Investment advice prevention
investment_advice_rules = {
    "patterns": [
        r"should.*invest",
        r"recommend.*fund",
        r"best.*fund",
        r"good.*investment"
    ],
    "risk_level": "HIGH",
    "action": "block_or_redirect",
    "allowed_responses": ["educational", "disclaimer"]
}

# Financial guarantee prevention
financial_guarantee_rules = {
    "patterns": [
        r"guaranteed.*return",
        r"sure.*profit",
        r"no.*risk",
        r"safe.*investment"
    ],
    "risk_level": "CRITICAL",
    "action": "block",
    "allowed_responses": []
}
```

### Response Formatting Templates
```python
# UI format template
ui_template = {
    "factual": "Answer: {content}\n\nSources: {sources}\n\nConfidence: {confidence:.1%}",
    "advisory": "Response: {content}\n\n⚠️ Disclaimer: This is not investment advice.",
    "performance": "Information: {content}\n\nSource: {sources}",
    "procedural": "Instructions: {content}\n\nSources: {sources}"
}

# Markdown format template
markdown_template = {
    "factual": "## Answer\n{content}\n\n### Sources\n{sources}\n\n**Confidence:** {confidence:.1%}",
    "advisory": "## Response\n{content}\n\n> ⚠️ **Disclaimer:** This is not investment advice.",
    "performance": "## Information\n{content}\n\n### Source\n{sources}",
    "procedural": "## Instructions\n{content}\n\n### Sources\n{sources}"
}
```

### Integration Testing Scenarios
```python
# Test query definitions
test_queries = [
    TestQuery(
        query_id="factual_1",
        query="What is the expense ratio of HDFC Mid Cap Fund?",
        expected_type=QueryType.FACTUAL,
        expected_intent="get_expense_ratio",
        expected_response_type="factual",
        test_category="factual",
        priority="high"
    ),
    TestQuery(
        query_id="advisory_1",
        query="Should I invest in HDFC Mid Cap Fund?",
        expected_type=QueryType.ADVISORY,
        expected_intent="provide_investment_advice",
        expected_response_type="advisory",
        test_category="advisory",
        priority="high"
    )
]
```

## Usage Instructions

### Running Phase 3

1. **Initialize Components**:
```python
from src.rag.query_processing import (
    QueryClassifier, ResponseGenerator, 
    ResponseFormatter, ComplianceSafetyLayer
)

query_classifier = QueryClassifier()
response_generator = ResponseGenerator()
response_formatter = ResponseFormatter()
compliance_safety = ComplianceSafetyLayer()
```

2. **Run Pipeline**:
```bash
python src/rag/query_processing/main.py
```

### Expected Pipeline Output

```
================================================================================
PHASE 3: QUERY PROCESSING AND RESPONSE GENERATION
================================================================================

🔹 TESTING QUERY CLASSIFICATION:
  ✅ Query Classification: 95.0% accuracy

🔹 TESTING RESPONSE GENERATION:
  ✅ Response Generation: 92.5% success

🔹 TESTING RESPONSE FORMATTING:
  ✅ Response Formatting: 5/5 formats

🔹 TESTING COMPLIANCE AND SAFETY:
  ✅ Compliance Safety: 88.0% approval rate

🔹 TESTING INTEGRATION:
  ✅ Integration: Passed

🔹 PERFORMANCE VALIDATION:
  ✅ Performance: All targets met

🔹 EXPORTING RESULTS:
  ✅ Export: Completed

================================================================================
PHASE 3 RESULTS: Query Processing and Response Generation
================================================================================
Success: ✅
Query Classification Accuracy: 95.0%
Response Generation Success: 92.5%
Compliance Approval Rate: 88.0%
Formatting Coverage: 100.0%
Integration Test Success: 100.0%

📈 COMPONENT TESTS:
Query Classification: ✅
Response Generation: ✅
Response Formatting: ✅
Compliance Safety: ✅
Integration: ✅
Performance: ✅

📊 PERFORMANCE METRICS:
Classification Processing: 0.085s
Generation Processing: 0.750s
Formatting Processing: 0.008s
Overall Pipeline: 1.250s

🔧 QUALITY METRICS:
Classification Accuracy: 95.0%
Generation Success Rate: 92.5%
Compliance Approval: 88.0%
Format Coverage: 100.0%
Integration Success: 100.0%

================================================================================
```

## Configuration Options

### Query Classifier
```python
# In src/rag/query_processing/query_classifier.py
QueryClassifier(
    cache_dir="cache/query_classifier",
    monitoring_interval=5.0,
    confidence_threshold=0.7
)
```

### Response Generator
```python
# In src/rag/query_processing/response_generator.py
ResponseGenerator(
    cache_dir="cache/response_generator",
    max_response_length=500,
    confidence_threshold=0.7,
    max_sources=3
)
```

### Response Formatter
```python
# In src/rag/query_processing/response_formatter.py
ResponseFormatter(
    cache_dir="cache/response_formatter",
    max_content_length=1000,
    default_format=OutputFormat.JSON
)
```

### Compliance Safety Layer
```python
# In src/rag/query_processing/compliance_safety.py
ComplianceSafetyLayer(
    cache_dir="cache/compliance_safety",
    max_risk_level=RiskLevel.HIGH,
    auto_approve_threshold=RiskLevel.MEDIUM
)
```

## Performance Metrics

### Target Performance
- **Query Classification**: < 100ms per query
- **Response Generation**: < 1 second per response
- **Response Formatting**: < 10ms per format
- **Compliance Check**: < 50ms per check
- **Overall Pipeline**: < 3 seconds total
- **Concurrent Queries**: > 100 QPS

### Monitoring
```python
# Performance validation includes:
- Query classification accuracy > 95%
- Response generation success > 90%
- Compliance approval rate > 85%
- Format coverage = 100%
- Integration testing success = 100%
- Error handling rate < 5%
```

## Testing

### Running Tests
```bash
# Run all Phase 3 tests
pytest tests/test_query_processing.py -v

# Run with coverage
pytest tests/test_query_processing.py --cov=src.rag.query_processing

# Run specific test class
pytest tests/test_query_processing.py::TestQueryClassifier -v

# Run performance tests
pytest tests/test_query_processing.py::TestPerformance -v
```

### Test Coverage
- Query classification functionality and accuracy
- Response generation strategies and validation
- Response formatting across all output types
- Compliance and safety rule enforcement
- Integration testing and workflow validation
- Performance benchmarking and validation
- Error handling and edge cases

## Success Criteria

### Technical Success
- All query types classified with >95% accuracy
- Response generation success >90%
- Compliance approval rate >85%
- All output formats working correctly
- Performance targets met (<3s total)
- Integration testing passing 100%

### Quality Success
- Query classification accuracy >95%
- Response content quality and relevance
- Compliance enforcement 100% for critical rules
- Format consistency across all output types
- Error handling robust and graceful

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Integration testing successful
- Results exported successfully
- Health monitoring functional
- Audit trail maintained

## Integration with Previous Phases

### Dependencies
- **Phase 2.5 Metadata**: Source information for citations
- **Phase 2.4 LLM**: Response generation capabilities
- **Phase 2.3 Retrieval**: Search results for context
- **Phase 2.2 Vector Store**: Document metadata
- **Phase 2.1 Chunking**: Content for responses

### Data Flow Integration
```
Previous Phases → Phase 3 Input
├── Phase 2.5 Metadata → Source Citations
├── Phase 2.4 LLM → Enhanced Response Generation
├── Phase 2.3 Retrieval → Context for Responses
├── Phase 2.2 Vector Store → Document Information
├── Phase 2.1 Chunking → Content Base
└── All Phases → End-to-End Query Processing
```

## Troubleshooting

### Common Issues

1. **Query Classification Errors**
   - Check pattern definitions in classifier
   - Verify regex patterns are correctly formatted
   - Ensure keyword and entity lists are comprehensive

2. **Response Generation Issues**
   - Verify response templates are properly configured
   - Check context data from retrieval phase
   - Ensure confidence thresholds are appropriate

3. **Compliance Violations**
   - Review compliance rule definitions
   - Check for false positives in pattern matching
   - Verify risk level assignments

4. **Formatting Problems**
   - Check template syntax and placeholders
   - Verify format-specific requirements
   - Ensure content length limits are reasonable

5. **Integration Failures**
   - Verify component initialization order
   - Check data flow between components
   - Ensure all dependencies are available

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG python src/rag/query_processing/main.py
```

## Success Criteria

### Technical Success
- Query classification accuracy >95%
- Response generation success >90%
- Compliance approval rate >85%
- Format coverage 100%
- Performance targets met (<3s total)
- Integration testing successful

### Quality Success
- Query classification accuracy >95%
- Response content quality and relevance
- Compliance enforcement 100% for critical rules
- Format consistency across all output types
- Error handling robust and graceful

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Integration testing successful
- Results exported successfully
- Health monitoring functional
- Audit trail maintained

## Next Steps

After completing Phase 3:

1. **Review Performance Metrics**: Ensure all targets met
2. **Validate Query Classification**: Verify >95% accuracy
3. **Test Compliance Enforcement**: Confirm proper rule enforcement
4. **Verify Integration**: Check end-to-end workflow
5. **Set Up Monitoring**: Deploy production monitoring
6. **Create User Documentation**: Provide user-facing documentation

This implementation provides a robust query processing and response generation system that accurately classifies user queries, generates appropriate responses with proper compliance enforcement, formats output consistently, and maintains comprehensive audit trails for regulatory compliance.
