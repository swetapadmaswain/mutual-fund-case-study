"""
Script to run the Phase 4 Frontend Interface
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to run the Streamlit frontend."""
    
    # Set environment variables
    os.environ.setdefault('API_BASE_URL', 'http://localhost:5000/api/v1')
    os.environ.setdefault('API_KEY', 'demo-api-key')
    
    print(f"🎨 Starting Mutual Fund FAQ Assistant Frontend")
    print(f"🌐 Frontend will be available at: http://localhost:8501")
    print(f"🔗 Backend API: {os.environ['API_BASE_URL']}")
    print(f"🔑 API Key: {os.environ['API_KEY']}")
    print(f"\n📋 Features:")
    print(f"   - Clean, minimal interface")
    print(f"   - Query input with example questions")
    print(f"   - Response display with source links")
    print(f"   - System health monitoring")
    print(f"   - Query history tracking")
    print(f"   - Mobile-responsive design")
    print(f"\n⚠️  Make sure the backend API server is running first!")
    print(f"   Run: python run_api.py")
    print(f"\n⏹️  Press Ctrl+C to stop the frontend")
    print("=" * 60)
    
    frontend_dir = Path(__file__).parent / "frontend"
    app_file = frontend_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ Frontend app not found at: {app_file}")
        return 1
    
    try:
        # Run streamlit
        cmd = [
            "streamlit", "run", str(app_file),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"🚀 Starting Streamlit with command: {' '.join(cmd)}")
        
        # Change to frontend directory
        original_cwd = os.getcwd()
        os.chdir(frontend_dir)
        
        try:
            subprocess.run(cmd, check=True)
        finally:
            os.chdir(original_cwd)
            
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit error: {e}")
        return 1
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it with:")
        print("   pip install streamlit")
        return 1
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
