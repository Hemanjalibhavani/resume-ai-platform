"""Optional LLM access (Gemini or OpenAI) via REST. Never required: callers fall back to local logic."""
import httpx

from backend.config import settings
from backend.utils.helpers import get_logger

log = get_logger(__name__)


def provider() -> str:
    if settings.gemini_api_key:
        return "gemini"
    if settings.openai_api_key:
        return "openai"
    return "none"


def is_available() -> bool:
    return provider() != "none"


def mode() -> str:
    return "llm" if is_available() else "local"


def generate(prompt: str, system: str = "You are a helpful career assistant.", timeout: float = 30.0) -> str | None:
    """Return model text, or None if no key is configured or the call fails."""
    try:
        if settings.gemini_api_key:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent")
            r = httpx.post(url, params={"key": settings.gemini_api_key}, timeout=timeout,
                           json={"system_instruction": {"parts": [{"text": system}]},
                                 "contents": [{"parts": [{"text": prompt}]}]})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if settings.openai_api_key:
            r = httpx.post("https://api.openai.com/v1/chat/completions", timeout=timeout,
                           headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                           json={"model": settings.openai_model,
                                 "messages": [{"role": "system", "content": system},
                                              {"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # network, quota, bad key ...
        log.warning("LLM call failed, using local mode: %s", exc)
    return None
