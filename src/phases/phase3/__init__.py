"""Phase 3 — integration: filter, relaxation, prompt assembly, safety."""

from .config import DEFAULT_FETCH_LIMIT, DEFAULT_TOP_K, MAX_PREFERENCES_PROMPT_CHARS
from .integration import IntegrationService
from .prompt import build_prompt
from .schema import CandidateSelectionResult
from .selection import select_candidates, select_candidates_with_relaxation
from .safety import sanitize_preferences

__all__ = [
    "DEFAULT_FETCH_LIMIT",
    "DEFAULT_TOP_K",
    "MAX_PREFERENCES_PROMPT_CHARS",
    "CandidateSelectionResult",
    "IntegrationService",
    "build_prompt",
    "sanitize_preferences",
    "select_candidates",
    "select_candidates_with_relaxation",
]
