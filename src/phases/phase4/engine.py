"""Groq-backed ``rank_and_explain`` with retries and deterministic fallback."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from src.phases.phase1 import RestaurantRecord

from .config import (
    DEFAULT_GROQ_MODEL,
    ENV_GROQ_API_KEY,
    ENV_GROQ_BASE_URL,
    ENV_GROQ_MODEL,
    GROQ_OPENAI_BASE_URL,
    MAX_COMPLETION_RETRIES,
    RETRY_BACKOFF_SEC,
)
from .env import load_project_dotenv
from .fallback import deterministic_rank_and_explain
from .parse import parse_ranked_json
from .schema import LLMUserContext, RankedRecommendations

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in {408, 429, 500, 502, 503, 504}
    return False


def _build_client() -> OpenAI:
    load_project_dotenv()
    key = os.environ.get(ENV_GROQ_API_KEY)
    if not key or not key.strip():
        raise RuntimeError(
            f"{ENV_GROQ_API_KEY} is not set. Add it to your project `.env` file (see `.env.example`)."
        )
    base = os.environ.get(ENV_GROQ_BASE_URL, GROQ_OPENAI_BASE_URL).strip()
    return OpenAI(api_key=key.strip(), base_url=base, timeout=90.0)


def _chat_completion(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict[str, str]],
    use_json_object_format: bool,
) -> str:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if use_json_object_format:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    content = choice.message.content
    if not content:
        raise RuntimeError("empty completion content")
    return content


def rank_and_explain(
    candidates: list[RestaurantRecord],
    user_context: LLMUserContext,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
) -> RankedRecommendations:
    """
    Call Groq (OpenAI-compatible chat completions), parse JSON, validate ids.

    On repeated failures, invalid JSON, or missing ``GROQ_API_KEY``, falls back to
    ``deterministic_rank_and_explain`` (architecture).
    """
    if not candidates:
        return RankedRecommendations(summary=None, ranked=[], used_llm_fallback=True)

    allowed_ids = {c.id for c in candidates}
    load_project_dotenv()
    mdl = (model or os.environ.get(ENV_GROQ_MODEL, DEFAULT_GROQ_MODEL)).strip()

    try:
        cli = client if client is not None else _build_client()
    except RuntimeError as exc:
        logger.warning("%s — using deterministic fallback.", exc)
        return deterministic_rank_and_explain(
            candidates,
            reason="Ranked by rating and votes (Groq API key not configured).",
        )

    last_error: BaseException | None = None
    content: str | None = None

    for attempt in range(MAX_COMPLETION_RETRIES):
        use_json = attempt == 0
        try:
            content = _chat_completion(
                cli,
                model=mdl,
                messages=user_context.messages,
                use_json_object_format=use_json,
            )
            parsed = parse_ranked_json(content, allowed_ids=allowed_ids)
            if parsed is not None:
                return RankedRecommendations(
                    summary=parsed.summary,
                    ranked=parsed.ranked,
                    used_llm_fallback=False,
                    raw_model_content=parsed.raw_model_content,
                )
            logger.warning("LLM output parsed but empty/invalid ranked list (attempt %s).", attempt + 1)
        except BaseException as exc:
            last_error = exc
            if not _is_retryable(exc):
                logger.exception("non-retryable Groq error: %s", exc)
                break
            logger.warning("Groq attempt %s failed (%s).", attempt + 1, exc)
            last_error = exc

        if attempt + 1 < MAX_COMPLETION_RETRIES:
            wait = RETRY_BACKOFF_SEC * (2**attempt)
            time.sleep(wait)

    if last_error:
        logger.error("Groq failed after retries: %s", last_error)

    fb = deterministic_rank_and_explain(
        candidates,
        reason="Ranked by rating and votes (Groq error or invalid JSON).",
    )
    return RankedRecommendations(
        summary=fb.summary,
        ranked=fb.ranked,
        used_llm_fallback=True,
        raw_model_content=content,
    )


class GroqRecommendationEngine:
    """Reuses a single OpenAI-compatible client for multiple ``rank_and_explain`` calls."""

    def __init__(self, *, client: OpenAI | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model
        self._cached: OpenAI | None = None
        self._missing_key: bool = False

    def rank_and_explain(
        self,
        candidates: list[RestaurantRecord],
        user_context: LLMUserContext,
    ) -> RankedRecommendations:
        if self._missing_key:
            return deterministic_rank_and_explain(
                candidates,
                reason="Ranked by rating and votes (Groq API key not configured).",
            )

        chosen = self._client
        if chosen is None:
            if self._cached is None:
                try:
                    self._cached = _build_client()
                except RuntimeError as exc:
                    logger.warning("%s — using deterministic fallback.", exc)
                    self._missing_key = True
                    return deterministic_rank_and_explain(
                        candidates,
                        reason="Ranked by rating and votes (Groq API key not configured).",
                    )
            chosen = self._cached

        return rank_and_explain(
            candidates,
            user_context,
            client=chosen,
            model=self._model,
        )
