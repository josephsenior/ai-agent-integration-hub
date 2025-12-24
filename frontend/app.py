"""Streamlit frontend for AI Agent Integration Hub."""

import json
from datetime import datetime
from typing import Any, Dict

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Agent Integration Hub",
    page_icon="🔗",
    layout="wide"
)

# API configuration
API_BASE_URL = st.sidebar.text_input(
    "API Base URL",
    value="http://localhost:8000",
    help="Base URL for the API gateway"
)

API_KEY = st.sidebar.text_input(
    "API Key",
    type="password",
    help="API key for authentication"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "message_history" not in st.session_state:
    st.session_state.message_history = []


def make_api_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make API request with authentication."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def main():
    """Main application."""
    st.title("🔗 AI Agent Integration Hub")
    st.markdown("Unified platform for AI agent integrations across multiple channels")
    
    # Sidebar
    st.sidebar.title("Configuration")
    
    # Health check
    if st.sidebar.button("Check Health"):
        health = make_api_request("/health")
        if "error" not in health:
            st.sidebar.success("✅ API is healthy")
            st.sidebar.json(health)
        else:
            st.sidebar.error(f"❌ Error: {health['error']}")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat",
        "📨 Messages",
        "🔌 Integrations",
        "📊 Analytics"
    ])
    
    # Chat Tab
    with tab1:
        st.header("Chat with Agent")
        
        # Channel selection
        col1, col2 = st.columns(2)
        with col1:
            channel = st.selectbox(
                "Channel",
                ["api", "slack", "discord", "email", "webhook", "websocket"]
            )
        with col2:
            channel_id = st.text_input(
                "Channel ID",
                placeholder="Slack channel, Discord channel, email address, etc.",
                help="Optional: Channel identifier for sending responses"
            )
        
        # User ID
        user_id = st.text_input("User ID (optional)", placeholder="user123")
        
        # Context
        with st.expander("Additional Context"):
            context_text = st.text_area(
                "Context JSON",
                value='{"key": "value"}',
                help="Additional context to pass to the agent"
            )
            try:
                context = json.loads(context_text) if context_text else {}
            except json.JSONDecodeError:
                context = {}
                st.error("Invalid JSON in context")
        
        # Chat interface
        st.subheader("Conversation")
        
        # Display message history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "metadata" in msg:
                    with st.expander("Metadata"):
                        st.json(msg["metadata"])
        
        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Send to agent
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    response_data = make_api_request(
                        "/api/v1/agents/chat",
                        method="POST",
                        data={
                            "message": prompt,
                            "channel": channel,
                            "user_id": user_id if user_id else None,
                            "channel_id": channel_id if channel_id else None,
                            "context": context,
                            "metadata": {}
                        }
                    )
                    
                    if "error" not in response_data:
                        response_text = response_data.get("response", "No response")
                        st.write(response_text)
                        
                        # Add to message history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "metadata": response_data
                        })
                        
                        st.session_state.message_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "request": prompt,
                            "response": response_text,
                            "channel": channel,
                            "message_id": response_data.get("message_id")
                        })
                    else:
                        st.error(f"Error: {response_data['error']}")
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Messages Tab
    with tab2:
        st.header("Message History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_channel = st.selectbox(
                "Filter by Channel",
                ["All", "api", "slack", "discord", "email", "webhook", "websocket"]
            )
        with col2:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All", "pending", "processing", "completed", "failed", "delivered"]
            )
        with col3:
            limit = st.number_input("Limit", min_value=1, max_value=100, value=50)
        
        # Fetch messages
        if st.button("Refresh Messages"):
            params = {}
            if filter_channel != "All":
                params["channel"] = filter_channel
            if filter_status != "All":
                params["status"] = filter_status
            params["limit"] = limit
            
            endpoint = "/api/v1/messages?" + "&".join([f"{k}={v}" for k, v in params.items()])
            messages = make_api_request(endpoint)
            
            if "error" not in messages and isinstance(messages, list):
                st.success(f"Found {len(messages)} messages")
                
                for msg in messages:
                    with st.expander(f"Message {msg.get('id', 'Unknown')[:8]}... - {msg.get('channel', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Content:**")
                            st.write(msg.get("content", "N/A"))
                        with col2:
                            st.write("**Response:**")
                            st.write(msg.get("response", "N/A"))
                        
                        st.write("**Metadata:**")
                        st.json({
                            "status": msg.get("status"),
                            "user_id": msg.get("user_id"),
                            "channel_id": msg.get("channel_id"),
                            "created_at": msg.get("created_at"),
                            "processed_at": msg.get("processed_at")
                        })
            else:
                st.error(f"Error fetching messages: {messages.get('error', 'Unknown error')}")
    
    # Integrations Tab
    with tab3:
        st.header("Integration Management")
        st.info("Integration management interface coming soon!")
        
        st.subheader("Available Integrations")
        integrations = [
            {"name": "Slack", "status": "✅ Available", "type": "slack"},
            {"name": "Discord", "status": "✅ Available", "type": "discord"},
            {"name": "Email", "status": "✅ Available", "type": "email"},
            {"name": "Webhook", "status": "✅ Available", "type": "webhook"},
            {"name": "WebSocket", "status": "✅ Available", "type": "websocket"},
        ]
        
        for integration in integrations:
            with st.expander(f"{integration['name']} - {integration['status']}"):
                st.write(f"**Type:** {integration['type']}")
                st.write("Configure this integration in your `.env` file")
    
    # Analytics Tab
    with tab4:
        st.header("Analytics & Metrics")
        st.info("Analytics dashboard coming soon!")
        
        # Placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", len(st.session_state.message_history))
        with col2:
            st.metric("Channels", "5")
        with col3:
            st.metric("Integrations", "5")
        with col4:
            st.metric("Success Rate", "98%")


if __name__ == "__main__":
    main()

