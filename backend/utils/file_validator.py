"""Upload validation: extension, size, emptiness and magic bytes."""
import re
from pathlib import Path

from backend.config import settings
from backend.utils.helpers import AppError

ALLOWED_RESUME = {".pdf", ".docx"}
ALLOWED_JD = {".pdf", ".docx", ".txt"}


def sanitize_filename(name: str) -> str:
    """Strip any path component and unsafe characters from an uploaded filename."""
    base = Path(name or "upload").name
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .") or "upload"
    return base[:120]


def validate_upload(filename: str, data: bytes, allowed: set[str] = ALLOWED_RESUME) -> str:
    """Validate an upload and return the sanitized filename."""
    clean = sanitize_filename(filename)
    ext = Path(clean).suffix.lower()
    if ext not in allowed:
        kind = "PDF or DOCX" if allowed == ALLOWED_RESUME else "PDF, DOCX or TXT"
        raise AppError(f"Please upload a valid {kind} file.", 400)
    if not data:
        raise AppError("The uploaded file is empty.", 400)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise AppError(f"File is too large. Maximum size is {settings.max_upload_mb} MB.", 413)
    if ext == ".pdf" and not data.lstrip()[:5].startswith(b"%PDF"):
        raise AppError("Please upload a valid PDF resume.", 400)
    if ext == ".docx" and not data.startswith(b"PK"):
        raise AppError("Please upload a valid DOCX file.", 400)
    return clean
