"""
Unit tests for individual specialized agents in OrchestraRAG AI.
Tests Orchestrator, RAG Agent, Research Agent, Tool Agent, Verification Agent, and Synthesis Agent.
"""

import pytest
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.rag_agent import RAGAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.tool_agent import ToolAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.models import Evidence, ToolCallRecord


class TestSpecializedAgents:
    """Test suite for individual specialized agents."""

    def test_orchestrator_math_planning(self):
        orch = OrchestratorAgent()
        state = {"task_id": "test_t1", "user_query": "What is 125 * 87?"}
        msg = orch.run(state)
        assert msg.status == "success"
        required = msg.result["required_agents"]
        assert "tool" in required
        assert "rag" not in required

    def test_orchestrator_rag_planning(self):
        orch = OrchestratorAgent()
        state = {"task_id": "test_t2", "user_query": "What does the uploaded company policy say about vacation?"}
        msg = orch.run(state)
        assert msg.status == "success"
        required = msg.result["required_agents"]
        assert "rag" in required
        assert "tool" not in required

    def test_rag_agent_execution(self):
        rag = RAGAgent()
        state = {
            "task_id": "test_t3",
            "user_query": "What are the main components of a RAG system?",
            "plan": {"subtasks": [{"agent": "rag", "task": "main components of a RAG system"}]},
        }
        msg = rag.run(state)
        assert msg.status == "success"
        assert len(msg.evidence) > 0
        assert msg.evidence[0].source_type == "document"

    def test_tool_agent_execution(self):
        tool = ToolAgent()
        state = {
            "task_id": "test_t4",
            "user_query": "Calculate 8492 * 372",
            "plan": {"subtasks": [{"agent": "tool", "task": "Calculate 8492 * 372", "tool_name": "calculator"}]},
        }
        msg = tool.run(state)
        assert msg.status == "success"
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].output == 3159024

    def test_verification_agent_contradiction_detection(self):
        verifier = VerificationAgent()
        state = {
            "task_id": "test_t5",
            "user_query": "What is the annual baseline vacation allocation according to policy?",
            "evidence": [
                Evidence(source_type="document", document="company_policy.txt", page=1, content="Baseline Allocation: 20 paid vacation days per calendar year."),
                Evidence(source_type="document", document="conflicting_policy.txt", page=1, content="Baseline Allocation: 18 paid vacation days per calendar year."),
            ],
            "tool_results": [],
            "verification_loop_count": 0,
        }
        msg = verifier.run(state)
        assert msg.status == "success"
        v_data = msg.result["verification"]
        assert len(v_data["conflicts_detected"]) > 0
        assert "conflict" in v_data["conflicts_detected"][0].lower()

    def test_synthesis_agent_format(self):
        synth = SynthesisAgent()
        state = {
            "task_id": "test_t6",
            "user_query": "What is 10 + 20?",
            "evidence": [],
            "tool_calls": [ToolCallRecord(tool_name="calculator", arguments={"expression": "10 + 20"}, output=30, success=True)],
            "verification": {"is_verified": True},
            "errors": [],
        }
        msg = synth.run(state)
        assert msg.status == "success"
        ans = msg.result["final_answer"]
        assert "## Answer" in ans
        assert "30" in ans
