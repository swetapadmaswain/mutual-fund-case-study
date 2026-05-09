#!/usr/bin/env python3
"""
Script to check if GitHub secrets are properly configured
"""
import subprocess
import sys
import json
from pathlib import Path

def create_secret_test_workflow():
    """Create a test workflow to check secrets"""
    workflow_content = """name: 🔐 Test GitHub Secrets

on:
  workflow_dispatch:
    inputs:
      test_type:
        description: 'Type of test to run'
        required: true
        default: 'basic'
        type: choice
        options:
          - basic
          - email
          - api

jobs:
  test-secrets:
    name: 🔍 Test Secrets Configuration
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout repository
      uses: actions/checkout@v4
      
    - name: 🐍 Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: 🔍 Test Basic Secrets
      run: |
        echo "Testing basic secret access..."
        
        # Test GROQ_API_KEY
        if [ -n "$GROQ_API_KEY" ]; then
          echo "✅ GROQ_API_KEY is configured"
          echo "🔑 Key length: ${#GROQ_API_KEY}"
          if [[ "$GROQ_API_KEY" == gsk_* ]]; then
            echo "✅ GROQ_API_KEY format is correct"
          else
            echo "❌ GROQ_API_KEY format may be incorrect"
          fi
        else
          echo "❌ GROQ_API_KEY is missing"
        fi
        
        # Test API_BASE_URL
        if [ -n "$API_BASE_URL" ]; then
          echo "✅ API_BASE_URL is configured"
          echo "🔗 URL: $API_BASE_URL"
        else
          echo "❌ API_BASE_URL is missing"
        fi
        
        # Test EMAIL_USERNAME
        if [ -n "$EMAIL_USERNAME" ]; then
          echo "✅ EMAIL_USERNAME is configured"
          echo "📧 Email: $EMAIL_USERNAME"
        else
          echo "❌ EMAIL_USERNAME is missing"
        fi
        
        # Test EMAIL_PASSWORD
        if [ -n "$EMAIL_PASSWORD" ]; then
          echo "✅ EMAIL_PASSWORD is configured"
          echo "🔐 Password length: ${#EMAIL_PASSWORD}"
        else
          echo "❌ EMAIL_PASSWORD is missing"
        fi
        
        # Test NOTIFICATION_EMAIL
        if [ -n "$NOTIFICATION_EMAIL" ]; then
          echo "✅ NOTIFICATION_EMAIL is configured"
          echo "📧 Notification email: $NOTIFICATION_EMAIL"
        else
          echo "❌ NOTIFICATION_EMAIL is missing"
        fi
        
        echo ""
        echo "📊 Secret Summary:"
        echo "GROQ_API_KEY: $([ -n "$GROQ_API_KEY" ] && echo "✅ Configured" || echo "❌ Missing")"
        echo "API_BASE_URL: $([ -n "$API_BASE_URL" ] && echo "✅ Configured" || echo "❌ Missing")"
        echo "EMAIL_USERNAME: $([ -n "$EMAIL_USERNAME" ] && echo "✅ Configured" || echo "❌ Missing")"
        echo "EMAIL_PASSWORD: $([ -n "$EMAIL_PASSWORD" ] && echo "✅ Configured" || echo "❌ Missing")"
        echo "NOTIFICATION_EMAIL: $([ -n "$NOTIFICATION_EMAIL" ] && echo "✅ Configured" || echo "❌ Missing")"
        
    - name: 📧 Test Email Configuration
      if: github.event.inputs.test_type == 'email' || github.event.inputs.test_type == 'api'
      run: |
        echo "Testing email configuration..."
        
        if [ -n "$EMAIL_USERNAME" ] && [ -n "$EMAIL_PASSWORD" ]; then
          echo "✅ Email credentials available"
          
          # Test basic SMTP connection (without sending email)
          python3 << 'EOF'
import smtplib
import os
from email.mime.text import MIMEText

def test_smtp_connection():
    try:
        username = os.environ.get('EMAIL_USERNAME')
        password = os.environ.get('EMAIL_PASSWORD')
        
        if not username or not password:
            print("❌ Email credentials not available")
            return False
            
        print("🔗 Testing SMTP connection to smtp.gmail.com:587")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        server.quit()
        print("✅ SMTP connection successful")
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

test_smtp_connection()
EOF
        else
          echo "❌ Email credentials not configured"
        fi
        
    - name: 🌐 Test API Configuration
      if: github.event.inputs.test_type == 'api'
      run: |
        echo "Testing API configuration..."
        
        if [ -n "$GROQ_API_KEY" ] && [ -n "$API_BASE_URL" ]; then
          echo "✅ API credentials available"
          
          # Test Groq API connection
          python3 << 'EOF'
import requests
import os
import json

def test_groq_api():
    try:
        api_key = os.environ.get('GROQ_API_KEY')
        base_url = os.environ.get('API_BASE_URL')
        
        if not api_key or not base_url:
            print("❌ API credentials not available")
            return False
            
        print("🔗 Testing Groq API connection...")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Test models endpoint
        response = requests.get(f'{base_url}/models', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Groq API connection successful")
            models = response.json()
            print(f"📊 Available models: {len(models.get('data', []))}")
            
            # Show first few models
            for i, model in enumerate(models.get('data', [])[:3]):
                print(f"  - {model.get('id', 'Unknown')}")
                
            return True
        else:
            print(f"❌ Groq API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

test_groq_api()
EOF
        else
          echo "❌ API credentials not configured"
        fi
        
    - name: 📊 Generate Test Report
      if: always()
      run: |
        echo "📊 Generating test report..."
        
        cat > secret_test_report.json << EOF
        {
          "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
          "repository": "${{ github.repository }}",
          "run_id": "${{ github.run_id }}",
          "test_type": "${{ github.event.inputs.test_type }}",
          "secrets_status": {
            "GROQ_API_KEY": "$([ -n "$GROQ_API_KEY" ] && echo "configured" || echo "missing")",
            "API_BASE_URL": "$([ -n "$API_BASE_URL" ] && echo "configured" || echo "missing")",
            "EMAIL_USERNAME": "$([ -n "$EMAIL_USERNAME" ] && echo "configured" || echo "missing")",
            "EMAIL_PASSWORD": "$([ -n "$EMAIL_PASSWORD" ] && echo "configured" || echo "missing")",
            "NOTIFICATION_EMAIL": "$([ -n "$NOTIFICATION_EMAIL" ] && echo "configured" || echo "missing")"
          },
          "workflow_status": "completed"
        }
        EOF
        
        echo "📄 Test report generated"
        
    - name: 📤 Upload Test Report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: secret-test-report-${{ github.run_number }}
        path: secret_test_report.json
        retention-days: 7
"""
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(exist_ok=True)
    
    with open(workflow_dir / "test_secrets.yml", "w", encoding="utf-8") as f:
        f.write(workflow_content)
    
    print("Created test_secrets.yml workflow")

def main():
    """Main function to check secrets"""
    print("Checking GitHub Secrets Configuration\n")
    
    # Create test workflow
    create_secret_test_workflow()
    
    print("\n📋 Instructions to Check Secrets:")
    print("1. Commit and push the test workflow:")
    print("   git add .github/workflows/test_secrets.yml")
    print("   git commit -m 'Add secrets test workflow'")
    print("   git push origin main")
    print()
    print("2. Go to GitHub Actions tab")
    print("3. Select '🔐 Test GitHub Secrets' workflow")
    print("4. Click 'Run workflow'")
    print("5. Choose test type:")
    print("   - basic: Check if secrets exist")
    print("   - email: Test email configuration")
    print("   - api: Test API connections")
    print()
    print("6. Monitor the workflow results")
    print()
    print("📊 Expected Results:")
    print("✅ All 5 secrets should show as 'configured'")
    print("✅ Email test should show successful SMTP connection")
    print("✅ API test should show successful Groq API connection")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
