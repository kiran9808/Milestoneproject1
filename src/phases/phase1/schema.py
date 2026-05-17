"""Canonical restaurant model and search filters for Phase 1 serving."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RestaurantRecord:
    """Internal schema aligned with Miletone1_PhaseWise_Architecture Phase 1."""

    id: str
    name: str
    location: str
    cuisines: tuple[str, ...]
    cost_for_two: float | None
    aggregate_rating: float | None
    votes: int | None = None
    establishment_type: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "cuisines": list(self.cuisines),
            "cost_for_two": self.cost_for_two,
            "aggregate_rating": self.aggregate_rating,
            "votes": self.votes,
            "establishment_type": self.establishment_type,
            "extras": dict(self.extras),
        }


def venue_identity_key(record: RestaurantRecord) -> tuple[str, str]:
    """
    Stable key for deduplicating rows that describe the same real-world venue.

    The Hugging Face table often repeats the same name + area with separate rows / ids.
    """
    name = record.name.strip().casefold() if record.name else ""
    location = record.location.strip().casefold() if record.location else ""
    return (name, location)


@dataclass(slots=True)
class SearchFilters:
    """Read path for integration layer; Phase 3 may extend this."""

    location: str | None = None
    """Exact area/city match. ``None`` or blank skips this predicate (search any location)."""

    exclude_location: str | None = None
    """If set, exclude this area (used with broad search to show *other* locations)."""

    min_rating: float = 0.0
    cuisine: str | None = None
    max_cost_for_two: float | None = None
    min_cost_for_two: float | None = None
    limit: int = 100


@dataclass
class DatasetVersionInfo:
    """Written alongside ingest for reproducibility."""

    dataset_name: str
    revision: str | None
    ingested_at: str
    row_count: int
    split: str
