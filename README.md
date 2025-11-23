# ChiliHead OpsManager v2.1 - OHHH1MAIL Platform

AI-powered restaurant operations management platform leveraging ByteDance Dolphin scheduler and UI-TARS visual debugging.

## Overview

ChiliHead OpsManager automates restaurant email processing using specialized AI agents orchestrated through Apache DolphinScheduler, with visual debugging capabilities via UI-TARS Desktop.

### Key Features

- **Multi-Agent Email Processing**: 5 specialized AI agents (Triage, Vision, Deadline, Task, Context)
- **Visual Workflow Debugging**: UI-TARS Desktop integration for execution replay and debugging
- **Enterprise Orchestration**: ByteDance Dolphin scheduler for fault-tolerant DAG execution
- **Contextual Intelligence**: 30+ day memory with vector search for pattern recognition
- **Automated Actions**: MCP tools for task creation, calendar scheduling, and notifications

## Architecture

```
Open-WebUI → AUBS → Dolphin Scheduler → Agent Workers → Actions
     ↓           ↓            ↓
UI-TARS    NATS Events  PostgreSQL/Redis/Qdrant
```

## Quick Start

### Prerequisites

- Docker Desktop with WSL2 (Windows) or Docker Engine (Linux/Mac)
- NVIDIA GPU with CUDA support (for Vision Agent)
- 16GB+ RAM
- Python 3.11+
- Node.js 18+

### Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd ohhh1mail
   ```

2. **Set Up Environment**
   ```bash
   cp infrastructure/docker/.env.example infrastructure/docker/.env
   # Edit .env with your configuration
   ```

3. **Start Infrastructure**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

4. **Initialize Database**
   ```bash
   ./infrastructure/scripts/init-db.sh
   ```

5. **Set Up Ollama Models**
   ```bash
   ./infrastructure/scripts/setup-ollama.sh
   ```

6. **Access Services**
   - Open-WebUI: http://localhost:3000
   - Dolphin Scheduler: http://localhost:12345
   - UI-TARS: http://localhost:8080
   - AUBS API: http://localhost:5000

## System Components

### AUBS (Autonomous Unified Business System)
Central orchestrator that builds Dolphin DAGs, monitors execution, and routes actions to MCP tools.

**Location**: `aubs/`

### Agent Workers

1. **Triage Agent** (`agents/triage/`)
   - Model: llama-3.2-8b-instruct
   - Purpose: Email categorization and routing
   - Output: Category, urgency, vision requirement

2. **Vision Agent** (`agents/vision/`)
   - GPU-accelerated OCR and image processing
   - Purpose: Extract data from invoices, receipts, PDFs
   - Output: Structured data from images

3. **Deadline Scanner** (`agents/deadline/`)
   - Purpose: Extract dates and deadlines
   - Output: Parsed datetime objects with context

4. **Task Categorizer** (`agents/task/`)
   - Purpose: Identify action items
   - Output: Task list with priorities

5. **Context Agent** (`agents/context/`)
   - Model: oss-120b (NO FALLBACK)
   - Purpose: Synthesize all agent outputs with historical context
   - Output: Recommendations and risk assessment

### Infrastructure Services

- **Dolphin Scheduler**: DAG-based workflow orchestration
- **PostgreSQL**: Persistent data storage
- **Redis**: State management and caching
- **NATS JetStream**: Event streaming
- **Qdrant**: Vector database for context retrieval
- **Ollama**: Local LLM hosting

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# With coverage
pytest --cov=aubs --cov=agents --cov-report=html
```

### Code Quality

```bash
# Format code
black .
isort .

# Type checking
mypy aubs/ agents/ shared/

# Linting
flake8 aubs/ agents/ shared/

# Security scan
bandit -r aubs/ agents/
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `DOLPHIN_URL`: Dolphin scheduler API endpoint
- `OLLAMA_BASE_URL`: Ollama API endpoint
- `POSTGRES_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `NATS_URL`: NATS server URL
- `QDRANT_URL`: Qdrant API endpoint

### Agent Configuration

Agent-specific configuration in `aubs/src/config.py`:

```python
AGENT_CONFIG = {
    "triage": {"model": "llama-3.2-8b-instruct", "timeout": 15},
    "vision": {"model": "llama-vision", "gpu": True, "timeout": 30},
    "context": {"model": "oss-120b", "fallback": False, "timeout": 30}
}
```

## Deployment

### Docker Compose (Development)

```bash
cd infrastructure/docker
docker-compose up -d
```

### Kubernetes (Production)

```bash
cd infrastructure/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f .
```

## Monitoring

### Health Checks

- AUBS: `http://localhost:5000/health`
- Dolphin: `http://localhost:12345/dolphinscheduler/health`
- Each service exposes `/health` endpoint

### Metrics

- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3001`
- UI-TARS debugging: `http://localhost:8080`

## Documentation

- [Architecture](docs/architecture.md)
- [Agent Specifications](docs/agent-specs.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## Project Status

- [x] PRD Complete
- [x] Implementation Plan
- [ ] Infrastructure Setup
- [ ] AUBS Core Implementation
- [ ] Agent Development
- [ ] UI-TARS Integration
- [ ] E2E Testing
- [ ] Production Deployment

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

## Support

For issues and questions:
- GitHub Issues: [Repository Issues]
- Documentation: [docs/](docs/)
- Email: [support email]
