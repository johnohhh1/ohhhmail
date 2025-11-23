"""
Dolphin Scheduler Plugins
Custom operators and integrations for email processing orchestration
"""

from .uitars_plugin import UITARSPlugin, CheckpointManager

__all__ = [
    "UITARSPlugin",
    "CheckpointManager",
]

# Plugin registry
__plugins__ = {
    "uitars": UITARSPlugin,
}
