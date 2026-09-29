"""
Document Parser for OrchestraRAG AI.
Parses PDF, DOCX, and TXT files while preserving exact page provenance and structural boundaries.
"""

import io
import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    """A page or discrete section extracted from a document."""
    page_number: int
    text: str
    section: Optional[str] = None


class ParsedDocument(BaseModel):
    """Structured representation of a parsed document."""
    document_id: str
    filename: str
    file_type: str
    total_pages: int
    pages: List[ParsedPage] = Field(default_factory=list)
    raw_character_count: int = 0


class DocumentParser:
    """Multi-format document ingestion engine for PDF, DOCX, and TXT."""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize whitespace and strip unprintable characters."""
        if not text:
            return ""
        # Normalize carriage returns and non-breaking spaces
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
        # Remove consecutive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def parse_txt(cls, content: bytes, filename: str, document_id: str) -> ParsedDocument:
        """Parse plain text or Markdown files."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")

        cleaned = cls._clean_text(text)
        page = ParsedPage(page_number=1, text=cleaned)
        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            file_type="txt",
            total_pages=1,
            pages=[page],
            raw_character_count=len(cleaned),
        )

    @classmethod
    def parse_pdf(cls, content: bytes, filename: str, document_id: str) -> ParsedDocument:
        """Parse PDF files preserving page boundaries using pypdf."""
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(content))
        pages: List[ParsedPage] = []
        total_chars = 0

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned = cls._clean_text(page_text)
            if cleaned:
                total_chars += len(cleaned)
                pages.append(ParsedPage(page_number=idx + 1, text=cleaned))

        # Handle empty/scanned PDFs fallback
        if not pages:
            pages.append(ParsedPage(page_number=1, text="[Warning: PDF contained no extractable text layer]"))

        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            file_type="pdf",
            total_pages=len(reader.pages) or 1,
            pages=pages,
            raw_character_count=total_chars,
        )

    @classmethod
    def parse_docx(cls, content: bytes, filename: str, document_id: str) -> ParsedDocument:
        """Parse DOCX documents using python-docx."""
        import docx

        doc = docx.Document(io.BytesIO(content))
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        combined_text = cls._clean_text("\n\n".join(full_text))
        page = ParsedPage(page_number=1, text=combined_text)
        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            file_type="docx",
            total_pages=1,
            pages=[page],
            raw_character_count=len(combined_text),
        )

    @classmethod
    def parse_file(cls, filename: str, content: bytes, document_id: Optional[str] = None) -> ParsedDocument:
        """Dispatch document parsing based on file extension."""
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        doc_id = document_id or f"doc_{abs(hash(filename + str(len(content)))) % 1000000}"

        if ext in ("txt", "md", "csv", "json"):
            return cls.parse_txt(content, filename, doc_id)
        elif ext == "pdf":
            return cls.parse_pdf(content, filename, doc_id)
        elif ext in ("docx", "doc"):
            return cls.parse_docx(content, filename, doc_id)
        else:
            # Fallback to text parsing
            return cls.parse_txt(content, filename, doc_id)
