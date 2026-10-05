from datetime import UTC, date, datetime, timedelta
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import UUID4, ConfigDict, Field, model_validator

from mealie.schema._mealie import MealieModel
from mealie.schema._mealie.mealie_model import CookingSource

DEFAULT_WINDOW_DAYS = 365
MAX_WINDOW_DAYS = 1827


class CookingInsightsQuery(MealieModel):
    start_date: date | None = None
    end_date: date | None = None
    time_zone: str = "UTC"
    include_inferred: bool = False
    limit: int = Field(default=10, ge=1, le=50)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def resolve_window(self) -> Self:
        try:
            zone = ZoneInfo(self.time_zone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("timeZone must be a valid IANA time zone") from error
        today = datetime.now(UTC).astimezone(zone).date()
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("startDate and endDate must be supplied together")
        if self.start_date is None or self.end_date is None:
            self.end_date = today
            self.start_date = today - timedelta(days=DEFAULT_WINDOW_DAYS - 1)
        if self.end_date > today or self.start_date > self.end_date:
            raise ValueError("Dates must be ordered and endDate must not be in the future")
        if (self.end_date - self.start_date).days >= MAX_WINDOW_DAYS:
            raise ValueError(f"The inclusive window cannot exceed {MAX_WINDOW_DAYS} days")
        return self


class CookingInsightRecipe(MealieModel):
    id: UUID4
    slug: str
    name: str
    image: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CookingInsightItem(MealieModel):
    recipe: CookingInsightRecipe
    cooking_days: int = 0
    recorded_days: int = 0
    inferred_only_days: int = 0
    last_cooking_date: date | None = None
    last_cooking_source: CookingSource | None = None
    days_since_last_cooking: int | None = None
    rating: float | None = None
    is_favorite: bool = False
    years_observed: int = 0
    reason: Literal["neglected_favorite", "recurring_month", "liked_recipe"] | None = None
    no_recorded_history: bool = False
    includes_inferred_activity: bool = False


class CookingInsightCollection(MealieModel):
    items: list[CookingInsightItem] = Field(default_factory=list)
    total: int = 0
    truncated: bool = False


class CookingMonthHabit(MealieModel):
    month: int
    cooking_days: int = 0
    active_dates: int = 0
    recurring_recipes: CookingInsightCollection = Field(default_factory=CookingInsightCollection)


class CookingInsightsCoverage(MealieModel):
    first_cooking_date: date | None = None
    has_unclassified_events: bool = False
    cooking_days: int = 0
    active_dates: int = 0
    recorded_days: int = 0
    inferred_only_days: int = 0
    sufficient_seasonal_history: bool = False


class CookingInsightsResponse(MealieModel):
    filters: CookingInsightsQuery
    coverage: CookingInsightsCoverage
    frequent_meals: CookingInsightCollection
    neglected_favorites: CookingInsightCollection
    favorites_without_history: CookingInsightCollection
    recommendations: CookingInsightCollection
    monthly_habits: list[CookingMonthHabit]
