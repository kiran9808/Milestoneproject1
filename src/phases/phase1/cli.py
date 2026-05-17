"""CLI entrypoint for Phase 1 ingest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_SQLITE_PATH
from .service import Phase1DataService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 — dataset ingest")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Load HF dataset into SQLite")
    ingest.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="SQLite database path",
    )
    ingest.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Override Hugging Face dataset id",
    )
    ingest.add_argument(
        "--split",
        type=str,
        default=None,
        help="Dataset split (default: train)",
    )
    ingest.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Optional HF dataset git revision",
    )
    ingest.add_argument(
        "--streaming",
        action="store_true",
        help="Stream rows (lower memory; slower for counting)",
    )
    ingest.add_argument(
        "--append",
        action="store_true",
        help="Append without clearing existing rows",
    )

    args = parser.parse_args(argv)

    if args.command == "ingest":
        svc = Phase1DataService(db_path=args.db_path)
        info = svc.ingest_from_hf(
            dataset_name=args.dataset,
            split=args.split,
            revision=args.revision,
            streaming=args.streaming,
            replace=not args.append,
        )
        print(f"Ingested {info.row_count} rows into {args.db_path}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
