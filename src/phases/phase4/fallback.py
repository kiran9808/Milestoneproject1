"""Deterministic ranking when Groq is unavailable or output is invalid."""

from __future__ import annotations

from src.phases.phase1 import RestaurantRecord

from .schema import RankedEntry, RankedRecommendations


def _rating_key(r: RestaurantRecord) -> tuple[float, int]:
    rating = r.aggregate_rating if r.aggregate_rating is not None else float("-inf")
    votes = r.votes if r.votes is not None else -1
    return (rating, votes)


def deterministic_rank_and_explain(
    candidates: list[RestaurantRecord],
    *,
    reason: str = "Ranked by rating and votes (LLM unavailable or invalid response).",
) -> RankedRecommendations:
    """Same shape as LLM success, with generic explanations (architecture fallback)."""
    sorted_rows = sorted(candidates, key=_rating_key, reverse=True)
    ranked: list[RankedEntry] = []
    for i, r in enumerate(sorted_rows, start=1):
        extra = ""
        if r.aggregate_rating is not None:
            extra = f" Aggregate rating {r.aggregate_rating}."
        if r.cost_for_two is not None:
            extra += f" Typical cost for two ~{r.cost_for_two}."
        ranked.append(
            RankedEntry(
                id=r.id,
                rank=i,
                explanation=f"{reason}{extra}".strip(),
                relevance_score=None,
            )
        )
    return RankedRecommendations(
        summary=None,
        ranked=ranked,
        used_llm_fallback=True,
        raw_model_content=None,
    )
