# ChiliHead OpsManager v2.0 - Rebuild Plan

## The Real Goal

Build a **better, more scalable version** of the working `chilihead-opsmanager-unified` system.

## What Went Wrong

1. TikTok mentioned ByteDance tools (Dolphin, UITARS)
2. Dolphin was described as "document ingestion" (misleading - it's actually Apache DolphinScheduler for DAG orchestration)
3. AI assistants were sycophantic and didn't push back
4. Over-engineered with complex orchestration we didn't need
5. Lost sight of the real mission

## What We're Actually Building

### Core Mission
Improve the existing system with these specific fixes:

**Problems to Solve:**
- ❌ Gmail API sanitization (loses formatting, can't show images)
- ❌ Memory issues
- ❌ Image preview broken in triage
- ❌ Assistants blind to each other (no shared context)

**Solutions:**
- ✅ SnappyMail for unsanitized email viewing (DONE!)
- ⏳ Better memory management
- ⏳ Image preview support
- ⏳ Shared context across all assistants
- ⏳ AUBS as central orchestrator

### Keep ALL Working Features From v1

**From chilihead-opsmanager-unified:**

1. **AI Email Triage**
   - GPT-4 powered email analysis
   - Priority scoring and categorization
   - Smart task extraction with deadlines
   - Daily operations briefing
   - Automatic deadline scanning

2. **Operations Chat Assistant**
   - Context-aware AI chat about operations
   - Full conversation history (PostgreSQL)
   - Session management
   - Knows tasks, deadlines, priorities

3. **Smart Todo List**
   - Eisenhower Matrix prioritization
   - Deadline tracking with date/time
   - Task status management
   - Google Calendar integration
   - Bulk add from email analysis

4. **ChiliHead 5-Pillar Delegations**
   - Sense of Belonging
   - Clear Direction
   - Preparation
   - Support
   - Accountability

5. **Database (PostgreSQL)**
   - email_state
   - tasks
   - delegations
   - chat_sessions
   - chat_messages
   - watch_config
   - ai_analysis_cache

### New Capabilities to Add

- Google Calendar management
- Google Chat integration (for team messaging)
- ~~Text messaging (Twilio)~~ - NOT IN SCOPE

### What We DON'T Need

- ❌ Apache DolphinScheduler (removed)
- ❌ UITARS monitoring dashboard (removed)
- ❌ Complex DAG orchestration (removed)
- ❌ Multi-step agent workflows (too complex)
- ❌ Zookeeper (removed)

## Simplified Architecture

```
┌─────────────────────────────────────────┐
│   ChiliHead Frontend (Next.js/React)    │
│                                         │
│  Tabs:                                  │
│  - Email Triage (AI analysis)           │
│  - Todo List (Eisenhower Matrix)        │
│  - Delegations (5-Pillar system)        │
│  - Operations Chat (AUBS)               │
│  - Daily Briefing                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  AUBS (Orchestrator + Chat Service)     │
│  - EmailAnalyzer (Claude/GPT-4)         │
│  - TaskExtractor                        │
│  - DeadlineScanner                      │
│  - DailyBriefGenerator                  │
│  - Context Memory (shared)              │
│  - Chat Assistant                       │
└──────┬──────────────────────────────────┘
       │
       ├─→ PostgreSQL (tasks, chat, etc.)
       ├─→ Qdrant (vector memory)
       └─→ Redis (session cache)

┌─────────────────────────────────────────┐
│  Email Layer                            │
│  - SnappyMail (full email viewing)      │
│  - Email Ingestion (filtered)           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Integrations                           │
│  - Google Calendar API                  │
│  - Google Chat API                      │
│  - Gmail IMAP/SMTP                      │
└─────────────────────────────────────────┘
```

## Current State

**What's Already Working:**
- ✅ SnappyMail configured with Gmail
- ✅ Email Ingestion filtering work emails
- ✅ AUBS with SimpleOrchestrator
- ✅ EmailAnalyzer (Claude/GPT-4)
- ✅ AUBS Chat service
- ✅ Basic HTML frontend with tabs

**What's Next:**
1. Build Smart Email Triage UI (show AI analysis)
2. Port Todo List from v1
3. Port ChiliHead Delegations from v1
4. Port Operations Chat UI from v1
5. Add Daily Briefing
6. Add Google Calendar integration
7. Add Google Chat integration
8. Add shared context/memory system

## Technology Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL (persistent storage)
- Redis (caching)
- Qdrant (vector memory)
- NATS (event streaming)

**Frontend:**
- Next.js 14 (or simple HTML/JS - TBD)
- React + TypeScript
- Tailwind CSS

**Email:**
- SnappyMail (webmail client)
- Email Ingestion (filtering + processing)

**AI:**
- OpenAI GPT-4 (analysis, chat)
- Anthropic Claude Sonnet 4 (AUBS personality)
- Ollama (optional local models)

**Integrations:**
- Gmail IMAP/SMTP
- Google Calendar API
- Google Chat API

## Non-Goals

- ❌ Text messaging (Twilio)
- ❌ Complex multi-agent orchestration
- ❌ DAG workflows
- ❌ Visual debugging tools
- ❌ GPU acceleration (not needed)

## Success Criteria

The system is successful when:
1. All v1 features work in v2
2. Email viewing is better (SnappyMail, no sanitization)
3. Memory issues are resolved
4. Image preview works in triage
5. Assistants share context
6. Google Calendar integrated
7. Google Chat integrated
8. System is scalable and maintainable
9. **AND** it's actually simpler than v1, not more complex

---

**Built with lessons learned: Start with what works, fix specific problems, don't over-engineer.**
