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

This fragmentation leads to poor visibility into profits and expenses, delayed payments, missed follow-ups, and operational overload on business heads.

This platform centralizes **tasks, transactions, reminders, meetings, and insights** — without changing how businesses already work.

---

## Core Features

### 🔐 Auth & Multi-Tenancy
- JWT-based login with bcrypt password hashing and refresh tokens
- Email verification on sign-up
- Complete organisation isolation — each SME's data is siloed

### ✉️ Team Invitation System
- Owners/Managers send email invitations via **Resend**
- Invitees accept via a secure token link and are auto-enrolled with an assigned role

### ✅ Task & Operations Management
- Create and assign tasks to team members or contractors
- Priority levels (High / Medium / Low) and status tracking (Pending → In Progress → Completed)
- Due dates with overdue detection
- Tasks can be linked to payments or transactions

### 💰 Financial Hub
A full in-app accounting view driven entirely by bank transaction data — similar to how Tally reflects entries across all statements. Every imported or recorded transaction automatically flows into:

#### Transaction Ledger
- Full ledger with date, description, category, amount (₹), reconciliation status
- Inline AI categorisation (GPT/rule-based) — assigns categories to uncategorised transactions
- Manual category editing with per-org saved category library

#### Profit & Loss Statement
- **Revenue from Operations** — all credit transactions, grouped by category
- **Cost of Sales** — debit transactions tagged as `Purchases`, `COGS`, `Stock`, `Materials`, or `Inventory`
- **Gross Profit** = Revenue − Cost of Sales (real calculation, not simulated)
- **Operating Expenses** — all remaining debit categories
- **Net Operating Profit / (Loss)** = Gross Profit − Operating Expenses
- Revenue vs Expenses bar chart (categories merged correctly — no duplicate bars)
- Year-filtered: automatically refreshes when year selector changes

#### Balance Sheet (Indian Vertical Format)
- **Capital & Liabilities** on top:
  - Trade Payables (pending contractor payments)
  - Other Current Liabilities (processing payments)
  - Owners' Equity / Retained Earnings
- **Assets** below:
  - Cash and Cash Equivalents (net of all bank credits/debits)
  - Trade Receivables (unreconciled credit transactions)
- Balance check indicator (✓ / ⚠)

#### Cash Flow Statement
- **A. Operating Activities** — inflows (credits) and outflows (debits) by category
- **B. Investing Activities** — placeholder for future asset entries
- **C. Financing Activities** — completed contractor payments
- Net change in cash, opening balance, and closing balance
- Year-filtered

#### Spending Analytics
- Pie chart: spending by category (null and "Uncategorized" correctly merged into one bucket)
- Contractor spends widget: shows formal Payment records; falls back to transactions categorised as Contractor/Vendor/Salary when no Payment records exist

### 📅 Meetings & Calendar
- Full calendar view (month navigation) with colour-coded meeting status
- Schedule, edit, and cancel meetings with multiple participants
- **View All Org Meetings toggle** (owner / admin / manager only) — instantly see every meeting across the organisation, even at ground level

### 🤖 Clara — AI Assistant
- Context-aware AI that operates strictly on your organisation's data
- Answers financial questions, surfaces tasks/meetings, explains trends in plain language
- Does not hallucinate and does not modify data

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI (async) |
| Database | PostgreSQL + Async SQLAlchemy |
| AI / NLP | OpenAI GPT, LangChain, LangGraph |
| Vector Store | Qdrant |
| Email | Resend SDK |
| Background Jobs | Celery + Redis |
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Infrastructure | Docker, Docker Compose |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (financial, analytics, meetings, tasks…)
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (analytics, payments, meetings, AI)
│   │   └── core/            # Config, security, exceptions
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI (DashboardLayout, Modals…)
│   │   ├── pages/           # FinancePage, MeetingsPage, TasksPage…
│   │   └── lib/             # Axios API client
└── documentation/
    └── diagram-viewer/      # UML/ERD diagram viewer (Vite + Mermaid + Panzoom)
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.12+ with Poetry
- (Optional) Node.js 18+

### Quick Start (Docker)

```bash
git clone https://github.com/IshitaAgarwal05/EM_SME_System.git
cd EM_SME_System
cp .env.example .env   # fill in DB_URL, OPENAI_API_KEY, RESEND_API_KEY, etc.
bash start_dev.sh
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/docs |
| Mailpit | http://localhost:8025 |

### Manual Setup

**Backend (Poetry)**
```bash
cd backend
# Install via Poetry (manages its own virtualenv at ~/.cache/pypoetry/virtualenvs/)
poetry install
# Run using Poetry's python to avoid venv conflicts
poetry env info   # note the python path
/path/to/poetry/venv/python -m uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Tests**
```bash
cd backend
./run_tests_manual.sh   # pytest
```

---

## Key API Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/register` | Register organisation + owner |
| `POST /api/v1/auth/login` | JWT login |
| `GET /api/v1/financial/transactions` | Transaction ledger |
| `GET /api/v1/financial/statements/pl?year=YYYY` | P&L statement |
| `GET /api/v1/financial/statements/bs` | Balance sheet |
| `GET /api/v1/financial/statements/cf?year=YYYY` | Cash flow statement |
| `GET /api/v1/analytics/breakdown/category?year=YYYY` | Expense by category |
| `GET /api/v1/meetings?view_all=true` | All org meetings (elevated roles) |
| `POST /api/v1/financial/transactions/categorize-all` | AI categorisation |

---

## Roadmap

- Advanced payment delay prediction
- Contractor performance analytics
- Role-based dashboards for larger teams
- External calendar integrations (Google Calendar)
- Audit-ready export reports (multi-sheet Excel)
- Statutory compliance helpers (GST summary)

---

## Notes

- This platform does not replace accountants or CAs.
- It focuses on operational clarity and decision support.
- AI components are intentionally constrained for reliability.

---

## Author

Built and maintained by Ishita Agarwal ❤️