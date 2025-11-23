# Product Requirements Document (PRD)
## ChiliHead OpsManager v2.1 - OHHH1MAIL Platform
### Leveraging ByteDance Dolphin & UI-TARS

**Version:** 2.1  
**Date:** November 2025  
**Status:** Final Architecture with ByteDance Stack  
**Stack Decision:** Dolphin + UI-TARS + AUBS

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack Rationale](#2-technology-stack-rationale)
3. [System Architecture](#3-system-architecture)
4. [Dolphin Integration](#4-dolphin-integration)
5. [UI-TARS Integration](#5-ui-tars-integration)
6. [AUBS Orchestration Layer](#6-aubs-orchestration)
7. [Agent Specifications](#7-agent-specifications)
8. [Data Flow & Event Architecture](#8-data-flow)
9. [Deployment Architecture](#9-deployment)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

ChiliHead OpsManager v2.1 adopts ByteDance's production-proven AI infrastructure:

- **Dolphin**: Distributed task scheduling platform for resilient agent orchestration
- **UI-TARS**: Visual workflow debugging and automation monitoring
- **AUBS**: Your custom business logic layer coordinating the system

This stack provides enterprise-grade reliability with visual debugging capabilities specifically designed for AI agent workflows.

---

## 2. Technology Stack Rationale

### Why Dolphin?

ByteDance Dolphin provides:
- **DAG-based workflow orchestration** perfect for agent pipelines
- **Built-in fault tolerance** with retry logic and dead letter queues
- **Resource management** for GPU/CPU allocation per agent
- **Native distributed execution** for parallel agent processing
- **Task dependency management** ensuring Context Agent runs after others

### Why UI-TARS?

UI-TARS Desktop provides:
- **Visual workflow replay** to see exactly what agents decided
- **Step-by-step debugging** with screenshots at each decision point
- **Element inspection** for understanding agent outputs
- **Performance profiling** to identify bottlenecks

### Stack Comparison

| Component | Original Plan | ByteDance Stack | Benefit |
|-----------|--------------|-----------------|---------|
| Orchestration | LangGraph | Dolphin | Production-tested at TikTok scale |
| Debugging | LangSmith | UI-TARS | Visual replay built for automation |
| Runtime | Custom Python | Dolphin Workers | Fault isolation per agent |
| Monitoring | Grafana | UI-TARS + Native | Integrated visual debugging |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Open-WebUI                         │
│  ┌─────────────────────────────────────────────┐    │
│  │  Tabs: Email | Tasks | Debug | Analytics   │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │        UI-TARS Desktop (Embedded)           │    │
│  │    Visual Debugging & Workflow Monitor      │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              AUBS Business Logic Layer              │
│         (Restaurant-Specific Orchestration)         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Dolphin Scheduler Platform             │
│  ┌──────────────────────────────────────────────┐   │
│  │  DAG Engine | Task Queue | Resource Manager  │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐       ┌──────────────────┐
│  Dolphin Workers │       │  Dolphin Workers │
│  ┌────────────┐  │       │  ┌────────────┐  │
│  │   Triage   │  │       │  │   Vision   │  │
│  │   Agent    │  │       │  │   Agent    │  │
│  └────────────┘  │       │  └────────────┘  │
│  ┌────────────┐  │       │  ┌────────────┐  │
│  │  Deadline  │  │       │  │  Context   │  │
│  │   Agent    │  │       │  │   Agent    │  │
│  └────────────┘  │       │  └────────────┘  │
└──────────────────┘       └──────────────────┘
```

### 3.2 Component Relationships

```python
# Architecture Definition
ARCHITECTURE = {
    "ui_layer": {
        "platform": "Open-WebUI",
        "components": [
            "SnappyMail (Email Client)",
            "UI-TARS Desktop (Debugging)",
            "AUBS Dashboard (Control Panel)"
        ]
    },
    "orchestration_layer": {
        "business_logic": "AUBS",
        "execution_engine": "Dolphin",
        "scheduling": "Dolphin DAG Scheduler"
    },
    "execution_layer": {
        "workers": "Dolphin Worker Nodes",
        "agents": [
            "Triage", "Vision", "Deadline", 
            "Task", "Context"
        ]
    },
    "persistence_layer": {
        "state": "Redis",
        "events": "PostgreSQL",
        "vectors": "Qdrant",
        "messages": "NATS JetStream"
    }
}
```

---

## 4. Dolphin Integration

### 4.1 Dolphin Configuration

```yaml
# dolphin-config.yaml
dolphin:
  server:
    port: 12345
    database:
      type: postgresql
      host: postgres
      port: 5432
      database: dolphin_scheduler
    
  workers:
    - name: agent-worker-1
      type: AGENT_EXECUTOR
      resources:
        cpu: 4
        memory: 8192
        gpu: 1  # For Vision Agent
    
    - name: agent-worker-2
      type: AGENT_EXECUTOR
      resources:
        cpu: 4
        memory: 8192
        gpu: 0  # CPU-only agents
  
  task_types:
    - name: TRIAGE_TASK
      worker_group: agent-worker-2
      timeout: 15
      retry_times: 3
      
    - name: VISION_TASK
      worker_group: agent-worker-1
      timeout: 30
      retry_times: 2
      
    - name: CONTEXT_TASK
      worker_group: agent-worker-2
      timeout: 30
      retry_times: 1  # No retry for Context Agent
```

### 4.2 AUBS → Dolphin DAG Definition

```python
from dolphin.dag import DAG, Task
from datetime import datetime, timedelta

class EmailProcessingDAG:
    """
    Dolphin DAG for email processing pipeline
    """
    
    def __init__(self):
        self.dag = DAG(
            dag_id="email_processing",
            description="Process restaurant emails through agents",
            schedule_interval=None,  # Triggered by email arrival
            default_args={
                "owner": "AUBS",
                "depends_on_past": False,
                "start_date": datetime(2025, 11, 1),
                "retries": 1,
                "retry_delay": timedelta(seconds=30)
            }
        )
        
    def build_dag(self, email_data: dict):
        """Build DAG for specific email"""
        
        # Triage always runs first
        triage_task = Task(
            task_id="triage",
            task_type="TRIAGE_TASK",
            params={
                "email_id": email_data["id"],
                "body": email_data["body"],
                "subject": email_data["subject"]
            },
            dag=self.dag
        )
        
        # Vision runs conditionally
        vision_task = Task(
            task_id="vision",
            task_type="VISION_TASK",
            params={
                "email_id": email_data["id"],
                "attachments": email_data.get("attachments", [])
            },
            dag=self.dag,
            trigger_rule="ONE_SUCCESS"  # Only if triage says needed
        )
        
        # Deadline scanner runs in parallel with vision
        deadline_task = Task(
            task_id="deadline",
            task_type="DEADLINE_TASK",
            params={
                "email_id": email_data["id"],
                "body": email_data["body"]
            },
            dag=self.dag
        )
        
        # Context runs after all others complete
        context_task = Task(
            task_id="context",
            task_type="CONTEXT_TASK",
            params={
                "email_id": email_data["id"],
                "triage_output": "{{ task_instance.xcom_pull(task_ids='triage') }}",
                "vision_output": "{{ task_instance.xcom_pull(task_ids='vision') }}",
                "deadline_output": "{{ task_instance.xcom_pull(task_ids='deadline') }}"
            },
            dag=self.dag,
            trigger_rule="ALL_DONE"  # Run even if some fail
        )
        
        # Define dependencies
        triage_task >> [vision_task, deadline_task]
        [vision_task, deadline_task] >> context_task
        
        return self.dag
```

### 4.3 Dolphin Worker Implementation

```python
from dolphin.worker import Worker, task
import asyncio

class AgentWorker(Worker):
    """
    Dolphin worker that executes agent tasks
    """
    
    def __init__(self):
        super().__init__()
        self.agents = self._initialize_agents()
        
    @task(name="TRIAGE_TASK")
    async def execute_triage(self, params: dict):
        """Execute Triage Agent"""
        agent = self.agents["triage"]
        
        # UI-TARS checkpoint
        await self.checkpoint("triage_start", params)
        
        result = await agent.process({
            "email_body": params["body"],
            "subject": params["subject"]
        })
        
        # UI-TARS checkpoint
        await self.checkpoint("triage_complete", result)
        
        # Store in XCom for downstream tasks
        return {
            "category": result["category"],
            "urgency": result["urgency"],
            "requires_vision": result["requires_vision"],
            "confidence": result["confidence"]
        }
        
    @task(name="CONTEXT_TASK")
    async def execute_context(self, params: dict):
        """
        Execute Context Agent - NO FALLBACK
        This task fails if the model is unavailable
        """
        agent = self.agents["context"]
        
        # Retrieve context from vector store
        context = await self.retrieve_context(params["email_id"])
        
        # UI-TARS checkpoint with full context
        await self.checkpoint("context_synthesis_start", {
            "inputs": params,
            "retrieved_context": context
        })
        
        try:
            result = await agent.process({
                "triage": params["triage_output"],
                "vision": params.get("vision_output"),
                "deadline": params["deadline_output"],
                "historical_context": context
            })
        except ModelUnavailableError:
            # NO FALLBACK - Context Agent requires best model
            raise CriticalTaskFailure("Context Agent requires OSS-120B")
            
        await self.checkpoint("context_synthesis_complete", result)
        
        return result
```

---

## 5. UI-TARS Integration

### 5.1 UI-TARS Configuration

```javascript
// ui-tars-config.js
const UITARSConfig = {
    // Connect to Dolphin for workflow data
    dolphin: {
        api: "http://dolphin:12345/api",
        ws: "ws://dolphin:12345/ws"
    },
    
    // Visualization settings
    display: {
        layout: "hierarchical",  // Shows DAG structure
        animation: true,
        screenshot_capture: true,
        performance_metrics: true
    },
    
    // Agent monitoring
    agents: {
        triage: {
            color: "#4CAF50",
            icon: "filter_list",
            track_decisions: true
        },
        vision: {
            color: "#2196F3", 
            icon: "visibility",
            track_extractions: true
        },
        context: {
            color: "#FF9800",
            icon: "psychology",
            track_synthesis: true
        }
    },
    
    // Checkpoint configuration
    checkpoints: {
        capture_screenshots: true,
        log_decisions: true,
        track_performance: true,
        store_intermediate_results: true
    }
};
```

### 5.2 UI-TARS Embedded Component

```typescript
// UITARSPanel.tsx - Embedded in Open-WebUI
import React, { useEffect, useState } from 'react';
import { UITARSDesktop } from '@bytedance/ui-tars-desktop';

export const UITARSPanel: React.FC = () => {
    const [workflow, setWorkflow] = useState(null);
    const [selectedExecution, setSelectedExecution] = useState(null);
    
    useEffect(() => {
        // Connect to Dolphin WebSocket for real-time updates
        const ws = new WebSocket('ws://dolphin:12345/ws');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'WORKFLOW_UPDATE') {
                setWorkflow(data.workflow);
            }
        };
        
        return () => ws.close();
    }, []);
    
    return (
        <div className="ui-tars-panel">
            <UITARSDesktop
                config={UITARSConfig}
                workflow={workflow}
                onExecutionSelect={setSelectedExecution}
                features={{
                    replay: true,  // Enable execution replay
                    debug: true,   // Enable step-through debugging
                    profiling: true,  // Performance profiling
                    export: true   // Export execution traces
                }}
            />
            
            {selectedExecution && (
                <ExecutionDetail
                    execution={selectedExecution}
                    showScreenshots={true}
                    showDecisionTree={true}
                    showPerformanceMetrics={true}
                />
            )}
        </div>
    );
};
```

### 5.3 Visual Debugging Features

```python
class UITARSIntegration:
    """
    Integration between agents and UI-TARS visualization
    """
    
    async def checkpoint(
        self,
        checkpoint_name: str,
        data: dict,
        screenshot: bool = False
    ):
        """Create UI-TARS checkpoint for visualization"""
        
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "checkpoint": checkpoint_name,
            "data": data,
            "metrics": {
                "memory_usage": self.get_memory_usage(),
                "cpu_usage": self.get_cpu_usage(),
                "gpu_usage": self.get_gpu_usage() if self.has_gpu else None
            }
        }
        
        if screenshot:
            # Capture current state visualization
            checkpoint_data["screenshot"] = await self.capture_screenshot()
            
        # Send to UI-TARS
        await self.ui_tars_client.send_checkpoint(checkpoint_data)
        
        # Also log to Dolphin
        await self.dolphin_client.log_checkpoint(checkpoint_data)
```

---

## 6. AUBS Orchestration Layer

### 6.1 AUBS Implementation with Dolphin

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class AUBSConfig:
    """AUBS configuration"""
    dolphin_url: str = "http://dolphin:12345"
    ui_tars_url: str = "http://uitars:8080"
    confidence_threshold: float = 0.9
    max_retries: int = 3

class AUBS:
    """
    Autonomous Unified Business System
    Coordinates Dolphin DAGs for restaurant operations
    """
    
    def __init__(self, config: AUBSConfig):
        self.config = config
        self.dolphin = DolphinClient(config.dolphin_url)
        self.ui_tars = UITARSClient(config.ui_tars_url)
        self.dag_builder = EmailProcessingDAG()
        
    async def process_email(self, email: dict) -> dict:
        """
        Main entry point for email processing
        """
        
        # Start UI-TARS session
        session = await self.ui_tars.start_session({
            "type": "email_processing",
            "email_id": email["id"],
            "started_at": datetime.now()
        })
        
        try:
            # Build DAG for this email
            dag = self.dag_builder.build_dag(email)
            
            # Determine if we need Vision (saves money)
            if not self._needs_vision(email):
                dag.remove_task("vision")
                
            # Submit to Dolphin
            execution = await self.dolphin.submit_dag(
                dag=dag,
                params={
                    "email": email,
                    "session_id": session.id
                }
            )
            
            # Monitor execution
            result = await self._monitor_execution(execution, session)
            
            # Route to appropriate outputs
            actions = await self._route_actions(result)
            
            # Complete UI-TARS session
            await self.ui_tars.complete_session(
                session_id=session.id,
                result=result,
                actions=actions
            )
            
            return {
                "status": "success",
                "email_id": email["id"],
                "actions": actions,
                "execution_id": execution.id
            }
            
        except Exception as e:
            await self.ui_tars.fail_session(
                session_id=session.id,
                error=str(e)
            )
            raise
            
    def _needs_vision(self, email: dict) -> bool:
        """Determine if Vision Agent is needed"""
        
        # No attachments = no vision
        if not email.get("attachments"):
            return False
            
        # Check for invoice/receipt keywords
        keywords = ["invoice", "receipt", "bill", "statement", "po#"]
        if any(kw in email.get("subject", "").lower() for kw in keywords):
            return True
            
        return False
        
    async def _monitor_execution(
        self,
        execution: DolphinExecution,
        session: UITARSSession
    ) -> dict:
        """Monitor Dolphin execution with UI-TARS updates"""
        
        while not execution.is_complete():
            status = await execution.get_status()
            
            # Update UI-TARS visualization
            await self.ui_tars.update_session(
                session_id=session.id,
                status=status,
                tasks=execution.get_task_statuses()
            )
            
            # Check for failures
            if status == "FAILED":
                failed_tasks = execution.get_failed_tasks()
                
                # Context Agent failure is critical
                if "context" in failed_tasks:
                    raise CriticalFailure("Context Agent failed - no fallback")
                    
                # Other failures might be recoverable
                for task in failed_tasks:
                    if task != "vision":  # Vision is optional
                        await self._handle_task_failure(task, execution)
                        
            await asyncio.sleep(1)
            
        # Get final results
        return await execution.get_results()
```

### 6.2 Action Routing

```python
class ActionRouter:
    """Routes AUBS decisions to appropriate channels"""
    
    def __init__(self):
        self.mcp_tools = self._initialize_mcp_tools()
        
    async def route(self, context_output: dict) -> List[dict]:
        """Route based on Context Agent recommendations"""
        
        actions = []
        confidence = context_output["confidence"]
        
        for recommendation in context_output["recommendations"]:
            action_type = recommendation["type"]
            
            # High-risk actions need high confidence
            if self._is_high_risk(action_type) and confidence < 0.95:
                actions.append({
                    "type": "human_review",
                    "action": recommendation,
                    "reason": f"Confidence {confidence} below threshold"
                })
                continue
                
            # Route to appropriate tool
            if action_type == "create_task":
                result = await self.mcp_tools["task"].create(
                    title=recommendation["title"],
                    description=recommendation["description"],
                    due_date=recommendation.get("due_date"),
                    assignee=recommendation.get("assignee")
                )
                actions.append(result)
                
            elif action_type == "schedule_event":
                result = await self.mcp_tools["calendar"].schedule(
                    title=recommendation["title"],
                    time=recommendation["time"],
                    attendees=recommendation.get("attendees", [])
                )
                actions.append(result)
                
            elif action_type == "send_notification":
                result = await self.mcp_tools["sms"].send(
                    to=recommendation["recipient"],
                    message=recommendation["message"],
                    urgency=recommendation.get("urgency", "normal")
                )
                actions.append(result)
                
        return actions
```

---

## 7. Agent Specifications

### 7.1 Agent Contracts for Dolphin Workers

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Literal, Optional

class AgentContract(BaseModel):
    """Base contract all agents must follow"""
    
    class Input(BaseModel):
        email_id: str
        session_id: str
        checkpoint_enabled: bool = True
        
    class Output(BaseModel):
        agent_type: str
        findings: dict
        confidence: float = Field(ge=0.0, le=1.0)
        next_actions: list[str]
        execution_time_ms: int
        model_used: str
        ui_tars_checkpoints: list[str]

class TriageAgent(AgentContract):
    """Triage Agent - runs on Dolphin Worker"""
    
    agent_type = "triage"
    model = "llama-3.2-8b-instruct"  # Local on RTX 4070
    
    class Output(AgentContract.Output):
        findings: dict = {
            "category": Literal["vendor", "staff", "customer", "system"],
            "urgency": int,  # 0-100
            "type": str,
            "requires_vision": bool,
            "has_deadline": bool
        }

class ContextAgent(AgentContract):
    """Context Agent - NO FALLBACK ALLOWED"""
    
    agent_type = "context"
    model = "oss-120b"  # Or your best model
    fallback_allowed = False  # CRITICAL
    
    class Output(AgentContract.Output):
        findings: dict = {
            "synthesis": str,
            "historical_pattern": Optional[str],
            "vendor_reliability": Optional[float],
            "recommendations": list[dict],
            "risk_assessment": Literal["low", "medium", "high", "critical"]
        }
```

---

## 8. Data Flow & Event Architecture

### 8.1 Complete Event Flow

```
Email Arrives (IMAP/SnappyMail)
    ↓
AUBS Receives Event
    ↓
AUBS Builds Dolphin DAG
    ↓
Dolphin Schedules Tasks
    ↓
Workers Execute Agents (with UI-TARS checkpoints)
    ↓
Results Flow Back to AUBS
    ↓
AUBS Routes to Actions via MCP
    ↓
UI-TARS Shows Complete Execution Timeline
```

### 8.2 NATS Event Streams

```python
EVENT_STREAMS = {
    # Email events
    "emails.received": "New email arrived",
    "emails.processing": "Email being processed",
    "emails.completed": "Email fully processed",
    
    # Dolphin events
    "dolphin.dag.submitted": "DAG submitted to scheduler",
    "dolphin.task.started": "Task started on worker",
    "dolphin.task.completed": "Task completed successfully",
    "dolphin.task.failed": "Task failed, may retry",
    
    # Agent events
    "agents.triage.complete": "Triage categorization done",
    "agents.vision.complete": "Vision extraction done",
    "agents.context.complete": "Context synthesis done",
    
    # UI-TARS events
    "uitars.checkpoint": "Visual checkpoint created",
    "uitars.session.started": "Debug session started",
    "uitars.session.complete": "Debug session complete",
    
    # Action events
    "actions.task.created": "Task created in system",
    "actions.calendar.scheduled": "Calendar event created",
    "actions.notification.sent": "SMS/push sent"
}
```

---

## 9. Deployment Architecture

### 9.1 Docker Compose Stack

```yaml
version: '3.8'

services:
  # UI Layer
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DOLPHIN_URL=http://dolphin:12345
      - UITARS_URL=http://uitars:8080
    depends_on:
      - dolphin-server
      - uitars
      
  uitars:
    build: ./uitars-desktop
    ports:
      - "8080:8080"
    environment:
      - DOLPHIN_API=http://dolphin:12345/api
      - CAPTURE_SCREENSHOTS=true
      
  # Orchestration Layer
  dolphin-server:
    image: apache/dolphinscheduler:3.2.0
    ports:
      - "12345:12345"
    environment:
      - DATABASE_TYPE=postgresql
      - DATABASE_URL=postgres://dolphin:password@postgres:5432/dolphin
      - RESOURCE_MANAGER_ENABLED=true
    depends_on:
      - postgres
      
  dolphin-worker-1:
    image: apache/dolphinscheduler:3.2.0-worker
    environment:
      - WORKER_GROUP=agent-workers
      - GPU_ENABLED=true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
              
  dolphin-worker-2:
    image: apache/dolphinscheduler:3.2.0-worker
    environment:
      - WORKER_GROUP=agent-workers
      - GPU_ENABLED=false
      
  # AUBS Service
  aubs:
    build: ./aubs
    ports:
      - "5000:5000"
    environment:
      - DOLPHIN_URL=http://dolphin-server:12345
      - UITARS_URL=http://uitars:8080
      - NATS_URL=nats://nats:4222
      
  # Supporting Services
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dolphin
      POSTGRES_USER: dolphin
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      
  nats:
    image: nats:2.10-alpine
    command: ["-js"]
    ports:
      - "4222:4222"
      
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
      
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  ollama_models:
```

### 9.2 Production Kubernetes Deployment

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chilihead-v2

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dolphin-server
  namespace: chilihead-v2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dolphin-server
  template:
    metadata:
      labels:
        app: dolphin-server
    spec:
      containers:
      - name: dolphin
        image: apache/dolphinscheduler:3.2.0
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: dolphin-workers
  namespace: chilihead-v2
spec:
  serviceName: dolphin-workers
  replicas: 3
  selector:
    matchLabels:
      app: dolphin-worker
  template:
    metadata:
      labels:
        app: dolphin-worker
    spec:
      containers:
      - name: worker
        image: apache/dolphinscheduler:3.2.0-worker
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: "1"  # For Vision Agent
```

---

## 10. Implementation Roadmap

### Phase 1: Infrastructure (Week 1-2)
- [ ] Deploy Dolphin scheduler
- [ ] Set up UI-TARS desktop
- [ ] Configure Open-WebUI
- [ ] Establish PostgreSQL/Redis/Qdrant

### Phase 2: AUBS Core (Week 3-4)
- [ ] Implement AUBS orchestrator
- [ ] Create Dolphin DAG builder
- [ ] Set up NATS event streams
- [ ] Configure UI-TARS checkpoints

### Phase 3: Agent Development (Week 5-6)
- [ ] Implement Triage Agent
- [ ] Implement Vision Agent
- [ ] Implement Deadline Scanner
- [ ] Implement Task Categorizer
- [ ] Implement Context Agent (no fallback)

### Phase 4: Integration (Week 7-8)
- [ ] Wire MCP tools
- [ ] Connect email ingestion
- [ ] Test end-to-end flow
- [ ] UI-TARS debugging setup

### Phase 5: Production Hardening (Week 9-10)
- [ ] Load testing with Dolphin
- [ ] Failure recovery scenarios
- [ ] Performance optimization
- [ ] Documentation and training

---

## Success Criteria

1. **Process 500+ emails/day through Dolphin workers**
2. **UI-TARS provides complete execution visibility**
3. **Context Agent maintains 30+ day memory**
4. **Zero critical failures in 30-day run**
5. **Visual debugging reduces troubleshooting time by 80%**
6. **Dolphin ensures 99.9% execution reliability**

---

## Appendix A: ByteDance Tool Documentation

### Dolphin Documentation
- GitHub: https://github.com/apache/dolphinscheduler
- Architecture: https://dolphinscheduler.apache.org/en-us/docs/latest/architecture/design
- API Reference: https://dolphinscheduler.apache.org/en-us/docs/latest/api/open-api

### UI-TARS Documentation  
- GitHub: https://github.com/bytedance/UI-TARS-desktop
- Visual Debugging Guide: [Internal Documentation]
- Integration Examples: [Internal Documentation]

---

**END OF PRD v2.1**

This PRD fully integrates ByteDance's Dolphin and UI-TARS into your ChiliHead OpsManager architecture, providing enterprise-grade orchestration with visual debugging capabilities that are specifically designed for AI agent workflows. The combination gives you TikTok-scale reliability with complete visibility into your agent decision-making process.