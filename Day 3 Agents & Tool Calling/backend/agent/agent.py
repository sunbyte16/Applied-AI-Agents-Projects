"""
Agent Interface for AgentLab AI.
Exposes high-level execution method.
"""

from typing import List, Optional
from backend.agent.loop import AgentLoop
from backend.models import ChatMessage, ChatResponse
from backend.services.llm_service import llm_service
from backend.tools.registry import default_registry


class AgentLabAI:
    """The AgentLab AI Assistant Coordinator."""

    def __init__(self) -> None:
        self.loop = AgentLoop(service=llm_service, registry=default_registry)

    def chat(
        self,
        message: str,
        enabled_tools: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tool_calls: int = 5,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """Run a conversation turn through the agent reasoning and tool execution loop."""
        return self.loop.run(
            user_message=message,
            enabled_tools=enabled_tools,
            model=model,
            temperature=temperature,
            max_tool_calls=max_tool_calls,
            conversation_history=conversation_history,
        )


# Singleton agent instance
agent = AgentLabAI()
