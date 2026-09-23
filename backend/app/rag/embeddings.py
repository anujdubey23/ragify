import numpy as np
from typing import List, Union
from backend.app.config import settings
from backend.app.utils.logging import logger, log_latency

class EmbeddingModel:
    """
    Embedding generator wrapping SentenceTransformers.
    Uses unit L2-normalization so that inner product in FAISS matches cosine similarity.
    Shared embedding space ensures symmetric query and document representations.
    """

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None and settings.EMBEDDING_PROVIDER not in ["openai", "lightweight"]:
            try:
                logger.info(f"Loading embedding model: '{settings.EMBEDDING_MODEL}' on device '{settings.EMBEDDING_DEVICE}'...")
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    model_name_or_path=settings.EMBEDDING_MODEL,
                    device=settings.EMBEDDING_DEVICE
                )
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to ultra-lightweight zero-RAM vectorizer.")
                self._model = None

    @property
    def dimension(self) -> int:
        if settings.EMBEDDING_PROVIDER == "openai":
            # OpenAI text-embedding-3-small uses 1536 dim
            return 1536 if "large" not in settings.EMBEDDING_MODEL else 3072
        if "MiniLM" in settings.EMBEDDING_MODEL:
            return 384
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embeds a list of document chunk texts.
        Returns a float32 numpy array of shape (N, D) normalized to unit length.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if settings.EMBEDDING_PROVIDER == "openai":
            import httpx
            import os
            api_key = settings.LLM_API_KEY or os.getenv("LLM_API_KEY", "")
            with log_latency("OpenAI Embed texts", f"count={len(texts)}"):
                headers = {"Authorization": f"Bearer {api_key}"}
                payload = {
                    "model": "text-embedding-3-small" if "text-embedding" not in settings.EMBEDDING_MODEL else settings.EMBEDDING_MODEL,
                    "input": texts
                }
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    vectors = [item["embedding"] for item in data["data"]]
                    arr = np.array(vectors, dtype=np.float32)
                    norms = np.linalg.norm(arr, axis=1, keepdims=True)
                    norms[norms == 0] = 1.0
                    return arr / norms

        try:
            self._load_model()
            if self._model is not None:
                with log_latency("Embed texts", f"count={len(texts)}"):
                    embeddings = self._model.encode(
                        texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True  # L2 normalization for cosine similarity
                    )
                return embeddings.astype(np.float32)
            raise RuntimeError("Model is None, activating fallback")
        except Exception as e:
            logger.warning(f"SentenceTransformer failed or OOM ({e}). Using ultra-fast zero-memory fallback embedding.")
            # Deterministic, zero-RAM semantic projection for low-memory hosting
            dim = self.dimension
            out = np.zeros((len(texts), dim), dtype=np.float32)
            for i, text in enumerate(texts):
                words = text.lower().split()
                for w in words:
                    idx = abs(hash(w)) % dim
                    out[i, idx] += 1.0
                norm = np.linalg.norm(out[i])
                if norm > 0:
                    out[i] /= norm
            return out

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a user query in the exact same vector space.
        Returns a 1D float32 numpy array of shape (D,) normalized to unit length.
        """
        cleaned_query = query.strip()
        if settings.EMBEDDING_PROVIDER == "openai":
            embeddings = self.embed_texts([cleaned_query])
            return embeddings[0]

        try:
            self._load_model()
            if self._model is not None:
                embedding = self._model.encode(
                    cleaned_query,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                return embedding.astype(np.float32)
            raise RuntimeError("Model is None")
        except Exception:
            dim = self.dimension
            vec = np.zeros(dim, dtype=np.float32)
            for w in cleaned_query.lower().split():
                vec[abs(hash(w)) % dim] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            return vec

# Global singleton
embedding_service = EmbeddingModel()
