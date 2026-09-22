import os
import json
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from backend.app.config import settings
from backend.app.utils.logging import logger, log_latency

class BaseVectorStore(ABC):
    """Abstract Vector Store interface to allow seamless cloud/database migrations."""

    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, chunks: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        pass

    @abstractmethod
    def persist(self) -> None:
        pass

    @abstractmethod
    def load(self) -> bool:
        pass

class FAISSVectorStore(BaseVectorStore):
    """
    FAISS vector database using IndexFlatIP for exact cosine similarity search
    over L2-normalized embeddings.
    Maintains synchronization between FAISS index IDs and rich chunk metadata.
    """

    def __init__(self, dimension: int = 384, storage_dir: Optional[str] = None):
        import faiss

        self.dimension = dimension
        self.storage_dir = Path(storage_dir or settings.VECTOR_STORE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.storage_dir / "faiss_index.bin"
        self.metadata_file = self.storage_dir / "faiss_metadata.json"

        self.index = faiss.IndexFlatIP(self.dimension)
        # Position index -> chunk metadata dictionary
        self.chunks_data: List[Dict[str, Any]] = []
        # In-memory fast vector cache for fast rebuild on document deletion
        self.vectors_cache: Optional[np.ndarray] = None

        # Attempt to load existing index
        self.load()

    def add_vectors(self, vectors: np.ndarray, chunks: List[Dict[str, Any]]) -> None:
        """
        Appends vectors and corresponding metadata chunks to FAISS index.
        """
        if len(vectors) == 0 or len(chunks) == 0:
            return

        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} does not match index dimension {self.dimension}")

        vectors = vectors.astype(np.float32)

        with log_latency("FAISS Add Vectors", f"count={len(chunks)}"):
            self.index.add(vectors)
            self.chunks_data.extend(chunks)

            # Update cache
            if self.vectors_cache is None or len(self.vectors_cache) == 0:
                self.vectors_cache = vectors.copy()
            else:
                self.vectors_cache = np.vstack([self.vectors_cache, vectors])

        logger.info(f"FAISS index now contains {self.index.ntotal} vectors.")
        self.persist()

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Performs inner product similarity search (equivalent to cosine similarity).
        Returns list of chunk dicts annotated with 'score'.
        """
        if self.index.ntotal == 0:
            return []

        # Ensure query is 2D float32
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)
        query_vector = query_vector.astype(np.float32)

        actual_k = min(top_k, self.index.ntotal)
        with log_latency("FAISS Search", f"top_k={actual_k}"):
            scores, indices = self.index.search(query_vector, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks_data):
                continue
            chunk = dict(self.chunks_data[idx])
            # Cosine similarity is in [-1, 1], normalized to [0, 1] for unified scoring
            norm_score = float(np.clip((score + 1.0) / 2.0, 0.0, 1.0))
            chunk["semantic_score"] = float(score)
            chunk["score"] = norm_score
            results.append(chunk)

        return results

    def delete_document(self, document_id: str) -> None:
        """
        Deletes all chunks belonging to a document and rebuilds the FAISS index.
        """
        import faiss

        if self.index.ntotal == 0 or not self.chunks_data:
            return

        indices_to_keep = [
            i for i, chunk in enumerate(self.chunks_data)
            if chunk.get("document_id") != document_id
        ]

        if len(indices_to_keep) == len(self.chunks_data):
            logger.info(f"No vectors found for document_id {document_id}")
            return

        logger.info(f"Rebuilding FAISS index after deleting document {document_id} (keeping {len(indices_to_keep)} vectors)...")

        new_index = faiss.IndexFlatIP(self.dimension)
        new_chunks = [self.chunks_data[i] for i in indices_to_keep]

        if len(indices_to_keep) > 0 and self.vectors_cache is not None:
            new_vectors = self.vectors_cache[indices_to_keep]
            new_index.add(new_vectors)
            self.vectors_cache = new_vectors
        else:
            self.vectors_cache = None

        self.index = new_index
        self.chunks_data = new_chunks

        self.persist()
        logger.info(f"FAISS index rebuilt. Remaining vectors: {self.index.ntotal}")

    def persist(self) -> None:
        """Saves FAISS index and metadata mapping to disk."""
        import faiss

        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks_data, f, ensure_ascii=False, indent=2)

            if self.vectors_cache is not None:
                cache_file = self.storage_dir / "vectors_cache.npy"
                np.save(str(cache_file), self.vectors_cache)

            logger.info(f"Persisted FAISS index ({self.index.ntotal} vectors) to {self.storage_dir}")
        except Exception as e:
            logger.error(f"Failed to persist FAISS index: {str(e)}")

    def load(self) -> bool:
        """Loads existing FAISS index and metadata from disk if available."""
        import faiss

        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.chunks_data = json.load(f)

                cache_file = self.storage_dir / "vectors_cache.npy"
                if cache_file.exists():
                    self.vectors_cache = np.load(str(cache_file))

                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors and {len(self.chunks_data)} chunks.")
                return True
            except Exception as e:
                logger.warning(f"Could not load existing FAISS index: {str(e)}. Initializing clean index.")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.chunks_data = []
                self.vectors_cache = None
        return False

    def clear(self) -> None:
        """Clears all vectors and metadata."""
        import faiss
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks_data = []
        self.vectors_cache = None
        self.persist()
