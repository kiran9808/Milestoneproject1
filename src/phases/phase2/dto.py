"""Validated boundary DTOs for Phase 2 (REST / CLI)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .config import (
    MAX_ADDITIONAL_PREFERENCES_LEN,
    MAX_BUDGET_AMOUNT_FOR_TWO,
    MAX_CUISINE_LEN,
    MAX_LOCATION_LEN,
    MAX_RATING,
    MIN_RATING,
)
from .location_normalize import normalize_location


class RecommendationRequest(BaseModel):
    """
    User preferences from Miletone1_PhaseWise_Architecture Phase 2.

    Maps to ``SearchFilters`` (Phase 1) plus ``additional_preferences`` for Phase 3 prompts.
    """

    location: str = Field(..., min_length=1, max_length=MAX_LOCATION_LEN)
    budget_amount: float = Field(
        ...,
        ge=0,
        le=MAX_BUDGET_AMOUNT_FOR_TWO,
        description=(
            "Maximum approximate cost for two (INR). Restaurants with cost above this are "
            "excluded. Use 0 to apply no upper cap."
        ),
    )
    cuisine: str | None = Field(default=None, max_length=MAX_CUISINE_LEN)
    min_rating: float = Field(default=0.0, ge=MIN_RATING, le=MAX_RATING)
    additional_preferences: str | None = Field(
        default=None,
        max_length=MAX_ADDITIONAL_PREFERENCES_LEN,
    )
    strict_cuisine: bool = Field(
        default=True,
        description=(
            "If true, candidate search never relaxes by dropping the cuisine filter "
            "(recommended for predictable matches)."
        ),
    )
    explore_other_locations: bool = Field(
        default=True,
        description=(
            "If true and cuisine is set, when no venues match the selected area the "
            "search may include the same cuisine in other areas."
        ),
    )

    @field_validator("location")
    @classmethod
    def strip_location(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("location cannot be blank")
        return normalize_location(t)

    @field_validator("cuisine")
    @classmethod
    def strip_cuisine(cls, v: str | None) -> str | None:
        if v is None:
            return None
        t = v.strip()
        return t or None

    @field_validator("additional_preferences")
    @classmethod
    def strip_prefs(cls, v: str | None) -> str | None:
        if v is None:
            return None
        t = v.strip()
        return t or None


class RecommendationResponse(BaseModel):
    """API response: echo validated request, optional idempotency key, structured candidates."""

    idempotency_key: str | None = None
    location: str
    budget_amount: float
    cuisine: str | None
    min_rating: float
    additional_preferences: str | None
    candidates: list[dict]
    candidate_count: int


class LocationsResponse(BaseModel):
    """Distinct restaurant area/city strings from the Phase 1 SQLite store."""

    locations: list[str]


class CuisinesResponse(BaseModel):
    """Distinct cuisine tags (one label per cuisine style) from the Phase 1 SQLite store."""

    cuisines: list[str]
