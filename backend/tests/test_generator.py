import pytest
from backend.app.rag.generator import LLMGenerator, INSUFFICIENT_CONTEXT_MESSAGE
from backend.app.rag.reranker import Reranker

@pytest.mark.asyncio
async def test_generator_insufficient_context():
    generator = LLMGenerator()
    # When chunks list is empty
    res = await generator.generate_response("What is quantum computing?", retrieved_chunks=[])
    assert res["insufficient_context"] is True
    assert res["answer"] == INSUFFICIENT_CONTEXT_MESSAGE

    # When confidence is below threshold
    low_confidence_chunks = [
        {"chunk_id": "c1", "text": "Unrelated recipe for baking cookies.", "score": 0.1, "document_name": "cookies.txt"}
    ]
    res2 = await generator.generate_response(
        "Explain backpropagation",
        retrieved_chunks=low_confidence_chunks,
        confidence_threshold=0.5
    )
    assert res2["insufficient_context"] is True
    assert res2["answer"] == INSUFFICIENT_CONTEXT_MESSAGE

@pytest.mark.asyncio
async def test_generator_grounded_answer():
    generator = LLMGenerator()
    valid_chunks = [
        {
            "chunk_id": "c1",
            "document_name": "deep_learning.pdf",
            "page_number": 4,
            "text": "Backpropagation calculates gradients using the chain rule to update neural weights.",
            "score": 0.85
        }
    ]
    res = await generator.generate_response("How does backpropagation work?", retrieved_chunks=valid_chunks)
    assert res["insufficient_context"] is False
    assert len(res["sources"]) == 1
    assert res["sources"][0]["document"] == "deep_learning.pdf"
    assert res["sources"][0]["page"] == 4
    assert "Backpropagation" in res["answer"] or "gradients" in res["answer"]

def test_reranker_sorting():
    reranker = Reranker()
    candidates = [
        {"chunk_id": "c1", "text": "Completely unrelated text about gardening.", "hybrid_score": 0.4},
        {"chunk_id": "c2", "text": "Convolutional neural networks extract spatial feature maps in vision models.", "hybrid_score": 0.6}
    ]
    # Reranking disabled mode test
    top = reranker.rerank("CNN feature maps", candidates, top_k=1, enabled=False)
    assert len(top) == 1
    assert top[0]["chunk_id"] == "c1"  # First in candidate list

    # Reranking enabled mode test
    top2 = reranker.rerank("CNN feature maps", candidates, top_k=1, enabled=True)
    assert len(top2) == 1
    assert top2[0]["chunk_id"] == "c2"
