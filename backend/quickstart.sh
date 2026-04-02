#!/bin/bash
# Quick start script for the multi-agent AI system

set -e

echo "==================================="
echo "Multi-Agent AI System - Quick Start"
echo "==================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "! Please edit .env with your API keys before running"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=== Environment Setup Complete ==="
echo ""
echo "To start the application:"
echo "1. Start PostgreSQL: postgres -D /path/to/data"
echo "2. Start Redis: redis-server"
echo "3. Run the backend: uvicorn app.main:app --reload"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
