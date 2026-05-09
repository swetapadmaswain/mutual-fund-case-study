#!/usr/bin/env python3
"""
Deploy Streamlit application to Streamlit Cloud
"""
import subprocess
import sys
import os
from pathlib import Path

def check_prerequisites():
    """Check if deployment prerequisites are met"""
    print("Checking deployment prerequisites...")
    
    # Check if streamlit_app.py exists
    if not Path("streamlit_app.py").exists():
        print("ERROR: streamlit_app.py not found")
        return False
    
    # Check if streamlit_requirements.txt exists
    if not Path("streamlit_requirements.txt").exists():
        print("ERROR: streamlit_requirements.txt not found")
        return False
    
    # Check if .streamlit/config.toml exists
    if not Path(".streamlit/config.toml").exists():
        print("ERROR: .streamlit/config.toml not found")
        return False
    
    # Check if streamlit is installed
    try:
        result = subprocess.run([sys.executable, "-m", "streamlit", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: Streamlit not installed")
            return False
        print(f"Streamlit version: {result.stdout.strip()}")
    except Exception as e:
        print(f"ERROR: Cannot check Streamlit version: {e}")
        return False
    
    print("All prerequisites met!")
    return True

def install_dependencies():
    """Install Streamlit dependencies"""
    print("Installing dependencies...")
    
    try:
        # Install streamlit requirements
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: Failed to install dependencies: {result.stderr}")
            return False
        print("Dependencies installed successfully!")
    except Exception as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False
    
    return True

def test_local_app():
    """Test the Streamlit application locally"""
    print("Testing Streamlit application locally...")
    
    try:
        # Test import
        result = subprocess.run([sys.executable, "-c", "import streamlit_app; print('Import successful')"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: Failed to import streamlit_app: {result.stderr}")
            return False
        print("Local test passed!")
    except Exception as e:
        print(f"ERROR: Local test failed: {e}")
        return False
    
    return True

def deploy_to_streamlit_cloud():
    """Deploy to Streamlit Cloud"""
    print("Deploying to Streamlit Cloud...")
    
    try:
        # Check if streamlit is installed
        result = subprocess.run([sys.executable, "-m", "streamlit", "deploy", "--help"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: Streamlit CLI not available for deployment")
            return False
        
        print("Streamlit Cloud deployment command available!")
        print("To deploy to Streamlit Cloud:")
        print("1. Go to https://share.streamlit.io/")
        print("2. Connect your GitHub account")
        print("3. Select this repository: swetapadmaswain/mutual-fund-case-study")
        print("4. Configure secrets in Streamlit Cloud dashboard")
        print("5. Click 'Deploy'")
        
        return True
    except Exception as e:
        print(f"ERROR: Deployment check failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("Streamlit Cloud Deployment")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test local app
    if not test_local_app():
        sys.exit(1)
    
    # Deploy to Streamlit Cloud
    if not deploy_to_streamlit_cloud():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("DEPLOYMENT READY!")
    print("=" * 50)
    
    print("\nNext Steps:")
    print("1. Visit https://share.streamlit.io/")
    print("2. Connect your GitHub account")
    print("3. Select repository: swetapadmaswain/mutual-fund-case-study")
    print("4. Configure secrets in Streamlit Cloud:")
    print("   - GROQ_API_KEY")
    print("   - API_BASE_URL (optional)")
    print("   - EMAIL_USERNAME (optional)")
    print("   - EMAIL_PASSWORD (optional)")
    print("   - NOTIFICATION_EMAIL (optional)")
    print("5. Click 'Deploy'")
    print("6. Test the deployed application")
    
    print("\nDeployment URL will be:")
    print("https://mutual-fund-ai-assistant.streamlit.app")

if __name__ == "__main__":
    main()
