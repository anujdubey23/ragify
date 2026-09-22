import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.models import Document, DocumentChunk, Conversation, ChatMessage, EvaluationRun

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, doc_id: str, filename: str, file_type: str, file_size: int, file_path: str) -> Document:
        doc = Document(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status="processing",
            chunk_count=0
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, doc_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def get_all(self) -> List[Document]:
        return self.db.query(Document).order_by(Document.upload_date.desc()).all()

    def update_status(self, doc_id: str, status: str, chunk_count: Optional[int] = None, error_message: Optional[str] = None):
        doc = self.get_by_id(doc_id)
        if doc:
            doc.status = status
            if chunk_count is not None:
                doc.chunk_count = chunk_count
            if error_message is not None:
                doc.error_message = error_message
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def delete(self, doc_id: str) -> bool:
        doc = self.get_by_id(doc_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False

    def save_chunks(self, chunks_data: List[Dict[str, Any]]):
        for data in chunks_data:
            chunk = DocumentChunk(
                id=data["chunk_id"],
                document_id=data["document_id"],
                chunk_index=data["chunk_index"],
                page_number=data.get("page_number"),
                text=data["text"],
                source=data.get("source", ""),
                metadata_json=json.dumps(data.get("metadata", {}))
            )
            self.db.add(chunk)
        self.db.commit()

    def get_chunks_by_document(self, doc_id: str) -> List[DocumentChunk]:
        return self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).order_by(DocumentChunk.chunk_index).all()

    def get_all_chunks(self) -> List[DocumentChunk]:
        return self.db.query(DocumentChunk).all()

    def get_stats(self) -> Dict[str, Any]:
        total_docs = self.db.query(func.count(Document.id)).scalar() or 0
        indexed_docs = self.db.query(func.count(Document.id)).filter(Document.status == "indexed").scalar() or 0
        total_chunks = self.db.query(func.count(DocumentChunk.id)).scalar() or 0
        total_conversations = self.db.query(func.count(Conversation.id)).scalar() or 0
        total_questions = self.db.query(func.count(ChatMessage.id)).filter(ChatMessage.role == "user").scalar() or 0
        return {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "total_chunks": total_chunks,
            "total_conversations": total_conversations,
            "total_questions": total_questions
        }

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, title: str = "New Chat") -> Conversation:
        conv = Conversation(title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conv_id).first()

    def list_conversations(self) -> List[Conversation]:
        return self.db.query(Conversation).order_by(Conversation.updated_at.desc()).all()

    def update_conversation_title(self, conv_id: str, title: str):
        conv = self.get_conversation(conv_id)
        if conv:
            conv.title = title
            self.db.commit()

    def delete_conversation(self, conv_id: str) -> bool:
        conv = self.get_conversation(conv_id)
        if conv:
            self.db.delete(conv)
            self.db.commit()
            return True
        return False

    def add_message(self, conv_id: str, role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None, metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        msg = ChatMessage(
            conversation_id=conv_id,
            role=role,
            content=content,
            sources_json=json.dumps(sources) if sources else None,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, conv_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        query = self.db.query(ChatMessage).filter(ChatMessage.conversation_id == conv_id).order_by(ChatMessage.created_at.asc())
        if limit:
            query = query.limit(limit)
        return query.all()

class EvaluationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_run(self, total_questions: int, precision: float, recall: float, context_relevance: float, faithfulness: float, answer_relevance: float, avg_latency_ms: float, details: List[Dict[str, Any]]) -> EvaluationRun:
        run = EvaluationRun(
            total_questions=total_questions,
            precision_at_k=precision,
            recall_at_k=recall,
            context_relevance=context_relevance,
            faithfulness=faithfulness,
            answer_relevance=answer_relevance,
            avg_latency_ms=avg_latency_ms,
            details_json=json.dumps(details)
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_runs(self, limit: int = 10) -> List[EvaluationRun]:
        return self.db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit).all()
