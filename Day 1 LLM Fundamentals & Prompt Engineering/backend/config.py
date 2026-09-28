"""
PromptLab AI - Configuration Management
Handles environment variables, security defaults, and API settings.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Locate and load the .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ==============================================================================
# Security Decision:
# API keys are read server-side only from environment variables / .env.
# They are NEVER sent to the browser or included in any client-facing response.
# ==============================================================================
# Primary API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()

# Base URL resolution
_base_url_env = os.getenv("OPENAI_BASE_URL", "").strip()

# Provider resolution
ACTIVE_API_KEY: str = ""
OPENAI_BASE_URL: str = ""
PROVIDER_NAME: str = "OpenAI"

if OPENAI_API_KEY and OPENAI_API_KEY not in ("your_openai_api_key_here", "your_key_here", "sk-your-key-here"):
    ACTIVE_API_KEY = OPENAI_API_KEY
    OPENAI_BASE_URL = _base_url_env
    PROVIDER_NAME = "OpenAI"
    AVAILABLE_MODELS: List[str] = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini").strip()
elif GEMINI_API_KEY and GEMINI_API_KEY not in ("your_gemini_api_key_here", "your_key_here"):
    ACTIVE_API_KEY = GEMINI_API_KEY
    OPENAI_BASE_URL = _base_url_env or "https://generativelanguage.googleapis.com/v1beta/openai/"
    PROVIDER_NAME = "Google Gemini"
    AVAILABLE_MODELS: List[str] = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash").strip()
elif GROQ_API_KEY and GROQ_API_KEY not in ("your_groq_api_key_here", "your_key_here"):
    ACTIVE_API_KEY = GROQ_API_KEY
    OPENAI_BASE_URL = _base_url_env or "https://api.groq.com/openai/v1"
    PROVIDER_NAME = "Groq"
    AVAILABLE_MODELS: List[str] = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile").strip()
else:
    ACTIVE_API_KEY = OPENAI_API_KEY
    OPENAI_BASE_URL = _base_url_env
    PROVIDER_NAME = "OpenAI"
    AVAILABLE_MODELS: List[str] = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini").strip()

# Guardrails & Validation Limits
MAX_INPUT_LENGTH: int = 10_000  # Prevent denial-of-service / token exhaustion
MIN_INPUT_LENGTH: int = 1
DEFAULT_TEMPERATURE: float = 0.3
MIN_TEMPERATURE: float = 0.0
MAX_TEMPERATURE: float = 1.0
REQUEST_TIMEOUT_SECONDS: float = 45.0

# Server configuration
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))


def is_api_key_configured() -> bool:
    """Check if a valid, non-placeholder API key has been provided."""
    key = ACTIVE_API_KEY
    if not key:
        return False
    if key in ("your_openai_api_key_here", "your_gemini_api_key_here", "your_groq_api_key_here", "your_key_here", "sk-your-key-here"):
        return False
    return len(key) > 5


def get_masked_api_key() -> str:
    """Return a safe masked version of the API key for diagnostics (e.g. sk-****1234)."""
    if not is_api_key_configured():
        return "Not Configured"
    key = ACTIVE_API_KEY
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}****{key[-4:]}"
