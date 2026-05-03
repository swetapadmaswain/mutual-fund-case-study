"""
Middleware for the API layer including authentication, logging, and error handling.
"""

import logging
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional

from flask import Flask, request, g, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import prometheus_client as prom

logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = prom.Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = prom.Histogram('api_request_duration_seconds', 'API request duration')
ACTIVE_CONNECTIONS = prom.Gauge('api_active_connections', 'Active connections')
ERROR_COUNT = prom.Counter('api_errors_total', 'Total API errors', ['error_type'])

class RequestLoggingMiddleware:
    """Middleware for request logging."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize request logging middleware."""
        
        @app.before_request
        def before_request():
            """Log request start time and assign request ID."""
            g.request_id = str(uuid.uuid4())
            g.start_time = time.time()
            g.request_data = {
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8'),
                'user_agent': request.headers.get('User-Agent', ''),
                'remote_addr': get_remote_address(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Request started: {g.request_id} - {request.method} {request.path}")
        
        @app.after_request
        def after_request(response):
            """Log request completion."""
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                log_data = {
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': f"{duration:.3f}s",
                    'remote_addr': getattr(g, 'request_data', {}).get('remote_addr', 'unknown')
                }
                
                logger.info(f"Request completed: {log_data}")
                
                # Update Prometheus metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.path,
                    status=response.status_code
                ).inc()
                REQUEST_DURATION.observe(duration)
            
            return response
        
        @app.errorhandler(Exception)
        def handle_exception(e):
            """Handle exceptions and log them."""
            error_data = {
                'request_id': getattr(g, 'request_id', 'unknown'),
                'error': str(e),
                'path': request.path,
                'method': request.method,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.error(f"Request error: {error_data}")
            
            # Update error metrics
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            
            return jsonify({
                'error': 'Internal server error',
                'request_id': getattr(g, 'request_id', 'unknown')
            }), 500

class SecurityMiddleware:
    """Middleware for security headers and CORS."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security middleware."""
        
        # CORS configuration
        CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to responses."""
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
            
            # Add request ID header
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            
            return response

class RateLimitMiddleware:
    """Middleware for rate limiting."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.limiter = None
        self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize rate limiting middleware."""
        self.limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[app.config.get('RATE_LIMIT', '100/minute')]
        )

def setup_middleware(app: Flask):
    """Setup all middleware for the Flask application."""
    
    # Initialize middleware components
    RequestLoggingMiddleware(app)
    SecurityMiddleware(app)
    RateLimitMiddleware(app)
    
    # Setup monitoring endpoints
    setup_monitoring_endpoints(app)
    
    logger.info("Middleware setup completed")

def setup_monitoring_endpoints(app: Flask):
    """Setup monitoring and health check endpoints."""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config.get('API_VERSION', 'v1')
        })
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint."""
        if app.config.get('ENABLE_MONITORING', True):
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            response = app.response_class(
                response=generate_latest(),
                mimetype=CONTENT_TYPE_LATEST
            )
            return response
        else:
            return jsonify({'error': 'Monitoring disabled'}), 404
    
    @app.route('/info')
    def app_info():
        """Application information endpoint."""
        return jsonify({
            'name': 'Mutual Fund FAQ Assistant API',
            'version': app.config.get('API_VERSION', 'v1'),
            'environment': app.config.get('ENV', 'development'),
            'timestamp': datetime.utcnow().isoformat()
        })

def require_api_key(f):
    """Decorator to require API key for authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        # For now, we'll accept any API key (in production, validate against database)
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Store API key in global context for logging
        g.api_key = api_key
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_request_data(required_fields: list = None):
    """Decorator to validate request data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Invalid JSON data'}), 400
                
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return jsonify({
                            'error': 'Missing required fields',
                            'missing_fields': missing_fields
                        }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def handle_errors(f):
    """Decorator to handle common errors."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except KeyError as e:
            return jsonify({'error': f'Missing required field: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function
