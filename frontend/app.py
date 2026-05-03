"""
Streamlit Frontend for Mutual Fund FAQ Assistant

A clean, minimal interface for querying the mutual fund FAQ system.
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "demo-api-key"  # In production, this should be securely managed

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
    
    .query-input {
        margin-bottom: 1.5rem;
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
    
    .stats-card {
        background-color: #f3f4f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .health-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .health-healthy { background-color: #10b981; }
    .health-degraded { background-color: #f59e0b; }
    .health-critical { background-color: #ef4444; }
    
    .response-meta {
        font-size: 0.875rem;
        color: #6b7280;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .loading-spinner {
        text-align: center;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class MutualFundFAQApp:
    """Main application class for the Mutual Fund FAQ Assistant."""
    
    def __init__(self):
        """Initialize the application."""
        self.session_state = st.session_state
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'query_history' not in self.session_state:
            self.session_state.query_history = []
        
        if 'current_response' not in self.session_state:
            self.session_state.current_response = None
        
        if 'api_error' not in self.session_state:
            self.session_state.api_error = None
        
        if 'system_health' not in self.session_state:
            self.session_state.system_health = None
    
    def render_header(self):
        """Render the application header."""
        st.markdown('<h1 class="main-header">📊 Mutual Fund FAQ Assistant</h1>', unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("""
        <div class="disclaimer-box">
            <strong>⚠️ Important Disclaimer:</strong> This assistant provides factual information only and does not give investment advice. 
            Please consult a qualified financial advisor for investment recommendations.
        </div>
        """, unsafe_allow_html=True)
    
    def render_example_questions(self):
        """Render example questions that users can click."""
        st.subheader("💡 Example Questions")
        
        examples = [
            "What is the expense ratio of HDFC Mid Cap Fund?",
            "What is the minimum SIP amount for HDFC Equity Fund?",
            "How to start SIP in HDFC Mutual Fund?",
            "How to download account statement from HDFC Mutual Fund?",
            "What are the historical returns of HDFC Mid Cap Fund?"
        ]
        
        for example in examples:
            if st.markdown(f'<div class="example-question">📝 {example}</div>', unsafe_allow_html=True):
                if st.button(example, key=f"example_{len(example)}"):
                    self.session_state.query_input = example
                    st.rerun()
    
    def render_query_input(self):
        """Render the query input interface."""
        st.subheader("🔍 Ask a Question")
        
        # Query input
        query = st.text_input(
            "Enter your question about HDFC Mutual Funds:",
            placeholder="e.g., What is the expense ratio of HDFC Mid Cap Fund?",
            key="query_input",
            help="Ask factual questions about HDFC Mutual Funds. No investment advice will be provided."
        )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            submit_button = st.button("🚀 Submit", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        with col3:
            health_button = st.button("🏥 Health Check", use_container_width=True)
        
        # Handle button clicks
        if submit_button and query:
            self.process_query(query)
        elif clear_button:
            self.clear_response()
        elif health_button:
            self.check_system_health()
    
    def process_query(self, query: str):
        """Process a user query."""
        try:
            # Show loading spinner
            with st.spinner("Processing your question..."):
                # Make API request
                response_data = self.make_api_request(query)
                
                if response_data:
                    self.session_state.current_response = response_data
                    self.session_state.api_error = None
                    
                    # Add to query history
                    self.session_state.query_history.insert(0, {
                        'query': query,
                        'timestamp': datetime.now().isoformat(),
                        'response': response_data
                    })
                    
                    # Keep only last 10 queries in history
                    self.session_state.query_history = self.session_state.query_history[:10]
                else:
                    self.session_state.api_error = "No response received from the server."
        
        except Exception as e:
            self.session_state.api_error = f"Error: {str(e)}"
            self.session_state.current_response = None
    
    def make_api_request(self, query: str) -> Optional[Dict[str, Any]]:
        """Make API request to the backend."""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            }
            
            data = {
                'query': query,
                'user_context': {
                    'session_id': 'streamlit_session',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                f"{API_BASE_URL}/query",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
        
        except requests.exceptions.RequestException as e:
            st.error(f"Network Error: {str(e)}")
            return None
    
    def render_response(self):
        """Render the response display area."""
        if self.session_state.api_error:
            st.error(f"❌ {self.session_state.api_error}")
            return
        
        if not self.session_state.current_response:
            st.info("💭 Ask a question above to get started!")
            return
        
        response = self.session_state.current_response
        
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
            
            if not approved and compliance.get('reasons'):
                st.write("**Reasons:**")
                for reason in compliance['reasons']:
                    st.write(f"- {reason}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("---")
        st.markdown(f"*Disclaimer: {response.get('disclaimer', 'No disclaimer available.')}*")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar with additional features."""
        with st.sidebar:
            st.header("🔧 Tools")
            
            # Query History
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
            
            # System Health
            if st.session_state.system_health:
                st.subheader("🏥 System Health")
                health = st.session_state.system_health
                
                overall_status = health.get('overall_status', 'unknown')
                status_color = {
                    'healthy': 'green',
                    'degraded': 'orange',
                    'critical': 'red'
                }.get(overall_status, 'gray')
                
                st.markdown(f"**Overall Status:** :{status_color}[{overall_status.title()}]")
                
                components = health.get('components', {})
                for component, status in components.items():
                    comp_status = status.get('status', 'unknown')
                    comp_color = {
                        'healthy': 'green',
                        'degraded': 'orange',
                        'critical': 'red'
                    }.get(comp_status, 'gray')
                    
                    st.markdown(f"**{component.replace('_', ' ').title()}:** :{comp_color}[{comp_status.title()}]")
            
            # API Statistics
            if st.button("📊 Get API Stats"):
                self.show_api_stats()
    
    def show_api_stats(self):
        """Show API statistics."""
        try:
            headers = {'X-API-Key': API_KEY}
            response = requests.get(f"{API_BASE_URL}/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                
                st.subheader("📊 API Statistics")
                
                # API Stats
                api_stats = stats.get('api_stats', {})
                
                st.markdown("#### Query Processing")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Classifications", api_stats.get('total_classifications', 0))
                    st.metric("Total Responses", api_stats.get('total_responses', 0))
                with col2:
                    avg_time = api_stats.get('average_response_time', 0)
                    st.metric("Avg Response Time", f"{avg_time:.2f}s")
                    approval_rate = api_stats.get('compliance_approval_rate', 0)
                    st.metric("Compliance Approval", f"{approval_rate:.1f}%")
                
                # Query Type Distribution
                classification_dist = api_stats.get('classification_distribution', {})
                if classification_dist:
                    st.markdown("#### Query Type Distribution")
                    for query_type, data in classification_dist.items():
                        count = data.get('count', 0)
                        percentage = data.get('percentage', 0)
                        st.write(f"**{query_type.title()}:** {count} ({percentage:.1f}%)")
                
            else:
                st.error("Failed to fetch API statistics")
        
        except Exception as e:
            st.error(f"Error fetching stats: {str(e)}")
    
    def check_system_health(self):
        """Check system health."""
        try:
            headers = {'X-API-Key': API_KEY}
            response = requests.get(f"{API_BASE_URL}/health/detailed", headers=headers, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.session_state.system_health = health_data
                
                # Show health status
                overall_status = health_data.get('overall_status', 'unknown')
                
                if overall_status == 'healthy':
                    st.success("✅ All systems are healthy!")
                elif overall_status == 'degraded':
                    st.warning("⚠️ Some systems are degraded")
                else:
                    st.error("❌ Some systems have issues")
                
                # Show component status
                components = health_data.get('components', {})
                for component, status in components.items():
                    comp_status = status.get('status', 'unknown')
                    issues = status.get('issues', [])
                    
                    if comp_status == 'healthy':
                        st.success(f"✅ {component.replace('_', ' ').title()}")
                    elif comp_status == 'degraded':
                        st.warning(f"⚠️ {component.replace('_', ' ').title()}")
                        if issues:
                            for issue in issues:
                                st.write(f"   - {issue}")
                    else:
                        st.error(f"❌ {component.replace('_', ' ').title()}")
                        if issues:
                            for issue in issues:
                                st.write(f"   - {issue}")
            
            else:
                st.error("Failed to fetch health status")
        
        except Exception as e:
            st.error(f"Error checking health: {str(e)}")
    
    def clear_response(self):
        """Clear the current response."""
        self.session_state.current_response = None
        self.session_state.api_error = None
        if 'query_input' in self.session_state:
            del self.session_state.query_input
    
    def render_footer(self):
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
    
    def run(self):
        """Run the main application."""
        # Render main components
        self.render_header()
        self.render_example_questions()
        self.render_query_input()
        self.render_response()
        self.render_footer()
        
        # Render sidebar
        self.render_sidebar()

# Main application
def main():
    """Main function to run the Streamlit app."""
    app = MutualFundFAQApp()
    app.run()

if __name__ == "__main__":
    main()
