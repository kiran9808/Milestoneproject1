"""Orchestrates selection + prompt assembly for downstream Phase 4."""

from __future__ import annotations

from src.phases.phase1 import Phase1DataService

from src.phases.phase2.dto import RecommendationRequest
from src.phases.phase2.mapping import recommendation_request_to_search_filters

from .config import DEFAULT_FETCH_LIMIT, DEFAULT_TOP_K
from .prompt import build_prompt
from .schema import CandidateSelectionResult
from .selection import select_candidates_with_relaxation


class IntegrationService:
    """Phase 3 integration layer entrypoint."""

    def __init__(
        self,
        phase1: Phase1DataService,
        *,
        top_k: int | None = None,
        fetch_limit: int | None = None,
    ) -> None:
        self._phase1 = phase1
        self._top_k = top_k if top_k is not None else DEFAULT_TOP_K
        self._fetch_limit = fetch_limit if fetch_limit is not None else DEFAULT_FETCH_LIMIT

    def select(self, request: RecommendationRequest) -> CandidateSelectionResult:
        """Map request to ``SearchFilters``, fetch candidates, apply relaxation if needed."""
        pool = max(self._fetch_limit, self._top_k)
        filters = recommendation_request_to_search_filters(request, limit=pool)
        return select_candidates_with_relaxation(
            self._phase1,
            filters,
            top_k=self._top_k,
            fetch_limit=pool,
            strict_cuisine=request.strict_cuisine,
            explore_other_locations=request.explore_other_locations,
            user_location=request.location,
        )

    def build_llm_messages(
        self,
        request: RecommendationRequest,
        selection: CandidateSelectionResult | None = None,
    ) -> list[dict[str, str]]:
        """``build_prompt(request, candidates)`` from the architecture doc."""
        sel = selection if selection is not None else self.select(request)
        return build_prompt(request, sel.candidates, selection=sel)
