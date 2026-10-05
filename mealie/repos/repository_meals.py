from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy import case, func, select, update
from sqlalchemy.exc import OperationalError

from mealie.db.models.household import GroupMealPlan
from mealie.db.models.users.users import User
from mealie.schema.meal_plan.new_meal import (
    LeftoverPlanEntry,
    LeftoverPlanEntryPagination,
    PlanEntrySource,
    ReadPlanEntry,
    SavePlanEntry,
)
from mealie.schema.response.pagination import PaginationQuery

from .repository_generic import HouseholdRepositoryGeneric


class MealPlanError(Exception):
    def __init__(self, status_code: int, message_key: str, meal_ids: list[int] | None = None):
        self.status_code = status_code
        self.message_key = message_key
        self.meal_ids = meal_ids or []
        super().__init__(message_key)


class RepositoryMeals(HouseholdRepositoryGeneric[ReadPlanEntry, GroupMealPlan]):
    def _entry(self, entry_id: str | int | UUID) -> GroupMealPlan:
        statement = (
            self._query()
            .filter_by(**self._filter_builder(id=entry_id))
            .execution_options(populate_existing=True)
        )
        entry = self.session.execute(statement).unique().scalars().one_or_none()
        if entry is None:
            raise MealPlanError(404, "mealplan.leftover-source-not-found")
        return entry

    def _guard_rows(self, entry_ids: set[int]) -> dict[int, GroupMealPlan]:
        guarded = {}
        for entry_id in sorted(entry_ids):
            entry = self._entry(entry_id)
            statement = (
                update(GroupMealPlan)
                .filter_by(**self._filter_builder(id=entry_id))
                .where(GroupMealPlan.leftover_revision == entry.leftover_revision)
                .values(leftover_revision=GroupMealPlan.leftover_revision + 1)
                .execution_options(synchronize_session=False)
            )
            result = self.session.execute(statement)
            if result.rowcount != 1:
                raise MealPlanError(409, "mealplan.leftover-concurrent-change")
            self.session.refresh(entry)
            guarded[entry_id] = entry
        return guarded

    def _dependents(self, source_id: int) -> list[GroupMealPlan]:
        statement = self._query().filter_by(**self._filter_builder(leftover_source_id=source_id))
        return list(self.session.execute(statement).unique().scalars().all())

    def _reserved(self, source_id: int, excluding_id: int | None = None) -> int:
        statement = (
            select(func.coalesce(func.sum(GroupMealPlan.eaten_portions), 0))
            .select_from(GroupMealPlan)
            .filter_by(**self._filter_builder(leftover_source_id=source_id))
        )
        if excluding_id is not None:
            statement = statement.where(GroupMealPlan.id != excluding_id)
        return int(self.session.scalar(statement) or 0)

    def _validate_source(self, data: SavePlanEntry, source: GroupMealPlan, entry_id: int | None = None):
        if source.id == entry_id or source.leftover_source_id is not None or source.prepared_portions is None:
            raise MealPlanError(422, "mealplan.leftover-invalid-source")
        if data.date <= source.date:
            raise MealPlanError(422, "mealplan.leftover-invalid-date")
        if (data.recipe_id, data.title, data.text) != (source.recipe_id, source.title, source.text):
            raise MealPlanError(422, "mealplan.leftover-source-identity")
        available = source.prepared_portions - (source.eaten_portions or 0) - self._reserved(source.id, entry_id)
        if (data.eaten_portions or 0) > available:
            raise MealPlanError(409, "mealplan.leftover-insufficient-portions")

    def _validate_dependents(self, entry: GroupMealPlan, data: SavePlanEntry | None = None):
        dependents = self._dependents(entry.id)
        if not dependents:
            return
        meal_ids = [dependent.id for dependent in dependents]
        if data is None or data.leftover_source_id is not None or data.prepared_portions is None:
            raise MealPlanError(409, "mealplan.leftover-linked-meals", meal_ids)
        if (data.recipe_id, data.title, data.text) != (entry.recipe_id, entry.title, entry.text):
            raise MealPlanError(409, "mealplan.leftover-linked-meals", meal_ids)
        if any(dependent.date <= data.date for dependent in dependents):
            raise MealPlanError(409, "mealplan.leftover-linked-meals", meal_ids)
        if data.prepared_portions - (data.eaten_portions or 0) < sum(
            dependent.eaten_portions or 0 for dependent in dependents
        ):
            raise MealPlanError(409, "mealplan.leftover-linked-meals", meal_ids)

    def _validate_owner(self, data: SavePlanEntry, entry: GroupMealPlan | None = None):
        owner = self.session.get(User, data.user_id)
        if (
            owner is None
            or (self.group_id and data.group_id != self.group_id)
            or (self.household_id and owner.household_id != self.household_id)
            or (entry and (data.group_id != entry.group_id or data.user_id != entry.user_id))
        ):
            raise MealPlanError(422, "mealplan.leftover-invalid-owner")

    def _rollback_error(self, error: Exception):
        self.session.rollback()
        if isinstance(error, ValidationError):
            raise MealPlanError(422, "mealplan.leftover-invalid-portions") from error
        if isinstance(error, OperationalError):
            sqlite_code = getattr(error.orig, "sqlite_errorcode", None)
            postgres_code = getattr(error.orig, "pgcode", None)
            if sqlite_code in {5, 6, 517} or postgres_code in {"40001", "40P01", "55P03"}:
                raise MealPlanError(409, "mealplan.leftover-concurrent-change") from error
        raise error

    def create(self, data: ReadPlanEntry | BaseModel | dict) -> ReadPlanEntry:
        try:
            payload = data if isinstance(data, dict) else data.model_dump()
            saved = SavePlanEntry.model_validate(payload)
            self._validate_owner(saved)
            if saved.leftover_source_id is not None:
                sources = self._guard_rows({saved.leftover_source_id})
                self._validate_source(saved, sources[saved.leftover_source_id])
            entry = GroupMealPlan(session=self.session, **saved.model_dump())
            self.session.add(entry)
            self.session.flush()
            entry_id = entry.id
            self.session.commit()
            return self._enrich([self.schema.model_validate(self._entry(entry_id))])[0]
        except Exception as error:
            self._rollback_error(error)
            raise

    def update(self, match_value: str | int | UUID, new_data: dict | BaseModel) -> ReadPlanEntry:
        try:
            payload: dict[str, Any] = (
                new_data if isinstance(new_data, dict) else new_data.model_dump(exclude_unset=True)
            )
            entry = self._entry(match_value)
            old_source_id = entry.leftover_source_id
            proposed_source_id = payload.get("leftover_source_id", payload.get("leftoverSourceId", old_source_id))
            guard_ids = {entry.id}
            if old_source_id is not None:
                guard_ids.add(old_source_id)
            if proposed_source_id is not None:
                guard_ids.add(proposed_source_id)
            guarded = self._guard_rows(guard_ids)
            entry = guarded[entry.id]
            if entry.leftover_source_id != old_source_id:
                raise MealPlanError(409, "mealplan.leftover-concurrent-change")
            merged = SavePlanEntry.model_validate(entry).model_dump()
            for field_name, field in SavePlanEntry.model_fields.items():
                if field_name in payload:
                    merged[field_name] = payload[field_name]
                elif field.alias is not None and field.alias in payload:
                    merged[field_name] = payload[field.alias]
            saved = SavePlanEntry.model_validate(merged)
            self._validate_owner(saved, entry)
            self._validate_dependents(entry, saved)
            if saved.leftover_source_id is not None:
                self._validate_source(saved, guarded[saved.leftover_source_id], entry.id)
            for field_name, value in saved.model_dump().items():
                setattr(entry, field_name, value)
            self.session.commit()
            return self._enrich([self.schema.model_validate(self._entry(entry.id))])[0]
        except Exception as error:
            self._rollback_error(error)
            raise

    def delete(self, value, match_key: str | None = None) -> ReadPlanEntry:
        try:
            entry = self._entry(value)
            old_source_id = entry.leftover_source_id
            guard_ids = {entry.id}
            if old_source_id is not None:
                guard_ids.add(old_source_id)
            guarded = self._guard_rows(guard_ids)
            entry = guarded[entry.id]
            if entry.leftover_source_id != old_source_id:
                raise MealPlanError(409, "mealplan.leftover-concurrent-change")
            self._validate_dependents(entry)
            result = self._enrich([self.schema.model_validate(entry)])[0]
            self.session.delete(entry)
            self.session.commit()
            return result
        except Exception as error:
            self._rollback_error(error)
            raise

    def _enrich(self, entries: list[ReadPlanEntry]) -> list[ReadPlanEntry]:
        source_ids = {entry.id for entry in entries if entry.prepared_portions is not None}
        source_ids.update(entry.leftover_source_id for entry in entries if entry.leftover_source_id is not None)
        if not source_ids:
            return entries
        source_query = self._query().filter_by(**self._filter_builder()).where(GroupMealPlan.id.in_(source_ids))
        sources = {source.id: source for source in self.session.execute(source_query).unique().scalars().all()}
        totals_query = (
            select(GroupMealPlan.leftover_source_id, func.sum(GroupMealPlan.eaten_portions))
            .select_from(GroupMealPlan)
            .filter_by(**self._filter_builder())
            .where(GroupMealPlan.leftover_source_id.in_(source_ids))
            .group_by(GroupMealPlan.leftover_source_id)
        )
        totals = dict(self.session.execute(totals_query).all())
        for entry in entries:
            if entry.prepared_portions is not None:
                entry.expected_leftovers = entry.prepared_portions - (entry.eaten_portions or 0)
                entry.reserved_leftovers = int(totals.get(entry.id) or 0)
                entry.available_leftovers = entry.expected_leftovers - entry.reserved_leftovers
            if entry.leftover_source_id is not None and entry.leftover_source_id in sources:
                entry.leftover_source = PlanEntrySource.model_validate(
                    sources[entry.leftover_source_id], from_attributes=True
                )
        return entries

    def get_one(self, value: str | int | UUID, key=None, any_case=False, override_schema=None):
        entry = super().get_one(value, key, any_case, override_schema)
        if entry is not None and override_schema is None:
            return self._enrich([entry])[0]
        return entry

    def page_all(self, pagination: PaginationQuery, override=None, search: str | None = None):
        page = super().page_all(pagination, override, search)
        if override is None:
            page.items = self._enrich(page.items)
        return page

    def get_leftovers(
        self, target_date: date, pagination: PaginationQuery, editing_entry_id: int | None = None
    ) -> LeftoverPlanEntryPagination:
        editing = self._entry(editing_entry_id) if editing_entry_id is not None else None
        totals = (
            select(
                GroupMealPlan.leftover_source_id.label("source_id"),
                func.sum(GroupMealPlan.eaten_portions).label("reserved"),
            )
            .select_from(GroupMealPlan)
            .filter_by(**self._filter_builder())
            .group_by(GroupMealPlan.leftover_source_id)
            .subquery()
        )
        capacity = GroupMealPlan.prepared_portions - GroupMealPlan.eaten_portions - func.coalesce(totals.c.reserved, 0)
        if editing is not None and editing.leftover_source_id is not None:
            capacity = capacity + case(
                (GroupMealPlan.id == editing.leftover_source_id, editing.eaten_portions or 0), else_=0
            )
        query = (
            self._query(with_options=False)
            .filter_by(**self._filter_builder())
            .outerjoin(totals, totals.c.source_id == GroupMealPlan.id)
            .where(GroupMealPlan.leftover_source_id.is_(None), GroupMealPlan.date < target_date, capacity > 0)
        )
        requested = pagination.model_copy()
        requested.order_by = requested.order_by or "date,id"
        query, total, total_pages = self.add_pagination_to_query(query, requested)
        query = query.options(*self.schema.loader_options())
        entries = self._enrich(
            [self.schema.model_validate(entry) for entry in self.session.execute(query).unique().scalars().all()]
        )
        items = []
        for entry in entries:
            credit = (editing.eaten_portions or 0) if editing and editing.leftover_source_id == entry.id else 0
            items.append(
                LeftoverPlanEntry.model_validate(
                    {**entry.model_dump(), "allocatable_portions": (entry.available_leftovers or 0) + credit}
                )
            )
        return LeftoverPlanEntryPagination(
            page=requested.page,
            per_page=requested.per_page,
            total=total,
            total_pages=total_pages,
            items=items,
        )

    def get_today(self, tz=UTC) -> list[ReadPlanEntry]:
        if not self.household_id:
            raise Exception("household_id not set")

        today = datetime.now(tz=tz).date()
        stmt = self._query().filter(
            GroupMealPlan.date == today, GroupMealPlan.household_id == self.household_id
        )
        plans = self.session.execute(stmt).scalars().all()
        return self._enrich([self.schema.model_validate(plan) for plan in plans])

    def get_meals_by_date_range(self, start_date: datetime, end_date: datetime) -> list[ReadPlanEntry]:
        if not self.household_id:
            raise Exception("household_id not set")

        stmt = self._query().filter(
            GroupMealPlan.date >= start_date.date(),
            GroupMealPlan.date <= end_date.date(),
            GroupMealPlan.household_id == self.household_id,
        )
        plans = self.session.execute(stmt).scalars().all()
        return self._enrich([self.schema.model_validate(plan) for plan in plans])
