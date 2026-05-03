"""
Enhanced Backend API for Mutual Fund FAQ Assistant
Integrates with Phase 3 Pipeline for real query processing
"""

import json
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add src to path for Phase 3 imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

app = Flask(__name__)
CORS(app)

# Expanded mock responses for demonstration
MOCK_RESPONSES = {
    "What is the expense ratio of HDFC Mid Cap Fund?": {
        "query": "What is the expense ratio of HDFC Mid Cap Fund?",
        "answer": "The expense ratio of HDFC Mid Cap Fund is 1.5% for regular plan and 1.0% for direct plan.",
        "source": "https://hdfcfund.com/factsheet",
        "source_title": "HDFC Mid Cap Fund Factsheet",
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
        "answer": "The minimum SIP amount for HDFC funds is $500 per month through systematic investment plan.",
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
    },
    "How to start SIP in HDFC Mutual Fund?": {
        "query": "How to start SIP in HDFC Mutual Fund?",
        "answer": "To start SIP in HDFC Mutual Fund: 1) Visit HDFC Mutual Fund website or mobile app 2) Complete KYC if not done 3) Select the fund and SIP amount 4) Choose SIP date and frequency 5) Provide bank details 6) Complete the registration process 7) Start your SIP investment.",
        "source": "https://hdfcfund.com/sip-process",
        "source_title": "HDFC SIP Process Guide",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "procedural",
        "confidence": 0.88,
        "response_time": 1.0,
        "request_id": "demo-101",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "What are the historical returns of HDFC Mid Cap Fund?": {
        "query": "What are the historical returns of HDFC Mid Cap Fund?",
        "answer": "For detailed historical returns of HDFC Mid Cap Fund, please refer to the official factsheet available on HDFC Mutual Fund website, which provides comprehensive performance data across different time periods.",
        "source": "https://hdfcfund.com/factsheet",
        "source_title": "HDFC Mid Cap Fund Factsheet",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "performance",
        "confidence": 0.85,
        "response_time": 0.7,
        "request_id": "demo-202",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": ["Redirected to official source"]
        }
    },
    "What is the exit load for HDFC Equity Fund?": {
        "query": "What is the exit load for HDFC Equity Fund?",
        "answer": "The exit load for HDFC Equity Fund is 1% if redeemed within 1 year from the date of allotment. No exit load is applicable if redeemed after 1 year.",
        "source": "https://hdfcfund.com/equity-fund",
        "source_title": "HDFC Equity Fund Scheme Information Document",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.90,
        "response_time": 0.9,
        "request_id": "demo-303",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "How to download account statement from HDFC Mutual Fund?": {
        "query": "How to download account statement from HDFC Mutual Fund?",
        "answer": "To download account statement from HDFC Mutual Fund: 1) Login to HDFC Mutual Fund website with your credentials 2) Go to 'My Account' section 3) Click on 'Account Statement' 4) Select the desired period 5) Choose format (PDF/Excel) 6) Download the statement. You can also get statements through mobile app.",
        "source": "https://hdfcfund.com/statement",
        "source_title": "HDFC Account Statement Guide",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "procedural",
        "confidence": 0.87,
        "response_time": 1.1,
        "request_id": "demo-404",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "What is the minimum investment amount for HDFC funds?": {
        "query": "What is the minimum investment amount for HDFC funds?",
        "answer": "The minimum investment amount for HDFC mutual funds varies by scheme. For lumpsum investment, it's typically $500 for most equity funds and $1000 for debt funds. For SIP, the minimum is $500 per month across all schemes.",
        "source": "https://hdfcfund.com/investment-limits",
        "source_title": "HDFC Investment Guidelines",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.91,
        "response_time": 0.8,
        "request_id": "demo-505",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "Which HDFC fund is best for long term?": {
        "query": "Which HDFC fund is best for long term?",
        "answer": "I cannot provide investment advice or recommend specific funds. Please consult a qualified financial advisor who can analyze your risk profile, investment goals, and time horizon to suggest suitable HDFC funds for long-term investment.",
        "source": "",
        "source_title": "",
        "last_updated": "",
        "disclaimer": "This is not investment advice. Please consult a qualified financial advisor.",
        "query_type": "advisory",
        "confidence": 1.0,
        "response_time": 0.6,
        "request_id": "demo-606",
        "compliance": {
            "approved": True,
            "risk_level": "high",
            "modifications": ["Added disclaimer", "Refused investment advice"]
        }
    },
    "What is the NAV of HDFC Mid Cap Fund today?": {
        "query": "What is the NAV of HDFC Mid Cap Fund today?",
        "answer": "For current NAV of HDFC Mid Cap Fund, please check the official HDFC Mutual Fund website or financial websites like AMFI, Moneycontrol, or Value Research, as NAV is updated daily and varies based on market performance.",
        "source": "https://hdfcfund.com/nav",
        "source_title": "HDFC Fund NAV Information",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "performance",
        "confidence": 0.83,
        "response_time": 0.7,
        "request_id": "demo-707",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": ["Redirected to official source"]
        }
    },
    "How to complete KYC for HDFC Mutual Fund?": {
        "query": "How to complete KYC for HDFC Mutual Fund?",
        "answer": "To complete KYC for HDFC Mutual Fund: 1) Visit HDFC Mutual Fund website 2) Click on 'Invest Now' 3) Fill personal details 4) Upload required documents (PAN card, address proof, photo) 5) Complete video KYC or visit a KYC center 6) Receive KYC confirmation 7) Start investing. You can also complete KYC through CAMS/KRA.",
        "source": "https://hdfcfund.com/kyc",
        "source_title": "HDFC KYC Process Guide",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "procedural",
        "confidence": 0.89,
        "response_time": 1.0,
        "request_id": "demo-808",
        "compliance": {
            "approved": True,
            "risk_level": "low",
            "modifications": []
        }
    },
    "What is the risk level of HDFC Mid Cap Fund?": {
        "query": "What is the risk level of HDFC Mid Cap Fund?",
        "answer": "HDFC Mid Cap Fund is a mid-cap equity fund with very high risk level as per SEBI riskometer. Mid-cap funds are considered higher risk compared to large-cap funds but offer potential for higher returns over long term.",
        "source": "https://hdfcfund.com/riskometer",
        "source_title": "HDFC Fund Risk Information",
        "last_updated": "2024-01-15",
        "disclaimer": "Facts-only. No investment advice.",
        "query_type": "factual",
        "confidence": 0.86,
        "response_time": 0.8,
        "request_id": "demo-909",
        "compliance": {
            "approved": True,
            "risk_level": "medium",
            "modifications": []
        }
    }
}

# Phase 3 Pipeline Integration (fallback if import fails)
phase3_pipeline = None
try:
    from src.rag.query_processing.main import Phase3Pipeline
    phase3_pipeline = Phase3Pipeline()
    print("Phase 3 Pipeline loaded successfully")
except Exception as e:
    print(f"Phase 3 Pipeline not available: {e}")
    print("Using enhanced mock responses instead")

async def process_with_phase3(query):
    """Process query using Phase 3 Pipeline"""
    if not phase3_pipeline:
        return None
    
    try:
        # Classify the query
        classification = phase3_pipeline.query_classifier.classify_query(query)
        
        # Create response context
        from src.rag.query_processing.response_generator import ResponseContext
        response_context = ResponseContext(
            query=query,
            classification=classification,
            retrieved_chunks=[],
            search_results=[],
            user_context={},
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
            return {
                'query': query,
                'answer': 'I cannot provide a response to this query due to compliance requirements.',
                'source': '',
                'source_title': '',
                'last_updated': '',
                'disclaimer': 'Response blocked due to compliance requirements.',
                'query_type': classification.query_type.value,
                'confidence': 0.0,
                'response_time': response.response_time,
                'request_id': f"phase3-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
            
            return {
                'query': query,
                'answer': response.content,
                'source': source_url,
                'source_title': source_title,
                'last_updated': response.sources[0].get('last_updated', '') if response.sources else '',
                'disclaimer': 'Facts-only. No investment advice.',
                'query_type': classification.query_type.value,
                'confidence': response.confidence,
                'response_time': response.response_time,
                'request_id': f"phase3-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'compliance': {
                    'approved': True,
                    'risk_level': compliance_result.overall_risk.value,
                    'modifications': compliance_result.modifications
                }
            }
    
    except Exception as e:
        print(f"Phase 3 processing error: {e}")
        return None

@app.route('/api/v1/query', methods=['POST'])
def process_query():
    """Process a user query and return a response."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        
        # Try Phase 3 Pipeline first
        if phase3_pipeline:
            try:
                response = asyncio.run(process_with_phase3(query))
                if response:
                    return jsonify(response), 200
            except Exception as e:
                print(f"Phase 3 fallback to mock: {e}")
        
        # Fallback to enhanced mock responses
        if query in MOCK_RESPONSES:
            response = MOCK_RESPONSES[query]
        else:
            # Try to find partial matches
            response = find_partial_match(query)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

def find_partial_match(query):
    """Find partial match in mock responses"""
    query_lower = query.lower()
    
    # Check for keywords and return appropriate response
    if 'expense ratio' in query_lower:
        return {
            "query": query,
            "answer": "Expense ratios for HDFC funds vary by scheme. Please check the specific fund's factsheet for accurate expense ratio information.",
            "source": "https://hdfcfund.com/factsheet",
            "source_title": "HDFC Fund Factsheets",
            "last_updated": "2024-01-15",
            "disclaimer": "Facts-only. No investment advice.",
            "query_type": "factual",
            "confidence": 0.7,
            "response_time": 0.5,
            "request_id": f"partial-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "compliance": {
                "approved": True,
                "risk_level": "low",
                "modifications": []
            }
        }
    elif 'sip' in query_lower:
        return {
            "query": query,
            "answer": "For SIP-related information, please visit the HDFC Mutual Fund website or mobile app. The minimum SIP amount is typically $500 per month.",
            "source": "https://hdfcfund.com/sip",
            "source_title": "HDFC SIP Information",
            "last_updated": "2024-01-15",
            "disclaimer": "Facts-only. No investment advice.",
            "query_type": "procedural",
            "confidence": 0.7,
            "response_time": 0.5,
            "request_id": f"partial-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "compliance": {
                "approved": True,
                "risk_level": "low",
                "modifications": []
            }
        }
    elif 'invest' in query_lower or 'best' in query_lower:
        return {
            "query": query,
            "answer": "I cannot provide investment advice or recommend specific funds. Please consult a qualified financial advisor for personalized investment recommendations.",
            "source": "",
            "source_title": "",
            "last_updated": "",
            "disclaimer": "This is not investment advice. Please consult a qualified financial advisor.",
            "query_type": "advisory",
            "confidence": 1.0,
            "response_time": 0.5,
            "request_id": f"partial-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "compliance": {
                "approved": True,
                "risk_level": "high",
                "modifications": ["Added disclaimer", "Refused investment advice"]
            }
        }
    else:
        # Generic response
        return {
            "query": query,
            "answer": "I don't have specific information about this query. Please try asking about expense ratios, SIP amounts, or how to start investing in HDFC Mutual Funds.",
            "source": "https://hdfcfund.com",
            "source_title": "HDFC Mutual Fund",
            "last_updated": "2024-01-15",
            "disclaimer": "Facts-only. No investment advice.",
            "query_type": "general",
            "confidence": 0.3,
            "response_time": 0.5,
            "request_id": f"generic-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "compliance": {
                "approved": True,
                "risk_level": "low",
                "modifications": []
            }
        }

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
            'query': 'How to download account statement from HDFC Mutual Fund?',
            'category': 'procedural',
            'description': 'Get instructions for downloading statements'
        },
        {
            'query': 'What are the historical returns of HDFC Mid Cap Fund?',
            'category': 'performance',
            'description': 'Get historical performance information'
        },
        {
            'query': 'Should I invest in HDFC?',
            'category': 'advisory',
            'description': 'Investment advice query (will be refused)'
        },
        {
            'query': 'What is the exit load for HDFC Equity Fund?',
            'category': 'factual',
            'description': 'Get information about exit charges'
        },
        {
            'query': 'How to complete KYC for HDFC Mutual Fund?',
            'category': 'procedural',
            'description': 'Get KYC completion instructions'
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
                'factual': 5,
                'advisory': 2,
                'procedural': 3,
                'performance': 2
            },
            'phase3_status': 'connected' if phase3_pipeline else 'mock_only'
        },
        'system_health': {
            'query_classifier': 'healthy' if phase3_pipeline else 'mock',
            'response_generator': 'healthy' if phase3_pipeline else 'mock',
            'compliance_safety': 'healthy' if phase3_pipeline else 'mock',
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
        'message': 'Enhanced API is running',
        'phase3_connected': phase3_pipeline is not None
    }), 200

@app.route('/info', methods=['GET'])
def app_info():
    """Application information endpoint."""
    return jsonify({
        'name': 'Mutual Fund FAQ Assistant API (Enhanced)',
        'version': 'v1',
        'environment': 'development',
        'timestamp': datetime.now().isoformat(),
        'phase3_status': 'connected' if phase3_pipeline else 'mock_only',
        'mock_responses_count': len(MOCK_RESPONSES),
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
        'message': 'Mutual Fund FAQ Assistant API (Enhanced)',
        'version': 'v1',
        'phase3_status': 'connected' if phase3_pipeline else 'mock_only',
        'mock_responses': len(MOCK_RESPONSES),
        'endpoints': {
            'query': '/api/v1/query',
            'examples': '/api/v1/examples',
            'stats': '/api/v1/stats',
            'health': '/health',
            'info': '/info'
        }
    })

if __name__ == '__main__':
    print("Starting Enhanced Mutual Fund FAQ Assistant API")
    print("Server will be available at: http://localhost:5000")
    print(f"Phase 3 Pipeline: {'Connected' if phase3_pipeline else 'Mock Only'}")
    print(f"Mock Responses: {len(MOCK_RESPONSES)} available")
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
