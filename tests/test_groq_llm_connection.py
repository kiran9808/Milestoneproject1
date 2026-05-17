"""
Live Groq connectivity checks (3–4 tests).

Loads repo ``.env``, ``src/phases/phase4/.env``, and optional ``apikey.env``.
Never prints API keys — only safe LLM text and metadata.

Run with **stdout visible**::

    pytest tests/test_groq_llm_connection.py -v -s
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.phases.phase1.preprocess import raw_row_to_restaurant
from src.phases.phase2.dto import RecommendationRequest
from src.phases.phase3.prompt import build_prompt
from src.phases.phase4.config import DEFAULT_GROQ_MODEL, ENV_GROQ_API_KEY, ENV_GROQ_MODEL
from src.phases.phase4.engine import _build_client, _chat_completion
from src.phases.phase4.env import load_project_dotenv
from src.phases.phase4.enrich import to_phase5_payload
from src.phases.phase4.schema import LLMUserContext
from src.phases.phase4 import rank_and_explain

_ROOT = Path(__file__).resolve().parents[1]
for _env_path in (
    _ROOT / ".env",
    _ROOT / "src" / "phases" / "phase4" / ".env",
    _ROOT / "src" / "phases" / "phase4" / "apikey.env",
):
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)

load_project_dotenv()


def _groq_key_present() -> bool:
    return bool(os.environ.get(ENV_GROQ_API_KEY, "").strip())


def _skip_missing_key() -> None:
    if _groq_key_present():
        return
    phase4_dot = _ROOT / "src" / "phases" / "phase4" / ".env"
    root_dot = _ROOT / ".env"
    if phase4_dot.is_file() and phase4_dot.stat().st_size == 0:
        pytest.skip(
            "src/phases/phase4/.env exists but is empty — add a line: GROQ_API_KEY=your_key"
        )
    if root_dot.is_file() and root_dot.stat().st_size == 0:
        pytest.skip(".env at repo root exists but is empty — add GROQ_API_KEY=your_key")
    pytest.skip(
        "GROQ_API_KEY not set after loading .env files. "
        "Put GROQ_API_KEY in the repo root .env or src/phases/phase4/.env"
    )


def _peek(text: str | None, max_len: int = 500) -> str:
    if not text:
        return "(none)"
    t = text.strip().replace("\r\n", "\n")
    return t if len(t) <= max_len else t[: max_len - 3] + "..."


def test_groq_api_key_loaded_from_dotenv() -> None:
    """Env: key present (never print the key itself)."""
    _skip_missing_key()
    key = os.environ.get(ENV_GROQ_API_KEY, "").strip()
    assert len(key) >= 12, "GROQ_API_KEY should be a non-trivial string when configured"
    print("\n=== [1] API key ===")
    print(f"GROQ_API_KEY is set (length={len(key)} chars). Value is not printed.\n")


@pytest.mark.network
def test_groq_minimal_chat_completion() -> None:
    """Raw completion text from Groq (tiny prompt)."""
    _skip_missing_key()
    client = _build_client()
    model = os.environ.get(ENV_GROQ_MODEL, DEFAULT_GROQ_MODEL).strip()
    text = _chat_completion(
        client,
        model=model,
        messages=[
            {"role": "system", "content": "You reply with one word only."},
            {"role": "user", "content": 'Say exactly the word "PONG" and nothing else.'},
        ],
        use_json_object_format=False,
    )
    assert text.strip(), "completion should be non-empty"
    assert "PONG" in text.upper(), f"unexpected reply (truncated): {text.strip()[:80]!r}"

    print("\n=== [2] Minimal chat completion ===")
    print(f"model: {model}")
    print(f"assistant_message:\n{_peek(text, 400)}\n")


@pytest.mark.network
def test_rank_and_explain_uses_llm_not_fallback_single_candidate() -> None:
    """Structured JSON path: one restaurant — print summary + explanations."""
    _skip_missing_key()
    rec = raw_row_to_restaurant(
        {
            "Restaurant Name": "Test Bistro",
            "City": "Mumbai",
            "Cuisines": "North Indian",
            "Aggregate rating": 4.2,
            "Votes": 50,
            "Average Cost for two": 800,
        },
        row_index=0,
    )
    assert rec is not None
    req = RecommendationRequest(
        location="Mumbai",
        budget_amount=900.0,
        cuisine="North Indian",
        min_rating=4.0,
        additional_preferences=None,
    )
    messages = build_prompt(req, [rec])
    out = rank_and_explain([rec], LLMUserContext(messages=messages))
    assert not out.used_llm_fallback, "expected Groq path, not deterministic fallback"
    assert out.ranked, "expected non-empty ranked list"
    assert out.ranked[0].id == rec.id
    assert out.ranked[0].explanation.strip()
    allowed = {rec.id}
    for entry in out.ranked:
        assert entry.id in allowed, f"unexpected id from model: {entry.id!r}"

    print("\n=== [3] rank_and_explain (1 candidate) ===")
    print(f"used_llm_fallback: {out.used_llm_fallback}")
    print(f"summary: {_peek(out.summary, 600)}")
    for e in out.ranked:
        print(f"  rank={e.rank} id={e.id}")
        print(f"    explanation: {_peek(e.explanation, 400)}")
        if e.relevance_score is not None:
            print(f"    relevance_score: {e.relevance_score}")
    payload = to_phase5_payload(out, [rec])
    print(f"phase5 item count: {len(payload.get('items', []))}\n")


@pytest.mark.network
def test_rank_and_explain_two_candidates_prints_ordering() -> None:
    """Two venues — LLM ranks & explains; print merged payload preview."""
    _skip_missing_key()
    r1 = raw_row_to_restaurant(
        {
            "Restaurant Name": "Spice Hub",
            "City": "Delhi",
            "Cuisines": "North Indian",
            "Aggregate rating": 4.5,
            "Votes": 200,
            "Average Cost for two": 1200,
        },
        row_index=10,
    )
    r2 = raw_row_to_restaurant(
        {
            "Restaurant Name": "Budget Dhaba",
            "City": "Delhi",
            "Cuisines": "North Indian",
            "Aggregate rating": 3.8,
            "Votes": 40,
            "Average Cost for two": 400,
        },
        row_index=11,
    )
    assert r1 and r2
    candidates = [r1, r2]
    req = RecommendationRequest(
        location="Delhi",
        budget_amount=1500.0,
        cuisine="North Indian",
        min_rating=3.5,
        additional_preferences="Prefer good value for money.",
    )
    messages = build_prompt(req, candidates)
    out = rank_and_explain(candidates, LLMUserContext(messages=messages))

    print("\n=== [4] rank_and_explain (2 candidates) ===")
    print(f"used_llm_fallback: {out.used_llm_fallback}")
    print(f"summary: {_peek(out.summary, 600)}")
    for e in sorted(out.ranked, key=lambda x: x.rank):
        match = next((c for c in candidates if c.id == e.id), None)
        name = match.name if match else "?"
        print(f"  rank={e.rank}  {name!r}")
        print(f"    {_peek(e.explanation, 350)}")
    if not out.used_llm_fallback:
        assert len({e.id for e in out.ranked}) == len(out.ranked)
        for e in out.ranked:
            assert e.id in {r1.id, r2.id}
