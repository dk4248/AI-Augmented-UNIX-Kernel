"""
Shell AI Assistant Package
A natural language to shell command translator
"""

__version__ = "1.0.0"
__author__ = "Shell AI Team"

from .assistant import ShellAIAssistant
from .config import Config
from .command_executor import CommandExecutor
from .system_info import SystemInfo

__all__ = [
    "ShellAIAssistant",
    "Config", 
    "CommandExecutor",
    "SystemInfo"
]