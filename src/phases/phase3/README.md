# Phase 3 — Integration layer

Implements the architecture: **filter + truncate**, **relaxation when empty**, **LLM prompt assembly**, and **sanitization** of free-text preferences.

## Public API

| Function / type | Role |
|-----------------|------|
| `select_candidates(svc, filters, top_k=…)` | Thin wrapper: Phase 1 fetch with pool size, truncate to `top_k`. |
| `select_candidates_with_relaxation(svc, filters, …)` | Strict query first; then **drop cuisine → ignore budget → lower min_rating** until rows appear or exhausted. |
| `build_prompt(request, candidates)` | Chat-style `messages` list: system rules + JSON user payload (preferences + compact candidates + JSON output schema). |
| `sanitize_preferences(text)` | Strip obvious injection patterns; cap length before prompt. |
| `IntegrationService` | `select(request)` and `build_llm_messages(request, selection=…)` for Phase 4. |

## Relaxation order

1. Strict filters (location, rating, cuisine, cost band from Phase 2 mapping).  
2. If empty: **drop cuisine** (if it was set).  
3. If still empty: **clear cost band** (ignore budget).  
4. If still empty: **lower `min_rating` by 1.0** repeatedly down to `0`.

**Location widening** (alternate spellings / metro) is not done automatically in SQL today; Phase 2 already normalizes a few synonyms. Extending Phase 1 queries (e.g. `IN` list of city names) would be the next step.

## CLI

```bash
# Candidates + trace (needs Phase 1 DB)
python -m src.phases.phase3.cli select -f request.json --db-path data/restaurants.db

# Same + LLM messages JSON
python -m src.phases.phase3.cli prompt -f request.json
```

## Module map

- `config.py` — pool / top-k / prompt text caps  
- `schema.py` — `CandidateSelectionResult`  
- `selection.py` — `select_candidates`, `select_candidates_with_relaxation`  
- `safety.py` — `sanitize_preferences`  
- `prompt.py` — `build_prompt`  
- `integration.py` — `IntegrationService`  
- `cli.py` — `select` / `prompt`  
