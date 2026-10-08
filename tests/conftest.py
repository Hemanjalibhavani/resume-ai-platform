import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["VECTOR_DB_PATH"] = f"{_tmp}/vectors"
os.environ["EMBEDDING_BACKEND"] = "tfidf"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


SAMPLE = (Path(__file__).resolve().parent.parent / "backend" / "data" / "sample_resume.txt").read_text(encoding="utf-8")
