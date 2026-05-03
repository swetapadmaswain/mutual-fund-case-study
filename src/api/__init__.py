"""
API Layer for Mutual Fund FAQ Assistant

Provides RESTful API endpoints for the frontend to interact with the backend services.
"""

from .app import create_app
from .routes import api_bp
from .middleware import setup_middleware
from .config import Config

__all__ = [
    "create_app",
    "api_bp", 
    "setup_middleware",
    "Config"
]

__version__ = "4.0.0"
