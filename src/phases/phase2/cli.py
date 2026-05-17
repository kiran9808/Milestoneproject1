"""CLI: run API server or validate a JSON request payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .dto import RecommendationRequest
from .mapping import recommendation_request_to_search_filters


def _cmd_validate(args: argparse.Namespace) -> int:
    raw: Any
    if args.file:
        raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
    else:
        raw = json.load(sys.stdin)

    try:
        req = RecommendationRequest.model_validate(raw)
    except ValidationError as e:
        print(json.dumps(e.errors(), indent=2))
        return 1

    filters = recommendation_request_to_search_filters(req)
    out = {
        "ok": True,
        "search_filters": {
            "location": filters.location,
            "min_rating": filters.min_rating,
            "cuisine": filters.cuisine,
            "min_cost_for_two": filters.min_cost_for_two,
            "max_cost_for_two": filters.max_cost_for_two,
            "limit": filters.limit,
        },
        "additional_preferences": req.additional_preferences,
    }
    print(json.dumps(out, indent=2))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "src.phases.phase2.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        # Avoid uvloop/httptools extras — matches Streamlit Cloud requirements.txt
        loop="asyncio",
        http="h11",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2 — preferences API / validation")
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Validate JSON and print SearchFilters mapping")
    val.add_argument(
        "--file",
        "-f",
        type=Path,
        help="JSON file (default: read stdin)",
    )
    val.set_defaults(func=_cmd_validate)

    srv = sub.add_parser("serve", help="Run REST API (uvicorn)")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--reload", action="store_true")
    srv.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
