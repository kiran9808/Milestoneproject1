"""Phase 2 limits and budget-to-cost bands (aligned with Zomato-style cost for two, INR)."""

from __future__ import annotations

from enum import Enum


class BudgetBand(str, Enum):
    """User-facing budget tier from Miletone1 / architecture."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Average cost for two: (min_inclusive, max_inclusive); None = open bound
# Tuned for typical Indian Zomato-style ranges; adjust if your dataset differs.
BUDGET_COST_FOR_TWO: dict[BudgetBand, tuple[float | None, float | None]] = {
    BudgetBand.LOW: (None, 600.0),
    BudgetBand.MEDIUM: (400.0, 1500.0),
    BudgetBand.HIGH: (1200.0, None),
}

MAX_LOCATION_LEN: int = 128
MAX_CUISINE_LEN: int = 80
MIN_RATING: float = 0.0
MAX_RATING: float = 5.0
MAX_ADDITIONAL_PREFERENCES_LEN: int = 2000

# Upper bound for ``RecommendationRequest.budget_amount`` (cost for two, INR).
MAX_BUDGET_AMOUNT_FOR_TWO: float = 500_000.0
