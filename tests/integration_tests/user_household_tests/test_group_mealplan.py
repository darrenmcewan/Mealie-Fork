import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from mealie.db.models._model_base import SqlAlchemyBase
from mealie.db.models.group import Group
from mealie.db.models.household import GroupMealPlan, Household
from mealie.db.models.users.users import User
from mealie.repos.all_repositories import get_repositories
from mealie.repos.repository_meals import MealPlanError, RepositoryMeals
from mealie.routes.households.controller_mealplan import GroupMealplanController
from mealie.schema.household.household import HouseholdSummary
from mealie.schema.meal_plan.new_meal import CreatePlanEntry, ReadPlanEntry, SavePlanEntry
from mealie.schema.meal_plan.plan_rules import PlanRulesDay, PlanRulesOut, PlanRulesSave, PlanRulesType
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_category import CategoryOut, CategorySave, TagOut, TagSave
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.user.user import PrivateUser
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


def route_all_slice(page: int, perPage: int, start_date: str, end_date: str):
    return (
        f"{api_routes.households_mealplans}?page={page}&perPage={perPage}&start_date={start_date}&end_date={end_date}"
    )


def create_recipe(unique_user: TestUser, tags: list[TagOut] | None = None, categories: list[CategoryOut] | None = None):
    return unique_user.repos.recipes.create(
        Recipe(
            user_id=unique_user.user_id,
            group_id=UUID(unique_user.group_id),
            name=random_string(),
            tags=tags or [],
            recipe_category=categories or [],
        )
    )


def create_rule(
    unique_user: TestUser,
    day: PlanRulesDay,
    entry_type: PlanRulesType,
    tags: list[TagOut] | None = None,
    categories: list[CategoryOut] | None = None,
    households: list[HouseholdSummary] | None = None,
):
    qf_parts: list[str] = []
    if tags:
        qf_parts.append(f"tags.id CONTAINS ALL [{','.join([str(tag.id) for tag in tags])}]")
    if categories:
        qf_parts.append(f"recipe_category.id CONTAINS ALL [{','.join([str(cat.id) for cat in categories])}]")
    if households:
        qf_parts.append(f"household_id IN [{','.join([str(household.id) for household in households])}]")

    query_filter_string = " AND ".join(qf_parts)
    return unique_user.repos.group_meal_plan_rules.create(
        PlanRulesSave(
            group_id=UUID(unique_user.group_id),
            household_id=UUID(unique_user.household_id),
            day=day,
            entry_type=entry_type,
            query_filter_string=query_filter_string,
        )
    )


def test_create_mealplan_no_recipe(api_client: TestClient, unique_user: TestUser):
    title = random_string(length=25)
    text = random_string(length=25)
    new_plan = CreatePlanEntry(
        date=datetime.now(UTC).date(), entry_type="breakfast", title=title, text=text
    ).model_dump()
    new_plan["date"] = datetime.now(UTC).date().strftime("%Y-%m-%d")

    response = api_client.post(api_routes.households_mealplans, json=new_plan, headers=unique_user.token)

    assert response.status_code == 201

    response_json = response.json()
    assert response_json["title"] == title
    assert response_json["text"] == text


def test_create_mealplan_with_recipe(api_client: TestClient, unique_user: TestUser):
    recipe_name = random_string(length=25)
    response = api_client.post(api_routes.recipes, json={"name": recipe_name}, headers=unique_user.token)
    assert response.status_code == 201

    response = api_client.get(api_routes.recipes_slug(recipe_name), headers=unique_user.token)
    recipe = response.json()
    recipe_id = recipe["id"]

    new_plan = CreatePlanEntry(date=datetime.now(UTC).date(), entry_type="dinner", recipe_id=recipe_id).model_dump(
        by_alias=True
    )
    new_plan["date"] = datetime.now(UTC).date().strftime("%Y-%m-%d")
    new_plan["recipeId"] = str(recipe_id)

    response = api_client.post(api_routes.households_mealplans, json=new_plan, headers=unique_user.token)
    response_json = response.json()
    assert response.status_code == 201

    assert response_json["recipe"]["slug"] == recipe_name


def test_crud_mealplan(api_client: TestClient, unique_user: TestUser):
    new_plan = CreatePlanEntry(
        date=datetime.now(UTC).date(),
        entry_type="breakfast",
        title=random_string(),
        text=random_string(),
    ).model_dump()

    # Create
    new_plan["date"] = datetime.now(UTC).date().strftime("%Y-%m-%d")
    response = api_client.post(api_routes.households_mealplans, json=new_plan, headers=unique_user.token)
    response_json = response.json()
    assert response.status_code == 201
    plan_id = response_json["id"]

    # Update
    response_json["title"] = random_string()
    response_json["text"] = random_string()

    response = api_client.put(
        api_routes.households_mealplans_item_id(plan_id), headers=unique_user.token, json=response_json
    )

    assert response.status_code == 200

    assert response.json()["title"] == response_json["title"]
    assert response.json()["text"] == response_json["text"]

    # Delete
    response = api_client.delete(api_routes.households_mealplans_item_id(plan_id), headers=unique_user.token)

    assert response.status_code == 200

    response = api_client.get(api_routes.households_mealplans_item_id(plan_id), headers=unique_user.token)
    assert response.status_code == 404


def test_get_all_mealplans(api_client: TestClient, unique_user: TestUser):
    for _ in range(3):
        new_plan = CreatePlanEntry(
            date=datetime.now(UTC).date(),
            entry_type="breakfast",
            title=random_string(),
            text=random_string(),
        ).model_dump()

        new_plan["date"] = datetime.now(UTC).date().strftime("%Y-%m-%d")
        response = api_client.post(api_routes.households_mealplans, json=new_plan, headers=unique_user.token)
        assert response.status_code == 201

    response = api_client.get(
        api_routes.households_mealplans, headers=unique_user.token, params={"page": 1, "perPage": -1}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 3


def test_get_slice_mealplans(api_client: TestClient, unique_user: TestUser):
    # Make List of 10 dates from now to +10 days
    dates = [datetime.now(UTC).date() + timedelta(days=x) for x in range(10)]

    # Make a list of 10 meal plans
    meal_plans = [
        CreatePlanEntry(date=date, entry_type="breakfast", title=random_string(), text=random_string()).model_dump()
        for date in dates
    ]

    # Add the meal plans to the database
    for meal_plan in meal_plans:
        meal_plan["date"] = meal_plan["date"].strftime("%Y-%m-%d")
        response = api_client.post(api_routes.households_mealplans, json=meal_plan, headers=unique_user.token)
        assert response.status_code == 201

    # Get meal slice of meal plans from database
    slices = [dates, dates[1:2], dates[2:3], dates[3:4], dates[4:5]]

    for date_range in slices:
        start_date = date_range[0].strftime("%Y-%m-%d")
        end_date = date_range[-1].strftime("%Y-%m-%d")

        response = api_client.get(route_all_slice(1, -1, start_date, end_date), headers=unique_user.token)

        assert response.status_code == 200
        response_json = response.json()

        for meal_plan in response_json["items"]:
            assert meal_plan["date"] in [date.strftime("%Y-%m-%d") for date in date_range]


def test_get_mealplan_today(api_client: TestClient, unique_user: TestUser):
    # Create Meal Plans for today
    test_meal_plans = [
        CreatePlanEntry(
            date=datetime.now(UTC).date(), entry_type="breakfast", title=random_string(), text=random_string()
        ).model_dump()
        for _ in range(3)
    ]

    # Add the meal plans to the database
    for meal_plan in test_meal_plans:
        meal_plan["date"] = meal_plan["date"].strftime("%Y-%m-%d")
        response = api_client.post(api_routes.households_mealplans, json=meal_plan, headers=unique_user.token)
        assert response.status_code == 201

    # Get meal plan for today
    response = api_client.get(api_routes.households_mealplans_today, headers=unique_user.token)

    assert response.status_code == 200

    response_json = response.json()

    for meal_plan in response_json:
        assert meal_plan["date"] == datetime.now(UTC).date().strftime("%Y-%m-%d")


def leftover_source(unique_user: TestUser, prepared: int = 6, eaten: int = 4):
    return unique_user.repos.meals.create(
        SavePlanEntry(
            date=datetime.now(UTC).date(),
            title="Batch dinner",
            prepared_portions=prepared,
            eaten_portions=eaten,
            group_id=UUID(unique_user.group_id),
            user_id=unique_user.user_id,
        )
    )


def leftover_followup(unique_user: TestUser, source, portions: int = 2):
    return SavePlanEntry(
        date=source.date + timedelta(days=1),
        entry_type="lunch",
        title=source.title,
        text=source.text,
        recipe_id=source.recipe_id,
        eaten_portions=portions,
        leftover_source_id=source.id,
        group_id=UUID(unique_user.group_id),
        user_id=unique_user.user_id,
    )


def test_leftover_repository_allocation_and_release(unique_user: TestUser):
    source = leftover_source(unique_user)
    followup = unique_user.repos.meals.create(leftover_followup(unique_user, source))
    with pytest.raises(MealPlanError) as conflict:
        unique_user.repos.meals.create(leftover_followup(unique_user, source, 1))
    assert conflict.value.status_code == 409
    assert unique_user.repos.meals._reserved(source.id) == 2
    unique_user.repos.meals.delete(followup.id)
    assert unique_user.repos.meals._reserved(source.id) == 0


def test_leftover_repository_updates_and_legacy_metadata(unique_user: TestUser):
    source = leftover_source(unique_user)
    followup = unique_user.repos.meals.create(leftover_followup(unique_user, source))
    updated = unique_user.repos.meals.update(followup.id, {"entry_type": "dinner"})
    assert updated.leftover_source_id == source.id
    assert updated.eaten_portions == 2
    with pytest.raises(MealPlanError):
        unique_user.repos.meals.update(source.id, {"prepared_portions": 5})
    with pytest.raises(MealPlanError):
        unique_user.repos.meals.delete(source.id)
    assert unique_user.repos.meals.get_one(source.id).prepared_portions == 6
    increased = unique_user.repos.meals.update(source.id, {"prepared_portions": 8})
    assert increased.prepared_portions == 8
    detached = unique_user.repos.meals.update(
        followup.id, {"leftover_source_id": None, "prepared_portions": None, "eaten_portions": None}
    )
    assert detached.leftover_source_id is None
    assert unique_user.repos.meals._reserved(source.id) == 0


def test_leftover_repository_failed_reassignment_is_atomic(unique_user: TestUser):
    source = leftover_source(unique_user)
    exhausted = leftover_source(unique_user, prepared=4, eaten=4)
    followup = unique_user.repos.meals.create(leftover_followup(unique_user, source))
    with pytest.raises(MealPlanError):
        unique_user.repos.meals.update(followup.id, {"leftover_source_id": exhausted.id})
    assert unique_user.repos.meals.get_one(followup.id).leftover_source_id == source.id
    assert unique_user.repos.meals._reserved(source.id) == 2
    assert unique_user.repos.meals._reserved(exhausted.id) == 0


def test_leftover_repository_rejects_foreign_source(unique_user: TestUser, h2_user: TestUser):
    foreign = leftover_source(h2_user)
    with pytest.raises(MealPlanError) as missing:
        unique_user.repos.meals.create(leftover_followup(unique_user, foreign))
    assert missing.value.status_code == 404
    assert missing.value.meal_ids == []


def test_leftover_api_totals_discovery_and_lifecycle(api_client: TestClient, unique_user: TestUser):
    source = leftover_source(unique_user)
    payload = leftover_followup(unique_user, source).model_dump(mode="json", by_alias=True)
    created = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert created.status_code == 201
    followup = created.json()
    assert followup["leftoverSource"]["id"] == source.id
    def get_source():
        return api_client.get(api_routes.households_mealplans_item_id(source.id), headers=unique_user.token)

    assert get_source().json()["availableLeftovers"] == 0
    conflict = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert conflict.status_code == 409
    target_date = (source.date + timedelta(days=10)).isoformat()
    route = f"{api_routes.households_mealplans}/leftovers"
    sources = api_client.get(route, params={"target_date": target_date}, headers=unique_user.token)
    assert sources.status_code == 200
    assert source.id not in [item["id"] for item in sources.json()["items"]]
    editing = api_client.get(
        route, params={"target_date": target_date, "editing_entry_id": followup["id"]}, headers=unique_user.token
    )
    assert editing.status_code == 200
    edited_source = next(item for item in editing.json()["items"] if item["id"] == source.id)
    assert edited_source["allocatablePortions"] == 2
    assert edited_source["availableLeftovers"] == 0
    slice_response = api_client.get(
        api_routes.households_mealplans,
        params={"start_date": source.date.isoformat(), "end_date": source.date.isoformat()},
        headers=unique_user.token,
    )
    sliced_source = next(item for item in slice_response.json()["items"] if item["id"] == source.id)
    assert sliced_source["reservedLeftovers"] == 2
    legacy = {
        key: followup[key]
        for key in ["id", "date", "entryType", "title", "text", "recipeId", "groupId", "userId"]
    }
    legacy["entryType"] = "dinner"
    updated = api_client.put(
        api_routes.households_mealplans_item_id(followup["id"]), json=legacy, headers=unique_user.token
    )
    assert updated.status_code == 200
    assert updated.json()["eatenPortions"] == 2
    assert updated.json()["leftoverSourceId"] == source.id
    rejected_delete = api_client.delete(api_routes.households_mealplans_item_id(source.id), headers=unique_user.token)
    assert rejected_delete.status_code == 409
    assert rejected_delete.json()["detail"]["mealIds"] == [followup["id"]]
    deleted = api_client.delete(api_routes.households_mealplans_item_id(followup["id"]), headers=unique_user.token)
    assert deleted.status_code == 200
    assert get_source().json()["availableLeftovers"] == 2


@pytest.mark.parametrize("change", ["date", "identity", "chain", "untracked", "self"])
def test_leftover_api_invalid_links(api_client: TestClient, unique_user: TestUser, change: str):
    source = leftover_source(unique_user, prepared=8, eaten=4)
    payload = leftover_followup(unique_user, source).model_dump(mode="json", by_alias=True)
    if change == "date":
        payload["date"] = source.date.isoformat()
    elif change == "identity":
        payload["title"] = "Another batch"
    elif change == "chain":
        followup = unique_user.repos.meals.create(leftover_followup(unique_user, source, 1))
        payload["leftoverSourceId"] = followup.id
        payload["date"] = (followup.date + timedelta(days=1)).isoformat()
    elif change == "untracked":
        untracked = unique_user.repos.meals.create(
            SavePlanEntry(
                date=source.date, title=source.title, group_id=UUID(unique_user.group_id), user_id=unique_user.user_id
            )
        )
        payload["leftoverSourceId"] = untracked.id
    else:
        response = api_client.put(
            api_routes.households_mealplans_item_id(source.id),
            json={
                **source.model_dump(mode="json", by_alias=True),
                "leftoverSourceId": source.id,
                "preparedPortions": None,
            },
            headers=unique_user.token,
        )
        assert response.status_code == 422
        return
    response = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert response.status_code == 422


def test_leftover_api_foreign_discovery_and_links(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    foreign = leftover_source(h2_user)
    payload = leftover_followup(unique_user, foreign).model_dump(mode="json", by_alias=True)
    foreign_response = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    payload["leftoverSourceId"] = 2147483647
    missing_response = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert foreign_response.status_code == missing_response.status_code == 404
    assert foreign_response.json() == missing_response.json()
    response = api_client.get(
        f"{api_routes.households_mealplans}/leftovers",
        params={"target_date": (foreign.date + timedelta(days=1)).isoformat()},
        headers=unique_user.token,
    )
    assert response.status_code == 200
    assert foreign.id not in [item["id"] for item in response.json()["items"]]
    assert all(item["householdId"] == unique_user.household_id for item in response.json()["items"])


def test_leftover_api_events_and_owner(api_client: TestClient, unique_user: TestUser, h2_user: TestUser, monkeypatch):
    published = []
    monkeypatch.setattr(GroupMealplanController, "publish_event", lambda self, **payload: published.append(payload))
    source = leftover_source(unique_user)
    payload = leftover_followup(unique_user, source).model_dump(mode="json", by_alias=True)
    response = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert response.status_code == 201
    assert len(published) == 1
    rejected = api_client.post(api_routes.households_mealplans, json=payload, headers=unique_user.token)
    assert rejected.status_code == 409
    assert len(published) == 1
    update_payload = {**response.json(), "userId": str(h2_user.user_id)}
    redirected = api_client.put(
        api_routes.households_mealplans_item_id(response.json()["id"]), json=update_payload, headers=unique_user.token
    )
    assert redirected.status_code == 422
    assert unique_user.repos.meals.get_one(response.json()["id"]).user_id == unique_user.user_id


@pytest.mark.parametrize(
    "change",
    [{"date": "later"}, {"title": "Changed batch"}, {"prepared_portions": None, "eaten_portions": None}],
)
def test_leftover_source_edit_safeguards(unique_user: TestUser, change: dict):
    source = leftover_source(unique_user)
    unique_user.repos.meals.create(leftover_followup(unique_user, source))
    if change.get("date") == "later":
        change = {"date": source.date + timedelta(days=1)}
    with pytest.raises(MealPlanError) as conflict:
        unique_user.repos.meals.update(source.id, change)
    assert conflict.value.status_code == 409


def test_leftover_discovery_pagination_and_batched_reads(unique_user: TestUser):
    sources = [leftover_source(unique_user) for _ in range(4)]
    query_filter = f"id IN [{','.join(str(source.id) for source in sources)}]"
    target = sources[0].date + timedelta(days=1)
    first = unique_user.repos.meals.get_leftovers(target, PaginationQuery(per_page=1, query_filter=query_filter))
    second = unique_user.repos.meals.get_leftovers(
        target, PaginationQuery(page=2, per_page=1, query_filter=query_filter)
    )
    assert first.total == second.total == 4
    assert first.total_pages == 4
    assert first.items[0].id != second.items[0].id
    statements = []
    engine = unique_user.repos.meals.session.get_bind()

    def record_statement(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record_statement)
    try:
        unique_user.repos.meals.page_all(PaginationQuery(query_filter=f"id = {sources[0].id}"))
        single_count = len(statements)
        statements.clear()
        unique_user.repos.meals.page_all(PaginationQuery(query_filter=query_filter))
        assert len(statements) <= single_count + 1
    finally:
        event.remove(engine, "before_cursor_execute", record_statement)


@contextmanager
def concurrency_repository(database_kind: str, unique_user: TestUser):
    if database_kind == "sqlite":
        yield unique_user.repos.meals
        return
    url = os.getenv("MEALIE_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MEALIE_TEST_POSTGRES_URL to an isolated PostgreSQL instance")
    schema_name = f"leftover_test_{uuid4().hex}"
    admin_engine = create_engine(url)
    with admin_engine.begin() as connection:
        connection.execute(CreateSchema(schema_name))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema_name}"})
    try:
        SqlAlchemyBase.metadata.create_all(engine)
        with engine.begin() as connection:
            for model, identifier in [
                (Group, UUID(unique_user.group_id)),
                (Household, UUID(unique_user.household_id)),
                (User, unique_user.user_id),
            ]:
                original = unique_user.repos.meals.session.execute(
                    select(model.__table__).where(model.id == identifier)
                ).mappings().one()
                connection.execute(insert(model.__table__).values(dict(original)))
        with Session(engine) as session:
            yield RepositoryMeals(
                session, "id", GroupMealPlan, ReadPlanEntry,
                group_id=UUID(unique_user.group_id), household_id=UUID(unique_user.household_id),
            )
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(DropSchema(schema_name, cascade=True))
        admin_engine.dispose()


@pytest.mark.parametrize("database_kind", ["sqlite", "postgres"])
@pytest.mark.parametrize("operation", ["reserve", "reduce_source"])
def test_leftover_concurrent_mutations(unique_user: TestUser, monkeypatch, database_kind: str, operation: str):
    with concurrency_repository(database_kind, unique_user) as repository:
        source = repository.create(
            SavePlanEntry(
                date=datetime.now(UTC).date(), title="Concurrent batch", prepared_portions=6, eaten_portions=4,
                group_id=UUID(unique_user.group_id), user_id=unique_user.user_id,
            )
        )
        barrier = threading.Barrier(2)
        thread_state = threading.local()
        original_entry = RepositoryMeals._entry

        def overlap_entry(repo, entry_id):
            entry = original_entry(repo, entry_id)
            if (
                entry.id == source.id
                and threading.current_thread().name.startswith("leftover-race")
                and not getattr(thread_state, "waited", False)
            ):
                thread_state.waited = True
                barrier.wait(timeout=10)
            return entry

        monkeypatch.setattr(RepositoryMeals, "_entry", overlap_entry)
        engine = repository.session.get_bind()

        def mutate(index: int):
            with Session(engine) as session:
                worker = RepositoryMeals(
                    session, "id", GroupMealPlan, ReadPlanEntry,
                    group_id=UUID(unique_user.group_id), household_id=UUID(unique_user.household_id),
                )
                try:
                    if operation == "reduce_source" and index == 1:
                        worker.update(source.id, {"prepared_portions": 5})
                    else:
                        worker.create(leftover_followup(unique_user, source))
                    return 200
                except MealPlanError as error:
                    assert error.status_code == 409
                    return error.status_code

        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="leftover-race") as executor:
            outcomes = list(executor.map(mutate, [0, 1]))
        assert sorted(outcomes) == [200, 409]
        repository.session.expire_all()
        current = repository.get_one(source.id)
        assert current.reserved_leftovers <= current.expected_leftovers


@pytest.mark.parametrize("database_kind", ["sqlite", "postgres"])
def test_leftover_owner_teardown(unique_user: TestUser, database_kind: str):
    with concurrency_repository(database_kind, unique_user) as repository:
        owner_data = dict(repository.session.execute(
            select(User.__table__).where(User.id == unique_user.user_id)
        ).mappings().one())
        owner_id = uuid4()
        owner_data.update(id=owner_id, username=f"leftover-{owner_id.hex}", email=f"{owner_id.hex}@example.test")
        repository.session.execute(insert(User.__table__).values(owner_data))
        repository.session.commit()
        source = repository.create(SavePlanEntry(
            date=datetime.now(UTC).date(), title="Owner batch", prepared_portions=6, eaten_portions=4,
            group_id=unique_user._group_id, user_id=owner_id,
        ))
        followup = repository.create(SavePlanEntry(
            date=source.date + timedelta(days=1), title=source.title, eaten_portions=2, leftover_source_id=source.id,
            group_id=unique_user._group_id, user_id=owner_id,
        ))
        repository.update(followup.id, {"eaten_portions": 1})
        other_followup = repository.create(SavePlanEntry(
            date=source.date + timedelta(days=2), title=source.title, eaten_portions=1, leftover_source_id=source.id,
            group_id=unique_user._group_id, user_id=unique_user.user_id,
        ))
        PrivateUser.get_directory(owner_id).mkdir(parents=True, exist_ok=True)
        repos = get_repositories(
            repository.session, group_id=unique_user._group_id, household_id=unique_user._household_id
        )
        repos.users.delete(owner_id)
        assert repository.get_one(source.id) is None
        assert repository.get_one(followup.id) is None
        preserved = repository.get_one(other_followup.id)
        assert preserved.title == source.title
        assert preserved.leftover_source_id is None
        assert preserved.eaten_portions is None
        repository.delete(preserved.id)


def test_leftover_past_allocations_and_successful_reassignment(unique_user: TestUser):
    source = unique_user.repos.meals.create(SavePlanEntry(
        date=datetime(2020, 1, 1, tzinfo=UTC).date(), title="Past batch", prepared_portions=6, eaten_portions=4,
        group_id=unique_user._group_id, user_id=unique_user.user_id,
    ))
    followup = unique_user.repos.meals.create(leftover_followup(unique_user, source))
    assert unique_user.repos.meals.get_one(source.id).available_leftovers == 0
    destination = unique_user.repos.meals.create(SavePlanEntry(
        date=source.date, title=source.title, prepared_portions=8, eaten_portions=4,
        group_id=unique_user._group_id, user_id=unique_user.user_id,
    ))
    reassigned = unique_user.repos.meals.update(followup.id, {"leftover_source_id": destination.id})
    assert reassigned.leftover_source_id == destination.id
    assert unique_user.repos.meals.get_one(source.id).available_leftovers == 2
    assert unique_user.repos.meals.get_one(destination.id).reserved_leftovers == 2


def test_get_mealplan_with_rules_categories_and_tags_filter(api_client: TestClient, unique_user: TestUser):
    tags = [
        unique_user.repos.tags.create(TagSave(name=random_string(), group_id=unique_user.group_id)) for _ in range(4)
    ]
    categories = [
        unique_user.repos.categories.create(CategorySave(name=random_string(), group_id=unique_user.group_id))
        for _ in range(4)
    ]
    [
        create_recipe(unique_user, tags=[tag], categories=[category])
        for tag, category in zip(tags, categories, strict=True)
    ]
    [create_recipe(unique_user) for _ in range(5)]

    i = random.randint(0, 3)
    tag = tags[i]
    category = categories[i]
    rule = create_rule(
        unique_user,
        day=PlanRulesDay.saturday,
        entry_type=PlanRulesType.breakfast,
        tags=[tag],
        categories=[category],
    )

    try:
        payload = {"date": "2023-02-25", "entryType": "breakfast"}
        response = api_client.post(api_routes.households_mealplans_random, json=payload, headers=unique_user.token)
        assert response.status_code == 200
        recipe_data = response.json()["recipe"]
        assert recipe_data["tags"][0]["name"] == tag.name
        assert recipe_data["recipeCategory"][0]["name"] == category.name
    finally:
        unique_user.repos.group_meal_plan_rules.delete(rule.id)


def test_get_mealplan_with_rules_date_and_type_filter(api_client: TestClient, unique_user: TestUser):
    tags = [
        unique_user.repos.tags.create(TagSave(name=random_string(), group_id=unique_user.group_id)) for _ in range(4)
    ]
    recipes = [create_recipe(unique_user, tags=[tag]) for tag in tags]
    [create_recipe(unique_user) for _ in range(5)]

    rules: list[PlanRulesOut] = []
    rules.append(
        create_rule(unique_user, day=PlanRulesDay.saturday, entry_type=PlanRulesType.breakfast, tags=[tags[0]])
    )
    rules.append(create_rule(unique_user, day=PlanRulesDay.saturday, entry_type=PlanRulesType.dinner, tags=[tags[1]]))
    rules.append(create_rule(unique_user, day=PlanRulesDay.sunday, entry_type=PlanRulesType.breakfast, tags=[tags[2]]))
    rules.append(create_rule(unique_user, day=PlanRulesDay.sunday, entry_type=PlanRulesType.dinner, tags=[tags[3]]))

    try:
        payload = {"date": "2023-02-25", "entryType": "breakfast"}
        response = api_client.post(api_routes.households_mealplans_random, json=payload, headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["recipe"]["slug"] == recipes[0].slug
    finally:
        for rule in rules:
            unique_user.repos.group_meal_plan_rules.delete(rule.id)


def test_get_mealplan_with_rules_includes_other_households(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser
):
    tag = h2_user.repos.tags.create(TagSave(name=random_string(), group_id=h2_user.group_id))
    recipe = create_recipe(h2_user, tags=[tag])
    rule = create_rule(unique_user, day=PlanRulesDay.saturday, entry_type=PlanRulesType.breakfast, tags=[tag])

    try:
        payload = {"date": "2023-02-25", "entryType": "breakfast"}
        response = api_client.post(api_routes.households_mealplans_random, json=payload, headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["recipe"]["slug"] == recipe.slug
    finally:
        unique_user.repos.group_meal_plan_rules.delete(rule.id)


def test_get_mealplan_with_rules_households_filter(api_client: TestClient, unique_user: TestUser, h2_user: TestUser):
    tag = unique_user.repos.tags.create(TagSave(name=random_string(), group_id=unique_user.group_id))
    recipe = create_recipe(unique_user, tags=[tag])
    [create_recipe(h2_user, tags=[tag]) for _ in range(10)]

    household = unique_user.repos.households.get_by_slug_or_id(unique_user.household_id)
    assert household

    rule = create_rule(
        unique_user, day=PlanRulesDay.saturday, entry_type=PlanRulesType.breakfast, tags=[tag], households=[household]
    )

    try:
        payload = {"date": "2023-02-25", "entryType": "breakfast"}
        response = api_client.post(api_routes.households_mealplans_random, json=payload, headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["recipe"]["slug"] == recipe.slug
    finally:
        unique_user.repos.group_meal_plan_rules.delete(rule.id)


def test_get_mealplan_with_rules_households_filter_includes_any_households(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser
):
    tag = unique_user.repos.tags.create(TagSave(name=random_string(), group_id=unique_user.group_id))
    recipe = create_recipe(h2_user, tags=[tag])

    household = unique_user.repos.households.get_by_slug_or_id(unique_user.household_id)
    assert household
    h2_household = unique_user.repos.households.get_by_slug_or_id(h2_user.household_id)
    assert h2_household
    rule = create_rule(
        unique_user,
        day=PlanRulesDay.saturday,
        entry_type=PlanRulesType.breakfast,
        tags=[tag],
        households=[household, h2_household],
    )

    try:
        payload = {"date": "2023-02-25", "entryType": "breakfast"}
        response = api_client.post(api_routes.households_mealplans_random, json=payload, headers=unique_user.token)
        assert response.status_code == 200
        assert response.json()["recipe"]["slug"] == recipe.slug
    finally:
        unique_user.repos.group_meal_plan_rules.delete(rule.id)
