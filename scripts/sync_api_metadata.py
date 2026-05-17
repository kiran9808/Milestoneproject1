#!/usr/bin/env python3
"""Write ``zomato-ai-scout/public/api-metadata.json`` from the cloud SQLite DB."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "restaurants_cloud.db"
OUT = ROOT / "zomato-ai-scout" / "public" / "api-metadata.json"


def main() -> int:
    if not DB.is_file():
        print(f"Missing {DB}. Run scripts/build_cloud_db.py first.", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB)
    locations = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT location FROM restaurants ORDER BY location COLLATE NOCASE"
        )
    ]
    cuisines_by_location: dict[str, list[str]] = {}
    for loc in locations:
        cur = conn.execute(
            "SELECT cuisines_json FROM restaurants WHERE lower(location)=lower(?)",
            (loc,),
        )
        seen: set[str] = set()
        tags: list[str] = []
        for (raw,) in cur.fetchall():
            if not raw:
                continue
            for t in json.loads(raw):
                if isinstance(t, str) and t.strip():
                    key = t.strip().casefold()
                    if key not in seen:
                        seen.add(key)
                        tags.append(t.strip())
        tags.sort(key=lambda x: x.casefold())
        cuisines_by_location[loc] = tags
    conn.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"locations": locations, "cuisines_by_location": cuisines_by_location}),
        encoding="utf-8",
    )
    print(f"Wrote {OUT} ({len(locations)} locations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
