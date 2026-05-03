"""
Flask application factory for the Mutual Fund FAQ Assistant API.
"""

import os
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import config
from .middleware import setup_middleware
from .routes import api_bp

def create_app(config_name=None):
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration name (development, testing, production)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize configuration
    config[config_name].init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Setup middleware
    setup_middleware(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup CLI commands
    setup_cli(app)
    
    return app

def setup_logging(app):
    """Setup logging configuration."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE')
    
    # Create logs directory
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Set Flask logger
    app.logger.setLevel(getattr(logging, log_level))

def register_blueprints(app):
    """Register application blueprints."""
    app.register_blueprint(api_bp, url_prefix=app.config.get('API_PREFIX', '/api/v1'))

def setup_error_handlers(app):
    """Setup global error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500

def setup_cli(app):
    """Setup CLI commands."""
    
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        print("Database initialized (placeholder)")
    
    @app.cli.command()
    def run_phase3_tests():
        """Run Phase 3 integration tests."""
        import asyncio
        from ..rag.query_processing.main import Phase3Pipeline
        
        print("Running Phase 3 integration tests...")
        pipeline = Phase3Pipeline()
        result = asyncio.run(pipeline.run_pipeline())
        
        if result.success:
            print("✅ Phase 3 tests passed!")
        else:
            print("❌ Phase 3 tests failed!")
    
    @app.cli.command()
    def health_check():
        """Perform health check."""
        import asyncio
        from ..rag.query_processing.main import Phase3Pipeline
        
        print("Performing health check...")
        pipeline = Phase3Pipeline()
        
        # Check individual components
        classifier_health = asyncio.run(pipeline.query_classifier.health_check())
        generator_health = asyncio.run(pipeline.response_generator.health_check())
        formatter_health = asyncio.run(pipeline.response_formatter.health_check())
        compliance_health = asyncio.run(pipeline.compliance_safety.health_check())
        
        print(f"Query Classifier: {classifier_health['status']}")
        print(f"Response Generator: {generator_health['status']}")
        print(f"Response Formatter: {formatter_health['status']}")
        print(f"Compliance Safety: {compliance_health['status']}")
        
        overall_status = 'healthy' if all(
            health['status'] == 'healthy' for health in 
            [classifier_health, generator_health, formatter_health, compliance_health]
        ) else 'degraded'
        
        print(f"Overall Status: {overall_status}")

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False)
    )
