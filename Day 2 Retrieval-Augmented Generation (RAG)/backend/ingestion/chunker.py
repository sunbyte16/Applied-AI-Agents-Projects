from typing import List, Optional
import uuid

from backend.ingestion.document_loader import LoadedDocument
from backend.models import ChunkRecord, ChunkMetadata
from backend.config import settings


class RecursiveChunker:
    """Splits documents into coherent semantic chunks with configurable size, overlap, and metadata."""

    def __init__(
        self,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Recursively splits a text into chunks respecting natural boundary separators."""
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Splits text using the first viable separator, then merges small pieces into chunks."""
        final_chunks = []
        separator = separators[-1]
        remaining_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                remaining_separators = separators[i + 1:]
                break

        # Split on the chosen separator
        if separator:
            splits = text.split(separator)
        else:
            # Character level fallback
            splits = list(text)

        # Merge pieces into chunks of size <= chunk_size with overlap
        current_chunk = []
        current_length = 0

        for piece in splits:
            piece_len = len(piece) + (len(separator) if current_chunk else 0)

            # If an individual piece exceeds chunk_size, recursively split it
            if piece_len > self.chunk_size and remaining_separators:
                if current_chunk:
                    chunk_text = separator.join(current_chunk).strip()
                    if chunk_text:
                        final_chunks.append(chunk_text)
                    current_chunk = []
                    current_length = 0

                sub_chunks = self._recursive_split(piece, remaining_separators)
                final_chunks.extend(sub_chunks)
                continue

            if current_length + piece_len <= self.chunk_size:
                current_chunk.append(piece)
                current_length += piece_len
            else:
                if current_chunk:
                    chunk_text = separator.join(current_chunk).strip()
                    if chunk_text:
                        final_chunks.append(chunk_text)

                    # Build overlap from the end of the current chunk
                    overlap_chunk = []
                    overlap_len = 0
                    for prev_piece in reversed(current_chunk):
                        added_len = len(prev_piece) + (len(separator) if overlap_chunk else 0)
                        if overlap_len + added_len <= self.chunk_overlap:
                            overlap_chunk.insert(0, prev_piece)
                            overlap_len += added_len
                        else:
                            break

                    current_chunk = overlap_chunk
                    current_length = overlap_len

                current_chunk.append(piece)
                current_length += piece_len

        if current_chunk:
            chunk_text = separator.join(current_chunk).strip()
            if chunk_text:
                final_chunks.append(chunk_text)

        return [c for c in final_chunks if c.strip()]

    def chunk_document(
        self, loaded_doc: LoadedDocument, document_id: Optional[str] = None
    ) -> List[ChunkRecord]:
        """Splits a LoadedDocument into ChunkRecords containing exact metadata.

        Preserves page information per chunk for multi-page documents (PDFs).
        """
        doc_id = document_id or str(uuid.uuid4())
        raw_chunks: List[dict] = []

        for page in loaded_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            splits = self.split_text(page_text)
            for split_content in splits:
                raw_chunks.append({
                    "text": split_content,
                    "page": page.page_number
                })

        total_chunks = len(raw_chunks)
        records: List[ChunkRecord] = []

        for idx, item in enumerate(raw_chunks):
            chunk_id_str = f"{doc_id}_chunk_{idx:04d}"
            metadata = ChunkMetadata(
                document_id=doc_id,
                document_name=loaded_doc.document_name,
                chunk_id=idx,
                page=item["page"],
                source=loaded_doc.document_name,
                char_count=len(item["text"]),
                total_chunks=total_chunks
            )

            records.append(
                ChunkRecord(
                    id=chunk_id_str,
                    text=item["text"],
                    metadata=metadata
                )
            )

        return records
