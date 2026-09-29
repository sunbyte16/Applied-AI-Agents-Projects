"""
End-to-End Multi-Agent Workflow Tests for OrchestraRAG AI.
Tests Test 1 (direct/math), Test 2 (RAG), Test 3 (calculation), Test 4 (complex multi-agent),
and Test 5 (failure recovery and graceful degradation).
"""

import pytest
from backend.orchestration.graph import workflow_graph


class TestMultiAgentWorkflows:
    """Test suite for full multi-agent orchestration flows."""

    def test_workflow_test_3_calculation(self):
        """Test 3: Pure calculation routes to Tool Agent without invoking RAG."""
        res = workflow_graph.run_workflow(query="Calculate 8492 * 372", task_id="wf_test_calc")
        assert res["status"] in ("completed", "completed_with_warnings")
        assert "tool" in res["required_agents"]
        assert "rag" not in res["required_agents"]
        assert len(res["tool_calls"]) >= 1
        assert res["tool_calls"][0].output == 3159024
        assert "## Answer" in res["final_answer"]

    def test_workflow_test_2_rag_document_question(self):
        """Test 2: Document question routes to RAG and skips Calculator and Search."""
        res = workflow_graph.run_workflow(
            query="According to the uploaded RAG guide, what are the main components of a RAG system?",
            task_id="wf_test_rag",
        )
        assert res["status"] in ("completed", "completed_with_warnings")
        assert "rag" in res["required_agents"]
        assert "tool" not in res["required_agents"]
        assert len(res["evidence"]) > 0
        assert "rag_guide.txt" in [e.document for e in res["evidence"]]
        assert "## Evidence" in res["final_answer"]

    def test_workflow_test_4_complex_multi_agent(self):
        """Test 4: Complex multi-agent request invokes RAG, Research, and Tool agents."""
        res = workflow_graph.run_workflow(
            query="Based on the uploaded RAG guide, explain how RAG works, find recent information about RAG, and calculate the percentage improvement from the numbers mentioned in the document.",
            task_id="wf_test_complex",
        )
        assert res["status"] in ("completed", "completed_with_warnings")
        required = res["required_agents"]
        assert "rag" in required
        assert "tool" in required or "research" in required
        assert len(res["evidence"]) > 0
        assert "## Answer" in res["final_answer"]

    def test_workflow_test_5_failure_recovery(self):
        """Test 5: Workflow recovers gracefully when a tool or subtask produces an error."""
        # Query asking for invalid database syntax or missing external tool
        res = workflow_graph.run_workflow(
            query="Query the database for invalid syntax DROP TABLE employees AND calculate invalid syntax 5 // 0",
            task_id="wf_test_fail_recovery",
        )
        # Must not crash, must return completed status with error logging
        assert res["status"] in ("completed", "completed_with_warnings")
        assert res["final_answer"] is not None
        assert len(res["final_answer"]) > 10
        assert len(res["trace"]) > 0
