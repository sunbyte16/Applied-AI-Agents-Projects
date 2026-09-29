"""
Document Seeding Script for OrchestraRAG AI.
Parses sample knowledge base documents and indexes them in ChromaDB.
"""

import datetime
import glob
import os
from backend.models import DocumentMetadata
from backend.rag.chunker import TextChunker
from backend.rag.parser import DocumentParser
from backend.rag.vector_store import vector_store_manager

def seed_sample_documents(sample_dir: str = "sample_docs"):
    """Parse and index all files in sample_docs directory."""
    files = glob.glob(os.path.join(sample_dir, "*.*"))
    print(f"Discovered {len(files)} files to index in {sample_dir}...")

    parser = DocumentParser()
    chunker = TextChunker()

    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            content = f.read()

        doc_id = f"doc_{os.path.splitext(filename)[0]}"
        parsed = parser.parse_file(filename, content, document_id=doc_id)
        chunks = chunker.chunk_document(parsed)

        metadata = DocumentMetadata(
            document_id=doc_id,
            filename=filename,
            file_type=parsed.file_type,
            chunk_count=len(chunks),
            uploaded_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            file_size_bytes=len(content),
            status="indexed",
        )

        indexed_count = vector_store_manager.index_chunks(metadata, chunks)
        print(f"Indexed '{filename}': {indexed_count} chunks.")

    stats = vector_store_manager.get_stats()
    print("Seeding complete. Vector store statistics:", stats)

if __name__ == "__main__":
    seed_sample_documents()
