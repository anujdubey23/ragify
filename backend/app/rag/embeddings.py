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
        if self._model is None:
            logger.info(f"Loading embedding model: '{settings.EMBEDDING_MODEL}' on device '{settings.EMBEDDING_DEVICE}'...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                model_name_or_path=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
            logger.info("Embedding model loaded successfully.")

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embeds a list of document chunk texts.
        Returns a float32 numpy array of shape (N, D) normalized to unit length.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        self._load_model()
        with log_latency("Embed texts", f"count={len(texts)}"):
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a user query in the exact same vector space.
        Returns a 1D float32 numpy array of shape (D,) normalized to unit length.
        """
        self._load_model()
        cleaned_query = query.strip()
        embedding = self._model.encode(
            cleaned_query,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding.astype(np.float32)

# Global singleton
embedding_service = EmbeddingModel()
