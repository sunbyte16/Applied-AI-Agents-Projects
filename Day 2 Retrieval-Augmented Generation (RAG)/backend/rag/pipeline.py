import time
import re
import logging
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.models import (
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
    PipelineTrace,
    PipelineStageTrace,
)
from backend.retrieval.retriever import Retriever, retriever
from backend.rag.prompt import RAG_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class LLMClient:
    """Dispatches generation requests to configured LLM provider or local grounded engine."""

    def __init__(self):
        self.provider = self._resolve_provider()

    def _resolve_provider(self) -> str:
        pref = settings.LLM_PROVIDER.lower().strip()
        if (pref == "openai" or pref == "auto") and settings.OPENAI_API_KEY:
            if settings.OPENAI_API_KEY != "your_openai_api_key_here":
                return "openai"
        if (pref == "gemini" or pref == "auto") and settings.GEMINI_API_KEY:
            if settings.GEMINI_API_KEY != "your_gemini_api_key_here":
                return "gemini"
        return "offline_grounded"

    def generate(
        self,
        question: str,
        context: str,
        chunks: List[RetrievedChunk],
        temperature: float = 0.2,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        prov = self._resolve_provider()

        if prov == "openai":
            return self._generate_openai(question, context, temperature, conversation_history)
        elif prov == "gemini":
            return self._generate_gemini(question, context, temperature)
        else:
            return self._generate_offline(question, chunks)

    def _generate_openai(
        self,
        question: str,
        context: str,
        temperature: float,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

        messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]

        # Append limited prior conversation history if provided
        if conversation_history:
            # Keep last 4 turns max to avoid overwhelming context
            recent = conversation_history[-4:]
            for turn in recent:
                if turn.get("role") in {"user", "assistant"}:
                    messages.append({"role": turn["role"], "content": turn["content"]})

        user_content = build_user_prompt(question, context)
        messages.append({"role": "user", "content": user_content})

        response = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def _generate_gemini(self, question: str, context: str, temperature: float) -> str:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_CHAT_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        user_content = build_user_prompt(question, context)
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{RAG_SYSTEM_PROMPT}\n\n{user_content}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024
            }
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "I couldn't find enough information in the uploaded documents to answer that confidently."

    def _generate_offline(self, question: str, chunks: List[RetrievedChunk]) -> str:
        """High-precision offline deterministic grounding engine.

        Used when external API keys are not supplied. Performs strict lexical and
        semantic relevance verification against retrieved chunks and synthesizes
        grounded responses with exact citations, or refuses hallucination.
        """
        if not chunks:
            return "I couldn't find enough information in the uploaded documents to answer that confidently."

        # Filter keywords from question (removing common stop words)
        stop_words = {
            "what", "is", "the", "are", "how", "why", "where", "when", "who", "which",
            "a", "an", "in", "on", "of", "to", "for", "with", "by", "at", "from",
            "this", "that", "these", "those", "does", "do", "did", "can", "could",
            "would", "should", "document", "documents", "according", "mentioned", "tell",
            "me", "about", "find", "give"
        }
        q_tokens = [
            w.strip("?,.:;\"'") for w in question.lower().split()
            if len(w.strip("?,.:;'\"")) > 2 and w.strip("?,.:;'\"") not in stop_words
        ]

        # Check if question asks about something completely absent (e.g. Mars, alien, nonexistent term)
        all_text = " ".join(c.text.lower() for c in chunks)
        matching_q_tokens = [tok for tok in q_tokens if tok in all_text]

        # If none of the key question keywords exist in the retrieved text, refuse hallucination
        if q_tokens and len(matching_q_tokens) == 0:
            return "I couldn't find that information in the uploaded documents."

        # Check top chunk similarity
        top_chunk = chunks[0]
        if top_chunk.similarity_score < 0.25 and len(matching_q_tokens) < 1:
            return "I couldn't find enough information in the uploaded documents to answer that confidently."

        # Score chunks based on keyword matching
        scored_chunks = []
        for c in chunks:
            text_lower = c.text.lower()
            keyword_score = sum(1 for tok in q_tokens if tok in text_lower)
            combined_score = keyword_score * 2.0 + c.similarity_score
            scored_chunks.append((combined_score, keyword_score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        best_combined, best_keyword_score, best_chunk = scored_chunks[0]

        if best_keyword_score == 0 and best_chunk.similarity_score < 0.2:
            return "I couldn't find enough information in the uploaded documents to answer that confidently."

        # Extract the most relevant section or paragraph from the best chunk
        paragraphs = [p.strip() for p in best_chunk.text.split("\n\n") if p.strip()]
        scored_paras = []
        for p in paragraphs:
            p_score = sum(1 for tok in q_tokens if tok in p.lower())
            scored_paras.append((p_score, p))
        scored_paras.sort(key=lambda x: x[0], reverse=True)

        selected_paras = [p for score, p in scored_paras if score > 0]
        if not selected_paras:
            answer_text = paragraphs[0] if paragraphs else best_chunk.text
        else:
            answer_text = "\n\n".join(selected_paras[:2])

        page_str = f"Page {best_chunk.page}" if best_chunk.page is not None else "Page N/A"
        citation_str = f"\n\nSources:\n1. {best_chunk.document_name} — {page_str} (Chunk #{best_chunk.chunk_id})"

        return f"{answer_text}{citation_str}"


class RAGPipeline:
    """Coordinates Retrieval, Context Building, LLM Generation, and Source Citation."""

    def __init__(self, rtrvr: Optional[Retriever] = None, llm: Optional[LLMClient] = None):
        self.retriever = rtrvr or retriever
        self.llm = llm or LLMClient()

    def run(self, request: QueryRequest) -> QueryResponse:
        t_start = time.perf_counter()
        stages: List[PipelineStageTrace] = []

        # Stage 1: Document Retrieval (Vector Search)
        t0 = time.perf_counter()
        chunks, context_str, rtrv_metrics = self.retriever.retrieve(
            query=request.question,
            top_k=request.top_k or settings.DEFAULT_TOP_K,
            document_id=request.document_id
        )
        t1 = time.perf_counter()
        stages.append(
            PipelineStageTrace(
                stage="Vector Retrieval",
                status="success" if chunks else "no_chunks_found",
                duration_ms=round((t1 - t0) * 1000, 2),
                details={
                    "retrieved_count": len(chunks),
                    "top_similarity": chunks[0].similarity_score if chunks else 0.0,
                    "metrics": rtrv_metrics
                }
            )
        )

        # Stage 2: Context Construction
        t2 = time.perf_counter()
        stages.append(
            PipelineStageTrace(
                stage="Context Construction",
                status="success",
                duration_ms=round((t2 - t1) * 1000, 2),
                details={
                    "context_length_chars": len(context_str),
                    "sources_included": len(chunks)
                }
            )
        )

        # Stage 3: LLM Answer Generation
        t3 = time.perf_counter()
        raw_answer = self.llm.generate(
            question=request.question,
            context=context_str,
            chunks=chunks,
            temperature=request.temperature or settings.DEFAULT_TEMPERATURE,
            conversation_history=request.conversation_history
        )
        t4 = time.perf_counter()
        stages.append(
            PipelineStageTrace(
                stage="LLM Generation",
                status="success",
                duration_ms=round((t4 - t3) * 1000, 2),
                details={
                    "provider": self.llm.provider,
                    "answer_length_chars": len(raw_answer),
                    "temperature": request.temperature or settings.DEFAULT_TEMPERATURE
                }
            )
        )

        # Stage 4: Source Citation Extraction
        sources: List[Dict[str, Any]] = []
        for c in chunks:
            sources.append({
                "document": c.document_name,
                "document_id": c.document_id,
                "page": c.page,
                "chunk_id": c.chunk_id,
                "similarity": c.similarity_score,
                "distance": c.distance,
                "snippet": c.text[:220] + "..." if len(c.text) > 220 else c.text
            })

        t_end = time.perf_counter()
        trace = PipelineTrace(
            total_duration_ms=round((t_end - t_start) * 1000, 2),
            embedding_provider=self.retriever.embedder.provider_name,
            llm_provider=self.llm.provider,
            stages=stages
        )

        return QueryResponse(
            success=True,
            answer=raw_answer,
            sources=sources,
            retrieved_chunks=len(chunks),
            pipeline_trace=trace
        )


# Global singleton instance
rag_pipeline = RAGPipeline()
