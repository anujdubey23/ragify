import tempfile
import numpy as np
import pytest
from backend.app.rag.vector_store import FAISSVectorStore

def test_faiss_add_search_delete():
    with tempfile.TemporaryDirectory() as temp_dir:
        dim = 8
        store = FAISSVectorStore(dimension=dim, storage_dir=temp_dir)

        # Create dummy normalized vectors
        v1 = np.ones((1, dim), dtype=np.float32) / np.sqrt(dim)
        v2 = np.zeros((1, dim), dtype=np.float32)
        v2[0, 0] = 1.0  # Unit vector along first dimension

        vectors = np.vstack([v1, v2])
        chunks = [
            {"chunk_id": "c1", "document_id": "docA", "text": "All ones content", "source": "A.pdf"},
            {"chunk_id": "c2", "document_id": "docB", "text": "First dimension content", "source": "B.pdf"}
        ]

        store.add_vectors(vectors, chunks)
        assert store.index.ntotal == 2

        # Search with vector close to v2
        query = np.zeros(dim, dtype=np.float32)
        query[0] = 1.0

        results = store.search(query, top_k=2)
        assert len(results) == 2
        assert results[0]["chunk_id"] == "c2"
        assert results[0]["document_id"] == "docB"

        # Persistence test
        store2 = FAISSVectorStore(dimension=dim, storage_dir=temp_dir)
        assert store2.index.ntotal == 2

        # Delete document docA
        store.delete_document("docA")
        assert store.index.ntotal == 1
        assert store.chunks_data[0]["document_id"] == "docB"
