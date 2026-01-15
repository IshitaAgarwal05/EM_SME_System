# API Keys & Services Required for Full System Functionality

## ✅ REQUIRED for Core Features (System works without these but with limited functionality)

### 1. Database (REQUIRED - System won't start without this)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/event_management
```
**Status**: ✅ Already configured
**Purpose**: Stores all application data
**Cost**: Free (local PostgreSQL)

### 2. Secret Key (REQUIRED)
```bash
SECRET_KEY=your-secret-key-min-32-characters-long-change-in-production
```
**Status**: ✅ Already configured
**Purpose**: JWT token signing, session encryption
**Cost**: Free (generate your own)

---

## 🤖 AI Features (Optional but recommended)
### 3. OpenAI API Key (For AI Assistant)
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```
**Status**: ❌ NOT SET
**Purpose**: Powers the AI chatbot, transaction categorization, insights
**How to get**: https://platform.openai.com/api-keys
**Cost**: ~$0.01-0.03 per 1K tokens (pay-as-you-go)
**Impact if missing**: AI assistant won't work, manual categorization only

---

## 📊 Optional Services (System works fine without these)

### 4. Redis (For caching and background jobs)
```bash
REDIS_URL=redis://localhost:6379/0
```
**Status**: ⚠️ Optional (defaults to localhost)
**Purpose**: Caching, session storage, Celery task queue
**Cost**: Free (local Redis) or $5-10/month (Redis Cloud)
**Impact if missing**: Slightly slower performance, no background tasks

### 5. Qdrant (Vector Database for AI)
```bash
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
```
**Status**: ⚠️ Optional (only needed if using AI)
**Purpose**: Semantic search for AI assistant context
**Setup**: `docker run -p 6333:6333 qdrant/qdrant`
**Cost**: Free (local) or $25/month (Qdrant Cloud)
**Impact if missing**: AI assistant won't have context from your data

### 6. SendGrid (For email notifications)
```bash
SENDGRID_API_KEY=SG.your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
```
**Status**: ❌ NOT SET
**Purpose**: Send email reminders, notifications
**How to get**: https://sendgrid.com/pricing/ (Free tier: 100 emails/day)
**Impact if missing**: No email notifications

### 7. Twilio (For SMS notifications)
```bash
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```
**Status**: ❌ NOT SET
**Purpose**: Send SMS reminders
**How to get**: https://www.twilio.com/try-twilio (Free trial)
**Impact if missing**: No SMS notifications

### 8. Google Cloud Storage (For file uploads)
```bash
GCP_PROJECT_ID=your-project-id
GCP_BUCKET_NAME=your-bucket-name
GCP_CREDENTIALS_PATH=/path/to/credentials.json
```
**Status**: ❌ NOT SET
**Purpose**: Store uploaded files (currently using local storage)
**Impact if missing**: Files stored locally (works fine for development)

### 9. Sentry (For error tracking)
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```
**Status**: ❌ NOT SET
**Purpose**: Monitor errors and performance
**How to get**: https://sentry.io (Free tier available)
**Impact if missing**: No centralized error tracking

---

## 📅 Calendar Integration (Optional)

### 10. Google Calendar
```bash
GOOGLE_CALENDAR_CREDENTIALS=your-oauth-credentials-json
```
**Status**: ❌ NOT SET
**Purpose**: Sync meetings with Google Calendar
**Impact if missing**: No calendar sync

### 11. Microsoft Calendar
```bash
MICROSOFT_CALENDAR_CLIENT_ID=your-client-id
MICROSOFT_CALENDAR_CLIENT_SECRET=your-client-secret
```
**Status**: ❌ NOT SET
**Purpose**: Sync meetings with Outlook Calendar
**Impact if missing**: No calendar sync

---

## 📝 Summary

### Currently Working Without:
- ✅ Core system (database, auth, CRUD operations)
- ✅ File uploads (local storage)
- ✅ Analytics and reporting
- ✅ Task management
- ✅ Meeting scheduling
- ✅ Team management

### NOT Working Without API Keys:
- ❌ AI Assistant (needs OpenAI + Qdrant)
- ❌ Email notifications (needs SendGrid)
- ❌ SMS notifications (needs Twilio)
- ❌ Calendar sync (needs Google/Microsoft)

### Recommended Setup for Full Experience:
1. **OpenAI API Key** ($10-20/month) - For AI features
2. **SendGrid** (Free tier) - For email notifications
3. **Qdrant** (Free via Docker) - For AI context

### Minimum Setup (What you have now):
- Database ✅
- Secret Key ✅
- Redis (optional, defaults work) ✅

**Your system is fully functional for event management, finance tracking, and team collaboration!**
The missing API keys only affect AI and notification features.
