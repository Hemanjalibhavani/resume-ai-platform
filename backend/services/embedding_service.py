"""Semantic similarity: sentence-transformers (+FAISS) when available, TF-IDF cosine fallback."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import settings
from backend.utils.helpers import get_logger
from backend.utils.text_cleaner import chunk_text

log = get_logger(__name__)


class EmbeddingService:
    """Lazy-loading embedding backend with graceful fallback so the app always starts."""

    def __init__(self) -> None:
        self.backend: str | None = None
        self.model = None

    def _load(self) -> None:
        if self.backend:
            return
        if settings.embedding_backend in ("auto", "sentence-transformers"):
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(settings.embedding_model)
                self.backend = "sentence-transformers"
                log.info("Embedding backend: sentence-transformers")
                return
            except Exception as exc:
                log.warning("sentence-transformers unavailable (%s); using TF-IDF fallback", exc)
        self.backend = "tfidf"

    @property
    def name(self) -> str:
        self._load()
        return self.backend or "tfidf"

    @property
    def calibration(self) -> float:
        """Raw cosine value considered a 'full' match (embeddings and TF-IDF scale differently)."""
        return 0.65 if self.name == "sentence-transformers" else 0.18

    def _embed_long(self, text: str) -> np.ndarray:
        chunks = chunk_text(text, size=150, overlap=20) or [text or " "]
        vecs = self.model.encode(chunks, normalize_embeddings=True)
        mean = vecs.mean(axis=0)
        return mean / (np.linalg.norm(mean) or 1.0)

    def similarity(self, a: str, b: str) -> float:
        """Cosine similarity of two texts in [0, 1]."""
        if not (a or "").strip() or not (b or "").strip():
            return 0.0
        self._load()
        if self.backend == "sentence-transformers":
            return float(max(0.0, np.dot(self._embed_long(a), self._embed_long(b))))
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        try:
            m = vec.fit_transform([a, b])
        except ValueError:
            return 0.0
        return float(cosine_similarity(m[0], m[1])[0][0])

    def rank(self, query: str, docs: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Return [(doc_index, score)] sorted by similarity to the query (semantic search)."""
        if not docs or not (query or "").strip():
            return []
        self._load()
        if self.backend == "sentence-transformers":
            doc_vecs = self.model.encode(docs, normalize_embeddings=True).astype("float32")
            q = self.model.encode([query], normalize_embeddings=True).astype("float32")
            try:  # FAISS inner-product index == cosine for normalised vectors
                import faiss

                index = faiss.IndexFlatIP(doc_vecs.shape[1])
                index.add(doc_vecs)
                scores, ids = index.search(q, min(top_k, len(docs)))
                return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
            except ImportError:
                sims = (doc_vecs @ q.T).ravel()
        else:
            try:
                vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
                m = vec.fit_transform(docs + [query])
                sims = cosine_similarity(m[-1], m[:-1]).ravel()
            except ValueError:
                return []
        order = np.argsort(-sims)[:top_k]
        return [(int(i), float(sims[i])) for i in order]


embedding_service = EmbeddingService()
