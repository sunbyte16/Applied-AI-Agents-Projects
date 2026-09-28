"""
FastAPI Server for AgentLab AI.
Exposes REST APIs for agent chat, tool inspection, health checks,
and serves the professional developer UI.
"""

import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.agent.agent import agent
from backend.config import settings
from backend.models import ChatRequest, ChatResponse, HealthResponse, ToolExecuteRequest
from backend.tools.registry import default_registry

app = FastAPI(
    title="AgentLab AI",
    description="Tool-Using AI Agent & Function Calling Playground",
    version="1.0.0",
)

# Enable CORS for developer workflows
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)


# API Endpoints
@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return system and LLM configuration health status."""
    return HealthResponse(
        status="ok",
        llm_configured=settings.is_llm_configured(),
        provider=settings.get_active_provider(),
        default_model=settings.DEFAULT_MODEL,
        tools_available=len(default_registry.list_tools()),
    )


@app.get("/api/tools")
def get_tools() -> Dict[str, Any]:
    """Return all available registered tools and their full schemas."""
    return {
        "count": len(default_registry.list_tools()),
        "tools": default_registry.list_tools(),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main Agent Execution Endpoint.
    Performs autonomous agent loop with native tool calling.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    response = agent.chat(
        message=request.message.strip(),
        enabled_tools=request.enabled_tools,
        model=request.model,
        temperature=request.temperature or settings.DEFAULT_TEMPERATURE,
        max_tool_calls=request.max_tool_calls or settings.DEFAULT_MAX_TOOL_CALLS,
        conversation_history=request.conversation_history,
    )
    return response


@app.post("/api/tools/{tool_name}/execute")
def direct_tool_execute(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Direct execution endpoint for playground tool testing/inspection."""
    result = default_registry.execute(
        tool_name=tool_name,
        arguments=payload.get("arguments", {}),
        enabled_tools=[tool_name],
    )
    return result


# Mount Static Files and Root Route
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend() -> FileResponse:
        """Serve the frontend single page app."""
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        return FileResponse(index_file)
