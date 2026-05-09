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
- Regular Plan: ₹31,058 (approx.)
- Direct Plan: ₹32,473 (approx.)
- **Savings**: ₹1,415 (4.5% more wealth)

**Recommendation**: Consider Direct Plan for long-term investments to maximize returns."""
    
    # NAV queries
    if "nav" in query_lower or "net asset value" in query_lower:
        for fund_name, nav_info in FACTUAL_KNOWLEDGE["nav_info"].items():
            if fund_name.lower() in query_lower:
                return f"""The current NAV of {fund_name} is:
- **Regular Plan**: {nav_info['regular']}
- **Direct Plan**: {nav_info['direct']}

**Understanding NAV:**
- **NAV (Net Asset Value)**: Price per unit of the mutual fund
- **Regular vs Direct**: Direct plans typically have slightly higher NAV due to lower expenses
- **Trading**: NAV is updated at the end of each business day
- **Investment**: Units are allotted based on the NAV of the day you invest

**Important Note**: NAV values shown are for illustration purposes. Please check the official HDFC Mutual Fund website or your investment platform for current NAV values."""
    
    # SIP queries
    if "sip" in query_lower or "systematic investment plan" in query_lower:
        if "minimum" in query_lower or "start" in query_lower:
            return f"""**SIP (Systematic Investment Plan) Information:**

**Minimum SIP Amounts:**
- **Default**: {FACTUAL_KNOWLEDGE["sip_minimums"]["default"]}
- **Special Funds**: {FACTUAL_KNOWLEDGE["sip_minimums"]["special"]}

**How to Start SIP in HDFC Mutual Fund:**

1. **Online Process**:
   - Visit HDFC Mutual Fund website
   - Complete KYC (if not done)
   - Select fund and SIP amount
   - Choose SIP date (1st-28th of month)
   - Set up auto-debit mandate

2. **Through Distributor**:
   - Contact HDFC Mutual Fund distributor
   - Fill SIP application form
   - Provide bank details for auto-debit
   - Submit KYC documents

3. **Through Investment Apps**:
   - Use platforms like Groww, Paytm Money, etc.
   - Search for HDFC Mutual Fund
   - Follow app-specific SIP setup process

**Benefits of SIP:**
- Rupee cost averaging
- Power of compounding
- Disciplined investing
- Low minimum investment
- Flexible tenure options"""
    
    # Exit load queries
    if "exit load" in query_lower or "exit charges" in query_lower:
        return f"""**Exit Load Information for HDFC Mutual Funds:**

**Exit Loads by Fund Type:**
- **Equity Funds**: {FACTUAL_KNOWLEDGE["exit_loads"]["equity"]}
- **ELSS Funds**: {FACTUAL_KNOWLEDGE["exit_loads"]["elss"]}
- **Debt Funds**: {FACTUAL_KNOWLEDGE["exit_loads"]["debt"]}

**Understanding Exit Loads:**
- **Exit Load**: Fee charged when you redeem units
- **Purpose**: Discourages very short-term investments
- **Calculation**: Usually on the amount being redeemed
- **Waivers**: Often waived after certain holding period

**Example Calculation:**
For a ₹10,000 redemption from an equity fund within 1 year:
- Exit Load: 1% = ₹100
- Amount after load: ₹9,900

**Strategy**: Consider holding period when planning redemptions to minimize exit loads."""
    
    # Lock-in period queries
    if "lock in" in query_lower or "lock-in" in query_lower:
        return f"""**Lock-in Period Information:**

**Lock-in Periods by Fund Type:**
- **ELSS Funds**: {FACTUAL_KNOWLEDGE["lock_in_periods"]["ELSS"]}
- **Other Funds**: {FACTUAL_KNOWLEDGE["lock_in_periods"]["others"]}

**ELSS (Equity Linked Savings Scheme) Details:**
- **Tax Benefit**: Section 80C deduction up to ₹1.5 lakh
- **Lock-in**: 3 years from date of investment
- **After Lock-in**: Can redeem anytime (subject to exit loads)
- **Minimum Investment**: Usually ₹500 per month via SIP

**Important Points:**
- Lock-in applies to each investment installment
- Partial withdrawals not allowed during lock-in
- Premature withdrawal may have tax implications
- Consider investment horizon before choosing ELSS

**Alternative**: If you need liquidity, consider non-ELSS equity funds."""
    
    return None

def generate_ai_response(query):
    """Generate AI response using Groq API"""
    client = get_groq_client()
    if not client:
        return "I'm currently in demo mode. Please configure the GROQ_API_KEY to enable AI responses.", "demo_mode"
    
    try:
        system_prompt = """You are a helpful mutual fund assistant specializing in HDFC Mutual Funds. 
        You provide factual information about mutual funds, explain concepts clearly, and help users understand investment options.
        
        IMPORTANT RULES:
        1. NEVER provide specific investment advice or recommendations
        2. NEVER predict future performance or returns
        3. NEVER suggest which funds to buy or sell
        4. ALWAYS include a disclaimer that you're not providing investment advice
        5. Focus on educational information and factual data
        6. If asked for advice, redirect to consulting a qualified financial advisor
        
        You can discuss:
        - What mutual funds are and how they work
        - Different types of HDFC Mutual Funds
        - Expense ratios, NAV, SIP processes
        - General investment concepts
        - How to start investing
        - Risk factors (general, not specific advice)
        
        Always maintain a helpful, educational tone while being compliant."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Add compliance disclaimer
        if any(word in query.lower() for word in ['should i', 'recommend', 'suggest', 'advice', 'invest', 'buy', 'sell']):
            ai_response += "\n\n**Important Disclaimer**: I'm not providing investment advice. Please consult a qualified financial advisor for personalized investment guidance."
        
        return ai_response, "groq_generated"
        
    except Exception as e:
        return f"I apologize, but I encountered an error while generating a response. Please try again later. Error: {str(e)}", "error"

def validate_input(query):
    """Validate user input"""
    if not query or not query.strip():
        return False
    if len(query) > 1000:
        return False
    return True

def check_compliance(query):
    """Check if query requires compliance handling"""
    query_lower = query.lower()
    advice_keywords = ['should i', 'recommend', 'suggest', 'advice', 'which fund', 'invest in', 'buy', 'sell']
    return any(keyword in query_lower for keyword in advice_keywords)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Main application
def main():
    st.title("Mutual Fund AI Assistant")
    st.markdown("Ask questions about HDFC Mutual Funds, SIP, NAV, and investment concepts.")
    
    # Status indicator
    client = get_groq_client()
    if client:
        st.markdown('<span class="status-badge status-connected">Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-error">Demo Mode</span>', unsafe_allow_html=True)
    
    # Sidebar with examples
    with st.sidebar:
        st.header("Example Questions")
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
        if st.button("Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Statistics
        st.subheader("Chat Statistics")
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
                    st.caption("Factual Knowledge Base")
                elif metadata["type"] == "groq_generated":
                    st.caption("AI Generated via Groq")
                elif metadata["type"] == "demo_mode":
                    st.caption("Demo Mode")
                elif metadata["type"] == "error":
                    st.caption("Error")
    
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
                        st.caption("Factual Knowledge Base")
                    elif response_type == "groq_generated":
                        st.caption("AI Generated via Groq")
                    elif response_type == "demo_mode":
                        st.caption("Demo Mode")
                    elif response_type == "error":
                        st.caption("Error")
                    elif response_type == "compliance_refusal":
                        st.caption("Compliance Refusal")
            
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
