"""
ChiliHead OpsManager v2.1 - Client Libraries
Shared clients for external services
"""

from shared.clients.dolphin_client import DolphinClient
from shared.clients.nats_client import NATSClient
from shared.clients.qdrant_client import QdrantVectorClient
from shared.clients.ollama_client import OllamaClient
from shared.clients.uitars_client import UITARSClient
from shared.clients.llm_client import LLMClient, LLMResponse, create_llm_client

__all__ = [
    "DolphinClient",
    "NATSClient",
    "QdrantVectorClient",
    "OllamaClient",
    "UITARSClient",
    "LLMClient",
    "LLMResponse",
    "create_llm_client",
]
