"""
Orchestrator Agent for OrchestraRAG AI.
Analyzes user intent, performs dynamic task decomposition, and routes execution to specialized agents.
Optimizes execution by skipping unnecessary agents for simple queries.
"""

import time
from typing import Any, Dict, List
from backend.agents.base import BaseAgent
from backend.llm import llm_client
from backend.models import AgentMessage, AgentRole, TaskPlan


class OrchestratorAgent(BaseAgent):
    """The central coordinating agent that plans and directs multi-agent workflows."""

    role = AgentRole.ORCHESTRATOR
    description = "Decomposes complex requests, assigns subtasks to specialized agents, and optimizes routing."

    _SYSTEM_PROMPT = """You are the master Orchestrator Agent in the OrchestraRAG AI platform.
Your job is to analyze the user's task and decide which specialized worker agents are strictly necessary to fulfill it.

Available specialized agents:
- 'rag': Searches the uploaded internal document knowledge base (vector database) for policies, technical guides, benchmarks, and corporate documents.
- 'research': Searches the external live web for current real-world developments, recent news, or industry trends beyond the internal documents.
- 'tool': Performs deterministic calculations (arithmetic, percentage improvement), queries the structured SQL database (employees, salaries, leave balances), or queries live weather.

Routing Optimization Rules:
1. Pure calculation (e.g., "What is 8492 * 372?"): select ONLY ['tool']. Do NOT invoke RAG or research.
2. Pure internal document query (e.g., "What does the uploaded company policy say about vacation?"): select ONLY ['rag']. Do NOT invoke research or tool.
3. Pure external query (e.g., "Find recent information about RAG systems"): select ONLY ['research'].
4. Multi-agent complex query (e.g., "Explain how RAG works from the document, find recent external developments, and calculate the improvement percentage"): select ['rag', 'research', 'tool'].

Respond with valid JSON strictly adhering to:
{
  "intent": "<brief description of user intent>",
  "complexity": "simple" | "complex",
  "required_agents": ["rag" | "research" | "tool"],
  "subtasks": [
    {"agent": "rag", "task": "<specific retrieval query>"},
    {"agent": "research", "task": "<specific external web search query>"},
    {"agent": "tool", "task": "<tool subtask description>", "tool_name": "calculator" | "database" | "weather" | "analytics", "args": {...}}
  ],
  "rationale": "<brief explanation of why these agents were selected>"
}"""

    def _fallback_heuristic_planner(self, query: str, task_id: str) -> TaskPlan:
        """Heuristic planner when LLM is unavailable or for instant deterministic testing."""
        q_lower = query.lower()
        required_agents = []
        subtasks = []
        complexity = "simple"

        # Check for tool requirements (math, database, weather)
        has_math = any(op in q_lower for op in ["calculate", "multiply", "divide", "*", "+", "percentage improvement", "improvement percentage", "%"])
        has_db = any(term in q_lower for term in ["database", "employee", "salary", "salaries", "hire date", "leave balance"])
        has_weather = any(term in q_lower for term in ["weather", "temperature", "forecast", "humidity", "rain"])

        # Check for document / RAG requirements
        has_rag = any(term in q_lower for term in ["uploaded", "document", "policy", "handbook", "guide", "according to", "benchmark", "stated rule"])

        # Check for external research requirements
        has_research = any(term in q_lower for term in ["recent", "latest", "publicly available", "external", "news", "developments on the topic", "find recent"])

        if has_rag:
            required_agents.append("rag")
            subtasks.append({"agent": "rag", "task": f"Retrieve relevant evidence from knowledge base for: {query}"})

        if has_research:
            required_agents.append("research")
            subtasks.append({"agent": "research", "task": f"Search public external sources for: {query}"})

        if has_math or has_db or has_weather:
            required_agents.append("tool")
            tool_name = "calculator" if has_math else ("database" if has_db else "weather")
            subtasks.append({"agent": "tool", "task": f"Execute structured tool for: {query}", "tool_name": tool_name})

        # Default fallback if ambiguous
        if not required_agents:
            # Check if pure math numbers
            import re
            if re.search(r"\d+\s*[\*\+\-\/×÷]\s*\d+", query):
                required_agents = ["tool"]
                subtasks.append({"agent": "tool", "task": "Evaluate math expression", "tool_name": "calculator"})
            else:
                required_agents = ["rag"]
                subtasks.append({"agent": "rag", "task": query})

        if len(required_agents) > 1:
            complexity = "complex"

        return TaskPlan(
            task_id=task_id,
            intent="Dynamic multi-agent routing based on intent analysis",
            complexity=complexity,
            required_agents=required_agents,
            subtasks=subtasks,
            rationale=f"Selected {len(required_agents)} specialized agent(s): {', '.join(required_agents)}",
        )

    def run(self, state: Dict[str, Any]) -> AgentMessage:
        """Analyze query and formulate the dynamic execution plan."""
        start_time = time.perf_counter()
        task_id = state.get("task_id", "task_default")
        user_query = state.get("user_query", "")

        plan_dict = None
        # Attempt LLM dynamic planning
        if llm_client.provider in ("groq", "openai"):
            try:
                resp = llm_client.generate_json(
                    system_prompt=self._SYSTEM_PROMPT,
                    user_prompt=f"User Query:\n{user_query}",
                )
                if isinstance(resp, dict) and "required_agents" in resp:
                    agents = [str(a).lower() for a in resp.get("required_agents", [])]
                    # Filter valid agent roles
                    valid_agents = [a for a in agents if a in ("rag", "research", "tool")]
                    if valid_agents:
                        plan_dict = TaskPlan(
                            task_id=task_id,
                            intent=resp.get("intent", "Execute user query"),
                            complexity=resp.get("complexity", "simple"),
                            required_agents=valid_agents,
                            subtasks=resp.get("subtasks", []),
                            rationale=resp.get("rationale", ""),
                        )
            except Exception:
                pass

        if not plan_dict:
            plan_dict = self._fallback_heuristic_planner(user_query, task_id)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        summary = (
            f"Orchestrator planned workflow: selected {len(plan_dict.required_agents)} agent(s) "
            f"({', '.join(plan_dict.required_agents).upper()}) based on task complexity '{plan_dict.complexity}'."
        )

        return self.create_message(
            to_agent="orchestration_graph",
            task_id=task_id,
            status="success",
            summary=summary,
            result={
                "plan": plan_dict.model_dump(),
                "required_agents": plan_dict.required_agents,
                "complexity": plan_dict.complexity,
                "duration_ms": duration_ms,
            },
        )
