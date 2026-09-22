from typing import List, Dict, Any, Optional

SYSTEM_PROMPT = """You are a document-grounded AI assistant.

Answer the user's question using only the provided retrieved context.

Rules:
1. Do not invent information.
2. Do not use unsupported facts.
3. If the answer cannot be determined from the provided context, clearly state:
   'I could not find this information in the uploaded documents.'
4. Do not assume information that is not present.
5. Keep the answer concise but sufficiently detailed.
6. Cite the sources used for the answer by referencing their document name and page number.
7. If multiple documents support the answer, cite all relevant sources.
8. Never fabricate page numbers or document names."""

class PromptBuilder:
    """
    Constructs anti-hallucination prompts injecting retrieved chunks and conversational history.
    """

    @staticmethod
    def build_context_block(chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into structured context blocks for the LLM.
        """
        if not chunks:
            return "No relevant context found in documents."

        context_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            doc_name = chunk.get("document_name") or chunk.get("source", "Unknown Document")
            page_num = chunk.get("page_number")
            page_str = f"Page {page_num}" if page_num is not None else "No page number"
            chunk_id = chunk.get("chunk_id", f"chunk_{idx}")
            text = chunk.get("text", "").strip()

            context_parts.append(
                f"[Source {idx}]: Document: {doc_name} | {page_str} | ID: {chunk_id}\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def format_chat_history(messages: List[Dict[str, str]], max_turns: int = 6) -> List[Dict[str, str]]:
        """
        Extracts recent conversation turns and truncates to avoid context overflow.
        """
        if not messages:
            return []

        recent = messages[-max_turns:]
        formatted = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                formatted.append({"role": role, "content": content})
        return formatted

    @staticmethod
    def build_prompt(
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Constructs the final OpenAI/Chat-compatible messages payload.
        """
        context_text = PromptBuilder.build_context_block(retrieved_chunks)

        user_content = (
            f"Retrieved Document Context:\n"
            f"============================\n"
            f"{context_text}\n"
            f"============================\n\n"
            f"Question: {question}\n\n"
            f"Answer based only on the context above. Cite the source documents and page numbers where applicable."
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Inject truncated recent history before final query
        if chat_history:
            recent_turns = PromptBuilder.format_chat_history(chat_history)
            messages.extend(recent_turns)

        messages.append({"role": "user", "content": user_content})
        return messages
