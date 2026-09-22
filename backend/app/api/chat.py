import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.database.repository import ChatRepository
from backend.app.rag.pipeline import rag_pipeline
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/chats", tags=["Chat"])

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    model: Optional[str] = Field(None, description="Optional LLM model override")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_k: Optional[int] = Field(None, ge=1, le=20)
    semantic_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    bm25_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    reranking_enabled: Optional[bool] = Field(None)

@router.post("")
@router.post("/query")  # Also support /api/chat directly
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handles user chat questions:
    - Finds or creates conversation
    - Retrieves relevant context across all documents (Dense + BM25 + Reranking)
    - Generates grounded answer with source citations
    - Stores turn in conversation history
    """
    repo = ChatRepository(db)

    # 1. Manage Conversation
    conv_id = request.conversation_id
    if conv_id:
        conv = repo.get_conversation(conv_id)
        if not conv:
            conv = repo.create_conversation(title=request.question[:40] + "...")
            conv_id = conv.id
    else:
        conv = repo.create_conversation(title=request.question[:40] + "...")
        conv_id = conv.id

    # 2. Fetch recent conversation context for pronoun resolution & multi-turn memory
    past_messages = repo.get_messages(conv_id, limit=6)
    chat_history = [{"role": m.role, "content": m.content} for m in past_messages]

    # Save user message
    repo.add_message(conv_id=conv_id, role="user", content=request.question)

    # 3. Execute RAG Pipeline
    rag_result = await rag_pipeline.query(
        question=request.question,
        chat_history=chat_history,
        top_k=request.top_k,
        semantic_weight=request.semantic_weight,
        bm25_weight=request.bm25_weight,
        reranking_enabled=request.reranking_enabled,
        model=request.model,
        temperature=request.temperature
    )

    # Save assistant message
    repo.add_message(
        conv_id=conv_id,
        role="assistant",
        content=rag_result["answer"],
        sources=rag_result.get("sources"),
        metadata=rag_result.get("retrieval_metadata")
    )

    return {
        "conversation_id": conv_id,
        "answer": rag_result["answer"],
        "sources": rag_result.get("sources", []),
        "confidence": rag_result.get("confidence", 0.0),
        "insufficient_context": rag_result.get("insufficient_context", False),
        "retrieval_metadata": rag_result.get("retrieval_metadata", {})
    }

@router.get("")
def list_conversations(db: Session = Depends(get_db)):
    """Lists all active and previous conversation sessions."""
    repo = ChatRepository(db)
    convs = repo.list_conversations()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in convs
    ]

@router.get("/{conversation_id}")
def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieves full message history with citations and metadata for a conversation."""
    repo = ChatRepository(db)
    conv = repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = repo.get_messages(conversation_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources_json) if m.sources_json else [],
                "metadata": json.loads(m.metadata_json) if m.metadata_json else {},
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    }

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Deletes a conversation and its messages."""
    repo = ChatRepository(db)
    success = repo.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"message": "Conversation deleted successfully."}
