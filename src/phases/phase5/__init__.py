"""Phase 5 — public API response contract and ranked recommendations route."""

from .constants import PHASE5_AI_EXPLANATION_DISCLAIMER
from .response import ranked_response_from_internal_payload
from .schema import RankedRecommendationsResponse, RecommendationItem, SelectionMeta
from .service import run_ranked_recommendation

__all__ = [
    "PHASE5_AI_EXPLANATION_DISCLAIMER",
    "RankedRecommendationsResponse",
    "RecommendationItem",
    "SelectionMeta",
    "ranked_response_from_internal_payload",
    "run_ranked_recommendation",
]
