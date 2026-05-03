# Mutual Fund FAQ Assistant - Documentation

## Overview
This folder contains comprehensive documentation for the Mutual Fund FAQ Assistant project, a facts-only RAG-based system for answering objective queries about mutual fund schemes.

## Folder Structure

### 📋 `/planning/`
**Project planning and requirements**
- `problem-statement.md` - Complete project requirements and objectives

### 🏗️ `/architecture/`
**System architecture and design**
- `phase-wise-architecture.md` - Detailed 6-phase implementation plan

### ⚠️ `/edge-cases/`
**Risk management and edge case analysis**
- `complete-edge-cases.md` - Consolidated edge cases for all phases
- `phase1-foundation.md` - Edge cases for foundation and data collection
- `phase2-rag-system.md` - Edge cases for RAG system implementation
- `phase3-query-processing.md` - Edge cases for query processing and response generation
- `phase4-ui-development.md` - Edge cases for user interface development
- `phase5-integration-testing.md` - Edge cases for integration and testing
- `phase6-deployment.md` - Edge cases for deployment and documentation

### 🔧 `/technical/`
**Technical specifications and implementation details**
*(To be populated during development)*

## Project Phases Overview

### Phase 1: Foundation and Data Collection (Week 1-2)
- Environment setup and dependency management
- HDFC mutual fund data collection from Groww URLs
- Data ingestion pipeline implementation
- Compliance and source validation

### Phase 2: RAG System Implementation (Week 3-4)
- Document processing and chunking
- Vector database setup and indexing
- Retrieval system development
- LLM integration and prompt engineering

### Phase 3: Query Processing and Response Generation (Week 5-6)
- Query classification and intent detection
- Factual, advisory, and performance query handling
- Response generation with compliance constraints
- Response formatting and validation

### Phase 4: User Interface Development (Week 7)
- Frontend framework selection and setup
- UI component development
- Query input and response display
- Accessibility and compliance features

### Phase 5: Integration and Testing (Week 8)
- System integration and API development
- Unit, integration, and compliance testing
- User acceptance testing
- Test environment management

### Phase 6: Deployment and Documentation (Week 9-10)
- Deployment architecture and infrastructure
- Monitoring and alerting setup
- Documentation completion
- Backup and recovery procedures

## Key Compliance Requirements

### Facts-Only Constraint
- No investment advice or recommendations
- No performance comparisons or return calculations
- Strictly objective, verifiable information only

### Response Format Requirements
- Maximum 3 sentences per response
- Single source citation required
- "Last updated from sources: <date>" footer
- "Facts-only. No investment advice." disclaimer

### Data Sources
- HDFC Mutual Fund schemes from Groww platform
- 5 specific funds: Mid-Cap, Equity, Focused, ELSS Tax Saver, Large-Cap
- Official AMC documentation only

## Quick Reference

### Critical Success Metrics
- Query classification accuracy > 95%
- Response compliance rate 100%
- System uptime > 99.9%
- Response time < 3 seconds

### Risk Management
- Comprehensive edge case documentation
- Automated monitoring and alerting
- Compliance validation procedures
- Security and privacy controls

### Documentation Standards
- Clear, concise technical documentation
- Comprehensive risk analysis
- Step-by-step implementation guides
- Regular updates and maintenance

## Getting Started

1. **Review Requirements**: Start with `/planning/problem-statement.md`
2. **Understand Architecture**: Review `/architecture/phase-wise-architecture.md`
3. **Assess Risks**: Review `/edge-cases/complete-edge-cases.md`
4. **Begin Implementation**: Follow phase-wise approach in architecture document

## Notes

- This project prioritizes compliance and accuracy over advanced features
- All responses must be factual and source-backed
- System must refuse any advisory or recommendation requests
- Regular compliance audits and monitoring are essential
