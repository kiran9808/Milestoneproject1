"""REST API: ``POST /recommendations`` with optional ``Idempotency-Key`` header."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.phases.phase1 import Phase1DataService
from src.phases.phase5.routes import router as phase5_router
from src.phases.phase1.config import DEFAULT_SQLITE_PATH

from .dto import (
    CuisinesResponse,
    LocationsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from .mapping import recommendation_request_to_search_filters

logger = logging.getLogger(__name__)

ENV_DB_PATH = "RESTAURANTS_DB_PATH"

_WEB_ROOT = Path(__file__).resolve().parents[3] / "web"


def _db_path() -> Path:
    raw = os.environ.get(ENV_DB_PATH)
    return Path(raw) if raw else DEFAULT_SQLITE_PATH


def create_app() -> FastAPI:
    app = FastAPI(
        title="Restaurant recommendations",
        version="0.1.0",
        description=(
        "Phase 2 — validated preferences and candidate lookup (Phase 1 store). "
        "Phase 5 — POST /recommendations/ranked for LLM-ranked JSON with stable contract."
    ),
    )

    app.include_router(phase5_router)

    if _WEB_ROOT.is_dir():
        app.mount(
            "/ui",
            StaticFiles(directory=str(_WEB_ROOT), html=True),
            name="demo_ui",
        )

    @app.get("/", include_in_schema=False)
    def root_redirect() -> RedirectResponse:
        if _WEB_ROOT.is_dir():
            return RedirectResponse(url="/ui/", status_code=302)
        return RedirectResponse(url="/docs", status_code=302)

    @app.post("/recommendations", response_model=RecommendationResponse)
    def post_recommendations(
        body: RecommendationRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> RecommendationResponse:
        if idempotency_key:
            logger.info("request idempotency_key=%s", idempotency_key[:64])

        db = _db_path()
        if not db.is_file():
            raise HTTPException(
                status_code=503,
                detail=f"Restaurant database not found at {db}. Run Phase 1 ingest or set {ENV_DB_PATH}.",
            )

        filters = recommendation_request_to_search_filters(body)
        svc = Phase1DataService(db_path=db)
        records = svc.get_candidates(filters)
        candidates = [r.to_dict() for r in records]

        return RecommendationResponse(
            idempotency_key=idempotency_key,
            location=body.location,
            budget_amount=body.budget_amount,
            cuisine=body.cuisine,
            min_rating=body.min_rating,
            additional_preferences=body.additional_preferences,
            candidates=candidates,
            candidate_count=len(candidates),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/locations", response_model=LocationsResponse, tags=["Metadata"])
    def get_locations() -> LocationsResponse:
        """Distinct ``location`` values in the restaurant DB (for UI dropdowns)."""
        db = _db_path()
        if not db.is_file():
            raise HTTPException(
                status_code=503,
                detail=f"Restaurant database not found at {db}. Run Phase 1 ingest or set {ENV_DB_PATH}.",
            )
        svc = Phase1DataService(db_path=db)
        return LocationsResponse(locations=svc.list_locations())

    @app.get("/cuisines", response_model=CuisinesResponse, tags=["Metadata"])
    def get_cuisines(
        location: str | None = Query(
            default=None,
            description=(
                "If set, only cuisine tags that appear at this location are returned "
                "(same normalization as Phase 1 search)."
            ),
        ),
    ) -> CuisinesResponse:
        """Distinct cuisine tags in the restaurant DB (for UI dropdowns)."""
        db = _db_path()
        if not db.is_file():
            raise HTTPException(
                status_code=503,
                detail=f"Restaurant database not found at {db}. Run Phase 1 ingest or set {ENV_DB_PATH}.",
            )
        svc = Phase1DataService(db_path=db)
        return CuisinesResponse(
            cuisines=svc.list_cuisine_tags(
                location=location.strip() if location else None,
            ),
        )

    return app


# Uvicorn: ``uvicorn src.phases.phase2.api:app`` if module-level app is desired
app = create_app()
