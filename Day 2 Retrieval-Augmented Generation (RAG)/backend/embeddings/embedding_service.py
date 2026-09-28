import abc
import hashlib
import math
import logging
from typing import List, Optional
import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(abc.ABC):
    """Abstract base class for all embedding providers."""

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return the friendly name of the provider."""
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document chunks (batch)."""
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single user query."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using OpenAI API (e.g., text-embedding-3-small)."""

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small", base_url: Optional[str] = None):
        from openai import OpenAI
        self._model = model_name
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._dim = 1536 if "large" not in model_name else 3072
        if "3-small" in model_name:
            self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self._model})"

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        if not texts:
            return []
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self._client.embeddings.create(model=self._model, input=batch)
            sorted_data = sorted(resp.data, key=lambda x: x.index)
            all_embeddings.extend([item.embedding for item in sorted_data])
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        resp = self._client.embeddings.create(model=self._model, input=[text])
        return resp.data[0].embedding


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using Google Gemini API (text-embedding-004)."""

    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        self._api_key = api_key
        self._model = model_name
        self._dim = 768

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self._model})"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:batchEmbedContents?key={self._api_key}"
        requests_payload = [
            {"model": f"models/{self._model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json={"requests": requests_payload})
            resp.raise_for_status()
            data = resp.json()
            return [item["values"] for item in data.get("embeddings", [])]

    def embed_query(self, text: str) -> List[float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:embedContent?key={self._api_key}"
        payload = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]}
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["embedding"]["values"]


class LocalDeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Fast, deterministic 384-dimensional dense semantic vector projector.

    Uses normalized subword token n-grams, character shingling, and semantic hash
    projections with L2 unit normalization. Guarantees real cosine similarity scores
    in ChromaDB without network dependencies or random numbers.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"Local Semantic Vectorizer ({self._dim}-d)"

    def _project_text(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        if not text:
            return vec

        normalized = text.lower()
        # Extract word tokens stripping punctuation
        raw_words = [
            w.strip(".,!?:;\"'()[]{}<>-/*`~")
            for w in normalized.split()
            if w.strip(".,!?:;\"'()[]{}<>-/*`~")
        ]

        if not raw_words:
            return vec

        # Sublinear term frequency for word unigrams
        from collections import Counter
        word_counts = Counter(raw_words)
        for word, count in word_counts.items():
            w_val = 3.0 * (1.0 + math.log(count))
            h = int.from_bytes(hashlib.sha256(word.encode("utf-8")).digest()[:4], "big") % self._dim
            vec[h] += w_val

            # Secondary hash for dispersion
            h2 = int.from_bytes(hashlib.md5(word.encode("utf-8")).digest()[:4], "big") % self._dim
            vec[h2] += w_val * 0.5

        # Word bigrams for phrase matching
        for i in range(len(raw_words) - 1):
            bg = f"{raw_words[i]}_{raw_words[i+1]}"
            h_bg = int.from_bytes(hashlib.sha256(bg.encode("utf-8")).digest()[:4], "big") % self._dim
            vec[h_bg] += 2.0

        # Character 3-grams and 4-grams for subword similarity
        clean_text = " " + " ".join(raw_words) + " "
        for n in (3, 4):
            for i in range(max(0, len(clean_text) - n + 1)):
                shingle = clean_text[i:i + n]
                h_shingle = int.from_bytes(hashlib.sha256(shingle.encode("utf-8")).digest()[:4], "big") % self._dim
                vec[h_shingle] += 0.4

        # L2 unit normalization
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-12:
            vec = [v / norm for v in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._project_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._project_text(text)


class EmbeddingService:
    """Factory and wrapper managing the active embedding provider."""

    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        self._provider = provider or self._resolve_provider()

    @property
    def provider(self) -> BaseEmbeddingProvider:
        return self._provider

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def dimension(self) -> int:
        return self._provider.dimension

    def _resolve_provider(self) -> BaseEmbeddingProvider:
        pref = settings.EMBEDDING_PROVIDER.lower().strip()

        # Explicit OpenAI
        if pref == "openai" or (pref == "auto" and settings.OPENAI_API_KEY):
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
                logger.info("Initializing OpenAI Embedding Provider.")
                return OpenAIEmbeddingProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model_name=settings.OPENAI_EMBEDDING_MODEL,
                    base_url=settings.OPENAI_BASE_URL,
                )

        # Explicit Gemini
        if pref == "gemini" or (pref == "auto" and settings.GEMINI_API_KEY):
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
                logger.info("Initializing Google Gemini Embedding Provider.")
                return GeminiEmbeddingProvider(
                    api_key=settings.GEMINI_API_KEY,
                    model_name=settings.GEMINI_EMBEDDING_MODEL,
                )

        # Fallback to high-quality local deterministic semantic embedding
        logger.info("Initializing Local Deterministic Semantic Embedding Provider.")
        return LocalDeterministicEmbeddingProvider(dimension=384)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._provider.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._provider.embed_query(text)


# Global singleton instance
embedding_service = EmbeddingService()
