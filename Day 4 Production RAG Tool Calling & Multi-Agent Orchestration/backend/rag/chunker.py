"""
Semantic Chunker for OrchestraRAG AI.
Partitions documents into semantically coherent passages while preserving exact metadata provenance.
"""

import re
from typing import List, Optional
from pydantic import BaseModel
from backend.config import settings
from backend.rag.parser import ParsedDocument


class DocumentChunk(BaseModel):
    """An individual text chunk with strict metadata attribution."""
    chunk_uid: str
    chunk_id: int
    document_id: str
    document_name: str
    page: int
    section: Optional[str] = None
    content: str
    char_length: int


class TextChunker:
    """Configurable text chunker preserving page numbers and section headers."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text by double newlines or headers."""
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def chunk_document(self, doc: ParsedDocument) -> List[DocumentChunk]:
        """Split a ParsedDocument into chunks, strictly tracking page provenance."""
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Detect top-level section if present
            current_section = page.section
            paragraphs = self._split_into_paragraphs(page_text)

            current_chunk_text = ""
            for p in paragraphs:
                # Detect Markdown headers
                if p.startswith("#"):
                    header_line = p.split("\n")[0].strip("# ")
                    if header_line:
                        current_section = header_line

                if not current_chunk_text:
                    current_chunk_text = p
                elif len(current_chunk_text) + len(p) + 2 <= self.chunk_size:
                    current_chunk_text += "\n\n" + p
                else:
                    # Current chunk is full, record it
                    chunk_uid = f"{doc.document_id}_p{page.page_number}_c{global_chunk_idx}"
                    chunks.append(
                        DocumentChunk(
                            chunk_uid=chunk_uid,
                            chunk_id=global_chunk_idx,
                            document_id=doc.document_id,
                            document_name=doc.filename,
                            page=page.page_number,
                            section=current_section,
                            content=current_chunk_text,
                            char_length=len(current_chunk_text),
                        )
                    )
                    global_chunk_idx += 1

                    # Create overlap from end of previous text
                    overlap_text = current_chunk_text[-self.chunk_overlap :] if self.chunk_overlap > 0 else ""
                    current_chunk_text = (overlap_text + "\n\n" + p).strip()

            # Record trailing chunk for this page
            if current_chunk_text:
                chunk_uid = f"{doc.document_id}_p{page.page_number}_c{global_chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_uid=chunk_uid,
                        chunk_id=global_chunk_idx,
                        document_id=doc.document_id,
                        document_name=doc.filename,
                        page=page.page_number,
                        section=current_section,
                        content=current_chunk_text,
                        char_length=len(current_chunk_text),
                    )
                )
                global_chunk_idx += 1

        return chunks
