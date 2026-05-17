"""End-to-end ranked recommendations: Phase 1 + 3 + 4 → Phase 5 response."""

from __future__ import annotations

import logging
from pathlib import Path

from src.phases.phase1 import Phase1DataService
from src.phases.phase2.dto import RecommendationRequest
from src.phases.phase3 import IntegrationService
from src.phases.phase4.engine import GroqRecommendationEngine
from src.phases.phase4.enrich import to_phase5_payload
from src.phases.phase4.schema import LLMUserContext

from .response import ranked_response_from_internal_payload
from .schema import RankedRecommendationsResponse

logger = logging.getLogger(__name__)


def run_ranked_recommendation(
    request: RecommendationRequest,
    *,
    db_path: Path,
    idempotency_key: str | None = None,
    integration: IntegrationService | None = None,
    engine: GroqRecommendationEngine | None = None,
) -> RankedRecommendationsResponse:
    phase1 = Phase1DataService(db_path)
    integ = integration or IntegrationService(phase1)
    selection = integ.select(request)
    messages = integ.build_llm_messages(request, selection=selection)

    eng = engine if engine is not None else GroqRecommendationEngine()
    ranked = eng.rank_and_explain(selection.candidates, LLMUserContext(messages=messages))
    internal = to_phase5_payload(ranked, selection.candidates)
    return ranked_response_from_internal_payload(
        internal,
        selection=selection,
        idempotency_key=idempotency_key,
    )
