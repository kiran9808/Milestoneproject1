"use client";

import { type ReactNode, useEffect, useState } from "react";
import {
  ChevronDown,
  Loader2,
  MapPin,
  Sparkles,
  Star,
  StarHalf,
  UtensilsCrossed,
} from "lucide-react";
import { loadApiMetadata } from "@/lib/api-metadata";
import { backendPath } from "@/lib/backend";
import type { RankedRecommendationsPayload } from "@/lib/ranked-types";

const MAX_CUISINE_LEN = 80;

function cuisinePayload(value: string): string | null {
  const t = value.trim();
  if (!t) return null;
  return t.length > MAX_CUISINE_LEN ? t.slice(0, MAX_CUISINE_LEN) : t;
}

async function parseErrorMessage(res: Response): Promise<string> {
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("text/html")) {
    return (
      "API returned HTML instead of JSON. Set Vercel BACKEND_URL to your FastAPI host " +
      "(Render), not the Streamlit app URL."
    );
  }
  if (ct.includes("application/json")) {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((e: { msg?: string }) => e.msg)
        .filter(Boolean)
        .join("; ");
    }
  }
  return res.statusText || `HTTP ${res.status}`;
}

export function RecommendationEngine() {
  const [location, setLocation] = useState("");
  const [locations, setLocations] = useState<string[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(true);
  const [locationsError, setLocationsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadLocations() {
      setLocationsLoading(true);
      setLocationsError(null);
      try {
        const res = await fetch(backendPath("/locations"));
        if (res.ok) {
          const data = (await res.json()) as { locations?: string[] };
          const list = Array.isArray(data.locations) ? data.locations : [];
          if (!cancelled) setLocations(list);
          return;
        }
        if (res.status === 404 || res.status === 503 || res.status === 502) {
          const meta = await loadApiMetadata();
          if (!cancelled) setLocations(meta.locations);
          return;
        }
        throw new Error(await parseErrorMessage(res));
      } catch (e) {
        try {
          const meta = await loadApiMetadata();
          if (!cancelled) {
            setLocations(meta.locations);
            return;
          }
        } catch {
          /* use primary error below */
        }
        if (!cancelled)
          setLocationsError(
            e instanceof Error ? e.message : "Could not load locations.",
          );
      } finally {
        if (!cancelled) setLocationsLoading(false);
      }
    }

    void loadLocations();
    return () => {
      cancelled = true;
    };
  }, []);

  const [cuisine, setCuisine] = useState("");
  const [cuisineOptions, setCuisineOptions] = useState<string[]>([]);
  const [cuisinesLoading, setCuisinesLoading] = useState(false);
  const [cuisinesError, setCuisinesError] = useState<string | null>(null);

  useEffect(() => {
    const loc = location.trim();
    if (!loc) {
      setCuisineOptions([]);
      setCuisinesLoading(false);
      setCuisinesError(null);
      return;
    }

    let cancelled = false;
    setCuisine("");
    setCuisinesLoading(true);
    setCuisinesError(null);

    async function loadCuisines() {
      try {
        const q = new URLSearchParams({ location: loc });
        const res = await fetch(
          `${backendPath("/cuisines")}?${q.toString()}`,
        );
        if (res.ok) {
          const data = (await res.json()) as { cuisines?: string[] };
          const raw = Array.isArray(data.cuisines) ? data.cuisines : [];
          const unique = [...new Set(raw.map((c) => c.trim()).filter(Boolean))];
          unique.sort((a, b) => a.localeCompare(b));
          if (!cancelled) setCuisineOptions(unique);
          return;
        }
        if (res.status === 404 || res.status === 503 || res.status === 502) {
          const meta = await loadApiMetadata();
          const raw = meta.cuisines_by_location[loc] ?? [];
          if (!cancelled) setCuisineOptions(raw);
          return;
        }
        throw new Error(await parseErrorMessage(res));
      } catch (e) {
        try {
          const meta = await loadApiMetadata();
          if (!cancelled) {
            setCuisineOptions(meta.cuisines_by_location[loc] ?? []);
            return;
          }
        } catch {
          /* use primary error below */
        }
        if (!cancelled)
          setCuisinesError(
            e instanceof Error ? e.message : "Could not load cuisines.",
          );
      } finally {
        if (!cancelled) setCuisinesLoading(false);
      }
    }

    void loadCuisines();
    return () => {
      cancelled = true;
    };
  }, [location]);

  const [budgetAmount, setBudgetAmount] = useState("800");
  const [minRating, setMinRating] = useState(4.5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RankedRecommendationsPayload | null>(
    null,
  );

  async function submit() {
    setError(null);
    setResult(null);
    const loc = location.trim();
    if (!loc) {
      setError("Please choose a location from the list.");
      return;
    }

    const budgetVal = Number(budgetAmount);
    if (!Number.isFinite(budgetVal) || budgetVal < 0) {
      setError("Please enter a valid numeric budget.");
      return;
    }

    setLoading(true);
    try {
      const body = {
        location: loc,
        budget_amount: budgetVal,
        cuisine: cuisinePayload(cuisine),
        min_rating: minRating,
        additional_preferences: null as string | null,
      };

      const res = await fetch(backendPath("/recommendations/ranked"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        setError(await parseErrorMessage(res));
        return;
      }

      const data = (await res.json()) as RankedRecommendationsPayload;
      setResult(data);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Could not reach the API. Set BACKEND_URL on Vercel to your FastAPI (Render) URL.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="scout" className="relative z-20 mx-auto max-w-7xl px-5 pb-24 -mt-32">
      <div className="rounded-xl border border-outline-variant/30 bg-surface p-6 shadow-lg sm:p-8 ai-glow md:rounded-2xl">
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-4 border-b border-outline-variant pb-6 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="font-heading text-2xl font-bold text-on-surface">
                AI Recommendation Engine
              </h2>
              <p className="mt-1 text-on-surface-variant">
                Set your preferences and let our Scout find the perfect match.
              </p>
            </div>
            <div className="flex gap-2 text-primary">
              <UtensilsCrossed className="size-6 shrink-0" aria-hidden />
              <Sparkles className="size-6 shrink-0" aria-hidden />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="location-select"
                className="text-sm font-bold text-on-surface-variant"
              >
                Location
              </label>
              <div className="relative">
                <MapPin className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-on-surface-variant" />
                <select
                  id="location-select"
                  className="w-full appearance-none rounded-lg border-none bg-surface-container py-3 pl-10 pr-10 text-base outline-none ring-primary focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={locationsLoading || !!locationsError}
                  aria-busy={locationsLoading}
                >
                  <option value="">
                    {locationsLoading
                      ? "Loading locations…"
                      : locationsError
                        ? "Could not load locations"
                        : "Choose a location…"}
                  </option>
                  {locations.map((locItem) => (
                    <option key={locItem} value={locItem}>
                      {locItem}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-5 -translate-y-1/2 text-on-surface-variant" />
              </div>
              <p className="text-xs text-on-surface-variant">
                Unique areas from your ingested dataset (exact DB strings).
              </p>
              {locationsError ? (
                <p className="text-xs text-red-600" role="alert">
                  {locationsError}{" "}
                  <button
                    type="button"
                    className="font-semibold underline"
                    onClick={() => window.location.reload()}
                  >
                    Retry
                  </button>
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-2">
              <label
                htmlFor="budget-amount"
                className="text-sm font-bold text-on-surface-variant"
              >
                Budget
              </label>
              <input
                id="budget-amount"
                className="w-full rounded-lg border-none bg-surface-container py-3 pl-4 pr-4 text-base outline-none ring-primary focus:ring-2"
                value={budgetAmount}
                onChange={(e) => setBudgetAmount(e.target.value)}
                type="number"
                min={0}
                step={50}
                inputMode="numeric"
                placeholder="e.g. 800"
              />
              <p className="text-xs text-on-surface-variant">
                Enter approximate cost for two (numeric).
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <label
                htmlFor="cuisine-select"
                className="text-sm font-bold text-on-surface-variant"
              >
                Cuisine
              </label>
              <div className="relative">
                <UtensilsCrossed className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-on-surface-variant" />
                <select
                  id="cuisine-select"
                  className="w-full appearance-none rounded-lg border-none bg-surface-container py-3 pl-10 pr-10 text-base outline-none ring-primary focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
                  disabled={
                    !location.trim() ||
                    cuisinesLoading ||
                    !!cuisinesError
                  }
                  aria-busy={cuisinesLoading}
                >
                  <option value="">
                    {!location.trim()
                      ? "Choose a location first…"
                      : cuisinesLoading
                        ? "Loading cuisines…"
                        : cuisinesError
                          ? "Could not load cuisines"
                          : "Any cuisine (optional)"}
                  </option>
                  {cuisineOptions.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-5 -translate-y-1/2 text-on-surface-variant" />
              </div>
              <p className="text-xs text-on-surface-variant">
                Tags available at the selected location only (same scope as search).
              </p>
              {cuisinesError ? (
                <p className="text-xs text-red-600" role="alert">
                  {cuisinesError}{" "}
                  <button
                    type="button"
                    className="font-semibold underline"
                    onClick={() => window.location.reload()}
                  >
                    Retry
                  </button>
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-bold text-on-surface-variant">
                Min Rating
              </label>
              <div className="flex flex-col gap-2 rounded-lg bg-surface-container px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-heading text-xl font-semibold">
                    {minRating}
                  </span>
                  <RatingStars value={minRating} />
                </div>
                <input
                  type="range"
                  min={0}
                  max={5}
                  step={0.5}
                  value={minRating}
                  onChange={(e) => setMinRating(Number(e.target.value))}
                  className="w-full accent-primary"
                  aria-label="Minimum rating"
                />
              </div>
            </div>
          </div>

          <div className="mt-2 flex flex-col items-center gap-4">
            <button
              type="button"
              disabled={loading}
              onClick={submit}
              className="group flex items-center gap-3 rounded-lg bg-primary px-10 py-4 font-heading text-lg font-semibold text-on-primary shadow-lg shadow-primary/25 transition-transform enabled:hover:scale-[1.02] enabled:active:scale-95 disabled:opacity-60"
            >
              {loading ? (
                <Loader2 className="size-6 animate-spin" aria-hidden />
              ) : (
                <Sparkles
                  className="size-6 transition-transform group-hover:rotate-12"
                  aria-hidden
                />
              )}
              {loading ? "Scouting…" : "Get Recommendation"}
            </button>
          </div>

          {error ? (
            <div
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900"
            >
              {error}
            </div>
          ) : null}

          {result ? (
            <div className="space-y-4 border-t border-outline-variant pt-8">
              {result.selection?.cross_location_fallback ? (
                <div
                  role="status"
                  className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-center text-sm text-amber-950"
                >
                  No listings matched your cuisine in{" "}
                  <strong>
                    {result.selection.expanded_from_location ?? location}
                  </strong>
                  . Below are venues in <strong>other areas</strong> that still match your
                  cuisine (filters may be relaxed).
                </div>
              ) : null}
              {result.summary ? (
                <p className="text-center text-on-surface-variant">
                  {result.summary}
                </p>
              ) : null}
              {result.items?.length ? (
                <ul className="grid gap-4 sm:grid-cols-2">
                  {result.items.map((item) => (
                    <li
                      key={item.id}
                      className="rounded-xl border border-outline-variant/40 bg-white p-5 shadow-sm"
                    >
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <span className="font-heading text-lg font-semibold text-on-surface">
                          {item.rank}. {item.name}
                        </span>
                        {item.rating != null ? (
                          <span className="shrink-0 rounded bg-surface-container px-2 py-0.5 text-xs font-bold text-primary">
                            ★ {item.rating.toFixed(1)}
                          </span>
                        ) : null}
                      </div>
                      <p className="mb-2 text-xs text-on-surface-variant">
                        {item.location ? (
                          <>
                            <span className="font-medium text-on-surface">
                              {item.location}
                            </span>
                            {" · "}
                          </>
                        ) : null}
                        {item.cuisines.join(" · ")}
                        {item.cost != null ? ` · ~₹${item.cost}` : ""}
                      </p>
                      <p className="text-sm leading-relaxed text-on-surface">
                        {item.explanation}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-center text-sm text-on-surface-variant">
                  No ranked picks returned for these filters.
                </p>
              )}
              {result.disclaimer ? (
                <p className="text-center text-xs text-on-surface-variant">
                  {result.disclaimer}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function RatingStars({ value }: { value: number }) {
  const nodes: ReactNode[] = [];
  let remaining = value;
  for (let i = 0; i < 5; i += 1) {
    if (remaining >= 1) {
      nodes.push(
        <Star key={i} className="size-6 fill-primary text-primary" />,
      );
      remaining -= 1;
    } else if (remaining >= 0.5) {
      nodes.push(
        <StarHalf key={i} className="size-6 fill-primary text-primary" />,
      );
      remaining = 0;
    } else {
      nodes.push(
        <Star
          key={i}
          className="size-6 fill-transparent text-primary/35"
          strokeWidth={1.5}
        />,
      );
    }
  }
  return (
    <div className="flex items-center" aria-hidden>
      {nodes}
    </div>
  );
}
