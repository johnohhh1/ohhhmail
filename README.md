# 🌶️ ChiliHead OpsManager v2.1 - OHHH1MAIL Platform

> AI-powered restaurant operations management platform for Chili's #605 Auburn Hills

**Complete email automation + AI agent orchestration + Visual debugging + Intelligent chat assistant**

---

## 🎯 What Is This?

ChiliHead OpsManager v2.1 automates restaurant operations for John at Chili's #605 in Auburn Hills. The system:

1. **Monitors Gmail** for restaurant-related emails (filtered by domain/sender)
2. **Processes emails** through 5 specialized AI agents orchestrated by Apache Dolphin Scheduler
3. **Extracts tasks and deadlines** automatically from leadership communications
4. **Provides AUBS** - Your friendly AI assistant with complete operational awareness
5. **Visualizes everything** through Open-WebUI with embedded debugging tools

---

## ✨ Key Features

### 🤖 AUBS - Your Personal Assistant
**AUBS** (Auburn Hills Business System) is your friendly, intelligent operations assistant who:
- Has complete awareness of all emails, tasks, and deadlines
- Understands Chili's operations, RAP Mobile metrics, and HotSchedules
- Prioritizes like you would (leadership deadlines first, then team issues, then guests)
- Talks conversationally - not like a robot
- Available 24/7 via chat in Open-WebUI

[See full AUBS Guide](docs/AUBS_GUIDE.md)

### 📧 Smart Email Processing
- **5 AI Agents** working together:
  - **Triage Agent**: Categorizes and routes emails
  - **Vision Agent**: OCR for invoices, receipts, PDFs
  - **Deadline Scanner**: Extracts dates and deadlines
  - **Task Categorizer**: Identifies action items
  - **Context Agent**: Synthesizes everything with 30-day memory
- **Email Filtering**: Only processes emails from `chilis.com`, `brinker.com`, `hotschedules.com`
- **Attachment Handling**: OCR, PDF parsing, image analysis

### 🎨 Open-WebUI Interface
**8 tabs for complete operational visibility:**

1. **Dashboard** - Overview of operations
2. **Emails** - Inbox, processed emails, agent outputs, quick actions
3. **Tasks** - Task management with priorities and due dates
4. **Calendar** - Events, deadlines, scheduling
5. **Debug** - UI-TARS execution timeline, agent decisions, screenshots, DAG visualization
6. **Analytics** - Performance metrics, agent stats, email volume, response times
7. **Agents** - Agent status, model selection, performance, logs
8. **Settings** - Model config, thresholds, notifications, integrations

### 🔄 Enterprise Orchestration
- **Apache DolphinScheduler 3.2.0** - DAG-based workflow orchestration
- **Fault-tolerant** - Automatic retries and error handling
- **Visual debugging** - UI-TARS embedded in Open-WebUI
- **GPU acceleration** - NVIDIA GPU support for Vision Agent

### 🧠 Multi-Provider LLM Support
Easy model swapping between:
- **OpenAI**: GPT-4o, GPT-5
- **Anthropic**: Claude Sonnet 4 (AUBS uses this)
- **Ollama**: Llama 3.2, local models

Configure per-agent in `.env` file.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Open-WebUI (Port 3040)                    │
│  Dashboard | Emails | Tasks | Calendar | Debug | Analytics  │
│                        Chat with AUBS                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              AUBS (Autonomous Unified Business System)       │
│        Orchestrator | DAG Builder | Action Router           │
│               Chat Service (Claude Sonnet 4)                 │
└────────┬────────────────────────┬────────────────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐    ┌──────────────────────────────────┐
│ Email Ingestion  │    │  Apache Dolphin Scheduler 3.2.0  │
│  - IMAP Monitor  │    │   - DAG Execution                │
│  - Domain Filter │    │   - GPU/CPU Workers              │
│  - Attachment DL │    │   - Task Scheduling              │
└──────────────────┘    └──────────────┬───────────────────┘
                                       │
         ┌─────────────────────────────┼────────────────────┐
         │                             │                    │
         ▼                             ▼                    ▼
┌─────────────────┐         ┌─────────────────┐  ┌─────────────────┐
│ Triage Agent    │         │  Vision Agent   │  │ Deadline Agent  │
│ (Llama 3.2)     │         │  (GPT-4o + GPU) │  │ (Llama 3.2)     │
└─────────────────┘         └─────────────────┘  └─────────────────┘
         │                             │                    │
         └─────────────────────────────┼────────────────────┘
                                       ▼
                            ┌─────────────────────┐
                            │  Task Agent         │
                            │  (Llama 3.2)        │
                            └──────────┬──────────┘
                                       ▼
                            ┌─────────────────────┐
                            │  Context Agent      │
                            │  (Claude Sonnet 4)  │
                            │  NO FALLBACK        │
                            └──────────┬──────────┘
                                       ▼
                ┌──────────────────────────────────────────┐
                │         MCP Tools (Actions)              │
                │  - Task Manager    - SMS Sender          │
                │  - Calendar Sync   - Email Responder     │
                └──────────────────────────────────────────┘

Infrastructure:
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ PostgreSQL  │   Redis     │    NATS     │   Qdrant    │   Ollama    │
│  (Data)     │  (Cache)    │  (Events)   │ (Vectors)   │  (LLMs)     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 🚀 Quick Start (Windows)

### Prerequisites

- **Docker Desktop** with WSL2 enabled
- **NVIDIA GPU** with CUDA support (for Vision Agent)
- **16GB+ RAM** recommended
- **Gmail account** with App Password configured
- **OpenAI API key** (optional, for GPT models)
- **Anthropic API key** (for Claude / AUBS chat)

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/johnohhh1/ohhhmail.git
   cd ohhhmail
   ```

2. **Configure Environment**

   Edit `infrastructure/docker/.env` with your credentials:
   - OpenAI API key (if using GPT models)
   - Anthropic API key (required for AUBS chat)
   - Gmail credentials
   - Email filtering (allowed domains/senders)

   **CRITICAL Email Filtering:**
   ```env
   ALLOWED_DOMAINS=chilis.com,brinker.com,hotschedules.com
   ALLOWED_SENDERS=
   BLOCKED_DOMAINS=spam.com
   BLOCKED_SENDERS=
   ```

3. **Start All Services**
   ```bash
   start.bat
   ```

   This will:
   - Check Docker is running
   - Start all 13 services via Docker Compose
   - Wait for services to initialize
   - Open Open-WebUI in your browser

4. **Access Services**
   - **Open-WebUI**: http://localhost:3040
   - **Dolphin Scheduler**: http://localhost:12345 (admin/admin)
   - **AUBS API**: http://localhost:5000
   - **Grafana** (optional): http://localhost:3001

---

## 💬 Chat with AUBS

### Quick Start

1. Open http://localhost:3040
2. Click the chat button (floating button in bottom-right)
3. Start chatting!

### Example Conversations

**You:** "What's urgent today?"

**AUBS:** "Hey John! Here's what needs your attention:

1. **Leadership deadline** - Your DM needs the manager schedule by Friday 5pm
2. **Team issue** - Sarah called out for tonight's shift
3. **Guest complaint** - Slow service feedback from last night

Want me to help you prioritize?"

**You:** "Help me plan my next 2 hours"

**AUBS:** "Sure! Based on what we have:

First 30 minutes:
- Review and send manager schedule to DM (critical deadline)
- Call Sarah to confirm her shift status

Next 60 minutes:
- Address guest complaint - review section 3 service times
- Prep for tonight with one server short

The DM deadline is most urgent. Want me to pull up the schedule?"

**You:** "What's our comp sales this week?"

**AUBS:** "I don't have access to RAP Mobile data yet (coming in next update), but I can see we processed 47 emails this week with 3 from corporate leadership. Want me to check if any mentioned sales numbers?"

[See full AUBS Guide](docs/AUBS_GUIDE.md)

---

## 📊 System Components

### 13 Docker Services

1. **postgres** - PostgreSQL 15 (persistent storage)
2. **redis** - Redis 7 (caching, state)
3. **nats** - NATS JetStream (event streaming)
4. **qdrant** - Vector database (context memory)
5. **ollama** - Local LLM hosting
6. **dolphin-server** - Dolphin scheduler server
7. **dolphin-worker-gpu** - GPU worker for Vision Agent
8. **dolphin-worker-cpu** - CPU workers for other agents
9. **aubs** - AUBS orchestrator and chat service
10. **email-ingestion** - Gmail monitoring and filtering
11. **open-webui** - Web interface (port 3040)
12. **uitars** - Visual debugging service
13. **grafana** (optional) - Monitoring dashboards

### 5 AI Agents

| Agent | Model | Purpose | Timeout |
|-------|-------|---------|---------|
| **Triage** | llama3.2:8b-instruct | Email categorization | 15s |
| **Vision** | gpt-4o (GPU) | OCR, image processing | 30s |
| **Deadline** | llama3.2:8b-instruct | Date extraction | 15s |
| **Task** | llama3.2:8b-instruct | Action identification | 15s |
| **Context** | claude-sonnet-4 | Context synthesis (NO FALLBACK) | 30s |

All agents configurable per environment in `.env`.

---

## 🛠️ Management Commands

### Windows Batch Files

- **start.bat** - Start all services
- **stop.bat** - Stop all services
- **status.bat** - Check service health
- **logs.bat** - View service logs (interactive menu)
- **setup.bat** - Initial setup and dependency installation

### Docker Commands

```bash
# View all services
docker-compose ps

# View logs for specific service
docker-compose logs -f aubs
docker-compose logs -f email-ingestion

# Restart a service
docker-compose restart aubs

# Stop everything
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

---

## ⚙️ Configuration

### Agent Models

Edit `infrastructure/docker/.env` to change models:

```env
# Triage Agent - Fast categorization
TRIAGE_AGENT_PROVIDER=ollama
TRIAGE_AGENT_MODEL=llama3.2:8b-instruct
TRIAGE_AGENT_FALLBACK=openai:gpt-4o-mini

# Vision Agent - OCR (needs GPU)
VISION_AGENT_PROVIDER=openai
VISION_AGENT_MODEL=gpt-4o
VISION_AGENT_GPU=true

# Context Agent - CRITICAL, NO FALLBACK
CONTEXT_AGENT_PROVIDER=anthropic
CONTEXT_AGENT_MODEL=claude-sonnet-4
CONTEXT_AGENT_FALLBACK=DISABLED
```

### Email Filtering (CRITICAL)

```env
# Only process emails from these domains
ALLOWED_DOMAINS=chilis.com,brinker.com,hotschedules.com

# Optionally restrict to specific senders
ALLOWED_SENDERS=dm@chilis.com,regional@brinker.com

# Block specific domains or senders
BLOCKED_DOMAINS=spam.com,marketing.com
BLOCKED_SENDERS=noreply@spam.com
```

**After changing filters, restart email-ingestion:**
```bash
docker-compose restart email-ingestion
```

---

## 📁 Project Structure

```
ohhhmail/
├── aubs/                        # AUBS orchestrator
│   └── src/
│       ├── main.py             # FastAPI app
│       ├── orchestrator.py     # DAG builder
│       ├── dag_builder.py      # DAG construction
│       ├── action_router.py    # MCP tool routing
│       └── chat.py             # AUBS chat service ⭐
│
├── agents/                      # 5 AI agents
│   ├── triage/
│   ├── vision/
│   ├── deadline/
│   ├── task/
│   └── context/
│
├── email_ingestion/             # Gmail monitoring
│   ├── monitor.py              # IMAP monitoring
│   ├── processor.py            # Email processing ⭐ (filtering)
│   └── config.py               # Configuration
│
├── openwebui/                   # Open-WebUI components
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── EmailDashboard.tsx
│   │   ├── TaskManager.tsx
│   │   ├── CalendarView.tsx
│   │   ├── UITARSDebugPanel.tsx  # Embedded debugging
│   │   ├── Analytics.tsx
│   │   ├── AgentMonitor.tsx
│   │   ├── Settings.tsx
│   │   └── ChatWithAUBS.tsx    # AUBS chat UI ⭐
│   └── config/
│       └── tabs-config.json    # 8 tabs configuration
│
├── mcp_tools/                   # MCP action tools
│   ├── task_manager.py
│   ├── calendar_integration.py
│   └── sms_sender.py
│
├── shared/                      # Shared libraries
│   ├── models.py               # Pydantic models
│   ├── llm_config.py           # Multi-provider LLM
│   └── clients/                # Service clients
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml  # 13 services
│   │   └── .env                # Configuration ⭐
│   └── dolphin/                # Dolphin configs
│
├── docs/                        # Documentation
│   ├── AUBS_GUIDE.md           # AUBS user guide ⭐
│   ├── BUILD_STATUS.md         # Implementation status
│   ├── IMPLEMENTATION_PLAN.md  # 10-week plan
│   └── QUICK_START.md          # Getting started
│
├── start.bat                    # Windows start script
├── stop.bat                     # Windows stop script
├── status.bat                   # Health check script
└── logs.bat                     # Log viewer script
```

⭐ = Recently updated with AUBS persona and email filtering

---

## 📚 Documentation

- **[AUBS Guide](docs/AUBS_GUIDE.md)** - Complete guide to using AUBS
- **[Quick Start](docs/QUICK_START.md)** - Getting started guide
- **[Build Status](docs/BUILD_STATUS.md)** - Implementation status
- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)** - 10-week roadmap
- **[Build Orchestrator](docs/BUILD_ORCHESTRATOR.md)** - AI swarm build strategy

---

## 🔍 Monitoring & Debugging

### Health Checks

```bash
# Check all services
status.bat

# Individual health endpoints
curl http://localhost:5000/health      # AUBS
curl http://localhost:8001/health      # Email Ingestion
curl http://localhost:12345/dolphinscheduler/health  # Dolphin
```

### Logs

```bash
# Interactive log viewer
logs.bat

# Or direct Docker commands
docker-compose logs -f aubs
docker-compose logs -f email-ingestion
docker-compose logs -f dolphin-server
```

### UI-TARS Debug Panel

1. Open http://localhost:3040
2. Click "Debug" tab
3. View:
   - Execution timeline with timestamps
   - Agent decisions and reasoning
   - Screenshots from Vision Agent
   - DAG visualization
   - Replay capability

---

## 🎯 Current Status

### ✅ Completed

- [x] Complete project structure (40+ directories)
- [x] Docker infrastructure (13 services)
- [x] Shared client libraries (Dolphin, NATS, Qdrant, Ollama, LLM)
- [x] AUBS service (orchestrator, DAG builder, action router)
- [x] All 5 AI agents (Triage, Vision, Deadline, Task, Context)
- [x] MCP tools (Task, Calendar, SMS, Email)
- [x] Email ingestion with CRITICAL filtering
- [x] Open-WebUI components (8 tabs)
- [x] **AUBS chat with full persona and operational awareness** ⭐
- [x] Windows batch files for management
- [x] Complete documentation

### 🚧 In Progress

- [ ] PostgreSQL persistence for chat sessions
- [ ] RAP Mobile metrics integration
- [ ] HotSchedules integration
- [ ] Google Calendar sync
- [ ] ChiliHead 5-Pillar Delegations (can wait)

### 📋 Planned

- [ ] Proactive AUBS alerts
- [ ] Voice interface for AUBS
- [ ] Performance trend analysis
- [ ] Mobile app
- [ ] Multi-restaurant support

---

## 🔒 Security & Privacy

### Data Privacy
- All data stays on your infrastructure
- No external data sharing
- Gmail credentials stored securely in environment variables
- Email filtering prevents spam and noise

### API Keys
- OpenAI API key: Optional (only if using GPT models)
- Anthropic API key: Required (for AUBS chat and Context Agent)
- All API calls encrypted and ephemeral

### Access Control
- Currently single-user (John)
- Can be extended with authentication

---

## 🐛 Troubleshooting

### AUBS Not Responding

1. Check AUBS service:
   ```bash
   docker-compose ps aubs
   docker-compose logs -f aubs
   ```

2. Verify Anthropic API key in `.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

3. Restart AUBS:
   ```bash
   docker-compose restart aubs
   ```

### Emails Not Being Processed

1. Check email filtering configuration in `.env`
2. Verify Gmail credentials
3. Check email-ingestion logs:
   ```bash
   docker-compose logs -f email-ingestion
   ```

### Services Won't Start

1. Verify Docker Desktop is running
2. Check port 3040 is available (not 3000)
3. Review `.env` for missing values
4. Check logs: `docker-compose logs`

### GPU Not Detected (Vision Agent)

1. Verify NVIDIA drivers installed
2. Check Docker Desktop GPU support enabled
3. Test: `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`

---

## 👨‍💼 About

**Built specifically for:**
- **John Olenski** - Managing Partner
- **Chili's #605** - Auburn Hills, Michigan
- **Brinker International** - Franchise operations

**Contact:**
- Email: john.olenski@gmail.com
- GitHub: [@johnohhh1](https://github.com/johnohhh1)

---

## 📄 License

Private & Confidential - All Rights Reserved

---

**Built with ❤️ by a GM who believes great people deserve great tools.**

*🌶️ "Excellence Through Leadership & Accountability"*
