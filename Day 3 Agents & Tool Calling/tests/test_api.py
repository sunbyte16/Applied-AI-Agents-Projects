"""
API Integration Tests for AgentLab AI FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Verify /api/health responds with 200 and required fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "default_model" in data
    assert data["tools_available"] >= 5


def test_tools_endpoint() -> None:
    """Verify /api/tools lists registered tools with schemas."""
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 5
    tool_names = [t["name"] for t in data["tools"]]
    assert "calculator" in tool_names
    assert "weather" in tool_names
    assert "database" in tool_names
    assert "search" in tool_names
    assert "skill_gap_calculator" in tool_names


def test_direct_tool_execute_endpoint() -> None:
    """Verify /api/tools/{name}/execute runs a tool directly."""
    response = client.post(
        "/api/tools/calculator/execute",
        json={"arguments": {"expression": "25 * 4"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"] == 100


def test_chat_endpoint_empty_message() -> None:
    """Verify /api/chat rejects empty user messages."""
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400


def test_chat_endpoint_valid_request() -> None:
    """Verify /api/chat executes and returns structured answer and trace."""
    response = client.post(
        "/api/chat",
        json={
            "message": "Calculate 15 + 25",
            "enabled_tools": ["calculator"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "40" in data["answer"]
    assert len(data["trace"]) > 0
    assert data["tool_calls_executed"] == 1
