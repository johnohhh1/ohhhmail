"""
ChiliHead OpsManager v2.1 - AI Agents Module
All AI agents for email processing
"""

from .base import BaseAgent, AgentResult, DolphinWorkerBase
from .triage import TriageAgent
from .vision import VisionAgent
from .deadline import DeadlineAgent
from .task import TaskAgent
from .context import ContextAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "DolphinWorkerBase",
    "TriageAgent",
    "VisionAgent",
    "DeadlineAgent",
    "TaskAgent",
    "ContextAgent",
]
