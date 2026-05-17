"""Phase 4 — Groq recommendation engine (OpenAI-compatible API)."""

from .config import (
    DEFAULT_GROQ_MODEL,
    ENV_GROQ_API_KEY,
    ENV_GROQ_BASE_URL,
    ENV_GROQ_MODEL,
    GROQ_OPENAI_BASE_URL,
)
from .engine import GroqRecommendationEngine, rank_and_explain
from .enrich import enrich_ranked_with_candidates, to_phase5_payload
from .env import load_project_dotenv, project_root
from .fallback import deterministic_rank_and_explain
from .parse import parse_ranked_json
from .schema import LLMUserContext, RankedEntry, RankedRecommendations

__all__ = [
    "DEFAULT_GROQ_MODEL",
    "ENV_GROQ_API_KEY",
    "ENV_GROQ_BASE_URL",
    "ENV_GROQ_MODEL",
    "GROQ_OPENAI_BASE_URL",
    "GroqRecommendationEngine",
    "LLMUserContext",
    "RankedEntry",
    "RankedRecommendations",
    "deterministic_rank_and_explain",
    "enrich_ranked_with_candidates",
    "load_project_dotenv",
    "parse_ranked_json",
    "project_root",
    "rank_and_explain",
    "to_phase5_payload",
]
