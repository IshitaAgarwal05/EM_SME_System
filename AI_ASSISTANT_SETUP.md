# AI Assistant Setup Guide

## Overview
The AI Assistant is a RAG (Retrieval Augmented Generation) chatbot powered by **OpenAI GPT-4** with **LangChain** and **LangGraph** for intelligent conversation flow.

## How It Works

### Architecture
```
User Message → Security Layer → RAG Retrieval → LLM (GPT-4) → Tools → Response
```

1. **Input Sanitization**: User input is sanitized and PII is masked
2. **RAG Retrieval**: Relevant context is fetched from Qdrant vector database
3. **LLM Processing**: OpenAI GPT-4 processes the query with context
4. **Tool Calling**: AI can call tools to fetch real-time data (expenses, tasks, etc.)
5. **Output Validation**: Response is validated for security before returning

### Components

#### 1. **LangGraph Workflow** (`chatbot.py`)
- **Retrieve Node**: Fetches relevant context from vector store
- **Agent Node**: Calls OpenAI GPT-4 with tools
- **Tools Node**: Executes tool calls (database queries)

#### 2. **Vector Store** (Qdrant)
- Stores embeddings of your organization's data
- Enables semantic search for relevant context
- Currently uses `text-embedding-3-small` model

#### 3. **AI Tools** (`tools.py`)
- `get_top_expenses_tool`: Fetches top expenses
- `get_monthly_breakdown_tool`: Monthly financial breakdown
- `get_client_payments_total_tool`: Total payments received
- More tools can be added for tasks, meetings, etc.

## Configuration Required

### Environment Variables

**CRITICAL**: You need to set the following in your `.env` file:

```bash
# OpenAI API Key (REQUIRED for AI to work)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional: Customize models
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1

# Qdrant Vector Database (Optional - defaults to localhost)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local Qdrant
QDRANT_COLLECTION_NAME=event_management_embeddings
```

### Getting an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add it to your `.env` file as `OPENAI_API_KEY=sk-...`

**Cost**: OpenAI charges per token. GPT-4-turbo costs ~$0.01 per 1K input tokens and ~$0.03 per 1K output tokens.

### Setting Up Qdrant (Vector Database)

**Option 1: Docker (Recommended)**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Option 2: Qdrant Cloud**
1. Sign up at https://cloud.qdrant.io
2. Create a cluster
3. Get the URL and API key
4. Update `QDRANT_URL` and `QDRANT_API_KEY` in `.env`

## Current Status

### ✅ What's Working
- Security layer (input sanitization, PII masking, output validation)
- LangGraph workflow structure
- Tool calling framework
- Graceful error handling

### ❌ What's NOT Working (Why AI Assistant Fails)

**Root Cause**: Missing or invalid `OPENAI_API_KEY`

**Current Behavior**:
- If `OPENAI_API_KEY` is missing or set to `sk-dummy-key`, the chatbot returns:
  > "I'm sorry, but my AI brain (OpenAI API Key) is not connected right now. Please check the system configuration."

**Error Messages You Might See**:
1. **"AI brain not connected"** → Missing/invalid API key
2. **"Trouble connecting to AI core"** → API key invalid or quota exceeded
3. **"Technical error"** → LangGraph execution failed (check logs)

## How to Fix

### Step 1: Add OpenAI API Key
```bash
# In backend/.env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 2: Restart Backend
```bash
# Stop current server (Ctrl+C)
./start_dev.sh
```

### Step 3: Test AI Assistant
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "What were my top expenses last month?",
    "history": []
  }'
```

## Features

### Supported Queries
- **Financial Analysis**: "What were my top expenses?", "Show me April's spending"
- **Task Management**: "List my pending tasks", "Create a task for..."
- **Meeting Scheduling**: "When is my next meeting?"
- **General Q&A**: Answers based on your organization's data

### Multilingual Support
- English
- Hinglish (Hindi-English mix)

### Security Features
- PII masking (emails, phone numbers, credit cards)
- Input sanitization (prevents injection attacks)
- Output validation (blocks sensitive data leakage)
- No code execution from user input

## Troubleshooting

### Issue: "AI brain not connected"
**Solution**: Set valid `OPENAI_API_KEY` in `.env`

### Issue: "Quota exceeded"
**Solution**: Check your OpenAI billing at https://platform.openai.com/account/billing

### Issue: Vector store errors
**Solution**: Ensure Qdrant is running on port 6333

### Issue: Tools not working
**Solution**: Check database connection and ensure transactions exist

## Future Enhancements
- [ ] Add more AI tools (create tasks, schedule meetings)
- [ ] Implement data indexing pipeline
- [ ] Add conversation memory
- [ ] Support for file uploads (analyze PDFs, images)
- [ ] Voice input/output
