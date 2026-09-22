import asyncio
import sys
import json
from backend.app.evaluation.evaluator import RAGEvaluator
from backend.app.database.database import init_db

async def main():
    print("=" * 60)
    print("      RAGify — Automated RAG Quality Evaluation Benchmark     ")
    print("=" * 60)

    init_db()
    evaluator = RAGEvaluator()

    try:
        results = await evaluator.run_evaluation()
    except Exception as e:
        print(f"Evaluation failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("                 BENCHMARK SUMMARY METRICS                 ")
    print("=" * 60)
    print(f" Total Questions Evaluated : {results['total_questions']}")
    print(f" Retrieval Precision@K     : {results['avg_precision_at_k'] * 100:.1f}%")
    print(f" Retrieval Recall@K        : {results['avg_recall_at_k'] * 100:.1f}%")
    print(f" Context Relevance Score   : {results['avg_context_relevance'] * 100:.1f}%")
    print(f" Answer Faithfulness       : {results['avg_faithfulness'] * 100:.1f}%")
    print(f" Answer Relevance Score    : {results['avg_answer_relevance'] * 100:.1f}%")
    print(f" Average Latency           : {results['avg_latency_ms']:.2f} ms")
    print("=" * 60)

    print("\nPer-Question Breakdown:")
    for q in results["questions_evaluated"]:
        print(f"\n[Q: {q['question']}]")
        print(f"  - Precision: {q['precision_at_k'] * 100:.1f}% | Recall: {q['recall_at_k'] * 100:.1f}% | Faithfulness: {q['faithfulness'] * 100:.1f}% | Latency: {q['latency_ms']}ms")
        print(f"  - Sources Retrieved: {', '.join(q['retrieved_sources']) if q['retrieved_sources'] else 'None'}")
        print(f"  - Generated Answer: {q['generated_answer'][:140]}...")

    print("\nBenchmark run completed and persisted to SQLite.")

if __name__ == "__main__":
    asyncio.run(main())
