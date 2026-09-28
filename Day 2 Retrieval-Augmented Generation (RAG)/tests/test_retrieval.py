import uuid
import pytest
from backend.embeddings.embedding_service import LocalDeterministicEmbeddingProvider
from backend.vectorstore.chroma_store import ChromaStore
from backend.models import ChunkRecord, ChunkMetadata, DocumentInfo
from backend.retrieval.retriever import Retriever


@pytest.fixture
def temp_chroma(tmp_path):
    store = ChromaStore(
        persist_dir=str(tmp_path / "test_chroma"),
        collection_name=f"test_coll_{uuid.uuid4().hex[:8]}"
    )
    return store


def test_embedding_service_dimensions_and_determinism():
    provider = LocalDeterministicEmbeddingProvider(dimension=384)
    assert provider.dimension == 384
    text = "Retrieval-augmented generation improves LLM factual accuracy."
    emb1 = provider.embed_query(text)
    emb2 = provider.embed_query(text)

    assert len(emb1) == 384
    assert emb1 == emb2  # Deterministic

    # Batch embedding
    batch_embs = provider.embed_documents([text, "Different text for testing."])
    assert len(batch_embs) == 2
    assert len(batch_embs[0]) == 384


def test_chroma_store_add_and_query(temp_chroma):
    provider = LocalDeterministicEmbeddingProvider(dimension=384)

    # Prepare chunks
    doc_id = "doc_test_1"
    chunks = [
        ChunkRecord(
            id=f"{doc_id}_chunk_0",
            text="ChromaDB is an open-source vector database built for AI applications.",
            metadata=ChunkMetadata(
                document_id=doc_id,
                document_name="chroma_guide.txt",
                chunk_id=0,
                page=None,
                source="chroma_guide.txt",
                char_count=69,
                total_chunks=2
            )
        ),
        ChunkRecord(
            id=f"{doc_id}_chunk_1",
            text="Python is a widely used high-level programming language in machine learning.",
            metadata=ChunkMetadata(
                document_id=doc_id,
                document_name="chroma_guide.txt",
                chunk_id=1,
                page=None,
                source="chroma_guide.txt",
                char_count=77,
                total_chunks=2
            )
        )
    ]

    embeddings = provider.embed_documents([c.text for c in chunks])
    temp_chroma.add_chunks(chunks, embeddings)

    # Query for vector database
    q_emb = provider.embed_query("What is ChromaDB used for?")
    results = temp_chroma.query(query_embedding=q_emb, top_k=2)

    assert len(results) == 2
    # The first result should be the ChromaDB chunk
    assert "vector database" in results[0].text
    assert results[0].similarity_score > results[1].similarity_score


def test_chroma_store_document_filtering(temp_chroma):
    provider = LocalDeterministicEmbeddingProvider(dimension=384)

    doc_a = "doc_a"
    doc_b = "doc_b"

    chunks = [
        ChunkRecord(
            id=f"{doc_a}_chunk_0",
            text="Document A discusses climate change and renewable energy.",
            metadata=ChunkMetadata(
                document_id=doc_a,
                document_name="doc_a.txt",
                chunk_id=0,
                page=1,
                source="doc_a.txt",
                char_count=57,
                total_chunks=1
            )
        ),
        ChunkRecord(
            id=f"{doc_b}_chunk_0",
            text="Document B discusses quantum computing and qubits.",
            metadata=ChunkMetadata(
                document_id=doc_b,
                document_name="doc_b.txt",
                chunk_id=0,
                page=1,
                source="doc_b.txt",
                char_count=50,
                total_chunks=1
            )
        )
    ]

    embeddings = provider.embed_documents([c.text for c in chunks])
    temp_chroma.add_chunks(chunks, embeddings)

    # Query filtering by doc_b only
    q_emb = provider.embed_query("Tell me about technology")
    results = temp_chroma.query(query_embedding=q_emb, top_k=5, document_id=doc_b)

    assert len(results) == 1
    assert results[0].document_id == doc_b
    assert "quantum computing" in results[0].text


def test_chroma_store_delete_document(temp_chroma):
    provider = LocalDeterministicEmbeddingProvider(dimension=384)
    doc_id = "doc_to_delete"

    chunks = [
        ChunkRecord(
            id=f"{doc_id}_chunk_0",
            text="Temporary document content.",
            metadata=ChunkMetadata(
                document_id=doc_id,
                document_name="temp.txt",
                chunk_id=0,
                page=None,
                source="temp.txt",
                char_count=27,
                total_chunks=1
            )
        )
    ]
    embeddings = provider.embed_documents([c.text for c in chunks])
    temp_chroma.add_chunks(chunks, embeddings)

    doc_info = DocumentInfo(
        document_id=doc_id,
        document_name="temp.txt",
        file_type="txt",
        size_bytes=100,
        total_chunks=1,
        char_count=27,
        upload_time="2026-09-28 10:00:00"
    )
    temp_chroma.register_document(doc_info)

    assert len(temp_chroma.list_documents()) == 1

    deleted_count = temp_chroma.delete_document(doc_id)
    assert deleted_count == 1
    assert len(temp_chroma.list_documents()) == 0

    # Querying should yield 0 results
    q_emb = provider.embed_query("Temporary content")
    results = temp_chroma.query(query_embedding=q_emb, top_k=5)
    assert len(results) == 0
