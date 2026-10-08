"""Dictionary + regex skill extraction with alias and 'partial skill' support."""
import re
from functools import lru_cache

from backend.utils.helpers import load_json


@lru_cache(maxsize=1)
def _catalog() -> dict:
    return load_json("skills.json")["skills"]


@lru_cache(maxsize=1)
def _patterns() -> dict[str, re.Pattern]:
    """Compile one boundary-aware regex per skill (handles c++, c#, node.js, ci/cd)."""
    out = {}
    for name, meta in _catalog().items():
        terms = list(meta.get("aliases", []))
        if not meta.get("strict"):
            terms.append(name)
        alt = "|".join(re.escape(t) for t in sorted(set(terms), key=len, reverse=True))
        out[name] = re.compile(rf"(?<![\w+#./-])(?:{alt})(?![\w+#]|\.\w)", re.IGNORECASE)
    return out


def display_name(skill: str) -> str:
    """Pretty label for a canonical skill key."""
    special = {"aws": "AWS", "gcp": "GCP", "nlp": "NLP", "llm": "LLM", "rag": "RAG", "sql": "SQL",
               "html": "HTML", "css": "CSS", "oop": "OOP", "etl": "ETL", "ci/cd": "CI/CD", "mlops": "MLOps",
               "fastapi": "FastAPI", "mysql": "MySQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB",
               "sqlite": "SQLite", "xgboost": "XGBoost", "opencv": "OpenCV", "faiss": "FAISS",
               "chromadb": "ChromaDB", "github": "GitHub", "javascript": "JavaScript", "typescript": "TypeScript",
               "pytorch": "PyTorch", "tensorflow": "TensorFlow", "rest api": "REST API", "node.js": "Node.js",
               "langchain": "LangChain", "sqlalchemy": "SQLAlchemy", "power bi": "Power BI", "go": "Go",
               "r": "R", "c++": "C++", "c#": "C#", "php": "PHP", "scikit-learn": "scikit-learn", "kafka": "Kafka"}
    return special.get(skill, skill.title() if " " in skill else skill.capitalize())


def extract_skills(text: str) -> dict[str, dict]:
    """Return {skill: {category, mentions}} for every catalog skill found in text."""
    found: dict[str, dict] = {}
    if not text:
        return found
    for name, pat in _patterns().items():
        hits = pat.findall(text)
        if hits:
            found[name] = {"category": _catalog()[name]["category"], "mentions": len(hits)}
    return found


def is_basic_level(text: str, skill: str) -> bool:
    """True when the text only claims basic knowledge, e.g. 'Java basics'."""
    meta = _catalog().get(skill, {})
    terms = [skill] + list(meta.get("aliases", []))
    for term in terms:
        t = re.escape(term)
        if re.search(rf"(basics?\s+(of\s+|in\s+)?{t}|basic\s+{t}|{t}\s*(\(\s*basics?\s*\)|basics?\b))", text, re.I):
            return True
    return False


def related_skills(skill: str) -> list[str]:
    return _catalog().get(skill, {}).get("related", [])


def category_of(skill: str) -> str:
    return _catalog().get(skill, {}).get("category", "other")


SOFT_PATTERNS = {
    "communication": [r"communicat", r"presentation", r"presented", r"presenting"],
    "teamwork": [r"team ?work", r"team player", r"collaborat", r"worked (?:in|with) a team", r"with a team"],
    "leadership": [r"leadership", r"\bled\b", r"team lead", r"mentor"],
    "problem solving": [r"problem[- ]solving"],
    "critical thinking": [r"critical thinking"],
    "time management": [r"time management", r"within \d+ hours", r"deadline"],
    "adaptability": [r"adaptab", r"quick learner", r"fast learner"],
    "creativity": [r"creativ", r"innovati"],
    "analytical": [r"analytical", r"analytic skills"],
    "ownership": [r"ownership", r"end-to-end"],
}


def extract_soft_skills(text: str) -> list[str]:
    """Canonical soft skills found in text (stem patterns, e.g. 'collaborated' -> teamwork)."""
    low = (text or "").lower()
    return sorted(k for k, pats in SOFT_PATTERNS.items() if any(re.search(p, low) for p in pats))
