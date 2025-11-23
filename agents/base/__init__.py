"""
ChiliHead OpsManager v2.1 - Base Agent Framework
"""

from .agent_contract import BaseAgent, AgentResult
from .worker_base import DolphinWorkerBase

__all__ = ["BaseAgent", "AgentResult", "DolphinWorkerBase"]
