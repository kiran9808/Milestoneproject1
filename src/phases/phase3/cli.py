"""CLI: run selection + print LLM messages as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from src.phases.phase1 import Phase1DataService
from src.phases.phase1.config import DEFAULT_SQLITE_PATH

from src.phases.phase2.dto import RecommendationRequest

from .config import DEFAULT_FETCH_LIMIT, DEFAULT_TOP_K
from .integration import IntegrationService


def _load_request(path: Path | None) -> RecommendationRequest:
    raw = json.loads(path.read_text(encoding="utf-8")) if path else json.load(sys.stdin)
    return RecommendationRequest.model_validate(raw)


def _cmd_select(args: argparse.Namespace) -> int:
    try:
        req = _load_request(args.file)
    except (ValidationError, json.JSONDecodeError) as e:
        print(e, file=sys.stderr)
        return 1

    svc = Phase1DataService(Path(args.db_path))
    integ = IntegrationService(svc, top_k=args.top_k, fetch_limit=args.fetch_limit)
    sel = integ.select(req)
    out = {
        "had_strict_match": sel.had_strict_match,
        "relaxation_steps_applied": sel.relaxation_steps_applied,
        "candidate_count": len(sel.candidates),
        "filters_used": {
            "location": sel.filters_used.location,
            "min_rating": sel.filters_used.min_rating,
            "cuisine": sel.filters_used.cuisine,
            "min_cost_for_two": sel.filters_used.min_cost_for_two,
            "max_cost_for_two": sel.filters_used.max_cost_for_two,
            "limit": sel.filters_used.limit,
        },
        "candidates": [c.to_dict() for c in sel.candidates],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def _cmd_prompt(args: argparse.Namespace) -> int:
    try:
        req = _load_request(args.file)
    except (ValidationError, json.JSONDecodeError) as e:
        print(e, file=sys.stderr)
        return 1

    svc = Phase1DataService(Path(args.db_path))
    integ = IntegrationService(svc, top_k=args.top_k, fetch_limit=args.fetch_limit)
    sel = integ.select(req)
    messages = integ.build_llm_messages(req, selection=sel)
    out = {
        "had_strict_match": sel.had_strict_match,
        "relaxation_steps_applied": sel.relaxation_steps_applied,
        "candidate_count": len(sel.candidates),
        "messages": messages,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 — integration (select + prompt)")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="SQLite DB from Phase 1 ingest",
    )
    common.add_argument(
        "-f",
        "--file",
        type=Path,
        help="JSON file for RecommendationRequest (default: stdin)",
    )
    common.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    common.add_argument("--fetch-limit", type=int, default=DEFAULT_FETCH_LIMIT)

    sel_p = sub.add_parser("select", parents=[common], help="Select candidates + relaxation trace")
    sel_p.set_defaults(func=_cmd_select)

    pr_p = sub.add_parser("prompt", parents=[common], help="Select + build LLM chat messages JSON")
    pr_p.set_defaults(func=_cmd_prompt)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
