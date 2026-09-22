import pytest
from backend.app.rag.chunker import RecursiveCharacterChunker

def test_chunker_size_and_overlap():
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    assert chunker.chunk_size == 100
    assert chunker.chunk_overlap == 20

    long_text = "Machine learning is a field of artificial intelligence. " * 10
    pages = [{"text": long_text, "page_number": 1, "source": "test.pdf"}]
    chunks = chunker.chunk_document_pages(pages, "doc123", "test.pdf")

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]) <= 120  # Allows slight margin depending on separators
        assert chunk["document_id"] == "doc123"
        assert chunk["document_name"] == "test.pdf"
        assert chunk["page_number"] == 1
        assert "chunk_id" in chunk

def test_chunker_preserves_page_numbers():
    chunker = RecursiveCharacterChunker(chunk_size=200, chunk_overlap=50)
    pages = [
        {"text": "Section on page 1 covering embeddings and vector models.", "page_number": 1, "source": "paper.pdf"},
        {"text": "Section on page 2 covering cross-encoders and rerankers.", "page_number": 2, "source": "paper.pdf"}
    ]
    chunks = chunker.chunk_document_pages(pages, "paper_id", "paper.pdf")
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[-1]["page_number"] == 2

def test_chunker_invalid_overlap():
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=150)
