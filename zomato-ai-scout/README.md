# Zomato AI Scout (Next.js frontend)

Phase 5 UI for the restaurant recommendation system. Talks to the **FastAPI** REST API (not the Streamlit app URL).

## Local development

From this directory:

```bash
npm install
npm run dev
```

This starts FastAPI on `http://127.0.0.1:8000` and Next.js on `http://localhost:3000`. API calls use `/api/py/*` proxies.

Copy env template:

```bash
cp .env.example .env.local
```

## Deploy frontend on Vercel

1. Import the GitHub repo **Milestoneproject1** on [Vercel](https://vercel.com/new).
2. Set **Root Directory** to `zomato-ai-scout`.
3. Deploy the **REST API** first (see below) and copy its URL.
4. In Vercel → **Settings → Environment Variables** (then **Redeploy**):

| Variable | Value |
|----------|--------|
| `BACKEND_URL` | `https://YOUR-API.onrender.com` (no trailing slash) — required for **Get Recommendation** |
| `NEXT_PUBLIC_STREAMLIT_APP_URL` | `https://milestoneproject1-amob2aaxond6fjnqzp2oih.streamlit.app` (optional) |

5. Redeploy the frontend after saving env vars.

**Locations / cuisines** load from bundled `public/api-metadata.json` if `BACKEND_URL` is missing. **Ranked recommendations** still need a live FastAPI `BACKEND_URL`.

> **Important:** `BACKEND_URL` must be the **FastAPI** service (`/health`, `/locations`, `/recommendations/ranked`). The Streamlit URL is a separate Python UI and cannot serve those JSON endpoints.

### Deploy REST API on Render (free)

From the repository root on GitHub:

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → connect **Milestoneproject1**.
2. Apply `render.yaml` (service `milestoneproject1-api`).
3. Set **GROQ_API_KEY** in the Render service environment.
4. After deploy, use the Render URL as `BACKEND_URL` in Vercel (e.g. `https://milestoneproject1-api.onrender.com`).

Health check: `GET https://YOUR-API.onrender.com/health` → `{"status":"ok"}`.

## Architecture

| Layer | Platform | URL role |
|-------|----------|----------|
| Frontend | Vercel | Next.js UI |
| REST API | Render (or local) | JSON for the frontend |
| Python UI | Streamlit Cloud | Standalone demo / admin |
