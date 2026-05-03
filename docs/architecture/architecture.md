# Mutual Fund FAQ Assistant - Complete Architecture Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Phase 1: Foundation and Data Collection](#phase-1-foundation-and-data-collection)
3. [Phase 2: RAG System Implementation](#phase-2-rag-system-implementation)
4. [Phase 3: Query Processing and Response Generation](#phase-3-query-processing-and-response-generation)
5. [Phase 4: User Interface Development](#phase-4-user-interface-development)
6. [Phase 5: Integration and Testing](#phase-5-integration-and-testing)
7. [Phase 6: Deployment and Documentation](#phase-6-deployment-and-documentation)
8. [GitHub Actions Integration](#github-actions-integration)
9. [Technical Architecture Details](#technical-architecture-details)
10. [Success Metrics and Risk Mitigation](#success-metrics-and-risk-mitigation)

---

## Project Overview

This document outlines the complete architecture for building a facts-only mutual fund FAQ assistant using a Retrieval-Augmented Generation (RAG) approach with HDFC Mutual Fund data.

### Key Objectives
- **Facts-Only Responses**: Strict compliance with no investment advice
- **Official Sources**: Only HDFC Mutual Fund and Groww platform data
- **High Accuracy**: >95% factual correctness rate
- **Fast Response**: <3 seconds for most queries
- **Automated Updates**: Daily data synchronization

---

## Phase 1: Foundation and Data Collection (Week 1-2)

### 1.1 Environment Setup
- **Development Environment**: Python 3.9+ with virtual environment
- **Core Dependencies**: 
  - `langchain` for RAG framework
  - `chromadb` or `faiss-cpu` for vector storage
  - `sentence-transformers` for embeddings
  - `streamlit` or `flask` for UI
  - `beautifulsoup4` and `requests` for web scraping
  - `python-dotenv` for environment variables

### 1.2 Source Selection and Corpus Building
- **AMC Selection**: HDFC Mutual Fund
- **Scheme Selection**: 5 diverse schemes from Groww platform
  - HDFC Mid-Cap Fund (Direct Growth)
  - HDFC Equity Fund (Direct Growth)
  - HDFC Focused Fund (Direct Growth)
  - HDFC ELSS Tax Saver Fund (Direct Plan Growth)
  - HDFC Large-Cap Fund (Direct Growth)
- **Source URLs Collection**: 5 primary sources
  - https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
  - https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
  - https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth
  - https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
  - https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth

### 1.3 Data Ingestion Pipeline
```python
# Core components
- DocumentLoader: Fetch and parse web content
- ContentCleaner: Extract relevant text, remove noise
- MetadataExtractor: Extract scheme names, dates, document types
- SourceValidator: Verify official source authenticity
```

---

## Phase 2: RAG System Implementation (Week 3-4)

### Phase 2.1: Document Processing and Chunking (Week 3, Days 1-2)

#### Objective
Process Phase 1 collected data and create optimal chunks for vector storage.

#### Implementation Steps

**Step 2.1.1: Text Preprocessing Module**
**File**: `src/rag/document_processor.py`
- Clean HTML artifacts and normalize text
- Handle special characters and financial symbols
- Preserve important formatting (percentages, amounts)
- Remove noise and irrelevant content

**Key Components**:
```python
class TextPreprocessor:
    def clean_text(self, raw_content: str) -> str
    def normalize_financial_symbols(self, text: str) -> str
    def remove_noise(self, text: str) -> str
    def preserve_structure(self, text: str) -> str
```

**Step 2.1.2: Semantic Chunking Strategy**
**File**: `src/rag/chunker.py`
- Implement semantic chunking (500-800 tokens)
- Create overlapping chunks (200 token overlap)
- Preserve context boundaries
- Handle table structures

**Key Components**:
```python
class SemanticChunker:
    def create_chunks(self, text: str, metadata: dict) -> List[Chunk]
    def preserve_context(self, chunks: List[Chunk]) -> List[Chunk]
    def handle_tables(self, text: str) -> List[Chunk]
    def optimize_chunk_size(self, chunks: List[Chunk]) -> List[Chunk]
```

**Step 2.1.3: Metadata Enrichment**
**File**: `src/rag/metadata_enricher.py`
- Extract and preserve source metadata
- Add chunk-level metadata
- Create hierarchical indexing keys
- Maintain citation information

**Key Components**:
```python
class MetadataEnricher:
    def enrich_chunk_metadata(self, chunk: Chunk, source_metadata: dict) -> Chunk
    def create_hierarchical_keys(self, chunk: Chunk) -> str
    def preserve_citations(self, chunk: Chunk) -> Chunk
```

**Success Criteria**:
- All Phase 1 data successfully chunked
- Average chunk size: 500-800 tokens
- Context preservation > 90%
- Zero data loss during chunking

### Phase 2.2: Vector Store Setup and Configuration (Week 3, Days 3-4)

#### Objective
Set up vector database infrastructure for efficient storage and retrieval.

#### Implementation Steps

**Step 2.2.1: Embedding Model Integration**
**File**: `src/rag/embeddings.py`
- Integrate `sentence-transformers` model (BGE-Small-EN preferred)
- Implement batch embedding processing
- Handle embedding failures and retries
- Cache embeddings for performance

**Key Components**:
```python
class EmbeddingManager:
    def __init__(self, model_name: str = "BAAI/bge-small-en")
    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]
    def batch_process(self, chunks: List[Chunk], batch_size: int = 32)
    def cache_embeddings(self, embeddings: List[Embedding])
```

**Step 2.2.2: ChromaDB Configuration**
**File**: `src/rag/vector_store.py`
- Set up ChromaDB persistent storage
- Configure collection schema
- Implement metadata filtering
- Set up indexing strategies

**Key Components**:
```python
class VectorStore:
    def __init__(self, persist_directory: str = "vector_db")
    def create_collection(self, name: str, metadata_config: dict)
    def add_embeddings(self, embeddings: List[Embedding], chunks: List[Chunk])
    def configure_indexing(self, strategy: str = "hierarchical")
```

**Step 2.2.3: Hierarchical Indexing**
**File**: `src/rag/indexing.py`
- Implement scheme → document type → content hierarchy
- Create metadata filtering capabilities
- Set up efficient query routing
- Optimize for mutual fund data structure

**Key Components**:
```python
class HierarchicalIndexer:
    def create_fund_hierarchy(self, chunks: List[Chunk]) -> dict
    def setup_metadata_filters(self)
    def route_queries(self, query: str, fund_type: str = None)
    def optimize_index_structure(self)
```

**Step 2.2.4: Storage Optimization**
**File**: `src/rag/storage_optimizer.py`
- Implement vector compression
- Set up backup procedures
- Configure retention policies
- Monitor storage usage

**Success Criteria**:
- Vector database operational
- All chunks successfully embedded and stored
- Query latency < 100ms
- Storage efficiency > 80%

### Phase 2.3: Retrieval System Development (Week 3, Days 5-6)

#### Objective
Build efficient retrieval system for finding relevant documents.

#### Implementation Steps

**Step 2.3.1: Query Processing Module**
**File**: `src/rag/query_processor.py`
- Clean and optimize user queries
- Handle typos and misspellings
- Implement query expansion
- Detect query intent and type

**Key Components**:
```python
class QueryProcessor:
    def clean_query(self, query: str) -> str
    def expand_query(self, query: str) -> List[str]
    def handle_typos(self, query: str) -> str
    def detect_intent(self, query: str) -> QueryIntent
    def classify_query_type(self, query: str) -> QueryType
```

**Query Types**:
- **FACTUAL**: Expense ratio, exit load, minimum SIP, etc.
- **ADVISORY**: "Should I invest?", "Which fund is better?"
- **PERFORMANCE**: Historical returns, comparisons
- **PROCEDURAL**: How to download statements, tax guides

**Query Intents**:
- Expense ratio, exit load, NAV, SIP, AUM, risk, benchmark, performance returns, investment objective, fund comparison, investment guidance, procedural help, general info

**Step 2.3.2: Semantic Search Engine**
**File**: `src/rag/search_engine.py`
- Implement semantic similarity search
- Configure similarity thresholds
- Handle multiple search strategies
- Rank results by relevance

**Key Components**:
```python
class SemanticSearchEngine:
    def search(self, query_embedding: Embedding, top_k: int = 5) -> List[SearchResult]
    def configure_similarity_threshold(self, threshold: float = 0.7)
    def multi_strategy_search(self, query: str) -> List[SearchResult]
    def rank_results(self, results: List[SearchResult]) -> List[SearchResult]
```

**Search Strategies**:
- **SEMANTIC**: Basic semantic search
- **HYBRID**: Combine multiple strategies
- **FOCUSED**: Fund-specific, content-specific, type-specific

**Step 2.3.3: Context Builder**
**File**: `src/rag/context_builder.py`
- Assemble relevant context from chunks
- Maintain coherence across chunks
- Handle context window limitations (4000 tokens max)
- Preserve source citations

**Key Components**:
```python
class ContextBuilder:
    def build_context(self, search_results: List[SearchResult], max_tokens: int = 4000) -> Context
    def maintain_coherence(self, chunks: List[Chunk]) -> Context
    def handle_window_limits(self, context: Context) -> Context
    def preserve_citations(self, context: Context) -> Context
```

**Context Building Strategies**:
- **Relevance First**: Prioritize most relevant results
- **Chronological**: Order by recency
- **Fund Grouped**: Group by fund name
- **Content Grouped**: Group by content type
- **Hybrid**: Combine multiple approaches

**Step 2.3.4: Source Ranking System**
**File**: `src/rag/source_ranker.py`
- Prioritize official sources
- Implement multi-criteria ranking
- Handle source authority classification
- Generate ranking scores

**Key Components**:
```python
class SourceRanker:
    def rank_sources(self, results: List[SearchResult], query: ProcessedQuery) -> List[RankedSource]
    def prioritize_official_sources(self, sources: List[RankedSource]) -> List[RankedSource]
    def calculate_ranking_score(self, results: List[SearchResult], query: ProcessedQuery) -> RankingScore
```

**Ranking Criteria**:
- **Relevance**: Query-match relevance (40% weight)
- **Quality**: Content quality (20% weight)
- **Recency**: Content freshness (15% weight)
- **Completeness**: Metadata completeness (10% weight)
- **Authority**: Source credibility (10% weight)
- **Coverage**: Query coverage (5% weight)

**Success Criteria**:
- Retrieval accuracy > 90%
- Query processing time < 1 second
- Result relevance score > 0.8
- Zero compliance violations

### Phase 2.4: LLM Integration and Prompt Engineering (Week 4, Days 1-2)

#### Objective
Integrate LLM for response generation with strict compliance.

#### Implementation Steps

**Step 2.4.1: LLM Service Integration**
**File**: `src/rag/llm_service.py`
- Integrate OpenAI GPT-3.5-turbo
- Implement retry mechanisms
- Handle rate limiting
- Set up fallback options

**Key Components**:
```python
class LLMService:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo")
    async def generate_response(self, prompt: str) -> str
    def handle_rate_limits(self)
    def implement_retries(self, max_retries: int = 3)
    def setup_fallback(self, fallback_model: str = None)
```

**Step 2.4.2: Prompt Engineering System**
**File**: `src/rag/prompt_engine.py`
- Design facts-only prompts
- Implement response length constraints
- Add citation requirements
- Include compliance instructions

**Key Components**:
```python
class PromptEngine:
    def create_factual_prompt(self, context: Context, query: str) -> str
    def enforce_length_limit(self, prompt: str, max_sentences: int = 3)
    def require_citations(self, prompt: str)
    def add_compliance_instructions(self, prompt: str)
```

**Step 2.4.3: Response Validator**
**File**: `src/rag/response_validator.py`
- Validate response length
- Check for advisory content
- Ensure citation presence
- Verify compliance

**Key Components**:
```python
class ResponseValidator:
    def validate_length(self, response: str, max_sentences: int = 3) -> bool
    def check_advisory_content(self, response: str) -> bool
    def ensure_citation(self, response: str) -> bool
    def verify_compliance(self, response: str) -> ComplianceResult
```

**Step 2.4.4: Response Formatter**
**File**: `src/rag/response_formatter.py`
- Format responses with citations
- Add required disclaimers
- Include last updated dates
- Ensure consistent formatting

**Key Components**:
```python
class ResponseFormatter:
    def format_response(self, response: str, citation: str, date: str) -> FormattedResponse
    def add_disclaimer(self, response: str) -> str
    def include_last_updated(self, response: str, date: str) -> str
    def ensure_consistency(self, response: str) -> str
```

**Response Structure**:
```python
{
  "answer": "Concise factual response (max 3 sentences)",
  "source": "Single official source URL",
  "last_updated": "YYYY-MM-DD",
  "disclaimer": "Facts-only. No investment advice."
}
```

**Success Criteria**:
- LLM integration operational
- Response compliance rate 100%
- Average response time < 3 seconds
- Zero advice violations

### Phase 2.5: Metadata and Source Management (Week 4, Days 3-4)

#### Objective
Manage metadata and source links for accurate citations.

#### Implementation Steps

**Step 2.5.1: Source Link Management**
**File**: `src/rag/source_manager.py`
- Track source URL validity
- Handle link rot detection
- Implement source versioning
- Manage source updates

**Key Components**:
```python
class SourceManager:
    def validate_source_links(self, sources: List[Source]) -> List[ValidSource]
    def detect_link_rot(self, sources: List[Source]) -> List[BrokenLink]
    def version_sources(self, sources: List[Source]) -> List[VersionedSource]
    def handle_source_updates(self, updates: List[SourceUpdate])
```

**Step 2.5.2: Metadata Consistency**
**File**: `src/rag/metadata_manager.py`
- Ensure metadata consistency across chunks
- Handle metadata updates
- Validate metadata formats
- Manage metadata relationships

**Key Components**:
```python
class MetadataManager:
    def ensure_consistency(self, chunks: List[Chunk]) -> List[Chunk]
    def handle_updates(self, updates: List[MetadataUpdate])
    def validate_formats(self, metadata: dict) -> ValidationResult
    def manage_relationships(self, chunks: List[Chunk]) -> RelationshipMap
```

**Step 2.5.3: Citation System**
**File**: `src/rag/citation_system.py`
- Generate accurate citations
- Handle multiple source scenarios
- Validate citation formats
- Track citation usage

**Key Components**:
```python
class CitationSystem:
    def generate_citation(self, chunk: Chunk) -> Citation
    def handle_multiple_sources(self, chunks: List[Chunk]) -> Citation
    def validate_format(self, citation: Citation) -> bool
    def track_usage(self, citation: Citation) -> UsageStats
```

**Success Criteria**:
- Source link accuracy > 95%
- Metadata consistency 100%
- Citation format compliance
- Version tracking operational

### Phase 2.6: Performance Optimization and Testing (Week 4, Days 5-6)

#### Objective
Optimize system performance and ensure reliability.

#### Implementation Steps

**Step 2.6.1: Performance Optimization**
**File**: `src/rag/performance_optimizer.py`
- Implement query caching
- Optimize embedding storage
- Configure connection pooling
- Set up load balancing

**Key Components**:
```python
class PerformanceOptimizer:
    def implement_query_cache(self, cache_size: int = 1000)
    def optimize_embedding_storage(self)
    def configure_connection_pool(self, pool_size: int = 10)
    def setup_load_balancing(self)
```

**Step 2.6.2: Monitoring and Metrics**
**File**: `src/rag/monitoring.py`
- Track performance metrics
- Monitor system health
- Set up alerting
- Generate performance reports

**Key Components**:
```python
class RAGMonitoring:
    def track_performance(self, operation: str, duration: float)
    def monitor_health(self) -> HealthStatus
    def setup_alerting(self, thresholds: dict)
    def generate_reports(self) -> PerformanceReport
```

**Step 2.6.3: Integration Testing**
**File**: `tests/test_rag_integration.py`
- End-to-end RAG pipeline testing
- Performance benchmarking
- Compliance validation
- Error handling verification

**Key Components**:
```python
class RAGIntegrationTests:
    def test_end_to_end_pipeline(self)
    def benchmark_performance(self)
    def validate_compliance(self)
    def verify_error_handling(self)
```

**Success Criteria**:
- Query response time < 3 seconds
- Concurrent query handling > 100 QPS
- System uptime > 99%
- All integration tests passing

---

## Phase 3: Query Processing and Response Generation (Week 5-6)

### 3.1 Query Classification
```python
# Query types
- FACTUAL: Expense ratio, exit load, minimum SIP, etc.
- ADVISORY: "Should I invest?", "Which fund is better?"
- PERFORMANCE: Historical returns, comparisons
- PROCEDURAL: How to download statements, tax guides
```

### 3.2 Response Generation Pipeline
- **Factual Queries**: Direct retrieval + concise answer
- **Advisory Queries**: Polite refusal + educational link
- **Performance Queries**: Link to official factsheet only
- **Procedural Queries**: Step-by-step guidance with source

### 3.3 Response Formatting
```python
# Response structure
{
  "answer": "Concise factual response (max 3 sentences)",
  "source": "Single official source URL",
  "last_updated": "YYYY-MM-DD",
  "disclaimer": "Facts-only. No investment advice."
}
```

---

## Phase 4: User Interface Development (Week 7)

### 4.1 Frontend Components
- **Framework**: Streamlit (simple) or React (advanced)
- **Core Features**:
  - Welcome message with disclaimer
  - Query input interface
  - Three example questions
  - Response display area
  - Source link display

### 4.2 UI/UX Design
- **Minimal Design**: Clean, distraction-free interface
- **Accessibility**: Screen reader compatible
- **Mobile Responsive**: Works on all devices
- **Visual Indicators**: Clear separation between Q&A

### 4.3 Frontend Architecture
```javascript
// Component structure
- App: Main application container
- QueryInput: User query form
- ResponseDisplay: Answer presentation
- ExampleQuestions: Pre-defined queries
- DisclaimerFooter: Legal compliance text
```

---

## Phase 5: Integration and Testing (Week 8)

### 5.1 System Integration
- **API Development**: RESTful endpoints for frontend
- **Error Handling**: Graceful failures and fallbacks
- **Logging**: Comprehensive audit trails
- **Monitoring**: Performance and usage metrics

### 5.2 Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end query processing
- **Compliance Tests**: Verify facts-only responses
- **User Acceptance Tests**: Real user scenarios

### 5.3 Quality Assurance
- **Response Accuracy**: Verify factual correctness
- **Source Validation**: Ensure official citations
- **Constraint Compliance**: Check response length and format
- **Security Testing**: Verify no PII collection

---

## Phase 6: Deployment and Documentation (Week 9-10)

### 6.1 Deployment Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Vector Store  │
│  (Streamlit)    │◄──►│   (FastAPI)     │◄──►│  (ChromaDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   LLM Service   │
                       │  (OpenAI/Local) │
                       └─────────────────┘
```

### 6.2 Infrastructure Requirements
- **Compute**: 2-4 CPU cores, 8GB RAM minimum
- **Storage**: 10GB for vector database
- **Network**: Internet access for source updates
- **Security**: HTTPS, rate limiting, input validation

### 6.3 Documentation Deliverables
- **README.md**: Setup and usage instructions
- **API Documentation**: Endpoint specifications
- **Architecture Guide**: Technical implementation details
- **Compliance Document**: Regulatory adherence
- **User Manual**: End-user guidance

---

## GitHub Actions Integration

### 🔄 Automated Update Pipeline

#### Schedule
- **Daily Updates**: 2:00 AM IST (8:30 PM UTC previous day)
- **Manual Triggers**: Available via GitHub Actions UI
- **Force Updates**: Optional parameter to bypass change detection

#### Workflow Components

**1. Setup and Change Detection**
- Environment Setup: Python 3.9, dependency caching
- Change Detection: Checks HDFC website, data freshness, local file changes
- Decision Logic: Determines if full pipeline should run

**2. Data Collection (Phase 1)**
- Web Scraping: HDFC Mutual Fund website, Groww platform
- Data Validation: Quality checks and compliance verification
- Artifact Storage: Temporary storage for pipeline stages

**3. Document Processing (Phase 2.1)**
- Document Loading: Process collected raw data
- Semantic Chunking: Generate optimized text chunks
- Metadata Enrichment: Add hierarchical metadata

**4. Vector Store Update (Phase 2.2)**
- Embedding Generation: BGE-Small-EN model processing
- Vector Storage: ChromaDB database updates
- Hierarchical Indexing: Fund-specific organization

**5. Retrieval System (Phase 2.3)**
- Query Processing: Test query classification and intent
- Search Engine: Validate semantic search performance
- Context Building: Test context assembly strategies
- Source Ranking: Validate source prioritization

**6. Integration Testing**
- Comprehensive Tests: Full pipeline validation
- Performance Benchmarks: Latency and accuracy metrics
- Report Generation: Detailed update reports

**7. Deployment and Cleanup**
- Git Operations: Automated commits and tags
- Artifact Management: Cleanup old artifacts
- Health Checks: System validation

#### Performance Targets
- **Total Pipeline Time**: < 60 minutes
- **Data Collection**: < 20 minutes
- **Document Processing**: < 15 minutes
- **Embedding Generation**: < 20 minutes
- **Retrieval Validation**: < 10 minutes
- **Integration Testing**: < 15 minutes

#### Supporting Scripts
- `check_data_changes.py` - Smart change detection
- `validate_data.py` - Multi-phase validation
- `run_performance_tests.py` - Performance benchmarking
- `generate_update_report.py` - Comprehensive reporting
- `health_check.py` - System health monitoring

---

## Technical Architecture Details

### Data Flow
```
User Query → Query Classification → Retrieval → Context Building → LLM → Response Validation → Formatted Output
```

### Security Considerations
- **Input Sanitization**: Prevent injection attacks
- **Rate Limiting**: Prevent abuse
- **No PII Storage**: Privacy by design
- **Source Verification**: Ensure official sources only

### Performance Optimization
- **Caching**: Cache frequent queries
- **Lazy Loading**: Load vector store on demand
- **Batch Processing**: Process multiple queries efficiently
- **Monitoring**: Track response times and accuracy

### Scalability Considerations
- **Horizontal Scaling**: Multiple API instances
- **Database Sharding**: Distribute vector storage
- **CDN Integration**: Cache static assets
- **Load Balancing**: Distribute query traffic

---

## Success Metrics and Risk Mitigation

### Success Metrics
- **Accuracy**: >95% factual correctness
- **Response Time**: <3 seconds for most queries
- **Compliance**: 100% facts-only responses
- **User Satisfaction**: Positive feedback on clarity and usefulness

### Technical Metrics
- Retrieval accuracy > 90%
- Response time < 3 seconds
- System uptime > 99%
- Memory usage < 2GB

### Compliance Metrics
- Response compliance rate 100%
- Citation accuracy > 95%
- Zero advice violations
- Proper disclaimer inclusion

### Performance Metrics
- Concurrent queries > 100 QPS
- Storage efficiency > 80%
- Cache hit rate > 70%
- Error rate < 1%

### Risk Mitigation
- **Source Updates**: Automated source monitoring with GitHub Actions
- **Model Drift**: Regular retraining and validation
- **Regulatory Changes**: Compliance monitoring
- **Technical Failures**: Redundancy and fallback mechanisms

---

## Implementation Dependencies

### Sequential Dependencies
```
Phase 1 → Phase 2.1 → Phase 2.2 → Phase 2.3 → Phase 2.4 → Phase 2.5 → Phase 2.6 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

### Parallel Development Opportunities
- Steps within each sub-phase can be developed in parallel
- Testing can be done concurrently with development
- Documentation can be written alongside implementation

### Key Integration Points
- Phase 1 data → Phase 2.1 processing
- Phase 2.2 embeddings → Phase 2.3 retrieval
- Phase 2.3 context → Phase 2.4 LLM
- Phase 2.4 responses → Phase 2.5 citations
- All components → Phase 2.6 optimization

This comprehensive architecture provides a complete roadmap for building a compliant, accurate, and user-friendly mutual fund FAQ assistant that meets all specified requirements with automated data updates and robust performance monitoring.
