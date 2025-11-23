"""
ChiliHead OpsManager v2.1 - UI-TARS Desktop Client
Handles desktop automation checkpoints, sessions, and metrics
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from loguru import logger

import httpx

from shared.models import UITARSCheckpoint, UITARSSession, ExecutionStatus


class UITARSClient:
    """UI-TARS Desktop client for automation checkpointing"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize UI-TARS client

        Args:
            base_url: UI-TARS server URL (default: env UITARS_URL)
            api_key: API key for authentication (default: env UITARS_API_KEY)
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or os.getenv("UITARS_URL", "http://localhost:8080")).rstrip("/")
        self.api_key = api_key or os.getenv("UITARS_API_KEY", "")
        self.timeout = timeout

        self.headers = {
            "Content-Type": "application/json"
        }

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info(f"UITARSClient initialized: {self.base_url}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to UI-TARS API

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            params: Query parameters

        Returns:
            Response JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_session(
        self,
        execution_id: UUID,
        session_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UITARSSession:
        """
        Create a new UI-TARS session

        Args:
            execution_id: Associated execution ID
            session_type: Type of session (e.g., "email_processing")
            metadata: Additional metadata

        Returns:
            Created session object

        Example:
            session = await uitars_client.create_session(
                execution_id=execution_id,
                session_type="email_processing",
                metadata={"email_id": "123"}
            )
        """
        try:
            data = {
                "execution_id": str(execution_id),
                "session_type": session_type,
                "metadata": metadata or {},
                "started_at": datetime.now().isoformat()
            }

            response = await self._request("POST", "/api/v1/sessions", data=data)

            session = UITARSSession(
                id=UUID(response["id"]),
                execution_id=execution_id,
                session_type=session_type,
                started_at=datetime.fromisoformat(response["started_at"]),
                status=ExecutionStatus(response.get("status", "running"))
            )

            logger.info(f"Created UI-TARS session: {session.id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create UI-TARS session: {e}")
            raise

    async def create_checkpoint(
        self,
        session_id: UUID,
        checkpoint_name: str,
        data: Dict[str, Any],
        screenshot: Optional[bytes] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> UITARSCheckpoint:
        """
        Create a checkpoint in a session

        Args:
            session_id: Session ID
            checkpoint_name: Descriptive checkpoint name
            data: Checkpoint data (state information)
            screenshot: Optional screenshot bytes
            metrics: Optional performance metrics

        Returns:
            Created checkpoint object

        Example:
            checkpoint = await uitars_client.create_checkpoint(
                session_id=session.id,
                checkpoint_name="triage_complete",
                data={
                    "agent": "triage",
                    "result": "vendor_invoice",
                    "confidence": 0.95
                },
                metrics={
                    "duration_ms": 1234,
                    "tokens_used": 456
                }
            )
        """
        try:
            # Prepare data
            checkpoint_data = {
                "session_id": str(session_id),
                "checkpoint_name": checkpoint_name,
                "data": data,
                "metrics": metrics or {},
                "timestamp": datetime.now().isoformat()
            }

            # If screenshot provided, encode as base64
            if screenshot:
                import base64
                checkpoint_data["screenshot"] = base64.b64encode(screenshot).decode()

            response = await self._request(
                "POST",
                f"/api/v1/sessions/{session_id}/checkpoints",
                data=checkpoint_data
            )

            checkpoint = UITARSCheckpoint(
                timestamp=datetime.fromisoformat(response["timestamp"]),
                checkpoint_name=checkpoint_name,
                data=data,
                screenshot=response.get("screenshot"),
                metrics=metrics or {}
            )

            logger.debug(f"Created checkpoint: {checkpoint_name} in session {session_id}")
            return checkpoint

        except Exception as e:
            logger.error(f"Failed to create checkpoint {checkpoint_name}: {e}")
            raise

    async def end_session(
        self,
        session_id: UUID,
        status: ExecutionStatus = ExecutionStatus.COMPLETED,
        final_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        End a UI-TARS session

        Args:
            session_id: Session ID to end
            status: Final session status
            final_metrics: Final session metrics

        Returns:
            True if successful
        """
        try:
            data = {
                "status": status.value,
                "completed_at": datetime.now().isoformat(),
                "final_metrics": final_metrics or {}
            }

            await self._request(
                "PATCH",
                f"/api/v1/sessions/{session_id}/end",
                data=data
            )

            logger.info(f"Ended UI-TARS session: {session_id} with status {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False

    async def get_session(self, session_id: UUID) -> UITARSSession:
        """
        Get session details

        Args:
            session_id: Session ID

        Returns:
            Session object with all checkpoints
        """
        try:
            response = await self._request(
                "GET",
                f"/api/v1/sessions/{session_id}"
            )

            # Parse checkpoints
            checkpoints = []
            for cp_data in response.get("checkpoints", []):
                checkpoint = UITARSCheckpoint(
                    timestamp=datetime.fromisoformat(cp_data["timestamp"]),
                    checkpoint_name=cp_data["checkpoint_name"],
                    data=cp_data["data"],
                    screenshot=cp_data.get("screenshot"),
                    metrics=cp_data.get("metrics", {})
                )
                checkpoints.append(checkpoint)

            session = UITARSSession(
                id=UUID(response["id"]),
                execution_id=UUID(response["execution_id"]),
                session_type=response["session_type"],
                checkpoints=checkpoints,
                started_at=datetime.fromisoformat(response["started_at"]),
                completed_at=datetime.fromisoformat(response["completed_at"]) if response.get("completed_at") else None,
                status=ExecutionStatus(response.get("status", "running"))
            )

            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def get_checkpoints(
        self,
        session_id: UUID,
        checkpoint_name: Optional[str] = None
    ) -> List[UITARSCheckpoint]:
        """
        Get checkpoints for a session

        Args:
            session_id: Session ID
            checkpoint_name: Filter by checkpoint name

        Returns:
            List of checkpoints
        """
        try:
            params = {}
            if checkpoint_name:
                params["name"] = checkpoint_name

            response = await self._request(
                "GET",
                f"/api/v1/sessions/{session_id}/checkpoints",
                params=params
            )

            checkpoints = []
            for cp_data in response.get("checkpoints", []):
                checkpoint = UITARSCheckpoint(
                    timestamp=datetime.fromisoformat(cp_data["timestamp"]),
                    checkpoint_name=cp_data["checkpoint_name"],
                    data=cp_data["data"],
                    screenshot=cp_data.get("screenshot"),
                    metrics=cp_data.get("metrics", {})
                )
                checkpoints.append(checkpoint)

            return checkpoints

        except Exception as e:
            logger.error(f"Failed to get checkpoints for session {session_id}: {e}")
            raise

    async def capture_screenshot(
        self,
        window_title: Optional[str] = None,
        display: int = 0
    ) -> bytes:
        """
        Capture screenshot via UI-TARS

        Args:
            window_title: Optional window title to focus
            display: Display number (for multi-monitor)

        Returns:
            Screenshot image bytes (PNG)
        """
        try:
            params = {
                "display": display
            }
            if window_title:
                params["window"] = window_title

            response = await self._request(
                "POST",
                "/api/v1/screenshot",
                params=params
            )

            # Decode base64 screenshot
            import base64
            screenshot_bytes = base64.b64decode(response["screenshot"])

            logger.debug(f"Captured screenshot ({len(screenshot_bytes)} bytes)")
            return screenshot_bytes

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise

    async def send_metrics(
        self,
        session_id: UUID,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Send performance metrics to UI-TARS

        Args:
            session_id: Session ID
            metrics: Metrics dictionary

        Returns:
            True if successful

        Example:
            await uitars_client.send_metrics(
                session_id=session.id,
                metrics={
                    "cpu_percent": 45.2,
                    "memory_mb": 512,
                    "gpu_utilization": 78.5,
                    "inference_time_ms": 234
                }
            )
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }

            await self._request(
                "POST",
                f"/api/v1/sessions/{session_id}/metrics",
                data=data
            )

            logger.debug(f"Sent metrics for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")
            return False

    async def list_sessions(
        self,
        execution_id: Optional[UUID] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 50
    ) -> List[UITARSSession]:
        """
        List sessions with optional filtering

        Args:
            execution_id: Filter by execution ID
            status: Filter by status
            limit: Maximum results

        Returns:
            List of sessions
        """
        try:
            params = {"limit": limit}

            if execution_id:
                params["execution_id"] = str(execution_id)

            if status:
                params["status"] = status.value

            response = await self._request(
                "GET",
                "/api/v1/sessions",
                params=params
            )

            sessions = []
            for session_data in response.get("sessions", []):
                session = UITARSSession(
                    id=UUID(session_data["id"]),
                    execution_id=UUID(session_data["execution_id"]),
                    session_type=session_data["session_type"],
                    started_at=datetime.fromisoformat(session_data["started_at"]),
                    completed_at=datetime.fromisoformat(session_data["completed_at"]) if session_data.get("completed_at") else None,
                    status=ExecutionStatus(session_data.get("status", "running"))
                )
                sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if UI-TARS server is healthy

        Returns:
            True if server is responding
        """
        try:
            response = await self._request("GET", "/health")
            return response.get("status") == "ok"

        except Exception as e:
            logger.error(f"UI-TARS health check failed: {e}")
            return False

    async def close(self):
        """Cleanup resources"""
        logger.info("UITARSClient closed")
