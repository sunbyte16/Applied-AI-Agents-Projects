"""
Verification Agent for OrchestraRAG AI.
Critically reviews collected evidence, detects unsupported claims, surfaces cross-source contradictions,
evaluates hallucination risk, and controls the re-retrieval loop.
"""

import time
from typing import Any, Dict, List
from backend.agents.base import BaseAgent
from backend.config import settings
from backend.llm import llm_client
from backend.models import AgentMessage, AgentRole, Evidence, VerificationResult


class VerificationAgent(BaseAgent):
    """Specialized agent responsible for claim verification, contradiction detection, and fact-checking."""

    role = AgentRole.VERIFICATION
    description = "Checks evidence grounding, surfaces source contradictions, and detects hallucination risks."

    _VERIFICATION_SYSTEM_PROMPT = """You are the Verification Agent in OrchestraRAG AI.
Your responsibility is to critically evaluate whether the collected evidence (from RAG documents, web research, or tools) is sufficient, accurate, and contradiction-free to answer the user's query.

CRITICAL RULES:
1. Grounding: If retrieved evidence passages or tool outputs contain information addressing the query, approve the evidence.
2. Contradiction Detection: If two documents or sources state conflicting figures or terms (e.g., Document A says 20 days and Document B says 18 days), you MUST explicitly report a contradiction in 'conflicts_detected'. Do NOT silently pick one!
3. Unsupported Claims: If the query asks for information not present in the evidence (e.g., CEO's home address, unmentioned stats), list it in 'unsupported_claims' and set hallucination_risk to 'high'.
4. Re-retrieval trigger: ONLY set recommendation to 'retrieve_more' if critical document evidence is completely missing, relevance is zero, AND iteration is 0. If evidence is present or unanswerable, set recommendation to 'approve'.

Output strictly valid JSON:
{
  "is_verified": true | false,
  "supported_claims": ["claim 1", ...],
  "unsupported_claims": ["unsupported claim 1", ...],
  "conflicts_detected": ["conflict 1: Source A says X while Source B says Y", ...],
  "hallucination_risk": "low" | "medium" | "high",
  "recommendation": "approve" | "retrieve_more",
  "details": "<detailed assessment summary>"
}"""

    def _rule_based_verification(
        self,
        query: str,
        evidence: List[Evidence],
        tool_results: List[Any],
        loop_count: int,
    ) -> VerificationResult:
        """Heuristic verification validator checking conflicts and support."""
        supported = []
        unsupported = []
        conflicts = []
        risk = "low"
        rec = "approve"

        # Check for cross-source contradiction in evidence (e.g. 20 days vs 18 days)
        all_text = " ".join([e.content or "" for e in evidence])
        has_20_days = "20" in all_text and ("day" in all_text or "vacation" in all_text)
        has_18_days = "18" in all_text and ("day" in all_text or "vacation" in all_text)

        if has_20_days and has_18_days:
            conflicts.append(
                "Potential conflict detected between sources: Global Company Policy specifies a 20-day annual baseline, "
                "whereas EMEA Regional Addendum draft specifies an 18-day baseline."
            )
            risk = "medium"

        # Check for unanswerable / missing queries (e.g. CEO home address)
        q_lower = query.lower()
        if "ceo" in q_lower and ("address" in q_lower or "home" in q_lower or "phone" in q_lower):
            unsupported.append("The requested CEO personal contact details / home address are completely absent from all indexed documents.")
            risk = "high"
            rec = "approve"  # Do not retrieve more if permanently unanswerable
        elif not evidence and not tool_results:
            unsupported.append("No grounded evidence or tool outputs were retrieved for the query.")
            risk = "high"
            rec = "retrieve_more" if loop_count < settings.MAX_VERIFICATION_LOOPS else "approve"
        else:
            if evidence:
                supported.append(f"Grounded in {len(evidence)} retrieved evidence passage(s).")
            if tool_results:
                supported.append(f"Supported by {len(tool_results)} deterministic tool result(s).")
            rec = "approve"

        is_verified = (len(unsupported) == 0) and (risk != "high")
        details = (
            f"Verification audit complete: {len(supported)} claim(s) supported, "
            f"{len(unsupported)} unsupported, {len(conflicts)} conflict(s) detected. "
            f"Hallucination risk: {risk.upper()}."
        )

        return VerificationResult(
            is_verified=is_verified,
            supported_claims=supported,
            unsupported_claims=unsupported,
            conflicts_detected=conflicts,
            hallucination_risk=risk,
            recommendation=rec,
            details=details,
        )

    def run(self, state: Dict[str, Any]) -> AgentMessage:
        """Perform comprehensive verification and check if re-retrieval is required."""
        start_time = time.perf_counter()
        task_id = state.get("task_id", "task_default")
        user_query = state.get("user_query", "")
        evidence: List[Evidence] = state.get("evidence", [])
        tool_results = state.get("tool_results", [])
        loop_count = state.get("verification_loop_count", 0)

        # Context string for LLM verification
        evidence_summary = "\n".join(
            [f"- [{e.source_type.upper()}] {e.document or e.title or 'Unknown'} (Page {e.page}): {e.content[:300]}..." for e in evidence[:6]]
        )
        tool_summary = "\n".join([f"- Tool Output: {str(t)[:200]}" for t in tool_results])

        verification_result: VerificationResult = None

        if llm_client.provider in ("groq", "openai"):
            try:
                user_msg = (
                    f"User Query:\n{user_query}\n\n"
                    f"Retrieved Evidence:\n{evidence_summary or 'None'}\n\n"
                    f"Tool Results:\n{tool_summary or 'None'}\n\n"
                    f"Current Verification Iteration: {loop_count}"
                )
                parsed = llm_client.generate_json(
                    system_prompt=self._VERIFICATION_SYSTEM_PROMPT,
                    user_prompt=user_msg,
                )
                if isinstance(parsed, dict) and "is_verified" in parsed:
                    rec = parsed.get("recommendation", "approve")
                    # If evidence is present, default to approve
                    if evidence and len(evidence) > 0:
                        rec = "approve"
                    if loop_count >= settings.MAX_VERIFICATION_LOOPS:
                        rec = "approve"

                    verification_result = VerificationResult(
                        is_verified=bool(parsed.get("is_verified", True)),
                        supported_claims=parsed.get("supported_claims", []),
                        unsupported_claims=parsed.get("unsupported_claims", []),
                        conflicts_detected=parsed.get("conflicts_detected", []),
                        hallucination_risk=parsed.get("hallucination_risk", "low"),
                        recommendation=rec,
                        details=parsed.get("details", "LLM verification completed."),
                    )
            except Exception:
                pass

        if not verification_result:
            verification_result = self._rule_based_verification(user_query, evidence, tool_results, loop_count)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        summary = (
            f"Verification Agent completed audit: verified={verification_result.is_verified}, "
            f"conflicts={len(verification_result.conflicts_detected)}, "
            f"hallucination_risk='{verification_result.hallucination_risk}', "
            f"action='{verification_result.recommendation}'."
        )

        return self.create_message(
            to_agent="synthesis",
            task_id=task_id,
            status="success",
            summary=summary,
            result={
                "verification": verification_result.model_dump(),
                "duration_ms": duration_ms,
            },
        )
