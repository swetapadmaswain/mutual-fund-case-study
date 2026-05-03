# Mutual Fund FAQ Assistant

A facts-only Retrieval-Augmented Generation (RAG) system for answering objective queries about HDFC mutual fund schemes using data from Groww platform.

## 🎯 Project Overview

This project implements a compliant, facts-only FAQ assistant that:
- Answers objective queries about 5 HDFC mutual fund schemes
- Uses only official Groww platform data sources
- Strictly avoids investment advice or recommendations
- Provides concise, source-backed responses (max 3 sentences)
- Includes proper citations and disclaimers

## 📋 Supported HDFC Mutual Funds

1. **HDFC Mid-Cap Fund (Direct Growth)**
2. **HDFC Equity Fund (Direct Growth)**  
3. **HDFC Focused Fund (Direct Growth)**
4. **HDFC ELSS Tax Saver Fund (Direct Plan Growth)**
5. **HDFC Large-Cap Fund (Direct Growth)**

## 🏗️ Architecture

### Phase 1: Foundation and Data Collection ✅
- Environment setup and dependency management
- Data ingestion from Groww URLs
- Source validation and compliance checking
- Data processing and storage

### Phase 2.1: Document Processing and Chunking ✅
- Text preprocessing and cleaning
- Semantic chunking (500-800 tokens)
- Metadata enrichment and hierarchical keys
- Quality validation and compliance checking

### Phase 2: RAG System Implementation (In Progress)
- Document processing and chunking ✅
- Vector database setup (Planned)
- Retrieval system development (Planned)
- LLM integration (Planned)

### Phase 3: Query Processing (Planned)
- Query classification and intent detection
- Factual vs advisory query handling
- Response generation with compliance

### Phase 4: User Interface (Planned)
- Minimal Streamlit interface
- Query input and response display
- Accessibility and compliance features

### Phase 5: Integration and Testing (Planned)
- System integration
- Compliance testing
- User acceptance testing

### Phase 6: Deployment and Documentation (Planned)
- Production deployment
- Monitoring and alerting
- Complete documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- Internet connection for data collection

### Setup

1. **Clone repository**
```bash
git clone https://github.com/swetapadmaswain/mutual-fund-case-study.git
cd mutual-fund-case-study
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env file with your settings
```

5. **Run Phase 1 data collection**
```bash
python src/data_collection/main.py
```

6. **Run Phase 2.1 document processing**
```bash
python src/rag/chunking/main.py
```

### Phase 1 Usage

The Phase 1 pipeline performs:
- **URL Validation**: Checks all Groww URLs for accessibility and compliance
- **Data Collection**: Fetches fund information from all 5 HDFC fund pages
- **Content Processing**: Extracts and structures financial data
- **Storage**: Saves processed data in JSON format with metadata

### Phase 2.1 Usage

The Phase 2.1 pipeline performs:
- **Document Processing**: Cleans and preprocesses text content
- **Semantic Chunking**: Creates 500-800 token chunks with overlap
- **Metadata Enrichment**: Adds hierarchical keys and citations
- **Quality Validation**: Ensures compliance and quality standards

### Expected Output

#### Phase 1 Output
```
================================================================================
PHASE 1 RESULTS: Phase 1 - Foundation and Data Collection
================================================================================
Success: 
Duration: 45.23 seconds

 VALIDATION RESULTS:
  Total URLs: 5
  Valid URLs: 5
  Invalid URLs: 0
  SSL Enabled: 5
  Allowed Domains: 5

 COLLECTION RESULTS:
  Total URLs: 5
  Successful Fetches: 5
  Failed Fetches: 0

 PROCESSING RESULTS:
  Total Documents: 5
  New Documents: 5
  Duplicate Documents: 0
  Processed Documents: 5
  Failed Documents: 0

 FINAL SUMMARY:
  Total Documents: 5
  Unique Funds: 5
  Last Updated: 2025-01-15T10:30:45
  Avg Content Length: 2456.7 characters
  Funds Processed: 5
```

#### Phase 2.1 Output
```
================================================================================
PHASE 2.1 RESULTS: Document Processing and Chunking
================================================================================
Success: 
Duration: 45.67 seconds

 STEP RESULTS:
 DOCUMENT PROCESSING:
  documents_processed: 5
  total_words: 12456
  avg_compression_ratio: 0.85
  financial_data_extracted: {'expense_ratios': 5, 'sip_amounts': 5}
  Success: 

 CHUNKING:
  total_chunks: 23
  avg_chunk_size: 645.3
  size_distribution: {'small (< 500)': 3, 'medium (500-800)': 18, 'large (> 800)': 2}
  context_coverage: 0.87
  Success: 

 METADATA ENRICHMENT:
  chunks_enriched: 23
  avg_quality_score: 0.82
  content_types: {'expense_ratio': 8, 'nav': 6, 'sip': 5}
  financial_coverage: 0.91
  citation_completeness: 1.0
  Success: 

 VALIDATION:
  total_validated: 23
  valid_chunks: 21
  invalid_chunks: 0
  warning_chunks: 2
  avg_score: 0.79
  validation_rate: 0.91
  Success: 

 FINAL SUMMARY:
  Documents Processed: 5
  Chunks Created: 23
  Chunks Enriched: 23
  Average Quality Score: 0.79
  Validation Rate: 91.30%
```

## 📁 Project Structure

```
mutual-fund-case-study/
├── src/                          # Source code
│   ├── config/                   # Configuration files
│   │   └── settings.py          # Application settings
│   ├── data_collection/          # Phase 1 components
│   │   ├── main.py              # Phase 1 pipeline entry point
│   │   ├── document_loader.py   # Web scraping and content extraction
│   │   ├── source_validator.py  # Source validation and compliance
│   │   └── data_processor.py    # Data processing and storage
│   ├── rag/                      # Phase 2 components
│   │   └── chunking/           # Phase 2.1 components
│   │       ├── main.py         # Phase 2.1 pipeline entry point
│   │       ├── document_processor.py # Text preprocessing and cleaning
│   │       ├── chunker.py      # Semantic chunking strategy
│   │       ├── metadata_enricher.py # Metadata enrichment
│   │       └── chunk_validator.py # Quality validation
│   └── utils/                    # Utility modules
│       ├── logger.py            # Logging configuration
│       ├── exceptions.py        # Custom exceptions
│       └── monitoring.py        # Monitoring and metrics
├── tests/                        # Test files
│   ├── test_document_loader.py  # Tests for document loading
│   ├── test_source_validator.py # Tests for source validation
│   └── test_chunking.py       # Tests for chunking components
├── docs/                         # Documentation
│   ├── planning/                 # Project planning
│   ├── architecture/             # System architecture
│   ├── edge-cases/              # Risk management
│   └── technical/               # Technical specs
├── cache/                       # Data storage (auto-created)
├── logs/                        # Log files (auto-created)
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Data Collection
DATA_COLLECTION_DELAY=1.0      # Delay between requests (seconds)
MAX_RETRIES=3                  # Maximum retry attempts
TIMEOUT_SECONDS=30            # Request timeout

# Source Validation
ALLOWED_DOMAINS=groww.in       # Allowed source domains
SSL_VERIFY=true               # SSL certificate verification

# Cache and Storage
CACHE_TTL=3600                # Cache time-to-live (seconds)
CACHE_DIR=cache               # Cache directory

# Logging
LOG_LEVEL=INFO               # Logging level
LOG_FILE=logs/app.log        # Log file location
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_document_loader.py

# Run with verbose output
pytest -v
```

## 📊 Monitoring and Metrics

### Phase 1 Monitoring
- **Performance Metrics**: Execution time, success rates, processing speed
- **Data Quality**: Content length, duplicate detection, validation results
- **Health Checks**: System health, configuration validation
- **Export Reports**: JSON reports with detailed metrics

### Phase 2.1 Monitoring
- **Processing Statistics**: Document processing metrics and compression ratios
- **Chunking Metrics**: Chunk size distribution and context coverage
- **Quality Metrics**: Validation scores and compliance rates
- **Enrichment Stats**: Metadata completeness and quality scores

Access metrics in `cache/metrics/` directories.

## ⚠️ Compliance Requirements

### Facts-Only Constraint
- ❌ No investment advice or recommendations
- ❌ No performance comparisons or return calculations
- ❌ No personalized financial guidance
- ✅ Only objective, verifiable information
- ✅ Source citations for all responses

### Response Format
- Maximum 3 sentences per response
- Single source citation
- "Last updated from sources: <date>" footer
- "Facts-only. No investment advice." disclaimer

### Data Sources
- Only official Groww platform URLs
- HDFC Mutual Fund schemes only
- No third-party aggregators or blogs

## 🔍 Data Processing Details

### Phase 1 Extracted Information
- Fund name and type
- Expense ratio and exit load
- Minimum SIP amount
- Current NAV and risk level
- Benchmark index and AUM
- Investment objectives

### Phase 2.1 Processing Features
- Text cleaning and normalization
- Semantic chunking with overlap
- Hierarchical metadata structure
- Quality scoring and validation
- Compliance checking and filtering

## 🐛 Troubleshooting

### Common Issues

1. **Network Connection Errors**
   - Check internet connectivity
   - Verify firewall settings
   - Try running with increased timeout

2. **SSL Certificate Issues**
   - Set `SSL_VERIFY=false` in `.env` (not recommended for production)
   - Check system time and date
   - Update SSL certificates

3. **Memory Issues**
   - Reduce concurrent requests
   - Increase system memory
   - Clear cache directory

4. **Permission Errors**
   - Check file permissions for cache directory
   - Run with appropriate user permissions
   - Ensure Python has write access

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python src/data_collection/main.py
LOG_LEVEL=DEBUG python src/rag/chunking/main.py
```

## 📈 Performance

### Expected Performance

#### Phase 1
- **Execution Time**: 30-60 seconds for 5 URLs
- **Success Rate**: >95% for valid URLs
- **Memory Usage**: <100MB during operation
- **Storage**: ~10MB for processed data

#### Phase 2.1
- **Execution Time**: 30-60 seconds for processing
- **Chunk Generation**: 20-30 chunks per document
- **Quality Score**: Average >0.7 for good content
- **Validation Rate**: >90% for processed chunks

### Optimization Tips
- Use SSD for faster I/O
- Ensure stable internet connection
- Monitor system resources during execution
- Use appropriate chunk sizes for optimal processing

## 🤝 Contributing

1. Follow existing code style (Black formatting)
2. Write tests for new functionality
3. Update documentation for changes
4. Ensure compliance requirements are met
5. Run full test suite before submitting

## 📝 License

This project is licensed under MIT License - see project documentation for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the edge cases documentation
3. Check logs in `logs/app.log`
4. Create an issue with detailed information

## 🔄 Next Steps

### Current Status
- ✅ Phase 1: Foundation and Data Collection - Complete
- ✅ Phase 2.1: Document Processing and Chunking - Complete
- 🔄 Phase 2.2: Vector Store Setup - Next
- ⏳ Phase 2.3: Retrieval System - Planned
- ⏳ Phase 2.4: LLM Integration - Planned
- ⏳ Phase 2.5: Metadata Management - Planned
- ⏳ Phase 2.6: Performance Optimization - Planned

### After Phase 2.1
1. Review chunk quality and distribution
2. Validate metadata completeness
3. Proceed to Phase 2.2 (Vector Store Setup)
4. Set up embedding model integration
5. Configure ChromaDB collections

---

**Note**: This is an active 6-phase implementation. Phase 1 and Phase 2.1 are complete and ready for use.
