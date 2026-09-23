import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database.database import get_db
from backend.app.database.repository import DocumentRepository
from backend.app.rag.pipeline import rag_pipeline
from backend.app.utils.file_validation import validate_uploaded_file
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a document (PDF, DOCX, TXT), validates it, stores it,
    and performs chunking and vector indexing synchronously.
    With lightweight embeddings this completes in ~1-2 seconds.
    """
    content = await file.read()
    sanitized_filename = validate_uploaded_file(file, content)

    doc_id = str(uuid.uuid4())
    ext = os.path.splitext(sanitized_filename)[1].lower().lstrip(".")

    # Save file to disk
    stored_filename = f"{doc_id}_{sanitized_filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record in database
    repo = DocumentRepository(db)
    doc = repo.create(
        doc_id=doc_id,
        filename=sanitized_filename,
        file_type=ext,
        file_size=len(content),
        file_path=file_path
    )

    # Process synchronously — lightweight embeddings use zero RAM and are instant
    try:
        logger.info(f"Starting synchronous ingestion for '{sanitized_filename}' ({doc_id})...")
        chunks = rag_pipeline.ingest_document(
            file_path=file_path,
            filename=sanitized_filename,
            document_id=doc_id
        )
        repo.save_chunks(chunks)
        repo.update_status(doc_id=doc_id, status="indexed", chunk_count=len(chunks))
        logger.info(f"Indexing completed for '{sanitized_filename}': {len(chunks)} chunks")

        return {
            "message": f"Document indexed successfully with {len(chunks)} chunks.",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": "indexed",
                "chunk_count": len(chunks),
                "created_at": doc.upload_date.isoformat()
            }
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to process document '{sanitized_filename}' ({doc_id}): {error_msg}")
        repo.update_status(doc_id=doc_id, status="failed", error_message=error_msg)
        return {
            "message": f"Upload saved but indexing failed: {error_msg}",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": "failed",
                "chunk_count": 0,
                "created_at": doc.upload_date.isoformat(),
                "error": error_msg
            }
        }

@router.get("")
def list_documents(db: Session = Depends(get_db)):
    """Returns list of all uploaded documents and their processing status."""
    repo = DocumentRepository(db)
    docs = repo.get_all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "upload_date": d.upload_date.isoformat() if d.upload_date else None,
            "error_message": d.error_message
        }
        for d in docs
    ]

@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Gets details and chunk previews for a single document."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = repo.get_chunks_by_document(document_id)
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
        "chunks": [
            {
                "chunk_id": c.id,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "text_preview": (c.text[:200] + "...") if len(c.text) > 200 else c.text
            }
            for c in chunks[:10]  # Sample first 10 chunks
        ]
    }

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document, its database records, and its FAISS/BM25 vectors."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from FAISS and BM25 indices
    rag_pipeline.delete_document(document_id)

    # Delete physical file from disk if it exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not remove physical file {doc.file_path}: {e}")

    # Delete from database (cascades to chunks)
    repo.delete(document_id)

    return {"message": f"Document '{doc.filename}' ({document_id}) deleted successfully."}
