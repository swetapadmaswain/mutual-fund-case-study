"""
Script to run the Phase 4 Backend API Server
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.app import create_app

def main():
    """Main function to run the API server."""
    
    # Set environment variables
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('SECRET_KEY', 'demo-secret-key-for-development')
    os.environ.setdefault('HOST', '0.0.0.0')
    os.environ.setdefault('PORT', '5000')
    os.environ.setdefault('DEBUG', 'True')
    
    # Create and run app
    app = create_app()
    
    print(f"🚀 Starting Mutual Fund FAQ Assistant API Server")
    print(f"📍 Server will be available at: http://{os.environ['HOST']}:{os.environ['PORT']}")
    print(f"🔧 Environment: {os.environ['FLASK_ENV']}")
    print(f"📊 API Endpoints:")
    print(f"   - POST /api/v1/query - Process user queries")
    print(f"   - GET  /api/v1/examples - Get example questions")
    print(f"   - GET  /api/v1/stats - Get API statistics")
    print(f"   - GET  /health - Health check")
    print(f"   - GET  /metrics - Prometheus metrics")
    print(f"   - GET  /info - App information")
    print(f"\n🔑 API Key: 'demo-api-key' (for development)")
    print(f"\n⏹️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(
            host=app.config.get('HOST', '0.0.0.0'),
            port=app.config.get('PORT', 5000),
            debug=app.config.get('DEBUG', False)
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
