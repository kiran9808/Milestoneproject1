# Phase 1 — Data ingestion and storage

Implements the architecture doc: Hugging Face load, normalization, canonical `RestaurantRecord`, SQLite with indexes, version metadata, and `get_candidates(filters)`.

## Ingest

From the repository root (with ingest dependencies and network available):

```bash
pip install -e ".[ingest]"
python -m src.phases.phase1.cli ingest
```

Options: `--db-path`, `--dataset`, `--split`, `--revision`, `--streaming`, `--append`.

After ingest, `data/restaurants.db` and `data/dataset_version.json` are created by default.

## Query from code

```python
from pathlib import Path
from src.phases.phase1 import Phase1DataService, SearchFilters

svc = Phase1DataService(Path("data/restaurants.db"))
candidates = svc.get_candidates(
    SearchFilters(location="Bangalore", min_rating=4.0, cuisine="Chinese", limit=100)
)
```

## Layout

| Module        | Role                                      |
|---------------|-------------------------------------------|
| `config.py`   | Dataset id, paths, default candidate cap  |
| `schema.py`   | `RestaurantRecord`, `SearchFilters`       |
| `ingestion.py`| Hugging Face row iterator                 |
| `preprocess.py` | Row normalization and aliases          |
| `storage.py`  | SQLite schema, bulk insert, `get_candidates` |
| `service.py`  | `Phase1DataService` orchestration         |
| `cli.py`      | `ingest` command                            |
