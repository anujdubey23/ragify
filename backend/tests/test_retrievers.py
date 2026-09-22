import pytest
from backend.app.rag.bm25_retriever import BM25Retriever
from backend.app.rag.hybrid_retriever import HybridRetriever
from backend.app.rag.vector_store import FAISSVectorStore
from backend.app.rag.embeddings import embedding_service

def test_bm25_keyword_matching():
    retriever = BM25Retriever()
    chunks = [
        {"chunk_id": "c1", "document_id": "d1", "text": "Convolutional Neural Networks are great for computer vision."},
        {"chunk_id": "c2", "document_id": "d2", "text": "Recurrent Neural Networks model sequential time-series data."},
        {"chunk_id": "c3", "document_id": "d3", "text": "Transformers employ self-attention for sequence modeling."}
    ]
    retriever.index_chunks(chunks)

    results = retriever.search("computer vision convolutional", top_k=2)
    assert len(results) > 0
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["bm25_score"] > 0

def test_hybrid_weighted_retrieval():
    dim = embedding_service.dimension
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        vstore = FAISSVectorStore(dimension=dim, storage_dir=temp_dir)
        bm25 = BM25Retriever()

        chunks = [
            {"chunk_id": "c1", "document_id": "d1", "text": "Gradient descent optimizes the objective function parameters."},
            {"chunk_id": "c2", "document_id": "d2", "text": "Transformers utilize multi-head attention mechanisms."}
        ]

        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts(texts)

        vstore.add_vectors(embeddings, chunks)
        bm25.index_chunks(chunks)

        hybrid = HybridRetriever(vstore, bm25, embedding_service, semantic_weight=0.7, bm25_weight=0.3)
        results = hybrid.retrieve("multi-head attention", top_k_candidates=2)

        assert len(results) == 2
        # Transformers chunk should rank first
        assert results[0]["chunk_id"] == "c2"
        assert "hybrid_score" in results[0]
