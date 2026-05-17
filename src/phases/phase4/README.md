# Phase 4 — Recommendation engine (Groq)

Calls **Groq** using the **OpenAI-compatible** Python client (`base_url=https://api.groq.com/openai/v1`). Loads secrets via `python-dotenv`: repository **`.env`**, then optional **`src/phases/phase4/.env`** (non-overriding), then optional **`apikey.env`** in the same folder.

## Environment (`.env`)

```env
GROQ_API_KEY=gsk_...
# optional:
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

See **`.env.example`** in the repo root. Never commit a real `.env`.

## Public API

| Symbol | Role |
|--------|------|
| `load_project_dotenv()` | Load `.env` once from repo root. |
| `LLMUserContext(messages=…)` | Wrapper for Phase 3 chat `messages`. |
| `rank_and_explain(candidates, user_context, client=…, model=…)` | Groq chat → parse JSON → validate ids; **retries** with backoff; **deterministic fallback** if key missing, API errors, or invalid JSON. |
| `GroqRecommendationEngine` | Reuses one client for multiple calls. |
| `parse_ranked_json` | Parse / validate model output. |
| `deterministic_rank_and_explain` | Rating/votes fallback (same `RankedRecommendations` shape). |
| `to_phase5_payload` | `{ summary?, items, used_llm_fallback }` for Phase 5. |

## CLI

```bash
# Full path: selection + prompt + Groq + merged output (needs .env + DB)
python -m src.phases.phase4.cli recommend -f request.json --db-path data/restaurants.db

# No LLM call — inspect messages only
python -m src.phases.phase4.cli recommend -f request.json --dry-run
```

## Modules

- `config.py` — env keys, defaults, retry counts  
- `env.py` — dotenv loader  
- `engine.py` — Groq client + `rank_and_explain`  
- `parse.py` — JSON + id allowlist  
- `fallback.py` — deterministic ordering  
- `enrich.py` — merge ranks with `RestaurantRecord` dicts  
- `cli.py` — `recommend` command  
