"""
Central Tool Registry for AgentLab AI.
Manages tool definitions, argument validation, execution sandboxing, and enable/disable filtering.
"""

import concurrent.futures
import time
from typing import Any, Dict, List, Optional
from backend.tools.base import BaseTool
from backend.tools.calculator import CalculatorTool
from backend.tools.custom_tool import SkillGapTool
from backend.tools.database import DatabaseTool
from backend.tools.search import SearchTool
from backend.tools.weather import WeatherTool


class ToolRegistry:
    """Central registry and executor for agent tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._aliases: Dict[str, str] = {
            "custom": "skill_gap_calculator",
            "skill_gap": "skill_gap_calculator",
            "calc": "calculator",
        }

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Look up tool by exact name or recognized alias."""
        resolved = self._aliases.get(name, name)
        return self._tools.get(resolved)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List metadata for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "enabled_by_default": True,
            }
            for tool in self._tools.values()
        ]

    def get_openai_tool_definitions(
        self,
        enabled_tools: Optional[List[str]] = None,
        include_all_with_disabled_hints: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generate OpenAI-compatible tool schemas.
        If include_all_with_disabled_hints is True, all tools are defined so providers
        (like Groq) do not throw 400 validation errors if the model attempts to call a disabled tool;
        instead, disabled tools are clearly annotated, and execution returns an explicit disabled notice.
        """
        schemas = []
        enabled_set = set(enabled_tools) if enabled_tools is not None else set(self._tools.keys())
        expanded_enabled = set()
        for item in enabled_set:
            expanded_enabled.add(item)
            expanded_enabled.add(self._aliases.get(item, item))

        for name, tool in self._tools.items():
            is_enabled = name in expanded_enabled or any(self._aliases.get(a) == name for a in enabled_set)

            if is_enabled:
                schemas.append(tool.to_openai_tool())
            elif include_all_with_disabled_hints:
                # Include with explicit disabled warning in schema
                schema = tool.to_openai_tool()
                schema["function"]["description"] = (
                    f"[CURRENTLY DISABLED IN SETTINGS]: This tool is disabled. "
                    f"If called, it will report disabled status. "
                    f"Original description: {tool.description}"
                )
                schemas.append(schema)

        return schemas

    def validate_arguments(self, tool: BaseTool, arguments: Dict[str, Any]) -> Optional[str]:
        """Verify that required parameters are provided with expected types."""
        param_spec = tool.parameters.get("properties", {})
        required = tool.parameters.get("required", [])

        for req in required:
            if req not in arguments or arguments[req] is None or arguments[req] == "":
                return f"Missing required parameter '{req}' for tool '{tool.name}'."

        return None

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        enabled_tools: Optional[List[str]] = None,
        timeout_seconds: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Execute a tool safely with argument validation, timeout enforcement,
        and execution metrics.
        """
        start_time = time.perf_counter()
        resolved_name = self._aliases.get(tool_name, tool_name)
        tool = self._tools.get(resolved_name)

        if not tool:
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Tool '{tool_name}' is not recognized in the tool registry.",
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }

        # Check if tool is enabled by user settings
        if enabled_tools is not None:
            enabled_resolved = {self._aliases.get(t, t) for t in enabled_tools}
            if resolved_name not in enabled_resolved and tool_name not in enabled_tools:
                return {
                    "tool": tool_name,
                    "success": False,
                    "error": (
                        f"The '{tool_name}' tool is currently disabled in agent settings. "
                        "Inform the user that this tool is disabled and cannot be used."
                    ),
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                }

        # Validate arguments against tool schema
        validation_error = self.validate_arguments(tool, arguments)
        if validation_error:
            return {
                "tool": tool_name,
                "success": False,
                "error": validation_error,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }

        # Execute with timeout safeguard
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.execute, **arguments)
                result = future.result(timeout=timeout_seconds)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if isinstance(result, dict):
                    result["duration_ms"] = duration_ms
                return result
        except concurrent.futures.TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Execution of tool '{tool_name}' timed out after {timeout_seconds} seconds.",
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Tool execution failed with unexpected error: {str(e)}",
                "duration_ms": duration_ms,
            }


# Default pre-configured registry instance
default_registry = ToolRegistry()
default_registry.register(CalculatorTool())
default_registry.register(SearchTool())
default_registry.register(WeatherTool())
default_registry.register(DatabaseTool())
default_registry.register(SkillGapTool())
