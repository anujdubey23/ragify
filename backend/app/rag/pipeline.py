import time
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.rag.document_loader import DocumentLoader
from backend.app.rag.chunker import RecursiveCharacterChunker
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.vector_store import FAISSVectorStore
from backend.app.rag.bm25_retriever import BM25Retriever
from backend.app.rag.hybrid_retriever import HybridRetriever
from backend.app.rag.reranker import Reranker
from backend.app.rag.generator import LLMGenerator
from backend.app.utils.logging import logger, log_latency

class RAGPipeline:
    """
    End-to-end RAG Pipeline orchestrator:
    - Document Ingestion: Load -> Clean -> Chunk -> Embed -> FAISS + BM25 indexing
    - Query Processing: Hybrid Search -> Cross-Encoder Rerank -> Grounded Generation
    """

    def __init__(self):
        self.chunker = RecursiveCharacterChunker()
        self.vector_store = FAISSVectorStore(dimension=embedding_service.dimension)
        self.bm25_retriever = BM25Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_retriever=self.bm25_retriever,
            embedding_service=embedding_service
        )
        self.reranker = Reranker()
        self.generator = LLMGenerator()

        # Initialize BM25 from existing vector store metadata if available
        if self.vector_store.chunks_data:
            self.bm25_retriever.index_chunks(self.vector_store.chunks_data)

    def ingest_document(
        self,
        file_path: str,
        filename: str,
        document_id: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes complete ingestion for a new document.
        Returns the list of generated chunk records.
        """
        logger.info(f"Starting ingestion for document '{filename}' ({document_id})...")
        t0 = time.perf_counter()

        # 1. Load document pages/sections
        pages = DocumentLoader.load(file_path, filename)

        # 2. Chunk text with metadata
        chunker = RecursiveCharacterChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk_document_pages(pages, document_id, filename)

        if not chunks:
            raise ValueError(f"Document '{filename}' produced 0 usable text chunks.")

        # 3. Generate dense embeddings
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts(texts)

        # 4. Index in FAISS
        self.vector_store.add_vectors(embeddings, chunks)

        # 5. Index in BM25
        self.bm25_retriever.add_chunks(chunks)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(f"Ingestion completed for '{filename}': {len(chunks)} chunks in {elapsed_ms:.2f}ms.")
        return chunks

    def delete_document(self, document_id: str):
        """Removes a document from both FAISS and BM25 indices."""
        logger.info(f"Deleting document {document_id} from vector store and BM25 index...")
        self.vector_store.delete_document(document_id)
        self.bm25_retriever.delete_document(document_id)
        logger.info(f"Document {document_id} successfully deleted from indices.")

    async def query(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
        top_k_candidates: Optional[int] = None,
        semantic_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None,
        reranking_enabled: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes query through Hybrid Retrieval -> Reranking -> LLM Generation.
        """
        total_start = time.perf_counter()

        # 1. Hybrid Retrieval
        t_ret_start = time.perf_counter()
        candidates = self.hybrid_retriever.retrieve(
            query=question,
            top_k_candidates=top_k_candidates,
            semantic_weight=semantic_weight,
            bm25_weight=bm25_weight
        )
        retrieval_latency_ms = (time.perf_counter() - t_ret_start) * 1000

        # 2. Reranking
        t_rerank_start = time.perf_counter()
        top_chunks = self.reranker.rerank(
            query=question,
            candidates=candidates,
            top_k=top_k,
            enabled=reranking_enabled
        )
        rerank_latency_ms = (time.perf_counter() - t_rerank_start) * 1000

        # 3. LLM Generation & Grounding
        t_gen_start = time.perf_counter()
        gen_result = await self.generator.generate_response(
            question=question,
            retrieved_chunks=top_chunks,
            chat_history=chat_history,
            confidence_threshold=confidence_threshold,
            model_override=model,
            temp_override=temperature
        )
        generation_latency_ms = (time.perf_counter() - t_gen_start) * 1000

        total_latency_ms = (time.perf_counter() - total_start) * 1000

        # Assemble comprehensive response metadata
        return {
            "answer": gen_result["answer"],
            "sources": gen_result["sources"],
            "confidence": gen_result.get("confidence", 0.0),
            "insufficient_context": gen_result.get("insufficient_context", False),
            "retrieval_metadata": {
                "candidate_chunks_count": len(candidates),
                "top_k_chunks_count": len(top_chunks),
                "retrieval_latency_ms": round(retrieval_latency_ms, 2),
                "rerank_latency_ms": round(rerank_latency_ms, 2),
                "generation_latency_ms": round(generation_latency_ms, 2),
                "total_latency_ms": round(total_latency_ms, 2)
            }
        }

# Global singleton
rag_pipeline = RAGPipeline()
