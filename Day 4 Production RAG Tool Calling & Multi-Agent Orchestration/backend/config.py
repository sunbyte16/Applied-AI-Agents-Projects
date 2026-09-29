"""
OrchestraRAG AI - Production Configuration
Loads validated settings from environment variables and .env file.
Enforces security bounds, retry limits, and resource quotas.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env from root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))


class Settings:
    """Production configuration and security guardrails."""

    ROOT_DIR: str = ROOT_DIR

    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # LLM Provider Credentials
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")

    # LLM Generation Defaults
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-120b")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))

    # Embeddings & Vector Database
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    CHROMA_PERSIST_DIRECTORY: str = os.path.join(
        ROOT_DIR, os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db").lstrip("./")
    )
    SQLITE_DB_PATH: str = os.path.join(
        ROOT_DIR, os.getenv("SQLITE_DB_PATH", "data/app_database.sqlite").lstrip("./")
    )

    # Tool Credentials
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")
    SEARCH_API_KEY: Optional[str] = os.getenv("SEARCH_API_KEY") or os.getenv("TAVILY_API_KEY")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # RAG Tuning Parameters
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))

    # Multi-Agent Workflow Bounds & Retries
    MAX_AGENT_RETRIES: int = int(os.getenv("MAX_AGENT_RETRIES", "2"))
    MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "5"))
    MAX_WORKFLOW_STEPS: int = int(os.getenv("MAX_WORKFLOW_STEPS", "12"))
    MAX_VERIFICATION_LOOPS: int = int(os.getenv("MAX_VERIFICATION_LOOPS", "2"))
    TOOL_TIMEOUT_SECONDS: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "10.0"))

    # Resource & Security Limits
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    MAX_DOCUMENTS: int = 50
    MAX_CHUNKS_PER_QUERY: int = 10
    REQUEST_TIMEOUT_SECONDS: float = 60.0

    @classmethod
    def get_active_llm_provider(cls) -> str:
        """Return the active LLM provider based on configured API keys."""
        if cls.GROQ_API_KEY and not cls.GROQ_API_KEY.startswith("gsk_your"):
            return "groq"
        if cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("sk-your"):
            return "openai"
        return "mock"

    @classmethod
    def is_search_available(cls) -> bool:
        """Check if search capability is available."""
        if cls.SEARCH_API_KEY or cls.TAVILY_API_KEY:
            return True
        try:
            from ddgs import DDGS
            return True
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                return True
            except ImportError:
                return False


settings = Settings()
