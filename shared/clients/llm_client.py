"""
ChiliHead OpsManager v2.1 - Unified LLM Client
Supports OpenAI, Anthropic, and Ollama with automatic fallback
"""

import os
import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from loguru import logger

from shared.llm_config import LLMConfig, LLMProvider, LLMClientFactory


class LLMResponse(BaseModel):
    """Standardized LLM response"""
    content: str
    model_used: str
    provider_used: str
    execution_time_ms: int
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


class LLMClient:
    """Unified LLM client with multi-provider support and fallback"""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client with configuration

        Args:
            config: LLMConfig object with provider, model, and fallback settings
        """
        self.config = config
        self.primary_client = None
        self.fallback_client = None

        # Initialize primary client
        try:
            self.primary_client = LLMClientFactory.get_client(config)
            logger.info(f"Initialized {config.provider}:{config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize primary client: {e}")
            raise

        # Initialize fallback client if configured
        if config.fallback_provider and config.fallback_model:
            try:
                fallback_config = LLMConfig(
                    provider=config.fallback_provider,
                    model=config.fallback_model,
                    timeout=config.timeout,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                self.fallback_client = LLMClientFactory.get_client(fallback_config)
                logger.info(f"Initialized fallback: {config.fallback_provider}:{config.fallback_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback client: {e}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using configured LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            Exception: If primary fails and no fallback configured
        """
        start_time = time.time()

        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Try primary provider
        try:
            response = await self._generate_with_provider(
                messages=messages,
                client=self.primary_client,
                provider=self.config.provider,
                model=self.config.model,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs
            )

            execution_time = int((time.time() - start_time) * 1000)
            response.execution_time_ms = execution_time

            logger.info(f"Generated response using {self.config.provider}:{self.config.model} in {execution_time}ms")
            return response

        except Exception as primary_error:
            logger.error(f"Primary provider failed: {primary_error}")

            # Check if fallback is allowed
            if not self.config.fallback_allowed:
                logger.error("Fallback disabled - failing fast")
                raise

            # Try fallback if configured
            if self.fallback_client:
                try:
                    logger.warning(f"Attempting fallback to {self.config.fallback_provider}:{self.config.fallback_model}")

                    response = await self._generate_with_provider(
                        messages=messages,
                        client=self.fallback_client,
                        provider=self.config.fallback_provider,
                        model=self.config.fallback_model,
                        temperature=temperature or self.config.temperature,
                        max_tokens=max_tokens or self.config.max_tokens,
                        **kwargs
                    )

                    execution_time = int((time.time() - start_time) * 1000)
                    response.execution_time_ms = execution_time
                    response.metadata["fallback_used"] = True
                    response.metadata["primary_error"] = str(primary_error)

                    logger.success(f"Fallback successful in {execution_time}ms")
                    return response

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise Exception(f"Both primary and fallback failed. Primary: {primary_error}, Fallback: {fallback_error}")
            else:
                raise primary_error

    async def _generate_with_provider(
        self,
        messages: List[Dict[str, str]],
        client: Any,
        provider: LLMProvider,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """Generate using specific provider client"""

        if provider == LLMProvider.OPENAI:
            return await self._generate_openai(client, model, messages, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(client, model, messages, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.OLLAMA:
            return await self._generate_ollama(client, model, messages, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _generate_openai(
        self,
        client,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """Generate using OpenAI API"""

        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens

        params.update(kwargs)

        response = await client.chat.completions.create(**params)

        return LLMResponse(
            content=response.choices[0].message.content,
            model_used=model,
            provider_used="openai",
            execution_time_ms=0,  # Will be set by caller
            tokens_used=response.usage.total_tokens if response.usage else None,
            finish_reason=response.choices[0].finish_reason
        )

    async def _generate_anthropic(
        self,
        client,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """Generate using Anthropic API"""

        # Anthropic requires system prompt separate from messages
        system_prompt = None
        filtered_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        params = {
            "model": model,
            "messages": filtered_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,  # Anthropic requires max_tokens
        }

        if system_prompt:
            params["system"] = system_prompt

        params.update(kwargs)

        response = await client.messages.create(**params)

        return LLMResponse(
            content=response.content[0].text,
            model_used=model,
            provider_used="anthropic",
            execution_time_ms=0,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )

    async def _generate_ollama(
        self,
        client,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """Generate using Ollama API"""

        params = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            params["options"]["num_predict"] = max_tokens

        # Merge any additional options
        if "options" in kwargs:
            params["options"].update(kwargs.pop("options"))

        params.update(kwargs)

        response = await client.chat(**params)

        return LLMResponse(
            content=response["message"]["content"],
            model_used=model,
            provider_used="ollama",
            execution_time_ms=0,
            finish_reason=response.get("done_reason"),
            metadata={
                "total_duration": response.get("total_duration"),
                "load_duration": response.get("load_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count")
            }
        )

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output (OpenAI only for now)

        Args:
            messages: Conversation messages
            response_format: JSON schema for response
            **kwargs: Additional arguments

        Returns:
            Parsed JSON response
        """
        if self.config.provider != LLMProvider.OPENAI:
            logger.warning("Structured output only supported for OpenAI, falling back to text parsing")
            response = await self.generate(messages, **kwargs)
            import json
            return json.loads(response.content)

        response = await self.generate(
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs
        )

        import json
        return json.loads(response.content)


def create_llm_client(agent_name: str) -> LLMClient:
    """
    Factory function to create LLM client for specific agent

    Args:
        agent_name: Agent name (triage, vision, deadline, task, context)

    Returns:
        Configured LLMClient instance

    Example:
        triage_client = create_llm_client("triage")
        response = await triage_client.generate([
            {"role": "user", "content": "Classify this email"}
        ])
    """
    from shared.llm_config import AgentModelConfig

    configs = AgentModelConfig.from_env()

    if agent_name not in configs:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(configs.keys())}")

    return LLMClient(configs[agent_name])
