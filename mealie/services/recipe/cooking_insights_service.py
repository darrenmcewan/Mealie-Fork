import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import UUID4

from mealie.repos.repository_cooking_history import (
    CookingHistoryBounds,
    CookingHistoryEvent,
    CookingHistoryPreference,
    RepositoryCookingHistory,
)
from mealie.schema.recipe.recipe_timeline_events import CookingSource
from mealie.schema.user.cooking_insights import (
    CookingInsightCollection,
    CookingInsightItem,
    CookingInsightRecipe,
    CookingInsightsCoverage,
    CookingInsightsQuery,
    CookingInsightsResponse,
    CookingMonthHabit,
)

REPEAT_DAYS = 2
NEGLECT_DAYS = 30
RECENT_DAYS = 7
SEASONAL_WINDOW_DAYS = 730
SEASONAL_ACTIVE_DATES = 12


@dataclass
class RecipeCookingEvidence:
    recipe_id: UUID4
    days: dict[date, str] = field(default_factory=dict)
    last_date: date | None = None
    last_source: CookingSource | None = None
    gap: int | None = None
    rating: float | None = None
    favorite: bool = False
    years_observed: int = 0
    reason: Literal["neglected_favorite", "recurring_month", "liked_recipe"] | None = None

    @property
    def rating_order(self) -> float:
        return -(self.rating if self.rating is not None else -1)


def utc_window(query: CookingInsightsQuery) -> tuple[datetime, datetime]:
    assert query.start_date is not None and query.end_date is not None
    zone = ZoneInfo(query.time_zone)
    start = datetime.combine(query.start_date, time.min, tzinfo=zone)
    end = datetime.combine(query.end_date + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)


def calculate_insights(
    query: CookingInsightsQuery,
    events: Iterable[CookingHistoryEvent],
    bounds: Iterable[CookingHistoryBounds],
    preferences: Iterable[CookingHistoryPreference],
    has_unclassified: bool,
    load_recipes: Callable[[set[UUID4]], dict[UUID4, CookingInsightRecipe]],
) -> CookingInsightsResponse:
    assert query.start_date is not None and query.end_date is not None
    zone = ZoneInfo(query.time_zone)
    sources = {"manual", "mealplan"} if query.include_inferred else {"manual"}
    evidence: dict[UUID4, RecipeCookingEvidence] = {}
    first_dates: list[date] = []
    for record in events:
        if record.timestamp is None or record.source is None or record.source not in sources:
            continue
        local_date = record.timestamp.astimezone(zone).date()
        if not query.start_date <= local_date <= query.end_date:
            continue
        state = evidence.setdefault(record.recipe_id, RecipeCookingEvidence(record.recipe_id))
        if state.days.get(local_date) != "manual":
            state.days[local_date] = record.source
    for history in bounds:
        state = evidence.setdefault(history.recipe_id, RecipeCookingEvidence(history.recipe_id))
        available = []
        if history.manual_last is not None:
            available.append((history.manual_last.astimezone(zone).date(), CookingSource.manual))
        if query.include_inferred and history.inferred_last is not None:
            available.append((history.inferred_last.astimezone(zone).date(), CookingSource.mealplan))
        available = [(local_date, source) for local_date, source in available if local_date <= query.end_date]
        if available:
            state.last_date, state.last_source = max(
                available, key=lambda item: (item[0], item[1] == CookingSource.manual)
            )
            state.gap = (query.end_date - state.last_date).days
            first_dates.append(history.first.astimezone(zone).date())
    for preference in preferences:
        state = evidence.setdefault(preference.recipe_id, RecipeCookingEvidence(preference.recipe_id))
        state.favorite = preference.is_favorite
        if preference.rating is not None and math.isfinite(preference.rating) and 0 <= preference.rating <= 5:
            state.rating = preference.rating

    states = list(evidence.values())
    active_dates = {local_date for state in states for local_date in state.days}
    seasonal_ready = (
        (query.end_date - query.start_date).days + 1 >= SEASONAL_WINDOW_DAYS
        and len(active_dates) >= SEASONAL_ACTIVE_DATES
        and len({local_date.year for local_date in active_dates}) >= 2
    )
    frequent = sorted(
        [state for state in states if len(state.days) >= REPEAT_DAYS],
        key=lambda state: (-len(state.days), -max(state.days).toordinal(), str(state.recipe_id)),
    )
    neglected = sorted(
        [state for state in states if state.favorite and state.gap is not None and state.gap >= NEGLECT_DAYS],
        key=lambda state: (-(state.gap or 0), state.rating_order, str(state.recipe_id)),
    )
    unknown = sorted(
        [state for state in states if state.favorite and state.last_date is None],
        key=lambda state: (state.rating_order, str(state.recipe_id)),
    )
    monthly_entries: dict[int, list[RecipeCookingEvidence]] = {}
    monthly_active: dict[int, set[date]] = {}
    monthly_totals: dict[int, int] = {}
    for month in range(1, 13):
        entries = []
        month_dates: set[date] = set()
        count = 0
        for state in states:
            days = {local_date: source for local_date, source in state.days.items() if local_date.month == month}
            month_dates.update(days)
            count += len(days)
            years = {local_date.year for local_date in days}
            if seasonal_ready and len(years) >= 2:
                entries.append(replace(state, days=days, years_observed=len(years)))
        monthly_entries[month] = sorted(
            entries, key=lambda state: (-state.years_observed, -len(state.days), str(state.recipe_id))
        )
        monthly_active[month] = month_dates
        monthly_totals[month] = count
    recurring = {state.recipe_id: state for state in monthly_entries[query.end_date.month]}
    recommendations = []
    for state in states:
        reason: Literal["neglected_favorite", "recurring_month", "liked_recipe"]
        if state.rating is not None and state.rating < 3:
            continue
        if not state.favorite and (state.rating is None or state.rating < 4):
            continue
        if state.gap is not None and state.gap < RECENT_DAYS:
            continue
        if state.favorite and state.gap is not None and state.gap >= NEGLECT_DAYS:
            reason = "neglected_favorite"
        elif state.recipe_id in recurring:
            reason = "recurring_month"
        else:
            reason = "liked_recipe"
        supporting_state = recurring[state.recipe_id] if reason == "recurring_month" else state
        recommendations.append(replace(supporting_state, reason=reason))
    tiers = {"neglected_favorite": 0, "recurring_month": 1, "liked_recipe": 2}
    recommendations.sort(
        key=lambda state: (
            tiers[state.reason or "liked_recipe"],
            not state.favorite,
            state.rating_order,
            -(state.gap if state.gap is not None else -1),
            str(state.recipe_id),
        )
    )
    selections = [frequent, neglected, unknown, recommendations, *monthly_entries.values()]
    displayed_ids = {state.recipe_id for entries in selections for state in entries[: query.limit]}
    recipes = load_recipes(displayed_ids)

    def collection(entries: list[RecipeCookingEvidence]) -> CookingInsightCollection:
        items = []
        for state in entries[: query.limit]:
            if state.recipe_id not in recipes:
                continue
            recorded = sum(source == "manual" for source in state.days.values())
            inferred = len(state.days) - recorded
            items.append(
                CookingInsightItem(
                    recipe=recipes[state.recipe_id],
                    cooking_days=len(state.days),
                    recorded_days=recorded,
                    inferred_only_days=inferred,
                    last_cooking_date=state.last_date,
                    last_cooking_source=state.last_source,
                    days_since_last_cooking=state.gap,
                    rating=state.rating,
                    is_favorite=state.favorite,
                    years_observed=state.years_observed,
                    reason=state.reason,
                    no_recorded_history=state.last_date is None,
                    includes_inferred_activity=inferred > 0 or state.last_source == CookingSource.mealplan,
                )
            )
        return CookingInsightCollection(items=items, total=len(entries), truncated=len(entries) > query.limit)

    recorded_total = sum(source == "manual" for state in states for source in state.days.values())
    cooking_total = sum(len(state.days) for state in states)
    return CookingInsightsResponse(
        filters=query,
        coverage=CookingInsightsCoverage(
            first_cooking_date=min(first_dates) if first_dates else None,
            has_unclassified_events=has_unclassified,
            cooking_days=cooking_total,
            active_dates=len(active_dates),
            recorded_days=recorded_total,
            inferred_only_days=cooking_total - recorded_total,
            sufficient_seasonal_history=seasonal_ready,
        ),
        frequent_meals=collection(frequent),
        neglected_favorites=collection(neglected),
        favorites_without_history=collection(unknown),
        recommendations=collection(recommendations),
        monthly_habits=[
            CookingMonthHabit(
                month=month,
                cooking_days=monthly_totals[month],
                active_dates=len(monthly_active[month]),
                recurring_recipes=collection(monthly_entries[month]),
            )
            for month in range(1, 13)
        ],
    )


class CookingInsightsService:
    def __init__(self, repository: RepositoryCookingHistory, actor_id: UUID):
        if not isinstance(actor_id, UUID):
            raise ValueError("Cooking insights require an authenticated actor")
        self.repository = repository
        self.actor_id = actor_id

    def get(self, query: CookingInsightsQuery) -> CookingInsightsResponse:
        start, end = utc_window(query)
        sources = ["manual", "mealplan"] if query.include_inferred else ["manual"]
        return calculate_insights(
            query,
            self.repository.events(self.actor_id, start, end, sources),
            self.repository.bounds(self.actor_id, end, sources),
            self.repository.preferences(self.actor_id),
            self.repository.has_unclassified_events(self.actor_id),
            self.repository.recipes,
        )
