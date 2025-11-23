# Dolphin Scheduler Configuration

Complete distributed task orchestration system for email processing in the ohhhmail platform.

## Directory Structure

```
dolphin/
├── README.md                    # This file
├── CONFIGURATION_SUMMARY.md     # Detailed configuration documentation
├── config/
│   ├── dolphin-config.yaml      # Main Dolphin server configuration
│   └── worker-config.yaml       # Worker node configuration
├── dags/
│   ├── __init__.py              # DAG package initialization
│   └── email_processing.py      # Email processing DAG definition
└── plugins/
    ├── __init__.py              # Plugin package initialization
    └── uitars_plugin.py         # UI-TARS integration plugin
```

## Quick Start

### Prerequisites
- PostgreSQL 12+ for state persistence
- NATS 2.10+ with JetStream for messaging
- Python 3.9+ for DAG and plugin code

### Configuration Steps

1. **Set Environment Variables**
   ```bash
   export ENVIRONMENT=production
   export DB_HOST=postgres.example.com
   export DB_USER=dolphin
   export DB_PASSWORD=your_secure_password
   export NATS_URL=nats://nats:4222
   export ANTHROPIC_API_KEY=your_api_key
   export OPENAI_API_KEY=your_api_key
   ```

2. **Start Dolphin Server**
   ```bash
   dolphin-scheduler \
     --config config/dolphin-config.yaml \
     --port 12345 \
     --workers 4
   ```

3. **Deploy Workers**
   ```bash
   # CPU Workers
   dolphin-worker \
     --config config/worker-config.yaml \
     --group cpu_workers \
     --workers 4

   # GPU Workers
   dolphin-worker \
     --config config/worker-config.yaml \
     --group gpu_workers \
     --workers 2

   # Critical Workers
   dolphin-worker \
     --config config/worker-config.yaml \
     --group critical_workers \
     --workers 2
   ```

## Configuration Files

### dolphin-config.yaml (339 lines)
Main server configuration with:
- Database (PostgreSQL)
- Message broker (NATS JetStream)
- Worker groups (CPU, GPU, Critical)
- Task execution policies
- DAG configuration
- Resource management
- Monitoring and logging
- Security settings
- Integration endpoints

**Key Sections**:
- `database`: PostgreSQL connection pooling
- `message_broker`: NATS JetStream configuration
- `worker_groups`: 3 specialized worker pools
- `task_execution`: Timeout, retry, XCom settings
- `monitoring`: Prometheus metrics, logging
- `integrations`: UI-TARS, agents, Supabase

### worker-config.yaml (360 lines)
Worker node configuration with:
- Task polling and prefetching
- Task execution settings
- Resource allocation (CPU, memory, GPU)
- Health check configuration
- Communication settings
- Logging and log aggregation
- Checkpoint management
- Plugin configuration
- Security (TLS, auth)

**Key Sections**:
- `task_execution`: Concurrency, isolation, timeouts
- `resources`: CPU, memory, GPU limits
- `health_check`: Metrics and alerts
- `checkpoints`: Creation and recovery
- `plugins`: UI-TARS integration setup

## DAG Configuration

### Email Processing DAG
Complete task graph for email processing with 5 agents:

```
[Triage Agent]
      |
      +-------+-------+
      |       |       |
[Vision] [Deadline] [Task]
      |       |       |
      +-------+-------+
              |
      [Context Agent] ← CRITICAL
              |
          [Actions]
```

#### Agent Details:

| Agent | Type | Pool | Timeout | Retries | Critical |
|-------|------|------|---------|---------|----------|
| Triage | Text Classification | cpu_workers | 15-30s | 3 | No |
| Vision | Image Analysis | gpu_workers | 30s | 3 | No |
| Deadline | Deadline Extraction | cpu_workers | 15-30s | 3 | No |
| Task | Task Categorization | cpu_workers | 15-30s | 3 | No |
| Context | Synthesis & Routing | critical_workers | 30s | 0 | **YES** |

**Key Features**:
- Conditional Vision agent (only if attachments)
- XCom data passing between tasks
- Critical context agent with no fallback
- SLA enforcement on critical tasks
- Exponential backoff retry policy

## Plugin System

### UITARSPlugin (634 lines)
Integrates with UI-TARS for execution monitoring:

#### Components:

1. **CheckpointManager**
   - Creates checkpoints before task execution
   - Updates checkpoints during execution
   - Captures screenshots on errors
   - Retrieves checkpoint data
   - Local + cloud synchronization

2. **ExecutionLogger**
   - Task start/completion logging
   - Error tracking with tracebacks
   - Resource usage monitoring
   - JSONL format output
   - Automatic log rotation

3. **UITARSPlugin**
   - Hooks: on_task_start, on_task_success, on_task_failure
   - Resource monitoring
   - Error screenshot capture
   - Integration with UI-TARS API

## Execution Flow

### Task Execution Sequence:
1. Email arrives and triggers DAG creation
2. Triage Agent classifies email
3. Parallel execution (conditional):
   - Vision Agent processes attachments (if present)
   - Deadline Agent extracts deadlines
   - Task Agent categorizes tasks
4. Context Agent synthesizes all outputs
5. Routing actions executed

### Data Flow (XCom):
```
Email Input
    ↓
[Triage] → output
    ↓
    ├→ [Vision] → output ─┐
    ├→ [Deadline] → output ├→ [Context] → final_action
    └→ [Task] → output ────┘
```

## Monitoring

### Health Checks
- Server health: Port 12346 (HTTP)
- Worker health: Port 9091 (Prometheus)
- Check interval: 30 seconds
- Timeout: 10 seconds

### Metrics
- Task execution time
- Task success/failure rates
- Resource utilization
- XCom data sizes
- Worker availability

### Logging
- Format: JSON (structured)
- Level: Configurable (DEBUG, INFO, WARNING, ERROR)
- Storage: File + aggregation service
- Retention: 30 days

## Integration Points

### Services
- **PostgreSQL**: State persistence and history
- **NATS**: Inter-service messaging
- **UI-TARS**: Checkpoint and execution monitoring
- **Agents Service**: Email processing agents
- **Supabase**: Extended state and historical context

### APIs
- **Dolphin Server**: REST API on port 12345
- **Worker Health**: Prometheus metrics on port 9091
- **UI-TARS API**: Checkpoint management

## Security

### Authentication
- OAuth2 for server access
- Token-based worker authentication
- Token refresh every 3600s

### Authorization
- RBAC (Role-Based Access Control)
- Default user role
- Task-level permissions

### Encryption
- TLS/SSL for transport
- AES-256-GCM for data at rest
- Secret management via environment

## Performance Tuning

### Connection Pooling
- Min size: 5
- Max size: 20
- Idle timeout: 300s

### Caching
- Redis-based cache
- TTL: 3600s
- LRU eviction policy

### Task Batching
- Batch size: 10 tasks
- Flush interval: 5 seconds
- Async processing enabled

## Troubleshooting

### Common Issues

**Worker not connecting:**
- Check NATS connectivity
- Verify worker auth token
- Check firewall rules

**Tasks timing out:**
- Increase timeout in config
- Check agent service availability
- Monitor resource usage

**Checkpoint failures:**
- Verify UI-TARS availability
- Check storage permissions
- Review checkpoint logs

### Debug Mode
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
export LOG_EXECUTION_DETAILS=true
```

## Configuration Examples

### Development Setup
```yaml
environment: development
log_level: DEBUG
worker_groups:
  cpu_workers:
    worker_count: 2
  gpu_workers:
    worker_count: 1
  critical_workers:
    worker_count: 1
```

### Production Setup
```yaml
environment: production
log_level: INFO
worker_groups:
  cpu_workers:
    worker_count: 8
  gpu_workers:
    worker_count: 4
  critical_workers:
    worker_count: 2
```

## Resources

- **Main Documentation**: See `CONFIGURATION_SUMMARY.md`
- **DAG Definitions**: `dags/email_processing.py`
- **Plugin Code**: `plugins/uitars_plugin.py`
- **AUBS Integration**: `../aubs/src/dag_builder.py`

## Related Projects

- **AUBS**: Agent Unit Build System (`../aubs/`)
- **Agents**: Email processing agents (`../agents/`)
- **UI-TARS**: Execution monitoring (`../uitars/`)
- **Shared**: Common models (`../shared/`)

## File Statistics

| File | Lines | Type | Status |
|------|-------|------|--------|
| dolphin-config.yaml | 339 | YAML | ✓ Valid |
| worker-config.yaml | 360 | YAML | ✓ Valid |
| __init__.py (dags) | 13 | Python | ✓ Valid |
| email_processing.py | 465 | Python | ✓ Valid |
| __init__.py (plugins) | 16 | Python | ✓ Valid |
| uitars_plugin.py | 634 | Python | ✓ Valid |
| **Total** | **1,827** | Mixed | **✓ All Valid** |

## Notes

- All YAML files validated
- All Python files syntax-checked
- Configuration supports hot-reload
- Environment variables override defaults
- Checkpoint system enables recovery
- Critical tasks cannot be retried or fallback

## Maintenance

### Regular Tasks
- Monitor worker health
- Review execution logs weekly
- Backup checkpoint data daily
- Rotate logs as configured
- Update agent configurations

### Updates
- Non-breaking updates can be deployed without restart
- Configuration changes via hot-reload
- Worker group scaling supported
- Plugin updates without downtime

---

**Last Updated**: November 23, 2025
**Configuration Version**: 1.0
**Status**: Production Ready
