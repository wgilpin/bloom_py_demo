#!/bin/bash

# Bloom GCSE Mathematics Tutor - Local Server Startup Script
# ===========================================================

set -e  # Exit on error

echo "🚀 Starting Bloom GCSE Mathematics Tutor..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "   Creating .env from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and add your API keys before running the app!"
        echo "   Required: Set your LLM_PROVIDER and corresponding API key"
        echo ""
        read -p "Press Enter to continue anyway (or Ctrl+C to exit and configure .env)..."
    else
        echo "❌ env.example not found! Cannot create .env file."
        exit 1
    fi
fi

# Check if database exists
if [ ! -f bloom.db ]; then
    echo "ℹ️  No database found. The app will create it on startup."
    echo "   To load sample data, run: uv run python -m bloom.load_syllabus"
    echo ""
fi

# Display configuration info
echo "📋 Configuration:"
echo "   • Server will run on: http://localhost:8000"
echo "   • Database: bloom.db"
echo "   • Environment: .env"
echo ""

# Start the FastAPI server with uvicorn
echo "🔥 Starting FastAPI server with uvicorn..."
echo ""

# Run using uv with hot reload enabled for development
uv run uvicorn bloom.main:app --host 0.0.0.0 --port 8000 --reload

# Note: --reload enables hot reloading for development
# For production, remove --reload and consider using:
# uv run uvicorn bloom.main:app --host 0.0.0.0 --port 8000 --workers 4

