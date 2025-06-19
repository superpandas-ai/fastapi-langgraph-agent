import streamlit as st
import requests
import json
from datetime import datetime
import time
from typing import Optional, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="FastAPI Client",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class FastAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token = None
        self.session_id = None

    def set_token(self, token: str):
        """Set the access token for authenticated requests"""
        self.access_token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def clear_token(self):
        """Clear the access token"""
        self.access_token = None
        self.session.headers.pop('Authorization', None)

    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the API with error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json() if response.content else None,
                'headers': dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


def main():
    st.markdown('<h1 class="main-header">🚀 FastAPI Client</h1>',
                unsafe_allow_html=True)

    # Sidebar configuration
    st.sidebar.title("Configuration")

    # API Base URL input
    base_url = st.sidebar.text_input(
        "API Base URL",
        value="http://localhost:8000",
        help="Enter the base URL of your FastAPI server"
    )

    # Initialize client
    if 'client' not in st.session_state:
        st.session_state.client = FastAPIClient(base_url)
    else:
        st.session_state.client.base_url = base_url

    # Initialize session_id
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

    # Main navigation
    st.sidebar.subheader("Navigation")

    # Check if user is authenticated
    is_authenticated = st.session_state.client.access_token is not None

    # Navigation buttons
    if st.sidebar.button("🏠 Overview", use_container_width=True):
        st.session_state.current_page = "overview"

    if st.sidebar.button("🔐 Authentication", use_container_width=True):
        st.session_state.current_page = "authentication"

    # Disable buttons that require authentication
    if st.sidebar.button("🤖 Chatbot", use_container_width=True, disabled=not is_authenticated):
        st.session_state.current_page = "chatbot"

    if st.sidebar.button("💬 Chat Interface", use_container_width=True, disabled=not is_authenticated):
        st.session_state.current_page = "chat_interface"

    if st.sidebar.button("📊 Health & Status", use_container_width=True):
        st.session_state.current_page = "health_status"

    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "overview"

    # Show authentication warning for disabled features
    if not is_authenticated:
        st.sidebar.warning("⚠️ Some features require authentication")

    # Route to appropriate page
    if st.session_state.current_page == "overview":
        show_overview()
    elif st.session_state.current_page == "authentication":
        show_authentication()
    elif st.session_state.current_page == "chatbot":
        show_chatbot()
    elif st.session_state.current_page == "chat_interface":
        show_chat_interface()
    elif st.session_state.current_page == "health_status":
        show_health_status()


def show_overview():
    st.markdown('<h2 class="section-header">📋 API Overview</h2>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.info("**Available Endpoints:**")
        st.write("""
        - **Authentication**: Register, Login, Session Management
        - **Chatbot**: Agent Selection, Chat, Message Management  
        - **Health**: System Status and Health Checks
        - **Root**: Basic API Information
        """)

    with col2:
        st.info("**Current Status:**")
        if st.session_state.client.access_token:
            st.success("✅ Authenticated")
            st.write(f"Session ID: {st.session_state.session_id or 'Not set'}")
        else:
            st.warning("❌ Not Authenticated")

    # Test connection
    if st.button("🔍 Test Connection"):
        with st.spinner("Testing connection..."):
            result = st.session_state.client.make_request("GET", "/")

            if result['success']:
                st.success("✅ Connection successful!")
                st.json(result['data'])
            else:
                st.error(f"❌ Connection failed: {result['error']}")


def show_authentication():
    st.markdown('<h2 class="section-header">🔐 Authentication</h2>',
                unsafe_allow_html=True)

    # Authentication status
    if st.session_state.client.access_token:
        st.success("✅ You are currently authenticated!")
        if st.button("🚪 Logout"):
            st.session_state.client.clear_token()
            st.session_state.session_id = None
            st.rerun()

    # Initialize authentication mode
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = "login"

    # Authentication mode selector
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Login", use_container_width=True,
                     type="primary" if st.session_state.auth_mode == "login" else "secondary"):
            st.session_state.auth_mode = "login"
            st.rerun()

    with col2:
        if st.button("📝 Register", use_container_width=True,
                     type="primary" if st.session_state.auth_mode == "register" else "secondary"):
            st.session_state.auth_mode = "register"
            st.rerun()

    # Show login form
    if st.session_state.auth_mode == "login":
        st.subheader("🔑 User Login")
        with st.form("login_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input(
                "Password", type="password", key="login_password")

            login_submitted = st.form_submit_button("Login", type="primary")

            if login_submitted:
                with st.spinner("Logging in..."):
                    result = st.session_state.client.make_request(
                        "POST",
                        "/api/v1/auth/login",
                        data={
                            "username": login_email,
                            "password": login_password,
                            "grant_type": "password"
                        },
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded"}
                    )

                    if result['success']:
                        st.success("✅ Login successful!")
                        st.session_state.client.set_token(
                            result['data']['access_token'])
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed: {result['error']}")

    # Show registration form
    else:
        st.subheader("📝 User Registration")
        with st.form("register_form"):
            reg_email = st.text_input("Email", type="default")
            reg_password = st.text_input(
                "Password", type="password", max_chars=50)
            reg_confirm_password = st.text_input(
                "Confirm Password", type="password")

            # Password requirements help text
            st.markdown("""
            **Password Requirements:**
            - At least 8 characters long
            - At least one uppercase letter (A-Z)
            - At least one lowercase letter (a-z)
            - At least one number (0-9)
            - At least one special character (!@#$%^&*(),.?":{}|<>)
            """)

            register_submitted = st.form_submit_button(
                "Register", type="primary")

            if register_submitted:
                if reg_password != reg_confirm_password:
                    st.error("Passwords do not match!")
                else:
                    with st.spinner("Registering user..."):
                        result = st.session_state.client.make_request(
                            "POST",
                            "/api/v1/auth/register",
                            json={"email": reg_email, "password": reg_password}
                        )

                        if result['success']:
                            st.success("✅ Registration successful!")
                            st.json(result['data'])
                            # Auto-login after registration
                            st.session_state.client.set_token(
                                result['data']['token']['access_token'])
                            st.rerun()
                        else:
                            st.error(
                                f"❌ Registration failed: {result['error']}")

    # Session Management (only show if authenticated)
    if st.session_state.client.access_token:
        st.subheader("🔄 Session Management")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Create New Session"):
                with st.spinner("Creating session..."):
                    result = st.session_state.client.make_request(
                        "POST", "/api/v1/auth/session")

                    if result['success']:
                        st.success("✅ Session created!")
                        st.session_state.session_id = result['data']['session_id']
                        st.json(result['data'])
                    else:
                        st.error(
                            f"❌ Session creation failed: {result['error']}")

        with col2:
            if st.button("📋 Get User Sessions"):
                with st.spinner("Fetching sessions..."):
                    result = st.session_state.client.make_request(
                        "GET", "/api/v1/auth/sessions")

                    if result['success']:
                        st.success("✅ Sessions retrieved!")
                        sessions_df = pd.DataFrame(result['data'])
                        st.dataframe(sessions_df)
                    else:
                        st.error(
                            f"❌ Failed to get sessions: {result['error']}")

        # Update session name
        if st.session_state.session_id:
            st.subheader("✏️ Update Session Name")
            with st.form("update_session_name"):
                new_name = st.text_input("New Session Name", max_chars=100)
                if st.form_submit_button("Update Name"):
                    with st.spinner("Updating session name..."):
                        result = st.session_state.client.make_request(
                            "PATCH",
                            f"/api/v1/auth/session/{st.session_state.session_id}/name",
                            data={"name": new_name},
                            headers={
                                "Content-Type": "application/x-www-form-urlencoded"}
                        )

                        if result['success']:
                            st.success("✅ Session name updated!")
                            st.json(result['data'])
                        else:
                            st.error(
                                f"❌ Failed to update session name: {result['error']}")


def show_chatbot():
    st.markdown('<h2 class="section-header">🤖 Chatbot Management</h2>',
                unsafe_allow_html=True)

    if not st.session_state.client.access_token:
        st.warning("⚠️ Please authenticate first to access chatbot features.")
        return

    # Ensure a session exists
    if not st.session_state.session_id:
        st.warning("⚠️ No active session. Creating a new session...")
        with st.spinner("Creating session..."):
            result = st.session_state.client.make_request(
                "POST", "/api/v1/auth/session")

            if result['success']:
                st.session_state.session_id = result['data']['session_id']
                st.success("✅ Session created successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to create session: {result['error']}")
                return

    # Agent Selection
    st.subheader("🎯 Agent Selection")
    with st.form("agent_selection"):
        platform = st.selectbox(
            "Select Platform",
            ["fic", "sevdesk", "hr"],
            help="Choose the platform for your chatbot agent"
        )

        if st.form_submit_button("Select Agent"):
            with st.spinner("Selecting agent..."):
                result = st.session_state.client.make_request(
                    "POST",
                    "/api/v1/chatbot/select-agent",
                    json={"platform": platform}
                )

                if result['success']:
                    st.success(f"✅ Agent selected for platform: {platform}")
                    st.json(result['data'])
                else:
                    st.error(f"❌ Agent selection failed: {result['error']}")

    # Message Management
    st.subheader("💬 Message Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Get Session Messages"):
            with st.spinner("Fetching messages..."):
                result = st.session_state.client.make_request(
                    "GET", "/api/v1/chatbot/messages")

                if result['success']:
                    st.success("✅ Messages retrieved!")
                    if result['data']['messages']:
                        messages_df = pd.DataFrame(result['data']['messages'])
                        st.dataframe(messages_df)
                    else:
                        st.info("No messages in this session.")
                else:
                    st.error(f"❌ Failed to get messages: {result['error']}")

    with col2:
        if st.button("🗑️ Clear Chat History"):
            with st.spinner("Clearing chat history..."):
                result = st.session_state.client.make_request(
                    "DELETE", "/api/v1/chatbot/messages")

                if result['success']:
                    st.success("✅ Chat history cleared!")
                    st.json(result['data'])
                else:
                    st.error(
                        f"❌ Failed to clear chat history: {result['error']}")


def show_chat_interface():
    st.markdown('<h2 class="section-header">💬 Chat Interface</h2>',
                unsafe_allow_html=True)

    if not st.session_state.client.access_token:
        st.warning("⚠️ Please authenticate first to access chat features.")
        return

    # Ensure a session exists
    if not st.session_state.session_id:
        st.warning("⚠️ No active session. Creating a new session...")
        with st.spinner("Creating session..."):
            result = st.session_state.client.make_request(
                "POST", "/api/v1/auth/session")

            if result['success']:
                st.session_state.session_id = result['data']['session_id']
                st.success("✅ Session created successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to create session: {result['error']}")
                return

    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    # Chat configuration
    st.subheader("⚙️ Chat Configuration")
    col1, col2 = st.columns(2)

    with col1:
        platform = st.selectbox(
            "Platform (Optional)",
            [None, "fic", "sevdesk", "hr"],
            help="Select platform for the chat (optional)"
        )

    with col2:
        use_streaming = st.checkbox(
            "Use Streaming", value=False, help="Enable streaming responses")

    # Display chat messages
    st.subheader("💬 Chat History")

    # Create a container for chat messages
    chat_container = st.container()

    with chat_container:
        for i, message in enumerate(st.session_state.chat_messages):
            if message['role'] == 'user':
                st.markdown(f"**👤 You:** {message['content']}")
            else:
                st.markdown(f"**🤖 Assistant:** {message['content']}")
                if 'generated_code' in message and message['generated_code']:
                    with st.expander("📝 Generated Code"):
                        st.code(message['generated_code'], language='python')
                if 'fig' in message and message['fig']:
                    with st.expander("📊 Generated Plot"):
                        st.json(message['fig'])

    # Chat input
    st.subheader("💭 Send Message")
    with st.form("chat_form"):
        user_message = st.text_area(
            "Your message", height=100, placeholder="Type your message here...")

        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("Send Message")
        with col2:
            clear_chat = st.form_submit_button("Clear Chat")

        if clear_chat:
            st.session_state.chat_messages = []
            st.rerun()

        if submitted and user_message.strip():
            # Add user message to chat
            st.session_state.chat_messages.append({
                'role': 'user',
                'content': user_message
            })

            # Prepare chat request
            chat_request = {
                "messages": st.session_state.chat_messages,
                "platform": platform
            }

            # Send chat request
            with st.spinner("🤖 Processing your message..."):
                if use_streaming:
                    # Note: Streaming implementation would require WebSocket or Server-Sent Events
                    st.info(
                        "Streaming is not yet implemented in this interface. Using regular chat.")

                result = st.session_state.client.make_request(
                    "POST",
                    "/api/v1/chatbot/chat",
                    json=chat_request
                )

                if result['success']:
                    # Add assistant response to chat
                    assistant_message = result['data']['messages'][-1]
                    st.session_state.chat_messages.append(assistant_message)

                    # Display the response
                    st.success("✅ Response received!")
                    st.markdown(
                        f"**🤖 Assistant:** {assistant_message['content']}")

                    if 'generated_code' in result['data'] and result['data']['generated_code']:
                        with st.expander("📝 Generated Code"):
                            st.code(
                                result['data']['generated_code'], language='python')

                    if 'fig' in result['data'] and result['data']['fig']:
                        with st.expander("📊 Generated Plot"):
                            st.json(result['data']['fig'])

                    st.rerun()
                else:
                    st.error(f"❌ Chat request failed: {result['error']}")


def show_health_status():
    st.markdown('<h2 class="section-header">📊 Health & Status</h2>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏥 Health Check")
        if st.button("🔍 Check API Health"):
            with st.spinner("Checking API health..."):
                result = st.session_state.client.make_request(
                    "GET", "/api/v1/health")

                if result['success']:
                    st.success("✅ API is healthy!")
                    st.json(result['data'])
                else:
                    st.error(f"❌ Health check failed: {result['error']}")

    with col2:
        st.subheader("🌐 General Health")
        if st.button("🔍 Check General Health"):
            with st.spinner("Checking general health..."):
                result = st.session_state.client.make_request("GET", "/health")

                if result['success']:
                    st.success("✅ General health check passed!")
                    st.json(result['data'])
                else:
                    st.error(
                        f"❌ General health check failed: {result['error']}")

    # API Information
    st.subheader("ℹ️ API Information")
    if st.button("📋 Get API Info"):
        with st.spinner("Fetching API information..."):
            result = st.session_state.client.make_request("GET", "/")

            if result['success']:
                st.success("✅ API information retrieved!")
                st.json(result['data'])
            else:
                st.error(f"❌ Failed to get API information: {result['error']}")

    # Connection Status
    st.subheader("🔗 Connection Status")
    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.metric("Base URL", st.session_state.client.base_url)

    with status_col2:
        auth_status = "✅ Authenticated" if st.session_state.client.access_token else "❌ Not Authenticated"
        st.metric("Authentication", auth_status)

    with status_col3:
        session_status = "✅ Active" if st.session_state.session_id else "❌ No Session"
        st.metric("Session", session_status)


if __name__ == "__main__":
    main()
