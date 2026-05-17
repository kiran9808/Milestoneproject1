"""End-to-end CLI: Phase 1 DB + Phase 3 selection/prompt + Phase 4 Groq."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from src.phases.phase1 import Phase1DataService
from src.phases.phase1.config import DEFAULT_SQLITE_PATH

from src.phases.phase2.dto import RecommendationRequest

from src.phases.phase3 import IntegrationService
from src.phases.phase3.schema import CandidateSelectionResult

from .enrich import to_phase5_payload
from .engine import GroqRecommendationEngine, rank_and_explain
from .schema import LLMUserContext

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _load_request(path: Path | None) -> RecommendationRequest:
    raw = json.loads(path.read_text(encoding="utf-8")) if path else json.load(sys.stdin)
    return RecommendationRequest.model_validate(raw)


def _cmd_recommend(args: argparse.Namespace) -> int:
    try:
        req = _load_request(args.file)
    except (ValidationError, json.JSONDecodeError) as e:
        print(e, file=sys.stderr)
        return 1

    svc = Phase1DataService(Path(args.db_path))
    integ = IntegrationService(svc, top_k=args.top_k, fetch_limit=args.fetch_limit)
    selection: CandidateSelectionResult = integ.select(req)
    messages = integ.build_llm_messages(req, selection=selection)

    if args.dry_run:
        out = {
            "selection": {
                "had_strict_match": selection.had_strict_match,
                "relaxation_steps_applied": selection.relaxation_steps_applied,
                "candidate_count": len(selection.candidates),
            },
            "messages": messages,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    engine = GroqRecommendationEngine()
    ranked = engine.rank_and_explain(selection.candidates, LLMUserContext(messages=messages))
    payload = to_phase5_payload(ranked, selection.candidates)
    payload["selection_meta"] = {
        "had_strict_match": selection.had_strict_match,
        "relaxation_steps_applied": selection.relaxation_steps_applied,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4 — Groq rank_and_explain")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="SQLite DB from Phase 1 ingest",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="JSON file for RecommendationRequest (default: stdin)",
    )
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--fetch-limit", type=int, default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip Groq; only print selection + messages",
    )
    parser.set_defaults(func=_cmd_recommend)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
