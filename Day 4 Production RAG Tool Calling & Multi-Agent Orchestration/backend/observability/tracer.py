"""
Observability and Execution Tracer for OrchestraRAG AI.
Records granular execution spans, latency metrics, token consumption metadata, and human-readable timelines.
"""

import time
from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.models import TraceEvent, WorkflowResponse


class ExecutionTracer:
    """Production observability engine capturing task execution spans and performance telemetry."""

    def __init__(self):
        self._history: Dict[str, Dict[str, Any]] = {}

    def record_run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compute execution metrics from completed workflow state."""
        task_id = state.get("task_id", "unknown")
        start_ts = state.get("start_time", time.perf_counter())
        end_ts = state.get("end_time") or time.perf_counter()
        total_duration_sec = round(end_ts - start_ts, 3)

        evidence = state.get("evidence", [])
        tool_calls = state.get("tool_calls", [])
        trace = state.get("trace", [])
        errors = state.get("errors", [])
        statuses = state.get("agent_statuses", {})

        agents_active = [a for a, s in statuses.items() if s == "completed"]
        agents_skipped = [a for a, s in statuses.items() if s == "skipped"]
        agents_failed = [a for a, s in statuses.items() if s == "failed"]

        metrics = {
            "task_id": task_id,
            "status": "completed" if not agents_failed else "completed_with_warnings",
            "total_duration_sec": total_duration_sec,
            "total_workflow_steps": state.get("step_count", 0),
            "agents_executed_count": len(agents_active),
            "agents_executed": agents_active,
            "agents_skipped": agents_skipped,
            "agents_failed": agents_failed,
            "evidence_chunks_retrieved": len(evidence),
            "tool_calls_executed": len(tool_calls),
            "verification_loops": state.get("verification_loop_count", 0),
            "errors_logged": len(errors),
            "llm_provider": settings.get_active_llm_provider(),
            "model_name": settings.DEFAULT_MODEL,
            "token_usage": "Usage metrics unavailable (streaming/Groq direct)"
            if settings.get_active_llm_provider() == "groq"
            else "Standard API tracking",
        }

        self._history[task_id] = {
            "metrics": metrics,
            "trace": trace,
            "evidence": evidence,
            "tool_calls": tool_calls,
        }
        return metrics

    def get_task_trace(self, task_id: str) -> List[TraceEvent]:
        """Retrieve trace events for task."""
        record = self._history.get(task_id, {})
        return record.get("trace", [])

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve telemetry metrics for task."""
        record = self._history.get(task_id)
        return record.get("metrics") if record else None


# Global singleton tracer
tracer = ExecutionTracer()
