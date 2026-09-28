import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    APP_NAME: str = "DocuRAG AI"
    APP_SUBTITLE: str = "Document Intelligence & Retrieval-Augmented Q&A"
    APP_VERSION: str = "1.0.0"

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    UPLOAD_DIR: str = "./data/uploads"
    COLLECTION_NAME: str = "docurag_documents"
    CATALOG_FILE: str = "./chroma_db/documents_catalog.json"

    # Ingestion & Chunking Defaults
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 150
    DEFAULT_TOP_K: int = 5
    DEFAULT_TEMPERATURE: float = 0.2
    MAX_FILE_SIZE_MB: int = 20
    SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx", ".md"]

    # Provider Options: 'auto' | 'openai' | 'gemini' | 'local'
    EMBEDDING_PROVIDER: str = "auto"
    LLM_PROVIDER: str = "auto"

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_CHAT_MODEL: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            p = self.BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_chroma_path(self) -> Path:
        p = Path(self.CHROMA_PERSIST_DIR)
        if not p.is_absolute():
            p = self.BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
# Ensure directories exist
settings.get_upload_path()
settings.get_chroma_path()
