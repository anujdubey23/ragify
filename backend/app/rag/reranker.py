from typing import List, Dict, Any, Optional
import numpy as np
from backend.app.config import settings
from backend.app.utils.logging import logger, log_latency

class Reranker:
    """
    Reranks candidate chunks using a Cross-Encoder or fast hybrid scoring fallback.

    Why Reranking Matters in RAG:
    -----------------------------
    1. Bi-encoders (FAISS embeddings) compute representations of query and document separately.
       They are ultra-fast for MIPS (Maximum Inner Product Search) across millions of vectors,
       but cannot capture fine-grained token-level cross-interactions.
    2. Cross-encoders feed the concatenation [CLS] Query [SEP] Chunk [SEP] directly through
       full transformer self-attention layers, computing full token-to-token interactions.
    3. The 2-stage retrieval pattern (Fast Hybrid Retrieval for Top-15 -> Cross-Encoder for Top-5)
       achieves optimal latency-accuracy trade-offs for production RAG systems.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self._model = None

    def _load_model(self):
        if self._model is None and settings.RERANKING_ENABLED:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading Cross-Encoder reranker: '{self.model_name}'...")
                self._model = CrossEncoder(self.model_name, max_length=512)
                logger.info("Cross-Encoder reranker loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder ('{self.model_name}'): {e}. Falling back to hybrid score reranking.")
                self._model = None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        enabled: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunks against the query.
        Returns top_k chunks sorted by final rerank score.
        """
        k = top_k or settings.TOP_K
        is_enabled = enabled if enabled is not None else settings.RERANKING_ENABLED

        if not candidates:
            return []

        if not is_enabled:
            # Reranking disabled: return top_k candidates directly
            logger.info("Reranking disabled; returning top candidate chunks by hybrid score.")
            return candidates[:k]

        self._load_model()

        if self._model is None:
            # Fallback if cross-encoder model failed to initialize
            return candidates[:k]

        with log_latency("Cross-Encoder Rerank", f"candidates={len(candidates)}"):
            # Build (query, text) pairs
            pairs = [[query, chunk.get("text", "")] for chunk in candidates]
            raw_scores = self._model.predict(pairs)

            # Apply sigmoid normalization to bring logits into [0, 1]
            scores = 1.0 / (1.0 + np.exp(-raw_scores))

        # Assign rerank scores
        reranked = []
        for i, chunk in enumerate(candidates):
            item = dict(chunk)
            score_val = float(scores[i])
            item["rerank_score"] = score_val
            item["score"] = score_val
            reranked.append(item)

        # Sort descending by rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        final_top = reranked[:k]

        logger.info(f"Reranked {len(candidates)} candidates to top-{len(final_top)} chunks.")
        return final_top
