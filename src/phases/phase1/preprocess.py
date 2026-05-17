"""Normalize raw Hugging Face / CSV-style rows into RestaurantRecord."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .schema import RestaurantRecord


def _norm_key(key: str) -> str:
    s = key.strip().lower()
    s = s.replace("(", "_").replace(")", "_")
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map original column names to snake_case keys."""
    return {_norm_key(str(k)): v for k, v in row.items()}


def _first_present(flat: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        nk = _norm_key(k)
        if nk in flat and flat[nk] is not None and str(flat[nk]).strip() != "":
            return flat[nk]
    return None


def _parse_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "-", "--", "new", "not rated"}:
        return None
    s = re.sub(r"[₹$,]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _parse_rating(val: Any) -> float | None:
    """
    Dataset ``rate`` is often ``4.1/5``; also accepts plain numbers and ``aggregate_rating``.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "-", "--", "new", "not rated"}:
        return None
    if "/" in s:
        left = s.split("/", 1)[0].strip()
        return _parse_float(left)
    return _parse_float(s)


def _parse_int(val: Any) -> int | None:
    f = _parse_float(val)
    if f is None:
        return None
    return int(round(f))


def _split_cuisines(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    s = str(raw).strip()
    if not s:
        return ()
    parts = re.split(r"[,/|]", s)
    out: list[str] = []
    for p in parts:
        t = p.strip()
        if t:
            out.append(t)
    return tuple(out)


def _normalize_location(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val).strip())


def _normalize_cuisines_for_index(cuisines: tuple[str, ...]) -> str:
    """Pipe-separated lowercase string for SQL LIKE / index-friendly storage."""
    if not cuisines:
        return ""
    return "|".join(c.lower() for c in cuisines)


def _stable_id(name: str, location: str, row_index: int | None) -> str:
    base = f"{name}|{location}|{row_index if row_index is not None else ''}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def raw_row_to_restaurant(
    row: dict[str, Any],
    *,
    row_index: int | None = None,
) -> RestaurantRecord | None:
    """
    Convert one dataset row to RestaurantRecord, or None if unusable.

    Supports common Zomato-style column aliases used on Hugging Face mirrors.
    """
    flat = _flatten_row(row)

    name = _first_present(flat, "restaurant_name", "name", "restaurant name")
    if name is None:
        return None
    name = str(name).strip()
    if not name:
        return None

    loc_raw = _first_present(
        flat,
        "city",
        "location",
        "listed_in_city",
        "listed in city",
        "area",
    )
    location = _normalize_location(loc_raw)
    if not location:
        return None

    rid = _first_present(flat, "restaurant_id", "id", "restaurant id")
    rid_str: str
    if rid is not None and str(rid).strip():
        rid_str = str(rid).strip()
    else:
        rid_str = _stable_id(name, location, row_index)

    cuisines_raw = _first_present(flat, "cuisines", "cuisine")
    cuisines = _split_cuisines(cuisines_raw)

    cost = _first_present(
        flat,
        "approx_cost_for_two_people",
        "average_cost_for_two",
        "cost",
        "average cost for two",
        "cost_for_two",
    )
    cost_for_two = _parse_float(cost)

    rating = _first_present(
        flat,
        "aggregate_rating",
        "rating",
        "rate",
        "aggregate rating",
        "aggregate_rating_given_by_customers",
    )
    aggregate_rating = _parse_rating(rating)

    votes = _parse_int(_first_present(flat, "votes", "no_of_votes"))

    est = _first_present(
        flat,
        "restaurant_type",
        "listed_in_type",
        "listed in type",
        "establishment_type",
    )
    establishment_type = str(est).strip() if est is not None else None

    excluded_flat_keys = {
        "restaurant_id",
        "id",
        "restaurant_name",
        "name",
        "city",
        "location",
        "listed_in_city",
        "area",
        "cuisines",
        "cuisine",
        "approx_cost_for_two_people",
        "average_cost_for_two",
        "cost",
        "aggregate_rating",
        "rating",
        "rate",
        "votes",
        "restaurant_type",
        "listed_in_type",
        "establishment_type",
    }
    extras: dict[str, Any] = {}
    for k, v in flat.items():
        if k in excluded_flat_keys:
            continue
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        try:
            json.dumps(v)
            extras[k] = v
        except TypeError:
            extras[k] = str(v)

    return RestaurantRecord(
        id=rid_str,
        name=name,
        location=location,
        cuisines=cuisines,
        cost_for_two=cost_for_two,
        aggregate_rating=aggregate_rating,
        votes=votes,
        establishment_type=establishment_type,
        extras=extras,
    )


def restaurant_cuisine_index_value(record: RestaurantRecord) -> str:
    return _normalize_cuisines_for_index(record.cuisines)
