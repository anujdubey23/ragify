import re
import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from backend.app.utils.logging import logger, log_latency

class BM25Retriever:
    """
    Sparse keyword retriever implementing BM25Okapi.
    Ideal for exact keyword, acronym, name, and entity matching
    that dense vector embeddings can occasionally miss.
    """

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple, fast regex tokenizer: lowercases and extracts alphanumeric words."""
        return re.findall(r"\w+", text.lower())

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Replaces/initializes the BM25 index with a list of chunks.
        """
        self.chunks = list(chunks)
        self.tokenized_corpus = [self.tokenize(c.get("text", "")) for c in self.chunks]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index built with {len(self.chunks)} chunks.")
        else:
            self.bm25 = None

    def add_chunks(self, new_chunks: List[Dict[str, Any]]) -> None:
        """
        Appends new chunks and rebuilds the BM25 index.
        """
        if not new_chunks:
            return
        self.chunks.extend(new_chunks)
        self.tokenized_corpus = [self.tokenize(c.get("text", "")) for c in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        logger.info(f"BM25 index updated. Total chunks: {len(self.chunks)}.")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Performs BM25 keyword matching for query.
        Returns top_k chunks with normalized BM25 scores in [0, 1].
        """
        if self.bm25 is None or len(self.chunks) == 0:
            return []

        tokenized_query = self.tokenize(query)
        if not tokenized_query:
            return []

        with log_latency("BM25 Search", f"query='{query[:30]}'"):
            scores = self.bm25.get_scores(tokenized_query)

        # Filter out 0 scores or take top_k
        top_indices = np.argsort(scores)[::-1][:top_k]

        max_score = float(np.max(scores)) if len(scores) > 0 else 1.0
        min_score = float(np.min(scores)) if len(scores) > 0 else 0.0

        results = []
        for idx in top_indices:
            raw_score = float(scores[idx])
            if raw_score <= 0.0:
                continue

            chunk = dict(self.chunks[idx])
            # Min-Max normalization to [0, 1]
            if max_score > min_score:
                norm_score = (raw_score - min_score) / (max_score - min_score)
            else:
                norm_score = 1.0 if raw_score > 0 else 0.0

            chunk["bm25_raw_score"] = raw_score
            chunk["bm25_score"] = float(norm_score)
            chunk["score"] = float(norm_score)
            results.append(chunk)

        return results

    def delete_document(self, document_id: str) -> None:
        """Removes chunks for a document and rebuilds BM25 index."""
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]
        if self.chunks:
            self.tokenized_corpus = [self.tokenize(c.get("text", "")) for c in self.chunks]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.tokenized_corpus = []
            self.bm25 = None
        logger.info(f"BM25 index rebuilt after deleting doc {document_id}. Remaining chunks: {len(self.chunks)}")

    def clear(self) -> None:
        self.chunks = []
        self.tokenized_corpus = []
        self.bm25 = None
