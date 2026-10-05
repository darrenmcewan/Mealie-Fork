from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import UUID4
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from mealie.db.models.recipe.recipe import RecipeModel
from mealie.db.models.recipe.recipe_timeline import RecipeTimelineEvent
from mealie.db.models.users.user_to_recipe import UserToRecipe
from mealie.schema.user.cooking_insights import CookingInsightRecipe


@dataclass(frozen=True)
class CookingHistoryEvent:
    recipe_id: UUID4
    timestamp: datetime | None
    source: str | None


@dataclass(frozen=True)
class CookingHistoryBounds:
    recipe_id: UUID4
    first: datetime
    manual_last: datetime | None
    inferred_last: datetime | None


@dataclass(frozen=True)
class CookingHistoryPreference:
    recipe_id: UUID4
    rating: float | None
    is_favorite: bool


class RepositoryCookingHistory:
    def __init__(self, session: Session, group_id: UUID):
        if not isinstance(group_id, UUID):
            raise ValueError("Cooking history requires an authenticated group")
        self.session = session
        self.group_id = group_id

    def events(
        self, actor_id: UUID, start: datetime, end: datetime, sources: list[str]
    ) -> Iterator[CookingHistoryEvent]:
        statement = (
            select(RecipeTimelineEvent.recipe_id, RecipeTimelineEvent.timestamp, RecipeTimelineEvent.cooking_source)
            .join(RecipeModel, RecipeModel.id == RecipeTimelineEvent.recipe_id)
            .where(
                RecipeTimelineEvent.user_id == actor_id,
                RecipeModel.group_id == self.group_id,
                RecipeTimelineEvent.cooking_source.in_(sources),
                RecipeTimelineEvent.timestamp >= start,
                RecipeTimelineEvent.timestamp < end,
            )
            .execution_options(yield_per=500)
        )
        result = self.session.execute(statement)
        try:
            for recipe_id, timestamp, source in result:
                yield CookingHistoryEvent(recipe_id, timestamp, source)
        finally:
            result.close()

    def bounds(self, actor_id: UUID, end: datetime, sources: list[str]) -> list[CookingHistoryBounds]:
        statement = (
            select(
                RecipeTimelineEvent.recipe_id,
                func.min(RecipeTimelineEvent.timestamp),
                func.max(case((RecipeTimelineEvent.cooking_source == "manual", RecipeTimelineEvent.timestamp))),
                func.max(case((RecipeTimelineEvent.cooking_source == "mealplan", RecipeTimelineEvent.timestamp))),
            )
            .join(RecipeModel, RecipeModel.id == RecipeTimelineEvent.recipe_id)
            .where(
                RecipeTimelineEvent.user_id == actor_id,
                RecipeModel.group_id == self.group_id,
                RecipeTimelineEvent.cooking_source.in_(sources),
                RecipeTimelineEvent.timestamp < end,
            )
            .group_by(RecipeTimelineEvent.recipe_id)
        )
        return [CookingHistoryBounds(*row) for row in self.session.execute(statement)]

    def preferences(self, actor_id: UUID) -> list[CookingHistoryPreference]:
        statement = (
            select(UserToRecipe.recipe_id, UserToRecipe.rating, UserToRecipe.is_favorite)
            .join(RecipeModel, RecipeModel.id == UserToRecipe.recipe_id)
            .where(UserToRecipe.user_id == actor_id, RecipeModel.group_id == self.group_id)
        )
        return [CookingHistoryPreference(*row) for row in self.session.execute(statement)]

    def has_unclassified_events(self, actor_id: UUID) -> bool:
        statement = (
            select(RecipeTimelineEvent.id)
            .join(RecipeModel, RecipeModel.id == RecipeTimelineEvent.recipe_id)
            .where(
                RecipeTimelineEvent.user_id == actor_id,
                RecipeModel.group_id == self.group_id,
                RecipeTimelineEvent.cooking_source.is_(None),
            )
            .limit(1)
        )
        return self.session.execute(statement).first() is not None

    def recipes(self, recipe_ids: set[UUID4]) -> dict[UUID4, CookingInsightRecipe]:
        if not recipe_ids:
            return {}
        statement = select(RecipeModel.id, RecipeModel.slug, RecipeModel.name, RecipeModel.image).where(
            RecipeModel.group_id == self.group_id, RecipeModel.id.in_(recipe_ids)
        )
        recipes = [CookingInsightRecipe.model_validate(row) for row in self.session.execute(statement).mappings()]
        return {recipe.id: recipe for recipe in recipes}
