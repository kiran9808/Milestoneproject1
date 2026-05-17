"""Filter, rank alignment, truncation, and relaxation when no matches (Phase 3)."""

from __future__ import annotations

from dataclasses import replace

from src.phases.phase1 import Phase1DataService, RestaurantRecord, SearchFilters
from src.phases.phase1.schema import venue_identity_key

from .config import DEFAULT_FETCH_LIMIT, DEFAULT_TOP_K
from .schema import CandidateSelectionResult


def _dedupe_venues_preserve_order(rows: list[RestaurantRecord]) -> list[RestaurantRecord]:
    """Keep first row per ``(name, location)`` so the LLM does not see duplicate venues."""
    seen: set[tuple[str, str]] = set()
    out: list[RestaurantRecord] = []
    for r in rows:
        key = venue_identity_key(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def select_candidates(
    svc: Phase1DataService,
    filters: SearchFilters,
    *,
    top_k: int | None = None,
    fetch_limit: int | None = None,
) -> list[RestaurantRecord]:
    """
    Architecture interface: apply structured filters and return up to ``top_k`` rows.

    Uses Phase 1 read path with an enlarged fetch window, then truncates in-process so
    ordering matches the database (rating, then votes) while respecting ``top_k``.
    """
    k = top_k if top_k is not None else DEFAULT_TOP_K
    fetch = fetch_limit if fetch_limit is not None else max(DEFAULT_FETCH_LIMIT, k)
    f = replace(filters, limit=fetch)
    rows = _dedupe_venues_preserve_order(svc.get_candidates(f))
    return rows[:k]


def _result(
    rows: list[RestaurantRecord],
    filters_used: SearchFilters,
    *,
    steps: list[str],
    strict: bool,
    cross_loc: bool = False,
    expanded_from: str | None = None,
    top_k: int,
) -> CandidateSelectionResult:
    return CandidateSelectionResult(
        candidates=rows,
        filters_used=replace(filters_used, limit=top_k),
        relaxation_steps_applied=list(steps),
        had_strict_match=strict,
        cross_location_fallback=cross_loc,
        expanded_from_location=expanded_from,
    )


def _cross_filters(f: SearchFilters, user_location: str) -> SearchFilters:
    ul = user_location.strip()
    return replace(
        f,
        location=None,
        exclude_location=ul if ul else None,
    )


def select_candidates_with_relaxation(
    svc: Phase1DataService,
    filters: SearchFilters,
    *,
    top_k: int | None = None,
    fetch_limit: int | None = None,
    strict_cuisine: bool = True,
    explore_other_locations: bool = True,
    user_location: str = "",
) -> CandidateSelectionResult:
    """
    If strict filters return no rows, relax.

    When ``strict_cuisine`` is True (default), cuisine is never dropped. The engine
    first relaxes budget and minimum rating **within the selected location**, then
    optionally searches **other locations** while keeping cuisine (if
    ``explore_other_locations``).

    When ``strict_cuisine`` is False, the legacy order applies: drop cuisine, then
    budget, then rating (no cross-location expansion).
    """
    k = top_k if top_k is not None else DEFAULT_TOP_K
    fetch = fetch_limit if fetch_limit is not None else max(DEFAULT_FETCH_LIMIT, k)
    steps: list[str] = []

    def run(f: SearchFilters) -> list[RestaurantRecord]:
        ff = replace(f, limit=fetch)
        raw = svc.get_candidates(ff)
        return _dedupe_venues_preserve_order(raw)[:k]

    base = replace(filters, limit=fetch)
    loc_for_exclude = (user_location or base.location or "").strip()

    rows = run(base)
    if rows:
        return _result(rows, base, steps=steps, strict=True, top_k=k)

    steps.append("strict_filters_empty")

    if not strict_cuisine:
        return _legacy_relaxation(
            base=base,
            run=run,
            steps=steps,
            k=k,
        )

    # --- strict cuisine: local budget → local rating → other locations ---
    fb = replace(
        base,
        max_cost_for_two=None,
        min_cost_for_two=None,
    )
    rows = run(fb)
    if rows:
        steps.append("ignored_budget_cap")
        return _result(rows, fb, steps=steps, strict=False, top_k=k)

    f_cur = fb
    rating = fb.min_rating
    while rating > 0 and not rows:
        rating = max(0.0, rating - 1.0)
        f_cur = replace(f_cur, min_rating=rating)
        rows = run(f_cur)
        steps.append(f"lowered_min_rating_to_{rating}")

    if rows:
        return _result(rows, f_cur, steps=steps, strict=False, top_k=k)

    if (
        explore_other_locations
        and base.cuisine
        and base.cuisine.strip()
        and loc_for_exclude
    ):
        phases: list[tuple[SearchFilters, str]] = [
            (_cross_filters(base, loc_for_exclude), "expanded_to_other_locations"),
            (
                replace(
                    _cross_filters(base, loc_for_exclude),
                    max_cost_for_two=None,
                    min_cost_for_two=None,
                ),
                "expanded_to_other_locations_open_budget",
            ),
        ]
        f_cross_rating = replace(
            _cross_filters(base, loc_for_exclude),
            max_cost_for_two=None,
            min_cost_for_two=None,
        )
        rating_x = f_cross_rating.min_rating
        for f_try, step_name in phases:
            rows = run(f_try)
            if rows:
                steps.append(step_name)
                return _result(
                    rows,
                    f_try,
                    steps=steps,
                    strict=False,
                    cross_loc=True,
                    expanded_from=loc_for_exclude,
                    top_k=k,
                )

        f_xr = f_cross_rating
        while rating_x > 0 and not rows:
            rating_x = max(0.0, rating_x - 1.0)
            f_xr = replace(f_xr, min_rating=rating_x)
            rows = run(f_xr)
            steps.append(f"expanded_other_areas_lowered_min_rating_to_{rating_x}")
            if rows:
                return _result(
                    rows,
                    f_xr,
                    steps=steps,
                    strict=False,
                    cross_loc=True,
                    expanded_from=loc_for_exclude,
                    top_k=k,
                )

    steps.append("no_rows_after_relaxation")
    return CandidateSelectionResult(
        candidates=[],
        filters_used=replace(f_cur, limit=k),
        relaxation_steps_applied=steps,
        had_strict_match=False,
        cross_location_fallback=False,
        expanded_from_location=None,
    )


def _legacy_relaxation(
    *,
    base: SearchFilters,
    run,
    steps: list[str],
    k: int,
) -> CandidateSelectionResult:
    """Original relaxation: drop cuisine → budget → rating (no geographic expansion)."""

    # Step 1: drop cuisine
    if base.cuisine is not None:
        f1 = replace(base, cuisine=None)
        rows = run(f1)
        steps.append("dropped_cuisine")
        if rows:
            return _result(rows, f1, steps=steps, strict=False, top_k=k)

    f2 = replace(base, cuisine=None, min_cost_for_two=None, max_cost_for_two=None)
    rows = run(f2)
    steps.append("ignored_budget_cap")
    if rows:
        return _result(rows, f2, steps=steps, strict=False, top_k=k)

    rating = f2.min_rating
    f_cur = f2
    while rating > 0 and not rows:
        rating = max(0.0, rating - 1.0)
        f_cur = replace(f_cur, min_rating=rating)
        rows = run(f_cur)
        steps.append(f"lowered_min_rating_to_{rating}")

    if rows:
        return _result(rows, f_cur, steps=steps, strict=False, top_k=k)

    steps.append("no_rows_after_relaxation")
    return CandidateSelectionResult(
        candidates=[],
        filters_used=replace(f_cur, limit=k),
        relaxation_steps_applied=steps,
        had_strict_match=False,
        cross_location_fallback=False,
        expanded_from_location=None,
    )
