import os
import re
from fastapi import HTTPException, UploadFile
from backend.app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "application/octet-stream": None  # Will rely on extension check
}

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename by stripping directory paths and keeping only safe characters.
    Prevents path traversal attacks (e.g. ../../../etc/passwd).
    """
    base_name = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dot, dash, underscore
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    # Avoid hidden files or double dots
    sanitized = re.sub(r"\.{2,}", ".", sanitized).lstrip(".")
    if not sanitized:
        sanitized = "unnamed_document"
    return sanitized

def validate_uploaded_file(file: UploadFile, content: bytes) -> str:
    """
    Validates uploaded file extension, size, and content.
    Returns sanitized filename.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    sanitized = sanitize_filename(file.filename)
    ext = os.path.splitext(sanitized)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Size check
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed size of {max_mb:.0f} MB."
        )

    return sanitized
