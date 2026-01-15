#!/bin/bash
source venv/bin/activate

# Export dummy environment variables for testing
export SECRET_KEY="test_secret_key_min_32_chars_for_security_validation"
export OPENAI_API_KEY="sk-test-dummy-key"
export QDRANT_URL="http://localhost:6333" 
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/event_management"

pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings \
    "python-jose[cryptography]" "passlib[bcrypt]" python-multipart \
    pytest pytest-asyncio httpx \
    redis qdrant-client openai langchain langchain-openai langchain-qdrant langgraph langchain-community \
    pandas openpyxl celery structlog email-validator --upgrade

# Run tests
PYTHONPATH=. pytest tests/ -v
