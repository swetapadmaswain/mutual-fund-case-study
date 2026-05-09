import streamlit as st
import requests
import json
from datetime import datetime
import os
from groq import Groq
import uuid

# Page configuration
st.set_page_config(
    page_title="Mutual Fund AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-style interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #3b82f6;
        color: white;
        margin-left: 20%;
    }
    .ai-message {
        background-color: #f1f5f9;
        color: #1f2937;
        margin-right: 20%;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .confidence-badge {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .typing-indicator {
        color: #6b7280;
        font-style: italic;
    }
    .example-chip {
        background-color: #e5e7eb;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.2s;
    }
    .example-chip:hover {
        background-color: #d1d5db;
        transform: translateY(-1px);
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-block;
    }
    .status-connected {
        background-color: #10b981;
        color: white;
    }
    .status-error {
        background-color: #ef4444;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Groq client
@st.cache_resource
def get_groq_client():
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        return Groq(api_key=api_key)
    return None

# Knowledge base
FACTUAL_KNOWLEDGE = {
    "expense_ratios": {
        "HDFC Mid Cap Fund": {"regular": "1.50%", "direct": "0.95%"},
        "HDFC Large Cap Fund": {"regular": "1.62%", "direct": "1.00%"},
        "HDFC Small Cap Fund": {"regular": "1.75%", "direct": "1.15%"},
        "HDFC Equity Fund": {"regular": "1.50%", "direct": "0.95%"}
    },
    "nav_info": {
        "HDFC Mid Cap Fund": {
            "regular": "₹145.67 (as of last trading day)",
            "direct": "₹148.23 (as of last trading day)"
        },
        "HDFC Large Cap Fund": {
            "regular": "₹892.45 (as of last trading day)",
            "direct": "₹905.78 (as of last trading day)"
        },
        "HDFC Small Cap Fund": {
            "regular": "₹78.34 (as of last trading day)",
            "direct": "₹79.89 (as of last trading day)"
        },
        "HDFC Equity Fund": {
            "regular": "₹567.89 (as of last trading day)",
            "direct": "₹575.23 (as of last trading day)"
        }
    },
    "sip_minimums": {
        "default": "₹500 per month",
        "special": "₹1,000 per month (for some funds like HDFC Children's Gift Fund)"
    },
    "exit_loads": {
        "equity": "1% if redeemed within 1 year, 0% after 1 year",
        "elss": "No exit load after 3-year lock-in period",
        "debt": "Varies from 0% to 2% depending on fund and holding period"
    },
    "lock_in_periods": {
        "ELSS": "3 years from date of investment",
        "others": "No lock-in period (except ELSS)"
    }
}

def get_factual_response(query):
    """Get factual response from knowledge base"""
    query_lower = query.lower()
    
    # Expense ratio queries
    if "expense ratio" in query_lower:
        for fund_name, ratios in FACTUAL_KNOWLEDGE["expense_ratios"].items():
            if fund_name.lower() in query_lower:
                return f"""The expense ratio of {fund_name} is {ratios['regular']} for Regular Plan and {ratios['direct']} for Direct Plan.

**Understanding Expense Ratios:**
- **Regular Plan ({ratios['regular']}%)**: Includes distributor commissions
- **Direct Plan ({ratios['direct']}%)**: No distributor commissions, offering lower costs
- **Impact**: A 1% difference can significantly impact long-term wealth creation

**Cost Impact Example:**
For a ₹10,000 investment over 10 years with 12% returns:
- Direct Plan: Would grow to approximately ₹31,058
- Regular Plan: Would grow to approximately ₹29,037
- Difference: Over ₹2,000 saved with direct plan"""
    
    # NAV queries
    if "nav" in query_lower or "net asset value" in query_lower:
        for fund_name, nav_data in FACTUAL_KNOWLEDGE["nav_info"].items():
            if fund_name.lower() in query_lower:
                return f"""The Net Asset Value (NAV) of {fund_name} is:

**Current NAV Values:**
- **Regular Plan**: {nav_data['regular']}
- **Direct Plan**: {nav_data['direct']}

**Understanding NAV:**
NAV represents the per-unit value of a mutual fund scheme. It's calculated by dividing the total market value of all securities in the fund's portfolio, minus liabilities, by the total number of outstanding units.

**Key Concepts:**
- **Daily Calculation**: NAV is calculated at the end of each business day
- **Performance Indicator**: NAV changes reflect the fund's performance
- **Market Impact**: NAV fluctuates based on market movements"""
    
    # SIP queries
    if "sip" in query_lower and ("minimum" in query_lower or "amount" in query_lower):
        return f"""The minimum SIP amount for HDFC Mutual Fund schemes is {FACTUAL_KNOWLEDGE['sip_minimums']['default']}. {FACTUAL_KNOWLEDGE['sip_minimums']['special']}.

**Understanding SIP Investment:**

**What is SIP?**
Systematic Investment Plan (SIP) is a disciplined investment method where you invest a fixed amount at regular intervals.

**Benefits of SIP:**
- **Rupee Cost Averaging**: Reduces impact of market volatility
- **Discipline**: Encourages regular investing habit
- **Low Barrier**: Start with as little as ₹500 per month
- **Power of Compounding**: Small amounts grow significantly over time

**Impact of Regular SIP:**
Investing ₹1,000 monthly for different periods (assuming 12% annual return):
- 5 years: ₹82,000 (total invested: ₹60,000)
- 10 years: ₹2,30,000 (total invested: ₹1,20,000)
- 20 years: ₹9,89,000 (total invested: ₹2,40,000)"""
    
    # Exit load queries
    if "exit load" in query_lower:
        if "equity" in query_lower:
            return f"Exit load for HDFC Equity Funds: {FACTUAL_KNOWLEDGE['exit_loads']['equity']}. The exit load is calculated on the applicable NAV for the redemption day."
        elif "elss" in query_lower:
            return f"Exit load for HDFC ELSS Funds: {FACTUAL_KNOWLEDGE['exit_loads']['elss']}. No charges for redemption after the lock-in period."
    
    # Lock-in period queries
    if "lock in" in query_lower or "lock-in" in query_lower:
        if "elss" in query_lower:
            return f"HDFC ELSS Funds have {FACTUAL_KNOWLEDGE['lock_in_periods']['ELSS']}. During this period, you cannot redeem or withdraw your investment. After 3 years, you can redeem units or continue holding."
        else:
            return f"Most HDFC Mutual Funds have {FACTUAL_KNOWLEDGE['lock_in_periods']['others']}. Only ELSS funds have a mandatory 3-year lock-in period for tax benefits under Section 80C."
    
    return None

def check_compliance(query):
    """Check if query requires compliance handling"""
    query_lower = query.lower()
    
    compliance_patterns = [
        "should i invest", "recommend.*fund", "best.*fund", 
        "good.*investment", "which.*fund.*better", "advice.*investment",
        "guaranteed.*return", "sure.*profit", "no.*risk",
        "future.*return", "predict.*performance", "will.*perform"
    ]
    
    for pattern in compliance_patterns:
        if pattern in query_lower:
            return True
    
    return False

def generate_ai_response(query):
    """Generate AI response using Groq"""
    client = get_groq_client()
    if not client:
        return "Groq API is not configured. Please set GROQ_API_KEY environment variable to enable AI responses. For now, I can only provide factual information from my knowledge base.", "demo_mode"
    
    try:
        prompt = f"""
You are an expert HDFC Mutual Fund research analyst with deep knowledge of mutual fund operations, market dynamics, and investment principles. Provide comprehensive, detailed, and insightful responses to user questions about HDFC Mutual Funds.

Guidelines for high-quality responses:
1. Provide detailed explanations with context and background information
2. Include specific data, statistics, and examples when relevant
3. Explain concepts in an intuitive and educational manner
4. Break down complex topics into understandable components
5. Provide historical context and market insights when applicable
6. Include practical examples and real-world applications
7. Explain the "why" behind facts, not just the "what"
8. Use comparative analysis when helpful

Compliance Requirements:
- Never provide direct investment advice or recommendations
- Do not predict specific future returns or performance
- Always include appropriate disclaimers
- Focus on educational and informational content

User question: {query}

Provide a comprehensive, research-based response that demonstrates deep expertise and adds real value:"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert HDFC Mutual Fund research analyst providing detailed, educational, and insightful responses about mutual funds. Focus on comprehensive explanations, market context, and practical insights while maintaining strict compliance."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.4
        )
        
        return response.choices[0].message.content.strip(), "groq_generated"
        
    except Exception as e:
        return f"Error connecting to AI service: {str(e)}. Please try again later or visit www.hdfcfund.com for detailed information.", "error"

def validate_input(text):
    """Validate user input for security"""
    if not text or len(text.strip()) == 0:
        return False
    if len(text) > 1000:  # Reasonable limit
        return False
    return True

# Main application
def main():
    # Header
    st.title("🤖 Mutual Fund AI Assistant")
    st.markdown("Powered by Groq AI - Ask questions about HDFC Mutual Funds")
    
    # API Status
    client = get_groq_client()
    if client:
        st.markdown('<span class="status-badge status-connected">✅ Groq API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-error">❌ Groq API Not Connected</span>', unsafe_allow_html=True)
        st.warning("Please set GROQ_API_KEY environment variable to enable AI responses.")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    # Sidebar with examples
    with st.sidebar:
        st.header("💡 Example Questions")
        examples = [
            "What is the expense ratio of HDFC Mid Cap Fund?",
            "What is the NAV of HDFC Mid Cap Fund?",
            "What are the benefits of SIP investment?",
            "How to start SIP in HDFC Mutual Fund?",
            "What is the minimum SIP amount?",
            "What is the lock-in period for ELSS funds?",
            "What is the exit load for HDFC Equity Funds?"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{examples.index(example)}"):
                if validate_input(example):
                    st.session_state.messages.append({"role": "user", "content": example})
                else:
                    st.error("Invalid input. Please enter a valid question.")
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Chat Statistics")
        st.metric("Total Messages", len(st.session_state.messages))
        st.metric("User ID", st.session_state.user_id[:8] + "...")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add metadata for AI messages
            if message["role"] == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                if metadata["type"] == "factual":
                    st.caption("📊 Factual Knowledge Base")
                elif metadata["type"] == "groq_generated":
                    st.caption("🤖 AI Generated via Groq")
                elif metadata["type"] == "demo_mode":
                    st.caption("⚠️ Demo Mode")
                elif metadata["type"] == "error":
                    st.caption("❌ Error")
    
    # Chat input
    if prompt := st.chat_input("Ask about HDFC Mutual Funds..."):
        if validate_input(prompt):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Check compliance
            if check_compliance(prompt):
                response = "I cannot provide investment advice, recommendations, or predict future performance. Please consult a qualified financial advisor for personalized investment guidance. I can help with factual information about HDFC Mutual Funds, expense ratios, NAV, SIP processes, and other educational content."
                response_type = "compliance_refusal"
            else:
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("AI is thinking..."):
                        # Try factual response first
                        factual_response = get_factual_response(prompt)
                        if factual_response:
                            response = factual_response
                            response_type = "factual"
                        else:
                            response, response_type = generate_ai_response(prompt)
                    
                    st.markdown(response)
                    
                    # Add metadata
                    if response_type == "factual":
                        st.caption("📊 Factual Knowledge Base")
                    elif response_type == "groq_generated":
                        st.caption("🤖 AI Generated via Groq")
                    elif response_type == "demo_mode":
                        st.caption("⚠️ Demo Mode")
                    elif response_type == "error":
                        st.caption("❌ Error")
                    elif response_type == "compliance_refusal":
                        st.caption("🛡️ Compliance Refusal")
            
            # Add assistant message to session state
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "metadata": {"type": response_type}
            })
        else:
            st.error("Invalid input. Please enter a valid question (max 1000 characters).")

if __name__ == "__main__":
    main()
