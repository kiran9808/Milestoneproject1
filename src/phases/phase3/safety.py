"""Sanitize free-text preferences before they appear in LLM prompts (Phase 3)."""

from __future__ import annotations

import re

from .config import MAX_PREFERENCES_PROMPT_CHARS

# Obvious prompt-injection / role-breaking patterns (best-effort, not exhaustive).
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?is)\bignore\s+(all\s+)?(previous|prior)\s+instructions?\b"),
    re.compile(r"(?is)\bdisregard\s+(all\s+)?(previous|prior)\s+instructions?\b"),
    re.compile(r"(?is)\bforget\s+(all\s+)?(previous|prior)\s+instructions?\b"),
    re.compile(r"(?is)\byou\s+are\s+now\s+(a|an)\b"),
    re.compile(r"(?is)\bnew\s+instructions?\s*:"),
    re.compile(r"(?is)\boverride\s+(the\s+)?system\b"),
    re.compile(r"(?is)```\s*system"),
    re.compile(r"(?is)\[\s*INST\s*\]"),
)

_ROLE_LINE = re.compile(r"(?im)^(system|assistant|user)\s*:\s*")


def _neutralize_role_markers(s: str) -> str:
    return _ROLE_LINE.sub(lambda m: f"[{m.group(1)}]:", s)


def sanitize_preferences(text: str | None) -> str:
    """
    Strip or neutralize obvious prompt-injection patterns and cap length.

    Returns a safe string (possibly empty) suitable for embedding in user content.
    """
    if not text:
        return ""
    s = text.strip()
    for pat in _INJECTION_PATTERNS:
        s = pat.sub("[removed]", s)
    s = _neutralize_role_markers(s)
    s = s[:MAX_PREFERENCES_PROMPT_CHARS]
    return s.strip()
