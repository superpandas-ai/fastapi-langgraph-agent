# FastAPI Client - Streamlit App

A comprehensive Streamlit application that provides a user-friendly interface to interact with all endpoints of your FastAPI application.

## Features

### 🔐 Authentication
- **User Registration**: Create new user accounts
- **User Login**: Authenticate with email and password
- **Session Management**: Create, list, and manage chat sessions
- **Session Naming**: Update session names for better organization

### 🤖 Chatbot Management
- **Agent Selection**: Choose between different platforms (fic, sevdesk, hr)
- **Message Management**: View and clear chat history
- **Real-time Chat**: Interactive chat interface with the selected agent

### 💬 Chat Interface
- **Interactive Chat**: Send messages and receive responses
- **Code Generation**: View generated code snippets
- **Data Visualization**: Display generated plots and figures
- **Chat History**: Persistent chat history within the session

### 📊 Health & Status
- **API Health Checks**: Monitor API health status
- **Connection Status**: Real-time connection information
- **API Information**: View basic API details

## Prerequisites

- **uv**: The project uses `uv` for dependency management
- **Python 3.13+**: Required for the project
- **FastAPI Server**: Your FastAPI server should be running

### Installing uv

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative:**
Visit [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/) for more installation options.

## Installation

1. **Install dependencies using uv:**
   ```bash
   # From the project root directory
   uv sync --group streamlit
   ```

2. **Make sure your FastAPI server is running** (default: http://localhost:8000)

3. **Run the Streamlit app:**
   ```bash
   # Using the launcher script
   ./streamlit/run.sh  # Linux/macOS
   streamlit/run.bat   # Windows
   
   # Or manually
   uv run streamlit run streamlit/app.py
   ```

## Usage

### Getting Started
1. Open the Streamlit app in your browser (http://localhost:8501)
2. Configure the API Base URL in the sidebar (default: http://localhost:8000)
3. Test the connection using the "Test Connection" button

### Authentication
1. **Register**: Create a new account with email and password
2. **Login**: Use your credentials to authenticate
3. **Session Management**: Create new chat sessions and manage existing ones

### Chatting
1. **Select Agent**: Choose a platform for your chatbot
2. **Send Messages**: Use the chat interface to interact with the AI
3. **View Responses**: See generated code and visualizations
4. **Manage History**: Clear chat history when needed

### Monitoring
- Check API health status
- Monitor connection status
- View session information

## Configuration

### API Base URL
Set your FastAPI server URL in the sidebar. Default is `http://localhost:8000`.

### Authentication
The app automatically handles JWT tokens and session management. Once logged in, you'll remain authenticated until you logout or the token expires.

### Chat Configuration
- **Platform Selection**: Choose between fic, sevdesk, or hr platforms
- **Streaming**: Enable/disable streaming responses (currently using regular chat)

## API Endpoints Covered

### Authentication (`/api/v1/auth/`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /session` - Create new session
- `GET /sessions` - List user sessions
- `PATCH /session/{session_id}/name` - Update session name

### Chatbot (`/api/v1/chatbot/`)
- `POST /select-agent` - Select chatbot agent
- `POST /chat` - Send chat message
- `POST /chat/stream` - Stream chat responses
- `GET /messages` - Get session messages
- `DELETE /messages` - Clear chat history

### Health & Status
- `GET /api/v1/health` - API health check
- `GET /health` - General health check
- `GET /` - API information

## Development

### Testing
Run the test suite to verify everything works:
```bash
uv run python streamlit/test_app.py
```

### Adding New Features
The app is modular and easy to extend. Each section is in its own function:
- `show_overview()` - API overview and connection testing
- `show_authentication()` - User registration and login
- `show_chatbot()` - Agent selection and message management
- `show_chat_interface()` - Interactive chat interface
- `show_health_status()` - Health monitoring and status

### Customization
- Modify the CSS in the `st.markdown()` section for custom styling
- Add new endpoints by extending the `FastAPIClient` class
- Customize the UI layout by modifying the column structure

### Dependency Management
The project uses `uv` for dependency management. Dependencies are defined in `pyproject.toml`:

```toml
[dependency-groups]
streamlit = [
    "streamlit>=1.40.1",
    "requests>=2.31.0",
    "pandas>=2.0.0",
    "plotly>=5.15.0",
]
```

To add new dependencies:
1. Add them to the `streamlit` dependency group in `pyproject.toml`
2. Run `uv sync --group streamlit` to install

## Troubleshooting

### Connection Issues
- Verify your FastAPI server is running
- Check the API Base URL in the sidebar
- Ensure no firewall is blocking the connection

### Authentication Issues
- Verify your credentials are correct
- Check if the user account exists
- Ensure the API server is properly configured

### Chat Issues
- Make sure you're authenticated
- Verify an agent is selected
- Check if the session is active

### uv Issues
- Ensure `uv` is installed and in your PATH
- Run `uv sync --group streamlit` to reinstall dependencies
- Check that you're running from the project root directory

## License

This project is part of the FastAPI LangGraph Agent template. 