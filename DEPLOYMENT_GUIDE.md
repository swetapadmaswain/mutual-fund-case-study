# Mutual Fund AI Assistant - Deployment Guide

## Local Development

### Prerequisites
- Python 3.9 or higher
- Git
- Internet connection

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/swetapadmaswain/mutual-fund-case-study.git
cd mutual-fund-case-study
```

2. **Run the setup script**
```bash
python setup_local.py
```

3. **Configure API Key (Optional but Recommended)**
Edit `.streamlit/secrets.toml` and add your Groq API key:
```toml
GROQ_API_KEY = "your_actual_groq_api_key_here"
```
Get a free API key from: https://console.groq.com/

4. **Run the application**
```bash
streamlit run streamlit_app.py
```

The app will be available at http://localhost:8501

### Demo Mode
Without an API key, the app runs in demo mode using a built-in factual knowledge base. It can answer questions about:
- HDFC Mutual Fund expense ratios
- NAV information
- SIP processes
- Exit loads and lock-in periods

## Production Deployment

### Option 1: Streamlit Cloud (Recommended)

#### Step 1: Prepare Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

#### Step 2: Deploy via Streamlit Cloud
1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `swetapadmaswain/mutual-fund-case-study`
5. Set main file path: `streamlit_app.py`
6. Click "Deploy"

#### Step 3: Configure Secrets
In Streamlit Cloud dashboard, add these secrets:
- `GROQ_API_KEY` - Your Groq API key (required for AI responses)
- `API_BASE_URL` - Optional, defaults to https://api.groq.com

#### Expected URL
https://mutual-fund-ai-assistant.streamlit.app

### Option 2: Manual Deployment

#### VPS/Server Deployment
```bash
# 1. Set up server (Ubuntu example)
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip nginx -y

# 2. Clone repository
git clone https://github.com/swetapadmaswain/mutual-fund-case-study.git
cd mutual-fund-case-study

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r streamlit_requirements.txt

# 5. Configure environment
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your API keys

# 6. Run with Streamlit
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

#### Docker Deployment
```bash
# Build Docker image
docker build -t mutual-fund-assistant .

# Run container
docker run -p 8501:8501 -e GROQ_API_KEY=your_key mutual-fund-assistant
```

## Environment Variables

### Required for Full Functionality
- `GROQ_API_KEY` - Groq API key for AI responses

### Optional
- `API_BASE_URL` - Custom API base URL
- `EMAIL_USERNAME` - For email notifications
- `EMAIL_PASSWORD` - Email app password
- `NOTIFICATION_EMAIL` - Notification recipient

## Troubleshooting

### Common Issues

1. **Import Errors**
```bash
pip install -r streamlit_requirements.txt
```

2. **API Key Issues**
- Verify GROQ_API_KEY is correctly set
- Check that the key is valid and active
- Ensure the key has proper permissions

3. **Port Conflicts**
```bash
# Use a different port
streamlit run streamlit_app.py --server.port=8502
```

4. **Dependency Conflicts**
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r streamlit_requirements.txt
```

## Monitoring

### Application Health
- Check logs in Streamlit Cloud dashboard
- Monitor API usage in Groq console
- Track user engagement through built-in statistics

### Performance Optimization
- Enable caching for better performance
- Monitor response times
- Scale resources based on traffic

## Security Best Practices

1. **Never commit API keys** to repository
2. **Use environment variables** for sensitive data
3. **Enable SSL/TLS** for production deployments
4. **Regular updates** of dependencies
5. **Monitor** for unusual activity

## Post-Deployment Checklist

- [ ] Application loads without errors
- [ ] Chat interface works correctly
- [ ] AI responses are generated (if API key configured)
- [ ] Fallback to demo mode works (without API key)
- [ ] All secrets are properly configured
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] Mobile responsiveness works

## Support

For issues:
1. Check the troubleshooting section
2. Review logs in the Streamlit Cloud dashboard
3. Test locally first
4. Check GitHub repository for updates

## Cost Considerations

### Groq API
- Free tier available
- Pay-per-use beyond free tier
- Monitor usage to control costs

### Streamlit Cloud
- Free tier available
- Resource limits on free tier
- Upgrade options for higher traffic

## Scaling

### For Higher Traffic
1. Upgrade Streamlit Cloud plan
2. Implement caching strategies
3. Consider CDN for static assets
4. Optimize API calls
5. Add load balancing if needed

---

**Last Updated**: 2026-09-21
**Version**: 1.0