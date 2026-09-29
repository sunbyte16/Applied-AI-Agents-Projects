"""
RAG / Knowledge Agent for OrchestraRAG AI.
Performs semantic vector search over indexed internal documents,
extracts grounded factual evidence with provenance metadata, and refuses to fabricate claims.
"""

import time
from typing import Any, Dict, List, Optional
from backend.agents.base import BaseAgent
from backend.config import settings
from backend.models import AgentMessage, AgentRole, Evidence
from backend.rag.vector_store import vector_store_manager


class RAGAgent(BaseAgent):
    """Specialized agent responsible for grounded knowledge retrieval from documents."""

    role = AgentRole.RAG
    description = "Retrieves grounded factual chunks from vector database with page and document citations."

    def run(self, state: Dict[str, Any]) -> AgentMessage:
        """Perform semantic retrieval against the persistent ChromaDB collection."""
        start_time = time.perf_counter()
        task_id = state.get("task_id", "task_default")
        user_query = state.get("user_query", "")
        plan = state.get("plan", {})
        doc_filter = state.get("filter_documents")
        loop_count = state.get("verification_loop_count", 0)

        # Extract specific RAG subtask if defined by orchestrator
        retrieval_query = user_query
        subtasks = plan.get("subtasks", []) if isinstance(plan, dict) else []
        for st in subtasks:
            if st.get("agent") == "rag" and st.get("task"):
                retrieval_query = st.get("task")
                break

        # Dynamically adjust top_k if in re-retrieval loop
        top_k = settings.TOP_K + (2 * loop_count)
        min_threshold = max(0.20, settings.SIMILARITY_THRESHOLD - (0.05 * loop_count))

        evidence_list: List[Evidence] = vector_store_manager.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_filter=doc_filter,
            min_relevance=min_threshold,
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if not evidence_list:
            summary = (
                f"RAG Agent executed semantic search for '{retrieval_query[:60]}...' "
                f"but found 0 chunks meeting the minimum relevance threshold ({min_threshold})."
            )
            return self.create_message(
                to_agent="verification",
                task_id=task_id,
                status="success",
                summary=summary,
                evidence=[],
                result={
                    "retrieved_count": 0,
                    "query": retrieval_query,
                    "duration_ms": duration_ms,
                    "note": "No supporting document evidence met threshold.",
                },
            )

        unique_docs = list(set([e.document for e in evidence_list if e.document]))
        summary = (
            f"RAG Agent retrieved {len(evidence_list)} grounded chunk(s) "
            f"across {len(unique_docs)} document(s) ({', '.join(unique_docs)}) in {duration_ms}ms."
        )

        return self.create_message(
            to_agent="verification",
            task_id=task_id,
            status="success",
            summary=summary,
            evidence=evidence_list,
            result={
                "retrieved_count": len(evidence_list),
                "query": retrieval_query,
                "documents_referenced": unique_docs,
                "duration_ms": duration_ms,
            },
        )
