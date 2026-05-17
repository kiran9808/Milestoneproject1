"""Map ``RecommendationRequest`` to Phase 1 ``SearchFilters``."""

from __future__ import annotations

from src.phases.phase1 import SearchFilters
from src.phases.phase1.config import DEFAULT_CANDIDATE_LIMIT

from .dto import RecommendationRequest


def recommendation_request_to_search_filters(
    req: RecommendationRequest,
    *,
    limit: int | None = None,
) -> SearchFilters:
    lim = limit if limit is not None else DEFAULT_CANDIDATE_LIMIT
    max_cost = None if req.budget_amount == 0 else req.budget_amount
    return SearchFilters(
        location=req.location,
        exclude_location=None,
        min_rating=req.min_rating,
        cuisine=req.cuisine,
        min_cost_for_two=None,
        max_cost_for_two=max_cost,
        limit=lim,
    )
