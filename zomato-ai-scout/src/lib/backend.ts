/** Same-origin prefix proxied to FastAPI via `next.config` rewrites. */
export const BACKEND_PROXY_PREFIX = "/api/py";

export function backendPath(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${BACKEND_PROXY_PREFIX}${p}`;
}
