"""
BaseAgent abstract class for OrchestraRAG AI.
Standardizes agent communication protocol, error boundaries, and trace generation.
"""

import abc
import datetime
import time
from typing import Any, Dict, List, Optional
from backend.models import AgentMessage, AgentRole, Evidence, ToolCallRecord, TraceEvent


class BaseAgent(abc.ABC):
    """Abstract base class for all specialized agents."""

    role: AgentRole
    description: str = ""

    def __init__(self):
        pass

    def create_message(
        self,
        to_agent: str,
        task_id: str,
        status: str = "success",
        summary: str = "",
        evidence: Optional[List[Evidence]] = None,
        tool_calls: Optional[List[ToolCallRecord]] = None,
        result: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
    ) -> AgentMessage:
        """Construct a standardized agent message for shared state communication."""
        return AgentMessage(
            from_agent=self.role.value,
            to_agent=to_agent,
            task_id=task_id,
            status=status,
            summary=summary,
            evidence=evidence or [],
            tool_calls=tool_calls or [],
            result=result or {},
            errors=errors or [],
            timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
        )

    def create_trace_event(
        self,
        action: str,
        status: str,
        details: str,
        duration_ms: Optional[float] = None,
    ) -> TraceEvent:
        """Create an execution trace event."""
        now = datetime.datetime.now()
        event_id = f"evt_{now.strftime('%H%M%S%f')[:10]}"
        return TraceEvent(
            event_id=event_id,
            timestamp=now.strftime("%H:%M:%S"),
            agent=self.role.value,
            action=action,
            status=status,
            details=details,
            duration_ms=duration_ms,
        )

    @abc.abstractmethod
    def run(self, state: Dict[str, Any]) -> AgentMessage:
        """Execute agent's specialized task given the shared workflow state."""
        pass
