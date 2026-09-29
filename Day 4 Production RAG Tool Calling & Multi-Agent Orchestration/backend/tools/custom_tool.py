"""
Custom Analytics Tool for OrchestraRAG AI.
Calculates percentage improvements, statistical metrics, and quantitative comparisons.
"""

from typing import Any, Dict, List, Optional
from backend.tools.base import BaseTool


class CustomAnalyticsTool(BaseTool):
    """Tool for specialized analytical computations like percentage improvement and statistical metrics."""

    name = "analytics"
    description = (
        "Compute analytical metrics such as percentage improvement, percentage difference, "
        "relative increase, and summary statistics across numerical figures. "
        "Useful for calculating benchmark improvements, e.g., comparing baseline accuracy to RAG accuracy."
    )
    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["percentage_improvement", "percentage_difference", "summary_statistics"],
                "description": "The mathematical analysis operation to execute.",
            },
            "baseline_value": {
                "type": "number",
                "description": "Baseline initial value (for percentage improvement), e.g. 60.0.",
            },
            "new_value": {
                "type": "number",
                "description": "New/improved value (for percentage improvement), e.g. 90.0.",
            },
            "values": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of numbers for summary statistics.",
            },
        },
        "required": ["operation"],
    }

    def execute(
        self,
        operation: str = "percentage_improvement",
        baseline_value: Optional[float] = None,
        new_value: Optional[float] = None,
        values: Optional[List[float]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Compute the requested analytics operation."""
        op = (operation or "").strip().lower()

        if op in ("percentage_improvement", "percentage_difference"):
            if baseline_value is None or new_value is None:
                return {
                    "tool_name": self.name,
                    "success": False,
                    "error": "Both 'baseline_value' and 'new_value' must be provided for percentage calculations.",
                }
            if baseline_value == 0:
                return {
                    "tool_name": self.name,
                    "success": False,
                    "error": "Baseline value cannot be zero when calculating percentage improvement.",
                }

            abs_diff = round(new_value - baseline_value, 4)
            pct_change = round(((new_value - baseline_value) / abs(baseline_value)) * 100, 2)
            ratio = round(new_value / baseline_value, 4)

            return {
                "tool_name": self.name,
                "success": True,
                "operation": op,
                "baseline": baseline_value,
                "new_value": new_value,
                "absolute_difference": abs_diff,
                "percentage_change": pct_change,
                "percentage_improvement_formatted": f"{pct_change:+0.2f}%",
                "ratio": ratio,
            }

        elif op == "summary_statistics":
            if not values or not isinstance(values, list) or len(values) == 0:
                return {
                    "tool_name": self.name,
                    "success": False,
                    "error": "A non-empty list of numbers must be provided for summary statistics.",
                }

            import statistics
            return {
                "tool_name": self.name,
                "success": True,
                "operation": op,
                "count": len(values),
                "sum": round(sum(values), 4),
                "mean": round(statistics.mean(values), 4),
                "median": round(statistics.median(values), 4),
                "min": min(values),
                "max": max(values),
                "stdev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            }

        return {
            "tool_name": self.name,
            "success": False,
            "error": f"Unsupported analytics operation: '{operation}'.",
        }
