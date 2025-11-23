"""
ChiliHead OpsManager v2.1 - Ollama LLM Client
Handles local LLM inference with streaming support
"""

import os
from typing import Any, AsyncIterator, Dict, List, Optional
from loguru import logger

import ollama
from ollama import AsyncClient, Options


class OllamaClient:
    """Ollama client for local LLM inference"""

    def __init__(
        self,
        host: Optional[str] = None,
        timeout: int = 120
    ):
        """
        Initialize Ollama client

        Args:
            host: Ollama server URL (default: env OLLAMA_HOST)
            timeout: Request timeout in seconds
        """
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout

        self.client = AsyncClient(
            host=self.host,
            timeout=timeout
        )

        logger.info(f"OllamaClient initialized: {self.host}")

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        system: Optional[str] = None,
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send chat completion request

        Args:
            model: Model name (e.g., "llama3.2:8b-instruct")
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            system: System prompt
            format: Response format ("json" for JSON output)

        Returns:
            Response dict with 'message' and 'model' fields

        Example:
            response = await ollama_client.chat(
                model="llama3.2:8b-instruct",
                messages=[
                    {"role": "user", "content": "Classify this email"}
                ],
                temperature=0.3,
                format="json"
            )
            print(response['message']['content'])
        """
        try:
            # Build options
            options = Options(
                temperature=temperature,
                num_predict=max_tokens or -1
            )

            # Add system message if provided
            if system:
                messages = [{"role": "system", "content": system}] + messages

            logger.debug(f"Ollama chat request: {model} ({len(messages)} messages)")

            if stream:
                return await self._chat_stream(model, messages, options, format)
            else:
                response = await self.client.chat(
                    model=model,
                    messages=messages,
                    options=options,
                    format=format
                )

                logger.debug(f"Ollama response received (model: {response.get('model')})")
                return response

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def _chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Options,
        format: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat completion"""
        try:
            stream = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
                format=format,
                stream=True
            )

            async for chunk in stream:
                yield chunk

        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            raise

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text completion

        Args:
            model: Model name
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system: System prompt
            stream: Whether to stream response

        Returns:
            Generated text
        """
        try:
            options = Options(
                temperature=temperature,
                num_predict=max_tokens or -1
            )

            response = await self.client.generate(
                model=model,
                prompt=prompt,
                system=system,
                options=options,
                stream=stream
            )

            if stream:
                # Collect streamed response
                full_response = ""
                async for chunk in response:
                    full_response += chunk.get("response", "")
                return full_response
            else:
                return response.get("response", "")

        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def embed(
        self,
        model: str,
        input_text: str
    ) -> List[float]:
        """
        Generate embeddings

        Args:
            model: Embedding model name
            input_text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings(
                model=model,
                prompt=input_text
            )

            return response.get("embedding", [])

        except Exception as e:
            logger.error(f"Ollama embed failed: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models

        Returns:
            List of model information
        """
        try:
            response = await self.client.list()

            models = []
            for model in response.get("models", []):
                models.append({
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "modified_at": model.get("modified_at"),
                    "digest": model.get("digest")
                })

            return models

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model

        Args:
            model: Model name to pull

        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {model}")

            await self.client.pull(model)

            logger.info(f"Model pulled successfully: {model}")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    async def show_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed model information

        Args:
            model: Model name

        Returns:
            Model details including parameters, template, etc.
        """
        try:
            response = await self.client.show(model)

            return {
                "license": response.get("license"),
                "modelfile": response.get("modelfile"),
                "parameters": response.get("parameters"),
                "template": response.get("template"),
                "details": response.get("details")
            }

        except Exception as e:
            logger.error(f"Failed to show model info for {model}: {e}")
            raise

    async def delete_model(self, model: str) -> bool:
        """
        Delete a model

        Args:
            model: Model name to delete

        Returns:
            True if successful
        """
        try:
            await self.client.delete(model)
            logger.info(f"Model deleted: {model}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete model {model}: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Check if Ollama server is healthy

        Returns:
            True if server is responding
        """
        try:
            await self.client.list()
            logger.debug("Ollama health check: OK")
            return True

        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def chat_with_vision(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        images: List[bytes],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Chat with vision-enabled model

        Args:
            model: Vision model name (e.g., "llama3.2-vision:11b")
            messages: Chat messages
            images: List of image bytes
            temperature: Sampling temperature

        Returns:
            Response with vision analysis
        """
        try:
            options = Options(temperature=temperature)

            response = await self.client.chat(
                model=model,
                messages=messages,
                images=images,
                options=options
            )

            return response

        except Exception as e:
            logger.error(f"Ollama vision chat failed: {e}")
            raise

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count
        Assumes ~4 characters per token on average

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    async def close(self):
        """Cleanup resources"""
        # AsyncClient doesn't require explicit cleanup
        logger.info("OllamaClient closed")
