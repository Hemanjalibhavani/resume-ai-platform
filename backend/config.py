"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Central settings object. Secrets only ever come from the environment."""

    app_name: str = "AI-Powered Resume Screening & Job Matching System"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./resume_ai.db")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "vector_store"))
    upload_dir: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "5"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    # auto | sentence-transformers | tfidf
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "auto")
    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    frontend_dir: str = str(BASE_DIR / "frontend")
    data_dir: str = str(BASE_DIR / "backend" / "data")


settings = Settings()
