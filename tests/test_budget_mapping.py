"""Phase 2: numeric budget maps to Phase 1 cost filters."""

from __future__ import annotations

from src.phases.phase2.dto import RecommendationRequest
from src.phases.phase2.mapping import recommendation_request_to_search_filters


def _base_req(**kwargs: object) -> RecommendationRequest:
    data = {
        "location": "BTM",
        "budget_amount": 800.0,
        "cuisine": None,
        "min_rating": 0.0,
        "additional_preferences": None,
    }
    data.update(kwargs)
    return RecommendationRequest.model_validate(data)


def test_budget_amount_sets_max_cost_for_two() -> None:
    f = recommendation_request_to_search_filters(_base_req(budget_amount=1200.0))
    assert f.max_cost_for_two == 1200.0
    assert f.min_cost_for_two is None


def test_zero_budget_amount_opens_upper_cap() -> None:
    f = recommendation_request_to_search_filters(_base_req(budget_amount=0.0))
    assert f.max_cost_for_two is None
    assert f.min_cost_for_two is None
