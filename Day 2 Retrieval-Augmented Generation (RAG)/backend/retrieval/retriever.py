import time
from typing import List, Optional, Tuple, Dict, Any

from backend.models import RetrievedChunk
from backend.embeddings.embedding_service import EmbeddingService, embedding_service
from backend.vectorstore.chroma_store import ChromaStore, chroma_store


class Retriever:
    """Orchestrates query embedding, vector search, and context construction."""

    def __init__(
        self,
        vector_store: Optional[ChromaStore] = None,
        embedder: Optional[EmbeddingService] = None
    ):
        self.vector_store = vector_store or chroma_store
        self.embedder = embedder or embedding_service

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> Tuple[List[RetrievedChunk], str, Dict[str, float]]:
        """Performs end-to-end retrieval for a user question.

        Args:
            query: The user's natural language question.
            top_k: Number of relevant chunks to retrieve.
            document_id: Optional document ID to filter chunks.

        Returns:
            Tuple of (retrieved_chunks, formatted_context_string, timing_metrics_dict).
        """
        metrics = {}

        # 1. Embed user query
        t0 = time.perf_counter()
        query_embedding = self.embedder.embed_query(query)
        t1 = time.perf_counter()
        metrics["query_embedding_ms"] = round((t1 - t0) * 1000, 2)

        # 2. Similarity search in ChromaDB
        chunks = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id
        )
        t2 = time.perf_counter()
        metrics["vector_search_ms"] = round((t2 - t1) * 1000, 2)

        # 3. Construct delimited context
        context_str = self.format_context(chunks)
        t3 = time.perf_counter()
        metrics["context_construction_ms"] = round((t3 - t2) * 1000, 2)
        metrics["total_retrieval_ms"] = round((t3 - t0) * 1000, 2)

        return chunks, context_str, metrics

    @staticmethod
    def format_context(chunks: List[RetrievedChunk]) -> str:
        """Constructs clear, delimited context for the LLM prompt."""
        if not chunks:
            return "No relevant documents found."

        parts = []
        for i, chunk in enumerate(chunks, 1):
            page_info = f"Page: {chunk.page}" if chunk.page is not None else "Page: N/A"
            part = (
                f"--- SOURCE {i} ---\n"
                f"Document: {chunk.document_name}\n"
                f"{page_info}\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"Relevance Score: {chunk.similarity_score:.4f}\n"
                f"Content:\n{chunk.text.strip()}\n"
                f"----------------------------------------"
            )
            parts.append(part)

        return "\n\n".join(parts)


# Global singleton instance
retriever = Retriever()
