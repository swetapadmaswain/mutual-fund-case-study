# Phase-wise Architecture: Mutual Fund FAQ Assistant

## Overview
This document outlines the detailed phase-wise architecture for building a facts-only mutual fund FAQ assistant using a Retrieval-Augmented Generation (RAG) approach.

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

## Phase 2: RAG System Implementation (Week 3-4)

### 2.1 Document Processing and Chunking
- **Text Preprocessing**: Clean HTML, normalize text
- **Chunking Strategy**: 
  - Semantic chunking (500-800 tokens)
  - Preserve context for Q&A pairs
  - Maintain source metadata

### 2.2 Vector Store Setup
- **Embedding Model**: `all-MiniLM-L6-v2` or similar
- **Vector Database**: ChromaDB for local storage
- **Index Configuration**: 
  - Hierarchical indexing (scheme → document type → content)
  - Metadata filtering capabilities

### 2.3 Retrieval System
```python
# Retrieval components
- QueryProcessor: Clean and optimize user queries
- SemanticSearch: Find relevant chunks using similarity
- SourceRanker: Prioritize official sources
- ContextBuilder: Assemble relevant context for LLM
```

### 2.4 LLM Integration
- **Model Selection**: OpenAI GPT-3.5-turbo or local model
- **Prompt Engineering**: 
  - Facts-only constraint enforcement
  - Response length limitation (max 3 sentences)
  - Citation requirement enforcement
- **Response Validation**: Post-processing for compliance

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

## Success Metrics
- **Accuracy**: >95% factual correctness
- **Response Time**: <3 seconds for most queries
- **Compliance**: 100% facts-only responses
- **User Satisfaction**: Positive feedback on clarity and usefulness

## Risk Mitigation
- **Source Updates**: Automated source monitoring
- **Model Drift**: Regular retraining and validation
- **Regulatory Changes**: Compliance monitoring
- **Technical Failures**: Redundancy and fallback mechanisms

This architecture provides a comprehensive roadmap for building a compliant, accurate, and user-friendly mutual fund FAQ assistant that meets all specified requirements.
