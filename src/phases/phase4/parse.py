"""Parse and validate Groq chat JSON against allowed candidate ids."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .schema import RankedEntry, RankedRecommendations

logger = logging.getLogger(__name__)


def _strip_code_fence(content: str) -> str:
    s = content.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def parse_ranked_json(
    content: str,
    *,
    allowed_ids: set[str],
) -> RankedRecommendations | None:
    """
    Parse model output into ``RankedRecommendations``.

    Drops unknown ``id`` values (hallucinations). Returns ``None`` if JSON is invalid
    or ``ranked`` is missing/empty after filtering.
    """
    try:
        text = _strip_code_fence(content)
        data: Any = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("LLM JSON parse failed: %s", e)
        return None

    if not isinstance(data, dict):
        return None

    summary = data.get("summary")
    if summary is not None and not isinstance(summary, str):
        summary = str(summary)

    raw_ranked = data.get("ranked")
    if not isinstance(raw_ranked, list) or not raw_ranked:
        return None

    entries: list[RankedEntry] = []
    seen: set[str] = set()
    for item in raw_ranked:
        if not isinstance(item, dict):
            continue
        rid = item.get("id")
        if not isinstance(rid, str) or not rid.strip():
            continue
        rid = rid.strip()
        if rid not in allowed_ids:
            logger.info("dropping unknown candidate id from LLM output: %s", rid)
            continue
        if rid in seen:
            continue
        seen.add(rid)

        rank_raw = item.get("rank")
        try:
            rank = int(rank_raw)
        except (TypeError, ValueError):
            rank = len(entries) + 1

        expl = item.get("explanation")
        explanation = expl.strip() if isinstance(expl, str) else str(expl or "")

        score: float | None = None
        if "relevance_score" in item and item["relevance_score"] is not None:
            try:
                score = float(item["relevance_score"])
            except (TypeError, ValueError):
                score = None

        entries.append(
            RankedEntry(
                id=rid,
                rank=rank,
                explanation=explanation or "No explanation provided.",
                relevance_score=score,
            )
        )

    if not entries:
        return None

    entries.sort(key=lambda e: e.rank)
    return RankedRecommendations(
        summary=summary if isinstance(summary, str) else None,
        ranked=entries,
        used_llm_fallback=False,
        raw_model_content=content,
    )
