import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit Cloud configuration
STREAMLIT_CONFIG = {
    "title": "Mutual Fund AI Assistant",
    "description": "AI-powered mutual fund assistant with factual knowledge base",
    "author": "Sweta Padma Swain",
    "repository": "https://github.com/swetapadmaswain/mutual-fund-case-study",
    "license": "MIT"
}

# Required secrets for Streamlit Cloud
REQUIRED_SECRETS = [
    "GROQ_API_KEY",
    "API_BASE_URL"
]

def get_secrets_status():
    """Check if required secrets are configured"""
    status = {}
    missing = []
    
    for secret in REQUIRED_SECRETS:
        value = os.getenv(secret)
        if value:
            status[secret] = "configured"
        else:
            status[secret] = "missing"
            missing.append(secret)
    
    return {
        "status": "configured" if not missing else "incomplete",
        "missing_secrets": missing,
        "details": status
    }

def print_deployment_checklist():
    """Print deployment checklist"""
    print("Streamlit Cloud Deployment Checklist")
    print("=" * 50)
    
    secrets_status = get_secrets_status()
    
    print(f"Secrets Status: {secrets_status['status'].upper()}")
    if secrets_status['missing_secrets']:
        print("Missing Secrets:")
        for secret in secrets_status['missing_secrets']:
            print(f"   - {secret}")
    else:
        print("All required secrets are configured")
    
    print("\nFiles Ready:")
    print("   streamlit_app.py - Main application")
    print("   streamlit_requirements.txt - Dependencies")
    print("   .streamlit/config.toml - Configuration")
    
    print("\nDeployment Options:")
    print("   1. Streamlit Cloud (Recommended)")
    print("   2. AWS EC2")
    print("   3. Heroku")
    print("   4. Docker")
    
    print("\nNext Steps:")
    print("   1. Set up secrets in Streamlit Cloud")
    print("   2. Deploy to Streamlit Cloud")
    print("   3. Test deployed application")
    print("   4. Monitor performance")
    
    print("=" * 50)

if __name__ == "__main__":
    print_deployment_checklist()
