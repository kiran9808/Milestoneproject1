"""Normalize location strings; optional synonym map for common Indian cities."""

from __future__ import annotations

import re

# Keys must be lowercase; values are canonical spellings expected in the dataset / user input.
_LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "Bangalore",
    "blr": "Bangalore",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "noida": "Noida",
    "new delhi": "Delhi",
    "ncr": "Delhi",
}


def normalize_location(raw: str) -> str:
    """
    Collapse whitespace, strip, apply a small synonym map, title-case tokens.

    Dataset city names vary; Phase 1 queries are case-insensitive on location.
    """
    s = re.sub(r"\s+", " ", raw.strip())
    if not s:
        return ""
    key = s.lower()
    if key in _LOCATION_ALIASES:
        return _LOCATION_ALIASES[key]
    # Title-case heuristic for "New Delhi" style
    return " ".join(w.capitalize() for w in s.split())
