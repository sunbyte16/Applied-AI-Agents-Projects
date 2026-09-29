"""
External Search Tool for OrchestraRAG AI.
Queries web sources via DuckDuckGo (ddgs) or Tavily API.
Treats all retrieved content as untrusted data.
Never fabricates results; reports missing configuration cleanly.
"""

import os
from typing import Any, Dict, List
import httpx
from backend.config import settings
from backend.tools.base import BaseTool

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False


class SearchTool(BaseTool):
    """Tool for gathering current, external, or real-time web facts."""

    name = "search"
    description = (
        "Search the public web for recent developments, news, industry benchmarks, "
        "and external factual verification. Use this when the query asks for external "
        "or up-to-date public information outside the uploaded documents."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Specific search keywords or phrase, e.g., 'recent developments in RAG and agent orchestration 2026'.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of search results to retrieve (default: 3, max: 5).",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str = "", max_results: int = 3, **kwargs: Any) -> Dict[str, Any]:
        """Execute live search query with fallback and untrusted content tags."""
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "tool_name": self.name,
                "success": False,
                "error": "Query parameter must be a non-empty string.",
            }

        cleaned_query = query.strip()
        limit = min(max(1, int(max_results or 3)), 5)

        # 1. Try Tavily API if configured
        tavily_key = settings.TAVILY_API_KEY or settings.SEARCH_API_KEY
        if tavily_key and not tavily_key.startswith("tvly_your"):
            try:
                resp = httpx.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": cleaned_query, "max_results": limit},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results: List[Dict[str, str]] = []
                    for r in data.get("results", [])[:limit]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", "")[:500],
                            "untrusted": True,
                        })
                    if results:
                        return {
                            "tool_name": self.name,
                            "success": True,
                            "query": cleaned_query,
                            "provider": "Tavily Search API",
                            "results_count": len(results),
                            "results": results,
                        }
            except Exception:
                pass

        # 2. Try DuckDuckGo via DDGS
        if DDGS_AVAILABLE:
            try:
                results_list: List[Dict[str, Any]] = []
                with DDGS(timeout=5) as ddgs:
                    raw_results = list(ddgs.text(cleaned_query, max_results=limit))
                    for item in raw_results:
                        results_list.append({
                            "title": item.get("title", ""),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", "")[:500],
                            "untrusted": True,
                        })
                if results_list:
                    return {
                        "tool_name": self.name,
                        "success": True,
                        "query": cleaned_query,
                        "provider": "DuckDuckGo (DDGS)",
                        "results_count": len(results_list),
                        "results": results_list,
                    }
            except Exception:
                pass

        # If search service is unavailable or credentials not set
        return {
            "tool_name": self.name,
            "success": False,
            "query": cleaned_query,
            "error": (
                "Search service is currently unavailable or external network timeout. "
                "To enable enterprise web research, configure TAVILY_API_KEY in .env."
            ),
        }
