#!/usr/bin/env python3
"""Build ``data/restaurants_cloud.db`` for Streamlit / deploy (trimmed sample)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "restaurants.db"
DST = ROOT / "data" / "restaurants_cloud.db"
MAX_ROWS = 12_000
MAX_EXTRAS_STR = 256


def _trim_extras(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    out: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, str):
            if len(value) > MAX_EXTRAS_STR:
                out[key] = value[:MAX_EXTRAS_STR] + "…"
            else:
                out[key] = value
        elif isinstance(value, (list, dict)):
            if len(json.dumps(value)) <= MAX_EXTRAS_STR:
                out[key] = value
        else:
            text = str(value)
            if len(text) <= MAX_EXTRAS_STR:
                out[key] = value
    return json.dumps(out) if out else None


def main() -> int:
    if not SRC.is_file():
        print(f"Missing source DB: {SRC}. Run Phase 1 ingest first.", file=sys.stderr)
        return 1

    if DST.exists():
        DST.unlink()

    conn_src = sqlite3.connect(SRC)
    conn_dst = sqlite3.connect(DST)
    try:
        schema = conn_src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='restaurants'"
        ).fetchone()[0]
        conn_dst.execute(schema)
        for (idx_sql,) in conn_src.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='restaurants'"
        ):
            if idx_sql:
                conn_dst.execute(idx_sql)

        rows = conn_src.execute(
            """
            SELECT id, name, location, cuisines_pipe, cuisines_json, cost_for_two,
                   aggregate_rating, votes, establishment_type, extras_json
            FROM restaurants
            ORDER BY aggregate_rating DESC, votes DESC
            LIMIT ?
            """,
            (MAX_ROWS,),
        ).fetchall()

        trimmed = []
        for row in rows:
            r = list(row)
            r[9] = _trim_extras(r[9])
            trimmed.append(tuple(r))

        conn_dst.executemany(
            "INSERT INTO restaurants VALUES (?,?,?,?,?,?,?,?,?,?)",
            trimmed,
        )
        conn_dst.commit()
    finally:
        conn_src.close()
        conn_dst.close()

    size_mb = DST.stat().st_size / (1024 * 1024)
    print(f"Wrote {len(trimmed)} rows to {DST} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
