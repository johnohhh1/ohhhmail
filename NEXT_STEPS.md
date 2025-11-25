# ChiliHead v2.0 - Next Steps
**Based on:** Current state assessment
**Status:** SnappyMail done right, Open-WebUI has poorly wired tabs

---

## Immediate Priority: Fix Open-WebUI (Today)

### Problem
Open-WebUI exists with tabs but they're "wired poorly" - need to fix configuration.

### What to Check
1. **Which Open-WebUI instance are we using?**
   - External `open-webui` on port 3000?
   - OR `chilihead-openwebui-backend` (no port exposed)?

2. **What tabs exist and what's wrong?**
   - What tabs are configured?
   - How are they wired?
   - What should they do vs what they're doing?

### Actions
1. **Visit Open-WebUI** → http://localhost:3000
2. **Document current tab configuration**
3. **Identify what's wired wrong**
4. **Fix tab configuration** OR **start fresh with clean Open-WebUI setup**

---

## Clean Docker Containers (15 minutes)

Stop and remove dead services:
```bash
cd infrastructure/docker

# Stop old/broken services
docker stop chilihead-dolphin-server chilihead-uitars chilihead-frontend

# Remove them
docker rm chilihead-dolphin-server chilihead-uitars chilihead-frontend

# Verify they're gone
docker ps
```

---

## Fix AUBS /ready Endpoint (10 minutes)

**File:** `aubs/src/main.py` line 140-146

**Current (broken):**
```python
if not orchestrator.dolphin_healthy:
    raise HTTPException(...)
```

**Fix:** Remove Dolphin check entirely or replace with simple check:
```python
if not orchestrator.nats_connected:
    raise HTTPException(...)
```

**Rebuild:**
```bash
cd infrastructure/docker
docker-compose up -d --build aubs
```

---

## Phase 0: First Tool Implementation

### Goal
Get ONE tool working end-to-end:
- User asks in Open-WebUI: "Show me my recent emails"
- Open-WebUI calls AUBS tool
- AUBS fetches from Gmail IMAP
- Returns email list to user

### Step 1: Create Email Tools Module (2 hours)

**File:** `aubs/src/tools/email_tools.py` (NEW)

```python
"""
Email tools for Open-WebUI integration
Direct IMAP access to Gmail
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict
from src.config import settings
import structlog

logger = structlog.get_logger()

def get_emails(limit: int = 20, filter_criteria: str = "UNSEEN") -> List[Dict]:
    """
    Fetch emails directly from Gmail via IMAP

    Args:
        limit: Maximum number of emails to return
        filter_criteria: IMAP search criteria (UNSEEN, ALL, SINCE date, etc.)

    Returns:
        List of email dictionaries with id, subject, sender, date, snippet
    """
    try:
        # Connect to Gmail
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(settings.gmail_email, settings.gmail_app_password)
        imap.select("INBOX")

        # Search emails
        status, messages = imap.search(None, filter_criteria)
        if status != "OK":
            logger.error("IMAP search failed", status=status)
            return []

        email_ids = messages[0].split()
        # Get last N emails
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids

        results = []
        for email_id in email_ids:
            try:
                status, msg_data = imap.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Decode subject
                subject_parts = decode_header(msg["Subject"])
                subject = ""
                for part, encoding in subject_parts:
                    if isinstance(part, bytes):
                        subject += part.decode(encoding or "utf-8", errors="ignore")
                    else:
                        subject += part

                # Get body snippet
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                snippet = body[:200] if body else ""

                results.append({
                    "id": email_id.decode(),
                    "subject": subject,
                    "sender": msg["From"],
                    "date": msg["Date"],
                    "snippet": snippet
                })

            except Exception as e:
                logger.error("Failed to parse email", email_id=email_id, error=str(e))
                continue

        imap.logout()
        logger.info("Fetched emails from IMAP", count=len(results))
        return results

    except Exception as e:
        logger.error("Failed to connect to Gmail IMAP", error=str(e))
        return []
```

**Add to config.py:**
```python
# Gmail settings
gmail_email: str = Field(..., env="GMAIL_EMAIL")
gmail_app_password: str = Field(..., env="GMAIL_APP_PASSWORD")
```

**Add to docker-compose.yml:**
```yaml
environment:
  - GMAIL_EMAIL=${GMAIL_EMAIL}
  - GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD}
```

### Step 2: Expose as HTTP Endpoint (30 minutes)

**File:** `aubs/src/main.py`

Add route:
```python
@app.get("/api/emails")
async def get_emails_endpoint(
    limit: int = 20,
    filter: str = "UNSEEN"
):
    """
    Get emails from Gmail IMAP

    Args:
        limit: Max emails to return
        filter: IMAP search criteria

    Returns:
        List of emails
    """
    from src.tools.email_tools import get_emails

    try:
        emails = get_emails(limit=limit, filter_criteria=filter)
        return {
            "emails": emails,
            "count": len(emails)
        }
    except Exception as e:
        logger.error("Failed to get emails", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch emails: {str(e)}"
        )
```

### Step 3: Test with curl (5 minutes)

```bash
# Test endpoint
curl http://localhost:5000/api/emails?limit=5

# Expected response:
{
  "emails": [
    {
      "id": "12345",
      "subject": "Manager Schedule Due Today",
      "sender": "Stephanie <stephanie@chilis.com>",
      "date": "Mon, 25 Nov 2024 08:30:00",
      "snippet": "Please submit manager schedule by 3pm..."
    },
    ...
  ],
  "count": 5
}
```

### Step 4: Register with Open-WebUI (TBD - need to research)

**Options:**
1. **OpenAPI/Swagger integration** - Open-WebUI auto-discovers from `/docs`
2. **MCP Server** - Register AUBS as Model Context Protocol server
3. **Custom Function** - Define function in Open-WebUI config

**Need to:**
- Check Open-WebUI documentation
- Determine best integration method
- Implement tool registration

### Step 5: Test End-to-End (15 minutes)

```
User in Open-WebUI chat:
> "Show me my recent emails"

Expected:
- Open-WebUI calls get_emails tool
- AUBS returns email list
- User sees formatted email list in chat
```

---

## Phase 0 Completion Criteria

✅ **Done when:**
1. Dolphin/UITARS containers removed
2. AUBS /ready endpoint fixed
3. `get_emails()` tool implemented and tested
4. Tool accessible via HTTP at `/api/emails`
5. Open-WebUI tabs fixed/configured properly
6. Can test: "Show me my emails" in Open-WebUI
7. Results appear in chat

📄 **Deliverables:**
- PHASE_0_COMPLETE.md with:
  - What works
  - Test commands
  - Known issues
  - Next phase plan

---

## Questions to Answer

### 1. Open-WebUI Configuration
- Which tabs exist?
- What's wired wrong?
- What should each tab do?

### 2. Tool Registration
- How does Open-WebUI discover tools?
- OpenAPI vs MCP vs custom?
- Where's the config file?

### 3. Gmail Credentials
- Do we have GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env?
- Are they passed to AUBS container?

### 4. Email Ingestion Service
- Keep it or delete it?
- Currently unhealthy - what's the issue?
- Do we need it if we're using direct IMAP?

---

## Timeline

**Today (4 hours):**
- Clean Docker containers (15 min)
- Fix AUBS /ready endpoint (10 min)
- Check Open-WebUI tabs, document issues (30 min)
- Implement get_emails() tool (2 hours)
- Test with curl (5 min)
- Research Open-WebUI tool registration (1 hour)

**Tomorrow (4 hours):**
- Fix Open-WebUI tab configuration (2 hours)
- Register get_emails tool in Open-WebUI (1 hour)
- End-to-end testing (30 min)
- Write PHASE_0_COMPLETE.md (30 min)

**Total:** 1 day to Phase 0 complete

---

## What to Work on RIGHT NOW

### Priority 1: Clean Containers
```bash
cd infrastructure/docker
docker stop chilihead-dolphin-server chilihead-uitars chilihead-frontend
docker rm chilihead-dolphin-server chilihead-uitars chilihead-frontend
docker ps  # Verify clean
```

### Priority 2: Check Open-WebUI
1. Visit http://localhost:3000
2. Screenshot what you see
3. Document what tabs exist and what's wrong
4. Share findings so we can fix

### Priority 3: Implement get_emails Tool
Start coding `aubs/src/tools/email_tools.py`

---

**Let's start with Priority 1 and 2. Want me to help clean the containers and check Open-WebUI?**
