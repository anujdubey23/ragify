import numpy as np
import pytest
from backend.app.rag.embeddings import embedding_service

def test_embedding_dimension_and_norm():
    texts = ["Generative AI with retrieval augmented generation", "Neural language models"]
    vectors = embedding_service.embed_texts(texts)

    assert isinstance(vectors, np.ndarray)
    assert vectors.shape[0] == 2
    assert vectors.shape[1] == embedding_service.dimension
    assert vectors.dtype == np.float32

    # L2 Norm should be approximately 1.0 (unit normalized)
    for vec in vectors:
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, abs=1e-3) == 1.0

def test_query_embedding_matches_space():
    query_vec = embedding_service.embed_query("What is RAG?")
    assert query_vec.ndim == 1
    assert query_vec.shape[0] == embedding_service.dimension
    norm = np.linalg.norm(query_vec)
    assert pytest.approx(norm, abs=1e-3) == 1.0
