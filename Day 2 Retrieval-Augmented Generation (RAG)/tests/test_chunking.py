from pathlib import Path
import pytest
from backend.ingestion.text_cleaner import TextCleaner
from backend.ingestion.document_loader import DocumentLoader, LoadedDocument, PageContent
from backend.ingestion.chunker import RecursiveChunker


def test_text_cleaner_normalizes_whitespace():
    raw = "  Hello   world! \t This is a test.   \n\n\n\n\nNew paragraph here.  \r\n"
    cleaned = TextCleaner.clean(raw)
    assert "  " not in cleaned
    assert "\r" not in cleaned
    assert "Hello world! This is a test." in cleaned
    assert "New paragraph here." in cleaned


def test_document_loader_txt():
    sample_txt = Path("sample_docs/rag_demo.txt")
    loaded = DocumentLoader.load(sample_txt)
    assert loaded.document_name == "rag_demo.txt"
    assert loaded.file_type == "txt"
    assert len(loaded.pages) == 1
    assert loaded.total_characters > 100
    assert "Retrieval-Augmented Generation" in loaded.pages[0].text


def test_document_loader_docx():
    sample_docx = Path("sample_docs/enterprise_architecture.docx")
    loaded = DocumentLoader.load(sample_docx)
    assert loaded.file_type == "docx"
    assert len(loaded.pages) >= 1
    assert "microservices architecture" in loaded.pages[0].text.lower()


def test_document_loader_pdf():
    sample_pdf = Path("sample_docs/sample_guide.pdf")
    loaded = DocumentLoader.load(sample_pdf)
    assert loaded.file_type == "pdf"
    assert len(loaded.pages) == 2
    assert loaded.pages[0].page_number == 1
    assert loaded.pages[1].page_number == 2
    assert "ChromaDB" in loaded.pages[0].text


def test_document_loader_rejects_unsupported_format(tmp_path):
    bad_file = tmp_path / "test.bin"
    bad_file.write_bytes(b"\x00\x01\x02\x03")
    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentLoader.load(bad_file)


def test_document_loader_rejects_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n\n   ", encoding="utf-8")
    with pytest.raises(ValueError, match="contains no readable or extractable text"):
        DocumentLoader.load(empty_file)


def test_recursive_chunker_basic():
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "Retrieval-Augmented Generation combines information retrieval with language generation. "
        "The retrieval stage searches a knowledge base for relevant chunks of information. "
        "The generation stage uses the retrieved context to formulate an accurate answer. "
        "This architecture significantly reduces hallucination and ensures factual grounding."
    )
    doc = LoadedDocument(
        document_name="test.txt",
        file_type="txt",
        pages=[PageContent(text=sample_text, page_number=None, char_count=len(sample_text))],
        total_characters=len(sample_text)
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= 120  # Allows slight boundary buffer
        assert chunk.metadata.document_name == "test.txt"
        assert chunk.metadata.total_chunks == len(chunks)
        assert chunk.metadata.chunk_id >= 0


def test_chunker_preserves_pdf_page_numbers():
    doc = LoadedDocument(
        document_name="multipage.pdf",
        file_type="pdf",
        pages=[
            PageContent(text="Content for page one of the document.", page_number=1, char_count=37),
            PageContent(text="Content for page two of the document.", page_number=2, char_count=37)
        ],
        total_characters=74
    )
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)
    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 2
    assert chunks[0].metadata.page == 1
    assert chunks[1].metadata.page == 2
