"""
Automated Evaluation Engine for OrchestraRAG AI.
Executes test cases, benchmarks multi-agent collaboration, and computes empirical metrics.
"""

import json
import os
import time
from typing import Any, Dict, List
from backend.config import settings
from backend.orchestration.graph import workflow_graph


class WorkflowEvaluator:
    """Evaluates multi-agent orchestration performance across diverse task categories."""

    def __init__(self, dataset_path: str = "evaluation/test_cases.json"):
        self.dataset_path = os.path.join(settings.ROOT_DIR, dataset_path)

    def load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from dataset."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Evaluation dataset not found at: {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluation(self) -> Dict[str, Any]:
        """Execute all test cases and compile quantitative metrics."""
        cases = self.load_test_cases()
        results: List[Dict[str, Any]] = []

        total_cases = len(cases)
        completed_cases = 0
        total_retrieval_chunks = 0
        total_tool_calls = 0
        successful_tool_calls = 0
        citations_present_count = 0
        unsupported_claims_caught = 0
        conflicts_caught = 0
        total_latencies = []

        print(f"\n=================================================================")
        print(f"       ORCHESTRARAG AI - MULTI-AGENT EVALUATION BENCHMARK        ")
        print(f"=================================================================\n")

        for idx, case in enumerate(cases, 1):
            case_id = case["id"]
            question = case["question"]
            category = case["category"]
            print(f"[{idx}/{total_cases}] Running {case_id} ({category})...")

            start_t = time.perf_counter()
            res = workflow_graph.run_workflow(
                query=question,
                task_id=f"eval_{case_id}",
                mode="auto",
            )
            duration_sec = round(time.perf_counter() - start_t, 2)
            total_latencies.append(duration_sec)

            ans = res.get("final_answer") or ""
            evidence = res.get("evidence", [])
            tool_calls = res.get("tool_calls", [])
            verification = res.get("verification", {})
            required_agents = res.get("required_agents", [])

            completed_cases += 1
            total_retrieval_chunks += len(evidence)
            total_tool_calls += len(tool_calls)
            successful_tool_calls += sum(1 for tc in tool_calls if tc.success)

            # Check citation presence
            has_citations = "## Evidence" in ans and len(evidence) > 0
            if has_citations or not case.get("requires_evidence", True):
                citations_present_count += 1

            # Check unsupported claim detection
            unsupported = verification.get("unsupported_claims", [])
            if unsupported and case.get("expect_unsupported", False):
                unsupported_claims_caught += 1

            # Check conflict detection
            conflicts = verification.get("conflicts_detected", [])
            if conflicts and case.get("expect_conflict", False):
                conflicts_caught += 1

            case_result = {
                "id": case_id,
                "category": category,
                "question": question,
                "duration_sec": duration_sec,
                "required_agents": required_agents,
                "evidence_count": len(evidence),
                "tool_calls_count": len(tool_calls),
                "verification_status": verification.get("is_verified", True),
                "hallucination_risk": verification.get("hallucination_risk", "low"),
                "answer_length": len(ans),
            }
            results.append(case_result)
            print(f"    -> Agents: {required_agents} | Evidence: {len(evidence)} | Latency: {duration_sec}s")

        # Compile Summary Metrics
        avg_latency = round(sum(total_latencies) / len(total_latencies), 2) if total_latencies else 0.0
        workflow_completion_rate = round((completed_cases / total_cases) * 100, 1)
        tool_success_rate = round((successful_tool_calls / total_tool_calls * 100), 1) if total_tool_calls > 0 else 100.0
        citation_rate = round((citations_present_count / total_cases) * 100, 1)

        summary_metrics = {
            "total_test_cases": total_cases,
            "completed_cases": completed_cases,
            "workflow_completion_rate_pct": workflow_completion_rate,
            "average_latency_sec": avg_latency,
            "total_evidence_chunks_retrieved": total_retrieval_chunks,
            "average_chunks_per_query": round(total_retrieval_chunks / total_cases, 1),
            "total_tool_calls": total_tool_calls,
            "tool_call_success_rate_pct": tool_success_rate,
            "citation_presence_rate_pct": citation_rate,
            "unsupported_claims_caught": unsupported_claims_caught,
            "conflicts_detected": conflicts_caught,
        }

        print("\n=================================================================")
        print("                   EVALUATION SUMMARY REPORT                     ")
        print("=================================================================")
        for k, v in summary_metrics.items():
            print(f"  {k.replace('_', ' ').title():<36}: {v}")
        print("=================================================================\n")

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "llm_provider": settings.get_active_llm_provider(),
            "model": settings.DEFAULT_MODEL,
            "metrics": summary_metrics,
            "detailed_results": results,
        }

        report_path = os.path.join(settings.ROOT_DIR, "evaluation/evaluation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report


if __name__ == "__main__":
    evaluator = WorkflowEvaluator()
    evaluator.run_evaluation()
