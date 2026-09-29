"""
Embeddings Service for OrchestraRAG AI.
Provides dense vector representations using SentenceTransformers, OpenAI, or local deterministic projection.
Directly integrates with ChromaDB PersistentClient.
"""

import abc
import hashlib
import math
from typing import List, Optional
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from backend.config import settings


class BaseEmbeddingProvider(abc.ABC):
    """Abstract base class for all embedding providers."""

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class SentenceTransformerProvider(BaseEmbeddingProvider):
    """Local dense embedding provider using SentenceTransformers (all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dim = 384

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"SentenceTransformer ({self._model_name})"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embs = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embs.tolist()

    def embed_query(self, text: str) -> List[float]:
        embs = self._model.encode([text], show_progress_bar=False, normalize_embeddings=True)
        return embs[0].tolist()


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using OpenAI API (text-embedding-3-small)."""

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small", base_url: Optional[str] = None):
        from openai import OpenAI
        self._model = model_name
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self._model})"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> List[float]:
        resp = self._client.embeddings.create(input=[text], model=self._model)
        return resp.data[0].embedding


class LocalDeterministicProvider(BaseEmbeddingProvider):
    """Fast, deterministic 384-dimensional dense semantic vector projector.

    Uses normalized subword token n-grams and semantic hash projections with L2 unit normalization.
    Guarantees consistent cosine similarity scores in ChromaDB without network dependencies.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return f"Local Semantic Projector ({self._dim}-d)"

    def _project_text(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        if not text:
            return vec

        normalized = text.lower()
        words = [
            w.strip(".,!?:;\"'()[]{}<>-/*`~")
            for w in normalized.split()
            if w.strip(".,!?:;\"'()[]{}<>-/*`~")
        ]
        if not words:
            return vec

        from collections import Counter
        word_counts = Counter(words)

        for word, count in word_counts.items():
            tf = 1.0 + math.log(count)
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += tf * sign

            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i : i + 3]
                    nh = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    n_idx = nh % self._dim
                    n_sign = 0.5 if ((nh >> 4) & 1) == 0 else -0.5
                    vec[n_idx] += n_sign

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._project_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._project_text(text)


class ChromaEmbeddingAdapter(EmbeddingFunction):
    """ChromaDB compatible EmbeddingFunction adapter wrapping BaseEmbeddingProvider."""

    def __init__(self, provider: BaseEmbeddingProvider):
        self._provider = provider

    def name(self) -> str:
        """Return unique name for ChromaDB configuration."""
        return f"chroma_adapter_{self._provider.dimension}"

    def __call__(self, input: Documents) -> Embeddings:
        return self._provider.embed_documents(list(input))


class EmbeddingService:
    """Factory and management service for embedding providers."""

    _instance: Optional["EmbeddingService"] = None

    def __init__(self):
        self._provider: BaseEmbeddingProvider = self._resolve_provider()
        self._chroma_adapter = ChromaEmbeddingAdapter(self._provider)

    def _resolve_provider(self) -> BaseEmbeddingProvider:
        if settings.EMBEDDING_PROVIDER == "sentence_transformers":
            try:
                return SentenceTransformerProvider(settings.EMBEDDING_MODEL)
            except Exception:
                pass

        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your"):
            try:
                return OpenAIEmbeddingProvider(settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
            except Exception:
                pass

        return LocalDeterministicProvider()

    @property
    def provider(self) -> BaseEmbeddingProvider:
        return self._provider

    @property
    def chroma_adapter(self) -> ChromaEmbeddingAdapter:
        return self._chroma_adapter


# Global singleton
embedding_service = EmbeddingService()
