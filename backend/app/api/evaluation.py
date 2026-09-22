import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.database.repository import EvaluationRepository
from backend.app.evaluation.evaluator import RAGEvaluator
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])

class EvaluationQuestion(BaseModel):
    id: Optional[str] = None
    question: str
    expected_sources: List[str] = []
    expected_answer: Optional[str] = ""

class CustomEvaluationRequest(BaseModel):
    questions: Optional[List[EvaluationQuestion]] = None

@router.post("")
async def run_evaluation(request: Optional[CustomEvaluationRequest] = None):
    """
    Executes RAG evaluation benchmark across standardized test questions.
    Computes Precision, Recall, Context Relevance, Faithfulness, Answer Relevance, and Latency.
    """
    evaluator = RAGEvaluator()
    custom_qs = None
    if request and request.questions:
        custom_qs = [q.model_dump() for q in request.questions]

    try:
        report = await evaluator.run_evaluation(custom_questions=custom_qs)
        return report
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.get("/history")
def get_evaluation_history(limit: int = 10, db: Session = Depends(get_db)):
    """Retrieves previous evaluation run history."""
    repo = EvaluationRepository(db)
    runs = repo.get_runs(limit=limit)
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "total_questions": r.total_questions,
            "precision_at_k": r.precision_at_k,
            "recall_at_k": r.recall_at_k,
            "context_relevance": r.context_relevance,
            "faithfulness": r.faithfulness,
            "answer_relevance": r.answer_relevance,
            "avg_latency_ms": r.avg_latency_ms,
            "details": json.loads(r.details_json) if r.details_json else []
        }
        for r in runs
    ]

@router.get("/dataset")
def get_evaluation_dataset():
    """Returns the benchmark test dataset."""
    evaluator = RAGEvaluator()
    return evaluator.load_dataset()
