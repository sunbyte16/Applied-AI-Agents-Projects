"""
Shared State definition for OrchestraRAG AI multi-agent workflows.
Typed data structure passed through the LangGraph StateGraph nodes.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from backend.models import Evidence, ToolCallRecord, TraceEvent


class SharedWorkflowState(TypedDict, total=False):
    """Shared workflow state across all agents in the LangGraph orchestration cycle."""
    task_id: str
    status: str  # "running" | "completed" | "completed_with_warnings" | "failed"
    user_query: str
    mode: str  # "auto" | "simple" | "advanced"
    filter_documents: Optional[List[str]]

    # Planning & routing
    plan: Dict[str, Any]
    required_agents: List[str]
    completed_agents: List[str]

    # Collected artifacts
    evidence: List[Evidence]
    tool_calls: List[ToolCallRecord]
    tool_results: List[Any]
    agent_results: List[Dict[str, Any]]
    agent_statuses: Dict[str, str]

    # Verification & loops
    verification: Dict[str, Any]
    verification_loop_count: int

    # Final output & tracking
    final_answer: Optional[str]
    errors: List[str]
    trace: List[TraceEvent]
    step_count: int
    start_time: float
    end_time: Optional[float]
