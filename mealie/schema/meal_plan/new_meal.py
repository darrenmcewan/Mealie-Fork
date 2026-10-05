from datetime import date
from enum import Enum
from typing import Annotated, ClassVar, Self
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import LoaderOption

from mealie.db.models.household import GroupMealPlan
from mealie.db.models.recipe import RecipeModel
from mealie.db.models.users.users import User
from mealie.schema._mealie import MealieModel
from mealie.schema.recipe.recipe import RecipeSummary
from mealie.schema.response.pagination import PaginationBase


class PlanEntryType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    side = "side"


class CreateRandomEntry(MealieModel):
    date: date
    entry_type: PlanEntryType = PlanEntryType.dinner


class CreatePlanEntry(MealieModel):
    validate_portion_shape: ClassVar[bool] = True

    date: date
    entry_type: PlanEntryType = PlanEntryType.breakfast
    title: str = ""
    text: str = ""
    recipe_id: Annotated[UUID | None, Field(validate_default=True)] = None
    prepared_portions: Annotated[int, Field(strict=True, gt=0, le=2147483647)] | None = None
    eaten_portions: Annotated[int, Field(strict=True, ge=0, le=2147483647)] | None = None
    leftover_source_id: Annotated[int, Field(strict=True, gt=0)] | None = None

    @model_validator(mode="after")
    def valid_portions(self) -> Self:
        if not self.validate_portion_shape:
            return self
        if self.leftover_source_id is not None:
            if self.prepared_portions is not None or not self.eaten_portions:
                raise ValueError("A leftover meal requires eaten portions and cannot prepare new portions")
        elif self.prepared_portions is not None or self.eaten_portions is not None:
            if self.prepared_portions is None or self.eaten_portions is None:
                raise ValueError("Prepared and eaten portions must be provided together")
            if self.eaten_portions > self.prepared_portions:
                raise ValueError("Eaten portions cannot exceed prepared portions")
        return self

    @field_validator("recipe_id")
    @classmethod
    def id_or_title(cls, value, info: ValidationInfo):
        if bool(value) is False and bool(info.data["title"]) is False:
            raise ValueError(f"`recipe_id={value}` or `title={info.data['title']}` must be provided")

        return value


class UpdatePlanEntry(CreatePlanEntry):
    validate_portion_shape: ClassVar[bool] = False

    id: int
    group_id: UUID
    user_id: UUID


class SavePlanEntry(CreatePlanEntry):
    group_id: UUID
    user_id: UUID
    model_config = ConfigDict(from_attributes=True)


class PlanEntrySource(MealieModel):
    id: int
    date: date
    entry_type: PlanEntryType
    recipe_id: UUID | None = None
    title: str = ""
    text: str = ""


class ReadPlanEntry(UpdatePlanEntry):
    household_id: UUID
    recipe: RecipeSummary | None = None
    expected_leftovers: int | None = None
    reserved_leftovers: int | None = None
    available_leftovers: int | None = None
    leftover_source: PlanEntrySource | None = None
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            selectinload(GroupMealPlan.recipe).joinedload(RecipeModel.recipe_category),
            selectinload(GroupMealPlan.recipe).joinedload(RecipeModel.tags),
            selectinload(GroupMealPlan.recipe).joinedload(RecipeModel.tools),
            selectinload(GroupMealPlan.user).load_only(User.household_id),
        ]


class PlanEntryPagination(PaginationBase):
    items: list[ReadPlanEntry]


class LeftoverPlanEntry(ReadPlanEntry):
    allocatable_portions: int


class LeftoverPlanEntryPagination(PaginationBase):
    items: list[LeftoverPlanEntry]
