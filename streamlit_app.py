"""
Streamlit entrypoint for Community Cloud (backend / demo UI).

Set in the Streamlit app settings:
  Main file path: streamlit_app.py

Secrets (Streamlit Cloud → Settings → Secrets), e.g.:
  GROQ_API_KEY = "gsk_..."
  # Optional: hosted SQLite (restaurants.db is not in git — ~678 MB)
  # RESTAURANTS_DB_URL = "https://.../restaurants.db"
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

import streamlit as st

# Repo root on PYTHONPATH so `from src.phases...` works without `pip install -e .`
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _apply_streamlit_secrets() -> None:
    """Map Streamlit secrets into os.environ for Phase 4 / DB paths."""
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "GROQ_BASE_URL", "RESTAURANTS_DB_PATH", "RESTAURANTS_DB_URL"):
        if key in os.environ:
            continue
        try:
            value = st.secrets[key]
        except Exception:
            continue
        os.environ[key] = str(value)


def _ensure_database(db_path: Path) -> Path:
    """Use local DB, or download once from RESTAURANTS_DB_URL / st.secrets."""
    if db_path.is_file():
        return db_path

    url = os.environ.get("RESTAURANTS_DB_URL", "").strip()
    if not url:
        return db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    cache_key = f"db_downloaded_{hash(url)}"
    if not st.session_state.get(cache_key):
        with st.spinner("Downloading restaurant database (first run)…"):
            urllib.request.urlretrieve(url, db_path)  # noqa: S310 — URL from operator secrets
        st.session_state[cache_key] = True
    return db_path


def _db_path() -> Path:
    from src.phases.phase1.config import resolve_sqlite_path

    path = resolve_sqlite_path()
    return _ensure_database(path)


@st.cache_resource
def _phase1_service():
    from src.phases.phase1 import Phase1DataService

    return Phase1DataService(_db_path())


def main() -> None:
    st.set_page_config(page_title="Restaurant recommendations", layout="wide")
    _apply_streamlit_secrets()

    from src.phases.phase4.env import load_project_dotenv

    load_project_dotenv()

    st.title("AI restaurant recommendations")
    st.caption("Streamlit backend — ranked recommendations via Groq (Phase 4–5).")

    db = _db_path()
    groq_ok = bool(os.environ.get("GROQ_API_KEY", "").strip())

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Database", "ready" if db.is_file() else "missing")
    with col2:
        st.metric("Groq API key", "set" if groq_ok else "missing")

    if not db.is_file():
        st.error(
            "Restaurant database not found. The app expects `data/restaurants_cloud.db` "
            "(bundled sample) or a full `data/restaurants.db` after Phase 1 ingest. "
            "You can also set `RESTAURANTS_DB_PATH` or `RESTAURANTS_DB_URL` in Streamlit secrets."
        )
        st.stop()

    if db.name == "restaurants_cloud.db":
        st.info("Using bundled sample database (12k restaurants). For the full dataset, run Phase 1 ingest locally.")

    if not groq_ok:
        st.warning("Add `GROQ_API_KEY` in Streamlit **Settings → Secrets** (or project `.env` locally).")

    svc = _phase1_service()
    locations = svc.list_locations()
    location_default = locations[0] if locations else ""

    with st.form("preferences"):
        if locations:
            location = st.selectbox("Location", options=locations)
        else:
            location = st.text_input("Location", value=location_default)
        cuisine = st.text_input("Cuisine (optional)")
        min_rating = st.slider("Minimum rating", 0.0, 5.0, 3.5, 0.5)
        budget_amount = st.number_input(
            "Max cost for two (INR, 0 = no cap)",
            min_value=0.0,
            max_value=500_000.0,
            value=1500.0,
            step=100.0,
        )
        additional = st.text_area("Additional preferences (optional)", max_chars=2000)
        submitted = st.form_submit_button("Get recommendations", type="primary")

    if not submitted:
        st.info("Submit the form to run the full pipeline (filter → Groq rank → explain).")
        return

    if not location.strip():
        st.error("Location is required.")
        return

    from pydantic import ValidationError

    from src.phases.phase2.dto import RecommendationRequest
    from src.phases.phase5.service import run_ranked_recommendation

    try:
        req = RecommendationRequest(
            location=location.strip() if isinstance(location, str) else str(location),
            budget_amount=float(budget_amount),
            cuisine=cuisine.strip() or None,
            min_rating=float(min_rating),
            additional_preferences=additional.strip() or None,
        )
    except ValidationError as e:
        st.error("Invalid input")
        st.json(e.errors())
        return

    with st.spinner("Ranking restaurants…"):
        try:
            result = run_ranked_recommendation(req, db_path=db)
        except Exception as exc:
            st.exception(exc)
            return

    if result.summary:
        st.subheader("Summary")
        st.write(result.summary)

    st.subheader(f"Top picks ({len(result.items)})")
    for item in result.items:
        with st.container(border=True):
            st.markdown(f"**#{item.rank} — {item.name}**")
            st.caption(
                f"Rating: {item.rating if item.rating is not None else '—'} · "
                f"Cost for two: {item.cost if item.cost is not None else '—'} · "
                f"{', '.join(item.cuisines)}"
            )
            st.write(item.explanation)

    st.caption(result.disclaimer)
    if result.used_llm_fallback:
        st.warning("LLM unavailable — results ordered by rating (deterministic fallback).")


main()
