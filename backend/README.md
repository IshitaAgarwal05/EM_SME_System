# Event Management SaaS - Backend

Production-grade FastAPI backend for Event Management SaaS platform.

## Features

- 🔐 **Authentication & Authorization**: JWT-based auth with refresh tokens, RBAC
- 🏢 **Multi-tenant**: Organization-level data isolation
- 📊 **Financial Management**: Transaction tracking, payment reconciliation, contractor management
- ✅ **Task Management**: Hierarchical tasks, multi-user assignments, time tracking
- 📅 **Meeting Scheduling**: Calendar integration, RSVP tracking, conflict detection
- 🔔 **Reminders**: Automated notifications via email/SMS/push
- 📈 **Analytics**: Income/expense analysis, contractor costs, revenue tracking
- 🤖 **AI Chatbot**: Data-grounded LLM with LangChain/LangGraph
- 📁 **Excel Import**: Automated bank statement parsing with Pandas
- 🔍 **Audit Logging**: Comprehensive change tracking

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Cache/Queue**: Redis 7+
- **Task Queue**: Celery with Redis backend
- **Vector DB**: Qdrant for AI embeddings
- **AI/ML**: LangChain, LangGraph, OpenAI, scikit-learn
- **Validation**: Pydantic V2
- **Migrations**: Alembic
- **Testing**: Pytest with async support

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Security, exceptions, middleware
│   ├── db/              # Database configuration
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── ai/              # LangChain/LangGraph
│   ├── ml/              # ML models
│   ├── tasks/           # Celery tasks
│   └── utils/           # Utilities
├── alembic/             # Database migrations
├── tests/               # Test suite
└── pyproject.toml       # Dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose (for local development)

### Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services with Docker Compose**
   ```bash
   cd ..
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start development server**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/api/docs`

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
poetry run ruff check .
```

### Type Checking

```bash
poetry run mypy app
```

### Database Migrations

Create a new migration:
```bash
poetry run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
poetry run alembic upgrade head
```

Rollback:
```bash
poetry run alembic downgrade -1
```

### Celery Workers

Start worker:
```bash
poetry run celery -A app.tasks.celery_app worker --loglevel=info
```

Start beat scheduler:
```bash
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (min 32 chars)
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `QDRANT_URL`: Qdrant vector database URL

## Security

- Passwords hashed with bcrypt
- JWT tokens with short expiry (15 min access, 7 day refresh)
- Role-based access control (Owner, Manager, Contractor, Viewer)
- Multi-tenant data isolation
- SQL injection prevention via SQLAlchemy
- Input validation with Pydantic
- Rate limiting
- Audit logging

## Deployment

### Docker

Build production image:
```bash
docker build -t event-management-backend .
```

Run container:
```bash
docker run -p 8000:8000 --env-file .env event-management-backend
```

### GCP Cloud Run

Deploy to Cloud Run:
```bash
gcloud run deploy event-management-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated
```

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the development team.
