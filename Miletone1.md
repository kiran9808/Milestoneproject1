# Milestone 1 — AI-Powered Restaurant Recommendation System

Workflow for an AI-powered restaurant recommendation service (Zomato-inspired use case).

## Workflow

1. **Data ingestion** — Load and preprocess the Zomato-style dataset (Hugging Face).
2. **User input** — Collect location, budget, cuisine, rating, and free-text preferences.
3. **Integration layer** — Filter candidates and assemble the LLM prompt.
4. **Recommendation engine** — Rank and explain results via the LLM (Groq).
5. **Output display** — Present ranked recommendations with AI-generated explanations.

---

## Deployment

| Layer | Platform | Responsibility |
|-------|----------|----------------|
| **Backend** | **Streamlit** | Host the recommendation service (API / app logic, data pipeline integration, LLM calls). |
| **Frontend** | **Vercel** | Host the web UI that consumes the backend and displays recommendations. |

**Notes:**

- Configure backend secrets (e.g. `GROQ_API_KEY`) in the Streamlit deployment environment, not in source control.
- Point the Vercel frontend at the deployed Streamlit backend URL (environment variable for API base URL).
- Use separate staging and production deployments on each platform when ready for release.
