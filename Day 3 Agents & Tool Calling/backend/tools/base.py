"""
Base Tool Interface and Data Contracts for AgentLab AI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract base class for all tools available to the Agent."""

    name: str
    description: str
    parameters: Dict[str, Any]

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert tool schema into the standard OpenAI Function / Tool Calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the tool with validated arguments.
        Must return a dictionary containing at least:
        {"success": bool, ...}
        """
        raise NotImplementedError("Subclasses must implement execute()")
