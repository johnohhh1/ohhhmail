"""
AUBS Configuration Management
Load and validate settings from environment variables
"""

import os
from typing import Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.models import AgentConfig
from shared.llm_config import AgentModelConfig, LLMConfig


class AUBSSettings(BaseSettings):
    """AUBS configuration from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Service Configuration
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")

    # External Service URLs
    dolphin_url: str = Field(
        default="http://dolphin-server:12345",
        description="Dolphin server URL"
    )
    ui_tars_url: str = Field(
        default="http://uitars:8080",
        description="UI-TARS service URL"
    )
    nats_url: str = Field(
        default="nats://nats:4222",
        description="NATS server URL"
    )
    supabase_url: str = Field(
        default="http://supabase:8000",
        description="Supabase URL"
    )
    supabase_key: str = Field(
        default="",
        description="Supabase API key"
    )

    # Orchestration Settings
    confidence_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for automated actions"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for failed tasks"
    )
    execution_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Maximum execution time in seconds"
    )

    # Agent Configurations
    triage_agent_provider: str = Field(default="ollama")
    triage_agent_model: str = Field(default="llama3.2:8b-instruct")
    triage_agent_timeout: int = Field(default=15)
    triage_agent_gpu: bool = Field(default=False)

    vision_agent_provider: str = Field(default="openai")
    vision_agent_model: str = Field(default="gpt-4o")
    vision_agent_timeout: int = Field(default=30)
    vision_agent_gpu: bool = Field(default=False)

    deadline_agent_provider: str = Field(default="ollama")
    deadline_agent_model: str = Field(default="llama3.2:8b-instruct")
    deadline_agent_timeout: int = Field(default=15)
    deadline_agent_gpu: bool = Field(default=False)

    task_agent_provider: str = Field(default="ollama")
    task_agent_model: str = Field(default="llama3.2:8b-instruct")
    task_agent_timeout: int = Field(default=15)
    task_agent_gpu: bool = Field(default=False)

    context_agent_provider: str = Field(default="anthropic")
    context_agent_model: str = Field(default="claude-sonnet-4")
    context_agent_timeout: int = Field(default=30)
    context_agent_gpu: bool = Field(default=False)
    context_agent_fallback: str = Field(default="DISABLED")

    # MCP Tool Settings
    mcp_todoist_enabled: bool = Field(default=True)
    mcp_gcal_enabled: bool = Field(default=True)
    mcp_twilio_enabled: bool = Field(default=True)

    # High-Risk Detection
    high_risk_keywords: str = Field(
        default="fire,lawsuit,inspection,deadline,urgent,overdue",
        description="Comma-separated keywords for high-risk detection"
    )

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold is reasonable"""
        if v < 0.5:
            raise ValueError("Confidence threshold too low, must be >= 0.5")
        return v

    @field_validator("high_risk_keywords")
    @classmethod
    def validate_keywords(cls, v: str) -> str:
        """Ensure keywords are properly formatted"""
        return v.lower().strip()

    def get_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get agent configurations as AgentConfig objects"""
        return {
            "triage": AgentConfig(
                model=self.triage_agent_model,
                timeout=self.triage_agent_timeout,
                gpu=self.triage_agent_gpu,
                fallback_allowed=True,
                max_retries=self.max_retries
            ),
            "vision": AgentConfig(
                model=self.vision_agent_model,
                timeout=self.vision_agent_timeout,
                gpu=self.vision_agent_gpu,
                fallback_allowed=True,
                max_retries=self.max_retries
            ),
            "deadline": AgentConfig(
                model=self.deadline_agent_model,
                timeout=self.deadline_agent_timeout,
                gpu=self.deadline_agent_gpu,
                fallback_allowed=True,
                max_retries=self.max_retries
            ),
            "task": AgentConfig(
                model=self.task_agent_model,
                timeout=self.task_agent_timeout,
                gpu=self.task_agent_gpu,
                fallback_allowed=True,
                max_retries=self.max_retries
            ),
            "context": AgentConfig(
                model=self.context_agent_model,
                timeout=self.context_agent_timeout,
                gpu=self.context_agent_gpu,
                fallback_allowed=False,  # CRITICAL - NO FALLBACK
                max_retries=self.max_retries
            )
        }

    def get_llm_configs(self) -> Dict[str, LLMConfig]:
        """Get LLM configurations from environment"""
        return AgentModelConfig.from_env()

    def get_high_risk_keywords(self) -> list[str]:
        """Get list of high-risk keywords"""
        return [k.strip() for k in self.high_risk_keywords.split(",")]


# Global settings instance
settings = AUBSSettings()
