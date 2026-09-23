import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database.database import init_db, get_db
from backend.app.database.repository import DocumentRepository
from backend.app.rag.pipeline import rag_pipeline
from backend.app.rag.embeddings import embedding_service
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router, chat_endpoint, ChatRequest
from backend.app.api.evaluation import router as evaluation_router
from backend.app.utils.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing RAGify backend...")
    init_db()
    logger.info(f"Database initialized. Active vector count: {rag_pipeline.vector_store.index.ntotal}")

    # Synchronize BM25 from DB chunks if FAISS has items but BM25 is empty
    from backend.app.database.database import SessionLocal
    db = SessionLocal()
    try:
        repo = DocumentRepository(db)
        chunks = repo.get_all_chunks()
        if chunks and len(rag_pipeline.bm25_retriever.chunks) == 0:
            chunk_dicts = [
                {
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number,
                    "text": c.text,
                    "source": c.source
                }
                for c in chunks
            ]
            rag_pipeline.bm25_retriever.index_chunks(chunk_dicts)
            logger.info(f"Synchronized {len(chunk_dicts)} chunks from database to BM25 index.")
    finally:
        db.close()

    yield
    # Shutdown actions
    logger.info("Shutting down RAGify backend...")

app = FastAPI(
    title="RAGify — Intelligent Document RAG Chatbot",
    description="Production-grade, modular RAG API supporting hybrid retrieval, cross-encoder reranking, and anti-hallucination verification.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local dev and production frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(evaluation_router)

# Direct alias for POST /api/chat
@app.post("/api/chat", tags=["Chat"])
async def direct_chat_query(request: ChatRequest, db: Session = Depends(get_db)):
    return await chat_endpoint(request, db)

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint indicating service readiness."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_store_count": rag_pipeline.vector_store.index.ntotal,
        "bm25_count": len(rag_pipeline.bm25_retriever.chunks),
        "reranking_enabled": settings.RERANKING_ENABLED,
        "llm_provider": settings.LLM_PROVIDER
    }

@app.get("/api/stats", tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Provides high-level system metrics for the dashboard."""
    repo = DocumentRepository(db)
    stats = repo.get_stats()
    stats["active_vectors"] = rag_pipeline.vector_store.index.ntotal
    stats["bm25_indexed_chunks"] = len(rag_pipeline.bm25_retriever.chunks)
    stats["embedding_dimension"] = embedding_service.dimension
    return stats

@app.get("/api/settings", tags=["Settings"])
def get_runtime_settings():
    """Returns runtime parameters without exposing secret API keys."""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_temperature": settings.LLM_TEMPERATURE,
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "top_k_candidates": settings.TOP_K_CANDIDATES,
        "top_k": settings.TOP_K,
        "semantic_weight": settings.SEMANTIC_WEIGHT,
        "bm25_weight": settings.BM25_WEIGHT,
        "reranking_enabled": settings.RERANKING_ENABLED,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD
    }

@app.post("/api/settings", tags=["Settings"])
def update_runtime_settings(new_settings: dict):
    """Updates non-secret runtime hyperparameters dynamically."""
    allowed_keys = [
        "llm_model", "llm_temperature", "chunk_size", "chunk_overlap",
        "top_k_candidates", "top_k", "semantic_weight", "bm25_weight",
        "reranking_enabled", "confidence_threshold"
    ]
    for k, v in new_settings.items():
        if k in allowed_keys and hasattr(settings, k.upper()):
            setattr(settings, k.upper(), v)
            if k == "semantic_weight":
                rag_pipeline.hybrid_retriever.semantic_weight = float(v)
            elif k == "bm25_weight":
                rag_pipeline.hybrid_retriever.bm25_weight = float(v)
            elif k == "reranking_enabled":
                settings.RERANKING_ENABLED = bool(v)

    return {"message": "Settings updated successfully.", "current": get_runtime_settings()}

# Global exception handler for clean error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify backend logs."}
    )
