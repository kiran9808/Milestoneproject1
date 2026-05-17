"""HTTP routes for Phase 5 public recommendation contract."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from src.phases.phase1.config import ENV_DB_PATH, resolve_sqlite_path

from src.phases.phase2.dto import RecommendationRequest

from .schema import RankedRecommendationsResponse
from .service import run_ranked_recommendation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Phase 5 — Ranked recommendations"])


def _db_path() -> Path:
    return resolve_sqlite_path()


@router.post(
    "/recommendations/ranked",
    response_model=RankedRecommendationsResponse,
    summary="Ranked recommendations with AI explanations (Phase 5)",
)
def post_recommendations_ranked(
    body: RecommendationRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> RankedRecommendationsResponse:
    if idempotency_key:
        logger.info("ranked request idempotency_key=%s", idempotency_key[:64])

    db = _db_path()
    if not db.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Restaurant database not found at {db}. Run Phase 1 ingest or set {ENV_DB_PATH}.",
        )

    return run_ranked_recommendation(
        body,
        db_path=db,
        idempotency_key=idempotency_key,
    )
