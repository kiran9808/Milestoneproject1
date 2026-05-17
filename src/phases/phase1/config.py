"""Phase 1 configuration: Hugging Face dataset id and default storage paths."""

from __future__ import annotations

import os
from pathlib import Path

# Dataset from architecture / Miletone1.md
HF_DATASET_NAME: str = "ManikaSaini/zomato-restaurant-recommendation"
HF_DEFAULT_SPLIT: str = "train"

# Paths relative to repository root (parent of `src/`)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATA_DIR: Path = _PROJECT_ROOT / "data"
DEFAULT_SQLITE_PATH: Path = DEFAULT_DATA_DIR / "restaurants.db"
# Trimmed DB for Streamlit / deploy (~12k rows, committed to git)
DEFAULT_CLOUD_SQLITE_PATH: Path = DEFAULT_DATA_DIR / "restaurants_cloud.db"
DEFAULT_DATASET_VERSION_PATH: Path = DEFAULT_DATA_DIR / "dataset_version.json"

# Serving default from architecture (bounded candidate list before LLM)
DEFAULT_CANDIDATE_LIMIT: int = 100

ENV_DB_PATH: str = "RESTAURANTS_DB_PATH"


def resolve_sqlite_path() -> Path:
    """
    Pick the active SQLite file: explicit env, full local ingest DB, or cloud sample.
    """
    raw = os.environ.get(ENV_DB_PATH, "").strip()
    if raw:
        return Path(raw)
    if DEFAULT_SQLITE_PATH.is_file():
        return DEFAULT_SQLITE_PATH
    return DEFAULT_CLOUD_SQLITE_PATH
