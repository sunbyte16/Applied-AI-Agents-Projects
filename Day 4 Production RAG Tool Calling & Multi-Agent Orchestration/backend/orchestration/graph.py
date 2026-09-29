"""
LangGraph Multi-Agent Orchestration Graph for OrchestraRAG AI.
Implements dynamic conditional routing, specialized agent execution, verification loops,
bounded step execution, and human-readable execution tracing.
"""

import datetime
import time
from typing import Any, Dict, List, Literal, Optional
from langgraph.graph import END, START, StateGraph

from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.rag_agent import RAGAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.tool_agent import ToolAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.config import settings
from backend.models import AgentStatus, Evidence, ToolCallRecord, TraceEvent
from backend.orchestration.state import SharedWorkflowState


class MultiAgentGraph:
    """Production Multi-Agent Graph coordinator powered by LangGraph."""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.rag_agent = RAGAgent()
        self.research_agent = ResearchAgent()
        self.tool_agent = ToolAgent()
        self.verification_agent = VerificationAgent()
        self.synthesis_agent = SynthesisAgent()
        self.workflow = self._build_graph()

    def _add_trace(
        self,
        state: SharedWorkflowState,
        agent: str,
        action: str,
        status: str,
        details: str,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Helper to append an execution event to the state timeline."""
        now = datetime.datetime.now()
        trace_list = state.get("trace", [])
        trace_list.append(
            TraceEvent(
                event_id=f"evt_{len(trace_list) + 1}",
                timestamp=now.strftime("%H:%M:%S"),
                agent=agent,
                action=action,
                status=status,
                details=details,
                duration_ms=duration_ms,
            )
        )
        state["trace"] = trace_list

    # =========================================================================
    # Node 1: Orchestrator Node
    # =========================================================================
    def orchestrator_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Formulate execution plan and assign specialized agents."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["orchestrator"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="orchestrator",
            action="receive_request",
            status="info",
            details="User request received. Analyzing intent and scope.",
        )

        msg = self.orchestrator.run(state)
        plan_data = msg.result.get("plan", {})
        required = plan_data.get("required_agents", ["rag"])

        state["plan"] = plan_data
        state["required_agents"] = required
        state["agent_statuses"]["orchestrator"] = AgentStatus.COMPLETED.value

        # Mark non-required worker agents as skipped
        all_workers = ["rag", "research", "tool"]
        for w in all_workers:
            if w not in required:
                state["agent_statuses"][w] = AgentStatus.SKIPPED.value
            else:
                state["agent_statuses"][w] = AgentStatus.WAITING.value

        self._add_trace(
            state,
            agent="orchestrator",
            action="create_plan",
            status="completed",
            details=f"Orchestrator planned workflow. Required specialized agents: {', '.join(required).upper()}.",
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Node 2: RAG / Knowledge Agent Node
    # =========================================================================
    def rag_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Execute document retrieval."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["rag"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="rag",
            action="start_retrieval",
            status="running",
            details="Querying vector database for grounded document chunks.",
        )

        msg = self.rag_agent.run(state)
        current_evidence = state.get("evidence", [])
        current_evidence.extend(msg.evidence)
        state["evidence"] = current_evidence

        completed = state.get("completed_agents", [])
        if "rag" not in completed:
            completed.append("rag")
        state["completed_agents"] = completed

        state["agent_statuses"]["rag"] = AgentStatus.COMPLETED.value
        self._add_trace(
            state,
            agent="rag",
            action="complete_retrieval",
            status="completed",
            details=msg.summary,
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Node 3: Research Agent Node
    # =========================================================================
    def research_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Execute external web research."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["research"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="research",
            action="start_research",
            status="running",
            details="Querying external search tools for public information.",
        )

        msg = self.research_agent.run(state)
        if msg.status == "success":
            current_evidence = state.get("evidence", [])
            current_evidence.extend(msg.evidence)
            state["evidence"] = current_evidence
            state["agent_statuses"]["research"] = AgentStatus.COMPLETED.value
        else:
            state["errors"] = state.get("errors", []) + msg.errors
            state["agent_statuses"]["research"] = AgentStatus.FAILED.value

        completed = state.get("completed_agents", [])
        if "research" not in completed:
            completed.append("research")
        state["completed_agents"] = completed

        self._add_trace(
            state,
            agent="research",
            action="complete_research",
            status="completed" if msg.status == "success" else "warning",
            details=msg.summary,
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Node 4: Tool Agent Node
    # =========================================================================
    def tool_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Execute structured deterministic tool calls."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["tool"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="tool",
            action="start_tool",
            status="running",
            details="Selecting and executing structured tool.",
        )

        msg = self.tool_agent.run(state)
        current_calls = state.get("tool_calls", [])
        current_calls.extend(msg.tool_calls)
        state["tool_calls"] = current_calls

        current_res = state.get("tool_results", [])
        current_res.append(msg.result.get("output"))
        state["tool_results"] = current_res

        if msg.errors:
            state["errors"] = state.get("errors", []) + msg.errors
            state["agent_statuses"]["tool"] = AgentStatus.FAILED.value
        else:
            state["agent_statuses"]["tool"] = AgentStatus.COMPLETED.value

        completed = state.get("completed_agents", [])
        if "tool" not in completed:
            completed.append("tool")
        state["completed_agents"] = completed

        self._add_trace(
            state,
            agent="tool",
            action="complete_tool",
            status="completed" if not msg.errors else "warning",
            details=msg.summary,
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Node 5: Verification Agent Node
    # =========================================================================
    def verification_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Verify collected evidence and detect contradictions."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["verification"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="verification",
            action="start_verification",
            status="running",
            details="Checking source relevance, unsupported claims, and contradictions.",
        )

        msg = self.verification_agent.run(state)
        v_data = msg.result.get("verification", {})
        recommendation = v_data.get("recommendation", "approve")
        loop_count = state.get("verification_loop_count", 0)

        # Enforce loop bounds inside the node
        if recommendation == "retrieve_more" and loop_count < settings.MAX_VERIFICATION_LOOPS:
            state["verification_loop_count"] = loop_count + 1
            completed = [c for c in state.get("completed_agents", []) if c != "rag"]
            state["completed_agents"] = completed
            v_data["recommendation"] = "retrieve_more"
            self._add_trace(
                state,
                agent="verification",
                action="request_re_retrieval",
                status="info",
                details=f"Triggering supplementary retrieval loop ({state['verification_loop_count']}/{settings.MAX_VERIFICATION_LOOPS}).",
            )
        else:
            v_data["recommendation"] = "approve"

        state["verification"] = v_data
        state["agent_statuses"]["verification"] = AgentStatus.COMPLETED.value

        conflicts = v_data.get("conflicts_detected", [])
        conflict_note = f" (Found {len(conflicts)} conflict(s))" if conflicts else ""

        self._add_trace(
            state,
            agent="verification",
            action="complete_verification",
            status="completed",
            details=f"Verification complete: recommendation={v_data.get('recommendation')}{conflict_note}.",
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Node 6: Synthesis Agent Node
    # =========================================================================
    def synthesis_node(self, state: SharedWorkflowState) -> SharedWorkflowState:
        """Generate final grounded answer."""
        state["step_count"] = state.get("step_count", 0) + 1
        state["agent_statuses"]["synthesis"] = AgentStatus.RUNNING.value

        self._add_trace(
            state,
            agent="synthesis",
            action="start_synthesis",
            status="running",
            details="Synthesizing multi-agent outputs into final citation-grounded response.",
        )

        msg = self.synthesis_agent.run(state)
        state["final_answer"] = msg.result.get("final_answer", "")
        state["agent_statuses"]["synthesis"] = AgentStatus.COMPLETED.value
        state["end_time"] = time.perf_counter()
        state["status"] = "completed" if not state.get("errors") else "completed_with_warnings"

        self._add_trace(
            state,
            agent="synthesis",
            action="complete_synthesis",
            status="completed",
            details="Final answer produced and verified.",
            duration_ms=msg.result.get("duration_ms"),
        )
        return state

    # =========================================================================
    # Dynamic Conditional Routers
    # =========================================================================
    def _worker_router(
        self, state: SharedWorkflowState
    ) -> Literal["rag_agent", "research_agent", "tool_agent", "verification_agent"]:
        """Route to next pending required worker agent, or proceed to verification if all done."""
        if state.get("step_count", 0) >= settings.MAX_WORKFLOW_STEPS:
            return "verification_agent"

        required = state.get("required_agents", [])
        completed = state.get("completed_agents", [])

        if "rag" in required and "rag" not in completed:
            return "rag_agent"
        if "research" in required and "research" not in completed:
            return "research_agent"
        if "tool" in required and "tool" not in completed:
            return "tool_agent"

        return "verification_agent"

    def _verification_router(
        self, state: SharedWorkflowState
    ) -> Literal["rag_agent", "synthesis_agent"]:
        """Evaluate if additional evidence retrieval is required or if synthesis can proceed."""
        v_data = state.get("verification", {})
        recommendation = v_data.get("recommendation", "approve")
        if recommendation == "retrieve_more":
            return "rag_agent"
        return "synthesis_agent"

    # =========================================================================
    # Build LangGraph StateGraph
    # =========================================================================
    def _build_graph(self):
        graph = StateGraph(SharedWorkflowState)

        graph.add_node("orchestrator_agent", self.orchestrator_node)
        graph.add_node("rag_agent", self.rag_node)
        graph.add_node("research_agent", self.research_node)
        graph.add_node("tool_agent", self.tool_node)
        graph.add_node("verification_agent", self.verification_node)
        graph.add_node("synthesis_agent", self.synthesis_node)

        graph.add_edge(START, "orchestrator_agent")

        graph.add_conditional_edges(
            "orchestrator_agent",
            self._worker_router,
            {
                "rag_agent": "rag_agent",
                "research_agent": "research_agent",
                "tool_agent": "tool_agent",
                "verification_agent": "verification_agent",
            },
        )

        graph.add_conditional_edges(
            "rag_agent",
            self._worker_router,
            {
                "rag_agent": "rag_agent",
                "research_agent": "research_agent",
                "tool_agent": "tool_agent",
                "verification_agent": "verification_agent",
            },
        )
        graph.add_conditional_edges(
            "research_agent",
            self._worker_router,
            {
                "rag_agent": "rag_agent",
                "research_agent": "research_agent",
                "tool_agent": "tool_agent",
                "verification_agent": "verification_agent",
            },
        )
        graph.add_conditional_edges(
            "tool_agent",
            self._worker_router,
            {
                "rag_agent": "rag_agent",
                "research_agent": "research_agent",
                "tool_agent": "tool_agent",
                "verification_agent": "verification_agent",
            },
        )

        graph.add_conditional_edges(
            "verification_agent",
            self._verification_router,
            {
                "rag_agent": "rag_agent",
                "synthesis_agent": "synthesis_agent",
            },
        )

        graph.add_edge("synthesis_agent", END)

        return graph.compile()

    def run_workflow(
        self,
        query: str,
        task_id: str,
        mode: str = "auto",
        filter_documents: Optional[List[str]] = None,
    ) -> SharedWorkflowState:
        """Execute full end-to-end multi-agent workflow."""
        start_ts = time.perf_counter()
        initial_state: SharedWorkflowState = {
            "task_id": task_id,
            "status": "running",
            "user_query": query,
            "mode": mode,
            "filter_documents": filter_documents,
            "plan": {},
            "required_agents": [],
            "completed_agents": [],
            "evidence": [],
            "tool_calls": [],
            "tool_results": [],
            "agent_results": [],
            "agent_statuses": {
                "orchestrator": AgentStatus.WAITING.value,
                "rag": AgentStatus.WAITING.value,
                "research": AgentStatus.WAITING.value,
                "tool": AgentStatus.WAITING.value,
                "verification": AgentStatus.WAITING.value,
                "synthesis": AgentStatus.WAITING.value,
            },
            "verification": {},
            "verification_loop_count": 0,
            "final_answer": None,
            "errors": [],
            "trace": [],
            "step_count": 0,
            "start_time": start_ts,
            "end_time": None,
        }

        final_state = self.workflow.invoke(initial_state, config={"recursion_limit": 30})
        if "status" not in final_state:
            final_state["status"] = "completed" if not final_state.get("errors") else "completed_with_warnings"
        return final_state


# Global singleton
workflow_graph = MultiAgentGraph()
