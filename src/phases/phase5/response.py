"""Map Phase 4 enrich payloads to the stable Phase 5 HTTP contract."""

from __future__ import annotations

from typing import Any

from src.phases.phase3.schema import CandidateSelectionResult

from .schema import RankedRecommendationsResponse, RecommendationItem, SelectionMeta


def ranked_response_from_internal_payload(
    payload: dict[str, Any],
    *,
    selection: CandidateSelectionResult | None = None,
    idempotency_key: str | None = None,
) -> RankedRecommendationsResponse:
    raw_items: list[dict[str, Any]] = payload.get("items") or []
    items: list[RecommendationItem] = []
    for row in raw_items:
        rs = row.get("relevance_score")
        loc = row.get("location")
        items.append(
            RecommendationItem(
                id=str(row["id"]),
                name=str(row["name"]),
                location=str(loc) if loc is not None else None,
                cuisines=list(row.get("cuisines") or []),
                rating=row.get("aggregate_rating"),
                cost=row.get("cost_for_two"),
                explanation=str(row.get("explanation") or ""),
                rank=int(row["rank"]),
                relevance_score=float(rs) if rs is not None else None,
            )
        )

    sel: SelectionMeta | None = None
    if selection is not None:
        sel = SelectionMeta(
            had_strict_match=selection.had_strict_match,
            relaxation_steps_applied=list(selection.relaxation_steps_applied),
            cross_location_fallback=selection.cross_location_fallback,
            expanded_from_location=selection.expanded_from_location,
        )

    return RankedRecommendationsResponse(
        summary=payload.get("summary"),
        items=items,
        used_llm_fallback=bool(payload.get("used_llm_fallback", False)),
        selection=sel,
        idempotency_key=idempotency_key,
    )
