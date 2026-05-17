"""Enrich + selection dedupe: same venue often has multiple row ids in the dataset."""

from __future__ import annotations

from src.phases.phase1.schema import RestaurantRecord, venue_identity_key
from src.phases.phase4.enrich import enrich_ranked_with_candidates


def _dedupe_venues_clone(rows: list[RestaurantRecord]) -> list[RestaurantRecord]:
    """Mirrors ``phase3.selection._dedupe_venues_preserve_order`` (avoid importing Phase 3 package)."""
    seen: set[tuple[str, str]] = set()
    out: list[RestaurantRecord] = []
    for r in rows:
        key = venue_identity_key(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
from src.phases.phase4.schema import RankedEntry, RankedRecommendations


def test_venue_identity_key_normalizes() -> None:
    a = RestaurantRecord(
        id="1",
        name="  Foo Bar  ",
        location="  BTM ",
        cuisines=(),
        cost_for_two=None,
        aggregate_rating=None,
    )
    b = RestaurantRecord(
        id="2",
        name="foo bar",
        location="btm",
        cuisines=(),
        cost_for_two=None,
        aggregate_rating=None,
    )
    assert venue_identity_key(a) == venue_identity_key(b)


def test_dedupe_venues_preserve_order() -> None:
    rows = [
        RestaurantRecord(
            id="1",
            name="A",
            location="Loc",
            cuisines=("X",),
            cost_for_two=None,
            aggregate_rating=None,
        ),
        RestaurantRecord(
            id="2",
            name="A",
            location="Loc",
            cuisines=("Y",),
            cost_for_two=100.0,
            aggregate_rating=4.0,
        ),
        RestaurantRecord(
            id="3",
            name="B",
            location="Loc",
            cuisines=(),
            cost_for_two=None,
            aggregate_rating=None,
        ),
    ]
    out = _dedupe_venues_clone(rows)
    assert len(out) == 2
    assert out[0].id == "1"
    assert out[1].id == "3"


def test_enrich_dedupes_same_venue_different_row_ids() -> None:
    """LLM may return several ids that map to one real listing (duplicate HF rows)."""
    a = RestaurantRecord(
        id="id-hash-a",
        name="Oh! Calcutta",
        location="Church Street",
        cuisines=("Bengali",),
        cost_for_two=1200.0,
        aggregate_rating=4.5,
        votes=100,
    )
    b = RestaurantRecord(
        id="id-hash-b",
        name="Oh! Calcutta",
        location="Church Street",
        cuisines=("Bengali", "Seafood"),
        cost_for_two=1200.0,
        aggregate_rating=4.5,
        votes=200,
    )
    ranked = RankedRecommendations(
        summary=None,
        ranked=[
            RankedEntry(id="id-hash-a", rank=1, explanation="first"),
            RankedEntry(id="id-hash-b", rank=2, explanation="same venue other row"),
            RankedEntry(id="id-hash-b", rank=3, explanation="dup id"),
        ],
        used_llm_fallback=False,
    )
    out = enrich_ranked_with_candidates(ranked, [a, b])
    assert len(out) == 1
    assert out[0]["name"] == "Oh! Calcutta"
    assert out[0]["rank"] == 1


def test_enrich_still_dedupes_repeated_llm_id() -> None:
    r = RestaurantRecord(
        id="same",
        name="X",
        location="BTM",
        cuisines=("Indian",),
        cost_for_two=500.0,
        aggregate_rating=4.0,
        votes=10,
    )
    ranked = RankedRecommendations(
        summary=None,
        ranked=[
            RankedEntry(id="same", rank=1, explanation="a"),
            RankedEntry(id="same", rank=2, explanation="dup"),
        ],
        used_llm_fallback=False,
    )
    out = enrich_ranked_with_candidates(ranked, [r])
    assert len(out) == 1
