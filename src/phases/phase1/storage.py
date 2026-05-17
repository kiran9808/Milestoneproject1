"""SQLite storage with indexes for location, rating, and cost (Phase 1)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .preprocess import raw_row_to_restaurant, restaurant_cuisine_index_value
from .schema import DatasetVersionInfo, RestaurantRecord, SearchFilters


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            cuisines_pipe TEXT NOT NULL,
            cuisines_json TEXT NOT NULL,
            cost_for_two REAL,
            aggregate_rating REAL,
            votes INTEGER,
            establishment_type TEXT,
            extras_json TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_rest_loc_rating
            ON restaurants (location, aggregate_rating DESC);
        CREATE INDEX IF NOT EXISTS idx_rest_loc_cost
            ON restaurants (location, cost_for_two);
        CREATE INDEX IF NOT EXISTS idx_rest_loc_cuisines
            ON restaurants (location, cuisines_pipe);
        """
    )
    conn.commit()


def clear_restaurants(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM restaurants")
    conn.commit()


def insert_restaurants(conn: sqlite3.Connection, records: Iterable[RestaurantRecord]) -> int:
    rows = []
    for r in records:
        rows.append(
            (
                r.id,
                r.name,
                r.location,
                restaurant_cuisine_index_value(r),
                json.dumps(list(r.cuisines)),
                r.cost_for_two,
                r.aggregate_rating,
                r.votes,
                r.establishment_type,
                json.dumps(r.extras) if r.extras else None,
            )
        )
    conn.executemany(
        """
        INSERT OR REPLACE INTO restaurants (
            id, name, location, cuisines_pipe, cuisines_json,
            cost_for_two, aggregate_rating, votes, establishment_type, extras_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def row_to_record(row: sqlite3.Row) -> RestaurantRecord:
    cuisines = tuple(json.loads(row["cuisines_json"]))
    extras_raw = row["extras_json"]
    extras = json.loads(extras_raw) if extras_raw else {}
    return RestaurantRecord(
        id=row["id"],
        name=row["name"],
        location=row["location"],
        cuisines=cuisines,
        cost_for_two=row["cost_for_two"],
        aggregate_rating=row["aggregate_rating"],
        votes=row["votes"],
        establishment_type=row["establishment_type"],
        extras=extras,
    )


def get_candidates(conn: sqlite3.Connection, filters: SearchFilters) -> list[RestaurantRecord]:
    """
    Read-optimized path: filter by location, rating, optional cuisine substring and cost band.

    If ``filters.location`` is blank/None, no equality on ``location`` is applied (all areas).
    ``exclude_location`` removes one area (pair with open ``location`` for "elsewhere" search).

    Hard cap on rows via ``filters.limit`` (architecture: 50–100 typical before LLM).
    """
    limit = max(1, min(filters.limit, 500))

    cuisine_term: str | None = None
    if filters.cuisine and filters.cuisine.strip():
        cuisine_term = filters.cuisine.strip().lower()

    sql = """
        SELECT * FROM restaurants
        WHERE (aggregate_rating IS NULL OR aggregate_rating >= ?)
    """
    params: list[object] = [filters.min_rating]

    loc = (filters.location or "").strip()
    if loc:
        sql += " AND lower(location) = lower(?)"
        params.append(loc)

    excl = (filters.exclude_location or "").strip()
    if excl:
        sql += " AND lower(location) != lower(?)"
        params.append(excl)

    if cuisine_term is not None:
        # Pipe-separated lowercase segments (see ``restaurant_cuisine_index_value``). Match a
        # whole cuisine tag so "American" does not match "North American" as a substring,
        # and "Indian" does not match "South Indian" unless that tag exists as its own segment.
        sql += " AND ('|' || cuisines_pipe || '|') LIKE ?"
        params.append(f"%|{cuisine_term}|%")

    if filters.max_cost_for_two is not None:
        sql += " AND (cost_for_two IS NULL OR cost_for_two <= ?)"
        params.append(filters.max_cost_for_two)

    if filters.min_cost_for_two is not None:
        sql += " AND (cost_for_two IS NULL OR cost_for_two >= ?)"
        params.append(filters.min_cost_for_two)

    sql += """
        ORDER BY
            CASE WHEN aggregate_rating IS NULL THEN 1 ELSE 0 END,
            aggregate_rating DESC,
            CASE WHEN votes IS NULL THEN 1 ELSE 0 END,
            votes DESC
        LIMIT ?
    """
    params.append(limit)

    cur = conn.execute(sql, params)
    return [row_to_record(r) for r in cur.fetchall()]


def list_distinct_locations(conn: sqlite3.Connection) -> list[str]:
    """All unique ``location`` values, sorted case-insensitively (for UI dropdowns)."""
    cur = conn.execute(
        "SELECT DISTINCT location FROM restaurants ORDER BY location COLLATE NOCASE"
    )
    return [str(row[0]) for row in cur.fetchall() if row[0]]


def list_distinct_cuisine_tags(
    conn: sqlite3.Connection, location: str | None = None
) -> list[str]:
    """
    Unique cuisine labels (from ``cuisines_json``), sorted A–Z case-insensitive.

    If ``location`` is set, only restaurants in that area are considered — this keeps UI
    dropdown options aligned with what ``get_candidates`` can return for that location.

    Multi-label cells are split at ingest; each tag appears once in the list.
    """
    loc = (location or "").strip()
    if loc:
        cur = conn.execute(
            "SELECT cuisines_json FROM restaurants WHERE lower(location) = lower(?)",
            (loc,),
        )
    else:
        cur = conn.execute("SELECT cuisines_json FROM restaurants")
    seen: set[str] = set()
    out: list[str] = []
    for (raw,) in cur.fetchall():
        if not raw:
            continue
        try:
            tags = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(tags, list):
            continue
        for t in tags:
            if not isinstance(t, str):
                continue
            s = t.strip()
            if not s:
                continue
            norm = s.casefold()
            if norm in seen:
                continue
            seen.add(norm)
            out.append(s)
    out.sort(key=lambda x: x.casefold())
    return out


def write_dataset_version(path: Path, info: DatasetVersionInfo) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset_name": info.dataset_name,
        "revision": info.revision,
        "ingested_at": info.ingested_at,
        "row_count": info.row_count,
        "split": info.split,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
