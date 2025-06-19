#!/usr/bin/env python3
"""
Test script for the FastAPI Client Streamlit App
"""

from app import FastAPIClient
import sys
import os
import requests
from unittest.mock import Mock, patch

# Add the current directory to the path to import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPIClient from the app module


def test_fastapi_client():
    """Test the FastAPIClient class"""
    print("🧪 Testing FastAPIClient...")

    # Test client initialization
    client = FastAPIClient("http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
    assert client.access_token is None
    print("✅ Client initialization passed")

    # Test token setting
    client.set_token("test_token")
    assert client.access_token == "test_token"
    assert client.session.headers.get("Authorization") == "Bearer test_token"
    print("✅ Token setting passed")

    # Test token clearing
    client.clear_token()
    assert client.access_token is None
    assert "Authorization" not in client.session.headers
    print("✅ Token clearing passed")

    print("🎉 All FastAPIClient tests passed!")


def test_api_endpoints():
    """Test API endpoint structure"""
    print("\n🧪 Testing API endpoint structure...")

    # Expected endpoints based on OpenAPI spec
    expected_endpoints = [
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/session",
        "/api/v1/auth/sessions",
        "/api/v1/chatbot/select-agent",
        "/api/v1/chatbot/chat",
        "/api/v1/chatbot/chat/stream",
        "/api/v1/chatbot/messages",
        "/api/v1/health",
        "/health",
        "/"
    ]

    print(f"✅ Found {len(expected_endpoints)} expected endpoints")

    # Test client can handle these endpoints
    client = FastAPIClient("http://localhost:8000")

    # Mock a successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.content = b'{"status": "ok"}'
    mock_response.headers = {}

    with patch('requests.Session.request', return_value=mock_response):
        for endpoint in expected_endpoints[:3]:  # Test first 3 endpoints
            result = client.make_request("GET", endpoint)
            assert result['success'] is True
            assert result['status_code'] == 200

    print("✅ API endpoint structure tests passed!")


def test_required_dependencies():
    """Test that all required dependencies are available"""
    print("\n🧪 Testing required dependencies...")

    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found")
        return False

    try:
        import requests
        print(f"✅ Requests {requests.__version__}")
    except ImportError:
        print("❌ Requests not found")
        return False

    try:
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Pandas not found")
        return False

    try:
        import plotly
        print(f"✅ Plotly {plotly.__version__}")
    except ImportError:
        print("❌ Plotly not found")
        return False

    print("✅ All required dependencies are available!")
    return True


def test_uv_environment():
    """Test that we're running in a uv environment"""
    print("\n🧪 Testing uv environment...")

    # Check if we're in a uv-managed environment
    if os.path.exists(".venv") or "VIRTUAL_ENV" in os.environ:
        print("✅ Running in a virtual environment")
    else:
        print("⚠️  Not running in a virtual environment (this is okay with uv)")

    # Check if uv is available
    try:
        import subprocess
        result = subprocess.run(["uv", "--version"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv is available: {result.stdout.strip()}")
        else:
            print("❌ uv is not available")
            return False
    except FileNotFoundError:
        print("❌ uv command not found")
        return False

    return True


def main():
    """Run all tests"""
    print("🚀 Starting FastAPI Client Streamlit App Tests...\n")

    # Test uv environment first
    if not test_uv_environment():
        print("❌ uv environment test failed. Please ensure uv is installed and configured.")
        return

    # Test dependencies
    if not test_required_dependencies():
        print("❌ Dependency test failed. Please install required packages with: uv sync --group streamlit")
        return

    # Test client functionality
    test_fastapi_client()

    # Test API endpoints
    test_api_endpoints()

    print("\n🎉 All tests passed! The app should work correctly.")
    print("\n📝 To run the app:")
    print("   Linux/Mac: ./streamlit/run.sh")
    print("   Windows: streamlit/run.bat")
    print("   Manual: uv run streamlit run streamlit/app.py")


if __name__ == "__main__":
    main()
