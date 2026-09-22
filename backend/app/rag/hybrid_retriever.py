from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.rag.vector_store import FAISSVectorStore
from backend.app.rag.bm25_retriever import BM25Retriever
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.utils.logging import logger, log_latency

class HybridRetriever:
    """
    Hybrid retriever combining Dense Semantic Search (FAISS)
    with Sparse Lexical Search (BM25) using configurable weighted fusion.
    """

    def __init__(
        self,
        vector_store: FAISSVectorStore,
        bm25_retriever: BM25Retriever,
        embedding_service: EmbeddingModel,
        semantic_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.embedding_service = embedding_service
        self.semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
        self.bm25_weight = bm25_weight if bm25_weight is not None else settings.BM25_WEIGHT

        # Normalize weights so sum is 1.0
        total_w = self.semantic_weight + self.bm25_weight
        if total_w > 0:
            self.semantic_weight /= total_w
            self.bm25_weight /= total_w
        else:
            self.semantic_weight = 0.7
            self.bm25_weight = 0.3

    def retrieve(
        self,
        query: str,
        top_k_candidates: Optional[int] = None,
        semantic_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes dense vector search and sparse BM25 search in parallel,
        merges results using weighted hybrid scoring, and returns candidates.
        """
        k_candidates = top_k_candidates or settings.TOP_K_CANDIDATES
        sem_w = semantic_weight if semantic_weight is not None else self.semantic_weight
        bm_w = bm25_weight if bm25_weight is not None else self.bm25_weight

        # Normalize weights
        w_sum = sem_w + bm_w
        if w_sum > 0:
            sem_w /= w_sum
            bm_w /= w_sum

        with log_latency("Hybrid Retrieval", f"query='{query[:30]}'"):
            # 1. Dense Semantic Search
            query_vector = self.embedding_service.embed_query(query)
            semantic_results = self.vector_store.search(query_vector, top_k=k_candidates)

            # 2. Sparse BM25 Keyword Search
            bm25_results = self.bm25_retriever.search(query, top_k=k_candidates)

            # 3. Combine & Fuse Scores
            combined_candidates: Dict[str, Dict[str, Any]] = {}

            # Populate dense results
            for chunk in semantic_results:
                cid = chunk["chunk_id"]
                combined_candidates[cid] = dict(chunk)
                combined_candidates[cid]["dense_score"] = chunk.get("score", 0.0)
                combined_candidates[cid]["sparse_score"] = 0.0

            # Populate or update with sparse results
            for chunk in bm25_results:
                cid = chunk["chunk_id"]
                sparse_score = chunk.get("score", 0.0)
                if cid in combined_candidates:
                    combined_candidates[cid]["sparse_score"] = sparse_score
                else:
                    item = dict(chunk)
                    item["dense_score"] = 0.0
                    item["sparse_score"] = sparse_score
                    combined_candidates[cid] = item

            # Compute final hybrid score
            for cid, chunk in combined_candidates.items():
                d_score = chunk.get("dense_score", 0.0)
                s_score = chunk.get("sparse_score", 0.0)
                hybrid_score = (sem_w * d_score) + (bm_w * s_score)
                chunk["score"] = float(hybrid_score)
                chunk["hybrid_score"] = float(hybrid_score)

            # Sort descending by hybrid score
            sorted_candidates = sorted(
                combined_candidates.values(),
                key=lambda x: x["hybrid_score"],
                reverse=True
            )

            results = sorted_candidates[:k_candidates]
            logger.info(
                f"Hybrid retrieval merged {len(semantic_results)} dense and {len(bm25_results)} sparse "
                f"into {len(results)} candidate chunks."
            )
            return results
