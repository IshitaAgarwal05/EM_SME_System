# INTERNSHIP PROJECT REPORT

## EM SME System: Event Management SaaS for Small and Medium Enterprises

---

**Submitted by:** Ishita Agarwal  
**Internship Organization:** [Organization Name]  
**Department:** [Department Name]  
**Academic Institution:** [Institution Name / University]  
**Degree Programme:** [B.Tech / MCA / etc.]  
**Academic Year:** 2025–2026  
**Internship Duration:** [Start Date] – [End Date]  
**Supervisor:** [Supervisor Name]  
**Date of Submission:** February 2026

---

---

# ABSTRACT

This report documents the design, development, and partial deployment of **EM SME System** — a cloud-based, multi-tenant Software as a Service (SaaS) platform targeting Small and Medium Enterprises (SMEs) that organize and manage events, projects, and collaborative work. SMEs typically manage critical workflows through disconnected tools such as spreadsheets, instant messaging applications, and email, which leads to poor accountability, financial leakage, and lack of data-driven decision-making.

EM SME System consolidates event lifecycle management, collaborative task tracking, financial reconciliation, team invitation and onboarding, file management, meeting scheduling, and AI-driven business intelligence into a unified, web-accessible platform. The backend is built using FastAPI (Python 3.11) with an asynchronous PostgreSQL database via SQLAlchemy 2.0, deployed on Render using Docker. The frontend is a React 18 + TypeScript Single Page Application (SPA) deployed on Vercel. The AI assistant module integrates OpenAI GPT-4 and Google Gemini APIs through LangChain and LangGraph, utilizing Qdrant as a vector database for contextual retrieval.

The project demonstrates real-world application of multi-tenant architecture design, REST API development, role-based access control, secure email invitation workflows, document parsing for financial data ingestion, and modern cloud deployment practices, making it a comprehensive demonstration of full-stack software engineering proficiency.

---

---

# LIST OF FIGURES

| Figure No. | Title |
|---|---|
| Figure 1 | Entity Relationship Diagram (ERD) |
| Figure 2 | System Use Case Diagram |
| Figure 3 | Class Diagram |
| Figure 4 | User Registration Sequence Diagram |
| Figure 5 | Team Invitation Sequence Diagram |
| Figure 6 | Bank Statement Upload Sequence Diagram |
| Figure 7 | Component Diagram |
| Figure 8 | Deployment Architecture Diagram |
| Figure 9 | Screenshot — Dashboard Page |
| Figure 10 | Screenshot — Finance Module |
| Figure 11 | Screenshot — Team Management (Invite Modal) |
| Figure 12 | Screenshot — Task Board |

> *All UML diagrams are available in `documentation/UML_Diagrams.md` in the project repository.*

---

---

# CHAPTER 2: INTRODUCTION

## 2.1 Background and Motivation

The global event management market was valued at approximately USD 23.7 billion in 2023 and is projected to reach USD 61.6 billion by 2032 [1]. Despite this scale, the majority of entities organizing events — particularly Small and Medium Enterprises — continue to rely on improvised, manual, and fragmented systems.

An SME organizing an annual corporate event, a sports tournament, or a community workshop typically faces the following operational challenges:

1. **Task Delegation Without Accountability:** Tasks are assigned verbally or via messaging apps. There is no system tracking whether they were completed, by whom, or when.

2. **Financial Opacity:** Budget tracking is done in Excel. Payments to vendors and contractors are tracked informally. Bank reconciliation — the process of matching bank statement entries to recorded payments — is done manually and prone to error.

3. **Team Onboarding Friction:** Adding new members to the team involves sharing login credentials, creating ad-hoc access, or giving individuals access to tools they should not have. There is no formal role-based access management.

4. **No Historical Intelligence:** Since data is scattered across tools, there is no ability to look back at a previous event and understand what worked, what cost more than budgeted, or which contractors performed reliably.

5. **Scaling Challenges:** As the organization grows, these informal systems break down. The gap between what SMEs need and what enterprise software provides is significant — enterprise tools like SAP or Oracle are expensive and complex.

EM SME System is designed to fill this gap: a purpose-built, affordable, intuitive SaaS platform that brings enterprise-grade features to SME event organizers.

## 2.2 Scope of the Project

The project scope for this internship encompasses:

- Design of a scalable multi-tenant database schema covering organizational, user, task, financial, and event data
- Implementation of a secure REST API backend using FastAPI (Python)
- Implementation of a responsive frontend using React and TypeScript
- Integration of an email delivery system for team invitations
- Integration of AI capabilities (LLM-based business Q&A)
- Cloud deployment of both frontend and backend
- Comprehensive documentation including UML diagrams and technical reports

**Out of Scope:**
- Real-time collaboration features (WebSockets — planned for next phase)
- Mobile (React Native) application (scaffolding exists; feature implementation planned)
- Payment gateway integration (planned for next phase)
- Advanced financial analytics with machine learning (planned)

## 2.3 Objectives

The primary objectives of this internship project are:

1. To design and implement a multi-tenant SaaS backend with role-based access control using FastAPI and PostgreSQL
2. To implement a complete user authentication system using JWT tokens with refresh token rotation
3. To create a team invitation system using email with time-limited, token-based invitations
4. To build a comprehensive financial module capable of parsing bank statements and tracking contractor payments
5. To integrate a generative AI business assistant using LangChain/LangGraph and vector databases
6. To deploy the application to cloud infrastructure (Vercel and Render) and resolve all production deployment issues
7. To create comprehensive technical documentation

---

---

# CHAPTER 3: TOOLS & TECHNOLOGY STACK USED

## 3.1 Backend Technologies

### 3.1.1 FastAPI
FastAPI is a modern, high-performance web framework for building APIs with Python 3.7+ [2]. It is built on Starlette (for web handling) and Pydantic (for data validation). FastAPI was chosen for this project due to:
- Native asynchronous (async/await) support enabling high concurrency
- Automatic OpenAPI (Swagger) documentation generation
- Strong type safety through Pydantic integration
- Excellent performance — benchmarks show it handles more requests per second than Flask or Django REST Framework [2]

### 3.1.2 SQLAlchemy 2.0 with asyncpg
SQLAlchemy is the most widely used Python ORM (Object-Relational Mapper) [3]. Version 2.0 introduced first-class async support. Combined with `asyncpg` (a high-performance PostgreSQL driver), the system achieves fully asynchronous database operations without blocking the event loop.

### 3.1.3 PostgreSQL 15
PostgreSQL is an open-source relational database with strong ACID (Atomicity, Consistency, Isolation, Durability) compliance [4]. It was chosen for:
- Native support for UUID, JSONB, and Array column types used extensively in this project
- Robust support for complex relational queries and foreign key constraints
- Excellent support in SQLAlchemy and asyncpg

### 3.1.4 Alembic
Alembic is a database migration tool for SQLAlchemy [5]. It provides version-controlled, incrementally-applied database schema changes, enabling safe schema evolution in production without data loss.

### 3.1.5 Authentication: JWT + bcrypt
JSON Web Tokens (JWT) are used for stateless authentication [6]. The system generates:
- **Access Tokens** (short-lived, 30 minutes) for API requests
- **Refresh Tokens** (long-lived, 7 days) for obtaining new access tokens without re-login

Passwords are hashed using **bcrypt** through the `passlib` library [7]. bcrypt applies a configurable work factor (cost) that makes brute-force attacks computationally expensive. The `python-jose` library handles JWT encoding and decoding.

### 3.1.6 Resend (Email API)
Resend is a transactional email API service [8]. The SDK v2.x is used to send team invitation emails. Resend was chosen over alternatives (SendGrid, Mailgun) for its clean Python SDK and reliable deliverability.

### 3.1.7 LangChain, LangGraph, and AI Integrations
- **LangChain** [9]: Framework for developing applications powered by language models, providing abstractions for chains, memory, and tools
- **LangGraph** [10]: Built on LangChain, LangGraph enables building stateful, multi-step AI agents as directed graphs — suitable for complex multi-turn business Q&A
- **Qdrant** [11]: A high-performance vector database for storing and querying embeddings, used for RAG (Retrieval-Augmented Generation) to give the AI context about organization-specific data
- **OpenAI GPT-4** [12]: Primary LLM for natural language understanding and generation
- **Google Gemini** [13]: Secondary LLM providing cost-effective, high-quality responses

### 3.1.8 SlowAPI (Rate Limiting)
SlowAPI [14] is a rate limiting library for FastAPI/Starlette based on limits. It is used to prevent API abuse by restricting the number of requests per IP address per time window.

### 3.1.9 Poetry
Poetry [15] is a Python dependency management and packaging tool that ensures reproducible builds through `poetry.lock` files, similar to `package-lock.json` in Node.js.

## 3.2 Frontend Technologies

### 3.2.1 React 18 with TypeScript
React [16] is a JavaScript library for building user interfaces using a component-based architecture. TypeScript [17] adds static typing to JavaScript, enabling early error detection and improved IDE support. This combination was chosen for:
- Component reusability and maintainability
- Type safety reducing runtime errors
- Large ecosystem of compatible libraries

### 3.2.2 Axios
Axios [18] is a promise-based HTTP client for JavaScript with built-in support for request/response interceptors. Interceptors are used to automatically attach JWT tokens to outgoing requests and handle 401 (Unauthorized) responses by refreshing the token.

### 3.2.3 React Hook Form
React Hook Form [19] is a performant, flexible form library for React. It minimizes re-renders and provides built-in validation, used for Login, Register, and Invite forms.

### 3.2.4 Vite
Vite [20] is a next-generation frontend build tool offering extremely fast hot module replacement (HMR) during development and optimized production builds.

## 3.3 Infrastructure & DevOps

### 3.3.1 Docker
Docker [21] enables packaging the application with all its dependencies into a portable container image. The backend Dockerfile uses a multi-stage build to minimize the final image size. The startup command runs database migrations automatically before starting the server.

### 3.3.2 Vercel
Vercel [22] is a cloud platform optimized for frontend frameworks. It provides automatic CI/CD — every push to the GitHub `main` branch triggers a new deployment. The React SPA is deployed at `em-sme-system.vercel.app`.

### 3.3.3 Render
Render [23] is a unified Cloud Platform supporting Docker-based web services. The FastAPI backend is deployed as a Docker web service at `em-sme-system-ws.onrender.com`. Render provides a managed PostgreSQL database and handles SSL/TLS termination.

---

---

# CHAPTER 3.1 (Chapter 4): ROLES AND RESPONSIBILITIES

## 4.1 OBJECTIVES

The internship project was undertaken with the following specific objectives:

1. **Design a Production-Grade Multi-Tenant Architecture:** Create a database schema and backend architecture that cleanly separates data between organizations (tenants) while enabling efficient querying within each tenant.

2. **Implement Secure Authentication with RBAC:** Build a JWT-based authentication system with refresh token rotation and implement Role-Based Access Control (RBAC) with four distinct roles: Owner, Manager, Employee, and Contractor.

3. **Build a Complete Financial Tracking Module:** Implement the ability to import bank statements (CSV/XLSX), categorize transactions, link them to events and contractors, and track contractor payments with full audit trails.

4. **Create an Email Invitation Workflow:** Design and implement a complete team onboarding system using secure, time-limited email invitations powered by the Resend API.

5. **Integrate AI for Business Intelligence:** Implement an AI assistant capable of answering natural language questions about the organization's events, tasks, and financial data using RAG architecture.

6. **Deploy to Production Cloud Infrastructure:** Successfully deploy and debug the entire application stack on Vercel (frontend) and Render (backend), addressing real-world deployment challenges.

7. **Write Comprehensive Documentation:** Produce UML diagrams, technical documentation, and this report documenting the work completed.

## 4.2 ROLES AND RESPONSIBILITIES

As the sole developer on this internship project, the following roles and responsibilities were undertaken:

### Role 1: Backend Architect & Developer
**Responsibilities:**
- Designed the entire multi-tenant database schema (14 tables across 5 domains)
- Implemented all FastAPI routers and service classes (~16 API route files)
- Built the authentication system (JWT, refresh tokens, bcrypt password hashing)
- Implemented RBAC middleware and permission checking utilities
- Created the financial module including bank statement parser and reconciliation logic
- Integrated LangChain/LangGraph for the AI assistant module
- Configured security middleware: CORS, TrustedHostMiddleware, rate limiting, security headers

### Role 2: Frontend Developer
**Responsibilities:**
- Scaffolded the React + TypeScript + Vite frontend application
- Built 12 page components: Login, Register, Dashboard, Tasks, Finance, Team, Meetings, AI, Files, Profile, Legal, AcceptInvite
- Implemented the Axios API client with JWT token management and interceptors
- Built the Team Invite modal and Accept Invitation page with token validation
- Resolved multiple TypeScript strict mode compilation errors for production build

### Role 3: DevOps Engineer
**Responsibilities:**
- Wrote the multi-stage Dockerfile for the FastAPI backend
- Configured GitHub as the source control and CI/CD trigger for both Vercel and Render
- Managed environment variable configuration across development and production
- Debugged 8+ production deployment issues including:
  - Missing `poetry.lock` file
  - `ModuleNotFoundError` for `slowapi`, `langchain_qdrant`, and `ToolNode`
  - "Invalid host header" error from TrustedHostMiddleware misconfiguration
  - PYTHONPATH not set for Alembic migrations in Docker
  - Missing `events` table in migration scripts
  - Missing `bcrypt` dependency causing 500 errors

### Role 4: Technical Documentation Author
**Responsibilities:**
- Created 8 UML diagrams (ERD, Use Case, Class, 3x Sequence, Component, Deployment)
- Wrote 15-slide presentation content guide with speaker notes
- Wrote project synopsis covering problem definition, work plan, and tech requirements
- Authored this 15-page internship project report

---

---

# CHAPTER 5: WORK DONE

## 5.1 INTERNSHIP WORK DONE SO FAR

### 5.1.1 Database Design

The first significant deliverable was the design of the multi-tenant relational database schema. The schema spans 14 tables organized into 5 functional domains:

**Domain 1: Identity & Access**
- `organizations` — The root tenant table; all data belongs to an organization
- `users` — Each user belongs to one organization and has one role
- `refresh_tokens` — Stores hashed refresh tokens for JWT rotation
- `invitations` — Manages pending team invitations (token, expiry, role)

**Domain 2: Task Management**
- `tasks` — Core task entity with hierarchy (parent-child subtasks), priority, status, assignments
- `task_assignments` — Many-to-many relationship between tasks and users
- `task_comments` — User comments on tasks

**Domain 3: Financial Management**
- `bank_accounts` — Bank accounts linked to organizations
- `transactions` — Individual financial transactions (imported from bank statements or created manually)
- `contractors` — Vendor/contractor profiles with banking details (IFSC, UPI ID, bank account number)
- `payments` — Payment records linked to contractors and transactions
- `task_payment_links` — Many-to-many link between tasks and payments

**Domain 4: Event Management**
- `events` — Events or projects with budget, status, and date range
- `categories` — Custom transaction categories (expense/income types)

All tables use UUID primary keys and include `organization_id` as a foreign key for strict tenant isolation.

### 5.1.2 Backend API Development

A total of 16 API router files were implemented:

| Router | Key Endpoints |
|---|---|
| `/auth` | Register, Login, Refresh, Logout, Reset Password |
| `/users` | Profile, List, Update, Delete User |
| `/tasks` | CRUD Tasks, Assign, Comment, Subtasks |
| `/financial` | Upload Statement, CRUD Transactions, Reconcile |
| `/contractors` | CRUD Contractors, Payments |
| `/events` | CRUD Events, Budget Tracking |
| `/categories` | CRUD Categories |
| `/invitations` | Send Invite, Accept, List, Revoke |
| `/analytics` | Dashboard metrics, Financial summaries |
| `/ai` | Ask Business Questions, Get Insights |
| `/files` | Upload, List, Download Files |
| `/meetings` | Schedule, List, Update Meetings |
| `/announcements` | Team Announcements with tagging |
| `/reminders` | Task Reminders |
| `/health` | System health check |

### 5.1.3 Authentication System

A complete JWT authentication system was implemented:
- **Registration:** Creates organization and owner user atomically in a single database transaction; passwords hashed with bcrypt (cost factor 12)
- **Login:** Validates credentials, returns access token (30 min TTL) + refresh token (7 days TTL)
- **Token Refresh:** Validates refresh token, rotates it, returns new access token
- **Logout:** Revokes refresh token in database
- **Middleware:** `get_current_user` FastAPI dependency extracts and validates JWT from `Authorization: Bearer <token>` header on protected routes

### 5.1.4 Email Invitation System

A complete team onboarding flow was implemented:
1. Manager/Owner submits invite (email, role) via REST API
2. Backend generates a 48-character URL-safe random token using Python's `secrets.token_urlsafe(48)` [24]
3. Token is stored in the `invitations` table with a 7-day expiry and `status=pending`
4. Resend SDK sends a branded HTML email with the invite link
5. On the frontend, the Accept Invitation page reads the token from URL parameters, validates with the API, and presents a sign-up form
6. On acceptance, a new user account is created, linked to the organization, and the invitation is marked `accepted`

### 5.1.5 Financial Statement Parser

The financial module's most complex feature is the bank statement parser. It:
- Accepts CSV or XLSX files via multipart/form-data upload
- Uses `pandas` to read and normalize the file
- Attempts to detect common column name patterns (date, description, amount, credit, debit)
- Normalizes amounts to credit (positive) and debit (negative) conventions
- Bulk-inserts Transaction records into PostgreSQL with the source set to `csv_import` or `xlsx_import`
- Returns a summary of rows parsed, imported, and any parsing errors

### 5.1.6 AI Business Assistant

The AI module implements a LangGraph-based agent:
- The agent receives a natural language question from the user (e.g., "What was our total expense on events last month?")
- It uses LangChain tools to query financial data from PostgreSQL
- Qdrant is used to retrieve relevant historical context (via embeddings)
- The LLM (GPT-4 or Gemini) synthesizes a natural language response with actual figures
- The endpoint is protected and scoped to the authenticated user's organization

### 5.1.7 Frontend Application

The React frontend consists of 12 pages:

| Page | Key Features |
|---|---|
| Login | Email/password with show/hide toggle |
| Register | Organization creation + first user sign-up |
| Dashboard | Summary cards: tasks, events, finances, team size |
| Tasks | Task board with status columns, assign/comment/subtask |
| Finance | Statement upload, transaction list/filter, payment tracking |
| Team | Member directory, invite modal, role management |
| Meetings | Meeting scheduler and calendar view |
| AI | Chat interface with the business assistant |
| Files | Document upload and file browser |
| Profile | User profile edit and preferences |
| Legal | Terms, Privacy Policy |
| AcceptInvite | Token-based invitation acceptance form |

### 5.1.8 Production Deployment & Debugging

The deployment phase involved significant debugging work. Key issues resolved:

| Issue | Root Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: slowapi` | Dependency missing from `pyproject.toml` | Added `slowapi = "^0.1.9"` |
| `ImportError: ToolNode` | LangGraph version incompatibility | Updated all LangChain packages to compatible versions |
| "Invalid host header" 400 error | `TrustedHostMiddleware` with hardcoded hosts | Made `allowed_hosts` configurable via environment variable |
| CORS 500 error on login | Registration 500 caused by bcrypt | Temporary debug: allowed all CORS origins |
| `ModuleNotFoundError: No module named 'app'` | `PYTHONPATH` not set in Docker for Alembic | Added `ENV PYTHONPATH=/app` to Dockerfile |
| `UndefinedTableError: relation "events"` | Migration script didn't include `create_table` | Rewrote the migration file to create both `events` and `categories` tables |
| `ValueError: password > 72 bytes` | `passlib` bcrypt fallback (native `bcrypt` missing) | Added `bcrypt = "^4.0.1"` to `pyproject.toml` |

---

## 5.2 WEEK-WISE LOG

| Week | Dates (Approx.) | Work Done |
|---|---|---|
| Week 1 | Jan 10 | Project scope definition, technology research, repo initialization, Docker setup |
| Week 2 | Jan 11–12 | Database schema design (ERD), SQLAlchemy model implementation, Alembic migration setup |
| Week 3 | Jan 12–13 | Authentication API (register, login, refresh, logout), JWT middleware, bcrypt hashing |
| Week 4 | Jan 13–14 | RBAC implementation, Task API (CRUD, assignments, comments, subtasks) |
| Week 5 | Jan 14 | Financial module: BankAccount API, Transaction API, bank statement CSV parser |
| Week 6 | Jan 14–15 | Contractor management API, Payment tracking API, Task-Payment linking |
| Week 7 | Jan 15 | Email invitation system (Resend integration, backend + frontend accept flow) |
| Week 8 | Jan 15 | AI module: LangChain + LangGraph agent setup, Qdrant integration |
| Week 9 | Jan 15 | Analytics API, Events API, Meetings API, Announcements API |
| Week 10 | Jan 15 | Frontend: React/TypeScript scaffolding, Login/Register pages, Axios API client |
| Week 11 | Week of Jan 16 | Frontend: Dashboard, Tasks, Finance, Team pages |
| Week 12 | Week of Jan 19 | Frontend: AcceptInvite, AI, Files, Meetings, Profile, Legal pages |
| Week 13 | Week of Jan 20 | Vercel deployment, TypeScript build error fixes, `.gitignore` management |
| Week 14 | Week of Jan 25 | Render deployment, dependency debugging, migration issues, CORS debugging |
| Week 15–16 | Jan–Feb | Production debugging continued, bcrypt fix, documentation writing |

---

---

# CHAPTER 6: FUTURE PLAN

The following features and improvements are planned for the next development phase:

## 6.1 Mobile Application
A React Native mobile application is already scaffolded in the `mobile/` directory of the repository. Its implementation is planned for the next phase, providing managers and employees with on-the-go access to task updates, financial summaries, and team communications.

## 6.2 Real-Time Features (WebSockets)
A WebSocket layer using FastAPI's native WebSocket support will enable:
- Live task status updates without page refresh
- Real-time team announcements
- Live notification delivery for invitation acceptances and task assignments

## 6.3 Calendar Integrations
The Meetings module will be enhanced with two-way sync to:
- **Google Calendar API** — push meeting events to participants' Google Calendars
- **Microsoft Outlook Calendar API** — for enterprise clients using Microsoft 365

## 6.4 PDF Invoice Generation
When processing contractor payments, the system will generate professional PDF invoices and delivery receipts using a library such as `reportlab` or a third-party service like PDFMonkey.

## 6.5 Advanced Analytics with Machine Learning
Using the financial transaction history accumulated in PostgreSQL, ML models will be trained to:
- **Budget Forecasting:** Predict event expenditure based on historical patterns
- **Anomaly Detection:** Flag unusual transactions that deviate from expected patterns
- **Contractor Reliability Scoring:** Rate contractors based on payment history and task completion

## 6.6 Payment Gateway Integration
Integration with Razorpay or Stripe will enable:
- Direct payment initiation from within the platform
- Automatic reconciliation when a Razorpay payment is confirmed

## 6.7 Single Sign-On (SSO)
Adding OAuth2-based SSO using Google and Microsoft identity providers to allow users to sign in without creating separate passwords.

## 6.8 Performance Optimization
- Implement Redis caching for frequently accessed data (dashboard metrics, user sessions)
- Add pagination everywhere — currently some list endpoints lack proper cursor-based pagination
- Database query optimization using `EXPLAIN ANALYZE` profiling

---

---

# CHAPTER 7: CONCLUSION

This internship project has resulted in the design, development, and deployment of **EM SME System** — a full-featured, production-deployed, AI-enhanced SaaS platform addressing a genuine and underserved need in the SME event management sector.

The project provided hands-on exposure to the complete software development lifecycle:

1. **Architecture Design:** Designing a multi-tenant relational schema that scales cleanly with organizational growth required careful thought about data isolation, relationship cardinality, and performance indexing strategies.

2. **Backend Engineering:** Implementing a production-grade FastAPI application reinforced best practices in asynchronous programming, dependency injection, exception handling, and security (authentication, authorization, rate limiting, security headers).

3. **Frontend Engineering:** Building a TypeScript + React SPA with a structured Axios client and JWT-aware interceptors demonstrated careful state management and API integration patterns.

4. **Integration Challenges:** Integrating LangChain, Qdrant, and LLM APIs within a FastAPI application — while managing Python dependency conflicts — was a significant technical challenge that yielded important lessons in dependency management and version compatibility.

5. **Production Operations:** Debugging 8+ distinct deployment failures on Render (missing dependencies, wrong PYTHONPATH, incomplete migrations, bcrypt library absence) provided invaluable real-world DevOps experience that cannot be simulated in a classroom environment.

6. **Communication:** The process of documenting this project — writing UML diagrams, a synopsis, a presentation, and this report — reinforced the importance of clear technical communication in professional software development.

The system is live and publicly accessible at:
- **Frontend:** https://em-sme-system.vercel.app
- **Backend API:** https://em-sme-system-ws.onrender.com
- **API Documentation (Swagger):** https://em-sme-system-ws.onrender.com/docs

EM SME System is a solid foundation that is ready to be iterated upon. The planned future features — mobile app, WebSockets, calendar integrations, and predictive analytics — will further strengthen its value proposition and bring it closer to a commercially viable product.

---

---

# REFERENCES

[1] Grand View Research, "Event Management Software Market Size, Share & Trends Analysis Report by Solution," 2023. [Online]. Available: https://www.grandviewresearch.com/industry-analysis/event-management-software-market

[2] S. Ramírez, "FastAPI Documentation," Tiangolo. [Online]. Available: https://fastapi.tiangolo.com

[3] "SQLAlchemy 2.0 Documentation," SQLAlchemy Project. [Online]. Available: https://docs.sqlalchemy.org/en/20/

[4] "PostgreSQL 15 Documentation," PostgreSQL Global Development Group. [Online]. Available: https://www.postgresql.org/docs/15/

[5] M. Bayer, "Alembic Documentation," SQLAlchemy Project. [Online]. Available: https://alembic.sqlalchemy.org/en/latest/

[6] M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force (IETF), May 2015. [Online]. Available: https://www.rfc-editor.org/rfc/rfc7519

[7] "Passlib Documentation — bcrypt," Passlib Project. [Online]. Available: https://passlib.readthedocs.io/en/stable/lib/passlib.handlers.bcrypt.html

[8] "Resend Email API Documentation," Resend Inc. [Online]. Available: https://resend.com/docs

[9] H. Chase, "LangChain Documentation," LangChain AI. [Online]. Available: https://python.langchain.com/docs/

[10] LangChain AI, "LangGraph Documentation." [Online]. Available: https://langchain-ai.github.io/langgraph/

[11] "Qdrant Vector Database Documentation," Qdrant Solutions GmbH. [Online]. Available: https://qdrant.tech/documentation/

[12] OpenAI, "GPT-4 Technical Report," OpenAI, 2023. [Online]. Available: https://openai.com/research/gpt-4

[13] Google, "Gemini: A Family of Highly Capable Multimodal Models," Google DeepMind, 2023. [Online]. Available: https://deepmind.google/technologies/gemini/

[14] "SlowAPI: Rate limiting library for Starlette/FastAPI." [Online]. Available: https://github.com/laurents/slowapi

[15] "Poetry: Python dependency management and packaging made easy." [Online]. Available: https://python-poetry.org/docs/

[16] Meta Platforms, "React Documentation." [Online]. Available: https://react.dev

[17] Microsoft, "TypeScript Handbook." [Online]. Available: https://www.typescriptlang.org/docs/

[18] "Axios Documentation." [Online]. Available: https://axios-http.com/docs/intro

[19] "React Hook Form Documentation." [Online]. Available: https://react-hook-form.com

[20] E. You, "Vite Documentation." [Online]. Available: https://vitejs.dev/guide/

[21] Docker Inc., "Docker Documentation." [Online]. Available: https://docs.docker.com

[22] Vercel Inc., "Vercel Documentation." [Online]. Available: https://vercel.com/docs

[23] Render Services Inc., "Render Documentation." [Online]. Available: https://render.com/docs

[24] Python Software Foundation, "secrets — Generate secure random numbers for managing secrets," Python 3.11 Documentation. [Online]. Available: https://docs.python.org/3/library/secrets.html

[25] O. Wahlberg, "Twelve-Factor App Methodology." [Online]. Available: https://12factor.net/

---

*Project Repository: https://github.com/IshitaAgarwal05/EM_SME_System*  
*Report prepared as part of internship at [Organization] — February 2026*
