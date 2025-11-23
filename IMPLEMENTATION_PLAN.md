# ChiliHead OpsManager v2.1 - Implementation Plan

## Architecture Summary

### Core Components
1. **AUBS (Autonomous Unified Business System)** - Business logic orchestrator
2. **Dolphin Scheduler** - DAG-based task orchestration (Apache DolphinScheduler)
3. **UI-TARS Desktop** - Visual debugging and workflow monitoring
4. **Open-WebUI** - User interface layer with SnappyMail integration
5. **Agent Workers** - Specialized AI agents running on Dolphin workers
6. **Persistence Layer** - PostgreSQL, Redis, Qdrant, NATS JetStream

### Agent Specifications
- **Triage Agent** - Email categorization (llama-3.2-8b-instruct)
- **Vision Agent** - Image/PDF extraction (GPU-enabled)
- **Deadline Scanner** - Date/time extraction
- **Task Categorizer** - Action item identification
- **Context Agent** - Historical context synthesis (oss-120b, NO FALLBACK)

## Technology Stack

### Orchestration
- Apache DolphinScheduler 3.2.0
- NATS JetStream (event streaming)
- Redis (state management)

### AI/ML
- Ollama (local LLM hosting)
- Models: llama-3.2-8b-instruct, oss-120b
- Qdrant (vector database)

### Backend
- Python 3.11+ (FastAPI)
- PostgreSQL 15
- NATS messaging

### Frontend
- Open-WebUI (main interface)
- UI-TARS Desktop (React/TypeScript)
- SnappyMail (email client)

### Infrastructure
- Docker Compose (development)
- Kubernetes (production)
- NVIDIA GPU support

## Project Structure

```
ohhh1mail/
├── aubs/                          # AUBS orchestration service
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application
│   │   ├── orchestrator.py       # Main AUBS orchestrator
│   │   ├── dag_builder.py        # Dolphin DAG construction
│   │   ├── action_router.py      # Action routing logic
│   │   └── config.py             # Configuration management
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── agents/                        # Agent implementations
│   ├── base/
│   │   ├── __init__.py
│   │   ├── agent_contract.py     # Base agent interface
│   │   └── worker_base.py        # Dolphin worker base
│   ├── triage/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── prompts.py
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── extractors.py
│   ├── deadline/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── task/
│   │   ├── __init__.py
│   │   └── agent.py
│   └── context/
│       ├── __init__.py
│       ├── agent.py
│       └── memory.py
│
├── dolphin/                       # Dolphin configuration
│   ├── config/
│   │   ├── dolphin-config.yaml
│   │   └── worker-config.yaml
│   ├── dags/
│   │   └── email_processing.py
│   └── plugins/
│       └── uitars_plugin.py
│
├── uitars/                        # UI-TARS integration
│   ├── src/
│   │   ├── index.tsx
│   │   ├── UITARSPanel.tsx
│   │   ├── ExecutionDetail.tsx
│   │   └── config.ts
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── openwebui/                     # Open-WebUI customizations
│   ├── components/
│   │   ├── EmailDashboard.tsx
│   │   ├── TaskManager.tsx
│   │   └── DebugPanel.tsx
│   └── config/
│       └── openwebui-config.yaml
│
├── mcp-tools/                     # MCP tool implementations
│   ├── task_manager.py
│   ├── calendar.py
│   ├── sms.py
│   └── email_client.py
│
├── infrastructure/                # Infrastructure configs
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   └── .env.example
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── dolphin-server.yaml
│   │   ├── dolphin-workers.yaml
│   │   ├── aubs.yaml
│   │   ├── postgres.yaml
│   │   ├── redis.yaml
│   │   ├── nats.yaml
│   │   └── qdrant.yaml
│   └── scripts/
│       ├── init-db.sh
│       ├── setup-ollama.sh
│       └── deploy.sh
│
├── shared/                        # Shared libraries
│   ├── __init__.py
│   ├── events.py                 # NATS event definitions
│   ├── models.py                 # Pydantic models
│   ├── clients/
│   │   ├── dolphin_client.py
│   │   ├── uitars_client.py
│   │   ├── qdrant_client.py
│   │   └── nats_client.py
│   └── utils/
│       ├── logging.py
│       └── metrics.py
│
├── tests/
│   ├── integration/
│   ├── e2e/
│   └── load/
│
├── docs/
│   ├── architecture.md
│   ├── agent-specs.md
│   ├── deployment.md
│   └── troubleshooting.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── draftprd.md                   # Original PRD
├── IMPLEMENTATION_PLAN.md        # This file
├── README.md
└── requirements.txt              # Root dependencies
```

## Implementation Phases

### Phase 1: Infrastructure Setup (Week 1-2)
**Goal**: Get all supporting services running

#### Tasks:
1. Create Docker Compose configuration
   - PostgreSQL with initialization scripts
   - Redis for state management
   - NATS JetStream for event streaming
   - Qdrant for vector storage
   - Ollama with GPU support

2. Deploy Dolphin Scheduler
   - Server configuration
   - Worker node setup (2 workers: GPU + CPU)
   - Database initialization
   - API access configuration

3. Set up UI-TARS Desktop
   - Build UI-TARS React app
   - Configure Dolphin connection
   - Embed in Open-WebUI

4. Configure Open-WebUI
   - Custom component integration
   - SnappyMail email client setup
   - Tab structure (Email | Tasks | Debug | Analytics)

#### Deliverables:
- [ ] `docker-compose.yml` with all services
- [ ] All services running and healthy
- [ ] Dolphin UI accessible at localhost:12345
- [ ] Open-WebUI accessible at localhost:3000
- [ ] UI-TARS embedded in Open-WebUI

### Phase 2: AUBS Core (Week 3-4)
**Goal**: Build the orchestration layer

#### Tasks:
1. Create AUBS FastAPI service
   - Configuration management
   - Health checks and monitoring
   - API endpoints for email processing

2. Implement Dolphin DAG builder
   - Email processing DAG template
   - Dynamic task graph generation
   - Conditional Vision Agent inclusion
   - XCom data passing

3. Set up NATS event streams
   - Event schema definitions
   - Publisher/subscriber patterns
   - Event replay capability
   - Dead letter queues

4. Implement UI-TARS checkpoint system
   - Checkpoint creation API
   - Screenshot capture
   - Performance metrics collection
   - Timeline visualization data

5. Build action router
   - MCP tool integration
   - Confidence threshold logic
   - High-risk action detection
   - Human review queue

#### Deliverables:
- [ ] AUBS service running on port 5000
- [ ] Email -> DAG conversion working
- [ ] NATS events flowing
- [ ] UI-TARS checkpoints visible
- [ ] Action routing functional

### Phase 3: Agent Development (Week 5-6)
**Goal**: Implement all AI agents

#### Tasks:
1. Create base agent framework
   - AgentContract interface
   - Dolphin worker integration
   - UI-TARS checkpoint helpers
   - Error handling and retries

2. Implement Triage Agent
   - Prompt engineering for categorization
   - Urgency scoring (0-100)
   - Vision requirement detection
   - Deadline presence detection
   - Model: llama-3.2-8b-instruct

3. Implement Vision Agent
   - PDF/image processing
   - OCR with tesseract/paddleocr
   - Invoice data extraction
   - Receipt parsing
   - Structured output generation
   - GPU acceleration

4. Implement Deadline Scanner
   - Natural language date extraction
   - Recurring event detection
   - Timezone handling
   - Calendar integration prep

5. Implement Task Categorizer
   - Action item identification
   - Priority assignment
   - Assignee suggestion
   - Dependency detection

6. Implement Context Agent (CRITICAL)
   - Historical email retrieval from Qdrant
   - Vendor pattern analysis
   - Multi-agent output synthesis
   - Recommendation generation
   - Risk assessment
   - Model: oss-120b (NO FALLBACK)

#### Deliverables:
- [ ] All 5 agents implemented
- [ ] Unit tests for each agent
- [ ] Dolphin worker tasks registered
- [ ] Agent outputs validated against contracts
- [ ] Context Agent using best model only

### Phase 4: Integration (Week 7-8)
**Goal**: Wire everything together

#### Tasks:
1. Email ingestion pipeline
   - IMAP connection to SnappyMail
   - Email parsing and normalization
   - Attachment handling
   - Event publication to NATS

2. MCP tool implementations
   - Task manager (create, update, assign)
   - Calendar (schedule events, send invites)
   - SMS (Twilio integration)
   - Notification system

3. End-to-end testing
   - Synthetic email generation
   - Full pipeline execution
   - UI-TARS replay verification
   - Action execution validation

4. UI-TARS debugging setup
   - Session management
   - Execution replay
   - Screenshot timeline
   - Decision tree visualization
   - Performance profiling

5. Open-WebUI integration
   - Email dashboard with agent insights
   - Task management interface
   - Debug panel with UI-TARS
   - Analytics dashboard

#### Deliverables:
- [ ] Email -> Action end-to-end flow working
- [ ] MCP tools integrated
- [ ] UI shows agent decisions
- [ ] Debug replay functional
- [ ] All integration tests passing

### Phase 5: Production Hardening (Week 9-10)
**Goal**: Make it production-ready

#### Tasks:
1. Load testing with Dolphin
   - 500+ emails/day simulation
   - Concurrent execution testing
   - Resource utilization monitoring
   - Bottleneck identification

2. Failure recovery scenarios
   - Agent failure handling
   - Context Agent critical failure path
   - Dolphin worker restart
   - Database connection loss
   - NATS unavailability

3. Performance optimization
   - Database query optimization
   - Vector search tuning
   - Caching strategy
   - Model inference optimization
   - GPU memory management

4. Security hardening
   - API authentication (JWT)
   - Email content sanitization
   - SQL injection prevention
   - Rate limiting
   - Secrets management

5. Documentation and training
   - Architecture documentation
   - Agent specification docs
   - Deployment runbook
   - Troubleshooting guide
   - User manual

#### Deliverables:
- [ ] Load test passing 500 emails/day
- [ ] Failure scenarios handled gracefully
- [ ] Performance targets met
- [ ] Security audit passed
- [ ] Complete documentation

## Success Metrics

### Performance
- Process 500+ emails/day through Dolphin workers
- Agent execution time < 30s per email (avg)
- Context Agent response time < 10s
- UI-TARS latency < 100ms for checkpoint updates

### Reliability
- 99.9% uptime over 30-day period
- Zero critical failures (Context Agent)
- < 1% agent task retry rate
- Zero data loss

### Visibility
- 100% of executions visible in UI-TARS
- Complete decision audit trail
- 80% reduction in debugging time
- Real-time monitoring of all agents

### Accuracy
- Triage accuracy > 95%
- Vision extraction accuracy > 90%
- Deadline detection accuracy > 85%
- Context Agent confidence > 0.9 for auto-actions

## Risk Mitigation

### Critical Risks
1. **Context Agent Model Unavailable**
   - Mitigation: NO FALLBACK - fail the workflow
   - Alert: Immediate notification to ops team
   - Recovery: Manual processing queue

2. **GPU Resource Exhaustion**
   - Mitigation: Dolphin resource management
   - Alert: GPU memory monitoring
   - Recovery: Queue overflow to CPU-only tasks

3. **Dolphin Scheduler Failure**
   - Mitigation: Kubernetes pod restart
   - Alert: Health check failure
   - Recovery: In-flight DAGs resume from checkpoint

4. **Vector Database Corruption**
   - Mitigation: Daily backups to S3
   - Alert: Consistency checks
   - Recovery: Restore from backup

## Development Tools

### Required Tools
- Docker Desktop (with WSL2 on Windows)
- Python 3.11+
- Node.js 18+
- NVIDIA Container Toolkit (for GPU)
- kubectl (for K8s deployment)
- NATS CLI
- PostgreSQL client

### IDE Setup
- VSCode with Python, Docker, Kubernetes extensions
- PyCharm (optional)
- Insomnia/Postman for API testing

### Monitoring Tools
- Grafana (metrics visualization)
- Prometheus (metrics collection)
- Jaeger (distributed tracing)
- UI-TARS Desktop (workflow debugging)

## Next Steps

1. **Initialize Project Structure**
   ```bash
   mkdir -p ohhh1mail/{aubs,agents,dolphin,uitars,openwebui,mcp-tools,infrastructure,shared,tests,docs}
   cd ohhh1mail
   git init
   ```

2. **Create Python Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Start Infrastructure**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

5. **Run Initial Tests**
   ```bash
   pytest tests/integration/test_infrastructure.py
   ```

## Estimated Timeline

- **Phase 1**: 2 weeks (Infrastructure)
- **Phase 2**: 2 weeks (AUBS Core)
- **Phase 3**: 2 weeks (Agent Development)
- **Phase 4**: 2 weeks (Integration)
- **Phase 5**: 2 weeks (Production Hardening)

**Total**: 10 weeks (2.5 months)

## Team Recommendations

- 1x Backend Developer (AUBS, Agents)
- 1x DevOps Engineer (Infrastructure, Dolphin)
- 1x Frontend Developer (UI-TARS, Open-WebUI)
- 1x ML Engineer (Agent optimization, model management)
- 1x QA Engineer (Testing, validation)

Or: Use Claude Code with AI agent coordination to build incrementally!
