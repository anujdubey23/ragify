import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

# Resolve base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    APP_NAME: str = "RAGify"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,https://ragify-mu.vercel.app"

    # Data directories
    DATA_DIR: str = str(BACKEND_DIR / "data")
    UPLOAD_DIR: str = str(BACKEND_DIR / "data" / "uploads")
    VECTOR_STORE_DIR: str = str(BACKEND_DIR / "data" / "vectorstore")
    EVALUATION_DIR: str = str(BACKEND_DIR / "data" / "evaluation")
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'data' / 'ragify.db'}"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "openai", "groq", "gemini", "mock"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "lightweight"  # "lightweight", "openai", or "sentence-transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # Chunking Hyperparameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Retrieval Hyperparameters
    TOP_K_CANDIDATES: int = 15
    TOP_K: int = 5
    SEMANTIC_WEIGHT: float = 0.7
    BM25_WEIGHT: float = 0.3
    CONFIDENCE_THRESHOLD: float = 0.35

    # Reranking
    RERANKING_ENABLED: bool = False
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # File limits
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "allow"

# Singleton configuration instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(settings.EVALUATION_DIR, exist_ok=True)
