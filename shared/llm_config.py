"""
ChiliHead OpsManager v2.1 - LLM Provider Configuration
Multi-provider support: OpenAI (GPT-4o, GPT-5), Anthropic (Claude), Ollama
"""

from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
import os


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """LLM configuration for an agent"""
    provider: LLMProvider
    model: str
    fallback_provider: Optional[LLMProvider] = None
    fallback_model: Optional[str] = None
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    gpu_required: bool = False


class LLMClientFactory:
    """Factory for creating LLM clients based on provider"""

    @staticmethod
    def get_client(config: LLMConfig) -> Any:
        """Get appropriate LLM client based on provider"""
        if config.provider == LLMProvider.OPENAI:
            from openai import AsyncOpenAI
            return AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
        elif config.provider == LLMProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        elif config.provider == LLMProvider.OLLAMA:
            import ollama
            return ollama.AsyncClient(
                host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")


class AgentModelConfig:
    """Model configuration for all agents"""

    @staticmethod
    def from_env() -> Dict[str, LLMConfig]:
        """Load agent configurations from environment variables"""

        def parse_agent_config(agent_name: str, default_provider: str, default_model: str) -> LLMConfig:
            """Parse agent config from environment"""
            provider_key = f"{agent_name.upper()}_AGENT_PROVIDER"
            model_key = f"{agent_name.upper()}_AGENT_MODEL"
            fallback_key = f"{agent_name.upper()}_AGENT_FALLBACK"
            timeout_key = f"{agent_name.upper()}_AGENT_TIMEOUT"
            gpu_key = f"{agent_name.upper()}_AGENT_GPU"

            provider_str = os.getenv(provider_key, default_provider)
            model = os.getenv(model_key, default_model)
            fallback_str = os.getenv(fallback_key, "")
            timeout = int(os.getenv(timeout_key, "30"))
            gpu_required = os.getenv(gpu_key, "false").lower() == "true"

            # Parse fallback if provided (format: "provider:model")
            fallback_provider = None
            fallback_model = None
            if fallback_str and fallback_str.upper() != "DISABLED":
                if ":" in fallback_str:
                    fb_provider, fb_model = fallback_str.split(":", 1)
                    fallback_provider = LLMProvider(fb_provider)
                    fallback_model = fb_model

            return LLMConfig(
                provider=LLMProvider(provider_str),
                model=model,
                fallback_provider=fallback_provider,
                fallback_model=fallback_model,
                timeout=timeout,
                gpu_required=gpu_required
            )

        return {
            "triage": parse_agent_config(
                "triage",
                "ollama",
                "llama3.2:8b-instruct"
            ),
            "vision": parse_agent_config(
                "vision",
                "openai",
                "gpt-4o"
            ),
            "deadline": parse_agent_config(
                "deadline",
                "ollama",
                "llama3.2:8b-instruct"
            ),
            "task": parse_agent_config(
                "task",
                "ollama",
                "llama3.2:8b-instruct"
            ),
            "context": parse_agent_config(
                "context",
                "anthropic",
                "claude-sonnet-4"
            )
        }


# Example usage:
"""
from shared.llm_config import AgentModelConfig, LLMClientFactory

# Load all agent configs
configs = AgentModelConfig.from_env()

# Get triage agent config
triage_config = configs["triage"]
print(f"Triage using: {triage_config.provider}:{triage_config.model}")

# Create client
client = LLMClientFactory.get_client(triage_config)

# Use client
response = await client.chat.completions.create(
    model=triage_config.model,
    messages=[...],
    timeout=triage_config.timeout
)
"""


# Available Models Reference:
AVAILABLE_MODELS = {
    "openai": [
        "gpt-4o",           # Latest GPT-4 with vision
        "gpt-4o-mini",      # Faster, cheaper GPT-4
        "gpt-4-turbo",      # Previous generation
        "o1-preview",       # Reasoning model
        "o1-mini",          # Smaller reasoning model
        # Note: GPT-5 models when available
    ],
    "anthropic": [
        "claude-sonnet-4",      # Latest Claude Sonnet
        "claude-3-5-sonnet-20241022",  # Previous version
        "claude-opus-4",        # Claude Opus (most capable)
        "claude-3-opus-20240229",
        "claude-haiku-3",       # Fastest Claude
    ],
    "ollama": [
        "llama3.2:8b-instruct",     # Meta Llama 3.2 8B
        "llama3.2-vision:11b",      # Llama with vision
        "qwen:110b",                # Large Chinese model
        "mixtral:8x22b",            # Mixtral MoE
        "deepseek-coder:33b",       # Code specialist
        "phi3:14b",                 # Microsoft Phi-3
    ]
}
