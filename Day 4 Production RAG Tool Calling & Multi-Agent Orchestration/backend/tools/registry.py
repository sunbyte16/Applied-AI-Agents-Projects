"""
Central Tool Registry for OrchestraRAG AI.
Manages tool discovery, schema generation, role-based tool scoping, and safe execution.
"""

from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.tools.base import BaseTool
from backend.tools.calculator import SafeCalculator
from backend.tools.database import DatabaseTool
from backend.tools.weather import WeatherTool
from backend.tools.search import SearchTool
from backend.tools.custom_tool import CustomAnalyticsTool


class ToolRegistry:
    """Central registry of executable tools for agents."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the built-in tool suite."""
        self.register(SafeCalculator())
        self.register(DatabaseTool())
        self.register(WeatherTool())
        self.register(SearchTool())
        self.register(CustomAnalyticsTool())

    def register(self, tool: BaseTool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """Return list of all registered tools."""
        return list(self._tools.values())

    def get_tool_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get standard function schemas for LLM tool calling."""
        names = tool_names or list(self._tools.keys())
        schemas = []
        for name in names:
            if name in self._tools:
                schemas.append(self._tools[name].to_openai_schema())
        return schemas

    def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        timeout: float = settings.TOOL_TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """Execute tool by name with arguments and timeout guard."""
        tool = self.get(name)
        if not tool:
            return {
                "tool_name": name,
                "success": False,
                "error": f"Tool '{name}' is not registered in the system.",
            }
        return tool.run_safe(timeout_seconds=timeout, **arguments)


# Global singleton instance
tool_registry = ToolRegistry()
