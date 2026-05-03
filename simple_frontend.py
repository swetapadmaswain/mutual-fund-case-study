"""
Simple Streamlit Frontend for Mutual Fund FAQ Assistant
A minimal frontend that can connect to the backend API
"""

import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000"

# Page configuration
st.set_page_config(
    page_title="Mutual Fund FAQ Assistant",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .disclaimer-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.375rem;
    }
    
    .response-box {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .source-link {
        color: #3b82f6;
        text-decoration: none;
        font-weight: 500;
    }
    
    .source-link:hover {
        text-decoration: underline;
    }
    
    .example-question {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .example-question:hover {
        background-color: #dbeafe;
        border-color: #93c5fd;
    }
    
    .response-meta {
        font-size: 0.875rem;
        color: #6b7280;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-healthy { background-color: #10b981; }
    .status-degraded { background-color: #f59e0b; }
    .status-critical { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Check if the backend API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def make_api_request(query):
    """Make API request to the backend."""
    try:
        headers = {'Content-Type': 'application/json'}
        data = {'query': query}
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/query",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def get_example_questions():
    """Get example questions from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/examples", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('examples', [])
    except:
        pass
    
    # Return fallback examples
    return [
        {
            'query': 'What is the expense ratio of HDFC Mid Cap Fund?',
            'category': 'factual',
            'description': 'Get factual information about fund metrics'
        },
        {
            'query': 'What is the minimum SIP amount?',
            'category': 'factual',
            'description': 'Get factual information about investment requirements'
        },
        {
            'query': 'Should I invest in HDFC?',
            'category': 'advisory',
            'description': 'Investment advice query (will be refused)'
        }
    ]

def render_header():
    """Render the application header."""
    st.markdown('<h1 class="main-header">📊 Mutual Fund FAQ Assistant</h1>', unsafe_allow_html=True)
    
    # Check API health
    api_healthy = check_api_health()
    
    # API Status
    if api_healthy:
        st.success("✅ Backend API is connected and healthy")
    else:
        st.error("❌ Backend API is not available. Please start the backend server first.")
        st.info("Run: `python simple_api.py` in the project directory")
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ Important Disclaimer:</strong> This assistant provides factual information only and does not give investment advice. 
        Please consult a qualified financial advisor for investment recommendations.
    </div>
    """, unsafe_allow_html=True)

def render_example_questions():
    """Render example questions that users can click."""
    if not check_api_health():
        return
    
    st.subheader("💡 Example Questions")
    
    examples = get_example_questions()
    
    for example in examples:
        if st.button(example['query'], key=f"example_{len(example['query'])}"):
            st.session_state.query_input = example['query']
            st.rerun()

def render_query_input():
    """Render the query input interface."""
    if not check_api_health():
        st.warning("⚠️ Cannot submit queries while API is disconnected")
        return
    
    st.subheader("🔍 Ask a Question")
    
    # Query input
    query = st.text_input(
        "Enter your question about HDFC Mutual Funds:",
        placeholder="e.g., What is the expense ratio of HDFC Mid Cap Fund?",
        key="query_input",
        help="Ask factual questions about HDFC Mutual Funds. No investment advice will be provided."
    )
    
    # Submit button
    col1, col2 = st.columns([1, 1])
    with col1:
        submit_button = st.button("🚀 Submit", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    # Handle button clicks
    if submit_button and query:
        process_query(query)
    elif clear_button:
        clear_response()

def process_query(query):
    """Process a user query."""
    st.info("🔄 Processing your question...")
    
    # Make API request
    response_data = make_api_request(query)
    
    if response_data:
        st.session_state.current_response = response_data
        st.session_state.api_error = None
        st.success("✅ Query processed successfully!")
    else:
        st.session_state.current_response = None
        st.session_state.api_error = "Failed to get response from API"

def render_response():
    """Render the response display area."""
    if st.session_state.get('api_error'):
        st.error(f"❌ {st.session_state.api_error}")
        return
    
    if not st.session_state.get('current_response'):
        st.info("💭 Ask a question above to get started!")
        return
    
    response = st.session_state.current_response
    
    # Response box
    st.markdown('<div class="response-box">', unsafe_allow_html=True)
    
    # Answer
    st.markdown("### 📄 Answer")
    st.write(response.get('answer', 'No answer available.'))
    
    # Source information
    if response.get('source'):
        st.markdown("### 🔗 Source")
        source_url = response.get('source', '')
        source_title = response.get('source_title', 'Official Source')
        
        if source_url:
            st.markdown(
                f'<a href="{source_url}" target="_blank" class="source-link">{source_title}</a>',
                unsafe_allow_html=True
            )
        else:
            st.write(source_title)
    
    # Response metadata
    st.markdown('<div class="response-meta">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        query_type = response.get('query_type', 'unknown')
        st.write(f"**Type:** {query_type.title()}")
    
    with col2:
        confidence = response.get('confidence', 0)
        st.write(f"**Confidence:** {confidence:.1%}")
    
    with col3:
        response_time = response.get('response_time', 0)
        st.write(f"**Response Time:** {response_time:.2f}s")
    
    # Compliance information
    compliance = response.get('compliance', {})
    if compliance:
        approved = compliance.get('approved', False)
        risk_level = compliance.get('risk_level', 'unknown')
        
        st.write(f"**Compliance:** {'✅ Approved' if approved else '❌ Rejected'} ({risk_level.title()})")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("---")
    st.markdown(f"*Disclaimer: {response.get('disclaimer', 'No disclaimer available.')}*")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with additional features."""
    with st.sidebar:
        st.header("🔧 Tools")
        
        # Query History
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        if st.session_state.query_history:
            st.subheader("📜 Query History")
            
            for i, item in enumerate(st.session_state.query_history[:5]):
                with st.expander(f"Q: {item['query'][:50]}...", expanded=False):
                    st.write(f"**Query:** {item['query']}")
                    st.write(f"**Time:** {item['timestamp']}")
                    
                    response = item.get('response', {})
                    if response:
                        st.write(f"**Type:** {response.get('query_type', 'unknown')}")
                        st.write(f"**Confidence:** {response.get('confidence', 0):.1%}")
            
            if st.button("🗑️ Clear History"):
                st.session_state.query_history = []
                st.rerun()
        
        # API Statistics
        if st.button("📊 Get API Stats"):
            show_api_stats()

def show_api_stats():
    """Show API statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            st.subheader("📊 API Statistics")
            
            # API Stats
            api_stats = stats.get('api_stats', {})
            
            st.markdown("#### Query Processing")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", api_stats.get('total_queries', 0))
                st.metric("Successful Queries", api_stats.get('successful_queries', 0))
            with col2:
                avg_time = api_stats.get('average_response_time', 0)
                st.metric("Avg Response Time", f"{avg_time:.2f}s")
                approval_rate = api_stats.get('compliance_approval_rate', 0)
                st.metric("Compliance Approval", f"{approval_rate:.1f}%")
            
            # Query Type Distribution
            classification_dist = api_stats.get('query_type_distribution', {})
            if classification_dist:
                st.markdown("#### Query Type Distribution")
                for query_type, count in classification_dist.items():
                    st.write(f"**{query_type.title()}:** {count}")
                
        else:
            st.error("Failed to fetch API statistics")
    
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")

def clear_response():
    """Clear the current response."""
    st.session_state.current_response = None
    st.session_state.api_error = None
    if 'query_input' in st.session_state:
        del st.session_state.query_input

def render_footer():
    """Render the footer with additional information."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**About**")
        st.write("This assistant provides factual information about HDFC Mutual Funds based on official documents.")
    
    with col2:
        st.markdown("**Limitations**")
        st.write("No investment advice is provided. All responses are facts-only with official sources.")
    
    with col3:
        st.markdown("**Contact**")
        st.write("For investment advice, please consult a qualified financial advisor.")
    
    st.markdown("---")
    st.markdown(
        f"<center style='color: #6b7280; font-size: 0.875rem;'>"
        f"© 2024 Mutual Fund FAQ Assistant | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        f"</center>",
        unsafe_allow_html=True
    )

def main():
    """Main application function."""
    # Initialize session state
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'api_error' not in st.session_state:
        st.session_state.api_error = None
    
    # Render main components
    render_header()
    render_example_questions()
    render_query_input()
    render_response()
    render_footer()
    
    # Render sidebar
    render_sidebar()

if __name__ == "__main__":
    main()
