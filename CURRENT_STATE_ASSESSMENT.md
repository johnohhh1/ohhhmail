# ChiliHead v2.0 - Current State Assessment
**Date:** 2025-11-25
**Assessment:** What we actually have right now

---

## Docker Services Status

### ✅ Healthy & Needed
| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| **chilihead-aubs** | ✅ Healthy | 5000:8000 | Main AUBS backend with SimpleOrchestrator + Chat |
| **chilihead-snappymail** | ✅ Healthy | 8888 | Email viewing (IMAP to Gmail) |
| **chilihead-postgres** | ✅ Healthy | 5432 | Database |
| **chilihead-redis** | ✅ Healthy | 6379 | Cache |
| **chilihead-nats** | ✅ Healthy | 4222, 8222 | Event streaming |
| **chilihead-ollama** | ✅ Healthy | 11434 | Local LLM inference |
| **open-webui** | ✅ Healthy | **3000:8080** | **Main UI (NOT in docker-compose!)** |

### ⚠️ Needs Fixing
| Service | Status | Issue |
|---------|--------|-------|
| **chilihead-openwebui-backend** | ⚠️ Healthy but NO PORT | Missing `ports: - "8080:8080"` in docker-compose |
| **chilihead-email-ingestion** | ❌ Unhealthy | Need to diagnose why |
| **chilihead-qdrant** | ❌ Unhealthy | Vector DB not starting properly |

### ❌ Should Be Deleted
| Service | Status | Why Delete |
|---------|--------|------------|
| **chilihead-uitars** | ❌ Restarting (failed) | We deleted UITARS code but container still running |
| **chilihead-dolphin-server** | ✅ Healthy (but unused) | We deleted Dolphin code but container still running |
| **chilihead-frontend** | ❌ Unhealthy | Old custom HTML frontend - we're using Open-WebUI now |

---

## AUBS Backend (Current Code)

### Files in `aubs/src/`:
```
aubs/src/
├── main.py                    # FastAPI app
├── simple_orchestrator.py     # SimpleOrchestrator (no Dolphin)
├── email_analyzer.py          # EmailAnalyzer (Claude/GPT-4 triage)
├── chat.py                    # AUBSChatService
└── config.py                  # Settings
```

### Current API Endpoints (from main.py):
1. **`GET /health`** ✅ Working
   - Returns: `{"status": "healthy", "nats_connected": true, "chat_service_active": true}`

2. **`GET /ready`** ❌ BROKEN
   - References `orchestrator.dolphin_healthy` which doesn't exist
   - Need to remove Dolphin check

3. **`POST /process-email`** ✅ Working
   - Accepts EmailData
   - Calls SimpleOrchestrator.process_email()
   - Returns execution_id

4. **`GET /executions/{execution_id}`** ✅ Working
   - Returns execution status and results

5. **Chat endpoints** (need to check chat.py)

---

## What's Missing for v2 Vision

### Phase 0: Foundation (Partially Complete)
- ✅ SnappyMail deployed and configured
- ✅ AUBS backend running with SimpleOrchestrator
- ⚠️ Open-WebUI running but NOT CONFIGURED as main interface
- ❌ No tools registered with Open-WebUI yet
- ❌ Can't call AUBS from Open-WebUI chat

### Phase 1: Email Tools (Not Started)
Need to implement as Open-WebUI tools:
- ❌ `get_emails(limit, filter)` - Direct IMAP to Gmail
- ❌ `triage_email(thread_id)` - AI analysis
- ❌ `get_email_context(thread_id)` - Full thread
- ❌ `mark_email_done(thread_id)` - Update state

### Phase 2: Task Tools (Not Started)
Need to implement:
- ❌ `get_tasks()` - Retrieve todo list
- ❌ `add_task()` - Create task
- ❌ `update_task()` - Modify task
- ❌ `delete_task()` - Remove task

### Phase 3: Calendar Tools (Not Started)
- ❌ Google Calendar API integration
- ❌ `get_calendar()`, `add_event()`, etc.

### Phase 4: Vision + SnappyMail (Not Started)
- ❌ Screenshot automation (Playwright)
- ❌ OCR via Vision models

### Phase 5: Memory/RAG (Not Started)
- ❌ Qdrant integration (currently unhealthy)
- ❌ Semantic search

---

## Critical Path to Get v2 Working

### Step 1: Clean Up Docker (1 hour)
**Actions:**
1. Stop and remove UITARS container
2. Stop and remove Dolphin container
3. Stop and remove old frontend container
4. Fix openwebui-backend port mapping OR use the external open-webui on port 3000
5. Fix email-ingestion health
6. Fix Qdrant health

**Commands:**
```bash
cd infrastructure/docker
docker-compose stop uitars dolphin-server open-webui
docker-compose rm -f uitars dolphin-server open-webui
docker-compose up -d  # Restart with clean config
```

### Step 2: Fix AUBS /ready Endpoint (15 min)
**File:** `aubs/src/main.py`
**Change:** Remove `orchestrator.dolphin_healthy` check

### Step 3: Connect Open-WebUI to AUBS (2 hours)
**Goal:** Make Open-WebUI (port 3000) able to call AUBS tools

**Options:**
- **Option A:** Register AUBS as MCP server in Open-WebUI
- **Option B:** Create Open-WebUI functions that call AUBS HTTP endpoints
- **Option C:** Expose AUBS endpoints as OpenAPI spec for Open-WebUI tools

**Need to research:** How to register tools in Open-WebUI

### Step 4: Implement First Tool (get_emails) (4 hours)
**File:** `aubs/src/tools/email_tools.py` (new)

**Code:**
```python
import imaplib
import email

def get_emails(limit=20, filter="UNSEEN"):
    """Get emails directly from Gmail IMAP"""
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(settings.gmail_email, settings.gmail_app_password)
    imap.select("INBOX")

    status, messages = imap.search(None, filter)
    email_ids = messages[0].split()[-limit:]

    results = []
    for email_id in email_ids:
        status, msg_data = imap.fetch(email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        results.append({
            "id": email_id.decode(),
            "subject": msg["Subject"],
            "sender": msg["From"],
            "date": msg["Date"]
        })

    imap.logout()
    return results
```

**Expose as:**
- AUBS HTTP endpoint: `GET /api/emails`
- Open-WebUI tool: `get_emails(limit, filter)`

**Test:**
```
User in Open-WebUI: "Show me my recent emails"
AUBS calls get_emails(limit=10)
Returns list of emails to Open-WebUI
```

### Step 5: Implement triage_email Tool (2 hours)
**Reuse:** `email_analyzer.py` (already exists!)

**Expose as:**
- AUBS HTTP endpoint: `POST /api/emails/{id}/triage`
- Open-WebUI tool: `triage_email(email_id)`

**Test:**
```
User: "What's urgent in my inbox?"
AUBS calls get_emails() + triage_email() for each
Returns: "3 urgent emails: ..."
```

---

## Port Configuration (Corrected)

| Service | Port | Access |
|---------|------|--------|
| **Open-WebUI** | 3000 | http://localhost:3000 (main interface) |
| **AUBS API** | 5000 | http://localhost:5000 (backend) |
| **SnappyMail** | 8888 | http://localhost:8888 (email viewing) |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache |
| **Qdrant** | 6333 | Vector DB |
| **Ollama** | 11434 | Local LLM |
| **NATS** | 4222, 8222 | Events + monitoring |

**Notes:**
- Open-WebUI is running on port 3000 (external to docker-compose)
- openwebui-backend in docker-compose has no port mapping (might not be needed if external open-webui works)
- v1 system uses ports 3001 and 8002 (no conflicts)

---

## Database Schema (What Exists in v1)

Since we're NOT sharing with v1, we need to decide:

### Option A: Create Fresh v2 Database
- New PostgreSQL database: `chilihead_v2`
- Start clean, only tables we need
- No migration from v1

### Option B: Minimal Schema for v2
Only tables needed for Phase 0-1:
```sql
-- Email analysis cache (reuse from v1)
CREATE TABLE email_analysis_cache (
    email_id TEXT PRIMARY KEY,
    analysis_result JSONB,
    analyzed_at TIMESTAMP,
    model_used TEXT
);

-- Execution tracking (for AUBS)
CREATE TABLE executions (
    id UUID PRIMARY KEY,
    email_id TEXT,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);
```

Later add:
- `tasks` table (Phase 1)
- `delegations` table (Phase 2)
- `chat_sessions` / `chat_messages` (Phase 2)

---

## Next Actions (Priority Order)

### 🔥 Immediate (Today)
1. **Stop Dolphin/UITARS containers** (5 min)
   ```bash
   docker stop chilihead-dolphin-server chilihead-uitars chilihead-frontend
   docker rm chilihead-dolphin-server chilihead-uitars chilihead-frontend
   ```

2. **Fix AUBS /ready endpoint** (10 min)
   - Remove `orchestrator.dolphin_healthy` check
   - Rebuild AUBS: `docker-compose up -d --build aubs`

3. **Test Open-WebUI on port 3000** (5 min)
   - Visit http://localhost:3000
   - Confirm it's accessible
   - Check if Ollama is connected

### 🎯 Phase 0 Completion (Tomorrow)
4. **Research Open-WebUI tool registration** (1 hour)
   - How to add custom tools/functions
   - MCP vs OpenAPI vs custom functions
   - Document the process

5. **Create first AUBS tool endpoint** (2 hours)
   - `/api/emails` with `get_emails()` using direct IMAP
   - Test with curl
   - Document API

6. **Register tool in Open-WebUI** (2 hours)
   - Connect Open-WebUI to AUBS `/api/emails`
   - Test: "Show me my recent emails" in chat
   - Verify tool call works

7. **Write PHASE_0_COMPLETE.md** (30 min)
   - Document what works
   - Test cases
   - Known issues
   - Handoff to Phase 1

### 📋 Phase 1 (Next Week)
8. Implement remaining email tools
9. Implement task tools
10. Test email-to-task flow

---

## Key Decisions Needed

### 1. Open-WebUI Configuration
**Question:** Use external open-webui (port 3000) or fix openwebui-backend in docker-compose?

**Recommendation:** Use external open-webui if it's working. Simpler.

### 2. Database Strategy
**Question:** Create fresh v2 database or minimal migration from v1?

**Recommendation:** Fresh v2 database. Clean slate. Only add tables as needed.

### 3. Email Ingestion Service
**Question:** Fix current email-ingestion or delete it?

**Current state:** Email-ingestion runs a sync job that caches emails to PostgreSQL
**v2 approach:** Direct IMAP (no sync job)

**Recommendation:** Delete email-ingestion service. Not needed in v2.

### 4. Qdrant
**Question:** Fix Qdrant now or wait until Phase 4 (memory/RAG)?

**Recommendation:** Wait. Not needed for Phase 0-2.

---

## Success Criteria for Phase 0

**Done when:**
- ✅ Open-WebUI accessible on port 3000
- ✅ AUBS healthy on port 5000
- ✅ SnappyMail accessible on port 8888
- ✅ Dolphin/UITARS containers removed
- ✅ First tool implemented: `get_emails()`
- ✅ Can test in Open-WebUI: "Show me my recent emails"
- ✅ Tool call succeeds and returns email list
- ✅ PHASE_0_COMPLETE.md written

**Time estimate:** 1 day (8 hours)

---

## What We Have vs What We Need

| Component | Status | Next Action |
|-----------|--------|-------------|
| Open-WebUI | ✅ Running (port 3000) | Configure tools |
| AUBS backend | ✅ Running (port 5000) | Add tool endpoints |
| SimpleOrchestrator | ✅ Working | Keep using |
| EmailAnalyzer | ✅ Working | Expose as tool |
| Chat service | ✅ Working | Integrate with Open-WebUI |
| SnappyMail | ✅ Working (port 8888) | Screenshot automation (later) |
| Email tools | ❌ Not implemented | **START HERE** |
| Task tools | ❌ Not implemented | Phase 1 |
| Calendar tools | ❌ Not implemented | Phase 2 |
| Vision/OCR | ❌ Not implemented | Phase 3 |
| RAG/Memory | ❌ Qdrant unhealthy | Phase 4 |

---

**Bottom line:** We're 30% through Phase 0. Need to clean up Docker, implement first tool, and connect to Open-WebUI.
