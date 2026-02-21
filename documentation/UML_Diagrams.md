# UML Diagrams — EM SME System

> **Rendering:** Open in VS Code with the *Markdown Preview Mermaid Support* extension,  
> or paste any diagram block at [mermaid.live](https://mermaid.live).

---

## 1 · Entity Relationship Diagrams

> The full schema has 14 tables. To keep each diagram readable, the ERD is split into
> three domain groups. Only key columns are shown; timestamps (`created_at`, `updated_at`) are omitted for brevity.

---

### 1A · Identity & Access Domain

_Covers: Organisations, Users, Refresh Tokens, Invitations_

```mermaid
erDiagram
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
        string position
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
    USERS         ||--o{ INVITATIONS  : "creates"
```

---

### 1B · Task & Event Domain

_Covers: Tasks, Task Assignments, Task Comments, Events, Categories_

```mermaid
erDiagram
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
        decimal actual_hours
    }

    TASK_ASSIGNMENTS {
        uuid     id          PK
        uuid     task_id     FK
        uuid     user_id     FK
        uuid     assigned_by FK
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
        string color
        bool   is_default
    }

    TASKS          ||--o{ TASK_ASSIGNMENTS : "assigned via"
    TASKS          ||--o{ TASK_COMMENTS   : "has"
    TASKS          ||--o{ TASKS           : "has subtasks"
    EVENTS         ||--o{ TASKS           : "groups (via metadata)"
```

---

### 1C · Financial Domain

_Covers: Bank Accounts, Transactions, Contractors, Payments, Task-Payment Links_

```mermaid
erDiagram
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
        string  counterparty
        bool    is_reconciled
    }

    CONTRACTORS {
        uuid    id              PK
        uuid    organization_id FK
        string  name
        string  email
        string  service_type
        string  upi_id
        string  ifsc_code
        decimal default_rate
        bool    is_active
    }

    PAYMENTS {
        uuid    id             PK
        uuid    organization_id FK
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

    BANK_ACCOUNTS      ||--o{ TRANSACTIONS      : "records"
    EVENTS             ||--o{ TRANSACTIONS      : "groups"
    CONTRACTORS        ||--o{ PAYMENTS          : "receives"
    PAYMENTS           ||--o{ TASK_PAYMENT_LINKS : "linked via"
    TASKS              ||--o{ TASK_PAYMENT_LINKS : "linked via"
```

---

## 2 · Use Case Diagram

> Shows which **actor** can perform which **actions** in the system.

```mermaid
graph LR
    %% ── Actors ──────────────────────────────────────────
    OW(["👤 Owner"])
    MG(["👤 Manager"])
    EM(["👤 Employee"])
    CO(["👤 Contractor"])
    SY(["⚙️ System"])

    %% ── Use Cases ───────────────────────────────────────
    subgraph Auth ["🔐 Authentication"]
        direction TB
        A1["Register & Create Org"]
        A2["Login / Logout"]
        A3["Refresh Token"]
        A4["Reset Password"]
    end

    subgraph Team ["👥 Team Management"]
        direction TB
        T1["Invite Member (email)"]
        T2["Accept Invitation"]
        T3["View Team Directory"]
        T4["Assign / Change Role"]
    end

    subgraph Tasks ["✅ Task Management"]
        direction TB
        K1["Create / Edit Task"]
        K2["Assign Task to User"]
        K3["Update Task Status"]
        K4["Add Comment / Subtask"]
    end

    subgraph Finance ["💰 Financial Management"]
        direction TB
        F1["Upload Bank Statement"]
        F2["View & Filter Transactions"]
        F3["Reconcile Transaction"]
        F4["Manage Contractors"]
        F5["Create / Track Payment"]
    end

    subgraph Events ["📅 Event Management"]
        direction TB
        E1["Create Event / Project"]
        E2["Link Transactions to Event"]
        E3["Track Event Budget"]
    end

    subgraph AI ["🤖 AI & Analytics"]
        direction TB
        I1["Ask AI Business Assistant"]
        I2["View Analytics Dashboard"]
    end

    subgraph Files ["📁 File & Meetings"]
        direction TB
        L1["Upload / View Files"]
        L2["Schedule Meeting"]
    end

    %% ── Owner connections ────────────────────────────────
    OW --> A1 & A2 & T1 & T4
    OW --> F1 & F3 & F4 & F5
    OW --> E1 & E2 & E3
    OW --> I1 & I2

    %% ── Manager connections ──────────────────────────────
    MG --> A2 & T1 & K1 & K2
    MG --> F1 & F4 & F5
    MG --> E1 & I2 & L2

    %% ── Employee connections ─────────────────────────────
    EM --> A2 & A4 & T2 & T3
    EM --> K3 & K4 & L1 & L2

    %% ── Contractor connections ───────────────────────────
    CO --> A2 & T2 & K3

    %% ── System connections ───────────────────────────────
    SY --> A3 & I2
```

---

## 3 · Class Diagram

> Shows **key attributes and relationships** between the main domain classes.  
> Methods shown are the most behaviourally important ones only.

```mermaid
classDiagram
    direction TB

    class Organization {
        +UUID  id
        +str   name
        +str   slug
        +str   subscription_tier
        +dict  settings
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
        +str      token
        +datetime expires_at
        +str      status
        +is_valid() bool
        +generate_token()$ str
    }

    class Task {
        +UUID  id
        +str   title
        +str   status
        +str   priority
        +date  due_date
        +is_overdue() bool
    }

    class TaskAssignment {
        +UUID     task_id
        +UUID     user_id
        +UUID     assigned_by
        +datetime assigned_at
    }

    class Transaction {
        +UUID    id
        +date    transaction_date
        +Decimal amount
        +str     transaction_type
        +str     category
        +bool    is_reconciled
    }

    class BankAccount {
        +UUID id
        +str  account_name
        +str  bank_name
        +str  currency
    }

    class Contractor {
        +UUID id
        +str  name
        +str  service_type
        +str  upi_id
        +str  ifsc_code
        +bool is_active
    }

    class Payment {
        +UUID    id
        +Decimal amount
        +str     status
        +date    due_date
        +str     payment_type
    }

    class Event {
        +UUID    id
        +str     name
        +str     event_type
        +Decimal budget
        +str     status
    }

    Organization "1" --> "*" User         : contains
    Organization "1" --> "*" Invitation   : manages
    Organization "1" --> "*" Task         : owns
    Organization "1" --> "*" BankAccount  : has
    Organization "1" --> "*" Contractor   : employs
    Organization "1" --> "*" Event        : organises

    User          "1" --> "*" Task              : creates
    Task          "1" --> "*" TaskAssignment    : has
    Task          "*" --> "*" Payment           : linked via TaskPaymentLink
    Task          "0..1" --> "*" Task           : parent of

    BankAccount   "1" --> "*" Transaction  : records
    Contractor    "1" --> "*" Payment      : receives
    Event         "1" --> "*" Transaction  : groups
```

---

## 4 · Sequence Diagrams

---

### 4A · User Registration

```mermaid
sequenceDiagram
    autonumber
    actor U as Client (Browser)
    participant API as FastAPI Backend
    participant DB  as PostgreSQL
    participant EM  as Resend (Email)

    U   ->> API : POST /auth/register<br/>{email, password, full_name, org_name}
    API ->> API : Validate input (Pydantic)
    API ->> DB  : Check — email already exists?
    DB  -->> API: Not found ✓

    API ->> DB  : INSERT organizations
    DB  -->> API: organization_id

    API ->> API : hash_password (bcrypt, cost=12)
    API ->> DB  : INSERT users (role = owner)
    DB  -->> API: user_id

    API ->> DB  : INSERT refresh_token
    API ->> EM  : Send welcome email (optional)
    EM  -->> U  : Welcome email

    API -->> U  : 201 {access_token, refresh_token, user}
```

---

### 4B · Team Invitation Flow

```mermaid
sequenceDiagram
    autonumber
    actor OW  as Owner / Manager
    participant API  as FastAPI Backend
    participant DB   as PostgreSQL
    participant MAIL as Resend (Email)
    actor INV as Invitee

    OW   ->> API  : POST /invitations {email, role}
    API  ->> DB   : Check — pending invite exists?
    DB   -->> API : None found ✓
    API  ->> DB   : INSERT invitations (token, expires_in=7d)
    API  ->> MAIL : Send invite link (token in URL)
    MAIL -->> INV : "You've been invited" email

    INV  ->> API  : GET /invitations/validate?token=…
    API  ->> DB   : Fetch invitation
    DB   -->> API : Valid & not expired ✓
    API  -->> INV : {org_name, role, email}

    INV  ->> API  : POST /invitations/accept {token, full_name, password}
    API  ->> DB   : INSERT users (linked to org, role from invite)
    API  ->> DB   : UPDATE invitations SET status=accepted
    API  -->> INV : 201 {access_token, user}
```

---

### 4C · Bank Statement Upload

```mermaid
sequenceDiagram
    autonumber
    actor  U      as Manager / Owner
    participant API    as FastAPI Backend
    participant PARSER as CSV / XLSX Parser
    participant DB     as PostgreSQL

    U      ->> API    : POST /financial/upload (multipart CSV or XLSX)
    API    ->> API    : Validate file type & size
    API    ->> PARSER : parse_bank_statement(file_bytes)
    PARSER -->> API   : List[{date, description, amount, type}]

    loop  For each row
        API ->> DB : INSERT transactions
    end

    DB  -->> API : transaction_ids
    API -->> U   : 200 {imported: N, skipped: K, rows: […]}
```

---

## 5 · Component Diagram

> High-level view of how frontend, backend, and external services connect.

```mermaid
graph TB
    subgraph FE ["🖥️  Frontend — React + TypeScript  (Vercel)"]
        direction LR
        P1["Login / Register"]
        P2["Dashboard"]
        P3["Tasks Board"]
        P4["Finance Module"]
        P5["Team & Invites"]
        P6["Events"]
        P7["AI Assistant"]
        P8["Files / Meetings"]
        AX["Axios API Client"]
    end

    subgraph BE ["⚙️  Backend — FastAPI (Docker · Render)"]
        direction TB
        R1["/auth"]
        R2["/users"]
        R3["/tasks"]
        R4["/financial"]
        R5["/invitations"]
        R6["/events"]
        R7["/ai"]
        R8["/analytics"]
        SVC["Services Layer"]
        AI["LangGraph AI Agent"]
    end

    subgraph INFRA ["☁️  Infrastructure"]
        PG[("PostgreSQL")]
        RD[("Redis")]
        QD[("Qdrant\nVector DB")]
        RS["Resend\nEmail API"]
        LLM["OpenAI / Gemini\nLLM APIs"]
    end

    AX  <-->|"HTTPS REST"| R1
    AX  <-->|"HTTPS REST"| R2
    AX  <-->|"HTTPS REST"| R3
    AX  <-->|"HTTPS REST"| R4
    AX  <-->|"HTTPS REST"| R5
    AX  <-->|"HTTPS REST"| R6
    AX  <-->|"HTTPS REST"| R7
    AX  <-->|"HTTPS REST"| R8

    R1 & R2 & R3 & R4 & R5 & R6 --> SVC
    R7 --> AI
    SVC --> PG
    SVC --> RD
    SVC --> RS
    AI  --> QD
    AI  --> LLM
```

---

## 6 · Deployment Diagram

> Shows where each part of the system runs in production.

```mermaid
graph TD
    USER["🌐 End User\n(Browser)"]

    subgraph Vercel ["☁️ Vercel — Frontend CDN"]
        FE["React SPA\nem-sme-system.vercel.app"]
    end

    subgraph Render ["☁️ Render — Backend PaaS"]
        BE["FastAPI\nDocker Container\nem-sme-system-ws.onrender.com"]
        PG[("PostgreSQL\nManaged DB")]
    end

    subgraph External ["🌐 External APIs"]
        direction LR
        RESEND["Resend\n(Email)"]
        OPENAI["OpenAI\n(GPT-4)"]
        GEMINI["Google Gemini"]
        QDRANT["Qdrant Cloud\n(Vector DB)"]
    end

    USER  -->|"HTTPS"| FE
    FE    -->|"REST API"| BE
    BE    -->|"SQL"| PG
    BE    -->|"HTTPS"| RESEND
    BE    -->|"HTTPS"| OPENAI
    BE    -->|"HTTPS"| GEMINI
    BE    -->|"HTTPS"| QDRANT
```

---

## 7 · Context Diagram (Level-0 DFD)

> Shows the **entire system as a single process** ("black box") and all external entities
> that interact with it — the highest-level view of the system boundary.

```mermaid
graph TD
    %% ── External Entities ────────────────────────────────────
    OWNER(["👤 Owner / Admin"])
    MANAGER(["👤 Manager"])
    EMPLOYEE(["👤 Employee"])
    CONTRACTOR_EXT(["👤 Contractor"])
    EMAIL_SVC(["📧 Resend\nEmail Service"])
    LLM_SVC(["🤖 OpenAI / Gemini\nLLM APIs"])
    BANK(["🏦 Bank Statement\nCSV / XLSX File"])

    %% ── System boundary ──────────────────────────────────────
    SYS[["⬛  EM SME SYSTEM\n\nEvent Management SaaS\nfor Small & Medium Enterprises"]]

    %% ── Flows INTO the system ────────────────────────────────
    OWNER      -->|"Register org, manage settings,\nupload statements, view reports"| SYS
    MANAGER    -->|"Invite members, assign tasks,\nmanage contractors & payments"| SYS
    EMPLOYEE   -->|"Accept invite, update tasks,\nupload files, join meetings"| SYS
    CONTRACTOR_EXT -->|"Accept invite, view\nassigned tasks"| SYS
    BANK       -->|"Bank statement file\nCSV / XLSX"| SYS

    %% ── Flows OUT of the system ──────────────────────────────
    SYS -->|"Invitation emails,\nwelcome emails"| EMAIL_SVC
    SYS -->|"Business Q&A prompts\n+ financial context"| LLM_SVC
    SYS -->|"Dashboard, reports,\ntask updates, alerts"| OWNER
    SYS -->|"Task boards, financial\nsummaries, team directory"| MANAGER
    SYS -->|"Task assignments,\nnotifications"| EMPLOYEE
    SYS -->|"AI-generated\nbusiness insights"| OWNER
    LLM_SVC -->|"Natural language\nanswers"| SYS
    EMAIL_SVC -->|"Delivery confirmation"| SYS
```

---

## 8 · Data Flow Diagram (Level-1)

> Expands the system black box into **six internal processes**, showing how data moves
> between actors, processes, and the five data stores.

```mermaid
graph TD
    %% ── External entities ────────────────────────────────────
    USER(["👤 User\nOwner / Manager / Employee"])
    BANK_FILE(["📄 Bank Statement\nCSV / XLSX"])
    EMAIL_SVC(["📧 Resend\nEmail Service"])
    LLM(["🤖 LLM APIs\nOpenAI / Gemini"])

    %% ── Level-1 Processes ────────────────────────────────────
    P1["1.0\n🔐 Authentication\n& User Management"]
    P2["2.0\n✅ Task\nManagement"]
    P3["3.0\n💰 Financial\nProcessing"]
    P4["4.0\n✉️ Invitation\n& Onboarding"]
    P5["5.0\n🤖 AI Business\nIntelligence"]
    P6["6.0\n📅 Event &\nCategory Mgmt"]

    %% ── Data Stores ──────────────────────────────────────────
    DS1[("D1 · Users &\nOrganizations DB")]
    DS2[("D2 · Tasks &\nAssignments DB")]
    DS3[("D3 · Transactions,\nPayments & Contractors DB")]
    DS4[("D4 · Invitations DB")]
    DS5[("D5 · Events &\nCategories DB")]

    %% ── Flows ────────────────────────────────────────────────
    USER      -->|"Login / Registration data"| P1
    P1        -->|"JWT access + refresh tokens"| USER
    P1        <-->|"Read / Write user & org records"| DS1

    USER      -->|"Create / Update / Assign task"| P2
    P2        -->|"Task status, comments, board view"| USER
    P2        <-->|"Read / Write tasks & assignments"| DS2
    DS1       -->|"Resolve user & org context"| P2

    BANK_FILE -->|"Raw CSV / XLSX rows"| P3
    USER      -->|"Reconcile / pay contractor"| P3
    P3        -->|"Parsed transactions, reports"| USER
    P3        <-->|"Read / Write financial records"| DS3
    DS1       -->|"Org tenant scope"| P3

    USER      -->|"Send invite (email + role)"| P4
    P4        -->|"Invite confirmation & accept form"| USER
    P4        -->|"Invite email with token"| EMAIL_SVC
    EMAIL_SVC -->|"Delivery status"| P4
    P4        <-->|"Read / Write invitation records"| DS4
    P4        -->|"Create new user on accept"| DS1

    USER      -->|"Natural language business question"| P5
    P5        -->|"NL insights & analytics"| USER
    P5        -->|"Prompt + org context"| LLM
    LLM       -->|"Generated answer"| P5
    DS3       -->|"Financial data for context"| P5
    DS2       -->|"Task data for context"| P5

    USER      -->|"Create / edit event or category"| P6
    P6        -->|"Event list, budget tracking view"| USER
    P6        <-->|"Read / Write event & category records"| DS5
    DS3       -->|"Link transactions to events"| P6
```
