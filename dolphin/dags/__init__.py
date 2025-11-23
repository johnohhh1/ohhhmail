"""
Dolphin DAG Definitions
Email processing task graphs for the ohhhmail orchestration system
"""

from .email_processing import EmailProcessingDAG

__all__ = ["EmailProcessingDAG"]

# DAG registry - automatically discovered by Dolphin
__dags__ = {
    "email_processing": EmailProcessingDAG,
}
