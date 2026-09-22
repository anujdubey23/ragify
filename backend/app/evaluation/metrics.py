import re
from typing import List, Dict, Any, Set

class RAGEvaluationMetrics:
    """
    Evaluation metrics for evaluating RAG retrieval and generation quality:
    1. Retrieval Precision@K
    2. Retrieval Recall@K
    3. Context Relevance
    4. Answer Faithfulness (Groundedness)
    5. Answer Relevance
    """

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Lowercases and extracts alphanumeric word tokens."""
        return set(re.findall(r"\w+", text.lower()))

    @classmethod
    def retrieval_precision_at_k(cls, retrieved_sources: List[str], expected_sources: List[str]) -> float:
        """
        Precision@K = (Retrieved documents that are in Expected Sources) / (Total Retrieved Documents)
        """
        if not retrieved_sources:
            return 0.0
        if not expected_sources:
            return 1.0

        expected_set = {s.lower().strip() for s in expected_sources}
        hits = sum(1 for src in retrieved_sources if src.lower().strip() in expected_set)
        return round(hits / len(retrieved_sources), 4)

    @classmethod
    def retrieval_recall_at_k(cls, retrieved_sources: List[str], expected_sources: List[str]) -> float:
        """
        Recall@K = (Expected sources found in Retrieved documents) / (Total Expected Sources)
        """
        if not expected_sources:
            return 1.0
        if not retrieved_sources:
            return 0.0

        retrieved_set = {s.lower().strip() for s in retrieved_sources}
        hits = sum(1 for exp in expected_sources if exp.lower().strip() in retrieved_set)
        return round(hits / len(expected_sources), 4)

    @classmethod
    def context_relevance(cls, query: str, retrieved_contexts: List[str]) -> float:
        """
        Calculates lexical token overlap / Jaccard similarity between query terms
        and the retrieved context chunks.
        """
        query_tokens = cls._tokenize(query)
        if not query_tokens:
            return 0.0

        combined_context = " ".join(retrieved_contexts)
        context_tokens = cls._tokenize(combined_context)

        if not context_tokens:
            return 0.0

        # Overlap ratio of query tokens present in context
        intersection = query_tokens.intersection(context_tokens)
        overlap_score = len(intersection) / len(query_tokens)
        return round(float(overlap_score), 4)

    @classmethod
    def answer_faithfulness(cls, answer: str, retrieved_contexts: List[str]) -> float:
        """
        Measures the groundedness of the generated answer against retrieved context.
        Computes the ratio of non-trivial answer sentences supported by context tokens.
        """
        if not answer or not retrieved_contexts:
            return 0.0

        combined_context = " ".join(retrieved_contexts).lower()
        context_tokens = cls._tokenize(combined_context)

        # Split answer into sentences
        sentences = [s.strip() for s in re.split(r"[.!?\n]", answer) if len(s.strip()) > 15]
        if not sentences:
            return 1.0

        supported_sentences = 0
        for sent in sentences:
            sent_tokens = cls._tokenize(sent)
            # Filter out common stop words to focus on content words
            content_tokens = {t for t in sent_tokens if len(t) > 3}
            if not content_tokens:
                supported_sentences += 1
                continue

            matches = sum(1 for t in content_tokens if t in context_tokens)
            if (matches / len(content_tokens)) >= 0.5:
                supported_sentences += 1

        faithfulness = supported_sentences / len(sentences)
        return round(float(faithfulness), 4)

    @classmethod
    def answer_relevance(cls, answer: str, expected_answer: str, query: str) -> float:
        """
        Computes relevance of generated answer to question and expected reference answer.
        Uses token overlap / Jaccard index.
        """
        if not answer:
            return 0.0

        ans_tokens = cls._tokenize(answer)
        if not ans_tokens:
            return 0.0

        if expected_answer:
            target_tokens = cls._tokenize(expected_answer)
        else:
            target_tokens = cls._tokenize(query)

        if not target_tokens:
            return 1.0

        intersection = ans_tokens.intersection(target_tokens)
        union = ans_tokens.union(target_tokens)

        jaccard = len(intersection) / len(union) if union else 0.0
        # Scale appropriately since Jaccard between generated & reference is typically in [0.2, 0.7]
        normalized = min(1.0, jaccard * 2.0)
        return round(float(normalized), 4)
