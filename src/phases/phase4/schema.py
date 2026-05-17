"""Structured LLM output for Phase 4 (and handoff to Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RankedEntry:
    """One ranked restaurant from the LLM (or fallback)."""

    id: str
    rank: int
    explanation: str
    relevance_score: float | None = None


@dataclass(slots=True)
class LLMUserContext:
    """What ``rank_and_explain`` needs besides the candidate list (Phase 3 messages)."""

    messages: list[dict[str, str]]


@dataclass
class RankedRecommendations:
    """Result of ``rank_and_explain`` per architecture."""

    summary: str | None
    ranked: list[RankedEntry]
    used_llm_fallback: bool = False
    raw_model_content: str | None = field(default=None, repr=False)
