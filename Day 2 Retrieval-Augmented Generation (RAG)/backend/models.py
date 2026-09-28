from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    document_id: str
    document_name: str
    file_type: str
    size_bytes: int
    total_chunks: int
    char_count: int
    upload_time: str
    status: str = "indexed"


class ChunkMetadata(BaseModel):
    document_id: str
    document_name: str
    chunk_id: int
    page: Optional[int] = None
    source: str
    char_count: int
    total_chunks: int


class ChunkRecord(BaseModel):
    id: str
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: str
    document_name: str
    page: Optional[int] = None
    source: str
    text: str
    distance: float
    similarity_score: float


class SourceCitation(BaseModel):
    document: str
    page: Optional[int] = None
    chunk_id: int
    similarity: Optional[float] = None
    snippet: Optional[str] = None


class PipelineStageTrace(BaseModel):
    stage: str
    status: str
    duration_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineTrace(BaseModel):
    total_duration_ms: float
    embedding_provider: str
    llm_provider: str
    stages: List[PipelineStageTrace] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)
    conversation_history: Optional[List[Dict[str, str]]] = None


class QueryResponse(BaseModel):
    success: bool = True
    answer: str
    sources: List[Dict[str, Any]]
    retrieved_chunks: int
    pipeline_trace: Optional[PipelineTrace] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    document: DocumentInfo
    chunks_count: int
    duration_ms: float


class DeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_document_id: str
    deleted_chunks_count: int


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    vector_store: str
    embedding_provider: str
    llm_provider: str
    total_documents: int
    total_chunks: int
