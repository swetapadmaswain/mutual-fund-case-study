# Phase 2.5 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 2.5 - Metadata and Source Management of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. Source Link Management
- **File**: `src/rag/metadata/source_manager.py`
- **Purpose**: Track source URL validity, handle link rot detection, implement source versioning
- **Key Features**:
  - Source URL validation with HTTP status checking
  - Link rot detection and tracking
  - Source versioning with content hashing
  - Performance monitoring and caching
  - Update management and change detection

### 2. Metadata Consistency System
- **File**: `src/rag/metadata/metadata_manager.py`
- **Purpose**: Ensure metadata consistency across chunks, handle updates, manage relationships
- **Key Features**:
  - Schema enforcement and validation
  - Automatic metadata fixing and completion
  - Relationship mapping between chunks
  - Update tracking and history
  - Format validation and normalization

### 3. Citation System
- **File**: `src/rag/metadata/citation_system.py`
- **Purpose**: Generate accurate citations, handle multiple sources, track usage
- **Key Features**:
  - Multiple citation formats (HDFC standard, academic, simple, minimal)
  - Multi-source citation handling
  - Citation format validation
  - Usage tracking and analytics
  - Citation search and filtering

### 4. Version Control System
- **File**: `src/rag/metadata/version_control.py`
- **Purpose**: Track document versions, handle updates, implement rollback capabilities
- **Key Features**:
  - Document version tracking with content hashing
  - Version comparison and diffing
  - Rollback capabilities
  - Version relationships and lineage
  - Change type tracking

### 5. Main Pipeline
- **File**: `src/rag/metadata/main.py`
- **Purpose**: Orchestrate complete Phase 2.5 workflow
- **Key Features**:
  - Component initialization and testing
  - End-to-end workflow validation
  - Performance benchmarking
  - Integration testing
  - Results export and reporting

## Data Flow

```
Sources → Source Management → Metadata Consistency → Citation System → Version Control → Final Output
```

## Key Implementation Details

### Source Management Configuration
```python
# Configuration
check_interval: 24 hours
max_retries: 3
timeout: 10 seconds
user_agent: "MutualFundFAQBot/1.0"

# Performance Targets
source_validation: < 10 seconds for 10 sources
link_rot_detection: < 5 seconds for 100 sources
source_versioning: < 2 seconds for 50 sources
```

### Source Link Management

#### Source Validation Process
```python
# Validation workflow
1. Check cache for existing validation
2. Perform HTTP request with timeout
3. Analyze response status and content
4. Calculate content hash
5. Extract metadata (title, description, etc.)
6. Store validation results
7. Update performance statistics
```

#### Link Rot Detection
```python
# Link rot indicators
- HTTP 4xx/5xx status codes
- Request timeouts
- Connection errors
- Content hash changes
- Redirect loops

# Broken link tracking
{
    "url": "https://broken-site.com",
    "error_type": "http_error",
    "http_status": 404,
    "error_message": "Not Found",
    "last_checked": "2024-01-15T10:30:00Z",
    "retry_count": 3
}
```

#### Source Versioning
```python
# Version creation
version_id = f"v_{document_id}_{timestamp}_{content_hash[:8]}"

# Version tracking
{
    "url": "https://hdfcfund.com",
    "version": "v_doc_20240115_101500_abc12345",
    "timestamp": "2024-01-15T10:15:00Z",
    "content_hash": "abc1234567890",
    "title": "HDFC Mutual Fund Home",
    "metadata": {...},
    "previous_versions": ["v_doc_20240114_101500_def45678"]
}
```

### Metadata Consistency System

#### Schema Definition
```python
# Required fields
required_fields = {
    "chunk_id": str,
    "source_url": str,
    "fund_name": str,
    "content_type": str,
    "document_type": str,
    "last_updated": str,
    "chunk_index": int
}

# Format constraints
format_constraints = {
    "source_url": r"^https?://[^\s/$.?#].[^\s]*$",
    "content_type": r"^(expense_ratio|nav|sip|risk|performance|general|procedural)$",
    "document_type": r"^(factsheet|prospectus|kyc|statement|faq|article)$",
    "last_updated": r"^\d{4}-\d{2}-\d{2}$"
}

# Value constraints
value_constraints = {
    "chunk_index": {"min": 0},
    "confidence_score": {"min": 0.0, "max": 1.0}
}
```

#### Consistency Enforcement
```python
# Automatic fixing process
1. Add missing required fields with defaults
2. Fix format issues (URLs, dates, etc.)
3. Enforce value constraints
4. Normalize categorical values
5. Update relationship mappings

# Default values
defaults = {
    "chunk_id": "",
    "source_url": "",
    "fund_name": "Unknown Fund",
    "content_type": "general",
    "document_type": "article",
    "last_updated": datetime.now().strftime("%Y-%m-%d"),
    "chunk_index": 0
}
```

#### Relationship Mapping
```python
# Relationship types
parent_child: Document hierarchy
siblings: Same fund/content type
cross_references: Related documents
hierarchy_levels: 0=fund, 1=document, 2=content

# Example relationships
{
    "chunk_1": {
        "parent_child": [],
        "siblings": ["chunk_2", "chunk_3"],  # Same fund
        "cross_references": ["chunk_4"],
        "hierarchy_level": 2
    }
}
```

### Citation System

#### Citation Formats
```python
# HDFC Standard format
"HDFC Mutual Fund - {fund_name} ({document_type}). {content_type}. Available at: {source_url}. Last updated: {last_updated}."

# Academic format
"{fund_name} ({document_type}). {content_type}. HDFC Mutual Fund. Retrieved {last_updated} from {source_url}."

# Simple format
"Source: {source_url} (HDFC {fund_name} - {document_type})"

# Minimal format
"{source_url}"
```

#### Multi-Source Handling
```python
# Multi-source citation template
"Multiple sources: {source_url_1}, {source_url_2} and {count-2} more"

# Consolidated metadata
{
    "source_count": 3,
    "individual_citations": ["cite_1", "cite_2", "cite_3"],
    "consolidated_title": "Multiple funds: HDFC Mid Cap, HDFC Equity"
}
```

#### Usage Tracking
```python
# Usage statistics
{
    "total_uses": 15,
    "first_used": "2024-01-15T10:30:00Z",
    "last_used": "2024-01-20T14:45:00Z",
    "query_types": ["factual", "performance"],
    "response_types": ["response"],
    "average_relevance": 0.85
}
```

### Version Control System

#### Document Versioning
```python
# Version creation
version = {
    "version_id": "v_doc_20240115_101500_abc12345",
    "document_id": "doc_1",
    "timestamp": "2024-01-15T10:15:00Z",
    "content_hash": "abc1234567890",
    "metadata_hash": "def4567890123",
    "content_summary": "First 100 characters...",
    "changes_summary": "Document created: Test Document",
    "author": "system",
    "change_type": "create",
    "parent_version": null,
    "child_versions": [],
    "tags": ["initial"],
    "size_bytes": 1024,
    "chunk_count": 5,
    "metadata": {...}
}
```

#### Version Comparison
```python
# Diff result
{
    "version_a": "v_doc_20240115_101500_abc12345",
    "version_b": "v_doc_20240116_101500_def45678",
    "content_changes": ["Content changed", "Size increased by 100 bytes"],
    "metadata_changes": {
        "title": ("Document 1", "Document 1 Updated"),
        "chunk_count": (5, 6)
    },
    "similarity_score": 0.75,
    "change_magnitude": "moderate",
    "diff_summary": "Change magnitude: moderate, Time difference: 24.0 hours"
}
```

#### Rollback Implementation
```python
# Rollback process
1. Identify target version
2. Create rollback version with special marker
3. Link to current version as parent
4. Store rollback metadata
5. Update version lineage

# Rollback version marker
content = "ROLLED_BACK_TO:target_version_id"
tags = ["rollback"]
change_type = "rollback"
```

## Usage Instructions

### Running Phase 2.5

1. **Initialize Components**:
```python
from src.rag.metadata import SourceManager, MetadataManager, CitationSystem, VersionControl

source_manager = SourceManager()
metadata_manager = MetadataManager()
citation_system = CitationSystem()
version_control = VersionControl()
```

2. **Run Pipeline**:
```bash
python src/rag/metadata/main.py
```

### Expected Pipeline Output

```
================================================================================
PHASE 2.5: METADATA AND SOURCE MANAGEMENT
================================================================================

🔹 TESTING SOURCE MANAGEMENT:
  ✅ Source Management: 5 sources validated

🔹 TESTING METADATA CONSISTENCY:
  ✅ Metadata Consistency: 3 chunks processed
     Average consistency score: 0.95

🔹 TESTING CITATION SYSTEM:
  ✅ Citation System: 20 citations generated
     Average confidence: 0.87

🔹 TESTING VERSION CONTROL:
  ✅ Version Control: 2 versions tracked
     Rollback tested: ✅

🔹 TESTING INTEGRATION:
  ✅ Integration: Passed

🔹 PERFORMANCE VALIDATION:
  ✅ Performance: All targets met

🔹 EXPORTING RESULTS:
  ✅ Export: Completed

================================================================================
PHASE 2.5 RESULTS: Metadata and Source Management
================================================================================
Success: ✅
Total Sources: 5
Valid Sources: 4
Broken Links: 1
Metadata Consistency Score: 0.95
Citations Generated: 20
Versions Tracked: 2

📈 COMPONENT TESTS:
Source Management: ✅
Metadata Consistency: ✅
Citation System: ✅
Version Control: ✅
Integration: ✅
Performance: ✅

📊 PERFORMANCE METRICS:
Source Management: 2.3 sources/sec
Metadata Consistency: 15.0 chunks/sec
Citation System: 35.0 citations/sec
Version Control: 12.5 documents/sec

🔧 QUALITY METRICS:
Source Link Accuracy: 80.0%
Metadata Consistency: 95.0%
Citation Confidence: 0.87
Version Tracking: ✅

================================================================================
```

## Configuration Options

### Source Manager
```python
# In src/rag/metadata/source_manager.py
SourceManager(
    cache_dir="cache/source_manager",
    check_interval=timedelta(hours=24),
    max_retries=3,
    timeout=10,
    user_agent="MutualFundFAQBot/1.0"
)
```

### Metadata Manager
```python
# In src/rag/metadata/metadata_manager.py
MetadataManager(
    cache_dir="cache/metadata_manager",
    validation_cache_ttl=timedelta(hours=1),
    max_history_items=1000
)
```

### Citation System
```python
# In src/rag/metadata/citation_system.py
CitationSystem(
    cache_dir="cache/citation_system",
    default_format="hdfc_standard",
    max_citation_length=200,
    confidence_threshold=0.7
)
```

### Version Control
```python
# In src/rag/metadata/version_control.py
VersionControl(
    cache_dir="cache/version_control",
    max_versions_per_document=50,
    similarity_threshold=0.8,
    default_author="system"
)
```

## Performance Metrics

### Target Performance
- **Source Validation**: < 10 seconds for 10 sources
- **Metadata Consistency**: < 5 seconds for 50 chunks
- **Citation Generation**: < 2 seconds for 20 citations
- **Version Tracking**: < 3 seconds for 10 documents
- **Overall Pipeline**: < 20 seconds total

### Monitoring
```python
# Performance validation includes:
- Source validation speed and accuracy
- Metadata consistency processing throughput
- Citation generation efficiency
- Version tracking performance
- Integration testing validation
- Error handling and edge cases
```

## Testing

### Running Tests
```bash
# Run all Phase 2.5 tests
pytest tests/test_metadata.py -v

# Run with coverage
pytest tests/test_metadata.py --cov=src.rag.metadata

# Run specific test class
pytest tests/test_metadata.py::TestSourceManager -v

# Run performance tests
pytest tests/test_metadata.py::TestPerformance -v
```

### Test Coverage
- Source management functionality and error handling
- Metadata consistency validation and fixing
- Citation system formats and usage tracking
- Version control operations and rollback
- End-to-end pipeline integration
- Performance benchmarking and validation

## Success Criteria

### Technical Success
- Source link accuracy > 95%
- Metadata consistency score > 90%
- Citation format compliance 100%
- Version tracking operational
- Performance targets met

### Quality Success
- Source validation reliability > 98%
- Metadata completeness 100%
- Citation confidence > 0.8 on average
- Version comparison accuracy
- Integration testing passing

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Integration testing successful
- Results exported successfully
- Health monitoring functional

## Integration with Phase 2.4

### Dependencies
- **Phase 2.4 LLM Output**: Response citations and metadata
- **Phase 2.3 Retrieval**: Source information and context
- **Phase 2.2 Vector Store**: Document metadata
- **Phase 2.1 Chunking**: Chunk metadata

### Data Flow Integration
```
Phase 2.4 Output → Phase 2.5 Input
├── Formatted Response → Citation Generation
├── Source URLs → Source Validation
├── Response Metadata → Metadata Consistency
├── Document Content → Version Tracking
└── Usage Data → Analytics
```

## Troubleshooting

### Common Issues

1. **Source Validation Failures**
   - Check network connectivity
   - Verify source URLs are accessible
   - Check rate limiting and timeouts

2. **Metadata Consistency Issues**
   - Verify schema configuration
   - Check format constraint patterns
   - Ensure required fields are present

3. **Citation System Problems**
   - Verify citation format templates
   - Check required field mapping
   - Ensure proper URL formatting

4. **Version Control Issues**
   - Check document ID consistency
   - Verify content hash calculation
   - Ensure proper relationship tracking

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG python src/rag/metadata/main.py
```

## Success Criteria

### Technical Success
- All source management tests passing
- Metadata consistency achieving >90% score
- Citation system generating valid formats
- Version control tracking and rollback working
- Performance targets met (<20s total)

### Quality Success
- Source link accuracy >95%
- Metadata completeness 100%
- Citation confidence >0.8 average
- Version comparison accuracy
- Integration testing successful

### Operational Success
- Pipeline completes without errors
- Performance validation passing all criteria
- Integration testing successful
- Results exported successfully
- Health monitoring functional

## Next Steps

After completing Phase 2.5:

1. **Review Performance Metrics**: Ensure all targets met
2. **Validate Data Quality**: Verify source accuracy and metadata consistency
3. **Test Integration**: Confirm Phase 2.4 integration working
4. **Proceed to Phase 2.6**: Performance optimization and testing
5. **Set up Monitoring**: Implement production monitoring
6. **Document API**: Create API documentation for frontend

This implementation provides a robust metadata and source management system that ensures accurate citations, maintains data consistency, tracks document versions, and provides comprehensive analytics for the mutual fund FAQ assistant.
