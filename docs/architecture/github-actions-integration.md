# GitHub Actions Integration for Automated Data Updates

## Overview
This document describes the GitHub Actions workflow implementation for automated data updates in the Mutual Fund FAQ Assistant project.

## 🔄 Automated Update Pipeline

### Schedule
- **Daily Updates**: 2:00 AM IST (8:30 PM UTC previous day)
- **Manual Triggers**: Available via GitHub Actions UI
- **Force Updates**: Optional parameter to bypass change detection

### Workflow Components

#### 1. Setup and Change Detection
- **Environment Setup**: Python 3.9, dependency caching
- **Change Detection**: Checks HDFC website, data freshness, local file changes
- **Decision Logic**: Determines if full pipeline should run

#### 2. Data Collection (Phase 1)
- **Web Scraping**: HDFC Mutual Fund website, Groww platform
- **Data Validation**: Quality checks and compliance verification
- **Artifact Storage**: Temporary storage for pipeline stages

#### 3. Document Processing (Phase 2.1)
- **Document Loading**: Process collected raw data
- **Semantic Chunking**: Generate optimized text chunks
- **Metadata Enrichment**: Add hierarchical metadata

#### 4. Vector Store Update (Phase 2.2)
- **Embedding Generation**: BGE-Small-EN model processing
- **Vector Storage**: ChromaDB database updates
- **Hierarchical Indexing**: Fund-specific organization

#### 5. Retrieval System (Phase 2.3)
- **Query Processing**: Test query classification and intent
- **Search Engine**: Validate semantic search performance
- **Context Building**: Test context assembly strategies
- **Source Ranking**: Validate source prioritization

#### 6. Integration Testing
- **Comprehensive Tests**: Full pipeline validation
- **Performance Benchmarks**: Latency and accuracy metrics
- **Report Generation**: Detailed update reports

#### 7. Deployment and Cleanup
- **Git Operations**: Automated commits and tags
- **Artifact Management**: Cleanup old artifacts
- **Health Checks**: System validation

## 📊 Workflow Configuration

### Triggers
```yaml
on:
  schedule:
    - cron: '30 20 * * *'  # Daily at 2:00 AM IST
  workflow_dispatch:
    inputs:
      update_type:
        description: 'Type of update to perform'
        required: true
        default: 'full'
        type: choice
        options:
          - full
          - incremental
          - embeddings_only
          - validation_only
      force_update:
        description: 'Force update even if no changes detected'
        required: false
        default: false
        type: boolean
```

### Environment Variables
```yaml
env:
  PYTHON_VERSION: '3.9'
  NODE_VERSION: '18'
  GITHUB_ACTIONS: true
  SCRAPE_DELAY: 2
  MAX_RETRIES: 3
```

### Jobs Overview

#### 1. setup-and-check
- **Purpose**: Environment setup and change detection
- **Outputs**: `has_changes`, `update_type`, `should_run`
- **Duration**: ~2-3 minutes

#### 2. data-collection
- **Purpose**: Phase 1 data collection and processing
- **Dependencies**: setup-and-check
- **Duration**: ~10-15 minutes
- **Artifacts**: Raw and processed data

#### 3. document-processing
- **Purpose**: Phase 2.1 document chunking
- **Dependencies**: data-collection
- **Duration**: ~5-10 minutes
- **Artifacts**: Chunked documents

#### 4. vector-store-update
- **Purpose**: Phase 2.2 embedding and vector storage
- **Dependencies**: document-processing
- **Duration**: ~15-20 minutes
- **Artifacts**: Vector database

#### 5. retrieval-system-update
- **Purpose**: Phase 2.3 retrieval system validation
- **Dependencies**: vector-store-update
- **Duration**: ~5-10 minutes
- **Artifacts**: Retrieval system

#### 6. integration-testing
- **Purpose**: End-to-end testing and validation
- **Dependencies**: retrieval-system-update
- **Duration**: ~10-15 minutes
- **Artifacts**: Test results and reports

#### 7. commit-and-deploy
- **Purpose**: Git operations and deployment
- **Dependencies**: integration-testing
- **Duration**: ~2-5 minutes

#### 8. health-check
- **Purpose**: System health validation
- **Dependencies**: commit-and-deploy
- **Duration**: ~2-3 minutes

#### 9. cleanup
- **Purpose**: Artifact cleanup and maintenance
- **Dependencies**: setup-and-check
- **Duration**: ~1-2 minutes

## 🔧 Supporting Scripts

### check_data_changes.py
- **Purpose**: Detect changes in data sources
- **Features**:
  - Website content hashing
  - Data freshness validation
  - Local file change detection
  - Force update support

### validate_data.py
- **Purpose**: Validate data at each pipeline phase
- **Features**:
  - Phase-specific validation rules
  - Data quality metrics
  - Compliance checks
  - Detailed reporting

### run_performance_tests.py
- **Purpose**: Performance benchmarking
- **Features**:
  - Query processing speed tests
  - Search engine performance
  - Context building metrics
  - End-to-end latency measurement

### generate_update_report.py
- **Purpose**: Comprehensive update reporting
- **Features**:
  - Markdown and JSON output formats
  - Phase-by-phase summaries
  - Performance metrics
  - Recommendations

### health_check.py
- **Purpose**: System health monitoring
- **Features**:
  - File system health
  - Data freshness checks
  - External connectivity
  - Pipeline integrity validation

## 📈 Performance Metrics

### Target Performance
- **Total Pipeline Time**: < 60 minutes
- **Data Collection**: < 20 minutes
- **Document Processing**: < 15 minutes
- **Embedding Generation**: < 20 minutes
- **Retrieval Validation**: < 10 minutes
- **Integration Testing**: < 15 minutes

### Monitoring
- **Success Rate**: Track pipeline completion success
- **Update Frequency**: Daily automated updates
- **Data Freshness**: < 48 hours staleness threshold
- **Performance Degradation**: Alert on >20% slowdown

## 🚨 Error Handling

### Retry Logic
- **Network Requests**: 3 retries with exponential backoff
- **Database Operations**: Automatic retry on connection errors
- **File Operations**: Graceful handling of permission issues

### Failure Scenarios
- **Website Unavailable**: Skip scraping, use cached data
- **Insufficient Data**: Warning and continue with available data
- **Performance Degradation**: Alert but continue processing
- **Critical Failures**: Stop pipeline and notify

### Notifications
- **Success**: Automatic commit with update summary
- **Warnings**: Continue processing with log warnings
- **Failures**: Stop pipeline and create GitHub issue

## 🔐 Security Considerations

### Data Privacy
- **No Personal Data**: Only public fund information collected
- **Compliance**: Financial data handling best practices
- **Access Control**: GitHub Actions with minimal permissions

### API Keys
- **Environment Variables**: Sensitive data in GitHub Secrets
- **No Hardcoded Keys**: All credentials in secure storage
- **Rotation Policy**: Regular key rotation schedule

## 📋 Best Practices

### Pipeline Optimization
- **Parallel Processing**: Independent jobs run concurrently
- **Caching**: Dependency and model caching for speed
- **Incremental Updates**: Only process changed data when possible
- **Resource Management**: Efficient resource utilization

### Monitoring and Alerting
- **Health Checks**: Regular system validation
- **Performance Tracking**: Continuous metric monitoring
- **Error Reporting**: Detailed error logging and analysis
- **Success Metrics**: Track pipeline effectiveness

### Maintenance
- **Regular Updates**: Keep dependencies current
- **Log Rotation**: Prevent log file bloat
- **Artifact Cleanup**: Remove old build artifacts
- **Documentation**: Keep configuration docs updated

## 🔄 Integration with Architecture

### Phase Alignment
- **Phase 1**: Data collection automation
- **Phase 2.1**: Document processing pipeline
- **Phase 2.2**: Embedding generation and storage
- **Phase 2.3**: Retrieval system validation

### Data Flow
```
External Sources → GitHub Actions → Phase 1 → Phase 2.1 → Phase 2.2 → Phase 2.3 → Validation → Deployment
```

### Quality Assurance
- **Automated Testing**: Comprehensive test suite
- **Performance Validation**: Benchmark against targets
- **Data Quality**: Validation at each phase
- **Compliance Checks**: Regulatory compliance verification

## 🎯 Success Criteria

### Technical Success
- **Reliability**: >95% successful pipeline runs
- **Performance**: All targets met consistently
- **Data Quality**: Validation passes at all phases
- **Automation**: Minimal manual intervention required

### Operational Success
- **Fresh Data**: Regular updates without delays
- **Monitoring**: Proactive issue detection
- **Documentation**: Clear operational procedures
- **Scalability**: Handle increased data volume

### Business Success
- **Accuracy**: Reliable and up-to-date information
- **Availability**: System ready for user queries
- **Compliance**: Regulatory requirements met
- **User Satisfaction**: High-quality responses

## 📚 Additional Resources

### GitHub Actions Documentation
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Triggering Workflows](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow)
- [Environment Variables](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idenv)

### Best Practices
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Performance Optimization](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Error Handling](https://docs.github.com/en/actions/using-workflows/setting-exit-codes-for-jobs)

This GitHub Actions integration ensures the mutual fund data remains current and the retrieval system maintains high performance with minimal manual intervention.
