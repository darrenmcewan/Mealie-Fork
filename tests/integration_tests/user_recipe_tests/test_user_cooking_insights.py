from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, update

from mealie.db.models.users import User
from mealie.db.models.recipe.recipe_timeline import RecipeTimelineEvent
from mealie.repos.repository_cooking_history import RepositoryCookingHistory
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_timeline_events import RecipeTimelineEventCreate
from mealie.schema.user.cooking_insights import CookingInsightsQuery
from mealie.schema.user.user import UserRatingCreate
from mealie.services.recipe.cooking_insights_service import CookingInsightsService
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser

INSIGHTS_URL = "/api/users/self/cooking-insights"


def test_repository_history_scope(api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser):
    own = unique_user.repos.recipes.create(
        Recipe(
            name=random_string(),
            user_id=unique_user.user_id,
            group_id=unique_user.group_id,
            household_id=unique_user.household_id,
        )
    )
    shared = h2_user.repos.recipes.create(
        Recipe(
            name=random_string(), user_id=h2_user.user_id, group_id=h2_user.group_id, household_id=h2_user.household_id
        )
    )
    foreign = g2_user.repos.recipes.create(
        Recipe(
            name=random_string(), user_id=g2_user.user_id, group_id=g2_user.group_id, household_id=g2_user.household_id
        )
    )
    for owner, recipe, actor in [
        (unique_user, own, unique_user),
        (h2_user, shared, unique_user),
        (g2_user, foreign, unique_user),
        (unique_user, own, h2_user),
    ]:
        owner.repos.recipe_timeline_events.create(
            RecipeTimelineEventCreate(
                recipe_id=recipe.id,
                user_id=actor.user_id,
                subject="Recorded",
                event_type="comment",
                cooking_source="manual",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            )
        )
        owner.repos.user_ratings.create(
            UserRatingCreate(recipe_id=recipe.id, user_id=actor.user_id, rating=4, is_favorite=True)
        )
    repository = RepositoryCookingHistory(unique_user.repos.session, UUID(unique_user.group_id))
    response = CookingInsightsService(repository, unique_user.user_id).get(
        CookingInsightsQuery(startDate="2024-01-01", endDate="2024-02-01")
    )
    assert response.coverage.cooking_days == 2
    assert {item.recipe.id for item in response.neglected_favorites.items} == {own.id, shared.id}
    assert foreign.id not in {item.recipe.id for item in response.recommendations.items}
    api_response = api_client.get(
        INSIGHTS_URL, params={"startDate": "2024-01-01", "endDate": "2024-02-01"}, headers=unique_user.token
    )
    assert api_response.status_code == 200
    assert api_response.json()["coverage"]["cookingDays"] == 2
    assert api_response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 51},
        {"timeZone": "Invalid/Zone"},
        {"userId": "other"},
        {"groupId": "other"},
        {"startDate": "2024-01-01"},
    ],
)
def test_insights_api_invalid_queries(api_client: TestClient, unique_user: TestUser, params: dict):
    assert api_client.get(INSIGHTS_URL, params=params, headers=unique_user.token).status_code == 422


def test_insights_authentication(api_client: TestClient):
    assert api_client.get(INSIGHTS_URL).status_code == 401


def test_insights_read_after_edit(api_client: TestClient, unique_user_fn_scoped: TestUser):
    user = unique_user_fn_scoped
    recipe = user.repos.recipes.create(Recipe(name=random_string(), user_id=user.user_id, group_id=user.group_id))
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)
    cooking = user.repos.recipe_timeline_events.create(
        RecipeTimelineEventCreate(
            recipe_id=recipe.id,
            user_id=user.user_id,
            subject="Cooked",
            event_type="comment",
            cooking_source="manual",
            timestamp=timestamp,
        )
    )
    rating_url = api_routes.users_id_ratings_slug(user.user_id, recipe.slug)
    assert api_client.post(rating_url, json={"rating": 5, "isFavorite": True}, headers=user.token).status_code == 200
    params = {"startDate": "2024-01-01", "endDate": "2024-02-01"}

    def read():
        response = api_client.get(INSIGHTS_URL, params=params, headers=user.token)
        assert response.status_code == 200
        return response.json()

    assert read()["neglectedFavorites"]["total"] == 1
    assert read()["recommendations"]["total"] == 1
    assert api_client.post(rating_url, json={"rating": 2}, headers=user.token).status_code == 200
    assert read()["recommendations"]["total"] == 0
    assert (
        api_client.delete(api_routes.recipes_timeline_events_item_id(cooking.id), headers=user.token).status_code == 200
    )
    assert read()["coverage"]["cookingDays"] == 0
    assert read()["favoritesWithoutHistory"]["total"] == 1
    assert (
        api_client.delete(api_routes.users_id_favorites_slug(user.user_id, recipe.slug), headers=user.token).status_code
        == 200
    )
    assert read()["favoritesWithoutHistory"]["total"] == 0
    user.repos.recipes.delete(recipe.id, match_key="id")
    assert read()["frequentMeals"]["total"] == 0


def test_history_query_count_and_large_fixture(unique_user_fn_scoped: TestUser):
    user = unique_user_fn_scoped
    repository = RepositoryCookingHistory(user.repos.session, UUID(user.group_id))
    today = datetime.now(UTC).date()
    recipes = [
        user.repos.recipes.create(Recipe(name=random_string(), user_id=user.user_id, group_id=user.group_id))
        for _ in range(100)
    ]
    rows = [
        {
            "id": uuid4(),
            "recipe_id": recipe.id,
            "user_id": user.user_id,
            "subject": "Recorded",
            "event_type": "comment",
            "cooking_source": "manual",
            "timestamp": datetime.combine(today - timedelta(days=offset + 10), datetime.min.time(), tzinfo=UTC),
        }
        for recipe in recipes
        for offset in range(100)
    ]
    user.repos.session.execute(RecipeTimelineEvent.__table__.insert(), rows)
    user.repos.session.commit()
    statements = []

    def count_selects(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append((statement, parameters))

    engine = user.repos.session.get_bind()
    event.listen(engine, "before_cursor_execute", count_selects)
    try:
        results = []
        query_counts = []
        for limit, window in [(1, 365), (50, 1827)]:
            statements.clear()
            response = CookingInsightsService(repository, user.user_id).get(
                CookingInsightsQuery(startDate=today - timedelta(days=window - 1), endDate=today, limit=limit)
            )
            assert response.coverage.cooking_days == 10000
            assert response.frequent_meals.total == 100
            assert response.frequent_meals.truncated
            results.append(response.frequent_meals.items[0].recipe.id)
            query_counts.append(len(statements))
        assert results[0] == results[1]
        assert query_counts == [5, 5]
        if engine.dialect.name == "sqlite":
            statement, parameters = next(
                (sql, values) for sql, values in statements if "cooking_source IN" in sql and "timestamp >=" in sql
            )
            plan = user.repos.session.connection().exec_driver_sql("EXPLAIN QUERY PLAN " + statement, parameters).all()
            assert any("ix_timeline_actor_source_timestamp" in str(row) for row in plan)
    finally:
        event.remove(engine, "before_cursor_execute", count_selects)


def test_administrator_insights_remain_personal(api_client: TestClient, unique_admin: TestUser):
    response = api_client.get(INSIGHTS_URL, headers=unique_admin.token)
    assert response.status_code == 200
    assert response.json()["filters"]["includeInferred"] is False


def test_same_household_and_current_group_scope(api_client: TestClient, user_tuple: list[TestUser], g2_user: TestUser):
    actor, other = user_tuple
    assert actor.household_id == other.household_id
    recipe = actor.repos.recipes.create(Recipe(name=random_string(), user_id=actor.user_id, group_id=actor.group_id))
    for user, day in [(actor, 1), (other, 2)]:
        actor.repos.recipe_timeline_events.create(
            RecipeTimelineEventCreate(
                recipe_id=recipe.id,
                user_id=user.user_id,
                subject="Recorded",
                event_type="comment",
                cooking_source="manual",
                timestamp=datetime(2024, 1, day, tzinfo=UTC),
            )
        )
    params = {"startDate": "2024-01-01", "endDate": "2024-02-01"}
    assert api_client.get(INSIGHTS_URL, params=params, headers=actor.token).json()["coverage"]["cookingDays"] == 1
    assert api_client.get(INSIGHTS_URL, params=params, headers=other.token).json()["coverage"]["cookingDays"] == 1
    session = actor.repos.session
    try:
        session.execute(
            update(User)
            .where(User.id == actor.user_id)
            .values(group_id=UUID(g2_user.group_id), household_id=UUID(g2_user.household_id))
        )
        session.commit()
        session.expire_all()
        response = api_client.get(INSIGHTS_URL, params=params, headers=actor.token)
        assert response.status_code == 200
        assert response.json()["coverage"]["cookingDays"] == 0
    finally:
        session.execute(
            update(User)
            .where(User.id == actor.user_id)
            .values(group_id=UUID(actor.group_id), household_id=UUID(actor.household_id))
        )
        session.commit()
        session.expire_all()


def test_legacy_and_null_timestamp_evidence(api_client: TestClient, unique_user_fn_scoped: TestUser):
    user = unique_user_fn_scoped
    recipe = user.repos.recipes.create(Recipe(name=random_string(), user_id=user.user_id, group_id=user.group_id))
    user.repos.recipe_timeline_events.create(
        RecipeTimelineEventCreate(
            recipe_id=recipe.id,
            user_id=user.user_id,
            subject="I made this",
            event_type="comment",
            timestamp=datetime(2020, 1, 1, tzinfo=UTC),
        )
    )
    user.repos.session.execute(
        RecipeTimelineEvent.__table__.insert().values(
            id=uuid4(),
            recipe_id=recipe.id,
            user_id=user.user_id,
            subject="Null date",
            event_type="info",
            cooking_source="manual",
            timestamp=None,
        )
    )
    user.repos.session.commit()
    response = api_client.get(
        INSIGHTS_URL, params={"startDate": "2024-01-01", "endDate": "2024-02-01"}, headers=user.token
    )
    assert response.status_code == 200
    assert response.json()["coverage"]["cookingDays"] == 0
    assert response.json()["coverage"]["hasUnclassifiedEvents"]
