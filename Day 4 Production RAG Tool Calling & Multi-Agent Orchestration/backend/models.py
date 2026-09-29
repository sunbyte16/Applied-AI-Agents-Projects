"""
OrchestraRAG AI - Typed Data Models
Defines Pydantic schemas for multi-agent messages, shared state, evidence, traces, and API payloads.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Specialized agents in OrchestraRAG AI."""
    ORCHESTRATOR = "orchestrator"
    RAG = "rag"
    RESEARCH = "research"
    TOOL = "tool"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"


class AgentStatus(str, Enum):
    """Lifecycle status of each agent during workflow execution."""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Evidence(BaseModel):
    """Standardized evidence structure for document and external web sources."""
    source_type: str = Field(..., description="'document' or 'web'")
    document: Optional[str] = Field(None, description="Filename for document source")
    page: Optional[int] = Field(None, description="1-indexed page number if available")
    chunk_id: Optional[int] = Field(None, description="Index of the retrieved chunk")
    content: Optional[str] = Field(None, description="Retrieved passage / snippet")
    relevance: Optional[float] = Field(None, description="Cosine similarity score (0.0 to 1.0)")
    title: Optional[str] = Field(None, description="Web title or source headline")
    url: Optional[str] = Field(None, description="Source URL (only if actually retrieved)")
    snippet: Optional[str] = Field(None, description="Raw passage or search snippet")
    summary: Optional[str] = Field(None, description="Brief summary of source finding")


class ToolCallRecord(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    success: bool = True
    duration_ms: float = 0.0
    error: Optional[str] = None


class AgentMessage(BaseModel):
    """Structured message protocol for agent-to-agent communication."""
    from_agent: str
    to_agent: str
    task_id: str
    status: str = "success"  # "success" | "error" | "skipped"
    summary: str = ""
    evidence: List[Evidence] = Field(default_factory=list)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    result: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    timestamp: Optional[str] = None


class TraceEvent(BaseModel):
    """Event in the human-readable and machine-readable execution trace timeline."""
    event_id: str
    timestamp: str
    agent: str
    action: str
    status: str
    details: str
    duration_ms: Optional[float] = None


class VerificationResult(BaseModel):
    """Structured verification assessment output."""
    is_verified: bool = True
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    conflicts_detected: List[str] = Field(default_factory=list)
    hallucination_risk: str = "low"  # "low" | "medium" | "high"
    recommendation: str = "approve"  # "approve" | "retrieve_more" | "reject"
    details: str = "Evidence supports proposed conclusions."


class TaskPlan(BaseModel):
    """Task decomposition and dynamic routing plan created by the Orchestrator."""
    task_id: str
    intent: str
    complexity: str = "simple"  # "simple" | "complex"
    required_agents: List[str] = Field(default_factory=list)
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    rationale: str = ""


class WorkflowRequest(BaseModel):
    """Request payload for running a multi-agent workflow."""
    query: str
    mode: str = Field(default="auto", description="'auto' | 'simple' | 'advanced'")
    filter_documents: Optional[List[str]] = Field(default=None, description="Optional doc filter")


class WorkflowResponse(BaseModel):
    """Complete workflow response with answers, evidence, tool records, and traces."""
    task_id: str
    status: str
    user_query: str
    final_answer: Optional[str] = None
    agents_used: List[str] = Field(default_factory=list)
    agent_statuses: Dict[str, str] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    verification: Optional[VerificationResult] = None
    trace: List[TraceEvent] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Metadata for uploaded knowledge base documents."""
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str
    file_size_bytes: int
    status: str = "indexed"
