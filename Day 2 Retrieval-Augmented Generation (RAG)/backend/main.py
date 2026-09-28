import os
import time
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models import (
    DocumentInfo,
    QueryRequest,
    QueryResponse,
    UploadResponse,
    DeleteResponse,
    HealthResponse,
)
from backend.ingestion.document_loader import DocumentLoader
from backend.ingestion.chunker import RecursiveChunker
from backend.embeddings.embedding_service import embedding_service
from backend.vectorstore.chroma_store import chroma_store
from backend.rag.pipeline import rag_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("docurag")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_SUBTITLE,
    version=settings.APP_VERSION,
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Returns application health, vector database status, and active provider info."""
    stats = chroma_store.get_stats()
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        vector_store=f"ChromaDB ({stats['collection_name']})",
        embedding_provider=embedding_service.provider_name,
        llm_provider=rag_pipeline.llm.provider,
        total_documents=stats["total_documents"],
        total_chunks=stats["total_chunks"],
    )


@app.post("/api/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
):
    """Uploads, validates, parses, chunks, embeds, and stores a document in ChromaDB."""
    t_start = time.perf_counter()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_ext}'. Allowed formats: {', '.join(sorted(settings.SUPPORTED_EXTENSIONS))}",
        )

    doc_id = str(uuid.uuid4())
    upload_dir = settings.get_upload_path()
    safe_filename = f"{doc_id}_{Path(file.filename).name}"
    file_path = upload_dir / safe_filename

    # Save uploaded file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file on server: {str(e)}"
        )

    # Validate file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum limit of {settings.MAX_FILE_SIZE_MB} MB."
        )

    # Ingestion Step 1 & 2: Parse and Clean
    try:
        loaded_doc = DocumentLoader.load(file_path)
        loaded_doc.document_name = Path(file.filename).name
    except ValueError as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Error loading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing document: {str(e)}"
        )

    # Ingestion Step 3: Chunking
    c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
    c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
    try:
        chunker = RecursiveChunker(chunk_size=c_size, chunk_overlap=c_overlap)
        chunks = chunker.chunk_document(loaded_doc, document_id=doc_id)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunking error: {str(e)}"
        )

    if not chunks:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document could not be divided into any readable chunks."
        )

    # Ingestion Step 4: Embedding Generation
    try:
        chunk_texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )

    # Ingestion Step 5: Store in ChromaDB
    try:
        chroma_store.add_chunks(chunks=chunks, embeddings=embeddings)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"ChromaDB storage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist vectors in ChromaDB: {str(e)}"
        )

    # Ingestion Step 6: Register in Document Catalog
    upload_time = time.strftime("%Y-%m-%d %H:%M:%S")
    doc_info = DocumentInfo(
        document_id=doc_id,
        document_name=file.filename,
        file_type=file_ext.lstrip("."),
        size_bytes=file_path.stat().st_size,
        total_chunks=len(chunks),
        char_count=loaded_doc.total_characters,
        upload_time=upload_time,
        status="indexed"
    )
    chroma_store.register_document(doc_info)

    duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(f"Indexed document '{file.filename}' ({len(chunks)} chunks) in {duration_ms} ms.")

    return UploadResponse(
        success=True,
        message=f"Document '{file.filename}' successfully processed and indexed ({len(chunks)} chunks).",
        document=doc_info,
        chunks_count=len(chunks),
        duration_ms=duration_ms
    )


@app.get("/api/documents", response_model=List[DocumentInfo])
def get_documents():
    """Returns the list of all currently indexed documents in the library."""
    return chroma_store.list_documents()


@app.delete("/api/documents/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str):
    """Deletes a document, removing its chunks from ChromaDB, catalog, and disk."""
    doc = chroma_store.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    deleted_chunks = chroma_store.delete_document(document_id)

    # Also clean up uploaded file if present
    upload_dir = settings.get_upload_path()
    for f in upload_dir.glob(f"{document_id}_*"):
        try:
            f.unlink()
        except Exception as e:
            logger.warning(f"Could not delete physical file {f}: {e}")

    logger.info(f"Deleted document '{doc.document_name}' ({deleted_chunks} vectors removed).")
    return DeleteResponse(
        success=True,
        message=f"Document '{doc.document_name}' and its {deleted_chunks} vector chunks were deleted.",
        deleted_document_id=document_id,
        deleted_chunks_count=deleted_chunks
    )


@app.get("/api/documents/{document_id}/chunks")
def get_document_chunks(document_id: str):
    """Retrieves all indexed chunks of a specific document for inspection."""
    doc = chroma_store.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    chunks = chroma_store.get_document_chunks(document_id)
    return {
        "document_id": document_id,
        "document_name": doc.document_name,
        "total_chunks": len(chunks),
        "chunks": chunks
    }


@app.post("/api/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """Performs full RAG similarity retrieval and grounded answer generation."""
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question string cannot be empty."
        )

    stats = chroma_store.get_stats()
    if stats["total_chunks"] == 0:
        return QueryResponse(
            success=True,
            answer="No documents have been uploaded yet. Please upload a document to begin asking questions.",
            sources=[],
            retrieved_chunks=0
        )

    try:
        response = rag_pipeline.run(request)
        return response
    except Exception as e:
        logger.error(f"Error during RAG query pipeline execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline execution failed: {str(e)}"
        )


# Serve frontend static assets
frontend_dir = settings.BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dir / "index.html")
