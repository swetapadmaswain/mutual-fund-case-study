"""
Local Setup Script for Mutual Fund AI Assistant
This script helps configure the environment for local development
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Setup local environment configuration"""
    print("Setting up Mutual Fund AI Assistant for local development...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("[ERROR] .env file not found. Creating from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("[OK] Created .env file from .env.example")
        else:
            print("[ERROR] .env.example not found. Please create .env file manually.")
            return False
    
    # Check Streamlit secrets
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        with open(secrets_file, 'r') as f:
            content = f.read()
            if "your_groq_api_key_here" in content:
                print("[WARNING] GROQ_API_KEY not configured in .streamlit/secrets.toml")
                print("[INFO] App will run in DEMO MODE without AI responses")
                print("[INFO] To enable AI, edit .streamlit/secrets.toml and add your Groq API key")
                print("       You can get a free API key from: https://console.groq.com/")
                print("[INFO] You can get started anyway - the app will work with demo mode")
        print("[OK] Streamlit secrets file exists")
    else:
        print("[ERROR] .streamlit/secrets.toml not found")
        return False
    
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"[ERROR] Python 3.9+ required, found {sys.version}")
        return False
    print(f"[OK] Python version: {sys.version}")
    
    # Check required packages
    required_packages = ['streamlit', 'groq', 'requests', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"[ERROR] Missing packages: {', '.join(missing_packages)}")
        print("[INFO] Installing missing packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Packages installed")
    else:
        print("[OK] All required packages installed")
    
    print("\n[OK] Setup complete! You can now run the app with:")
    print("     streamlit run streamlit_app.py")
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)