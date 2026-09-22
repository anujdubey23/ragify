import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.config import settings
from backend.app.rag.pipeline import rag_pipeline
from backend.app.evaluation.metrics import RAGEvaluationMetrics
from backend.app.database.database import SessionLocal
from backend.app.database.repository import EvaluationRepository
from backend.app.utils.logging import logger

class RAGEvaluator:
    """
    Automated evaluation framework for RAGify.
    Runs standardized queries through the pipeline and assesses:
    - Retrieval Precision & Recall against expected documents
    - Context Relevance
    - Answer Faithfulness (groundedness)
    - Answer Relevance
    - End-to-end Latency
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path or Path(settings.EVALUATION_DIR) / "questions.json")

    def load_dataset(self) -> List[Dict[str, Any]]:
        if not self.dataset_path.exists():
            logger.warning(f"Evaluation dataset not found at {self.dataset_path}")
            return []
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def run_evaluation(self, custom_questions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Runs batch evaluation, computes metrics, and persists run to database.
        """
        questions = custom_questions or self.load_dataset()
        if not questions:
            raise ValueError("No evaluation questions available to run.")

        logger.info(f"Starting RAG evaluation across {len(questions)} test cases...")

        results = []
        total_p = 0.0
        total_r = 0.0
        total_cr = 0.0
        total_faith = 0.0
        total_ans_rel = 0.0
        total_lat = 0.0

        for item in questions:
            qid = item.get("id", str(time.time()))
            q_text = item.get("question", "")
            exp_sources = item.get("expected_sources", [])
            exp_answer = item.get("expected_answer", "")

            # Execute pipeline
            t0 = time.perf_counter()
            response = await rag_pipeline.query(question=q_text)
            latency_ms = (time.perf_counter() - t0) * 1000

            generated_answer = response.get("answer", "")
            sources = response.get("sources", [])
            retrieved_doc_names = [s.get("document", "") for s in sources]
            retrieved_contexts = [s.get("full_text", s.get("preview", "")) for s in sources]

            # Compute metrics
            prec = RAGEvaluationMetrics.retrieval_precision_at_k(retrieved_doc_names, exp_sources)
            rec = RAGEvaluationMetrics.retrieval_recall_at_k(retrieved_doc_names, exp_sources)
            ctx_rel = RAGEvaluationMetrics.context_relevance(q_text, retrieved_contexts)
            faith = RAGEvaluationMetrics.answer_faithfulness(generated_answer, retrieved_contexts)
            ans_rel = RAGEvaluationMetrics.answer_relevance(generated_answer, exp_answer, q_text)

            total_p += prec
            total_r += rec
            total_cr += ctx_rel
            total_faith += faith
            total_ans_rel += ans_rel
            total_lat += latency_ms

            results.append({
                "id": qid,
                "question": q_text,
                "expected_sources": exp_sources,
                "retrieved_sources": retrieved_doc_names,
                "generated_answer": generated_answer,
                "expected_answer": exp_answer,
                "precision_at_k": prec,
                "recall_at_k": rec,
                "context_relevance": ctx_rel,
                "faithfulness": faith,
                "answer_relevance": ans_rel,
                "latency_ms": round(latency_ms, 2),
                "insufficient_context": response.get("insufficient_context", False)
            })

        n = len(questions)
        summary = {
            "total_questions": n,
            "avg_precision_at_k": round(total_p / n, 4),
            "avg_recall_at_k": round(total_r / n, 4),
            "avg_context_relevance": round(total_cr / n, 4),
            "avg_faithfulness": round(total_faith / n, 4),
            "avg_answer_relevance": round(total_ans_rel / n, 4),
            "avg_latency_ms": round(total_lat / n, 2),
            "questions_evaluated": results
        }

        # Save to DB
        db = SessionLocal()
        try:
            repo = EvaluationRepository(db)
            repo.save_run(
                total_questions=n,
                precision=summary["avg_precision_at_k"],
                recall=summary["avg_recall_at_k"],
                context_relevance=summary["avg_context_relevance"],
                faithfulness=summary["avg_faithfulness"],
                answer_relevance=summary["avg_answer_relevance"],
                avg_latency_ms=summary["avg_latency_ms"],
                details=results
            )
        finally:
            db.close()

        logger.info(f"RAG Evaluation completed: Avg Precision={summary['avg_precision_at_k']}, Avg Faithfulness={summary['avg_faithfulness']}")
        return summary
