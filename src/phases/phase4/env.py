"""Load ``.env`` from project root (architecture: secrets in .env)."""

from __future__ import annotations

from pathlib import Path

from .config import _PROJECT_ROOT

_LOADED = False


def load_project_dotenv() -> None:
    """Load ``.env`` once from repository root (no-op if python-dotenv missing)."""
    global _LOADED
    if _LOADED:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        _LOADED = True
        return

    env_path = _PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()  # cwd fallback

    # Phase-local `.env` (e.g. `src/phases/phase4/.env`) — fills missing keys only.
    phase4_dotenv = _PROJECT_ROOT / "src" / "phases" / "phase4" / ".env"
    if phase4_dotenv.is_file():
        load_dotenv(phase4_dotenv, override=False)

    # Optional dev file (never overrides variables already set).
    alt = _PROJECT_ROOT / "src" / "phases" / "phase4" / "apikey.env"
    if alt.is_file():
        load_dotenv(alt, override=False)

    _LOADED = True


def project_root() -> Path:
    return _PROJECT_ROOT
