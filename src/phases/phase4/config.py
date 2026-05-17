"""Groq / environment configuration for Phase 4."""

from __future__ import annotations

import os
from pathlib import Path

# Repository root: src/phases/phase4/config.py -> parents[3]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

GROQ_OPENAI_BASE_URL: str = "https://api.groq.com/openai/v1"
ENV_GROQ_API_KEY: str = "GROQ_API_KEY"
ENV_GROQ_MODEL: str = "GROQ_MODEL"
ENV_GROQ_BASE_URL: str = "GROQ_BASE_URL"

# Default Groq model (override via .env); small/fast tier suitable for v1.
DEFAULT_GROQ_MODEL: str = "llama-3.1-8b-instant"

MAX_COMPLETION_RETRIES: int = 3
RETRY_BACKOFF_SEC: float = 1.0
