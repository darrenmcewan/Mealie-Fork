from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from mealie.repos.repository_cooking_history import CookingHistoryBounds, CookingHistoryEvent, CookingHistoryPreference
from mealie.schema.user.cooking_insights import CookingInsightRecipe, CookingInsightsQuery
from mealie.services.recipe.cooking_insights_service import calculate_insights, utc_window


def test_insights_query_defaults_and_bounds():
    query = CookingInsightsQuery(timeZone="America/Los_Angeles")
    assert query.end_date == datetime.now(UTC).astimezone(ZoneInfo(query.time_zone)).date()
    assert query.start_date == query.end_date - timedelta(days=364)
    assert query.limit == 10
    assert not query.include_inferred
    assert query.model_dump(by_alias=True)["timeZone"] == "America/Los_Angeles"
    assert (
        CookingInsightsQuery(startDate=query.end_date - timedelta(days=1826), endDate=query.end_date, limit=50).limit
        == 50
    )


@pytest.mark.parametrize(
    "values",
    [
        {"startDate": "2020-01-01"},
        {"endDate": "2020-01-01"},
        {"startDate": "2020-02-01", "endDate": "2020-01-01"},
        {"startDate": "2020-01-01", "endDate": "2025-01-01"},
        {"startDate": "9999-01-01", "endDate": "9999-01-02"},
        {"timeZone": "Invalid/Zone"},
        {"timeZone": "../UTC"},
        {"limit": 0},
        {"limit": 51},
        {"userId": "someone-else"},
        {"groupId": "someone-else"},
        {"queryFilter": "user_id = someone-else"},
    ],
)
def test_insights_query_rejects_invalid_values(values: dict):
    with pytest.raises(ValidationError):
        CookingInsightsQuery.model_validate(values)


def insight_result(records=(), preferences=(), has_unclassified=False, **filters):
    query = CookingInsightsQuery.model_validate({"startDate": "2024-01-01", "endDate": "2024-12-31", **filters})
    events = [
        CookingHistoryEvent(
            UUID(int=identifier, version=4), datetime.fromisoformat(timestamp).replace(tzinfo=UTC), source
        )
        for identifier, timestamp, source in records
    ]
    _, end = utc_window(query)
    sources = {"manual", "mealplan"} if query.include_inferred else {"manual"}
    bounds = []
    for recipe_id in {event.recipe_id for event in events}:
        eligible = [
            event
            for event in events
            if event.recipe_id == recipe_id and event.source in sources and event.timestamp < end
        ]
        if eligible:
            bounds.append(
                CookingHistoryBounds(
                    recipe_id,
                    min(event.timestamp for event in eligible),
                    max((event.timestamp for event in eligible if event.source == "manual"), default=None),
                    max((event.timestamp for event in eligible if event.source == "mealplan"), default=None),
                )
            )
    ratings = [
        CookingHistoryPreference(UUID(int=identifier, version=4), rating, favorite)
        for identifier, rating, favorite in preferences
    ]
    return calculate_insights(
        query,
        events,
        bounds,
        ratings,
        has_unclassified,
        lambda ids: {
            recipe_id: CookingInsightRecipe(id=recipe_id, slug=str(recipe_id), name=str(recipe_id)) for recipe_id in ids
        },
    )


def test_repeat_counts_and_source_precedence():
    records = [
        (1, "2024-03-01", "manual"),
        (1, "2024-03-01", "manual"),
        (1, "2024-03-01", "mealplan"),
        (1, "2024-03-02", "mealplan"),
        (2, "2024-03-01", "manual"),
        (2, "2024-03-02", "manual"),
        (2, "2024-03-03", None),
    ]
    recorded = insight_result(records)
    assert recorded.coverage.cooking_days == 3
    assert recorded.frequent_meals.total == 1
    inferred = insight_result(records, includeInferred=True)
    assert inferred.coverage.cooking_days == 4
    assert inferred.coverage.recorded_days == 3
    assert inferred.coverage.inferred_only_days == 1
    assert [item.recipe.id.int & 0xFFF for item in inferred.frequent_meals.items] == [1, 2]
    assert inferred.frequent_meals.items[0].last_cooking_source == "mealplan"


def test_neglect_and_missing_history_are_distinct():
    response = insight_result(
        [(1, "2024-12-01", "manual"), (2, "2024-12-02", "manual"), (3, "2023-12-01", "manual")],
        [(1, 4, True), (2, 5, True), (3, 3, True), (4, None, True)],
        has_unclassified=True,
    )
    assert [item.days_since_last_cooking for item in response.neglected_favorites.items] == [396, 30]
    assert len(response.favorites_without_history.items) == 1
    assert response.favorites_without_history.items[0].days_since_last_cooking is None
    assert response.coverage.has_unclassified_events


def test_recommendations_reject_recent_and_poor_ratings():
    response = insight_result(
        [(1, "2024-12-25", "manual"), (2, "2024-12-24", "manual")],
        [(1, 5, True), (2, 4, False), (3, 2, True), (4, float("nan"), True), (5, 6, False), (6, 4, False)],
    )
    assert [item.recipe.id.int & 0xFFF for item in response.recommendations.items] == [4, 2, 6]
    assert response.recommendations.items[0].rating is None
    assert response.recommendations.items[0].no_recorded_history
    assert insight_result().recommendations.total == 0


def test_totals_are_not_truncated_with_items():
    records = [(identifier, day, "manual") for identifier in range(1, 5) for day in ("2024-03-01", "2024-03-02")]
    response = insight_result(records, limit=1)
    assert response.frequent_meals.total == 4
    assert response.frequent_meals.truncated
    assert len(response.frequent_meals.items) == 1
    assert response.coverage.cooking_days == 8
    assert len(response.monthly_habits) == 12
    assert response.monthly_habits[2].active_dates == 2
    assert not response.coverage.sufficient_seasonal_history


@pytest.mark.parametrize("zone, days", [("UTC", 1), ("America/Los_Angeles", 0), ("Asia/Kathmandu", 1)])
def test_local_calendar_boundaries(zone: str, days: int):
    response = insight_result([(1, "2024-01-01T00:30:00", "manual")], timeZone=zone)
    assert response.coverage.cooking_days == days


def test_dst_midnight_bounds_and_end_of_day():
    query = CookingInsightsQuery(startDate="2024-03-10", endDate="2024-03-10", timeZone="America/Los_Angeles")
    start, end = utc_window(query)
    assert (end - start).total_seconds() == 23 * 3600
    today = datetime.now(UTC).date()
    query = CookingInsightsQuery(startDate=today, endDate=today)
    recipe_id = UUID(int=1, version=4)
    timestamp = datetime.combine(today, datetime.max.time(), tzinfo=UTC)
    response = calculate_insights(
        query,
        [CookingHistoryEvent(recipe_id, timestamp, "manual")],
        [CookingHistoryBounds(recipe_id, timestamp, timestamp, None)],
        [],
        False,
        lambda ids: {},
    )
    assert response.coverage.cooking_days == 1


def test_seasonal_recurrence_and_recommendation_evidence():
    records = [(1, "2023-10-01", "manual"), (1, "2024-10-01", "manual")]
    records += [(2, f"2023-12-{day:02}", "manual") for day in range(1, 11)]
    response = insight_result(records, [(1, 4.5, False), (2, 4, True)], startDate="2022-10-01", endDate="2024-10-20")
    assert response.coverage.sufficient_seasonal_history
    october = response.monthly_habits[9]
    assert october.cooking_days == 2
    assert october.recurring_recipes.items[0].years_observed == 2
    assert [item.reason for item in response.recommendations.items] == ["neglected_favorite", "recurring_month"]
    assert response.recommendations.items[1].years_observed == 2
    assert response.recommendations.items[1].cooking_days == 2
    sparse = insight_result(records[:2], [(1, 5, False)], startDate="2022-10-01", endDate="2024-10-20")
    assert not sparse.coverage.sufficient_seasonal_history
    assert sparse.monthly_habits[9].cooking_days == 2
    assert sparse.monthly_habits[9].recurring_recipes.total == 0


def test_repeat_recency_and_leap_day():
    records = [
        (1, "2024-02-28", "manual"),
        (1, "2024-02-29", "manual"),
        (2, "2024-02-28", "manual"),
        (2, "2024-03-01", "manual"),
    ]
    response = insight_result(records)
    assert [item.recipe.id.int & 0xFFF for item in response.frequent_meals.items] == [2, 1]
    assert response.monthly_habits[1].cooking_days == 3


def test_last_date_prefers_manual_over_inferred_same_day():
    records = [(1, "2023-12-01T08:00:00", "manual"), (1, "2023-12-01T22:00:00", "mealplan")]
    response = insight_result(records, [(1, 5, True)], includeInferred=True)
    assert response.neglected_favorites.items[0].last_cooking_source == "manual"
    assert response.neglected_favorites.items[0].cooking_days == 0
