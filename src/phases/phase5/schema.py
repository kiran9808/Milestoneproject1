"""Stable public JSON contract for Phase 5."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .constants import PHASE5_AI_EXPLANATION_DISCLAIMER


class SelectionMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    had_strict_match: bool
    relaxation_steps_applied: list[str] = Field(default_factory=list)
    cross_location_fallback: bool = False
    expanded_from_location: str | None = None


class RecommendationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    location: str | None = None
    cuisines: list[str]
    rating: float | None = None
    cost: float | None = None
    explanation: str
    rank: int = Field(ge=1)
    relevance_score: float | None = None


class RankedRecommendationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    items: list[RecommendationItem]
    disclaimer: str = Field(default=PHASE5_AI_EXPLANATION_DISCLAIMER)
    used_llm_fallback: bool = False
    selection: SelectionMeta | None = None
    idempotency_key: str | None = None
