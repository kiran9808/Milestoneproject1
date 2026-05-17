# AI-Powered Restaurant Recommendation System — Phase-Wise Architecture

This document expands the requirements in `Miletone1.md` into a structured, phase-wise technical architecture for an AI-powered restaurant recommendation service (Zomato-inspired use case).

---

## 1. Executive Summary

The system combines **structured restaurant data** (Zomato-style dataset from Hugging Face) with an **LLM** to produce **ranked, explainable** recommendations from **user preferences** (location, budget, cuisine, rating, and free-text constraints). Architecture is organized so that **deterministic filtering** reduces candidate sets and cost, while the **LLM** handles ranking, rationale, and natural-language summarization.

---

## 2. High-Level System Architecture

```mermaid
flowchart TB
  subgraph Phase_Data["Phase 1 — Data"]
    HF[Hugging Face Dataset]
    ETL[Load / Preprocess / Index]
    Store[(Structured Store + Search Index)]
    HF --> ETL --> Store
  end

  subgraph Phase_Input["Phase 2 — User Input"]
    UI[Web / API Client]
    API[Preference API]
    UI --> API
  end

  subgraph Phase_Integration["Phase 3 — Integration"]
    Filter[Filter & Candidate Selection]
    Prompt[Prompt Builder]
    API --> Filter
    Store --> Filter
    Filter --> Prompt
  end

  subgraph Phase_LLM["Phase 4 — Recommendation Engine"]
    LLM[Groq API (chat completions)]
    Prompt --> LLM
  end

  subgraph Phase_Output["Phase 5 — Output"]
    Parse[Response Parse & Validate]
    Present[Presentation Layer]
    LLM --> Parse --> Present
    Present --> UI
  end

  subgraph Phase_Ops["Phase 6 — Quality & Operations"]
    Obs[Logging / Metrics]
    Test[Tests & Evals]
    Filter -.-> Obs
    LLM -.-> Obs
  end

  subgraph Deployment["Deployment"]
    BE[Backend — Streamlit]
    FE[Frontend — Vercel]
    Present --> BE
    UI --> FE
    FE -->|API calls| BE
  end
```

**Core principle:** Narrow the restaurant universe with **structured filters** first; send only a **bounded candidate list** (with key fields) to the LLM for **ranking and explanations**, keeping latency and token usage predictable.

**Deployment:** The **backend** is deployed on **Streamlit**; the **frontend** is deployed on **Vercel** (see [Deployment](#8-deployment) and `Miletone1.md`).

---

## 3. Phase Definitions

### Phase 0 — Foundation & Non-Functional Baseline

| Aspect | Description |
|--------|-------------|
| **Goals** | Agree on scope, success metrics, and constraints (latency budget, cost per recommendation, supported cities). |
| **Deliverables** | Requirements checklist, definition of “top N” recommendations, error-handling policy (empty results, LLM failure). |
| **Architecture decisions** | Monolith vs. split services; sync API vs. async job for heavy batches; **Groq** as the LLM provider (Phase 4) and model tier; secrets loaded from **`.env`** (see Phase 4). |

**Outcomes:** A thin **architecture decision record (ADR)** set or equivalent notes so later phases do not rework fundamentals.

---

### Phase 1 — Data Ingestion & Storage

**Source:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on Hugging Face.

| Layer | Responsibility |
|-------|----------------|
| **Ingestion** | Download or stream dataset; version the snapshot used in production. |
| **Preprocessing** | Normalize location strings; map budget to numeric or enum bands aligned with dataset “cost” fields; split multi-label cuisines; coerce ratings to a consistent scale; drop or impute invalid rows with explicit rules. |
| **Schema** | Canonical internal model: `id`, `name`, `location` (city/area), `cuisines[]`, `cost_for_two` or equivalent, `aggregate_rating`, optional `votes`, `establishment_type`, free-text fields if present. |
| **Storage** | File/DB for batch jobs; optional **search index** (e.g., inverted index on city + cuisine) or SQL with composite indexes for `(location, cuisine, rating, cost)`. |
| **Serving** | Read-optimized path for the integration layer: query by filters with a **hard cap** on rows returned (e.g., top 50–100 by rating/votes before LLM). |

**Interfaces:** Internal module or microservice: `get_candidates(filters) -> List[RestaurantRecord]`.

**Risks:** Messy location names and cuisine spelling variants → plan for **normalization maps** and fuzzy matching in Phase 3 if needed.

---

### Phase 2 — User Input Collection

| Component | Responsibility |
|-----------|----------------|
| **Input model** | Structured fields: `location`, `budget` (low/medium/high), `cuisine`, `min_rating`, plus optional `additional_preferences` (free text). |
| **Validation** | Enums for budget; min/max for rating; allowlist or normalization for location; length limits on free text. |
| **API surface** | REST or GraphQL endpoint, e.g. `POST /recommendations`, accepting JSON body; idempotency key optional for logging. |
| **Client** | Web form or CLI; display validation errors before calling downstream logic. |

**Interfaces:** `RecommendationRequest` DTO validated at the boundary; maps to internal `SearchFilters`.

---

### Phase 3 — Integration Layer (Filter + Prompt Assembly)

| Step | Description |
|------|-------------|
| **1. Filter** | Apply strict predicates: location match, cuisine overlap, rating ≥ minimum, cost band vs. budget. Sort by rating and/or popularity; **truncate** to `K` candidates (configurable). |
| **2. Empty / sparse handling** | If zero matches: relax rules in documented order (e.g., widen location → drop secondary cuisine) or return a structured “no exact match” with suggestions without calling the LLM. |
| **3. Prompt design** | System + user messages (or single structured prompt) including: user preferences verbatim; **tabular or JSON** list of candidates with only fields needed for ranking; instructions to output **JSON** (ranked ids, short explanations, optional summary). |
| **4. Safety** | Strip or neutralize obvious prompt-injection patterns in free-text preferences; cap token size of user-added text. |

**Interfaces:** `build_prompt(request, candidates) -> messages_or_string`; `select_candidates(filters) -> candidates`.

---

### Phase 4 — Recommendation Engine (LLM)

Phase 4 calls **[Groq](https://console.groq.com/)** for inference. Use Groq’s **OpenAI-compatible Chat Completions API** (base URL `https://api.groq.com/openai/v1`) so the Phase 3 `messages` payload maps cleanly to `POST /openai/v1/chat/completions`.

| Concern | Approach |
|---------|----------|
| **Provider** | **Groq API** for chat completions; pick a supported Groq model id (e.g. from Groq’s model list) and keep it configurable (env or config file). |
| **Authentication** | **API key in a `.env` file** at the project root (e.g. `GROQ_API_KEY=...`). The application must load `.env` at startup (e.g. `python-dotenv`) and **never** commit `.env` to version control; document a `.env.example` with placeholder variable names only. |
| **Tasks for the model** | Rank `K` candidates; assign **relevance scores** if useful; write **1–3 sentence explanations** per top item; optional **overall summary** of the shortlist. |
| **Model behavior** | Require **only restaurants from the provided list** (no hallucinated venues); JSON schema or regex-validated output. |
| **Resilience** | Retries with backoff; fallback: deterministic order by rating if Groq times out or returns an error. |
| **Cost control** | Small `K`, compact field list, appropriate Groq model tier for v1; cache identical `(filters hash, dataset version)` if product allows. |

**Interfaces:** `rank_and_explain(candidates, user_context) -> RankedRecommendations`.

**Configuration (summary):** `.env` holds `GROQ_API_KEY` (and optionally `GROQ_MODEL` or equivalent). Runtime code reads these after loading `.env`.

---

### Phase 5 — Output Display & API Contract

| Field (per item) | Source |
|------------------|--------|
| Restaurant name | Structured data |
| Cuisine | Structured data |
| Rating | Structured data |
| Estimated cost | Structured data (aligned with dataset) |
| AI explanation | LLM output merged by `id` |

**Presentation:** Card layout or list; show **disclaimer** that explanations are AI-generated; link or static map placeholder if no URLs in dataset.

**API response:** Stable JSON schema, e.g. `{ summary?, items: [{ id, name, cuisines, rating, cost, explanation, rank }] }`.

**Implementation status:**

- **Done (backend):** `POST /recommendations/ranked` serves the public contract: `summary?`, `items[]` (fields above, with `rating` / `cost` as the outward names for aggregate rating and cost-for-two), a fixed **`disclaimer`** string (AI-generated explanations), `used_llm_fallback`, and optional **`selection`** metadata (Phase 3 relaxation trace). Echoes `Idempotency-Key` when sent. Run the API via the same FastAPI app as Phase 2 (`create_app` / `uvicorn`).
- **Done (frontend - Next.js):** Next.js UI is the project frontend for Phase 5. It consumes `POST /recommendations/ranked`, renders card/list recommendations, and displays the AI disclaimer in-UI.
- **Optional later:** maps/links, richer styling, and accessibility polish in the Next.js frontend.

---

### Phase 6 — Quality, Observability, and Hardening

| Area | Actions |
|------|---------|
| **Testing** | Unit tests for filters and normalization; contract tests on LLM JSON parser; golden-file tests for prompt shape. |
| **Evaluation** | Spot-check explanations for faithfulness (only facts from candidate row); optional human rating of usefulness. |
| **Observability** | Structured logs: request id, filter counts, LLM latency, token usage, errors; metrics for empty-result rate. |
| **Security** | **Groq API key** only in **`.env`** (or deployment secrets manager in production), not in source; rate limiting on public API; PII minimization (this use case is low PII). |

---

## 4. Cross-Cutting Concerns

| Concern | Guidance |
|---------|----------|
| **Secrets (Groq)** | Store **`GROQ_API_KEY`** in **`.env`** at repo root; load with `python-dotenv` (or equivalent); add `.env` to `.gitignore`; ship **`.env.example`** without real keys. |
| **Dataset versioning** | Pin dataset revision; rebuild indexes on upgrade. |
| **Idempotency** | Same logical request may be retried; use request id in logs, not as a cache key unless product requires. |
| **Internationalization** | Phase 2+ if UI supports multiple languages; LLM prompts may need locale. |
| **Accessibility** | Semantic HTML, contrast, screen-reader friendly labels for ratings and costs. |

---

## 5. Suggested Technology Stack (Non-Binding)

| Layer | Example options |
|-------|-----------------|
| Runtime | Python (FastAPI) or Node (Express/Nest) |
| Data | Parquet + DuckDB/Pandas for offline; SQLite/Postgres for online |
| LLM | **Groq API** (OpenAI-compatible client); local via Ollama only if you add a dev override later |
| UI | **Next.js** (selected and implemented for this project) |
| **Backend deployment** | **Streamlit** (Streamlit Community Cloud or equivalent) |
| **Frontend deployment** | **Vercel** |

---

## 6. Phase Rollout Order (Implementation Sequence)

1. **Phase 0** — Scope and ADRs.  
2. **Phase 1** — Ingest, clean, expose `get_candidates`.  
3. **Phase 2** — API + validated request model.  
4. **Phase 3** — Filtering + prompt builder + empty-result policy.  
5. **Phase 4** — **Groq** LLM integration (key from **`.env`**) + parser + fallback.  
6. **Phase 5** — **Backend:** stable JSON API + disclaimer (`POST /recommendations/ranked`). **Frontend:** **Next.js UI** consuming the ranked API, with cards/list output and in-UI disclaimer.  
7. **Phase 6** — Tests, metrics, and iteration on prompts and filters.

---

## 7. Traceability to Original Workflow (`Miletone1.md`)

| Original workflow step | Primary architecture phase |
|------------------------|----------------------------|
| Data Ingestion | Phase 1 |
| User Input | Phase 2 |
| Integration Layer (filter + LLM prompt) | Phase 3 |
| Recommendation Engine (LLM rank + explain) | Phase 4 |
| Output Display | Phase 5 |
| Cross-cutting reliability and quality | Phase 6 |
| Deployment (backend Streamlit, frontend Vercel) | §8 Deployment; `Miletone1.md` |

---

## 8. Deployment

Aligned with `Miletone1.md`:

| Layer | Platform | Details |
|-------|----------|---------|
| **Backend** | **Streamlit** | Deploy the recommendation service (filtering, Groq integration, ranked API). Store secrets (`GROQ_API_KEY`, etc.) in Streamlit secrets / environment, not in the repo. |
| **Frontend** | **Vercel** | Deploy the Next.js UI. Set the public API base URL to the Streamlit backend endpoint via Vercel environment variables. |

**Operational checklist:**

1. Deploy backend to Streamlit and verify health (e.g. sample `POST /recommendations/ranked` or equivalent entrypoint).
2. Deploy frontend to Vercel with `NEXT_PUBLIC_API_URL` (or project equivalent) pointing at the Streamlit URL.
3. Smoke-test end-to-end: form submit → ranked cards → disclaimer visible.
4. Enable preview deployments on Vercel for PRs; use a separate Streamlit app or branch URL for staging when needed.

---

*Generated from `Miletone1.md` for planning and implementation handoff.*
