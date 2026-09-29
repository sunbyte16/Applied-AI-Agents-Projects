"""
Vector Store Manager for OrchestraRAG AI.
Integrates with ChromaDB PersistentClient for persistent, metadata-rich semantic indexing and retrieval.
"""

import datetime
import os
from typing import Any, Dict, List, Optional
import chromadb
from backend.config import settings
from backend.models import DocumentMetadata, Evidence
from backend.rag.chunker import DocumentChunk
from backend.rag.embeddings import embedding_service


class VectorStoreManager:
    """Manages persistent ChromaDB vector storage and semantic retrieval."""

    COLLECTION_NAME = "orchestrarag_knowledge_base"

    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIRECTORY):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=embedding_service.chroma_adapter,
            metadata={"hnsw:space": "cosine"},
        )
        self._doc_registry: Dict[str, DocumentMetadata] = {}

    def index_chunks(self, doc_metadata: DocumentMetadata, chunks: List[DocumentChunk]) -> int:
        """Add chunks to persistent vector collection with rich metadata."""
        if not chunks:
            return 0

        ids = [c.chunk_uid for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "document_name": c.document_name,
                "page": c.page,
                "section": c.section or "",
                "chunk_id": c.chunk_id,
                "char_length": c.char_length,
            }
            for c in chunks
        ]

        # Chroma add handles batching
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        # Update local document catalog
        self._doc_registry[doc_metadata.document_id] = doc_metadata
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = settings.TOP_K,
        document_filter: Optional[List[str]] = None,
        min_relevance: float = settings.SIMILARITY_THRESHOLD,
    ) -> List[Evidence]:
        """Perform semantic similarity search and convert top hits to standardized Evidence objects."""
        if not query or not query.strip():
            return []

        cleaned_query = query.strip()
        count = self.collection.count()
        if count == 0:
            return []

        k = min(max(1, top_k), count)
        where_filter = None
        if document_filter:
            if len(document_filter) == 1:
                where_filter = {"document_name": document_filter[0]}
            elif len(document_filter) > 1:
                where_filter = {"document_name": {"$in": document_filter}}

        try:
            results = self.collection.query(
                query_texts=[cleaned_query],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            # If filtered query returns nothing or error
            results = self.collection.query(
                query_texts=[cleaned_query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )

        evidence_list: List[Evidence] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for text, meta, dist in zip(docs, metas, distances):
            # Chroma with cosine distance: distance in [0, 2], cosine similarity = 1 - distance
            cosine_similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)
            # Filter if below threshold
            if cosine_similarity < min_relevance:
                continue

            evidence_list.append(
                Evidence(
                    source_type="document",
                    document=meta.get("document_name", "Unknown Document"),
                    page=int(meta.get("page", 1)),
                    chunk_id=int(meta.get("chunk_id", 0)),
                    content=text,
                    relevance=cosine_similarity,
                    summary=f"Excerpt from {meta.get('document_name')} (Page {meta.get('page', 1)})",
                )
            )

        return evidence_list

    def list_documents(self) -> List[DocumentMetadata]:
        """Return all indexed documents and their chunk statistics."""
        # Query collection to discover distinct documents if not in memory
        try:
            all_data = self.collection.get(include=["metadatas"])
            metas = all_data.get("metadatas", [])
            doc_counts: Dict[str, Dict[str, Any]] = {}

            for m in metas:
                doc_name = m.get("document_name", "Unknown")
                doc_id = m.get("document_id", doc_name)
                if doc_id not in doc_counts:
                    doc_counts[doc_id] = {
                        "filename": doc_name,
                        "file_type": doc_name.split(".")[-1] if "." in doc_name else "txt",
                        "chunk_count": 0,
                    }
                doc_counts[doc_id]["chunk_count"] += 1

            doc_list = []
            for doc_id, info in doc_counts.items():
                cached = self._doc_registry.get(doc_id)
                uploaded_at = cached.uploaded_at if cached else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                file_size = cached.file_size_bytes if cached else info["chunk_count"] * 500
                doc_list.append(
                    DocumentMetadata(
                        document_id=doc_id,
                        filename=info["filename"],
                        file_type=info["file_type"],
                        chunk_count=info["chunk_count"],
                        uploaded_at=uploaded_at,
                        file_size_bytes=file_size,
                        status="indexed",
                    )
                )
            return doc_list
        except Exception:
            return list(self._doc_registry.values())

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        try:
            self.collection.delete(where={"document_id": document_id})
            if document_id in self._doc_registry:
                del self._doc_registry[document_id]
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Retrieve total document and chunk statistics."""
        total_chunks = self.collection.count()
        docs = self.list_documents()
        return {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "vector_store": "ChromaDB (Persistent)",
            "persist_directory": self.persist_dir,
            "embedding_provider": embedding_service.provider.provider_name,
            "status": "ready",
        }


# Global singleton instance
vector_store_manager = VectorStoreManager()
