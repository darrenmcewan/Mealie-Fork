## Why

Mealie already stores personal ratings, favorites, and recipe timeline activity, but users must inspect individual recipes to understand their cooking habits or decide what to revisit. Turning reliable cooking records into explainable insights makes that history useful without treating comments, recipe creation, or automatically scheduled meals as confirmed cooking.

## What Changes

- Add an authenticated Cooking Insights view with frequently repeated meals, neglected favorites, calendar-month habits, and personal recommendations.
- Add stable, optional cooking provenance to timeline events, keeping existing event types and display subjects compatible. Distinguish manually recorded cooking from meal-plan-generated activity.
- Compute insights server-side from the signed-in user's accessible recipe history and current personal ratings/favorites, with bounded date windows, deterministic ordering, and recipe links.
- Count recorded cooking by default; allow an explicit, clearly labeled opt-in to include automatically inferred meal-plan activity. Exclude unclassified legacy events instead of guessing from translated subjects.
- Show evidence and coverage limitations, including empty, insufficient-history, loading, and error states. Recommendations use transparent rules rather than an external AI service.

### Planning Assumptions

The user was unavailable for clarification and requested autonomous decisions. This proposal includes all four suggested views, uses personal rather than household/group-wide history, and interprets seasonal habits as calendar-month history without hemisphere or climate assumptions. These scope choices remain reviewable before implementation.

### Non-Goals

- Household/group analytics, other-user comparisons, dietary or medical guidance, ingredient-seasonality predictions, and collaborative filtering.
- External AI calls, background recommendation jobs, persisted recommendation profiles, or automatic meal-plan changes.
- Inferring historical cooking from free-text subjects or manufacturing a history from a single household `lastMade` value.
- Redesigning the existing timeline, rating system, or recipe cards.

## Capabilities

### New Capabilities

- `cooking-history-events`: Backward-compatible structured cooking provenance on timeline events and its integration with manual cooking and automatic meal-plan writers.
- `cooking-history-insights`: Personal, access-scoped history aggregation, four explainable insight views, and their filtering, evidence, and empty-state behavior.

### Modified Capabilities

None. The project's main capability inventory is currently empty; no existing specification is being replaced.

## Impact

- Backend: timeline model/schema and Alembic migration; manual cooking and scheduler writers; a self-scoped insights route, repository queries, and deterministic calculation service using existing FastAPI, SQLAlchemy, and Pydantic conventions.
- Frontend: a group-context Cooking Insights page and navigation entry; existing user API client, generated types, recipe links/images, Vuetify controls, and translated copy.
- Compatibility: additive API/schema fields with null defaults for old events and omitted fields; preserve existing timeline CRUD and display behavior. No new external service or runtime dependency is planned.
- Verification: extend timeline and scheduler regression tests; add focused calculation/API/frontend tests and multi-user/group isolation coverage. Validate migration behavior for SQLite and PostgreSQL.
- Planning only: this change creates artifacts, not application code. Existing working-tree edits are outside its scope.