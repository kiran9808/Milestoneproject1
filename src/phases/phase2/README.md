# Phase 2 — User input collection

Implements `RecommendationRequest` (Pydantic), validation rules from the architecture doc, mapping to Phase 1 `SearchFilters`, REST `POST /recommendations`, optional `Idempotency-Key` header (logged), and a CLI.

## Request JSON

```json
{
  "location": "Bangalore",
  "budget": "medium",
  "cuisine": "Chinese",
  "min_rating": 4.0,
  "additional_preferences": "Family-friendly, quick service"
}
```

- `budget`: `"low"` | `"medium"` | `"high"` — mapped to `min_cost_for_two` / `max_cost_for_two` in `config.py`.
- `additional_preferences`: optional, capped length; carried in API responses for Phase 3 prompts (not used in Phase 1 SQL yet).

## Validate without server

```bash
echo '{"location":"Delhi","budget":"low","min_rating":3.5}' | python -m src.phases.phase2.cli validate
```

## Run API

Ensure Phase 1 ingest has created `data/restaurants.db` (or set `RESTAURANTS_DB_PATH`).

```bash
export RESTAURANTS_DB_PATH=/absolute/path/to/restaurants.db   # optional
python -m src.phases.phase2.cli serve --host 127.0.0.1 --port 8000
```

`POST http://127.0.0.1:8000/recommendations` with JSON body; optional header `Idempotency-Key`.

## Modules

| File | Role |
|------|------|
| `config.py` | Budget bands, field length limits |
| `dto.py` | `RecommendationRequest`, `RecommendationResponse` |
| `location_normalize.py` | Whitespace + small city synonym map |
| `mapping.py` | `recommendation_request_to_search_filters` |
| `api.py` | FastAPI app (`create_app`, module `app`) |
| `cli.py` | `validate`, `serve` |
