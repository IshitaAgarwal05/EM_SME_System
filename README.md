# Event Management & SME Operations Platform

A unified operations platform for **event managers and small-to-medium enterprises (SMEs)** to manage tasks, finances, contractors, meetings, and operational insights in one place.

The system is designed for **business heads, founders, and operations leaders** — people who coordinate work for everyone else, but rarely have a tool that works *for them*.

This is not a generic task manager or an accounting replacement.  
It is an **operations clarity layer** built on top of real business data.

---

## Why This Exists

Event managers and SME owners typically operate across:
- bank statements (Excel files),
- WhatsApp task updates,
- manual payment follow-ups,
- scattered calendars,
- and post-facto financial summaries from accountants.

This fragmentation leads to:
- poor visibility into profits and expenses,
- delayed payments and missed follow-ups,
- operational overload on business heads.

This platform centralizes **tasks, transactions, reminders, meetings, and insights** — without changing how businesses already work.

---

## Core Capabilities

### Financial Visibility
- Import bank statements (Excel/CSV) directly from banks.
- Automatically classify income and expenses.
- Track contractor-wise and client-wise cash flow.
- View weekly, monthly, yearly summaries aligned to the **Indian financial year**.
- Show trend indicators *only when sufficient historical data exists*.

> Focus: analysis and insight — **not tax filing or statutory compliance**.

---

### Task & Operations Management
- Create and assign tasks to internal team members or contractors.
- Priority levels (High / Medium / Low).
- Status tracking (Pending, In Progress, Completed).
- Due dates with overdue detection.
- Tasks can be linked to payments or transactions.

---

### Meetings & Reminders
- Schedule meetings with multiple participants.
- Availability checks and confirmation flow before finalizing.
- Centralized reminders for:
  - payment due dates,
  - overdue receivables,
  - contract expiries,
  - upcoming meetings.

---

### Clara — Context-Aware AI Assistant
An internal AI assistant that operates **strictly on your organization’s data**.

Clara can:
- Answer financial questions (e.g., *monthly profit, top expenses*).
- Surface pending tasks or meetings.
- Explain trends and summaries in plain language.

Clara **does not hallucinate external information** and does not modify data autonomously.

---

## System Design Philosophy

- **Data-first**: The database is the single source of truth.
- **AI as an interface**, not a replacement for logic.
- **Deterministic workflows** for meetings, reminders, and approvals.
- **Separation of concerns** between core logic, analytics, and AI.
- Built for gradual scale — event managers first, SMEs next.

---

## Technology Stack

### Backend
- **Python 3.12**
- **FastAPI** (async)
- **PostgreSQL** (Async SQLAlchemy)
- **LangChain** (AI query orchestration)
- **LangGraph** (stateful business workflows)
- **Qdrant** (vector store for contextual retrieval)
- **Celery + Redis** (background jobs & reminders)

---

### Frontend
- **React 18** (Vite)
- **TypeScript**
- **Tailwind CSS**
- Modular, role-based UI for owners, managers, and contractors

---

### Infrastructure
- Docker & Docker Compose
- Designed for deployment on **Google Cloud Platform**
  (Cloud Run, Cloud SQL)

---

## Project Structure
```
├── backend/ 
│ ├── app/ 
│ │ ├── api/        # API Endpoints (v1) 
│ │ ├── models/     # SQLAlchemy Database Models 
│ │ ├── services/   # Business Logic (AI, Analytics, Files) 
│ │ └── core/       # Config & Security 
│ └── tests/        # Unit & Integration Tests 
├── frontend/ 
│ ├── src/ 
│ │ ├── components/ # Reusable UI Components 
│ │ ├── pages/      # Application Pages 
│ │ └── lib/        # Utilities & API Client 
└── docker-compose.yml # Container Orchestration
└── README.md
```

## Getting Started
### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.12+
- (Optional) Node.js 18+

---

### Development Setup (Recommended)

```bash
git clone <repo-url>
cd EM_SME_System

cp .env.example .env
# add environment variables (DB, OpenAI, etc.)

bash start_dev.sh
```

Services:
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs
- Mailpit: http://localhost:8025

## Manual Setup
### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Testing
Backend tests use pytest.
```bash
cd backend
./run_tests_manual.sh
```
### Roadmap (High-Level)
- Advanced payment delay prediction
- Contractor performance analytics
- Role-based dashboards for larger teams
- External calendar integrations
- Audit-ready export reports

### Notes
- This platform does not replace accountants or CAs.
- It focuses on operational clarity and decision support.
- AI components are intentionally constrained for reliability.

### Author
Built and maintained by Ishita Agarwal with ❤️