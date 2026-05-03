# Phase 2.2 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 2.2 - Vector Store Setup and Configuration of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. Embedding Model Integration
- **File**: `src/rag/vector_store/embeddings.py`
- **Purpose**: Generate embeddings using sentence-transformers models
- **Key Features**:
  - Support for BGE-Small-EN model (384 dimensions)
  - Batch embedding processing with configurable batch size
  - Embedding caching for performance optimization
  - Text preprocessing and normalization
  - Model loading and configuration management

### 2. Vector Database Setup
- **File**: `src/rag/vector_store/vector_database.py`
- **Purpose**: ChromaDB-based vector storage and retrieval
- **Key Features**:
  - Persistent vector storage with ChromaDB
  - Hierarchical vector database with fund-specific organization
  - Metadata filtering and search capabilities
  - Collection management and statistics
  - Backup and restore functionality

### 3. Hierarchical Indexing System
- **File**: `src/rag/vector_store/hierarchical_indexing.py`
- **Purpose**: Organize and index data by fund hierarchy
- **Key Features**:
  - Fund hierarchy creation (fund → type → content)
  - Query routing based on fund, type, or content
  - Metadata filter configuration
  - Index structure optimization
  - Fund statistics and analysis

### 4. Storage Optimization
- **File**: `src/rag/vector_store/storage_optimizer.py`
- **Purpose**: Optimize storage efficiency and management
- **Key Features**:
  - Vector compression using PCA
  - Vector quantization (8/16/32 bit)
  - File compression with gzip
  - Backup procedures and retention policies
  - Storage usage monitoring

### 5. Main Pipeline
- **File**: `src/rag/vector_store/main.py`
- **Purpose**: Orchestrate the complete Phase 2.2 pipeline
- **Key Features**:
  - Step-by-step execution with error handling
  - Performance validation and metrics
  - Configuration export and management
  - Integration with Phase 2.1 data

## Data Flow

```
Phase 2.1 Chunks → Embedding Generation → Vector Storage → Hierarchical Indexing → Query Routing → Performance Validation
```

## Key Implementation Details

### Embedding Model Configuration
```python
# BGE-Small-EN model settings
model_name: "BAAI/bge-small-en"
embedding_dimension: 384
device: "cpu"
batch_size: 32
cache_enabled: true
```

### Vector Database Setup
```python
# ChromaDB configuration
collection_name: "mutual_fund_chunks"
persist_directory: "cache/vector_db"
embedding_dimension: 384
hierarchical_indexing: true
```

### Hierarchical Structure
```python
# Fund hierarchy levels
fund: "hdfc_mid_cap_fund"
type: "mid_cap"
content: "expense_ratio"
document: "doc_12345"
chunk: "chunk_0"
```

### Storage Optimization
```python
# Compression settings
vector_compression_ratio: 0.8
quantization_bits: 16
file_compression_threshold: 100MB
backup_retention_days: 30
```

## Usage Instructions

### Running Phase 2.2

1. **Ensure Phase 2.1 data is available**
```bash
# Phase 2.1 data should be at:
cache/phase2_1_results/enriched_chunks.json
```

2. **Install required dependencies**
```bash
pip install sentence-transformers chromadb scikit-learn
```

3. **Run the pipeline**
```bash
python src/rag/vector_store/main.py
```

### Expected Pipeline Output

```
================================================================================
PHASE 2.2 RESULTS: Vector Store Setup and Configuration
================================================================================
Success: ✅
Duration: 125.45 seconds

📊 STEP RESULTS:

🔹 DATA LOADING:
  chunks_loaded: 23
  Success: ✅

🔹 EMBEDDING GENERATION:
  chunks_processed: 23
  embeddings_generated: 23
  embedding_dimension: 384
  model_info: {'model_name': 'BAAI/bge-small-en', 'cache_enabled': True}
  Success: ✅

🔹 VECTOR STORAGE:
  documents_stored: 23
  collection_name: mutual_fund_chunks
  embedding_dimension: 384
  Success: ✅

🔹 HIERARCHICAL INDEXING:
  funds_indexed: 5
  fund_types: ['mid_cap', 'large_cap', 'equity', 'elss', 'focused']
  content_types: ['expense_ratio', 'nav', 'sip', 'risk', 'benchmark']
  total_documents: 5
  Success: ✅

🔹 HIERARCHICAL DB SETUP:
  total_funds: 5
  fund_types: ['mid_cap', 'large_cap', 'equity', 'elss', 'focused']
  total_documents: 5
  Success: ✅

🔹 METADATA FILTERS:
  fund_filters_count: 5
  type_filters_count: 5
  content_filters_count: 5
  combined_filters_count: 15
  Success: ✅

🔹 STORAGE OPTIMIZATION:
  backup_configured: True
  retention_configured: True
  compression_enabled: True
  Success: ✅

🔹 QUERY ROUTING TEST:
  queries_tested: 4
  routing_results: [
    {'query': 'HDFC Mid Cap Fund expense ratio', 'query_type': 'fund_specific'},
    {'query': 'HDFC Large Cap Fund SIP details', 'query_type': 'fund_specific'},
    {'query': 'Risk level of ELSS funds', 'query_type': 'content_specific'},
    {'query': 'General mutual fund information', 'query_type': 'general'}
  ]
  Success: ✅

🔹 PERFORMANCE VALIDATION:
  query_latency_test: {'query_time_ms': 45.2, 'meets_requirement': True}
  storage_efficiency_test: {'storage_efficiency': 0.85, 'meets_requirement': True}
  index_structure_test: {'funds_indexed': 5, 'meets_requirement': True}
  overall_performance: {'all_requirements_met': True}
  Success: ✅

🔹 EXPORT:
  configuration_exported: True
  results_exported: True
  Success: ✅

📈 FINAL SUMMARY:
  Chunks Processed: 23
  Embeddings Generated: 23
  Documents Stored: 23
  Collection: mutual_fund_chunks
  Document Count: 23
  Embedding Dimension: 384
  Funds Indexed: 5
  Fund Types: 5
  Content Types: 5
  Model: BAAI/bge-small-en
  Cache Enabled: True
  Storage Size: 12.3MB
  Compression: ✅
  Backup: ✅

================================================================================
```

## Configuration Options

### Embedding Model
```python
# In src/rag/vector_store/embeddings.py
EmbeddingService(
    model_name="BAAI/bge-small-en",    # Alternative: "all-MiniLM-L6-v2"
    device="cpu",                      # Alternative: "cuda"
    batch_size=32,                     # Adjust based on memory
    enable_cache=True                  # Enable for performance
)
```

### Vector Database
```python
# In src/rag/vector_store/vector_database.py
VectorDatabase(
    collection_name="mutual_fund_chunks",
    persist_directory="cache/vector_db",
    embedding_dimension=384            # Must match model
)
```

### Hierarchical Indexing
```python
# In src/rag/vector_store/hierarchical_indexing.py
HierarchicalIndexer(
    index_path="cache/hierarchical_index"
)
```

### Storage Optimization
```python
# In src/rag/vector_store/storage_optimizer.py
StorageOptimizer(
    storage_path="cache/vector_storage",
    compression_enabled=True,
    backup_enabled=True
)
```

## Performance Metrics

### Target Performance
- **Query Latency**: < 100ms for vector search
- **Storage Efficiency**: > 80% compression ratio
- **Index Coverage**: 100% fund and content type coverage
- **Cache Hit Rate**: > 70% for repeated queries

### Monitoring
```python
# Performance validation includes:
- Query latency measurement
- Storage efficiency calculation
- Index structure validation
- Cache performance analysis
```

## Testing

### Running Tests
```bash
# Run all Phase 2.2 tests
pytest tests/test_vector_store.py -v

# Run with coverage
pytest tests/test_vector_store.py --cov=src.rag.vector_store

# Run specific test class
pytest tests/test_vector_store.py::TestEmbeddingModel -v
```

### Test Coverage
- Embedding model functionality
- Vector database operations
- Hierarchical indexing logic
- Storage optimization features
- Integration testing
- Performance validation

## Troubleshooting

### Common Issues

1. **Model Loading Failures**
   - Ensure sentence-transformers is installed
   - Check internet connection for model download
   - Verify sufficient disk space for model cache

2. **ChromaDB Connection Issues**
   - Check directory permissions
   - Ensure sufficient disk space for vector storage
   - Verify embedding dimension compatibility

3. **Memory Issues**
   - Reduce batch size for embedding generation
   - Enable vector compression
   - Monitor system memory usage

4. **Performance Issues**
   - Enable embedding caching
   - Optimize batch sizes
   - Check storage optimization settings

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG python src/rag/vector_store/main.py
```

## Integration with Phase 2.3

### Output Format
Phase 2.2 produces a ready-to-use vector database:
```json
{
  "vector_database": {
    "collection_name": "mutual_fund_chunks",
    "document_count": 23,
    "embedding_dimension": 384
  },
  "hierarchical_indexing": {
    "total_funds": 5,
    "fund_types": ["mid_cap", "large_cap"],
    "content_types": ["expense_ratio", "nav", "sip"]
  },
  "query_routing": {
    "fund_specific": "fund_focused search",
    "content_specific": "content_focused search",
    "general": "semantic search"
  }
}
```

### Next Steps
After completing Phase 2.2:
1. Review vector database statistics
2. Validate query routing performance
3. Proceed to Phase 2.3 (Retrieval System Development)
4. Set up semantic search engine
5. Implement context builder

## Success Criteria

### Technical Success
- All Phase 2.1 chunks successfully embedded
- Vector database operational with ChromaDB
- Hierarchical indexing covering all funds and content types
- Query latency < 100ms
- Storage efficiency > 80%

### Quality Success
- Embeddings generated with BGE-Small-EN model
- Hierarchical structure properly organized
- Metadata filters configured for all levels
- Query routing working for all query types
- Performance validation passing all criteria

### Operational Success
- Pipeline completes without errors
- Results exported successfully
- Backup procedures configured
- Storage optimization applied
- Monitoring and logging functional

This implementation provides a robust vector storage foundation for Phase 2.3 (Retrieval System Development) with high-performance search capabilities and efficient storage management.
