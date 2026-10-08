"""Shared helpers: logging, errors, JSON loading."""
import json
import logging
from functools import lru_cache
from pathlib import Path

from backend.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class AppError(Exception):
    """Error with a friendly message that is safe to show to end users."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@lru_cache(maxsize=8)
def load_json(filename: str):
    with open(Path(settings.data_dir) / filename, encoding="utf-8") as fh:
        return json.load(fh)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
