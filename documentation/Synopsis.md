# PROJECT SYNOPSIS
## EM SME System — Event Management SaaS for Small & Medium Enterprises

**Submitted by:** Ishita Agarwal  
**Internship Organization:** [Organization Name]  
**Academic Institution:** [Institution Name]  
**Date:** February 2026

---

## 1. PROJECT / PROBLEM DEFINITION

### 1.1 Problem Statement

Small and Medium Enterprises (SMEs) that regularly organize events — cultural programs, corporate conferences, product launches, community gatherings, and intra-organizational workshops — face a significant operational challenge: the absence of a centralized, integrated platform to manage the complete event lifecycle.

Currently, most SMEs rely on a fragmented set of tools and informal communication channels:
- **WhatsApp / Telegram** for task delegation and team communication
- **Microsoft Excel / Google Sheets** for financial tracking and budgeting
- **Gmail / Outlook** for team invitations and approvals
- **Physical registers or scattered documents** for contractor records and payment tracking
- **No system** for tracking task accountability and overdue items

This fragmentation leads to:
1. **Communication breakdowns** — tasks fall through the cracks, responsibilities are unclear
2. **Financial leakage** — payments to contractors are not tracked, reconciliation is done manually after the fact
3. **No audit trail** — there is no historical record connecting a task to a payment to a contractor to an event
4. **Scalability issues** — as the team grows, managing permissions and access informally becomes chaotic
5. **No data-driven insights** — decisions on budget allocation and staffing are made based on gut feeling, not analytics

### 1.2 Proposed Solution

**EM SME System** is a cloud-based, multi-tenant SaaS (Software as a Service) platform specifically designed to address these pain points for SMEs. The system unifies the following lifecycle components into a single, web-accessible application:

- **Organization & Team Management:** Multi-tenant architecture supporting multiple independent organizations. Role-based access control (RBAC) with roles: Owner, Manager, Employee, and Contractor.
- **Task Management:** A collaborative task board with assignments, subtasks, comments, priorities, and due-date tracking.
- **Financial Module:** Import bank statements via CSV/XLSX, manage transactions categorized by event and contractor, reconcile payments, and generate financial summaries.
- **Event/Project Management:** Create events or projects with budgets, link transactions and tasks to specific events for holistic visibility.
- **Email Invitation System:** Invite team members via email with role-specific permissions using a secure, time-limited token-based system.
- **AI Business Assistant:** A GPT-4 and Gemini-powered AI assistant that can answer natural language queries about the organization's finances, tasks, and event performance using a Retrieval-Augmented Generation (RAG) architecture.
- **File Management:** Secure upload and retrieval of documents related to events, contracts, and invoices.
- **Meetings Module:** Schedule and track meetings related to events and projects.

---

## 2. BACKGROUND STUDY / COURSEWORK DONE SO FAR

### 2.1 Literature Review & Competitive Analysis

Before beginning development, a review of existing event management and project management tools was conducted:

| Tool | Strength | Gap for SMEs |
|---|---|---|
| **Eventbrite** | Ticketing and attendee management | No internal team/task management |
| **Asana / Trello** | Task management | No financial module or event context |
| **QuickBooks / Zoho Books** | Financial accounting | No event/task integration |
| **Monday.com** | Project management | Expensive for SMEs, no financial module |
| **Notion** | Flexible workspace | No structured financial or event workflows |

None of the reviewed tools provide a unified event + task + financial platform affordable and simple enough for SME use. This gap validates the need for EM SME System.

### 2.2 Technologies Studied

As part of preparation for this project, the following technologies, frameworks, and concepts were studied:

**Backend Development:**
- **FastAPI (Python):** Modern, async web framework for building REST APIs. FastAPI uses Python type hints for automatic request validation via Pydantic and generates OpenAPI documentation automatically.
- **SQLAlchemy 2.0 (Async):** Python ORM with full asynchronous support using `asyncpg` driver for PostgreSQL.
- **Alembic:** Database migration tool for SQLAlchemy, enabling version-controlled schema changes.
- **JWT (JSON Web Tokens):** Stateless authentication mechanism using access tokens (short-lived) and refresh tokens (long-lived) for secure API access.
- **Passlib / bcrypt:** Industry-standard password hashing library. bcrypt is specifically chosen for its resistance to brute-force attacks via its adjustable cost factor.
- **Poetry:** Python dependency management and packaging tool, used for reproducible builds.

**Frontend Development:**
- **React 18 with TypeScript:** Component-based UI framework with strong typing for maintainability and early error detection.
- **Axios:** Promise-based HTTP client for structured API communication, with interceptors for token management.
- **React Hook Form:** Performant form management with built-in validation.

**AI & Machine Learning:**
- **LangChain & LangGraph:** Framework for building LLM-powered applications. LangGraph specifically enables building stateful, multi-step AI agent workflows using directed graphs.
- **Retrieval-Augmented Generation (RAG):** Architecture combining semantic search (via vector databases) with LLM generation for factual, context-aware responses.
- **Qdrant:** Open-source vector database for storing and querying high-dimensional embeddings.
- **OpenAI GPT-4 / Google Gemini:** Large language models used as the reasoning engine for the AI assistant.

**DevOps & Cloud:**
- **Docker:** Containerization platform enabling consistent runtime environments across development and production.
- **Render:** Platform-as-a-Service (PaaS) for deploying Docker-based backend applications.
- **Vercel:** CDN-based deployment platform optimized for React SPA (Single Page Applications).
- **PostgreSQL:** Open-source relational database with strong ACID compliance, chosen for its robust support for JSON, arrays, and UUIDs.

**Security Concepts:**
- CORS (Cross-Origin Resource Sharing) configuration
- Rate limiting using SlowAPI to prevent API abuse
- TrustedHostMiddleware for preventing host header attacks
- HTTP security headers (HSTS, X-Frame-Options, X-Content-Type-Options)

---

## 3. TENTATIVE WORK PLAN

### Phase 1 — Planning & Setup (Week 1–2) ✅ Completed
- Requirements gathering and feature prioritization
- Database schema design (ERD)
- Technology stack selection and environment setup
- Repository initialization, Docker configuration, CI/CD pipeline setup

### Phase 2 — Core Backend Development (Week 3–5) ✅ Completed
- Organization and User models with multi-tenant architecture
- JWT authentication system (register, login, refresh, logout)
- Role-based access control (RBAC) middleware
- Database migrations via Alembic
- Task management API (CRUD + assignments + comments)

### Phase 3 — Financial Module (Week 6–7) ✅ Completed
- Bank account management API
- Bank statement parser (CSV/XLSX → Transaction records)
- Contractor management with payment terms and bank details
- Payment tracking with contractor linking
- Financial analytics and reconciliation endpoints

### Phase 4 — Team Collaboration Features (Week 8–9) ✅ Completed
- Email invitation system (Resend API integration)
- Accept invitation frontend flow
- Announcement module with tagging
- Meetings scheduling module
- File upload and management

### Phase 5 — AI Integration (Week 10–11) ✅ In Progress
- LangGraph AI agent setup
- Qdrant vector database integration
- Business Q&A endpoints
- Analytics dashboard data aggregation

### Phase 6 — Frontend Development (Week 8–12) ✅ In Progress
- React + TypeScript frontend scaffolding
- All page components: Login, Register, Dashboard, Tasks, Finance, Team, Events, AI, Files, Meetings, Profile

### Phase 7 — Deployment & Testing (Week 12–13) ✅ Completed
- Docker containerization and Render deployment
- Vercel frontend deployment
- Environment variable configuration
- Production debugging (CORS, migrations, dependency issues)

### Phase 8 — Mobile App & Enhancements (Week 14–16) 🔜 Planned
- React Native mobile application setup
- Real-time notifications via WebSockets
- Calendar integrations (Google/Microsoft)
- PDF invoice generation

---

## 4. TOOLS AND TECHNOLOGY REQUIRED

### 4.1 Development Tools

| Category | Tool/Technology | Version |
|---|---|---|
| Backend Language | Python | 3.11 |
| Backend Framework | FastAPI | 0.109+ |
| Database ORM | SQLAlchemy (asyncio) | 2.0+ |
| Database | PostgreSQL | 15+ |
| DB Migrations | Alembic | 1.13+ |
| Authentication | python-jose, passlib (bcrypt) | latest |
| Email Service | Resend SDK | v2.x |
| AI Framework | LangChain + LangGraph | 0.3+, 0.2+ |
| LLM APIs | OpenAI GPT-4, Google Gemini | API-based |
| Vector Database | Qdrant | 1.7+ |
| Frontend Framework | React | 18+ |
| Frontend Language | TypeScript | 5.x |
| HTTP Client | Axios | latest |
| Package Manager (PY) | Poetry | 1.7+ |
| Package Manager (JS) | npm | 9+ |
| Containerization | Docker | latest |
| Code Editor | VS Code | latest |
| Version Control | Git + GitHub | latest |

### 4.2 Cloud & Infrastructure

| Service | Purpose | Cost |
|---|---|---|
| Vercel | Frontend hosting (CDN) | Free tier |
| Render | Backend Docker hosting | Free tier |
| Render PostgreSQL | Production database | Free tier (90 days) |
| Resend | Transactional email delivery | Free tier (100/day) |
| OpenAI API | GPT-4 for AI assistant | Pay-per-use |
| Google AI Studio | Gemini API | Free tier |
| Qdrant Cloud | Vector database | Free tier |
| GitHub | Source control + CI/CD | Free |

### 4.3 Hardware Requirements

- **Development Machine:** Any modern laptop/desktop with at least 8GB RAM, 20GB free disk space
- **Production:** Cloud-managed (no on-premise hardware required)
- **Internet:** Required for cloud service access

---

*Repository: https://github.com/IshitaAgarwal05/EM_SME_System*
