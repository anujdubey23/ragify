import os
import time
import httpx
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.rag.prompt_builder import PromptBuilder
from backend.app.utils.logging import logger, log_latency

INSUFFICIENT_CONTEXT_MESSAGE = (
    "I couldn't find enough relevant information in the uploaded documents to answer this question accurately."
)

class LLMGenerator:
    """
    LLM generator supporting OpenAI, Groq, Gemini, and offline deterministic fallback.
    Enforces anti-hallucination confidence thresholding and source citation formatting.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def generate_response(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        confidence_threshold: Optional[float] = None,
        model_override: Optional[str] = None,
        temp_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded answer and citation metadata.
        """
        threshold = confidence_threshold if confidence_threshold is not None else settings.CONFIDENCE_THRESHOLD
        model = model_override or self.model
        temperature = temp_override if temp_override is not None else self.temperature

        # 1. Anti-Hallucination Confidence Check
        if not retrieved_chunks:
            return {
                "answer": INSUFFICIENT_CONTEXT_MESSAGE,
                "sources": [],
                "confidence": 0.0,
                "insufficient_context": True
            }

        max_score = max((chunk.get("score", 0.0) for chunk in retrieved_chunks), default=0.0)
        if max_score < threshold:
            logger.info(f"Retrieval confidence ({max_score:.3f}) below threshold ({threshold:.3f}). Rejecting generation.")
            return {
                "answer": INSUFFICIENT_CONTEXT_MESSAGE,
                "sources": self._format_sources(retrieved_chunks),
                "confidence": max_score,
                "insufficient_context": True
            }

        # 2. Build Structured Context Prompt
        messages = PromptBuilder.build_prompt(question, retrieved_chunks, chat_history)

        # 3. Invoke LLM Provider
        start_time = time.perf_counter()
        answer = await self._call_llm(messages, model=model, temperature=temperature, context_chunks=retrieved_chunks, question=question)
        generation_latency_ms = (time.perf_counter() - start_time) * 1000

        # 4. Format Sources
        sources = self._format_sources(retrieved_chunks)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": max_score,
            "insufficient_context": False,
            "generation_latency_ms": generation_latency_ms
        }

    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extracts structured source citations without duplicates."""
        seen_keys = set()
        sources = []

        for chunk in chunks:
            doc_name = chunk.get("document_name") or chunk.get("source", "Document")
            page = chunk.get("page_number")
            cid = chunk.get("chunk_id", "")
            score = chunk.get("score", 0.0)
            text = chunk.get("text", "")

            # Dedup key
            dedup_key = f"{doc_name}_{page}_{cid}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            # Preview snippet (first 180 chars)
            preview = (text[:180] + "...") if len(text) > 180 else text

            sources.append({
                "document": doc_name,
                "page": page,
                "chunk_id": cid,
                "score": round(float(score), 4),
                "preview": preview,
                "full_text": text
            })

        return sources

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        context_chunks: List[Dict[str, Any]],
        question: str
    ) -> str:
        """Dispatches LLM call according to configured provider."""
        provider = self.provider

        # Check if user configured Groq / OpenAI
        if provider in ["openai", "groq"]:
            return await self._call_openai_compatible(messages, model, temperature, provider)
        elif provider == "gemini":
            return await self._call_gemini(messages, model, temperature)
        else:
            # Fallback offline generator that deterministically synthesizes context
            return self._offline_grounded_synthesis(context_chunks, question)

    async def _call_openai_compatible(self, messages: List[Dict[str, str]], model: str, temperature: float, provider: str) -> str:
        """Calls OpenAI or Groq API."""
        api_key = self.api_key or os.getenv("LLM_API_KEY", "")
        if not api_key:
            logger.warning(f"No API key provided for {provider}. Falling back to grounded context synthesis.")
            return self._offline_grounded_synthesis(messages, "")

        base_url = settings.LLM_API_BASE
        if not base_url:
            base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://api.openai.com/v1"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling {provider} API: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"{provider} API returned error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                logger.error(f"Error communicating with {provider} API: {str(e)}")
                raise

    async def _call_gemini(self, messages: List[Dict[str, str]], model: str, temperature: float) -> str:
        """Calls Google Gemini API."""
        api_key = self.api_key or os.getenv("LLM_API_KEY", "")
        if not api_key:
            logger.warning("No API key provided for Gemini. Falling back to grounded context synthesis.")
            return self._offline_grounded_synthesis(messages, "")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # Convert OpenAI-style messages to Gemini contents
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": self.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.error(f"Error calling Gemini API: {str(e)}")
                raise

    def _offline_grounded_synthesis(self, context_chunks_or_messages: Any, question: str) -> str:
        """
        Deterministic, offline extraction that synthesizes factual points
        directly from retrieved chunks. Ensures that even without an external API key,
        the system operates as a real RAG engine without crashing or hallucinating.
        """
        if isinstance(context_chunks_or_messages, list) and len(context_chunks_or_messages) > 0 and isinstance(context_chunks_or_messages[0], dict):
            chunks = context_chunks_or_messages
        else:
            chunks = []

        if not chunks:
            return INSUFFICIENT_CONTEXT_MESSAGE

        # Group key findings by source document & page
        findings = []
        citations = []

        for idx, chunk in enumerate(chunks[:3], start=1):
            text = chunk.get("text", "").strip()
            doc_name = chunk.get("document_name") or chunk.get("source", "Document")
            page_num = chunk.get("page_number")
            page_str = f"Page {page_num}" if page_num is not None else "Page N/A"

            # Take the most informative sentences
            sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s.strip()) > 20]
            top_sentences = sentences[:2] if sentences else [text[:200]]

            findings.append(" ".join(top_sentences))
            citations.append(f"📄 **{doc_name}** ({page_str})")

        combined_findings = " ".join(findings)
        unique_citations = list(dict.fromkeys(citations))

        return (
            f"Based on the uploaded documents, here is the verified information:\n\n"
            f"{combined_findings}\n\n"
            f"**Sources Consulted:**\n" + "\n".join(f"- {c}" for c in unique_citations)
        )
