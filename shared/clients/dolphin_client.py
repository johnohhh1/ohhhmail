"""
ChiliHead OpsManager v2.1 - Apache DolphinScheduler Client
Handles DAG submission, execution monitoring, and task management
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from pydolphinscheduler.core.workflow import Workflow
from pydolphinscheduler.core.task import Task as DolphinTask
from pydolphinscheduler.tasks.python import Python
from pydolphinscheduler.exceptions import PyDSException
import httpx

from shared.models import ExecutionStatus


class DolphinClient:
    """Apache DolphinScheduler API Client with async support"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize DolphinScheduler client

        Args:
            host: DolphinScheduler API host (default: env DOLPHIN_HOST)
            port: DolphinScheduler API port (default: env DOLPHIN_PORT or 12345)
            username: Authentication username (default: env DOLPHIN_USER)
            password: Authentication password (default: env DOLPHIN_PASSWORD)
        """
        self.host = host or os.getenv("DOLPHIN_HOST", "localhost")
        self.port = port or int(os.getenv("DOLPHIN_PORT", "12345"))
        self.username = username or os.getenv("DOLPHIN_USER", "admin")
        self.password = password or os.getenv("DOLPHIN_PASSWORD", "dolphinscheduler123")

        self.base_url = f"http://{self.host}:{self.port}/dolphinscheduler"
        self.api_url = f"{self.base_url}/api/v1"
        self.token: Optional[str] = None

        logger.info(f"DolphinClient initialized: {self.base_url}")

    async def _get_token(self) -> str:
        """Get authentication token from DolphinScheduler API"""
        if self.token:
            return self.token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/login",
                data={
                    "userName": self.username,
                    "userPassword": self.password
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise Exception(f"Authentication failed: {data.get('msg')}")

            self.token = data["data"]["token"]
            logger.info("DolphinScheduler authentication successful")
            return self.token

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to DolphinScheduler API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data
        """
        token = await self._get_token()

        headers = {
            "token": token,
            "Content-Type": "application/json"
        }

        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                raise Exception(f"API request failed: {result.get('msg')}")

            return result.get("data", {})

    async def submit_dag(
        self,
        dag_name: str,
        tasks: List[Dict[str, Any]],
        description: Optional[str] = None,
        project_name: str = "default"
    ) -> str:
        """
        Submit a DAG workflow to DolphinScheduler

        Args:
            dag_name: Unique name for the workflow
            tasks: List of task definitions
            description: Workflow description
            project_name: Project name (default: "default")

        Returns:
            Workflow process definition ID

        Example:
            tasks = [
                {
                    "name": "triage_agent",
                    "type": "PYTHON",
                    "code": "from agents.triage import run; run()",
                    "dependencies": []
                },
                {
                    "name": "vision_agent",
                    "type": "PYTHON",
                    "code": "from agents.vision import run; run()",
                    "dependencies": ["triage_agent"]
                }
            ]
            dag_id = await client.submit_dag("email_processing", tasks)
        """
        try:
            logger.info(f"Submitting DAG: {dag_name} with {len(tasks)} tasks")

            # Create workflow definition
            workflow_data = {
                "name": dag_name,
                "description": description or f"Auto-generated workflow: {dag_name}",
                "projectName": project_name,
                "releaseState": "ONLINE",
                "timeout": 3600,
                "tasks": []
            }

            # Build task definitions
            for task in tasks:
                task_def = {
                    "name": task["name"],
                    "taskType": task.get("type", "PYTHON"),
                    "taskParams": {
                        "rawScript": task.get("code", ""),
                        "localParams": task.get("params", [])
                    },
                    "flag": "YES",
                    "taskPriority": "MEDIUM",
                    "workerGroup": "default",
                    "dependence": {
                        "relation": "AND",
                        "dependTaskList": [
                            {"name": dep} for dep in task.get("dependencies", [])
                        ]
                    },
                    "timeout": {
                        "enable": True,
                        "strategy": "WARN",
                        "interval": task.get("timeout", 900)
                    },
                    "retryTimes": task.get("retries", 3),
                    "retryInterval": 60
                }
                workflow_data["tasks"].append(task_def)

            # Submit workflow
            result = await self._request(
                "POST",
                f"projects/{project_name}/process/save",
                data=workflow_data
            )

            process_id = result.get("processDefinitionId")
            logger.info(f"DAG submitted successfully: {dag_name} (ID: {process_id})")
            return str(process_id)

        except Exception as e:
            logger.error(f"Failed to submit DAG {dag_name}: {e}")
            raise

    async def start_workflow(
        self,
        process_definition_id: str,
        schedule_time: Optional[datetime] = None,
        failure_strategy: str = "CONTINUE",
        project_name: str = "default"
    ) -> str:
        """
        Start a workflow execution

        Args:
            process_definition_id: Process definition ID
            schedule_time: Scheduled execution time (None for immediate)
            failure_strategy: How to handle failures (CONTINUE, END)
            project_name: Project name

        Returns:
            Process instance ID
        """
        try:
            params = {
                "processDefinitionId": process_definition_id,
                "scheduleTime": schedule_time.isoformat() if schedule_time else None,
                "failureStrategy": failure_strategy,
                "warningType": "NONE",
                "warningGroupId": 0,
                "execType": "START_PROCESS"
            }

            result = await self._request(
                "POST",
                f"projects/{project_name}/executors/start-process-instance",
                data=params
            )

            instance_id = result.get("processInstanceId")
            logger.info(f"Workflow started: instance {instance_id}")
            return str(instance_id)

        except Exception as e:
            logger.error(f"Failed to start workflow {process_definition_id}: {e}")
            raise

    async def get_execution_status(
        self,
        process_instance_id: str,
        project_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Get workflow execution status

        Args:
            process_instance_id: Process instance ID
            project_name: Project name

        Returns:
            Execution status information including:
            - status: ExecutionStatus enum value
            - start_time: Execution start time
            - end_time: Execution end time (if completed)
            - duration: Duration in seconds
            - tasks: List of task statuses
        """
        try:
            result = await self._request(
                "GET",
                f"projects/{project_name}/instance/select-by-id",
                params={"processInstanceId": process_instance_id}
            )

            # Map DolphinScheduler state to our ExecutionStatus
            state_mapping = {
                "SUBMITTED_SUCCESS": ExecutionStatus.PENDING,
                "RUNNING_EXECUTION": ExecutionStatus.RUNNING,
                "READY_PAUSE": ExecutionStatus.RUNNING,
                "PAUSE": ExecutionStatus.PENDING,
                "READY_STOP": ExecutionStatus.RUNNING,
                "STOP": ExecutionStatus.CANCELLED,
                "FAILURE": ExecutionStatus.FAILED,
                "SUCCESS": ExecutionStatus.COMPLETED,
                "NEED_FAULT_TOLERANCE": ExecutionStatus.FAILED,
                "KILL": ExecutionStatus.CANCELLED
            }

            dolphin_state = result.get("state", "UNKNOWN")
            status = state_mapping.get(dolphin_state, ExecutionStatus.PENDING)

            return {
                "status": status,
                "dolphin_state": dolphin_state,
                "start_time": result.get("startTime"),
                "end_time": result.get("endTime"),
                "duration": result.get("duration"),
                "host": result.get("host"),
                "command_type": result.get("commandType"),
                "tasks": result.get("taskList", [])
            }

        except Exception as e:
            logger.error(f"Failed to get execution status for {process_instance_id}: {e}")
            raise

    async def get_task_results(
        self,
        process_instance_id: str,
        task_name: Optional[str] = None,
        project_name: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Get task execution results

        Args:
            process_instance_id: Process instance ID
            task_name: Specific task name (None for all tasks)
            project_name: Project name

        Returns:
            List of task results with status, logs, and output
        """
        try:
            result = await self._request(
                "GET",
                f"projects/{project_name}/task-instance/list-by-process-id/{process_instance_id}",
                params={"pageNo": 1, "pageSize": 100}
            )

            tasks = result.get("taskList", [])

            if task_name:
                tasks = [t for t in tasks if t.get("name") == task_name]

            task_results = []
            for task in tasks:
                task_id = task.get("id")

                # Get task logs
                log_result = await self._request(
                    "GET",
                    f"log/detail",
                    params={"taskInstanceId": task_id}
                )

                task_results.append({
                    "task_name": task.get("name"),
                    "task_id": task_id,
                    "state": task.get("state"),
                    "start_time": task.get("startTime"),
                    "end_time": task.get("endTime"),
                    "duration": task.get("duration"),
                    "host": task.get("host"),
                    "log": log_result.get("data"),
                    "retry_times": task.get("retryTimes", 0)
                })

            return task_results

        except Exception as e:
            logger.error(f"Failed to get task results for {process_instance_id}: {e}")
            raise

    async def retry_task(
        self,
        task_instance_id: str,
        project_name: str = "default"
    ) -> bool:
        """
        Retry a failed task

        Args:
            task_instance_id: Task instance ID
            project_name: Project name

        Returns:
            True if retry was successful
        """
        try:
            await self._request(
                "POST",
                f"projects/{project_name}/task-instance/{task_instance_id}/retry"
            )
            logger.info(f"Task {task_instance_id} retry initiated")
            return True

        except Exception as e:
            logger.error(f"Failed to retry task {task_instance_id}: {e}")
            return False

    async def cancel_workflow(
        self,
        process_instance_id: str,
        project_name: str = "default"
    ) -> bool:
        """
        Cancel a running workflow

        Args:
            process_instance_id: Process instance ID
            project_name: Project name

        Returns:
            True if cancellation was successful
        """
        try:
            await self._request(
                "POST",
                f"projects/{project_name}/executors/execute",
                data={
                    "processInstanceId": process_instance_id,
                    "executeType": "STOP"
                }
            )
            logger.info(f"Workflow {process_instance_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel workflow {process_instance_id}: {e}")
            return False

    async def wait_for_completion(
        self,
        process_instance_id: str,
        timeout: int = 3600,
        poll_interval: int = 5,
        project_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Wait for workflow to complete with polling

        Args:
            process_instance_id: Process instance ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            project_name: Project name

        Returns:
            Final execution status

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
        """
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            status_info = await self.get_execution_status(
                process_instance_id,
                project_name
            )

            status = status_info["status"]

            if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                logger.info(f"Workflow {process_instance_id} finished with status: {status}")
                return status_info

            await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"Workflow {process_instance_id} did not complete within {timeout} seconds"
        )

    async def close(self):
        """Cleanup resources"""
        self.token = None
        logger.info("DolphinClient closed")
