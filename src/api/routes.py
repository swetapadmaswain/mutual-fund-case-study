"""
API routes for the Mutual Fund FAQ Assistant.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify, g
from flask_limiter import Limiter

from .middleware import require_api_key, validate_request_data, handle_errors
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.rag.query_processing.main import Phase3Pipeline
from src.rag.query_processing.query_classifier import QueryType

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)
limiter = Limiter(key_func=lambda: request.remote_addr)

# Initialize Phase 3 pipeline
phase3_pipeline = Phase3Pipeline()

@api_bp.route('/query', methods=['POST'])
@require_api_key
@validate_request_data(['query'])
@handle_errors
@limiter.limit("10/minute")
async def process_query():
    """
    Process a user query and return a response.
    
    Request Body:
    {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?",
        "user_context": {
            "session_id": "optional_session_id",
            "user_id": "optional_user_id"
        }
    }
    
    Response:
    {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?",
        "answer": "The expense ratio is 1.5% for HDFC Mid Cap Fund.",
        "source": "https://hdfcfund.com/factsheet",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.95,
        "response_time": 1.2,
        "request_id": "uuid"
    }
    """
    try:
        data = request.get_json()
        query = data['query']
        user_context = data.get('user_context', {})
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # Classify the query
        classification = phase3_pipeline.query_classifier.classify_query(query)
        
        # Create response context
        from ..rag.query_processing.response_generator import ResponseContext
        response_context = ResponseContext(
            query=query,
            classification=classification,
            retrieved_chunks=[],  # Will be populated by the pipeline
            search_results=[],  # Will be populated by the pipeline
            user_context=user_context,
            session_context=None,
            metadata={'api_request': True}
        )
        
        # Generate response
        response = await phase3_pipeline.response_generator.generate_response(response_context)
        
        # Check compliance
        compliance_result = await phase3_pipeline.compliance_safety.check_compliance(
            query, classification, response
        )
        
        # Format response for API
        if not compliance_result.approved:
            # Return compliance-rejected response
            api_response = {
                'query': query,
                'answer': 'I cannot provide a response to this query due to compliance requirements.',
                'source': '',
                'last_updated': '',
                'disclaimer': 'Response blocked due to compliance requirements.',
                'query_type': classification.query_type.value,
                'confidence': 0.0,
                'response_time': response.response_time,
                'request_id': getattr(g, 'request_id', 'unknown'),
                'compliance': {
                    'approved': False,
                    'risk_level': compliance_result.overall_risk.value,
                    'reasons': [check.details for check in compliance_result.compliance_checks if not check.passed]
                }
            }
        else:
            # Extract source information
            source_url = ''
            source_title = ''
            if response.sources:
                source_url = response.sources[0].get('source_url', '')
                source_title = response.sources[0].get('source_title', '')
            
            # Format successful response
            api_response = {
                'query': query,
                'answer': response.content,
                'source': source_url,
                'source_title': source_title,
                'last_updated': response.sources[0].get('last_updated', '') if response.sources else '',
                'disclaimer': 'Facts-only. No investment advice.',
                'query_type': classification.query_type.value,
                'confidence': response.confidence,
                'response_time': response.response_time,
                'request_id': getattr(g, 'request_id', 'unknown'),
                'compliance': {
                    'approved': True,
                    'risk_level': compliance_result.overall_risk.value,
                    'modifications': compliance_result.modifications
                }
            }
        
        logger.info(f"Query processed successfully: {api_response['request_id']}")
        return jsonify(api_response), 200
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 500

@api_bp.route('/query/classify', methods=['POST'])
@require_api_key
@validate_request_data(['query'])
@handle_errors
@limiter.limit("20/minute")
def classify_query():
    """
    Classify a query without generating a response.
    
    Request Body:
    {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?"
    }
    
    Response:
    {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?",
        "query_type": "factual",
        "intent": "get_expense_ratio",
        "confidence": 0.95,
        "keywords": ["expense", "ratio", "hdfc", "fund"],
        "entities": ["hdfc", "fund"],
        "request_id": "uuid"
    }
    """
    try:
        data = request.get_json()
        query = data['query']
        
        classification = phase3_pipeline.query_classifier.classify_query(query)
        
        response = {
            'query': query,
            'query_type': classification.query_type.value,
            'intent': classification.intent,
            'confidence': classification.confidence,
            'keywords': classification.keywords,
            'entities': classification.entities,
            'subcategory': classification.subcategory,
            'request_id': getattr(g, 'request_id', 'unknown')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}")
        return jsonify({
            'error': 'Failed to classify query',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 500

@api_bp.route('/examples', methods=['GET'])
@require_api_key
@handle_errors
def get_example_queries():
    """
    Get example queries for users.
    
    Response:
    {
        "examples": [
            {
                "query": "What is the expense ratio of HDFC Mid Cap Fund?",
                "category": "factual",
                "description": "Get factual information about fund metrics"
            },
            {
                "query": "How to start SIP in HDFC Mutual Fund?",
                "category": "procedural",
                "description": "Get step-by-step instructions"
            }
        ]
    }
    """
    try:
        examples = [
            {
                'query': 'What is the expense ratio of HDFC Mid Cap Fund?',
                'category': 'factual',
                'description': 'Get factual information about fund metrics'
            },
            {
                'query': 'What is the minimum SIP amount for HDFC Equity Fund?',
                'category': 'factual',
                'description': 'Get factual information about investment requirements'
            },
            {
                'query': 'How to start SIP in HDFC Mutual Fund?',
                'category': 'procedural',
                'description': 'Get step-by-step instructions for starting SIP'
            },
            {
                'query': 'How to download account statement from HDFC Mutual Fund?',
                'category': 'procedural',
                'description': 'Get instructions for downloading statements'
            },
            {
                'query': 'What are the historical returns of HDFC Mid Cap Fund?',
                'category': 'performance',
                'description': 'Get historical performance information'
            }
        ]
        
        return jsonify({'examples': examples}), 200
        
    except Exception as e:
        logger.error(f"Error getting examples: {str(e)}")
        return jsonify({'error': 'Failed to get examples'}), 500

@api_bp.route('/stats', methods=['GET'])
@require_api_key
@handle_errors
def get_api_stats():
    """
    Get API statistics and system health.
    
    Response:
    {
        "api_stats": {
            "total_queries": 1000,
            "successful_queries": 950,
            "average_response_time": 1.2,
            "query_type_distribution": {
                "factual": 60,
                "advisory": 20,
                "procedural": 15,
                "performance": 5
            }
        },
        "system_health": {
            "query_classifier": "healthy",
            "response_generator": "healthy",
            "compliance_safety": "healthy",
            "overall_status": "healthy"
        }
    }
    """
    try:
        # Get statistics from components
        classifier_stats = phase3_pipeline.query_classifier.get_classification_stats()
        generator_stats = phase3_pipeline.response_generator.get_response_stats()
        formatter_stats = phase3_pipeline.response_formatter.get_formatting_stats()
        compliance_stats = phase3_pipeline.compliance_safety.get_compliance_stats()
        
        # Get health status
        classifier_health = phase3_pipeline.query_classifier.health_check()
        generator_health = phase3_pipeline.response_generator.health_check()
        formatter_health = phase3_pipeline.response_formatter.health_check()
        compliance_health = phase3_pipeline.compliance_safety.health_check()
        
        # Calculate overall health
        health_statuses = [
            classifier_health.get('status', 'unknown'),
            generator_health.get('status', 'unknown'),
            formatter_health.get('status', 'unknown'),
            compliance_health.get('status', 'unknown')
        ]
        
        overall_status = 'healthy' if all(status == 'healthy' for status in health_statuses) else 'degraded'
        
        response = {
            'api_stats': {
                'total_classifications': classifier_stats.get('total_classifications', 0),
                'total_responses': generator_stats.get('total_responses', 0),
                'total_formatted': formatter_stats.get('total_formatted', 0),
                'compliance_checks': compliance_stats.get('total_checks', 0),
                'classification_distribution': classifier_stats.get('distribution', {}),
                'response_type_distribution': generator_stats.get('distribution', {}),
                'average_response_time': generator_stats.get('average_response_time', 0.0),
                'compliance_approval_rate': compliance_stats.get('approval_rate', 0.0)
            },
            'system_health': {
                'query_classifier': classifier_health.get('status', 'unknown'),
                'response_generator': generator_health.get('status', 'unknown'),
                'response_formatter': formatter_health.get('status', 'unknown'),
                'compliance_safety': compliance_health.get('status', 'unknown'),
                'overall_status': overall_status
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@api_bp.route('/validate', methods=['POST'])
@require_api_key
@validate_request_data(['query'])
@handle_errors
@limiter.limit("5/minute")
async def validate_response():
    """
    Validate a response for compliance and quality.
    
    Request Body:
    {
        "query": "What is the expense ratio?",
        "response": "The expense ratio is 1.5%.",
        "response_type": "factual"
    }
    
    Response:
    {
        "valid": true,
        "compliance": {
            "approved": true,
            "risk_level": "low",
            "issues": []
        },
        "quality": {
            "length_ok": true,
            "format_ok": true,
            "sources_ok": true
        }
    }
    """
    try:
        data = request.get_json()
        query = data['query']
        response_text = data['response']
        response_type = data.get('response_type', 'factual')
        
        # Create mock classification and response for validation
        from ..rag.query_processing.query_classifier import QueryClassification
        from ..rag.query_processing.response_generator import GeneratedResponse
        
        classification = QueryClassification(
            query=query,
            query_type=QueryType(response_type),
            confidence=0.8,
            keywords=[],
            entities=[],
            intent="validation_test",
            subcategory=None,
            metadata={}
        )
        
        response = GeneratedResponse(
            query=query,
            response_type=response_type,
            content=response_text,
            sources=[],
            confidence=0.8,
            response_time=0.5,
            metadata={}
        )
        
        # Check compliance
        compliance_result = await phase3_pipeline.compliance_safety.check_compliance(
            query, classification, response
        )
        
        # Validate quality
        quality_issues = []
        
        # Check length
        if len(response_text) > 500:
            quality_issues.append("Response too long")
        
        # Check format
        if response_type == 'advisory' and 'investment advice' not in response_text.lower():
            quality_issues.append("Advisory response should contain disclaimer")
        
        # Check sources for factual queries
        if response_type == 'factual' and not response.sources:
            quality_issues.append("Factual response should have sources")
        
        validation_result = {
            'valid': compliance_result.approved and len(quality_issues) == 0,
            'compliance': {
                'approved': compliance_result.approved,
                'risk_level': compliance_result.overall_risk.value,
                'issues': [check.details for check in compliance_result.compliance_checks if not check.passed]
            },
            'quality': {
                'length_ok': len(response_text) <= 500,
                'format_ok': len(quality_issues) == 0,
                'sources_ok': response_type != 'factual' or bool(response.sources),
                'issues': quality_issues
            },
            'request_id': getattr(g, 'request_id', 'unknown')
        }
        
        return jsonify(validation_result), 200
        
    except Exception as e:
        logger.error(f"Error validating response: {str(e)}")
        return jsonify({
            'error': 'Failed to validate response',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 500

@api_bp.route('/health/detailed', methods=['GET'])
@require_api_key
@handle_errors
async def detailed_health_check():
    """
    Get detailed health check for all components.
    
    Response:
    {
        "components": {
            "query_classifier": {
                "status": "healthy",
                "issues": [],
                "details": {...}
            },
            "response_generator": {
                "status": "healthy",
                "issues": [],
                "details": {...}
            },
            ...
        },
        "overall_status": "healthy"
    }
    """
    try:
        # Get health status for all components
        classifier_health = phase3_pipeline.query_classifier.health_check()
        generator_health = phase3_pipeline.response_generator.health_check()
        formatter_health = phase3_pipeline.response_formatter.health_check()
        compliance_health = phase3_pipeline.compliance_safety.health_check()
        
        # Get integration test health
        integration_health = phase3_pipeline.integration_tests.health_check()
        
        components = {
            'query_classifier': classifier_health,
            'response_generator': generator_health,
            'response_formatter': formatter_health,
            'compliance_safety': compliance_health,
            'integration_tests': integration_health
        }
        
        # Calculate overall status
        all_statuses = [comp.get('status', 'unknown') for comp in components.values()]
        if all(status == 'healthy' for status in all_statuses):
            overall_status = 'healthy'
        elif any(status == 'critical' for status in all_statuses):
            overall_status = 'critical'
        elif any(status == 'degraded' for status in all_statuses):
            overall_status = 'degraded'
        else:
            overall_status = 'unknown'
        
        response = {
            'components': components,
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        return jsonify({'error': 'Failed to get health status'}), 500

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 405

@api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors."""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 429

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'request_id': getattr(g, 'request_id', 'unknown')
    }), 500
