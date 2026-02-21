# Presentation: EM SME System
### Event Management SaaS for Small & Medium Enterprises
**Slide-by-Slide Content Guide**

---

## SLIDE 1 — Title Slide

**Content:**
- Title: **EM SME System — Event Management SaaS for SMEs**
- Subtitle: *An intelligent platform for team collaboration, financial tracking, and event lifecycle management*
- Your name / Internship Organization
- Date: February 2026

**What to Say:**
"Good morning everyone. I'm presenting today on EM SME System — an event management SaaS platform that I have been designing and developing as part of my internship. The system is targeted at small and medium enterprises that need to manage teams, events, finances, and tasks in a single unified platform."

---

## SLIDE 2 — Problem Statement

**Content (Bullet Points):**
- SMEs manage events using fragmented tools — WhatsApp, Excel sheets, and email
- No centralized system to track tasks, team, and finances together
- Lack of accountability in assigning work and tracking payments to contractors
- Manual effort needed for financial reconciliation from bank statements
- No AI-powered insights available for SME budget owners

**What to Say:**
"Small businesses today face a significant challenge. They use disconnected tools — WhatsApp for communication, Excel for budgets, email for invites. Nothing ties it all together. There is no single platform where an event organizer can see what tasks are pending, who owes whom money, and how the event budget is tracking — all at once. EM SME System aims to solve exactly this."

---

## SLIDE 3 — Solution Overview

**Content:**
- A unified SaaS platform built for SMEs and event organizers
- Modules: Authentication, Team Management, Task Management, Financial Tracking, Event Management, AI Assistant, File Management, Meetings
- Accessible via Web; Mobile-ready architecture
- Cloud-deployed on Vercel (frontend) and Render (backend)

**Diagram:** (Insert Component Diagram from UML_Diagrams.md)

**What to Say:**
"Our solution is a full-stack SaaS application. The frontend is built in React with TypeScript, and the backend is a production-grade FastAPI application backed by PostgreSQL. Users can register their organization, invite their team, track tasks, upload bank statements, manage contractors and payments — and get AI-driven insights about their business."

---

## SLIDE 4 — Key Features

**Content (Split into two columns):**

**Core Operations:**
- ✅ Multi-tenant organization management
- ✅ Role-Based Access Control (Owner, Manager, Employee, Contractor)
- ✅ Email invitation system via Resend API
- ✅ Task Board with assignments, subtasks, comments
- ✅ Event/Project creation with budget tracking

**Intelligence Layer:**
- ✅ Upload CSV/XLSX bank statements — auto-import transactions
- ✅ Financial reconciliation and contractor payment tracking
- ✅ AI Business Assistant powered by GPT-4 / Gemini
- ✅ Analytics dashboard with insights
- ✅ File management with secure uploads

**What to Say:**
"Let me walk you through the features. At the core, the platform supports multi-tenant architecture — each company is a separate isolated tenant. Managers can invite employees via email, assign tasks, and track completion. On the financial side, users can upload their bank statements and the system automatically imports transactions. Contractors can be managed with their payment records, UPI IDs, and service types. Finally, an AI assistant powered by LangChain and GPT-4 can answer business questions about your financials and event performance."

---

## SLIDE 5 — System Architecture

**Content:**
```
Frontend (React + TypeScript)
         ↕ REST API (HTTPS)
Backend (FastAPI + Python)
    ├── PostgreSQL (Primary DB)
    ├── Redis (Caching & Sessions)
    ├── Qdrant (Vector DB for AI)
    ├── OpenAI / Gemini (LLM APIs)
    └── Resend (Email Delivery)
```

**What to Say:**
"The architecture follows a clean separation of concerns. The React frontend communicates with the FastAPI backend via REST APIs over HTTPS. The backend uses PostgreSQL as the primary database with full asyncio support for high performance. Redis handles caching and rate limiting. Qdrant is a vector database used by the AI module for semantic search over business data. All email communication goes through Resend's transactional email API."

---

## SLIDE 6 — Technology Stack

**Content (Table):**

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + TypeScript | UI Framework |
| Styling | Vanilla CSS / Custom | Design |
| State/API | Axios, React Context | API communication |
| Backend | FastAPI (Python 3.11) | REST API server |
| ORM | SQLAlchemy 2.0 (Async) | Database abstraction |
| Migrations | Alembic | Schema versioning |
| Auth | JWT (python-jose) + bcrypt | Authentication |
| Email | Resend SDK v2 | Transactional emails |
| AI | LangChain + LangGraph + GPT-4 | AI agent pipeline |
| Vector DB | Qdrant | Semantic search |
| Deployment | Vercel + Render | Cloud hosting |
| Database | PostgreSQL 15+ | Primary data store |
| Packaging | Poetry | Python dependency management |
| Containers | Docker | Containerization |

**What to Say:**
"The technology choices reflect a modern, production-ready stack. FastAPI is one of the fastest Python web frameworks, with native async support. SQLAlchemy with asyncpg gives us asynchronous database access. For AI, we use LangGraph — a graph-based agent framework on top of LangChain — enabling multi-step reasoning. The entire deployment pipeline is containerized with Docker, simplifying production deployment."

---

## SLIDE 7 — Database Design (ERD Overview)

**Content:**
- 14 database tables across 5 domains
- Multi-tenant: all data scoped to `organization_id`
- UUID primary keys for global uniqueness
- Key relationships:
  - Organization → Users → Tasks → Assignments
  - Organization → Transactions → Events
  - Organization → Contractors → Payments

**Diagram:** (Insert ER Diagram or summary from UML_Diagrams.md)

**What to Say:**
"The database schema has 14 tables, all scoped by organization ID for strict multi-tenancy. Every user, task, transaction, and event belongs to an organization — data from one SME can never be accessed by another. We use UUID primary keys throughout for global uniqueness, which also simplifies future distributed scaling."

---

## SLIDE 8 — User Roles & Access Control

**Content:**

| Role | Create Events | Manage Team | Upload Statements | View Analytics |
|---|---|---|---|---|
| **Owner** | ✅ | ✅ | ✅ | ✅ |
| **Manager** | ✅ | ✅ | ✅ | ✅ |
| **Employee** | ❌ | ❌ | ❌ | Limited |
| **Contractor** | ❌ | ❌ | ❌ | ❌ |

**What to Say:**
"The system implements Role-Based Access Control with four roles. The Owner has full access and is created automatically when an organization registers. Managers can invite team members and manage finances. Employees can manage their tasks and files but cannot access financial data. Contractors have the most restricted access — they can only view tasks assigned to them."

---

## SLIDE 9 — Team Invitation Flow (Demo)

**Content:**
1. Owner/Manager enters email and selects role in the "Invite Member" modal
2. System generates a secure token and sends an email via Resend
3. Invitee clicks the link and is taken to the Accept Invitation page
4. Invitee fills in their name and password
5. Account is created, linked to the organization, and invitee is logged in

**Diagram:** (Insert Invitation Sequence Diagram from UML_Diagrams.md)

**What to Say:**
"The invitation flow is fully automated. When an owner invites somebody, a secure 48-character random token is generated and sent via email. The link is valid for 7 days. When the invitee clicks the link, they are taken to a React page that validates the token and lets them sign up directly into the organization — no admin approval needed. This was one of the core features I implemented during this internship."

---

## SLIDE 10 — Financial Module (Demo)

**Content:**
- Upload bank statement (CSV/XLSX)
- Auto-parse and import transactions
- Categorize transactions by type, event, or contractor
- Reconcile payments against contractor invoices
- View monthly summaries and dashboards

**What to Say:**
"The financial module is a key differentiator. Organisation owners can upload their bank statement as a CSV or Excel file. Our parser reads each row and creates a Transaction record in the database. From there, the manager can reconcile transactions, link them to specific events, and generate financial reports. For contractors, separate payment records track due dates, invoices, and payment mode — whether UPI, bank transfer, or cheque."

---

## SLIDE 11 — AI Business Assistant

**Content:**
- Powered by LangChain + LangGraph (multi-step reasoning)
- Connected to GPT-4 and Google Gemini APIs
- Qdrant vector database for semantic context
- Can answer: "What is our total spending on events this month?"
- Can explain financial anomalies, summarize task backlogs
- Future: predictive budget forecasting

**What to Say:**
"The AI module uses LangGraph — a stateful directed graph agent — to handle multi-step business queries. The agent can reason about financial data, summarize task status, and provide natural language answers. We use Qdrant as a vector store so the AI can retrieve relevant context about your specific organization's data before generating an answer. This is similar to a Retrieval-Augmented Generation (RAG) architecture."

---

## SLIDE 12 — Deployment & DevOps

**Content:**
- **Frontend:** Deployed on Vercel with automatic CI/CD from GitHub
- **Backend:** Dockerized FastAPI on Render Free Tier
- **Database Migrations:** Run automatically via `alembic upgrade head` in Docker startup
- **Environment variables:** Managed via Render dashboard and Vercel project settings
- **Security:** JWT auth, CORS configuration, TrustedHostMiddleware, rate limiting (SlowAPI), security headers (HSTS, X-Frame-Options)

**What to Say:**
"Deployment is fully automated. Whenever I push to the main branch on GitHub, Vercel automatically rebuilds and deploys the frontend. On the backend side, Render detects the changes, builds the Docker image, and deploys the container. Database migrations run automatically when the container starts. For security, we have JWT-based authentication with refresh token rotation, rate limiting to prevent brute force attacks, and standard security headers."

---

## SLIDE 13 — Current Status & Challenges

**Content:**

**✅ Completed:**
- Multi-tenant organization registration and authentication
- Role-based team management and email invitations
- Task board with assignments, subtasks, comments
- Financial module: bank statement upload, transactions, contractors, payments
- Event management and budgeting
- AI assistant integration
- File management module
- Meetings module
- Cloud deployment (Vercel + Render)

**⚠️ Challenges Faced:**
- Poetry dependency resolution conflicts across LangChain versions
- Missing `bcrypt` library causing 500 errors on Render
- Alembic migration script was incomplete (missing `events` table)
- CORS and PYTHONPATH configuration for Docker

**What to Say:**
"Most of the core functionality is complete. The deployment went through several rounds of debugging — particularly around Python dependency conflicts with the LangChain ecosystem and database migration issues on Render's free tier. These were learning experiences that deepened my understanding of production deployment challenges."

---

## SLIDE 14 — Future Roadmap

**Content:**
- 📱 React Native mobile app for on-the-go task management
- 📊 Advanced analytics: budget forecasting with ML
- 🔔 Real-time notifications via WebSockets
- 🗓️ Google/Microsoft Calendar integration for meetings
- 📋 PDF invoice generation for payments
- 🌐 Multi-language support
- 💳 Payment gateway integration (Razorpay)
- 👥 SSO (Google/Microsoft login)

**What to Say:**
"Looking ahead, the mobile app scaffolding is already in the repository. In the next phase, I plan to add real-time notifications using WebSockets, Google Calendar integration for meeting scheduling, and ML-based budget forecasting using the financial data already being collected. The architecture is designed to support these extensions without major refactoring."

---

## SLIDE 15 — Conclusion & Thank You

**Content:**
- EM SME System addresses real problems faced by event-organizing SMEs
- Full-stack, production-deployed, AI-enhanced SaaS platform
- Built using industry-standard tools and best practices
- Scalable, secure, multi-tenant architecture
- Open to questions!

**What to Say:**
"In conclusion, EM SME System is a production-ready, AI-enhanced SaaS platform tailored for SMEs managing events and projects. It integrates team management, task tracking, financial reconciliation, and AI insights in a single platform — replacing the fragmented tools that most SMEs currently rely on. The system is live and accessible on the web today. Thank you for your time, and I'm happy to take any questions."

---

*Repository: https://github.com/IshitaAgarwal05/EM_SME_System*
*Live Demo (Frontend): https://em-sme-system.vercel.app*
*Live Demo (API): https://em-sme-system-ws.onrender.com*
