from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.rag.text_cleaner import TextCleaner
from backend.app.utils.logging import logger

class RecursiveCharacterChunker:
    """
    Splits text recursively using hierarchical separators to preserve semantic context.

    Why Chunk Size & Overlap Matter in RAG:
    --------------------------------------
    1. Chunk Size:
       - Too small (e.g. 100 chars): Lacks sufficient context, fragments sentences,
         dilutes embedding semantic meaning.
       - Too large (e.g. 5000 chars): Surpasses attention limits, averages out distinct
         topics in embeddings, and overflows LLM context budget with irrelevant noise.
       - Optimal (e.g. 500-1000 chars / ~120-250 tokens): Self-contained semantic paragraph
         ideal for bi-encoder embeddings and accurate keyword matching.

    2. Chunk Overlap:
       - Preserves contextual continuity across split boundaries.
       - Prevents splitting a critical fact, name, equation, or definition across two chunks
         where neither chunk has sufficient standalone context to answer a query.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or self.DEFAULT_SEPARATORS

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be strictly less than chunk_size ({self.chunk_size})"
            )

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursive splitting based on separator hierarchy."""
        final_chunks = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        for s in splits:
            if separator and s:
                # Add separator back except when empty separator
                piece = s if separator == "\n\n" or separator == "\n" else s + separator
            else:
                piece = s
            if piece:
                good_splits.append(piece)

        # Merge splits respecting chunk_size and chunk_overlap
        current_doc = []
        total_len = 0

        for split in good_splits:
            split_len = len(split)
            if total_len + split_len > self.chunk_size:
                if total_len > 0:
                    joined = "".join(current_doc).strip()
                    if joined:
                        final_chunks.append(joined)

                    # Keep tail of current_doc for overlap
                    while total_len > self.chunk_overlap and current_doc:
                        popped = current_doc.pop(0)
                        total_len -= len(popped)

                if split_len > self.chunk_size and new_separators:
                    # Recursive split for pieces still exceeding chunk_size
                    sub_chunks = self._split_text(split, new_separators)
                    final_chunks.extend(sub_chunks)
                    current_doc = []
                    total_len = 0
                else:
                    current_doc.append(split)
                    total_len += split_len
            else:
                current_doc.append(split)
                total_len += split_len

        if current_doc:
            joined = "".join(current_doc).strip()
            if joined:
                final_chunks.append(joined)

        return final_chunks

    def chunk_document_pages(
        self,
        pages: List[Dict[str, Any]],
        document_id: str,
        document_name: str
    ) -> List[Dict[str, Any]]:
        """
        Chunks multiple pages of a document while strictly preserving page numbers.
        Returns chunk records ready for vector storage and database insertion.
        """
        chunks = []
        chunk_idx = 0

        for page_data in pages:
            raw_text = page_data.get("text", "")
            cleaned_text = TextCleaner.clean(raw_text)
            page_num = page_data.get("page_number")
            source = page_data.get("source", document_name)

            if not cleaned_text:
                continue

            raw_chunks = self._split_text(cleaned_text, self.separators)

            for text_chunk in raw_chunks:
                text_chunk = text_chunk.strip()
                if not text_chunk:
                    continue

                chunk_id = f"{document_id}_{chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": page_num,
                    "chunk_index": chunk_idx,
                    "text": text_chunk,
                    "source": source,
                    "metadata": {
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": page_num,
                        "chunk_index": chunk_idx,
                        "char_count": len(text_chunk)
                    }
                })
                chunk_idx += 1

        logger.info(f"Generated {len(chunks)} chunks for document '{document_name}' ({document_id})")
        return chunks
