@echo off
REM FastAPI Client Streamlit App Launcher for Windows

echo 🚀 Starting FastAPI Client Streamlit App...

REM Check if uv is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ uv is not installed. Please install uv first:
    echo    Visit: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Check if we're in the project root (where pyproject.toml is)
if not exist "pyproject.toml" (
    echo ❌ pyproject.toml not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Install dependencies using uv
echo 📥 Installing dependencies using uv...
uv sync --group streamlit

REM Check if FastAPI server is running
echo 🔍 Checking if FastAPI server is running...
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FastAPI server is running on http://localhost:8000
) else (
    echo ⚠️  Warning: FastAPI server doesn't seem to be running on http://localhost:8000
    echo    Please start your FastAPI server first.
    echo    You can still use the app to test connections to other URLs.
)

REM Launch Streamlit app using uv
echo 🌐 Launching Streamlit app...
echo    The app will open in your browser at http://localhost:8501
echo    Press Ctrl+C to stop the app
echo.

uv run streamlit run streamlit/app.py --server.port 8501 --server.address 0.0.0.0

pause 