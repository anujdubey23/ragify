import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)      # bytes
    file_path = Column(String(512), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="uploading") # uploading, processing, indexed, failed
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True)       # doc_id_chunk_idx
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)     # 1-indexed for PDF, null for txt/docx without pages
    text = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    metadata_json = Column(Text, nullable=True)

    document = relationship("Document", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)        # user, assistant, system
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)       # JSON string of citation items
    metadata_json = Column(Text, nullable=True)      # retrieval stats, latencies
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    total_questions = Column(Integer, nullable=False)
    precision_at_k = Column(Float, nullable=False)
    recall_at_k = Column(Float, nullable=False)
    context_relevance = Column(Float, nullable=False)
    faithfulness = Column(Float, nullable=False)
    answer_relevance = Column(Float, nullable=False)
    avg_latency_ms = Column(Float, nullable=False)
    details_json = Column(Text, nullable=False)
