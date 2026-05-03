# Phase 4 Implementation Guide

## Overview
This document provides detailed implementation guidance for Phase 4 - User Interface Development of the Mutual Fund FAQ Assistant project.

## Architecture Components

### 1. Backend API Layer
- **Files**: `src/api/` directory
- **Purpose**: Provides RESTful API endpoints for frontend integration
- **Key Features**:
  - RESTful API design with Flask
  - Authentication and authorization
  - Request/response validation
  - Error handling and logging
  - Rate limiting and security
  - Monitoring and metrics

### 2. Frontend Interface
- **File**: `frontend/app.py`
- **Purpose**: Streamlit-based user interface
- **Key Features**:
  - Clean, minimal design
  - Query input interface
  - Response display area
  - Example questions
  - System health monitoring
  - Query history

### 3. API Endpoints
- **Query Processing**: `/api/v1/query`
- **Query Classification**: `/api/v1/query/classify`
- **Example Questions**: `/api/v1/examples`
- **API Statistics**: `/api/v1/stats`
- **Response Validation**: `/api/v1/validate`
- **Health Check**: `/api/v1/health/detailed`

## Data Flow

```
Frontend (Streamlit) → API Gateway → Phase 3 Pipeline → Response → Frontend Display
```

## Key Implementation Details

### Backend API Configuration
```python
# API Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
API_VERSION = "v1"
CORS_ORIGINS = ["*"]
RATE_LIMIT = "100/hour"
SECRET_KEY = "your-secret-key"
```

### API Endpoint Structure
```python
# Main Query Endpoint
POST /api/v1/query
{
    "query": "What is the expense ratio of HDFC Mid Cap Fund?",
    "user_context": {
        "session_id": "optional_session_id",
        "user_id": "optional_user_id"
    }
}

# Response Structure
{
    "query": "What is the expense ratio of HDFC Mid Cap Fund?",
    "answer": "The expense ratio is 1.5% for HDFC Mid Cap Fund.",
    "source": "https://hdfcfund.com/factsheet",
    "source_title": "HDFC Fund Factsheet",
    "last_updated": "2024-01-15",
    "disclaimer": "Facts-only. No investment advice.",
    "query_type": "factual",
    "confidence": 0.95,
    "response_time": 1.2,
    "request_id": "uuid",
    "compliance": {
        "approved": true,
        "risk_level": "low",
        "modifications": []
    }
}
```

### Frontend Components
```python
# Main Application Class
class MutualFundFAQApp:
    def __init__(self):
        self.session_state = st.session_state
        self.initialize_session_state()
    
    def render_header(self):
        # Application header with disclaimer
    
    def render_example_questions(self):
        # Clickable example questions
    
    def render_query_input(self):
        # Query input interface with submit/clear buttons
    
    def render_response(self):
        # Response display with source links and metadata
    
    def render_sidebar(self):
        # Query history and system health monitoring
```

### Security and Authentication
```python
# API Key Authentication
@require_api_key
@validate_request_data(['query'])
@handle_errors
@limiter.limit("10/minute")
async def process_query():
    # Query processing logic

# Security Headers
response.headers['X-Content-Type-Options'] = 'nosniff'
response.headers['X-Frame-Options'] = 'DENY'
response.headers['X-XSS-Protection'] = '1; mode=block'
response.headers['Content-Security-Policy'] = "default-src 'self'"
```

### Monitoring and Logging
```python
# Request Logging
@request_logging
def log_request():
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    # Log request details

# Prometheus Metrics
REQUEST_COUNT = prom.Counter('api_requests_total', 'Total API requests')
REQUEST_DURATION = prom.Histogram('api_request_duration_seconds', 'API request duration')
ERROR_COUNT = prom.Counter('api_errors_total', 'Total API errors')
```

## Usage Instructions

### Running the Backend API

1. **Start the API Server**:
```bash
cd src/api
python app.py
```

2. **API Endpoints Available**:
   - `http://localhost:5000/api/v1/query` - Main query processing
   - `http://localhost:5000/api/v1/examples` - Example questions
   - `http://localhost:5000/api/v1/stats` - API statistics
   - `http://localhost:5000/health` - Health check
   - `http://localhost:5000/metrics` - Prometheus metrics

### Running the Frontend

1. **Start Streamlit App**:
```bash
cd frontend
streamlit run app.py
```

2. **Access the Interface**:
   - Open browser to `http://localhost:8501`
   - The interface will connect to the backend API automatically

### API Usage Examples

```python
# Query Processing
import requests

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
}

data = {
    'query': 'What is the expense ratio of HDFC Mid Cap Fund?',
    'user_context': {
        'session_id': 'demo_session'
    }
}

response = requests.post(
    'http://localhost:5000/api/v1/query',
    json=data,
    headers=headers
)

result = response.json()
print(result['answer'])
print(result['source'])
```

## Configuration Options

### Backend Configuration
```python
# Environment Variables
FLASK_ENV=development
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=*
RATE_LIMIT=100/hour
LOG_LEVEL=INFO
OPENAI_API_KEY=your-openai-key
PHASE3_CACHE_DIR=cache
ENABLE_MONITORING=True
```

### Frontend Configuration
```python
# API Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "demo-api-key"

# UI Configuration
PAGE_TITLE = "Mutual Fund FAQ Assistant"
PAGE_ICON = "📊"
LAYOUT = "centered"
```

## Performance Metrics

### Target Performance
- **API Response Time**: < 3 seconds
- **Frontend Load Time**: < 2 seconds
- **Concurrent Users**: 100+
- **API Rate Limit**: 100 requests/hour
- **System Uptime**: > 99%

### Monitoring
```python
# Performance Monitoring
- Request count by endpoint
- Response time distribution
- Error rate tracking
- System resource usage
- API health status
- User session tracking
```

## Testing

### Backend API Testing
```bash
# Run API tests
python -m pytest tests/test_api.py -v

# Test specific endpoints
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-api-key" \
  -d '{"query": "What is the expense ratio?"}'
```

### Frontend Testing
```bash
# Run Streamlit app
streamlit run frontend/app.py

# Test UI components manually
- Query input functionality
- Response display
- Example questions
- System health check
```

## Security Considerations

### API Security
- API key authentication
- Rate limiting
- CORS configuration
- Security headers
- Input validation
- Error handling

### Frontend Security
- Content Security Policy
- XSS protection
- Input sanitization
- Secure API communication
- Session management

## Success Criteria

### Technical Success
- API endpoints functional and tested
- Frontend interface responsive and accessible
- Integration between frontend and backend working
- Performance targets met (<3s response time)
- Security measures implemented
- Monitoring and logging functional

### User Experience Success
- Clean, intuitive interface
- Fast response times
- Clear error messages
- Helpful example questions
- Comprehensive disclaimers
- Mobile-responsive design

### Operational Success
- System health monitoring
- API statistics tracking
- Error logging and alerting
- Graceful error handling
- Scalable architecture
- Documentation complete

## Integration with Previous Phases

### Dependencies
- **Phase 3**: Query processing and response generation
- **Phase 2.6**: Performance optimization and testing
- **Phase 2.5**: Metadata and source management
- **Phase 2.4**: LLM integration
- **Phase 2.3**: Retrieval system
- **Phase 2.2**: Vector storage
- **Phase 2.1**: Document processing

### Data Flow Integration
```
Frontend → API Gateway → Phase 3 Pipeline → Phase 2 Components → Response → Frontend
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check if backend server is running
   - Verify API URL and port
   - Check API key configuration

2. **Frontend Loading Issues**
   - Verify Streamlit installation
   - Check Python dependencies
   - Ensure backend API is accessible

3. **Response Time Issues**
   - Check Phase 3 pipeline performance
   - Monitor system resources
   - Review API logs

4. **Security Issues**
   - Verify API key configuration
   - Check CORS settings
   - Review security headers

### Debug Mode
Enable debug logging:
```bash
# Backend debug mode
FLASK_ENV=development python src/api/app.py

# Frontend debug mode
streamlit run frontend/app.py --logger.level=debug
```

## Deployment

### Production Deployment
```bash
# Backend deployment
gunicorn -w 4 -b 0.0.0.0:5000 src.api.app:create_app()

# Frontend deployment
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0
```

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.api.app:create_app()"]
```

## Success Criteria

### Technical Success
- All API endpoints functional and tested ✅
- Frontend interface responsive and accessible ✅
- Integration between frontend and backend working ✅
- Performance targets met (<3s response time) ✅
- Security measures implemented ✅
- Monitoring and logging functional ✅

### User Experience Success
- Clean, intuitive interface ✅
- Fast response times ✅
- Clear error messages ✅
- Helpful example questions ✅
- Comprehensive disclaimers ✅
- Mobile-responsive design ✅

### Operational Success
- System health monitoring ✅
- API statistics tracking ✅
- Error logging and alerting ✅
- Graceful error handling ✅
- Scalable architecture ✅
- Documentation complete ✅

## Next Steps

After completing Phase 4:

1. **Performance Testing**: Load test the complete system
2. **User Acceptance Testing**: Test with real users
3. **Security Audit**: Perform security assessment
4. **Production Deployment**: Deploy to production environment
5. **Monitoring Setup**: Configure production monitoring
6. **Documentation**: Create user documentation

This implementation provides a complete, production-ready user interface for the Mutual Fund FAQ Assistant with a robust backend API, clean frontend design, comprehensive security measures, and full integration with all previous phases of the system.
