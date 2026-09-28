import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings
from backend.models import ChunkRecord, RetrievedChunk, DocumentInfo

logger = logging.getLogger(__name__)


class ChromaStore:
    """Manages persistent ChromaDB vector storage and document indexing catalog."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or str(settings.get_chroma_path())
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.catalog_path = Path(self.persist_dir) / "documents_catalog.json"

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get or create collection with cosine similarity space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self._ensure_catalog()

    def _ensure_catalog(self) -> None:
        if not self.catalog_path.exists():
            self._save_catalog({})

    def _load_catalog(self) -> Dict[str, dict]:
        try:
            if self.catalog_path.exists():
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading document catalog: {e}")
        return {}

    def _save_catalog(self, catalog: Dict[str, dict]) -> None:
        try:
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving document catalog: {e}")

    def register_document(self, doc_info: DocumentInfo) -> None:
        catalog = self._load_catalog()
        catalog[doc_info.document_id] = doc_info.model_dump()
        self._save_catalog(catalog)

    def list_documents(self) -> List[DocumentInfo]:
        catalog = self._load_catalog()
        docs = []
        for d in catalog.values():
            docs.append(DocumentInfo(**d))
        return sorted(docs, key=lambda x: x.upload_time, reverse=True)

    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        catalog = self._load_catalog()
        data = catalog.get(document_id)
        return DocumentInfo(**data) if data else None

    def add_chunks(self, chunks: List[ChunkRecord], embeddings: List[List[float]]) -> int:
        """Adds chunks and their embeddings into ChromaDB collection in batches."""
        if not chunks:
            return 0

        batch_size = 100
        total = len(chunks)

        for i in range(0, total, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            ids = [c.id for c in batch_chunks]
            documents = [c.text for c in batch_chunks]
            metadatas = [
                {
                    "document_id": c.metadata.document_id,
                    "document_name": c.metadata.document_name,
                    "chunk_id": c.metadata.chunk_id,
                    "page": c.metadata.page if c.metadata.page is not None else -1,
                    "source": c.metadata.source,
                    "char_count": c.metadata.char_count,
                    "total_chunks": c.metadata.total_chunks,
                }
                for c in batch_chunks
            ]

            self.collection.upsert(
                ids=ids,
                embeddings=batch_embeddings,
                documents=documents,
                metadatas=metadatas
            )

        return total

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """Searches vector store for Top-K most similar chunks, with optional document filtering."""
        where_filter = None
        if document_id and document_id != "all":
            where_filter = {"document_id": document_id}

        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        retrieved: List[RetrievedChunk] = []

        if not results or not results.get("ids") or not results["ids"][0]:
            return retrieved

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id_str, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            # Cosine distance to similarity: similarity = 1 - distance
            # Clamped in [0.0, 1.0]
            sim = max(0.0, min(1.0, 1.0 - float(dist)))
            raw_page = meta.get("page")
            page_val = int(raw_page) if raw_page is not None and int(raw_page) != -1 else None

            retrieved.append(
                RetrievedChunk(
                    chunk_id=int(meta.get("chunk_id", 0)),
                    document_id=str(meta.get("document_id", "")),
                    document_name=str(meta.get("document_name", "unknown")),
                    page=page_val,
                    source=str(meta.get("source", "unknown")),
                    text=doc_text,
                    distance=round(float(dist), 4),
                    similarity_score=round(sim, 4)
                )
            )

        # Sort by similarity score descending
        retrieved.sort(key=lambda x: x.similarity_score, reverse=True)
        return retrieved

    def delete_document(self, document_id: str) -> int:
        """Deletes all chunks and metadata associated with a document from ChromaDB."""
        # Find count of chunks before deletion
        try:
            existing = self.collection.get(where={"document_id": document_id})
            deleted_count = len(existing["ids"]) if existing and "ids" in existing else 0
            if deleted_count > 0:
                self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            logger.error(f"Error deleting vectors for document {document_id}: {e}")
            deleted_count = 0

        # Remove from catalog
        catalog = self._load_catalog()
        if document_id in catalog:
            del catalog[document_id]
            self._save_catalog(catalog)

        return deleted_count

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieves all chunks for a specific document."""
        data = self.collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )
        chunks = []
        if data and "ids" in data:
            for c_id, text, meta in zip(data["ids"], data["documents"], data["metadatas"]):
                chunks.append({
                    "id": c_id,
                    "text": text,
                    "metadata": meta
                })
        chunks.sort(key=lambda x: x["metadata"].get("chunk_id", 0))
        return chunks

    def get_stats(self) -> Dict[str, Any]:
        catalog = self._load_catalog()
        return {
            "total_documents": len(catalog),
            "total_chunks": self.collection.count(),
            "collection_name": self.collection_name
        }


# Global singleton instance
chroma_store = ChromaStore()
