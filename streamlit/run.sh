#!/bin/bash

# FastAPI Client Streamlit App Launcher

echo "🚀 Starting FastAPI Client Streamlit App..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if we're in the project root (where pyproject.toml is)
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run this script from the project root directory."
    exit 1
fi

# Install dependencies using uv
echo "📥 Installing dependencies using uv..."
uv sync --group streamlit

# Check if FastAPI server is running
echo "🔍 Checking if FastAPI server is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ FastAPI server is running on http://localhost:8000"
else
    echo "⚠️  Warning: FastAPI server doesn't seem to be running on http://localhost:8000"
    echo "   Please start your FastAPI server first."
    echo "   You can still use the app to test connections to other URLs."
fi

# Launch Streamlit app using uv
echo "🌐 Launching Streamlit app..."
echo "   The app will open in your browser at http://localhost:8501"
echo "   Press Ctrl+C to stop the app"
echo ""

uv run streamlit run streamlit/app.py --server.port 8501 --server.address 0.0.0.0 