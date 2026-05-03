# Phase 2.3 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 2.3 - Retrieval System Development of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. Query Processing Module
- **File**: `src/rag/retrieval/query_processor.py`
- **Purpose**: Clean, optimize, and classify user queries
- **Key Features**:
  - Text preprocessing and normalization
  - Entity extraction (fund names, financial terms, amounts)
  - Query type classification (factual, advisory, performance, procedural)
  - Intent determination (expense_ratio, nav, sip, etc.)
  - Filter generation for vector database
  - Confidence scoring and batch processing

### 2. Semantic Search Engine
- **File**: `src/rag/retrieval/search_engine.py`
- **Purpose**: Implement semantic similarity search with multiple strategies
- **Key Features**:
  - Multiple search strategies (semantic, hybrid, fund-focused, content-focused)
  - Similarity threshold configuration
  - Result ranking and re-ranking
  - Multi-strategy search combination
  - Performance optimization and caching

### 3. Context Builder
- **File**: `src/rag/retrieval/context_builder.py`
- **Purpose**: Assemble relevant context from search results
- **Key Features**:
  - Multiple context building strategies (relevance-first, chronological, fund-grouped)
  - Token window management (4000 tokens max)
  - Coherence maintenance across windows
  - Source citation preservation
  - Context window limitations handling

### 4. Source Ranking System
- **File**: `src/rag/retrieval/source_ranker.py`
- **Purpose**: Prioritize official sources and rank search results
- **Key Features**:
  - Multi-criteria ranking (relevance, quality, recency, authority)
  - Official source prioritization
  - Source authority classification
  - Ranking score breakdown and analysis
  - Coverage and completeness assessment

### 5. Main Pipeline
- **File**: `src/rag/retrieval/main.py`
- **Purpose**: Orchestrate the complete Phase 2.3 pipeline
- **Key Features**:
  - Step-by-step execution with validation
  - Performance testing and metrics
  - Integration testing between components
  - Configuration export and management
  - End-to-end retrieval validation

## Data Flow

```
User Query → Query Processing → Semantic Search → Source Ranking → Context Building → LLM-Ready Context
```

## Key Implementation Details

### Query Processing Configuration
```python
# Query type classification
QueryType: {
    FACTUAL = "factual"
    ADVISORY = "advisory" 
    PERFORMANCE = "performance"
    PROCEDURAL = "procedural"
    GENERAL = "general"
}

# Intent determination
QueryIntent: {
    EXPENSE_RATIO = "expense_ratio"
    EXIT_LOAD = "exit_load"
    NAV = "nav"
    SIP = "sip"
    AUM = "aum"
    RISK = "risk"
    BENCHMARK = "benchmark"
    PERFORMANCE_RETURNS = "performance_returns"
    INVESTMENT_OBJECTIVE = "investment_objective"
    FUND_COMPARISON = "fund_comparison"
    INVESTMENT_GUIDANCE = "investment_guidance"
    PROCEDURAL_HELP = "procedural_help"
    GENERAL_INFO = "general_info"
}
```

### Search Engine Strategies
```python
# Search strategies
SearchStrategy: {
    SEMANTIC = "semantic"           # Basic semantic search
    HYBRID = "hybrid"              # Combine multiple strategies
    FUND_FOCUSED = "fund_focused"  # Search within specific funds
    CONTENT_FOCUSED = "content_focused"  # Search by content type
    TYPE_FOCUSED = "type_focused"  # Search by fund type
}

# Search configuration
similarity_threshold: 0.7
max_results: 5
enable_hierarchical_search: true
enable_result_reranking: true
```

### Context Building Strategies
```python
# Context building approaches
strategies: {
    relevance_first: "Prioritize most relevant results"
    chronological: "Order by recency"
    fund_grouped: "Group by fund name"
    content_grouped: "Group by content type"
    hybrid: "Combine multiple approaches"
}

# Token management
max_context_tokens: 4000
window_overlap_tokens: 100
min_relevance_threshold: 0.5
```

### Source Ranking Criteria
```python
# Ranking criteria weights
RankingCriteria: {
    RELEVANCE: 0.4      # Query-match relevance
    QUALITY: 0.2        # Content quality
    RECENCY: 0.15       # Content freshness
    COMPLETENESS: 0.1   # Metadata completeness
    AUTHORITY: 0.1      # Source credibility
    COVERAGE: 0.05      # Query coverage
}

# Authority levels
authority_weights: {
    official: 1.0,      # Official fund sites
    primary: 0.9,        # Primary financial platforms
    secondary: 0.7,      # Secondary financial sites
    general: 0.5         # General information sites
}
```

## Usage Instructions

### Running Phase 2.3

1. **Ensure Phase 2.2 data is available**
```bash
# Vector database should be at:
cache/vector_db/mutual_fund_chunks

# Hierarchical index should be at:
cache/hierarchical_index/hierarchical_index.json
```

2. **Install required dependencies**
```bash
pip install numpy scikit-learn
```

3. **Run the pipeline**
```bash
python src/rag/retrieval/main.py
```

### Expected Pipeline Output

```
================================================================================
PHASE 2.3 RESULTS: Retrieval System Development
================================================================================
Success: ✅
Duration: 45.67 seconds

📊 STEP RESULTS:

🔹 INITIALIZATION:
  Success: ✅
  vector_database: {'collection_name': 'mutual_fund_chunks', 'document_count': 23}
  hierarchical_index: {'total_funds': 5, 'fund_types': ['mid_cap', 'large_cap']}
  embedding_service: {'model_name': 'BAAI/bge-small-en', 'cache_enabled': True}

🔹 QUERY PROCESSING:
  validation_results: {
    'total_queries': 8,
    'successful_processing': 8,
    'average_confidence': 0.82,
    'entity_coverage': 0.75
  }
  Success: ✅

🔹 SEARCH ENGINE:
  strategy_results: {
    'semantic': {'results_count': 5, 'average_similarity': 0.85},
    'fund_focused': {'results_count': 3, 'average_similarity': 0.88},
    'content_focused': {'results_count': 4, 'average_similarity': 0.83}
  }
  Success: ✅

🔹 CONTEXT BUILDER:
  strategy_results: {
    'relevance_first': {'total_tokens': 1850, 'context_windows': 5},
    'fund_grouped': {'total_tokens': 1920, 'context_windows': 4},
    'hybrid': {'total_tokens': 2100, 'context_windows': 6}
  }
  Success: ✅

🔹 SOURCE RANKING:
  ranking_summary: {
    'total_sources': 3,
    'average_score': 0.78,
    'authority_distribution': {'official': 2, 'primary': 1}
  }
  Success: ✅

🔹 END TO END:
  overall_statistics: {
    'total_queries_tested': 5,
    'successful_queries': 5,
    'success_rate': 1.0,
    'average_processing_time': 0.23
  }
  Success: ✅

🔹 PERFORMANCE VALIDATION:
  overall_performance: {
    'all_requirements_met': True,
    'query_processing_ok': True,
    'search_ok': True,
    'context_building_ok': True
  }
  Success: ✅

🔹 INTEGRATION TESTING:
  component_integration: {'query_to_search': True, 'search_to_ranking': True}
  data_flow_validation: {'data_flow_consistent': True}
  error_handling: {'graceful_handling': True}
  Success: ✅

🔹 EXPORT:
  configuration_exported: True
  results_exported: True
  Success: ✅

📈 FINAL SUMMARY:
  Components Configured: 4
  Performance Targets:
    Query Processing Time: < 1 second
    Search Time: < 0.5 seconds
    Context Time: < 0.5 seconds
    Retrieval Accuracy: > 90%
  Integration Status:
    Phase22 Integration: complete
    Component Integration: tested
    Data Flow Validation: passed
    Error Handling: validated

================================================================================
```

## Configuration Options

### Query Processor
```python
# In src/rag/retrieval/query_processor.py
QueryProcessor()
# Configured with:
- Entity patterns for fund names, financial terms, amounts
- Query type classification patterns
- Intent determination patterns
- Confidence scoring algorithm
```

### Search Engine
```python
# In src/rag/retrieval/search_engine.py
SemanticSearchEngine(
    vector_database=vector_db,
    embedding_service=embedding_service,
    hierarchical_db=hierarchical_db
)
# Configured with:
- Similarity threshold: 0.7
- Max results: 5
- Multiple search strategies
- Result re-ranking enabled
```

### Context Builder
```python
# In src/rag/retrieval/context_builder.py
ContextBuilder(
    max_context_tokens=4000,
    window_overlap_tokens=100,
    min_relevance_threshold=0.5
)
# Configured with:
- Multiple building strategies
- Token management
- Coherence maintenance
- Source citation preservation
```

### Source Ranker
```python
# In src/rag/retrieval/source_ranker.py
SourceRanker()
# Configured with:
- Official domain prioritization
- Multi-criteria ranking
- Authority classification
- Quality assessment
```

## Performance Metrics

### Target Performance
- **Query Processing Time**: < 1 second
- **Search Time**: < 0.5 seconds
- **Context Building Time**: < 0.5 seconds
- **Retrieval Accuracy**: > 90%
- **Source Ranking Quality**: > 0.7 average score

### Monitoring
```python
# Performance validation includes:
- Query processing speed
- Search latency measurement
- Context building efficiency
- Source ranking accuracy
- End-to-end retrieval time
- Integration testing validation
```

## Testing

### Running Tests
```bash
# Run all Phase 2.3 tests
pytest tests/test_retrieval.py -v

# Run with coverage
pytest tests/test_retrieval.py --cov=src.rag.retrieval

# Run specific test class
pytest tests/test_retrieval.py::TestQueryProcessor -v

# Run integration tests
pytest tests/test_retrieval.py::TestIntegration -v
```

### Test Coverage
- Query processing functionality
- Semantic search engine operations
- Context building strategies
- Source ranking algorithms
- End-to-end integration testing
- Performance validation
- Error handling and edge cases

## Troubleshooting

### Common Issues

1. **Query Processing Failures**
   - Check entity pattern configurations
   - Verify query type classification patterns
   - Ensure proper text normalization

2. **Search Engine Issues**
   - Verify vector database connection
   - Check embedding service availability
   - Validate similarity thresholds

3. **Context Building Problems**
   - Check token limit configurations
   - Verify search result relevance
   - Ensure proper source citation

4. **Source Ranking Issues**
   - Verify authority domain configurations
   - Check ranking criteria weights
   - Ensure proper metadata extraction

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG python src/rag/retrieval/main.py
```

## Integration with Phase 2.4

### Output Format
Phase 2.3 produces LLM-ready context:
```json
{
  "query": {
    "original": "What is the expense ratio of HDFC Mid Cap Fund?",
    "type": "factual",
    "intent": "expense_ratio",
    "confidence": 0.85
  },
  "context": {
    "text": "HDFC Mid Cap Fund has expense ratio of 0.85%...",
    "tokens": 1850,
    "sources": [
      {
        "fund_name": "HDFC Mid Cap Fund",
        "source_url": "https://groww.in/funds/hdfc-mid-cap",
        "relevance_score": 0.9
      }
    ]
  },
  "retrieval_metadata": {
    "search_strategy": "fund_focused",
    "processing_time": 0.23,
    "ranking_score": 0.78
  }
}
```

### Next Steps
After completing Phase 2.3:
1. Review retrieval performance metrics
2. Validate query classification accuracy
3. Test with various query types
4. Proceed to Phase 2.4 (LLM Integration and Prompt Engineering)
5. Set up LLM service integration
6. Implement response generation pipeline

## Success Criteria

### Technical Success
- All query types correctly classified
- Search strategies working for all query types
- Context building within token limits
- Source ranking prioritizing official sources
- Performance targets met (<1s total processing)

### Quality Success
- Query confidence scores > 0.7 on average
- Search relevance scores > 0.8 on average
- Context coherence maintained across windows
- Source authority correctly identified
- Integration testing passing all components

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Configuration exported successfully
- Error handling graceful for edge cases
- Monitoring and logging functional

This implementation provides a robust retrieval system foundation for Phase 2.4 (LLM Integration) with high-quality query processing, semantic search, and context building capabilities.
