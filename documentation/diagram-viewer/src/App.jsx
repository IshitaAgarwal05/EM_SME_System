import React, { useState, useEffect, useRef } from 'react'
import mermaid from 'mermaid'
import Panzoom from '@panzoom/panzoom'

/* ══════════════════════════════════════════════════════════════
   DIAGRAM DATA
══════════════════════════════════════════════════════════════ */
const DIAGRAMS = [
    {
        id: 'context', label: 'Context Diagram', icon: '🌐',
        code: `graph TD
    OWNER(["👤 Owner / Admin"])
    MANAGER(["👤 Manager"])
    EMPLOYEE(["👤 Employee"])
    CONTRACTOR_EXT(["👤 Contractor"])
    EMAIL_SVC(["📧 Resend Email Service"])
    LLM_SVC(["🤖 OpenAI / Gemini LLMs"])
    BANK(["🏦 Bank Statement CSV/XLSX"])

    SYS[["⬛  EM SME SYSTEM\nEvent Management SaaS\nfor Small & Medium Enterprises"]]

    OWNER      -->|"Manage org, settings,\nstatements, reports"| SYS
    MANAGER    -->|"Invite members, assign tasks,\nmanage contractors"| SYS
    EMPLOYEE   -->|"Accept invite, update tasks,\nupload files"| SYS
    CONTRACTOR_EXT -->|"Accept invite, view tasks"| SYS
    BANK       -->|"Bank statement file"| SYS

    SYS -->|"Invite & welcome emails"| EMAIL_SVC
    SYS -->|"Business Q&A prompts"| LLM_SVC
    SYS -->|"Dashboard, reports, alerts"| OWNER
    SYS -->|"Task boards, financials"| MANAGER
    SYS -->|"Task assignments"| EMPLOYEE
    LLM_SVC -->|"NL answers"| SYS
    EMAIL_SVC -->|"Delivery status"| SYS`,
    },
    {
        id: 'dfd', label: 'Data Flow Diagram', icon: '🔄',
        code: `graph TD
    USER(["👤 User\nOwner / Manager / Employee"])
    BANK_FILE(["📄 Bank Statement CSV/XLSX"])
    EMAIL_SVC(["📧 Resend Email Service"])
    LLM(["🤖 LLM APIs OpenAI/Gemini"])

    P1["1.0 🔐 Auth\n& User Mgmt"]
    P2["2.0 ✅ Task\nManagement"]
    P3["3.0 💰 Financial\nProcessing"]
    P4["4.0 ✉️ Invitation\n& Onboarding"]
    P5["5.0 🤖 AI Business\nIntelligence"]
    P6["6.0 📅 Event\nMgmt"]

    DS1[("D1 · Users & Orgs")]
    DS2[("D2 · Tasks")]
    DS3[("D3 · Financials")]
    DS4[("D4 · Invitations")]
    DS5[("D5 · Events")]

    USER --> |"Credentials"| P1
    P1 --> |"JWT tokens"| USER
    P1 <--> DS1

    USER --> |"Create/Update task"| P2
    P2 --> |"Board view"| USER
    P2 <--> DS2
    DS1 --> |"Org context"| P2

    BANK_FILE --> |"CSV/XLSX rows"| P3
    USER --> |"Reconcile/Pay"| P3
    P3 --> |"Transactions & reports"| USER
    P3 <--> DS3

    USER --> |"Send invite"| P4
    P4 --> |"Accept form"| USER
    P4 --> |"Invite email"| EMAIL_SVC
    EMAIL_SVC --> |"Status"| P4
    P4 <--> DS4
    P4 --> |"Create user"| DS1

    USER --> |"Business question"| P5
    P5 --> |"Insights"| USER
    P5 --> |"Prompt + context"| LLM
    LLM --> |"Answer"| P5
    DS3 --> |"Financial context"| P5

    USER --> |"Create event"| P6
    P6 --> |"Budget view"| USER
    P6 <--> DS5`,
    },
    {
        id: 'erd-identity', label: 'ERD · Identity', icon: '🔐',
        code: `erDiagram
    ORGANIZATIONS {
        uuid   id              PK
        string name
        string slug
        string subscription_tier
        jsonb  settings
    }
    USERS {
        uuid   id              PK
        uuid   organization_id FK
        string email
        string full_name
        string role
        string branch
        bool   is_active
        bool   email_verified
    }
    REFRESH_TOKENS {
        uuid     id       PK
        uuid     user_id  FK
        string   token_hash
        datetime expires_at
        bool     revoked
    }
    INVITATIONS {
        uuid     id              PK
        uuid     organization_id FK
        uuid     invited_by_id   FK
        string   email
        string   role
        string   token
        datetime expires_at
        string   status
    }
    ORGANIZATIONS ||--o{ USERS        : "has members"
    ORGANIZATIONS ||--o{ INVITATIONS  : "sends"
    USERS         ||--o{ REFRESH_TOKENS : "holds"
    USERS         ||--o{ INVITATIONS  : "creates"`,
    },
    {
        id: 'erd-task', label: 'ERD · Tasks & Events', icon: '✅',
        code: `erDiagram
    TASKS {
        uuid    id              PK
        uuid    organization_id FK
        uuid    created_by      FK
        uuid    parent_task_id  FK
        string  title
        string  status
        string  priority
        date    due_date
        decimal estimated_hours
    }
    TASK_ASSIGNMENTS {
        uuid     id          PK
        uuid     task_id     FK
        uuid     user_id     FK
        datetime assigned_at
    }
    TASK_COMMENTS {
        uuid   id      PK
        uuid   task_id FK
        uuid   user_id FK
        text   comment
    }
    EVENTS {
        uuid    id              PK
        uuid    organization_id FK
        string  name
        string  event_type
        date    start_date
        date    end_date
        decimal budget
        string  status
    }
    CATEGORIES {
        uuid   id              PK
        uuid   organization_id FK
        string name
        string category_type
        bool   is_default
    }
    TASKS ||--o{ TASK_ASSIGNMENTS : "assigned via"
    TASKS ||--o{ TASK_COMMENTS   : "has"
    TASKS ||--o{ TASKS           : "has subtasks"`,
    },
    {
        id: 'erd-finance', label: 'ERD · Financial', icon: '💰',
        code: `erDiagram
    BANK_ACCOUNTS {
        uuid   id              PK
        uuid   organization_id FK
        string account_name
        string bank_name
        string account_type
        string currency
        bool   is_active
    }
    TRANSACTIONS {
        uuid    id              PK
        uuid    organization_id FK
        uuid    bank_account_id FK
        uuid    event_id        FK
        date    transaction_date
        decimal amount
        string  transaction_type
        string  category
        bool    is_reconciled
    }
    CONTRACTORS {
        uuid    id              PK
        uuid    organization_id FK
        string  name
        string  service_type
        string  upi_id
        decimal default_rate
        bool    is_active
    }
    PAYMENTS {
        uuid    id             PK
        uuid    contractor_id  FK
        uuid    transaction_id FK
        decimal amount
        string  payment_type
        string  status
        date    due_date
    }
    TASK_PAYMENT_LINKS {
        uuid    id              PK
        uuid    task_id         FK
        uuid    payment_id      FK
        decimal amount_allocated
    }
    BANK_ACCOUNTS  ||--o{ TRANSACTIONS      : "records"
    CONTRACTORS    ||--o{ PAYMENTS          : "receives"
    PAYMENTS       ||--o{ TASK_PAYMENT_LINKS : "linked via"`,
    },
    {
        id: 'usecase', label: 'Use Case', icon: '👤',
        code: `graph LR
    OW(["👤 Owner"])
    MG(["👤 Manager"])
    EM(["👤 Employee"])
    CO(["👤 Contractor"])
    SY(["⚙️ System"])

    subgraph Auth ["🔐 Authentication"]
        direction TB
        A1["Register & Create Org"]
        A2["Login / Logout"]
        A3["Refresh Token"]
        A4["Reset Password"]
    end
    subgraph Team ["👥 Team"]
        direction TB
        T1["Invite Member"]
        T2["Accept Invitation"]
        T3["Team Directory"]
        T4["Assign Role"]
    end
    subgraph Tasks ["✅ Tasks"]
        direction TB
        K1["Create / Edit Task"]
        K2["Assign Task"]
        K3["Update Status"]
        K4["Comment / Subtask"]
    end
    subgraph Finance ["💰 Finance"]
        direction TB
        F1["Upload Statement"]
        F2["View Transactions"]
        F3["Reconcile"]
        F4["Manage Contractors"]
        F5["Create Payment"]
    end
    subgraph AI ["🤖 AI"]
        direction TB
        I1["Ask AI Assistant"]
        I2["Analytics Dashboard"]
    end

    OW --> A1 & A2 & T1 & T4
    OW --> F1 & F3 & F4 & F5 & I1 & I2
    MG --> A2 & T1 & K1 & K2 & F1 & F4 & I2
    EM --> A2 & A4 & T2 & T3 & K3 & K4
    CO --> A2 & T2 & K3
    SY --> A3 & I2`,
    },
    {
        id: 'class', label: 'Class Diagram', icon: '📦',
        code: `classDiagram
    direction TB
    class Organization {
        +UUID  id
        +str   name
        +str   slug
        +str   subscription_tier
    }
    class User {
        +UUID  id
        +str   email
        +str   full_name
        +str   role
        +bool  is_active
        +verify_password(plain) bool
        +generate_access_token() str
    }
    class Invitation {
        +UUID     id
        +str      email
        +str      role
        +str      status
        +is_valid() bool
    }
    class Task {
        +UUID  id
        +str   title
        +str   status
        +str   priority
        +is_overdue() bool
    }
    class Transaction {
        +UUID    id
        +Decimal amount
        +str     transaction_type
        +bool    is_reconciled
    }
    class BankAccount {
        +UUID id
        +str  account_name
        +str  bank_name
    }
    class Contractor {
        +UUID id
        +str  name
        +bool is_active
    }
    class Payment {
        +UUID    id
        +Decimal amount
        +str     status
    }
    class Event {
        +UUID    id
        +str     name
        +Decimal budget
        +str     status
    }

    Organization "1" --> "*" User        : contains
    Organization "1" --> "*" Invitation  : manages
    Organization "1" --> "*" Task        : owns
    Organization "1" --> "*" BankAccount : has
    Organization "1" --> "*" Contractor  : employs
    Organization "1" --> "*" Event       : organises
    Task          "1" --> "*" Task       : parent of
    BankAccount   "1" --> "*" Transaction: records
    Contractor    "1" --> "*" Payment    : receives`,
    },
    {
        id: 'seq-register', label: 'Seq · Registration', icon: '📋',
        code: `sequenceDiagram
    autonumber
    actor U as Client Browser
    participant API as FastAPI Backend
    participant DB  as PostgreSQL
    participant EM  as Resend Email

    U   ->> API : POST /auth/register
    API ->> API : Validate input (Pydantic)
    API ->> DB  : Check — email exists?
    DB  -->> API: Not found ✓
    API ->> DB  : INSERT organizations
    DB  -->> API: organization_id
    API ->> API : hash_password (bcrypt)
    API ->> DB  : INSERT users (role=owner)
    DB  -->> API: user_id
    API ->> DB  : INSERT refresh_token
    API ->> EM  : Send welcome email
    EM  -->> U  : Welcome email
    API -->> U  : 201 access_token + user`,
    },
    {
        id: 'seq-invite', label: 'Seq · Invitation', icon: '✉️',
        code: `sequenceDiagram
    autonumber
    actor OW  as Owner / Manager
    participant API  as FastAPI Backend
    participant DB   as PostgreSQL
    participant MAIL as Resend Email
    actor INV as Invitee

    OW   ->> API  : POST /invitations
    API  ->> DB   : Check existing invite
    DB   -->> API : None found ✓
    API  ->> DB   : INSERT invitation (token, 7d)
    API  ->> MAIL : Send invite link
    MAIL -->> INV : Invitation email

    INV  ->> API  : GET /invitations/validate?token
    API  ->> DB   : Fetch invitation
    DB   -->> API : Valid & not expired ✓
    API  -->> INV : org_name, role, email

    INV  ->> API  : POST /invitations/accept
    API  ->> DB   : INSERT user (linked to org)
    API  ->> DB   : UPDATE invitation SET accepted
    API  -->> INV : 201 access_token + user`,
    },
    {
        id: 'component', label: 'Component', icon: '🏗️',
        code: `graph TB
    subgraph FE ["🖥️  Frontend — React + TypeScript  (Vercel)"]
        direction LR
        P1["Login/Register"] & P2["Dashboard"] & P3["Tasks"]
        P4["Finance"] & P5["Team"] & P6["Events"]
        P7["AI Assistant"] & P8["Files/Meetings"]
        AX["Axios API Client"]
    end
    subgraph BE ["⚙️  Backend — FastAPI  (Docker · Render)"]
        direction TB
        R1["/auth"] & R2["/users /tasks"]
        R3["/financial"] & R4["/invitations"]
        R5["/events /ai /analytics"]
        SVC["Services Layer"]
        AI["LangGraph AI Agent"]
    end
    subgraph INFRA ["☁️  Infrastructure"]
        PG[("PostgreSQL")]
        RD[("Redis")]
        QD[("Qdrant Vector DB")]
        RS["Resend Email API"]
        LLM["OpenAI / Gemini"]
    end

    AX <-->|"HTTPS REST"| R1 & R2 & R3 & R4 & R5
    R1 & R2 & R3 & R4 --> SVC
    R5 --> AI
    SVC --> PG & RD & RS
    AI  --> QD & LLM`,
    },
    {
        id: 'deployment', label: 'Deployment', icon: '🚀',
        code: `graph TD
    USER["🌐 End User Browser"]

    subgraph Vercel ["☁️ Vercel — Frontend CDN"]
        FE["React SPA\nem-sme-system.vercel.app"]
    end
    subgraph Render ["☁️ Render — Backend PaaS"]
        BE["FastAPI Docker Container"]
        PG[("PostgreSQL DB")]
    end
    subgraph External ["🌐 External APIs"]
        direction LR
        RESEND["Resend Email"]
        OPENAI["OpenAI GPT-4"]
        GEMINI["Google Gemini"]
        QDRANT["Qdrant Cloud"]
    end

    USER  -->|"HTTPS"| FE
    FE    -->|"REST API"| BE
    BE    -->|"SQL"| PG
    BE    -->|"HTTPS"| RESEND & OPENAI & GEMINI & QDRANT`,
    },
]

/* ══════════════════════════════════════════════════════════════
   STATIC PAGE DATA
══════════════════════════════════════════════════════════════ */
const FEATURES = [
    {
        icon: '🔐', title: 'Auth & Multi-Tenancy', desc: `JWT-based login with bcrypt hashing, refresh tokens, email verification, and complete organisation isolation so each SME's data stays separate.`
    },
    { icon: '✉️', title: 'Team Invitation System', desc: 'Owners/Managers send email invitations via Resend. Invitees accept via a secure token link and are auto-enrolled into the organisation with the assigned role.' },
    { icon: '✅', title: 'Task Management', desc: 'Full Kanban-style task board with priorities, due dates, subtasks, comments, assignees, and role-based access — tailored for event teams.' },
    { icon: '💰', title: 'Financial Management', desc: 'Upload bank statements (CSV/XLSX), auto-parse transactions, reconcile entries, manage contractors, create payments, and generate financial summaries.' },
    { icon: '📅', title: 'Event & Category Tracking', desc: 'Create named events/projects and link transactions and tasks to them. Track per-event budget, spending, and status at a glance.' },
    { icon: '🤖', title: 'AI Business Assistant', desc: 'LangGraph-powered agentic assistant (GPT-4 / Gemini) with RAG over your financial data. Ask business questions in natural language and get contextual insights.' },
    { icon: '📊', title: 'Analytics Dashboard', desc: 'Visual charts for income vs. expenses, task completion rates, contractor spend, event budgets, and team performance metrics.' },
    { icon: '📁', title: 'File Management', desc: 'Secure file upload, organisation-scoped storage, and file listing — supporting documents, receipts, and contracts.' },
    { icon: '🤝', title: 'Contractor Management', desc: 'Maintain contractor profiles with payment terms, UPI/IFSC details, service types, and contract timelines. Link payments to tasks.' },
    { icon: '🔒', title: 'Security & Rate Limiting', desc: 'Standard security headers, CORS policy, TrustedHostMiddleware, SlowAPI rate limiting, and bcrypt password hashing with configurable cost factor.' },
]

const TECH_STACK = [
    {
        category: 'Frontend', color: '#61dafb', items: [
            { name: 'React 18', role: 'UI framework with hooks', icon: '⚛️' },
            { name: 'TypeScript', role: 'Type-safe development', icon: '🔷' },
            { name: 'Vite', role: 'Fast dev server & bundler', icon: '⚡' },
            { name: 'Axios', role: 'HTTP client with interceptors', icon: '🔗' },
            { name: 'CSS Modules', role: 'Scoped component styling', icon: '🎨' },
            { name: 'Vercel', role: 'Hosting & edge CDN', icon: '▲' },
        ]
    },
    {
        category: 'Backend', color: '#009688', items: [
            { name: 'FastAPI', role: 'Async Python web framework', icon: '⚡' },
            { name: 'SQLAlchemy', role: 'ORM with async support', icon: '🔌' },
            { name: 'Alembic', role: 'DB migration management', icon: '🗂️' },
            { name: 'Pydantic v2', role: 'Request/response validation', icon: '✅' },
            { name: 'passlib + bcrypt', role: 'Secure password hashing', icon: '🔒' },
            { name: 'SlowAPI', role: 'Rate limiting middleware', icon: '🛡️' },
            { name: 'Poetry', role: 'Dependency management', icon: '📦' },
            { name: 'uvicorn', role: 'ASGI production server', icon: '🚀' },
        ]
    },
    {
        category: 'AI & ML', color: '#a855f7', items: [
            { name: 'LangGraph', role: 'Agentic multi-step reasoning', icon: '🧠' },
            { name: 'LangChain', role: 'LLM orchestration layer', icon: '🔗' },
            { name: 'OpenAI GPT-4', role: 'Primary LLM', icon: '🤖' },
            { name: 'Google Gemini', role: 'Secondary LLM', icon: '✨' },
            { name: 'Qdrant', role: 'Vector database for RAG', icon: '🗄️' },
        ]
    },
    {
        category: 'Infrastructure', color: '#f59e0b', items: [
            { name: 'Docker', role: 'Containerised deployment', icon: '🐳' },
            { name: 'Render', role: 'Backend PaaS hosting', icon: '☁️' },
            { name: 'PostgreSQL', role: 'Primary relational DB', icon: '🐘' },
            { name: 'Redis', role: 'Caching & session store', icon: '🔴' },
            { name: 'Resend', role: 'Transactional email API', icon: '📧' },
            { name: 'GitHub Actions', role: 'CI/CD automation', icon: '⚙️' },
        ]
    },
]

const FUTURE_SCOPE = [
    { icon: '📱', title: 'Mobile Application', priority: 'HIGH', desc: 'React Native cross-platform app (iOS & Android) with biometric login, push notifications for task deadlines, and offline-capable task viewing.' },
    { icon: '⚡', title: 'Real-Time Collaboration', priority: 'HIGH', desc: 'WebSocket-based live updates — task status changes, comments, and financial reconciliation reflect instantly across all connected team members.' },
    { icon: '📅', title: 'Calendar & Scheduling', priority: 'MEDIUM', desc: 'Integrated event calendar with drag-and-drop scheduling, Google Calendar sync, iCal export, and automated reminders.' },
    { icon: '🧠', title: 'ML-Powered Analytics', priority: 'HIGH', desc: 'Expense forecasting, anomaly detection in transactions, predictive task completion timelines, and automated spending-category classification.' },
    { icon: '💳', title: 'Payment Gateway', priority: 'MEDIUM', desc: 'Direct Razorpay/Stripe integration for initiating contractor payments from within the platform and reconciling them automatically.' },
    { icon: '🔑', title: 'SSO / OAuth2', priority: 'MEDIUM', desc: 'Single sign-on via Google Workspace, Microsoft Entra ID, and GitHub OAuth so enterprise teams can use existing credentials.' },
    { icon: '📄', title: 'Invoice Generation', priority: 'LOW', desc: 'Auto-generate PDF invoices for contractor payments, branded with organisation logo, and send via email directly from the platform.' },
    { icon: '🌐', title: 'Multi-Language Support', priority: 'LOW', desc: 'Internationalisation (i18n) with support for Indian regional languages, making the platform accessible to non-English-speaking SMEs.' },
    { icon: '🏢', title: 'White-Label SaaS', priority: 'LOW', desc: 'Reseller mode that lets agencies deploy custom-branded instances of the platform for their clients with configurable feature flags.' },
]

const PRIORITY_COLOR = { HIGH: '#22c55e', MEDIUM: '#f59e0b', LOW: '#64748b' }

/* ══════════════════════════════════════════════════════════════
   MERMAID INIT
══════════════════════════════════════════════════════════════ */
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    darkMode: true,
    themeVariables: {
        background: '#1e2631', mainBkg: '#1e2631', nodeBorder: '#30363d',
        clusterBkg: '#161b22', titleColor: '#e6edf3', edgeLabelBackground: '#161b22',
        primaryColor: '#1f6feb', primaryTextColor: '#e6edf3',
        primaryBorderColor: '#58a6ff', lineColor: '#58a6ff',
        secondaryColor: '#161b22', tertiaryColor: '#0d1117',
        fontFamily: 'Segoe UI, system-ui, sans-serif', fontSize: '14px',
    },
    er: { useMaxWidth: false },
    sequence: { useMaxWidth: false },
    flowchart: { useMaxWidth: false, htmlLabels: true },
})

/* ══════════════════════════════════════════════════════════════
   DIAGRAM PANE (pan / zoom)
══════════════════════════════════════════════════════════════ */
function DiagramPane({ diagram }) {
    const wrapRef = useRef(null)
    const pzRef = useRef(null)
    const [zoom, setZoom] = useState(1)
    const [svg, setSvg] = useState('')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        setLoading(true); setError(null); setSvg('')
        mermaid.render('diag-' + diagram.id + '-' + Date.now(), diagram.code)
            .then(({ svg }) => { setSvg(svg); setLoading(false) })
            .catch(err => { setError(String(err)); setLoading(false) })
    }, [diagram])

    useEffect(() => {
        if (!wrapRef.current || !svg) return
        if (pzRef.current) { pzRef.current.destroy(); pzRef.current = null }
        const el = wrapRef.current
        pzRef.current = Panzoom(el, { maxScale: 8, minScale: 0.2, step: 0.1, canvas: true })
        const parent = el.parentElement
        const onWheel = e => { e.preventDefault(); pzRef.current.zoomWithWheel(e); setZoom(+(pzRef.current.getScale().toFixed(2))) }
        parent.addEventListener('wheel', onWheel, { passive: false })
        el.addEventListener('panzoomchange', () => setZoom(+(pzRef.current.getScale().toFixed(2))))
        pzRef.current.reset(); setZoom(1)
        return () => { parent.removeEventListener('wheel', onWheel); pzRef.current?.destroy(); pzRef.current = null }
    }, [svg])

    const zoomIn = () => { pzRef.current?.zoomIn(); setZoom(+(pzRef.current.getScale().toFixed(2))) }
    const zoomOut = () => { pzRef.current?.zoomOut(); setZoom(+(pzRef.current.getScale().toFixed(2))) }
    const reset = () => { pzRef.current?.reset(); setZoom(1) }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
            <div className="controls">
                <span className="controls-label">ZOOM</span>
                <button className="btn" onClick={zoomOut}>− Out</button>
                <span className="zoom-display">{Math.round(zoom * 100)}%</span>
                <button className="btn" onClick={zoomIn}>+ In</button>
                <button className="btn" onClick={reset}>⟳ Reset</button>
                <div className="tip">
                    <span><kbd>Scroll</kbd> zoom</span>
                    <span><kbd>Drag</kbd> pan</span>
                </div>
            </div>
            <div className="canvas-wrap">
                <div className="canvas">
                    {loading && <div className="state-box"><div className="spinner" /><span>Rendering…</span></div>}
                    {error && <div className="state-box"><div className="error-box">⚠️ {error}</div></div>}
                    {svg && (
                        <div ref={wrapRef} className="diagram-box"
                            dangerouslySetInnerHTML={{ __html: svg }} />
                    )}
                </div>
            </div>
        </div>
    )
}

/* ══════════════════════════════════════════════════════════════
   DIAGRAMS SECTION  (sub-tabs)
══════════════════════════════════════════════════════════════ */
function DiagramsSection() {
    const [active, setActive] = useState(DIAGRAMS[0].id)
    const current = DIAGRAMS.find(d => d.id === active)
    return (
        <div className="diagrams-section">
            <div className="sub-tab-strip">
                {DIAGRAMS.map(d => (
                    <button key={d.id}
                        className={`sub-tab ${d.id === active ? 'active' : ''}`}
                        onClick={() => setActive(d.id)}>
                        <span>{d.icon}</span>{d.label}
                    </button>
                ))}
            </div>
            <DiagramPane key={active} diagram={current} />
        </div>
    )
}

/* ══════════════════════════════════════════════════════════════
   FEATURES PAGE
══════════════════════════════════════════════════════════════ */
function FeaturesPage() {
    return (
        <div className="content-page">
            <div className="page-header">
                <h2>✨ Software Features</h2>
                <p>EM SME System is a comprehensive event management platform built for small and medium enterprises.
                    Below are the core capabilities shipped in the current release.</p>
            </div>
            <div className="card-grid">
                {FEATURES.map(f => (
                    <div key={f.title} className="feature-card">
                        <div className="card-icon">{f.icon}</div>
                        <h3>{f.title}</h3>
                        <p>{f.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}

/* ══════════════════════════════════════════════════════════════
   TECH STACK PAGE
══════════════════════════════════════════════════════════════ */
function TechStackPage() {
    return (
        <div className="content-page">
            <div className="page-header">
                <h2>🛠️ Technology Stack</h2>
                <p>A modern, cloud-native stack chosen for developer productivity, scalability, and free-tier deployability.</p>
            </div>
            {TECH_STACK.map(group => (
                <div key={group.category} className="tech-group">
                    <h3 className="tech-group-title" style={{ color: group.color }}>
                        <span className="tech-group-pill" style={{ background: group.color + '22', borderColor: group.color }}>
                            {group.category}
                        </span>
                    </h3>
                    <div className="tech-grid">
                        {group.items.map(item => (
                            <div key={item.name} className="tech-card" style={{ '--accent': group.color }}>
                                <span className="tech-icon">{item.icon}</span>
                                <div>
                                    <div className="tech-name">{item.name}</div>
                                    <div className="tech-role">{item.role}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}

/* ══════════════════════════════════════════════════════════════
   FUTURE SCOPE PAGE
══════════════════════════════════════════════════════════════ */
function FutureScopePage() {
    return (
        <div className="content-page">
            <div className="page-header">
                <h2>🔭 Future Scope</h2>
                <p>Planned enhancements to evolve EM SME System into a full-featured enterprise platform.</p>
            </div>
            <div className="card-grid">
                {FUTURE_SCOPE.map(f => (
                    <div key={f.title} className="feature-card future-card">
                        <div className="card-icon">{f.icon}</div>
                        <div className="priority-badge" style={{ background: PRIORITY_COLOR[f.priority] + '22', color: PRIORITY_COLOR[f.priority], borderColor: PRIORITY_COLOR[f.priority] }}>
                            {f.priority}
                        </div>
                        <h3>{f.title}</h3>
                        <p>{f.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}

/* ══════════════════════════════════════════════════════════════
   TOP NAV TABS
══════════════════════════════════════════════════════════════ */
const TOP_TABS = [
    { id: 'features', label: 'Features', icon: '✨' },
    { id: 'techstack', label: 'Tech Stack', icon: '🛠️' },
    { id: 'diagrams', label: 'Diagrams', icon: '📊' },
    { id: 'future', label: 'Future Scope', icon: '🔭' },
]

/* ══════════════════════════════════════════════════════════════
   APP ROOT
══════════════════════════════════════════════════════════════ */
export default function App() {
    const [active, setActive] = useState('features')
    return (
        <div className="app">
            <header className="header">
                <span className="header-icon">📊</span>
                <div className="header-text">
                    <h1>EM SME System — Project Presentation</h1>
                    <p>Event Management SaaS for Small &amp; Medium Enterprises</p>
                </div>
                <span className="header-badge">INTERNSHIP PROJECT</span>
            </header>

            <nav className="top-nav">
                {TOP_TABS.map(t => (
                    <button key={t.id}
                        className={`top-tab ${t.id === active ? 'active' : ''}`}
                        onClick={() => setActive(t.id)}>
                        <span className="tab-icon">{t.icon}</span>
                        {t.label}
                    </button>
                ))}
            </nav>

            <div className="main-area">
                {active === 'features' && <FeaturesPage />}
                {active === 'techstack' && <TechStackPage />}
                {active === 'diagrams' && <DiagramsSection />}
                {active === 'future' && <FutureScopePage />}
            </div>
        </div>
    )
}
