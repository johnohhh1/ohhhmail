"""
UI-TARS Integration Plugin for Dolphin
Manages checkpoint creation, screenshot capture, and execution logging
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import structlog
import httpx

logger = structlog.get_logger()


class CheckpointManager:
    """
    Manages checkpoint creation and retrieval for UI-TARS integration
    Handles:
    - Checkpoint creation before agent execution
    - Checkpoint updates during execution
    - Screenshot capture and storage
    - Checkpoint metadata management
    """

    def __init__(
        self,
        uitars_url: str = "http://uitars:8080",
        storage_path: str = "/data/checkpoints",
        timeout: int = 30
    ):
        """
        Initialize checkpoint manager
        Args:
            uitars_url: UI-TARS service URL
            storage_path: Local checkpoint storage path
            timeout: HTTP request timeout
        """
        self.uitars_url = uitars_url
        self.storage_path = Path(storage_path)
        self.timeout = timeout
        self.client = None

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Checkpoint manager initialized",
            storage_path=str(self.storage_path),
            uitars_url=uitars_url
        )

    async def create_checkpoint(
        self,
        execution_id: str,
        task_id: str,
        email_id: str,
        task_input: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new checkpoint before task execution
        Args:
            execution_id: Dolphin execution ID
            task_id: Task identifier
            email_id: Email being processed
            task_input: Input data for the task
            metadata: Additional metadata
        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{execution_id}_{task_id}_{datetime.utcnow().timestamp()}"

        log = logger.bind(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            task_id=task_id,
            email_id=email_id
        )

        try:
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "execution_id": execution_id,
                "task_id": task_id,
                "email_id": email_id,
                "created_at": datetime.utcnow().isoformat(),
                "task_input": task_input,
                "metadata": metadata or {},
                "status": "created",
            }

            # Save checkpoint locally
            checkpoint_file = self.storage_path / f"{checkpoint_id}.json"
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f, indent=2)

            log.info("Checkpoint created locally", checkpoint_file=str(checkpoint_file))

            # Create checkpoint in UI-TARS
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.uitars_url}/api/checkpoints",
                    json=checkpoint_data
                )
                response.raise_for_status()
                log.info("Checkpoint created in UI-TARS")

            return checkpoint_id

        except Exception as e:
            log.exception("Failed to create checkpoint", error=str(e))
            raise

    async def update_checkpoint(
        self,
        checkpoint_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update an existing checkpoint
        Args:
            checkpoint_id: Checkpoint identifier
            updates: Dictionary of updates
        """
        log = logger.bind(checkpoint_id=checkpoint_id)

        try:
            # Load and update local checkpoint
            checkpoint_file = self.storage_path / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, "r") as f:
                    checkpoint_data = json.load(f)
                checkpoint_data.update(updates)
                checkpoint_data["updated_at"] = datetime.utcnow().isoformat()

                with open(checkpoint_file, "w") as f:
                    json.dump(checkpoint_data, f, indent=2)

                # Update in UI-TARS
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    await client.put(
                        f"{self.uitars_url}/api/checkpoints/{checkpoint_id}",
                        json=updates
                    )
                    log.info("Checkpoint updated in UI-TARS")
            else:
                log.warning("Checkpoint file not found", checkpoint_file=str(checkpoint_file))

        except Exception as e:
            log.exception("Failed to update checkpoint", error=str(e))
            raise

    async def capture_screenshot(
        self,
        checkpoint_id: str,
        screenshot_data: bytes,
        screenshot_type: str = "task_execution"
    ) -> str:
        """
        Capture and store screenshot
        Args:
            checkpoint_id: Associated checkpoint ID
            screenshot_data: Raw screenshot data
            screenshot_type: Type of screenshot
        Returns:
            Screenshot ID
        """
        screenshot_id = f"{checkpoint_id}_{screenshot_type}_{datetime.utcnow().timestamp()}"

        log = logger.bind(
            screenshot_id=screenshot_id,
            checkpoint_id=checkpoint_id,
            screenshot_type=screenshot_type
        )

        try:
            # Save screenshot locally
            screenshots_dir = self.storage_path / checkpoint_id / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            screenshot_file = screenshots_dir / f"{screenshot_id}.png"
            with open(screenshot_file, "wb") as f:
                f.write(screenshot_data)

            log.info("Screenshot saved locally", file=str(screenshot_file))

            # Upload to UI-TARS
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"screenshot": screenshot_data}
                response = await client.post(
                    f"{self.uitars_url}/api/checkpoints/{checkpoint_id}/screenshots",
                    files=files,
                    params={"type": screenshot_type}
                )
                response.raise_for_status()
                log.info("Screenshot uploaded to UI-TARS")

            return screenshot_id

        except Exception as e:
            log.exception("Failed to capture screenshot", error=str(e))
            raise

    async def finalize_checkpoint(
        self,
        checkpoint_id: str,
        status: str = "completed",
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Finalize checkpoint after task execution
        Args:
            checkpoint_id: Checkpoint identifier
            status: Final status (completed, failed, etc)
            result: Task result data
        """
        log = logger.bind(checkpoint_id=checkpoint_id, status=status)

        try:
            updates = {
                "status": status,
                "finalized_at": datetime.utcnow().isoformat(),
            }

            if result:
                updates["result"] = result

            await self.update_checkpoint(checkpoint_id, updates)
            log.info("Checkpoint finalized")

        except Exception as e:
            log.exception("Failed to finalize checkpoint", error=str(e))
            raise

    async def get_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Retrieve checkpoint data
        Args:
            checkpoint_id: Checkpoint identifier
        Returns:
            Checkpoint data
        """
        log = logger.bind(checkpoint_id=checkpoint_id)

        try:
            checkpoint_file = self.storage_path / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, "r") as f:
                    return json.load(f)
            else:
                log.warning("Checkpoint not found locally, fetching from UI-TARS")

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.uitars_url}/api/checkpoints/{checkpoint_id}"
                    )
                    response.raise_for_status()
                    return response.json()

        except Exception as e:
            log.exception("Failed to retrieve checkpoint", error=str(e))
            raise


class ExecutionLogger:
    """
    Logs task execution details for debugging and auditing
    Tracks:
    - Task start/completion
    - Resource usage
    - Errors and warnings
    - Agent interactions
    """

    def __init__(
        self,
        log_dir: str = "/var/log/dolphin/executions",
        max_log_size: int = 10485760  # 10MB
    ):
        """
        Initialize execution logger
        Args:
            log_dir: Directory for execution logs
            max_log_size: Maximum log file size
        """
        self.log_dir = Path(log_dir)
        self.max_log_size = max_log_size

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Execution logger initialized",
            log_dir=str(self.log_dir)
        )

    def log_task_start(
        self,
        execution_id: str,
        task_id: str,
        input_data: Dict[str, Any]
    ) -> None:
        """Log task execution start"""
        log = logger.bind(
            execution_id=execution_id,
            task_id=task_id
        )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_start",
            "execution_id": execution_id,
            "task_id": task_id,
            "input_keys": list(input_data.keys()),
        }

        self._write_log(execution_id, log_entry)
        log.info("Task started", task_id=task_id)

    def log_task_completion(
        self,
        execution_id: str,
        task_id: str,
        duration: float,
        output_data: Dict[str, Any],
        status: str = "success"
    ) -> None:
        """Log task execution completion"""
        log = logger.bind(
            execution_id=execution_id,
            task_id=task_id,
            status=status,
            duration=duration
        )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_completion",
            "execution_id": execution_id,
            "task_id": task_id,
            "status": status,
            "duration_seconds": duration,
            "output_keys": list(output_data.keys()),
        }

        self._write_log(execution_id, log_entry)
        log.info("Task completed", duration=duration)

    def log_task_error(
        self,
        execution_id: str,
        task_id: str,
        error: str,
        traceback: Optional[str] = None
    ) -> None:
        """Log task execution error"""
        log = logger.bind(
            execution_id=execution_id,
            task_id=task_id,
            error=error
        )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_error",
            "execution_id": execution_id,
            "task_id": task_id,
            "error": error,
            "traceback": traceback,
        }

        self._write_log(execution_id, log_entry)
        log.error("Task error occurred", error=error)

    def log_resource_usage(
        self,
        execution_id: str,
        task_id: str,
        cpu_percent: float,
        memory_mb: float,
        gpu_percent: Optional[float] = None
    ) -> None:
        """Log resource usage during execution"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "resource_usage",
            "execution_id": execution_id,
            "task_id": task_id,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "gpu_percent": gpu_percent,
        }

        self._write_log(execution_id, log_entry)

    def _write_log(
        self,
        execution_id: str,
        log_entry: Dict[str, Any]
    ) -> None:
        """Write log entry to execution log file"""
        log_file = self.log_dir / f"{execution_id}.jsonl"

        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            # Check file size and rotate if necessary
            if log_file.stat().st_size > self.max_log_size:
                self._rotate_log(log_file)

        except Exception as e:
            logger.exception("Failed to write execution log", error=str(e))

    def _rotate_log(self, log_file: Path) -> None:
        """Rotate log file when it exceeds max size"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rotated_file = log_file.parent / f"{log_file.stem}_{timestamp}.jsonl"
        log_file.rename(rotated_file)
        logger.info("Log file rotated", rotated_file=str(rotated_file))


class UITARSPlugin:
    """
    Main UI-TARS integration plugin for Dolphin
    Provides hooks for checkpoint management and execution logging
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize UI-TARS plugin
        Args:
            config: Plugin configuration
        """
        self.config = config or {}

        # Initialize components
        self.checkpoint_manager = CheckpointManager(
            uitars_url=self.config.get("uitars_url", "http://uitars:8080"),
            storage_path=self.config.get("storage_path", "/data/checkpoints"),
            timeout=self.config.get("timeout", 30)
        )

        self.execution_logger = ExecutionLogger(
            log_dir=self.config.get("log_dir", "/var/log/dolphin/executions"),
            max_log_size=self.config.get("max_log_size", 10485760)
        )

        logger.info(
            "UI-TARS plugin initialized",
            config_keys=list(self.config.keys())
        )

    async def on_task_start(
        self,
        context: Dict[str, Any]
    ) -> None:
        """
        Hook called when task starts
        Creates checkpoint and logs start event
        Args:
            context: Task execution context
        """
        try:
            execution_id = context.get("execution_id", "unknown")
            task_id = context.get("task_id", "unknown")
            email_id = context.get("email_id", "unknown")
            task_input = context.get("input", {})

            # Create checkpoint
            checkpoint_id = await self.checkpoint_manager.create_checkpoint(
                execution_id=execution_id,
                task_id=task_id,
                email_id=email_id,
                task_input=task_input,
                metadata={
                    "agent_type": context.get("agent_type"),
                    "model": context.get("model"),
                    "provider": context.get("provider"),
                }
            )

            # Log execution start
            self.execution_logger.log_task_start(
                execution_id=execution_id,
                task_id=task_id,
                input_data=task_input
            )

            logger.info(
                "Task started with checkpoint",
                task_id=task_id,
                checkpoint_id=checkpoint_id
            )

        except Exception as e:
            logger.exception("Error in on_task_start hook", error=str(e))

    async def on_task_success(
        self,
        context: Dict[str, Any]
    ) -> None:
        """
        Hook called when task succeeds
        Updates checkpoint and logs completion
        Args:
            context: Task execution context with result
        """
        try:
            execution_id = context.get("execution_id", "unknown")
            task_id = context.get("task_id", "unknown")
            duration = context.get("duration", 0)
            output_data = context.get("output", {})

            # Update checkpoint
            checkpoint_id = f"{execution_id}_{task_id}"
            await self.checkpoint_manager.finalize_checkpoint(
                checkpoint_id=checkpoint_id,
                status="completed",
                result=output_data
            )

            # Log completion
            self.execution_logger.log_task_completion(
                execution_id=execution_id,
                task_id=task_id,
                duration=duration,
                output_data=output_data,
                status="success"
            )

            logger.info(
                "Task completed successfully",
                task_id=task_id,
                duration=duration
            )

        except Exception as e:
            logger.exception("Error in on_task_success hook", error=str(e))

    async def on_task_failure(
        self,
        context: Dict[str, Any],
        exception: Exception
    ) -> None:
        """
        Hook called when task fails
        Captures error state and logs failure
        Args:
            context: Task execution context
            exception: The exception that occurred
        """
        try:
            execution_id = context.get("execution_id", "unknown")
            task_id = context.get("task_id", "unknown")
            duration = context.get("duration", 0)

            # Attempt to capture screenshot on failure
            if self.config.get("screenshot_on_error", True):
                try:
                    screenshot_data = context.get("screenshot_data")
                    if screenshot_data:
                        checkpoint_id = f"{execution_id}_{task_id}"
                        await self.checkpoint_manager.capture_screenshot(
                            checkpoint_id=checkpoint_id,
                            screenshot_data=screenshot_data,
                            screenshot_type="error_state"
                        )
                except Exception as e:
                    logger.warning("Failed to capture error screenshot", error=str(e))

            # Update checkpoint with failure
            checkpoint_id = f"{execution_id}_{task_id}"
            await self.checkpoint_manager.finalize_checkpoint(
                checkpoint_id=checkpoint_id,
                status="failed",
                result={
                    "error": str(exception),
                    "error_type": type(exception).__name__,
                }
            )

            # Log error
            self.execution_logger.log_task_error(
                execution_id=execution_id,
                task_id=task_id,
                error=str(exception),
                traceback=context.get("traceback")
            )

            logger.error(
                "Task failed",
                task_id=task_id,
                error=str(exception),
                duration=duration
            )

        except Exception as e:
            logger.exception("Error in on_task_failure hook", error=str(e))

    def on_resource_check(
        self,
        context: Dict[str, Any]
    ) -> None:
        """
        Hook called during resource monitoring
        Logs resource usage
        Args:
            context: Resource usage context
        """
        try:
            execution_id = context.get("execution_id", "unknown")
            task_id = context.get("task_id", "unknown")

            self.execution_logger.log_resource_usage(
                execution_id=execution_id,
                task_id=task_id,
                cpu_percent=context.get("cpu_percent", 0),
                memory_mb=context.get("memory_mb", 0),
                gpu_percent=context.get("gpu_percent")
            )

        except Exception as e:
            logger.warning("Error in on_resource_check hook", error=str(e))
