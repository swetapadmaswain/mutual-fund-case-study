# Streamlit Cloud Deployment Guide

## 🚀 Deployment Overview

This guide will help you deploy the Mutual Fund AI Assistant to Streamlit Cloud.

## 📋 Prerequisites

### ✅ Files Ready
- `streamlit_app.py` - Main application
- `streamlit_requirements.txt` - Dependencies
- `.streamlit/config.toml` - Configuration
- `.streamlit/secrets.toml` - Local secrets template

### ✅ Dependencies Installed
- Streamlit 1.57.0+
- All required packages from requirements.txt

### ✅ Local Testing
- Application imports successfully
- All modules load without errors

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Recommended)
**Best for:** Quick deployment, free tier, automatic scaling

**Steps:**
1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Connect your GitHub account
3. Select repository: `swetapadmaswain/mutual-fund-case-study`
4. Configure secrets in Streamlit Cloud dashboard:
   - `GROQ_API_KEY` - Your Groq API key
   - `API_BASE_URL` - Groq API base URL (optional)
   - `EMAIL_USERNAME` - Email for notifications (optional)
   - `EMAIL_PASSWORD` - Email app password (optional)
   - `NOTIFICATION_EMAIL` - Notification email (optional)
5. Click "Deploy"

**Expected URL:** `https://mutual-fund-ai-assistant.streamlit.app`

### Option 2: Manual Deployment
**Best for:** Custom domains, full control

**Steps:**
1. Clone repository locally
2. Install dependencies: `pip install -r streamlit_requirements.txt`
3. Set environment variables
4. Run: `streamlit run streamlit_app.py`

### Option 3: Docker Deployment
**Best for:** Consistent environments, containerization

**Steps:**
1. Create Dockerfile
2. Build image
3. Deploy to container registry
4. Run container

## 🔧 Configuration

### Required Secrets
```toml
[secrets]
GROQ_API_KEY = "your_groq_api_key_here"
API_BASE_URL = "https://api.groq.com/openai/v1"
```

### Optional Secrets
```toml
[secrets]
EMAIL_USERNAME = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
NOTIFICATION_EMAIL = "notification@example.com"
```

## 📱 Application Features

### ✅ Working Features
- Chat interface with message history
- Factual knowledge base for HDFC Mutual Funds
- AI-powered responses via Groq
- Compliance checking for investment advice
- User session management
- Example questions sidebar
- Real-time typing indicators
- Message metadata display

### 🔧 Technical Stack
- **Frontend:** Streamlit 1.57.0
- **Backend:** Python 3.9+
- **AI:** Groq API
- **Data:** JSON knowledge base
- **Styling:** Custom CSS (ChatGPT-style)

## 🚀 Deployment Instructions

### Step 1: Prepare Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Streamlit Cloud Setup
1. Visit [Streamlit Cloud](https://share.streamlit.io/)
2. Click "New app"
3. Connect GitHub account
4. Select repository: `swetapadmaswain/mutual-fund-case-study`
5. Set main file path: `streamlit_app.py`
6. Configure Python version: `3.9`

### Step 3: Configure Secrets
In Streamlit Cloud dashboard, add:
- `GROQ_API_KEY` - Required for AI responses
- `API_BASE_URL` - Optional, defaults to Groq API
- `EMAIL_USERNAME` - Optional, for notifications
- `EMAIL_PASSWORD` - Optional, for notifications
- `NOTIFICATION_EMAIL` - Optional, for notifications

### Step 4: Deploy
1. Click "Deploy" in Streamlit Cloud
2. Wait for deployment to complete
3. Test the deployed application

## 🧪 Testing

### Local Testing
```bash
# Test locally before deployment
streamlit run streamlit_app.py
```

### Deployment Testing
1. Visit deployed URL
2. Test chat functionality
3. Verify AI responses work
4. Check compliance features
5. Test example questions

## 📊 Monitoring

### Application Metrics
- User engagement
- Response times
- Error rates
- API usage

### Health Checks
- Application availability
- API connectivity
- Performance benchmarks

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem:** ModuleNotFoundError
**Solution:** Ensure all dependencies are installed
```bash
pip install -r streamlit_requirements.txt
```

#### 2. API Key Issues
**Problem:** Authentication errors
**Solution:** Verify GROQ_API_KEY is correctly set
- Check Streamlit Cloud secrets
- Verify API key is valid

#### 3. Styling Issues
**Problem:** CSS not loading
**Solution:** Ensure custom CSS is properly formatted
- Check for syntax errors in CSS

#### 4. Performance Issues
**Problem:** Slow responses
**Solution:** Check API rate limits
- Optimize API calls
- Consider caching

### Debug Mode
Enable debug mode by setting:
```python
import streamlit as st
st.set_option('logger.level', 'debug')
```

## 📚 Resources

### Documentation
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cloud Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started)
- [Deployment Tutorial](https://docs.streamlit.io/knowledge-base/tutorials/deploy)

### Support
- [Streamlit Community](https://discuss.streamlit.io/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)

## 🎯 Success Criteria

### ✅ Deployment Success
- Application loads without errors
- Chat interface works
- AI responses are generated
- All secrets are properly configured
- No console errors

### ✅ Performance Success
- Page loads in < 3 seconds
- AI responses in < 5 seconds
- No memory leaks
- Smooth user experience

## 🔄 Next Steps

### Post-Deployment
1. **Monitor Performance**
   - Set up analytics
   - Track user engagement
   - Monitor error rates

2. **Enhance Features**
   - Add more mutual fund data
   - Improve AI responses
   - Add file upload capabilities

3. **Scale Infrastructure**
   - Monitor resource usage
   - Optimize for higher traffic
   - Consider CDN for static assets

4. **Security**
   - Regularly update dependencies
   - Monitor for vulnerabilities
   - Implement rate limiting

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review Streamlit Cloud logs
3. Test locally first
4. Check GitHub repository for updates

---

**Deployment Target:** `https://mutual-fund-ai-assistant.streamlit.app`

**Repository:** `https://github.com/swetapadmaswain/mutual-fund-case-study`

**Last Updated:** May 9, 2026
