"""Text normalisation helpers used before parsing."""
import re
import unicodedata

BULLET_CHARS = "•●▪■◦○➢➤✓✔►‣∙·"


def clean_text(text: str) -> str:
    """Normalise unicode, bullets and whitespace while keeping line structure."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    for ch in BULLET_CHARS:
        text = text.replace(ch, "- ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text or ""))


def chunk_text(text: str, size: int = 90, overlap: int = 20) -> list[str]:
    """Split text into overlapping word chunks for embedding / RAG."""
    words = (text or "").split()
    if not words:
        return []
    chunks, step = [], max(1, size - overlap)
    for start in range(0, len(words), step):
        piece = " ".join(words[start:start + size])
        if piece:
            chunks.append(piece)
        if start + size >= len(words):
            break
    return chunks
