/** Bundled fallback when FastAPI is unreachable (e.g. BACKEND_URL not set on Vercel). */
export type ApiMetadata = {
  locations: string[];
  cuisines_by_location: Record<string, string[]>;
};

export const API_METADATA_PATH = "/api-metadata.json";

export async function loadApiMetadata(): Promise<ApiMetadata> {
  const res = await fetch(API_METADATA_PATH, { cache: "force-cache" });
  if (!res.ok) {
    throw new Error("Could not load bundled location metadata.");
  }
  return (await res.json()) as ApiMetadata;
}
