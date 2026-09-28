"""
Agent Execution Loop Tests for AgentLab AI.
Tests tool selection, direct response, multi-tool orchestration, disabled tools, and loop safety.
"""

from typing import Any, Dict, List, Optional
import pytest
from backend.agent.loop import AgentLoop
from backend.services.llm_service import LLMResult, LLMService, ToolCallItem
from backend.tools.registry import ToolRegistry
from backend.tools.calculator import CalculatorTool
from backend.tools.database import DatabaseTool


class MockTestLLM(LLMService):
    """Custom controllable mock LLM for deterministic unit tests."""

    def __init__(self, script: List[LLMResult]):
        super().__init__()
        self.script = script
        self.call_count = 0

    def call_llm(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> LLMResult:
        if self.call_count < len(self.script):
            res = self.script[self.call_count]
            self.call_count += 1
            return res
        return LLMResult(content="Final default mock answer.", tool_calls=[])


class TestAgentLoop:
    """Test suite for AgentLoop orchestration."""

    def setup_method(self) -> None:
        self.registry = ToolRegistry()
        self.registry.register(CalculatorTool())
        self.registry.register(DatabaseTool())

    def test_direct_answer_without_tools(self) -> None:
        mock_llm = MockTestLLM([
            LLMResult(content="Machine learning is the study of computer algorithms that improve automatically through experience.", tool_calls=[])
        ])
        loop = AgentLoop(service=mock_llm, registry=self.registry)
        response = loop.run(user_message="What is machine learning?")

        assert response.success is True
        assert response.tool_calls_executed == 0
        assert "Machine learning" in response.answer
        # Check trace recorded direct response
        step_types = [t.type for t in response.trace]
        assert "direct_response" in step_types

    def test_single_calculator_tool_call(self) -> None:
        mock_llm = MockTestLLM([
            # Step 1: Model requests tool call
            LLMResult(
                content="",
                tool_calls=[ToolCallItem(id="call_calc_1", name="calculator", arguments={"expression": "1250 * 37"})]
            ),
            # Step 2: Model receives result and generates final answer
            LLMResult(
                content="The calculation 1250 * 37 equals 46250.",
                tool_calls=[]
            )
        ])
        loop = AgentLoop(service=mock_llm, registry=self.registry)
        response = loop.run(user_message="Calculate 1250 * 37")

        assert response.success is True
        assert response.tool_calls_executed == 1
        assert "46250" in response.answer

        # Verify trace contains tool_call and tool_result
        types = [t.type for t in response.trace]
        assert "tool_call" in types
        assert "tool_result" in types
        assert "final_answer" in types

    def test_disabled_tool_handling(self) -> None:
        mock_llm = MockTestLLM([
            LLMResult(
                content="",
                tool_calls=[ToolCallItem(id="call_db_1", name="database", arguments={"operation": "count_products"})]
            ),
            LLMResult(
                content="The database tool is currently disabled in your settings.",
                tool_calls=[]
            )
        ])
        loop = AgentLoop(service=mock_llm, registry=self.registry)
        # Pass enabled_tools without database
        response = loop.run(
            user_message="How many products are in the database?",
            enabled_tools=["calculator"]
        )

        assert response.success is True
        assert response.tool_calls_executed == 1
        # The tool result should have recorded an error about disabled tool
        tool_result_step = next(t for t in response.trace if t.type == "tool_result")
        assert tool_result_step.result["success"] is False
        assert "disabled" in tool_result_step.result["error"]

    def test_maximum_tool_calls_enforcement(self) -> None:
        # Script an infinite loop of tool calls
        infinite_script = [
            LLMResult(
                content="",
                tool_calls=[ToolCallItem(id=f"c_{i}", name="calculator", arguments={"expression": f"{i} + 1"})]
            )
            for i in range(10)
        ]
        mock_llm = MockTestLLM(infinite_script)
        loop = AgentLoop(service=mock_llm, registry=self.registry)

        max_calls = 3
        response = loop.run(
            user_message="Keep computing numbers",
            max_tool_calls=max_calls
        )

        # Loop must stop at max_calls
        assert response.tool_calls_executed <= max_calls
