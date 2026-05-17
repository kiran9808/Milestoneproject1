/** Subset of Phase 5 `RankedRecommendationsResponse` used by the UI. */

export type RankedItem = {
  id: string;
  name: string;
  location?: string | null;
  cuisines: string[];
  rating: number | null;
  cost: number | null;
  explanation: string;
  rank: number;
  relevance_score: number | null;
};

export type RankedSelectionMeta = {
  had_strict_match: boolean;
  relaxation_steps_applied?: string[];
  cross_location_fallback?: boolean;
  expanded_from_location?: string | null;
};

export type RankedRecommendationsPayload = {
  summary?: string | null;
  items: RankedItem[];
  disclaimer?: string;
  used_llm_fallback?: boolean;
  idempotency_key?: string | null;
  selection?: RankedSelectionMeta | null;
};
