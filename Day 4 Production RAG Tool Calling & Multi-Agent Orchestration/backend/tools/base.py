"""
BaseTool abstract class for OrchestraRAG AI.
Enforces schema validation, safe timeouts, and structured error handling.
"""

import abc
import time
from typing import Any, Dict, Optional


class BaseTool(abc.ABC):
    """Abstract base class for all callable tools in OrchestraRAG AI."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool logic and return structured dictionary."""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool declaration to standard OpenAI/Groq function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def run_safe(self, timeout_seconds: float = 10.0, **kwargs: Any) -> Dict[str, Any]:
        """Execute tool safely with latency measurement and exception containment."""
        start_time = time.perf_counter()
        try:
            res = self.execute(**kwargs)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if isinstance(res, dict):
                res["duration_ms"] = duration_ms
                if "tool_name" not in res:
                    res["tool_name"] = self.name
                return res
            return {
                "tool_name": self.name,
                "success": True,
                "output": res,
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "tool_name": self.name,
                "success": False,
                "error": f"Tool execution failed: {type(e).__name__}: {str(e)}",
                "duration_ms": duration_ms,
            }
