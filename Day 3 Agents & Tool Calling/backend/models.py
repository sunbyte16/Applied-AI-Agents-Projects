"""
Data Models and Request/Response Schemas for AgentLab AI.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Conversation history message."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request payload for /api/chat."""
    message: str = Field(..., min_length=1, description="User prompt or question.")
    enabled_tools: Optional[List[str]] = Field(
        default=["calculator", "search", "weather", "database", "custom"],
        description="List of tool names enabled for this conversation turn.",
    )
    model: Optional[str] = Field(None, description="LLM model identifier.")
    temperature: Optional[float] = Field(0.2, ge=0.0, le=1.0, description="Sampling temperature.")
    max_tool_calls: Optional[int] = Field(5, ge=1, le=15, description="Maximum number of sequential tool calls.")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns.")


class TraceEvent(BaseModel):
    """An event representing a single step in the agent's execution process."""
    step: int
    type: str  # 'start', 'thought', 'tool_call', 'tool_result', 'direct_response', 'final_answer', 'error'
    message: Optional[str] = None
    tool: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    duration_ms: Optional[float] = None
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    """Response payload for /api/chat."""
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    answer: str
    trace: List[TraceEvent]
    tool_calls_executed: int
    model_used: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response for /api/health."""
    status: str
    llm_configured: bool
    provider: str
    default_model: str
    tools_available: int


class ToolExecuteRequest(BaseModel):
    """Payload to test-execute an individual tool directly."""
    tool_name: str
    arguments: Dict[str, Any]
