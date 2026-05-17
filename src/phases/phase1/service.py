"""Orchestrates ingest and exposes ``get_candidates`` for later phases."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import storage
from .config import DEFAULT_DATASET_VERSION_PATH, DEFAULT_SQLITE_PATH
from .ingestion import iter_hf_rows
from .preprocess import raw_row_to_restaurant
from .schema import DatasetVersionInfo, RestaurantRecord, SearchFilters


class Phase1DataService:
    """Internal module boundary: ``get_candidates(filters) -> list[RestaurantRecord]``."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_SQLITE_PATH)

    def ingest_from_hf(
        self,
        *,
        dataset_name: str | None = None,
        split: str | None = None,
        revision: str | None = None,
        streaming: bool = False,
        replace: bool = True,
        version_path: Path | None = None,
    ) -> DatasetVersionInfo:
        """
        Load Hugging Face rows, normalize, and bulk-write SQLite.

        If ``replace`` is True, existing restaurant rows are cleared first.
        """
        from .config import HF_DATASET_NAME, HF_DEFAULT_SPLIT

        name = dataset_name or HF_DATASET_NAME
        sp = split or HF_DEFAULT_SPLIT

        conn = storage._connect(self.db_path)
        row_count = 0
        try:
            storage.init_schema(conn)
            if replace:
                storage.clear_restaurants(conn)

            batch: list[RestaurantRecord] = []
            for idx, raw in enumerate(
                iter_hf_rows(name, sp, revision=revision, streaming=streaming)
            ):
                rec = raw_row_to_restaurant(raw, row_index=idx)
                if rec is None:
                    continue
                batch.append(rec)
                if len(batch) >= 2000:
                    storage.insert_restaurants(conn, batch)
                    batch.clear()
            if batch:
                storage.insert_restaurants(conn, batch)

            row_count = int(conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0])
        finally:
            conn.close()

        info = DatasetVersionInfo(
            dataset_name=name,
            revision=revision,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            row_count=row_count,
            split=sp,
        )
        storage.write_dataset_version(version_path or DEFAULT_DATASET_VERSION_PATH, info)
        return info

    def get_candidates(self, filters: SearchFilters) -> list[RestaurantRecord]:
        conn = storage._connect(self.db_path)
        try:
            storage.init_schema(conn)
            return storage.get_candidates(conn, filters)
        finally:
            conn.close()

    def list_locations(self) -> list[str]:
        """Distinct locations in the store (sorted), for demo UI dropdowns."""
        conn = storage._connect(self.db_path)
        try:
            storage.init_schema(conn)
            return storage.list_distinct_locations(conn)
        finally:
            conn.close()

    def list_cuisine_tags(self, location: str | None = None) -> list[str]:
        """Distinct cuisine tags (sorted), optionally scoped to one area for UI dropdowns."""
        conn = storage._connect(self.db_path)
        try:
            storage.init_schema(conn)
            return storage.list_distinct_cuisine_tags(conn, location=location)
        finally:
            conn.close()
