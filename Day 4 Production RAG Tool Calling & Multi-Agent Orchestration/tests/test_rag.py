"""
Unit tests for RAG pipeline components in OrchestraRAG AI.
Tests document parser, chunker, embeddings, and vector store retrieval.
"""

import pytest
from backend.models import DocumentMetadata
from backend.rag.parser import DocumentParser
from backend.rag.chunker import TextChunker
from backend.rag.embeddings import EmbeddingService
from backend.rag.vector_store import VectorStoreManager


class TestRAGPipeline:
    """Test suite for RAG subsystem."""

    def test_text_document_parsing(self):
        sample_text = b"# Sample Title\n\nParagraph one.\n\nParagraph two."
        parser = DocumentParser()
        parsed = parser.parse_file("test.txt", sample_text, document_id="doc_test_1")
        assert parsed.document_id == "doc_test_1"
        assert parsed.total_pages == 1
        assert len(parsed.pages) == 1
        assert "Paragraph one." in parsed.pages[0].text

    def test_text_chunking_with_metadata(self):
        sample_text = b"# Section Alpha\n\n" + b"This is a longer passage designed to be chunked into pieces.\n\n" * 15
        parser = DocumentParser()
        parsed = parser.parse_file("manual.txt", sample_text, document_id="doc_manual")
        chunker = TextChunker(chunk_size=200, chunk_overlap=30)
        chunks = chunker.chunk_document(parsed)

        assert len(chunks) > 1
        for c in chunks:
            assert c.document_name == "manual.txt"
            assert c.page == 1
            assert c.char_length <= 300
            assert c.document_id == "doc_manual"

    def test_embedding_dimensions(self):
        service = EmbeddingService()
        vector = service.provider.embed_query("Multi-agent AI architecture")
        assert len(vector) == service.provider.dimension
        assert service.provider.dimension in (384, 1536)

    def test_vector_store_retrieval(self):
        store = VectorStoreManager()
        # Query for RAG guide content already indexed
        results = store.retrieve("What are the main components of a RAG system?", top_k=3)
        assert len(results) > 0
        assert results[0].source_type == "document"
        assert results[0].document is not None
        assert results[0].page >= 1
        assert results[0].relevance > 0.20

    def test_vector_store_stats(self):
        store = VectorStoreManager()
        stats = store.get_stats()
        assert stats["total_documents"] >= 1
        assert stats["total_chunks"] >= 1
        assert stats["status"] == "ready"
