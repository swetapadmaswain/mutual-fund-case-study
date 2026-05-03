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

### Phase 2: RAG System Implementation (Planned)
- Document processing and chunking
- Vector database setup
- Retrieval system development
- LLM integration

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

1. **Clone the repository**
```bash
git clone <repository-url>
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

### Phase 1 Usage

The Phase 1 pipeline performs:
- **URL Validation**: Checks all Groww URLs for accessibility and compliance
- **Data Collection**: Fetches fund information from all 5 HDFC fund pages
- **Content Processing**: Extracts and structures financial data
- **Storage**: Saves processed data in JSON format with metadata

### Expected Output

```
================================================================================
PHASE 1 RESULTS: Phase 1 - Foundation and Data Collection
================================================================================
Success: ✅
Duration: 45.23 seconds

📊 VALIDATION RESULTS:
  Total URLs: 5
  Valid URLs: 5
  Invalid URLs: 0
  SSL Enabled: 5
  Allowed Domains: 5

🌐 COLLECTION RESULTS:
  Total URLs: 5
  Successful Fetches: 5
  Failed Fetches: 0

⚙️ PROCESSING RESULTS:
  Total Documents: 5
  New Documents: 5
  Duplicate Documents: 0
  Processed Documents: 5
  Failed Documents: 0

📈 FINAL SUMMARY:
  Total Documents: 5
  Unique Funds: 5
  Last Updated: 2025-01-15T10:30:45
  Avg Content Length: 2456.7 characters
  Funds Processed: 5
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
│   └── utils/                    # Utility modules
│       ├── logger.py            # Logging configuration
│       ├── exceptions.py        # Custom exceptions
│       └── monitoring.py        # Monitoring and metrics
├── tests/                        # Test files
│   ├── test_document_loader.py  # Tests for document loading
│   └── test_source_validator.py # Tests for source validation
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

Phase 1 includes comprehensive monitoring:

- **Performance Metrics**: Execution time, success rates, processing speed
- **Data Quality**: Content length, duplicate detection, validation results
- **Health Checks**: System health, configuration validation
- **Export Reports**: JSON reports with detailed metrics

Access metrics in `cache/metrics/phase1_metrics.json`.

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

### Extracted Information
- Fund name and type
- Expense ratio and exit load
- Minimum SIP amount
- Current NAV and risk level
- Benchmark index and AUM
- Investment objectives

### Data Quality
- Content deduplication using hash comparison
- Structured data extraction and validation
- Compliance checking for advisory language
- Personal data detection and filtering

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
```

## 📈 Performance

### Expected Performance
- **Execution Time**: 30-60 seconds for 5 URLs
- **Success Rate**: >95% for valid URLs
- **Memory Usage**: <100MB during operation
- **Storage**: ~10MB for processed data

### Optimization Tips
- Use SSD for faster I/O
- Ensure stable internet connection
- Monitor system resources during execution

## 🤝 Contributing

1. Follow the existing code style (Black formatting)
2. Write tests for new functionality
3. Update documentation for changes
4. Ensure compliance requirements are met
5. Run the full test suite before submitting

## 📝 License

This project is licensed under the MIT License - see the project documentation for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the edge cases documentation
3. Check logs in `logs/app.log`
4. Create an issue with detailed information

## 🔄 Next Steps

After completing Phase 1:
1. Review collected data quality
2. Proceed to Phase 2 (RAG System Implementation)
3. Set up vector database
4. Implement document chunking and indexing

---

**Note**: This is Phase 1 of a 6-phase implementation. Current functionality focuses on data collection and processing only.
