from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from mealie.schema.meal_plan.new_meal import CreatePlanEntry, UpdatePlanEntry
from mealie.schema.meal_plan.plan_rules import PlanRulesDay

test_cases = [
    (datetime(2022, 2, 7), PlanRulesDay.monday),
    (datetime(2022, 2, 8), PlanRulesDay.tuesday),
    (datetime(2022, 2, 9), PlanRulesDay.wednesday),
    (datetime(2022, 2, 10), PlanRulesDay.thursday),
    (datetime(2022, 2, 11), PlanRulesDay.friday),
    (datetime(2022, 2, 12), PlanRulesDay.saturday),
    (datetime(2022, 2, 13), PlanRulesDay.sunday),
]


@pytest.mark.parametrize("date, expected", test_cases)
def test_date_obj_to_enum(date: datetime, expected: PlanRulesDay):
    assert PlanRulesDay.from_date(date) == expected


@pytest.mark.parametrize(
    "portions",
    [
        {},
        {"preparedPortions": 6, "eatenPortions": 4},
        {"preparedPortions": 4, "eatenPortions": 4},
        {"preparedPortions": 4, "eatenPortions": 0},
        {"leftoverSourceId": 1, "eatenPortions": 2},
    ],
)
def test_valid_meal_portion_shapes(portions: dict):
    entry = CreatePlanEntry.model_validate({"date": "2026-10-05", "title": "Dinner", **portions})
    payload = entry.model_dump(by_alias=True)
    assert all(payload[key] == value for key, value in portions.items())


@pytest.mark.parametrize(
    "portions",
    [
        {"preparedPortions": 6},
        {"eatenPortions": 4},
        {"preparedPortions": 0, "eatenPortions": 0},
        {"preparedPortions": 4, "eatenPortions": -1},
        {"preparedPortions": 4, "eatenPortions": 5},
        {"preparedPortions": 4.5, "eatenPortions": 2},
        {"preparedPortions": True, "eatenPortions": 1},
        {"preparedPortions": 4, "eatenPortions": False},
        {"preparedPortions": 2147483648, "eatenPortions": 1},
        {"leftoverSourceId": 1},
        {"leftoverSourceId": 1, "eatenPortions": 0},
        {"leftoverSourceId": 1, "preparedPortions": 2, "eatenPortions": 1},
        {"leftoverSourceId": 0, "eatenPortions": 1},
    ],
)
def test_invalid_meal_portion_shapes(portions: dict):
    with pytest.raises(ValidationError):
        CreatePlanEntry.model_validate({"date": "2026-10-05", "title": "Dinner", **portions})


def test_update_preserves_provided_field_intent():
    payload = {"id": 1, "groupId": uuid4(), "userId": uuid4(), "date": "2026-10-05", "title": "Dinner"}
    omitted = UpdatePlanEntry.model_validate(payload)
    cleared = UpdatePlanEntry.model_validate({**payload, "preparedPortions": None, "eatenPortions": None})
    partial = UpdatePlanEntry.model_validate({**payload, "eatenPortions": 2})
    assert "prepared_portions" not in omitted.model_fields_set
    assert "prepared_portions" in cleared.model_fields_set
    assert "eaten_portions" in partial.model_fields_set
    assert "prepared_portions" not in partial.model_fields_set
