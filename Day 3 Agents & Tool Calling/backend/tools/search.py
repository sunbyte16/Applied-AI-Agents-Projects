"""
Search Tool for AgentLab AI.
Queries external web sources using DuckDuckGo (via ddgs) or Tavily/SerpApi if configured.
Treats all search results as untrusted external content.
"""

import os
from typing import Any, Dict, List
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
    """Tool for searching the web for current or external information."""

    name = "search"
    description = (
        "Search the web for up-to-date, current, or external information, news, "
        "and factual documentation. Use this tool when answering questions about "
        "recent events, real-world developments, or topics beyond static knowledge."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Specific search query keywords, e.g., 'latest developments in retrieval augmented generation' or 'Python 3.13 release'.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of search results to return (default: 3, max: 5).",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str = "", max_results: int = 3, **kwargs: Any) -> Dict[str, Any]:
        """Perform search and return clean structured snippets."""
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "tool": self.name,
                "success": False,
                "error": "Query parameter must be a non-empty string.",
            }

        query = query.strip()
        limit = min(max(1, int(max_results or 3)), 5)

        # 1. Try DuckDuckGo via DDGS
        if DDGS_AVAILABLE:
            try:
                results_list: List[Dict[str, str]] = []
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=limit))
                    for item in raw_results:
                        results_list.append({
                            "title": item.get("title", ""),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", "")[:400],
                        })

                if results_list:
                    return {
                        "tool": self.name,
                        "success": True,
                        "query": query,
                        "results_count": len(results_list),
                        "results": results_list,
                    }
            except Exception as e:
                # If network or rate limit, fall through or report error
                pass

        # 2. Check Tavily / SEARCH_API_KEY if configured in environment
        tavily_key = os.getenv("TAVILY_API_KEY") or os.getenv("SEARCH_API_KEY")
        if tavily_key:
            try:
                import requests
                resp = requests.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": query, "max_results": limit},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tavily_results = [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", "")[:400],
                        }
                        for r in data.get("results", [])[:limit]
                    ]
                    return {
                        "tool": self.name,
                        "success": True,
                        "query": query,
                        "results_count": len(tavily_results),
                        "results": tavily_results,
                    }
            except Exception as e:
                pass

        # If live search is currently unavailable or network down
        return {
            "tool": self.name,
            "success": False,
            "query": query,
            "error": (
                "Search service is currently unavailable or network connection failed. "
                "Configure SEARCH_API_KEY or verify internet connectivity."
            ),
        }
