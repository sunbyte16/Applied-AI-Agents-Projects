"""
Research Agent for OrchestraRAG AI.
Queries external web sources for current industry facts, real-world developments, and news.
Treats retrieved external data as untrusted, preserves actual URLs, and never fabricates results.
"""

import time
from typing import Any, Dict, List
from backend.agents.base import BaseAgent
from backend.models import AgentMessage, AgentRole, Evidence
from backend.tools.registry import tool_registry


class ResearchAgent(BaseAgent):
    """Specialized agent responsible for public web research and external verification."""

    role = AgentRole.RESEARCH
    description = "Searches the live public web for external information, recent developments, and news."

    def run(self, state: Dict[str, Any]) -> AgentMessage:
        """Execute web research using the search tool."""
        start_time = time.perf_counter()
        task_id = state.get("task_id", "task_default")
        user_query = state.get("user_query", "")
        plan = state.get("plan", {})

        # Extract search query
        search_query = user_query
        subtasks = plan.get("subtasks", []) if isinstance(plan, dict) else []
        for st in subtasks:
            if st.get("agent") == "research" and st.get("task"):
                search_query = st.get("task")
                break

        # Execute search tool
        tool_res = tool_registry.execute_tool("search", {"query": search_query, "max_results": 3})
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if not tool_res.get("success"):
            err_msg = tool_res.get("error", "External search service unavailable.")
            summary = f"Research Agent failed to retrieve external web sources: {err_msg}"
            return self.create_message(
                to_agent="verification",
                task_id=task_id,
                status="error",
                summary=summary,
                errors=[err_msg],
                result={"search_available": False, "duration_ms": duration_ms, "error": err_msg},
            )

        raw_results = tool_res.get("results", [])
        evidence_list: List[Evidence] = []
        for item in raw_results:
            title = item.get("title", "Web Source")
            url = item.get("url", "")
            snippet = item.get("snippet", "")
            evidence_list.append(
                Evidence(
                    source_type="web",
                    title=title,
                    url=url,
                    snippet=snippet,
                    content=f"[Web Source: {title}] {snippet}",
                    summary=f"External web finding from {url or title}",
                )
            )

        summary = f"Research Agent retrieved {len(evidence_list)} external source(s) for query: '{search_query[:50]}...'."
        return self.create_message(
            to_agent="verification",
            task_id=task_id,
            status="success",
            summary=summary,
            evidence=evidence_list,
            result={
                "search_query": search_query,
                "sources_retrieved": len(evidence_list),
                "duration_ms": duration_ms,
            },
        )
