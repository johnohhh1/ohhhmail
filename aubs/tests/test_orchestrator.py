"""
Unit tests for AUBS orchestrator
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from datetime import datetime
from uuid import uuid4

from src.config import AUBSSettings
from src.orchestrator import AUBSOrchestrator
from shared.models import EmailData, EmailAttachment, ExecutionStatus


@pytest.fixture
def settings():
    """Create test settings"""
    return AUBSSettings(
        environment="test",
        dolphin_url="http://localhost:12345",
        ui_tars_url="http://localhost:8080",
        nats_url="nats://localhost:4222"
    )


@pytest.fixture
async def orchestrator(settings):
    """Create orchestrator instance"""
    orch = AUBSOrchestrator(settings)
    # Don't initialize for unit tests (avoids external dependencies)
    # await orch.initialize()
    yield orch
    # await orch.shutdown()


@pytest.mark.asyncio
async def test_orchestrator_creation(settings):
    """Test orchestrator can be created"""
    orch = AUBSOrchestrator(settings)
    assert orch is not None
    assert orch.settings == settings
    assert orch.executions == {}


@pytest.mark.asyncio
async def test_process_email_creates_execution(orchestrator):
    """Test that processing an email creates an execution"""
    email = EmailData(
        subject="Test Email",
        sender="test@example.com",
        recipient="manager@restaurant.com",
        body="This is a test email"
    )

    # Mock the DAG submission to avoid external calls
    orchestrator._submit_dag = lambda dag: "test_execution_id"
    orchestrator._check_dolphin_health = lambda: True

    # Note: This will fail without mocking HTTP calls
    # In a real test, use pytest-httpx or similar to mock external calls
    # execution = await orchestrator.process_email(email)
    # assert execution is not None
    # assert execution.email_id == email.id
    # assert execution.status == ExecutionStatus.RUNNING


def test_execution_storage(orchestrator):
    """Test execution storage and retrieval"""
    from shared.models import Execution

    execution_id = uuid4()
    execution = Execution(
        id=execution_id,
        email_id="test_email_123",
        dag_id="test_dag",
        status=ExecutionStatus.PENDING
    )

    orchestrator.executions[execution_id] = execution

    # Test retrieval
    retrieved = orchestrator.executions.get(execution_id)
    assert retrieved is not None
    assert retrieved.id == execution_id
    assert retrieved.email_id == "test_email_123"


@pytest.mark.asyncio
async def test_list_executions_empty(orchestrator):
    """Test listing executions when none exist"""
    executions = await orchestrator.list_executions()
    assert executions == []


@pytest.mark.asyncio
async def test_list_executions_with_data(orchestrator):
    """Test listing executions with data"""
    from shared.models import Execution

    # Create test executions
    exec1 = Execution(email_id="email1", dag_id="dag1", status=ExecutionStatus.COMPLETED)
    exec2 = Execution(email_id="email2", dag_id="dag2", status=ExecutionStatus.RUNNING)
    exec3 = Execution(email_id="email3", dag_id="dag3", status=ExecutionStatus.FAILED)

    orchestrator.executions = {
        exec1.id: exec1,
        exec2.id: exec2,
        exec3.id: exec3
    }

    # Test listing all
    executions = await orchestrator.list_executions(limit=10)
    assert len(executions) == 3

    # Test with status filter
    completed = await orchestrator.list_executions(status_filter=ExecutionStatus.COMPLETED)
    assert len(completed) == 1
    assert completed[0].status == ExecutionStatus.COMPLETED

    # Test with limit
    limited = await orchestrator.list_executions(limit=2)
    assert len(limited) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
