"""Merge LLM ranks with catalog rows (handoff to Phase 5-style payloads)."""

from __future__ import annotations

from typing import Any

from src.phases.phase1 import RestaurantRecord
from src.phases.phase1.schema import venue_identity_key

from .schema import RankedRecommendations


def enrich_ranked_with_candidates(
    ranked: RankedRecommendations,
    candidates: list[RestaurantRecord],
) -> list[dict[str, Any]]:
    """
    Join ``RankedRecommendations.ranked`` with ``RestaurantRecord`` fields by ``id``.

    Output order follows ascending ``rank``. Unknown ids are skipped.

    Deduplicates by (1) LLM ``id`` repeats and (2) same ``name`` + ``location`` so multiple
    dataset rows for one real venue do not produce repeated cards.
    """
    by_id = {r.id: r for r in candidates}
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_venues: set[tuple[str, str]] = set()
    for entry in sorted(ranked.ranked, key=lambda e: e.rank):
        if entry.id in seen_ids:
            continue
        base = by_id.get(entry.id)
        if base is None:
            continue
        venue_key = venue_identity_key(base)
        if venue_key in seen_venues:
            continue
        seen_ids.add(entry.id)
        seen_venues.add(venue_key)
        row = base.to_dict()
        row["rank"] = entry.rank
        row["explanation"] = entry.explanation
        if entry.relevance_score is not None:
            row["relevance_score"] = entry.relevance_score
        out.append(row)
    for i, row in enumerate(out, start=1):
        row["rank"] = i
    return out


def to_phase5_payload(
    ranked: RankedRecommendations,
    candidates: list[RestaurantRecord],
) -> dict[str, Any]:
    """Shape aligned with architecture §Phase 5: ``{ summary?, items: [...] }`` plus meta."""
    items = enrich_ranked_with_candidates(ranked, candidates)
    payload: dict[str, Any] = {
        "items": items,
        "used_llm_fallback": ranked.used_llm_fallback,
    }
    if ranked.summary:
        payload["summary"] = ranked.summary
    return payload
