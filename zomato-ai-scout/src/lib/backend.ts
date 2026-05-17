/** Same-origin prefix proxied to FastAPI via `next.config` rewrites (local / Vercel). */
export const BACKEND_PROXY_PREFIX = "/api/py";

/** Streamlit demo UI (not the REST API). Set in Vercel env. */
export const STREAMLIT_APP_URL =
  process.env.NEXT_PUBLIC_STREAMLIT_APP_URL?.replace(/\/$/, "") ?? "";

/**
 * Build a URL for FastAPI (`/locations`, `/cuisines`, `/recommendations/ranked`).
 * Uses the Vercel rewrite proxy unless `NEXT_PUBLIC_BACKEND_URL` is set.
 */
export function backendPath(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const direct = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "");
  if (direct) {
    return `${direct}${p}`;
  }
  return `${BACKEND_PROXY_PREFIX}${p}`;
}
