"""
ChiliHead OpsManager v2.1 - Base Agent Contract
All AI agents must inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from shared.models import AgentType, AgentInput, AgentOutput
from shared.clients.llm_client import LLMClient, LLMResponse
from shared.llm_config import LLMConfig


class AgentResult(BaseModel):
    """Standardized agent execution result"""
    success: bool
    output: Optional[AgentOutput] = None
    error: Optional[str] = None
    execution_time_ms: int
    checkpoints_created: List[str] = []


class BaseAgent(ABC):
    """
    Base agent contract that all ChiliHead agents must implement

    Features:
    - Standardized input/output handling
    - LLM client integration with fallback support
    - UI-TARS checkpoint creation
    - Error handling and logging
    - Performance tracking
    """

    def __init__(self, config: LLMConfig, agent_type: AgentType):
        """
        Initialize base agent

        Args:
            config: LLM configuration with provider and model settings
            agent_type: Type of agent (triage, vision, etc.)
        """
        self.config = config
        self.agent_type = agent_type
        self.llm_client = LLMClient(config)
        self.checkpoints: List[str] = []

        logger.info(f"Initialized {agent_type.value} agent with {config.provider}:{config.model}")

    @abstractmethod
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process input and return agent-specific output

        Args:
            input_data: Agent-specific input model

        Returns:
            Agent-specific output model

        Raises:
            Exception: On processing failure
        """
        pass

    async def execute(self, input_data: AgentInput) -> AgentResult:
        """
        Execute agent with error handling and performance tracking

        Args:
            input_data: Agent input data

        Returns:
            AgentResult with output or error information
        """
        start_time = datetime.now()

        try:
            logger.info(f"Starting {self.agent_type.value} agent execution")

            # Process the input
            output = await self.process(input_data)

            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            output.execution_time_ms = execution_time

            # Create final checkpoint if enabled
            if input_data.checkpoint_enabled:
                await self._create_checkpoint(
                    session_id=input_data.session_id,
                    checkpoint_name=f"{self.agent_type.value}_complete",
                    data=output.model_dump()
                )

            logger.success(
                f"{self.agent_type.value} agent completed in {execution_time}ms "
                f"with confidence {output.confidence:.2f}"
            )

            return AgentResult(
                success=True,
                output=output,
                error=None,
                execution_time_ms=execution_time,
                checkpoints_created=self.checkpoints
            )

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"{self.agent_type.value} agent failed after {execution_time}ms: {e}")

            return AgentResult(
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=execution_time,
                checkpoints_created=self.checkpoints
            )

    async def _create_checkpoint(
        self,
        session_id: str,
        checkpoint_name: str,
        data: Dict[str, Any],
        screenshot: bool = False
    ) -> str:
        """
        Create UI-TARS checkpoint for tracking and debugging

        Args:
            session_id: Execution session ID
            checkpoint_name: Name of the checkpoint
            data: Checkpoint data to store
            screenshot: Whether to capture screenshot

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{session_id}_{checkpoint_name}_{int(datetime.now().timestamp())}"

        # TODO: Integrate with actual UI-TARS service
        # For now, just log and track
        logger.debug(f"Created checkpoint: {checkpoint_id}")

        self.checkpoints.append(checkpoint_id)

        return checkpoint_id

    async def _generate_with_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate response using configured LLM

        Args:
            messages: Conversation messages
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        return await self.llm_client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )

    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling markdown code blocks

        Args:
            content: LLM response content

        Returns:
            Parsed JSON object
        """
        import json
        import re

        # Remove markdown code blocks if present
        content = content.strip()

        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Remove any leading/trailing non-JSON content
        start = content.find('{')
        end = content.rfind('}') + 1

        if start != -1 and end > start:
            content = content[start:end]

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nContent: {content[:200]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    @property
    def model_name(self) -> str:
        """Get the model name being used"""
        return f"{self.config.provider}:{self.config.model}"

    @property
    def supports_fallback(self) -> bool:
        """Check if fallback is configured"""
        return self.config.fallback_allowed and self.config.fallback_provider is not None
