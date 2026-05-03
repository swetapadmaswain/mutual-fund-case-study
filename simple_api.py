"""
Simple Backend API for Mutual Fund FAQ Assistant
A minimal Flask API that can run without complex dependencies
"""

import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple mock responses for demonstration
MOCK_RESPONSES = {
    "What is the expense ratio of HDFC Mid Cap Fund?": {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?",
        "answer": "The expense ratio of HDFC Mid Cap Fund is 1.5%.",
        "source": "https://hdfcfund.com/factsheet",
        "source_title": "HDFC Fund Factsheet",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.95,
        "response_time": 1.2,
        "request_id": "demo-123",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "What is the minimum SIP amount?": {
        "query": "What is the minimum SIP amount?",
        "answer": "The minimum SIP amount for HDFC funds is ₹500.",
        "source": "https://hdfcfund.com/sip",
        "source_title": "HDFC SIP Information",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.92,
        "response_time": 0.8,
        "request_id": "demo-456",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "Should I invest in HDFC?": {
        "query": "Should I invest in HDFC?",
        "answer": "I cannot provide investment advice. Please consult a qualified financial advisor who can provide personalized recommendations based on your financial situation and goals.",
        "source": "",
        "source_title": "",
        "last_updated": "",
        "disclaimer": "This is not investment advice. Please consult a qualified financial advisor.",
        "query_type": "advisory",
        "confidence": 1.0,
        "response_time": 0.5,
        "request_id": "demo-789",
        "compliance": {
            "approved": True,
            "risk_level": "medium",
            "modifications": ["Added disclaimer"]
        }
    }
}

@app.route('/api/v1/query', methods=['POST'])
def process_query():
    """Process a user query and return a response."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        
        # Check if we have a mock response
        if query in MOCK_RESPONSES:
            response = MOCK_RESPONSES[query]
        else:
            # Generate a generic response
            response = {
                "query": query,
                "answer": "I don't have specific information about this query in the current data. Please try asking about expense ratios, SIP amounts, or how to start investing.",
                "source": "https://hdfcfund.com",
                "source_title": "HDFC Mutual Fund",
                "last_updated": "2024-01-15",
                "disclaimer": "Facts-only. No investment advice.",
                "query_type": "general",
                "confidence": 0.3,
                "response_time": 0.5,
                "request_id": f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "compliance": {
                    "approved": True,
                    "risk_level": "low",
                    "modifications": []
                }
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/v1/examples', methods=['GET'])
def get_examples():
    """Get example questions."""
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
            'query': 'Should I invest in HDFC?',
            'category': 'advisory',
            'description': 'Investment advice query (will be refused)'
        }
    ]
    
    return jsonify({'examples': examples}), 200

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get API statistics."""
    stats = {
        'api_stats': {
            'total_queries': len(MOCK_RESPONSES),
            'successful_queries': len(MOCK_RESPONSES),
            'average_response_time': 0.8,
            'compliance_approval_rate': 100.0,
            'query_type_distribution': {
                'factual': 2,
                'advisory': 1,
                'procedural': 1
            }
        },
        'system_health': {
            'query_classifier': 'healthy',
            'response_generator': 'healthy',
            'compliance_safety': 'healthy',
            'overall_status': 'healthy'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(stats), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'v1',
        'message': 'Simple API is running'
    }), 200

@app.route('/info', methods=['GET'])
def app_info():
    """Application information endpoint."""
    return jsonify({
        'name': 'Mutual Fund FAQ Assistant API (Simple)',
        'version': 'v1',
        'environment': 'development',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/api/v1/query',
            '/api/v1/examples',
            '/api/v1/stats',
            '/health',
            '/info'
        ]
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        'message': 'Mutual Fund FAQ Assistant API',
        'version': 'v1',
        'endpoints': {
            'query': '/api/v1/query',
            'examples': '/api/v1/examples',
            'stats': '/api/v1/stats',
            'health': '/health',
            'info': '/info'
        }
    })

if __name__ == '__main__':
    print("Starting Simple Mutual Fund FAQ Assistant API")
    print("Server will be available at: http://localhost:5000")
    print("This is a simplified version for demonstration")
    print("Available endpoints:")
    print("   - POST /api/v1/query - Process user queries")
    print("   - GET  /api/v1/examples - Get example questions")
    print("   - GET  /api/v1/stats - Get API statistics")
    print("   - GET  /health - Health check")
    print("   - GET  /info - App information")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
