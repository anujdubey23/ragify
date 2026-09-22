import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "embedding_model" in data

def test_settings_endpoint():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "chunk_size" in data
    assert "semantic_weight" in data

def test_document_upload_and_chat_flow():
    # 1. Upload a text document
    doc_content = (
        "Attention Is All You Need is a 2017 research paper presenting the Transformer architecture. "
        "The Transformer uses multi-head self-attention and eliminates recurrent neural networks. "
        "It achieves state-of-the-art results on machine translation tasks."
    )
    file_bytes = io.BytesIO(doc_content.encode("utf-8"))

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("attention_paper.txt", file_bytes, "text/plain")}
    )
    assert upload_res.status_code == 200
    doc_info = upload_res.json()["document"]
    doc_id = doc_info["id"]
    assert doc_info["status"] == "indexed"
    assert doc_info["chunk_count"] > 0

    # 2. Verify document in listing
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Query chat endpoint
    chat_res = client.post(
        "/api/chat",
        json={"question": "What architecture was introduced in Attention Is All You Need?"}
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert "Transformer" in chat_data["answer"]
    assert len(chat_data["sources"]) > 0
    assert chat_data["sources"][0]["document"] == "attention_paper.txt"

    # 4. Check conversation history
    conv_id = chat_data["conversation_id"]
    conv_res = client.get(f"/api/chats/{conv_id}")
    assert conv_res.status_code == 200
    messages = conv_res.json()["messages"]
    assert len(messages) >= 2  # user and assistant

    # 5. Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
