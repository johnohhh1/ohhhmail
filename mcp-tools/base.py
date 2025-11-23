"""
Base MCP Tool Class

Provides common functionality for all MCP tool implementations.
"""

from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pydantic import BaseModel, Field


class MCPToolError(Exception):
    """Base exception for MCP tools."""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ResultStatus(str, Enum):
    """Result status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class MCPToolResult:
    """Standard result format for all MCP tools."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> ResultStatus:
        """Get result status."""
        if self.success:
            return ResultStatus.SUCCESS
        elif self.data is not None:
            return ResultStatus.PARTIAL
        return ResultStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            "success": self.success,
            "status": self.status.value,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.error_code is not None:
            result["error_code"] = self.error_code
        if self.error_details:
            result["error_details"] = self.error_details
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class MCPToolConfig(BaseModel):
    """Base configuration for MCP tools."""

    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    rate_limit: Optional[int] = Field(default=None, description="Rate limit per minute")

    class Config:
        extra = "allow"


T = TypeVar("T", bound=MCPToolConfig)


class MCPToolBase(Generic[T]):
    """
    Base class for all MCP tool implementations.

    Provides:
    - HTTP client setup
    - Error handling
    - Retry logic
    - Response validation
    - Logging
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP tool.

        Args:
            config: Configuration dictionary
        """
        self.config = self._create_config(config)
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._setup_logging()

    def _create_config(self, config: Dict[str, Any]) -> T:
        """
        Create typed configuration object.

        Args:
            config: Configuration dictionary

        Returns:
            Typed configuration object
        """
        # Override in subclasses to return specific config type
        return MCPToolConfig(**config)  # type: ignore

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logger.add(
            f"logs/{self.__class__.__name__.lower()}.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
        )

    async def initialize(self) -> None:
        """Initialize the tool and setup HTTP client."""
        if self._initialized:
            return

        if not self.config.enabled:
            logger.info(f"{self.__class__.__name__} is disabled")
            self._initialized = True
            return

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._get_headers(),
            base_url=self.config.base_url,
        )

        await self._on_initialize()
        self._initialized = True
        logger.info(f"{self.__class__.__name__} initialized successfully")

    async def _on_initialize(self) -> None:
        """Override in subclasses for custom initialization."""
        pass

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for requests.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"MCP-Tools/{self.__class__.__name__}/1.0",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            HTTP response

        Raises:
            MCPToolError: If request fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.config.enabled:
            raise MCPToolError(
                f"{self.__class__.__name__} is disabled",
                code="TOOL_DISABLED",
            )

        if self.client is None:
            raise MCPToolError(
                "HTTP client not initialized",
                code="CLIENT_NOT_INITIALIZED",
            )

        try:
            logger.debug(f"Making {method} request to {endpoint}")

            request_headers = self._get_headers()
            if headers:
                request_headers.update(headers)

            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=request_headers,
            )

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise MCPToolError(
                f"HTTP request failed: {e.response.status_code}",
                code=f"HTTP_{e.response.status_code}",
                details={"response": e.response.text},
            )
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise MCPToolError(
                "Request timed out",
                code="TIMEOUT",
                details={"timeout": self.config.timeout},
            )
        except httpx.NetworkError as e:
            logger.error(f"Network error: {e}")
            raise MCPToolError(
                "Network error occurred",
                code="NETWORK_ERROR",
                details={"error": str(e)},
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise MCPToolError(
                f"Unexpected error: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)},
            )

    def _create_result(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        **metadata,
    ) -> MCPToolResult:
        """
        Create standardized result object.

        Args:
            success: Whether operation was successful
            data: Result data
            error: Error message
            error_code: Error code
            error_details: Error details
            **metadata: Additional metadata

        Returns:
            MCPToolResult object
        """
        return MCPToolResult(
            success=success,
            data=data,
            error=error,
            error_code=error_code,
            error_details=error_details,
            metadata=metadata,
        )

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._initialized = False
        logger.info(f"{self.__class__.__name__} closed")

    async def health_check(self) -> bool:
        """
        Check if the tool is healthy and operational.

        Returns:
            True if healthy, False otherwise
        """
        if not self.config.enabled:
            return False

        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                logger.error(f"Health check failed during initialization: {e}")
                return False

        return await self._health_check_impl()

    async def _health_check_impl(self) -> bool:
        """
        Override in subclasses for custom health check.

        Returns:
            True if healthy, False otherwise
        """
        return self.client is not None

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(enabled={self.config.enabled}, initialized={self._initialized})"
