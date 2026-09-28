"""
Configuration module for AgentLab AI.
Loads settings from environment variables and .env file safely.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env from root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))


class Settings:
    """Application settings and API credentials."""

    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # LLM API credentials & endpoints
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")

    # Default model configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-120b")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))
    DEFAULT_MAX_TOOL_CALLS: int = int(os.getenv("DEFAULT_MAX_TOOL_CALLS", "5"))
    TOOL_TIMEOUT_SECONDS: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "10.0"))

    # Tool credentials
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")
    SEARCH_API_KEY: Optional[str] = os.getenv("SEARCH_API_KEY") or os.getenv("TAVILY_API_KEY")

    # Safe display info (never leaks secrets)
    @classmethod
    def get_active_provider(cls) -> str:
        """Identify which LLM provider is active."""
        if cls.GROQ_API_KEY and "your_" not in cls.GROQ_API_KEY:
            return "groq"
        if cls.OPENAI_API_KEY and "your_" not in cls.OPENAI_API_KEY:
            return "openai"
        return "mock"

    @classmethod
    def is_llm_configured(cls) -> bool:
        """Check if a valid real LLM key is configured."""
        return cls.get_active_provider() in ("groq", "openai")


settings = Settings()
