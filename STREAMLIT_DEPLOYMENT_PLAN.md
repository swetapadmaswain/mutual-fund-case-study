# Mutual Fund AI Assistant - Streamlit Deployment Plan

## 📋 Project Overview

This Streamlit deployment plan converts the Flask-based Mutual Fund AI Assistant into a unified Streamlit application that combines both frontend and backend functionality.

## 🚀 Streamlit Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │────│   Groq API      │────│   User Browser  │
│   Application   │    │   (External)     │    │   (Web Interface)│
│   (Python)      │    │   (AI Service)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Phase 1: Streamlit Application Development

### 1.1 Create Main Streamlit App

```python
# streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime
import os
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Mutual Fund AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-style interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #3b82f6;
        color: white;
        margin-left: 20%;
    }
    .ai-message {
        background-color: #f1f5f9;
        color: #1f2937;
        margin-right: 20%;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .confidence-badge {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .typing-indicator {
        color: #6b7280;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Groq client
@st.cache_resource
def get_groq_client():
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        return Groq(api_key=api_key)
    return None

# Knowledge base
FACTUAL_KNOWLEDGE = {
    "expense_ratios": {
        "HDFC Mid Cap Fund": {"regular": "1.50%", "direct": "0.95%"},
        "HDFC Large Cap Fund": {"regular": "1.62%", "direct": "1.00%"},
        "HDFC Small Cap Fund": {"regular": "1.75%", "direct": "1.15%"},
        "HDFC Equity Fund": {"regular": "1.50%", "direct": "0.95%"}
    },
    "nav_info": {
        "HDFC Mid Cap Fund": {
            "regular": "₹145.67 (as of last trading day)",
            "direct": "₹148.23 (as of last trading day)"
        }
    },
    "sip_minimums": {
        "default": "₹500 per month",
        "special": "₹1,000 per month (for some funds)"
    }
}

def get_factual_response(query):
    """Get factual response from knowledge base"""
    query_lower = query.lower()
    
    # Expense ratio queries
    if "expense ratio" in query_lower:
        for fund_name, ratios in FACTUAL_KNOWLEDGE["expense_ratios"].items():
            if fund_name.lower() in query_lower:
                return f"The expense ratio of {fund_name} is {ratios['regular']} for Regular Plan and {ratios['direct']} for Direct Plan."
    
    # NAV queries
    if "nav" in query_lower:
        for fund_name, nav_data in FACTUAL_KNOWLEDGE["nav_info"].items():
            if fund_name.lower() in query_lower:
                return f"The NAV of {fund_name} is {nav_data['regular']} (Regular) and {nav_data['direct']} (Direct)."
    
    # SIP queries
    if "sip" in query_lower and ("minimum" in query_lower or "amount" in query_lower):
        return f"The minimum SIP amount is {FACTUAL_KNOWLEDGE['sip_minimums']['default']}. {FACTUAL_KNOWLEDGE['sip_minimums']['special']}."
    
    return None

def generate_ai_response(query):
    """Generate AI response using Groq"""
    client = get_groq_client()
    if not client:
        return "Groq API is not configured. Please set GROQ_API_KEY environment variable.", "demo_mode"
    
    try:
        prompt = f"""
You are an expert HDFC Mutual Fund research analyst. Provide comprehensive, detailed responses to user questions about HDFC Mutual Funds.

User question: {query}

Provide a helpful, factual response:"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert HDFC Mutual Fund research analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.4
        )
        
        return response.choices[0].message.content.strip(), "groq_generated"
        
    except Exception as e:
        return f"Error connecting to AI service: {str(e)}", "error"

# Main application
def main():
    st.title("🤖 Mutual Fund AI Assistant")
    st.markdown("Powered by Groq AI - Ask questions about HDFC Mutual Funds")
    
    # Check API status
    client = get_groq_client()
    if client:
        st.success("✅ Groq API Connected")
    else:
        st.warning("⚠️ Groq API not configured. Set GROQ_API_KEY environment variable.")
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Example questions
    with st.sidebar:
        st.header("💡 Example Questions")
        examples = [
            "What is the expense ratio of HDFC Mid Cap Fund?",
            "What is the NAV of HDFC Mid Cap Fund?",
            "What are the benefits of SIP investment?",
            "How to start SIP in HDFC Mutual Fund?",
            "What is the minimum SIP amount?"
        ]
        
        for example in examples:
            if st.button(example):
                st.session_state.messages.append({"role": "user", "content": example})
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about HDFC Mutual Funds..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                # Try factual response first
                factual_response = get_factual_response(prompt)
                if factual_response:
                    response = factual_response
                    response_type = "factual"
                else:
                    response, response_type = generate_ai_response(prompt)
            
            st.markdown(response)
            
            # Add metadata
            if response_type == "factual":
                st.caption("📊 Factual Knowledge Base")
            elif response_type == "groq_generated":
                st.caption("🤖 AI Generated via Groq")
            else:
                st.caption("⚠️ Demo Mode")
        
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
```

### 1.2 Requirements File

```txt
# streamlit_requirements.txt
streamlit==1.28.0
groq==1.2.0
requests==2.31.0
python-dotenv==1.0.0
```

## 🚀 Phase 2: Local Development Setup

### 2.1 Environment Setup

```bash
# 1. Create virtual environment
python -m venv streamlit_env
source streamlit_env/bin/activate  # On Windows: streamlit_env\Scripts\activate

# 2. Install dependencies
pip install -r streamlit_requirements.txt

# 3. Set environment variables
export GROQ_API_KEY="your_groq_api_key_here"
# On Windows: set GROQ_API_KEY="your_groq_api_key_here"

# 4. Run Streamlit app
streamlit run streamlit_app.py
```

### 2.2 Configuration File

```python
# config.py
import os

class Config:
    # Groq API Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = "llama-3.3-70b-versatile"
    
    # Streamlit Configuration
    PAGE_TITLE = "Mutual Fund AI Assistant"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    
    # Application Settings
    MAX_TOKENS = 600
    TEMPERATURE = 0.4
    TIMEOUT = 30
```

## 🌐 Phase 3: Cloud Deployment Options

### 3.1 Streamlit Cloud (Recommended)

**Step 1: Prepare for Deployment**
```bash
# 1. Create requirements.txt
pip freeze > requirements.txt

# 2. Create secrets management
# In Streamlit Cloud: Settings > Secrets > Add new secret
# Secret name: GROQ_API_KEY
# Value: your_actual_groq_api_key
```

**Step 2: Deploy to Streamlit Cloud**
```bash
# 1. Install Streamlit CLI
pip install streamlit

# 2. Login to Streamlit Cloud
streamlit login

# 3. Deploy your app
streamlit deploy

# 4. Or deploy via GitHub integration
# Connect your GitHub repository to Streamlit Cloud
```

**Step 3: Configuration in Streamlit Cloud**
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#3b82f6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f1f5f9"
textColor = "#1f2937"

[server]
headless = true
port = 8501
baseUrlPath = ""

[browser]
gatherUsageStats = false
```

### 3.2 AWS EC2 Deployment

**Step 1: Server Setup**
```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip nginx -y
curl https://bootstrap.pypa.io/get-pip.py | sudo python3

# 4. Install Streamlit
sudo pip3 install streamlit
```

**Step 2: Application Setup**
```bash
# 1. Create app directory
sudo mkdir -p /opt/streamlit-app
sudo chown ubuntu:ubuntu /opt/streamlit-app
cd /opt/streamlit-app

# 2. Clone repository
git clone https://github.com/your-username/mutual-fund-case-study.git .

# 3. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r streamlit_requirements.txt

# 4. Create service script
cat > run_streamlit.sh << EOF
#!/bin/bash
cd /opt/streamlit-app
source venv/bin/activate
export GROQ_API_KEY="your_api_key_here"
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
EOF

chmod +x run_streamlit.sh
```

**Step 3: Systemd Service**
```bash
# Create systemd service
sudo cat > /etc/systemd/system/streamlit-app.service << EOF
[Unit]
Description=Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/streamlit-app
Environment=PATH=/opt/streamlit-app/venv/bin
ExecStart=/opt/streamlit-app/run_streamlit.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable streamlit-app
sudo systemctl start streamlit-app
sudo systemctl status streamlit-app
```

**Step 4: Nginx Reverse Proxy**
```bash
# Create Nginx config
sudo cat > /etc/nginx/sites-available/streamlit-app << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/streamlit-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.3 Heroku Deployment

**Step 1: Prepare for Heroku**
```bash
# 1. Create Procfile
echo "web: streamlit run streamlit_app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# 2. Create runtime.txt
echo "python-3.9.16" > runtime.txt

# 3. Update requirements.txt
pip freeze > requirements.txt
```

**Step 2: Deploy to Heroku**
```bash
# 1. Install Heroku CLI
# Download from https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create app
heroku create your-app-name

# 4. Set environment variables
heroku config:set GROQ_API_KEY="your_api_key_here"

# 5. Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 6. Open app
heroku open
```

### 3.4 Docker Deployment

**Step 1: Create Dockerfile**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Environment variables
ENV GROQ_API_KEY="your_api_key_here"

# Run the application
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Step 2: Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  streamlit-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

**Step 3: Deploy with Docker**
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔒 Phase 4: Security Configuration

### 4.1 Environment Variables Management

```python
# .env (local development)
GROQ_API_KEY=your_groq_api_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 4.2 Streamlit Security Settings

```python
# In streamlit_app.py
import streamlit as st

# Security configurations
st.set_page_config(
    initial_sidebar_state="collapsed",
    menu_items={
        'Get help': None,
        'Report a bug': "https://github.com/your-username/issues",
        'About': "Mutual Fund AI Assistant v1.0"
    }
)

# Disable telemetry
import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
```

### 4.3 Input Validation

```python
def validate_input(text):
    """Validate user input for security"""
    if not text or len(text.strip()) == 0:
        return False
    if len(text) > 1000:  # Reasonable limit
        return False
    # Add more validation as needed
    return True

# In main app
if prompt := st.chat_input("Ask about HDFC Mutual Funds..."):
    if validate_input(prompt):
        # Process the input
        pass
    else:
        st.error("Invalid input. Please enter a valid question.")
```

## 📊 Phase 5: Performance Optimization

### 5.1 Caching Strategy

```python
import streamlit as st
from functools import lru_cache

# Cache expensive operations
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_factual_data():
    """Cache factual knowledge base"""
    return FACTUAL_KNOWLEDGE

@st.cache_resource(ttl=86400)  # Cache for 24 hours
def get_groq_client():
    """Cache Groq client"""
    return Groq(api_key=os.getenv('GROQ_API_KEY'))
```

### 5.2 Session State Management

```python
# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'preferences' not in st.session_state:
    st.session_state.preferences = {
        'theme': 'light',
        'model': 'llama-3.3-70b-versatile'
    }
```

### 5.3 Resource Management

```python
# Limit concurrent requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def process_query_async(query):
    """Process query asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, generate_ai_response, query)
```

## 📋 Phase 6: Monitoring & Logging

### 6.1 Application Logging

```python
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# In main app
logger.info(f"User query: {prompt}")
logger.info(f"Response type: {response_type}")
```

### 6.2 Performance Monitoring

```python
import time
from datetime import datetime

def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        performance_data = {
            'function': func.__name__,
            'duration': end_time - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log or send to monitoring service
        logger.info(f"Performance: {performance_data}")
        
        return result
    return wrapper

# Apply to AI response generation
@monitor_performance
def generate_ai_response(query):
    # Existing code
    pass
```

## 🚀 Phase 7: Deployment Automation

### 7.1 GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy Streamlit App

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r streamlit_requirements.txt
    
    - name: Deploy to Streamlit Cloud
      env:
        STREAMLIT_API_KEY: ${{ secrets.STREAMLIT_API_KEY }}
      run: |
        streamlit deploy
```

### 7.2 Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Deploying Streamlit App..."

# Pull latest changes
git pull origin main

# Install dependencies
source venv/bin/activate
pip install -r streamlit_requirements.txt

# Run tests
python -m pytest tests/

# Restart service
sudo systemctl restart streamlit-app

echo "✅ Deployment completed!"
```

## 📊 Phase 8: Testing & Validation

### 8.1 Unit Tests

```python
# tests/test_app.py
import pytest
import streamlit_app as app

def test_get_factual_response():
    """Test factual response generation"""
    response = app.get_factual_response("What is the expense ratio of HDFC Mid Cap Fund?")
    assert "1.50%" in response
    assert "0.95%" in response

def test_validate_input():
    """Test input validation"""
    assert app.validate_input("Valid question") == True
    assert app.validate_input("") == False
    assert app.validate_input("a" * 1001) == False
```

### 8.2 Integration Tests

```python
# tests/test_integration.py
import pytest
import requests

def test_api_health():
    """Test API health endpoint"""
    response = requests.get("http://localhost:8501")
    assert response.status_code == 200

def test_chat_functionality():
    """Test chat functionality"""
    response = requests.post("http://localhost:8501/api/chat", 
                           json={"message": "Test question"})
    assert response.status_code == 200
    assert "response" in response.json()
```

## 🎯 Phase 9: Maintenance & Updates

### 9.1 Regular Maintenance Tasks

```bash
# Weekly maintenance script
#!/bin/bash

# Update dependencies
pip install --upgrade -r streamlit_requirements.txt

# Clean cache
streamlit cache clear

# Restart service
sudo systemctl restart streamlit-app

# Check logs
sudo journalctl -u streamlit-app --since "1 day ago"
```

### 9.2 Backup Strategy

```bash
# Backup script
#!/bin/bash

# Create backup directory
BACKUP_DIR="/backup/streamlit-app/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup application files
cp -r /opt/streamlit-app $BACKUP_DIR/

# Backup database (if applicable)
# pg_dump streamlit_db > $BACKUP_DIR/database.sql

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Clean old backups (keep last 30 days)
find /backup/streamlit-app -name "*.tar.gz" -mtime +30 -delete
```

## 📋 Phase 10: Scaling & Performance

### 10.1 Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  streamlit-app:
    build: .
    ports:
      - "8501-8505:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    deploy:
      replicas: 3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - streamlit-app
```

### 10.2 Performance Optimization

```python
# Optimize for production
import streamlit as st

# Disable telemetry
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'warning'

# Optimize caching
@st.cache_data(ttl=3600, max_entries=100)
def expensive_operation(data):
    # Expensive computation
    return result

# Lazy loading
def load_large_dataset():
    """Load large dataset only when needed"""
    if 'large_dataset' not in st.session_state:
        st.session_state.large_dataset = pd.read_csv('large_dataset.csv')
    return st.session_state.large_dataset
```

## 🚀 Quick Start Guide

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/your-username/mutual-fund-case-study.git
cd mutual-fund-case-study

# 2. Setup environment
python -m venv streamlit_env
source streamlit_env/bin/activate
pip install -r streamlit_requirements.txt

# 3. Set API key
export GROQ_API_KEY="your_api_key_here"

# 4. Run app
streamlit run streamlit_app.py
```

### Streamlit Cloud Deployment
```bash
# 1. Install Streamlit CLI
pip install streamlit

# 2. Login and deploy
streamlit login
streamlit deploy
```

### Docker Deployment
```bash
# 1. Build and run
docker-compose up -d

# 2. Access app
open http://localhost:8501
```

## 📊 Deployment Comparison

| Platform | Ease of Use | Cost | Scalability | Customization |
|----------|-------------|------|-------------|---------------|
| Streamlit Cloud | ⭐⭐⭐⭐⭐ | $$ | ⭐⭐⭐ | ⭐⭐ |
| AWS EC2 | ⭐⭐ | $$$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Heroku | ⭐⭐⭐⭐ | $$$ | ⭐⭐⭐ | ⭐⭐⭐ |
| Docker | ⭐⭐ | $$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 Recommended Deployment Path

1. **Development**: Local Streamlit with virtual environment
2. **Testing**: Streamlit Cloud (free tier)
3. **Production**: AWS EC2 with Nginx or Docker
4. **Scaling**: Container orchestration with Kubernetes

---

This Streamlit deployment plan provides a comprehensive guide for deploying the Mutual Fund AI Assistant using Streamlit, from local development to production scaling.
