"""Assemble LLM-ready messages from user request + candidate list (Phase 3)."""

from __future__ import annotations

import json
from typing import Any

from src.phases.phase1 import RestaurantRecord
from src.phases.phase2.dto import RecommendationRequest

from .safety import sanitize_preferences
from .schema import CandidateSelectionResult


def _compact_candidate(r: RestaurantRecord) -> dict[str, Any]:
    """Only fields needed for ranking / explanations (architecture)."""
    return {
        "id": r.id,
        "name": r.name,
        "location": r.location,
        "cuisines": list(r.cuisines),
        "cost_for_two": r.cost_for_two,
        "aggregate_rating": r.aggregate_rating,
        "votes": r.votes,
    }


_SYSTEM_PROMPT = """You are a restaurant recommendation assistant for a structured catalog.

Rules:
- Rank ONLY restaurants whose ``id`` appears in the provided ``candidates`` list. Never invent venues or IDs.
- When mentioning cuisine, use ONLY labels from each candidate's ``cuisines`` array. Never claim a venue serves a cuisine that is not listed there.
- Use the numeric fields (rating, votes, cost_for_two vs user ``budget_amount``) and cuisines to justify ordering.
- Output a single JSON object, no markdown fences, with this shape:
  {
    "summary": string (optional, one short paragraph),
    "ranked": [
      {"id": string, "rank": integer (1-based), "explanation": string (1-3 sentences)}
    ]
  }
- Include at most one entry per candidate ``id``. Prefer the top matches for the user preferences.
- If ``user_preferences.candidate_scope_note`` is present, reflect it in the summary: candidates may be outside the user's preferred area—name each venue's ``location`` when relevant.
"""


def build_prompt(
    request: RecommendationRequest,
    candidates: list[RestaurantRecord],
    *,
    selection: CandidateSelectionResult | None = None,
) -> list[dict[str, str]]:
    """
    Build chat-style messages: system instructions + user JSON payload.

    Returns ``messages`` suitable for OpenAI-compatible ``/v1/chat/completions`` APIs.
    """
    prefs: dict[str, Any] = {
        "location": request.location,
        "budget_amount": request.budget_amount,
        "cuisine": request.cuisine,
        "min_rating": request.min_rating,
        "additional_preferences": sanitize_preferences(request.additional_preferences),
    }
    if selection is not None and selection.cross_location_fallback:
        area = selection.expanded_from_location or request.location
        prefs["candidate_scope_note"] = (
            f"No matches in {area}; candidates are from other areas but still align with "
            "your cuisine (and relaxed filters). Reference each venue's location in the summary."
        )
    payload = {
        "user_preferences": prefs,
        "candidates": [_compact_candidate(r) for r in candidates],
    }
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)
    return [
        {"role": "system", "content": _SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_content},
    ]
