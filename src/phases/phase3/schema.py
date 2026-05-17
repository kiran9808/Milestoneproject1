"""Result types for candidate selection (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.phases.phase1 import RestaurantRecord, SearchFilters


@dataclass(slots=True)
class CandidateSelectionResult:
    """Structured outcome including relaxation trace for empty/sparse handling."""

    candidates: list[RestaurantRecord]
    filters_used: SearchFilters
    relaxation_steps_applied: list[str] = field(default_factory=list)
    had_strict_match: bool = field(default=True)
    cross_location_fallback: bool = field(default=False)
    expanded_from_location: str | None = field(default=None)
