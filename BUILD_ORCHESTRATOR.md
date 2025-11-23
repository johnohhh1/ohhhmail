# ChiliHead OpsManager v2.1 - Build Orchestration Strategy

## Automated Build Approach

This project will be built using AI agent swarms coordinated through Claude-Flow and Flow-Nexus to maximize development velocity and code quality.

## Swarm Architecture

### Swarm Topology: Hierarchical
**Why**: Complex multi-component system requires central coordination with specialized worker teams

### Agent Teams

#### 1. Infrastructure Team (backend-dev + devops agents)
**Responsibilities**:
- Docker Compose configuration
- Kubernetes manifests
- Database initialization scripts
- Service networking
- Volume management

**Deliverables**:
- `infrastructure/docker/docker-compose.yml`
- `infrastructure/kubernetes/*.yaml`
- `infrastructure/scripts/*.sh`

#### 2. AUBS Team (backend-dev + api-docs agents)
**Responsibilities**:
- FastAPI application structure
- AUBS orchestrator implementation
- DAG builder for Dolphin
- Action router logic
- Configuration management

**Deliverables**:
- `aubs/src/*.py`
- `aubs/tests/*.py`
- `aubs/Dockerfile`
- API documentation

#### 3. Agent Development Team (ml-developer + coder agents)
**Responsibilities**:
- Base agent contracts
- Triage Agent implementation
- Vision Agent with GPU support
- Deadline Scanner
- Task Categorizer
- Context Agent (critical, no fallback)

**Deliverables**:
- `agents/base/*.py`
- `agents/{triage,vision,deadline,task,context}/*.py`
- Model integration code
- Agent tests

#### 4. Frontend Team (mobile-dev focused on React)
**Responsibilities**:
- UI-TARS Desktop integration
- Open-WebUI custom components
- Email dashboard
- Debug panel
- Analytics views

**Deliverables**:
- `uitars/src/*.tsx`
- `openwebui/components/*.tsx`
- TypeScript type definitions

#### 5. Integration Team (backend-dev + tester agents)
**Responsibilities**:
- MCP tool implementations
- NATS event streaming
- Email ingestion pipeline
- End-to-end testing
- Integration tests

**Deliverables**:
- `mcp-tools/*.py`
- `shared/clients/*.py`
- `tests/integration/*.py`
- `tests/e2e/*.py`

#### 6. Quality Assurance Team (tester + reviewer agents)
**Responsibilities**:
- Unit test coverage
- Integration test suites
- Load testing scripts
- Security scanning
- Code review

**Deliverables**:
- Comprehensive test suites
- Performance benchmarks
- Security audit reports

## Build Execution Plan

### Stage 1: Foundation (Parallel Execution)
```
Infrastructure Team → Docker Compose + Base Services
     ↓
  [postgres, redis, nats, qdrant containers]
```

### Stage 2: Core Services (Sequential after Stage 1)
```
AUBS Team → FastAPI service + Dolphin integration
     ↓
Agent Development Team → Base contracts + Triage Agent
     ↓
  [Basic orchestration pipeline working]
```

### Stage 3: Agent Expansion (Parallel Execution)
```
Agent Team → Vision | Deadline | Task | Context
     ↓
  [All agents implemented]
```

### Stage 4: User Interface (Parallel with Stage 3)
```
Frontend Team → UI-TARS + Open-WebUI components
     ↓
  [Visual debugging and monitoring UI]
```

### Stage 5: Integration (Sequential after Stage 3 & 4)
```
Integration Team → Wire all components + E2E tests
     ↓
QA Team → Validate entire system
     ↓
  [Production-ready system]
```

## Swarm Coordination Commands

### Initialize Build Swarm
```bash
# Using Flow-Nexus for distributed build
mcp__flow-nexus__swarm_init({
  "topology": "hierarchical",
  "maxAgents": 20,
  "strategy": "specialized"
})
```

### Spawn Specialized Teams
```bash
# Infrastructure Team
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["docker", "kubernetes", "devops"]})
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["bash", "networking", "databases"]})

# AUBS Team
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["python", "fastapi", "async"]})
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["dag", "orchestration", "dolphin"]})

# Agent Development Team
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["ml", "llm", "transformers"]})
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["vision", "ocr", "gpu"]})
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["nlp", "context", "rag"]})

# Frontend Team
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["react", "typescript", "ui"]})
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["visualization", "debugging", "uitars"]})

# Integration Team
mcp__flow-nexus__agent_spawn({"type": "coder", "capabilities": ["mcp", "integration", "testing"]})

# QA Team
mcp__flow-nexus__agent_spawn({"type": "tester", "capabilities": ["pytest", "load-testing", "security"]})
mcp__flow-nexus__agent_spawn({"type": "reviewer", "capabilities": ["code-review", "architecture"]})
```

### Orchestrate Tasks
```bash
# Stage 1: Infrastructure
mcp__flow-nexus__task_orchestrate({
  "task": "Create Docker Compose configuration with PostgreSQL, Redis, NATS, Qdrant, Ollama",
  "strategy": "parallel",
  "maxAgents": 3,
  "priority": "high"
})

# Stage 2: AUBS Core
mcp__flow-nexus__task_orchestrate({
  "task": "Implement AUBS FastAPI service with Dolphin DAG builder and action router",
  "strategy": "sequential",
  "maxAgents": 2,
  "priority": "critical"
})

# Stage 3: Agents (parallel)
mcp__flow-nexus__task_orchestrate({
  "task": "Implement all 5 agents: Triage, Vision, Deadline, Task, Context",
  "strategy": "adaptive",
  "maxAgents": 5,
  "priority": "high"
})

# Stage 4: Frontend (parallel with agents)
mcp__flow-nexus__task_orchestrate({
  "task": "Build UI-TARS integration and Open-WebUI components",
  "strategy": "parallel",
  "maxAgents": 2,
  "priority": "medium"
})

# Stage 5: Integration
mcp__flow-nexus__task_orchestrate({
  "task": "Wire MCP tools, NATS events, email ingestion, and create E2E tests",
  "strategy": "sequential",
  "maxAgents": 3,
  "priority": "high"
})
```

## File Generation Strategy

### Phase 1: Configuration Files
1. `requirements.txt` - Python dependencies
2. `docker-compose.yml` - Infrastructure services
3. `.env.example` - Environment variables template
4. `dolphin-config.yaml` - Dolphin scheduler config
5. `pyproject.toml` - Python project config

### Phase 2: Core Implementation
1. `aubs/src/main.py` - FastAPI entry point
2. `aubs/src/orchestrator.py` - AUBS orchestrator
3. `aubs/src/dag_builder.py` - Dolphin DAG builder
4. `agents/base/agent_contract.py` - Base agent interface
5. `shared/models.py` - Pydantic models

### Phase 3: Agents
1. `agents/triage/agent.py` - Triage agent
2. `agents/vision/agent.py` - Vision agent
3. `agents/deadline/agent.py` - Deadline scanner
4. `agents/task/agent.py` - Task categorizer
5. `agents/context/agent.py` - Context agent (critical)

### Phase 4: Frontend
1. `uitars/src/UITARSPanel.tsx` - Main UI component
2. `uitars/src/config.ts` - UI-TARS configuration
3. `openwebui/components/EmailDashboard.tsx` - Email dashboard
4. `openwebui/components/DebugPanel.tsx` - Debug panel

### Phase 5: Integration
1. `mcp-tools/task_manager.py` - Task MCP tool
2. `mcp-tools/calendar.py` - Calendar MCP tool
3. `shared/clients/dolphin_client.py` - Dolphin client
4. `shared/clients/nats_client.py` - NATS client
5. `tests/integration/test_email_pipeline.py` - E2E test

## Quality Gates

### Per-Component Gates
- [ ] Type hints on all functions
- [ ] Unit tests with >80% coverage
- [ ] Integration tests for public APIs
- [ ] Docstrings on all classes/functions
- [ ] No security vulnerabilities (Bandit scan)
- [ ] Code formatted (Black)
- [ ] Imports sorted (isort)
- [ ] Linted (Flake8)

### Integration Gates
- [ ] All services start successfully
- [ ] Health checks passing
- [ ] Database migrations applied
- [ ] NATS topics created
- [ ] Qdrant collections initialized
- [ ] Dolphin DAG can be submitted
- [ ] UI-TARS connects to Dolphin

### System Gates
- [ ] Email -> Task creation works E2E
- [ ] All 5 agents execute successfully
- [ ] Context Agent uses correct model
- [ ] UI-TARS shows execution timeline
- [ ] Actions route to correct MCP tools
- [ ] Load test passes (100 emails)

## Development Workflow

1. **Agent spawns for specific task**
2. **Agent generates code**
3. **Auto-format with Black/isort**
4. **Run type checking (mypy)**
5. **Run tests (pytest)**
6. **Security scan (bandit)**
7. **Code review by reviewer agent**
8. **If approved → commit**
9. **If rejected → fix and retry**

## Monitoring & Progress Tracking

### Real-time Progress Dashboard
- Tasks completed / total
- Current active agents
- Code files generated
- Test coverage percentage
- Build health status

### Metrics
- Lines of code written
- Test coverage %
- Type hint coverage %
- Security issues found/fixed
- Time to completion

## Risk Management

### Critical Path Items
1. Context Agent must use oss-120b (NO FALLBACK)
2. Dolphin scheduler must be properly configured
3. GPU support for Vision Agent required
4. NATS event streaming must be reliable

### Fallback Strategies
- If Dolphin unavailable → Use Celery as temp replacement
- If UI-TARS build fails → Use basic logging UI
- If GPU unavailable → CPU-only vision (slower)
- If oss-120b unavailable → FAIL Context Agent (by design)

## Success Criteria

### Code Quality
- 100% type hints
- >85% test coverage
- Zero high-severity security issues
- All linting rules passing

### Functionality
- All PRD requirements implemented
- All 5 agents working
- E2E email processing functional
- UI-TARS visualization working

### Performance
- Email processing < 30s
- Context Agent < 10s
- UI latency < 100ms
- Handles 500 emails/day

## Next Action

Run the swarm initialization to begin automated build:

```bash
# This will be executed by Claude Code to orchestrate the entire build
Task(subagent_type="swarm-coordinator", prompt="Initialize hierarchical swarm with 20 agents to build ChiliHead OpsManager v2.1 following the BUILD_ORCHESTRATOR.md plan")
```
