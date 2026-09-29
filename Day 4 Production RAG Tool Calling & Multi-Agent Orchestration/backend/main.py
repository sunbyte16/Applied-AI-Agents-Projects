"""
FastAPI Main Application for OrchestraRAG AI.
Exposes REST APIs for multi-agent workflows, document ingestion, tool inspection, and observability.
Serves the modern enterprise frontend application.
"""

import datetime
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.models import (
    DocumentMetadata,
    Evidence,
    ToolCallRecord,
    TraceEvent,
    VerificationResult,
    WorkflowRequest,
    WorkflowResponse,
)
from backend.observability.tracer import tracer
from backend.orchestration.graph import workflow_graph
from backend.rag.chunker import TextChunker
from backend.rag.parser import DocumentParser
from backend.rag.vector_store import vector_store_manager
from backend.tools.registry import tool_registry

app = FastAPI(
    title="OrchestraRAG AI",
    description="Production Multi-Agent RAG & Tool Orchestration Platform",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory workflow cache for fast GET queries
_WORKFLOW_CACHE: Dict[str, WorkflowResponse] = {}


# =============================================================================
# Workflow Endpoints
# =============================================================================
@app.post("/api/workflow/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Execute dynamic multi-agent workflow for the submitted query."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    task_id = f"task_{uuid.uuid4().hex[:8]}"

    try:
        final_state = workflow_graph.run_workflow(
            query=request.query.strip(),
            task_id=task_id,
            mode=request.mode,
            filter_documents=request.filter_documents,
        )

        metrics = tracer.record_run(final_state)

        # Assemble clean WorkflowResponse
        agents_used = [
            a for a, status in final_state.get("agent_statuses", {}).items()
            if status == "completed"
        ]

        verification_raw = final_state.get("verification", {})
        verification_obj = None
        if verification_raw:
            verification_obj = VerificationResult(
                is_verified=verification_raw.get("is_verified", True),
                supported_claims=verification_raw.get("supported_claims", []),
                unsupported_claims=verification_raw.get("unsupported_claims", []),
                conflicts_detected=verification_raw.get("conflicts_detected", []),
                hallucination_risk=verification_raw.get("hallucination_risk", "low"),
                recommendation=verification_raw.get("recommendation", "approve"),
                details=verification_raw.get("details", ""),
            )

        response = WorkflowResponse(
            task_id=task_id,
            status="completed",
            user_query=request.query,
            final_answer=final_state.get("final_answer"),
            agents_used=agents_used,
            agent_statuses=final_state.get("agent_statuses", {}),
            evidence=final_state.get("evidence", []),
            tool_calls=final_state.get("tool_calls", []),
            verification=verification_obj,
            trace=final_state.get("trace", []),
            metrics=metrics,
            errors=final_state.get("errors", []),
        )

        _WORKFLOW_CACHE[task_id] = response
        return response

    except Exception as e:
        error_resp = WorkflowResponse(
            task_id=task_id,
            status="failed",
            user_query=request.query,
            final_answer="An error occurred while executing the multi-agent workflow.",
            agents_used=[],
            agent_statuses={},
            evidence=[],
            tool_calls=[],
            verification=None,
            trace=[],
            metrics={"status": "failed", "error": str(e)},
            errors=[f"Workflow execution failure: {type(e).__name__}: {str(e)}"],
        )
        _WORKFLOW_CACHE[task_id] = error_resp
        return error_resp


@app.get("/api/workflow/{task_id}", response_model=WorkflowResponse)
async def get_workflow_status(task_id: str) -> WorkflowResponse:
    """Retrieve full execution status and results for a previous task ID."""
    if task_id not in _WORKFLOW_CACHE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _WORKFLOW_CACHE[task_id]


@app.get("/api/workflow/{task_id}/trace", response_model=List[TraceEvent])
async def get_workflow_trace(task_id: str) -> List[TraceEvent]:
    """Retrieve execution trace timeline events for a task."""
    if task_id not in _WORKFLOW_CACHE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _WORKFLOW_CACHE[task_id].trace


@app.get("/api/workflow/{task_id}/evidence", response_model=List[Evidence])
async def get_workflow_evidence(task_id: str) -> List[Evidence]:
    """Retrieve grounded evidence collected for a task."""
    if task_id not in _WORKFLOW_CACHE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _WORKFLOW_CACHE[task_id].evidence


# =============================================================================
# Knowledge Base & Document Endpoints
# =============================================================================
@app.post("/api/documents/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)) -> DocumentMetadata:
    """Upload and index a document (PDF, TXT, DOCX) into persistent vector database."""
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size ({settings.MAX_FILE_SIZE_BYTES // (1024*1024)}MB).",
        )

    filename = file.filename or "uploaded_doc.txt"
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    parser = DocumentParser()
    chunker = TextChunker()

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

    vector_store_manager.index_chunks(metadata, chunks)
    return metadata


@app.get("/api/documents", response_model=List[DocumentMetadata])
async def list_documents() -> List[DocumentMetadata]:
    """List all indexed documents in the knowledge base."""
    return vector_store_manager.list_documents()


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete a document and its chunks from the vector database."""
    success = vector_store_manager.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Failed to delete document '{document_id}'.")
    return {"status": "deleted", "document_id": document_id}


# =============================================================================
# Tools & System Health Endpoints
# =============================================================================
@app.get("/api/tools")
async def get_tools() -> List[Dict[str, Any]]:
    """List all registered tools and their functional schemas."""
    tools = tool_registry.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
        }
        for t in tools
    ]


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Check system health, LLM configuration, and vector storage readiness."""
    stats = vector_store_manager.get_stats()
    return {
        "status": "operational",
        "service": "OrchestraRAG AI",
        "llm_provider": settings.get_active_llm_provider(),
        "model": settings.DEFAULT_MODEL,
        "search_available": settings.is_search_available(),
        "tools_registered": len(tool_registry.list_tools()),
        "knowledge_base": stats,
    }


# =============================================================================
# Static Frontend Serving
# =============================================================================
FRONTEND_DIR = os.path.join(settings.ROOT_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)

