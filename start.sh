#!/bin/bash
# Quick start script for Mac/Linux
# For Windows, use start_windows.bat

echo "🚀 Starting Nonprofit Intelligence Platform..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "📚 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
pip install -r requirements.txt > /dev/null 2>&1

# Start the application
echo "================================================"
echo "✅ Starting application..."
echo "📍 Access at: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "================================================"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
