#!/bin/bash

# Function to kill child processes on exit
trap 'kill $(jobs -p)' EXIT

echo "=================================================="
echo "   Event Management SaaS - Local Dev Starter"
echo "=================================================="

# Check for required databases
echo "Checking prerequisites..."
echo "NOTE: This script assumes you have the following running manually:"
echo "  - PostgreSQL (Port 5432)"
echo "  - Redis (Port 6379)"
echo "  - Qdrant (Port 6333)"
echo ""

# Start Backend
echo "[1/2] Starting Backend Service..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing backend dependencies..."
pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings \
    "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1" python-multipart \
    redis qdrant-client openai langchain langchain-openai langchain-qdrant langgraph langchain-community \
    pandas openpyxl xlrd celery structlog email-validator slowapi
pip install alembic # Ensure alembic is installed

# Export required environment variables
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export DEBUG=${DEBUG:-"true"}
export SECRET_KEY=${SECRET_KEY:-"development_secret_key_change_in_production_min_32_chars"}

# Handle OpenAI API Key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "sk-dummy-key-replace-with-real-one" ]; then
    if [ -f ".env" ]; then
        # Try to load from .env if exists
        ENV_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
        if [ ! -z "$ENV_KEY" ]; then
             export OPENAI_API_KEY="$ENV_KEY"
        fi
    fi
fi

# Fallback if still dummy
export OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-dummy-key-replace-with-real-one"}

export DATABASE_URL=${DATABASE_URL:-"postgresql+asyncpg://postgres:postgres@localhost:5432/event_management"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}
export QDRANT_URL=${QDRANT_URL:-"http://localhost:6333"}

# Fix for "ModuleNotFoundError: No module named 'app'"
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Attempt migrations
echo "Attempting to run database migrations..."
# We try to run alembic, but don't exit if it fails (user might not have DB yet)
alembic upgrade head || echo "⚠️  WARNING: Migrations failed. Likely cause: PostgreSQL is not running or database 'event_management' does not exist."

# check if running
echo "Starting Backend..."

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "[2/2] Starting Frontend Service..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    # Install missing dependencies identified during debugging
    npm install @tailwindcss/postcss @headlessui/react
else
    # Always ensure critical missing deps are installed
    npm install @tailwindcss/postcss @headlessui/react
fi
npm run dev -- --host &
FRONTEND_PID=$!
cd ..


echo ""
echo "=================================================="
echo "🚀 Services Started!"
echo "   Backend API: http://localhost:8000"
echo "   Frontend UI: http://localhost:5173"
echo "   Swagger Docs: http://localhost:8000/api/docs"
echo "=================================================="
echo "Press Ctrl+C to stop all services."

wait
