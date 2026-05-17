"""Phase 3 integration: pool size, final truncation, and prompt/safety limits."""

from __future__ import annotations

# Fetch a larger pool from Phase 1, then truncate to ``top_k`` after sorting (same order as SQL).
DEFAULT_FETCH_LIMIT: int = 150

# Final candidates passed to the LLM prompt (architecture: 50–100 typical).
DEFAULT_TOP_K: int = 50

# After sanitization, hard cap on additional_preferences embedded in prompts.
MAX_PREFERENCES_PROMPT_CHARS: int = 1500
