## Context

See `proposal.md` for motivation and reviewable scope assumptions. The contracts are in `specs/cooking-history-events/spec.md` and `specs/cooking-history-insights/spec.md`.

Observed implementation facts:

- `mealie/schema/recipe/recipe_timeline_events.py` defines `system`, `info`, and `comment` event types, but no semantic cooking field. `mealie/db/models/recipe/recipe_timeline.py` stores the actor, recipe, display subject, and UTC timestamp. Its household association is the recipe owner's household, not necessarily the actor's household.
- `frontend/components/Domain/Recipe/RecipeLastMade.vue` creates a `comment` event with a translated "user made this" subject. It stores the chosen date at local 23:59:59, optionally creates events for selected linked recipes, and separately patches household last-made state. `RecipeService.update_last_made` does not create a timeline event.
- `mealie/services/scheduler/tasks/create_timeline_events.py` generates `info` events for today's meal-plan entries using the meal-plan actor. This is inferred activity, not confirmation of who cooked. It already suppresses duplicates on subsequent runs.
- `RecipeService.get_one` reads the group-wide recipe repository; authenticated users can read recipes owned by other households in that group. The new endpoint must retain this read scope while restricting event actors and personal preferences.
- `RepositoryUserRatings.get_by_user` filters only by actor in its explicit SQL statement; relying on its repository's configured group is insufficient for this endpoint.
- `frontend/pages/g/[groupSlug]/recipes/timeline.vue` provides a group-global timeline. It is not a personal aggregate API. Navigation entries originate in `frontend/components/Layout/DefaultLayout.vue`.
- Existing stack: FastAPI/Pydantic/SQLAlchemy on Python 3.12; Nuxt 3/Vue 3/Vuetify 3 with MDI icons, generated API types, Vitest, and pytest. Backend CI already runs SQLite and PostgreSQL in `.github/workflows/test-backend.yml`.

## Goals / Non-Goals

**Goals:**

- Keep timeline display semantics independent from cooking provenance.
- Put access-controlled data selection in one repository boundary and testable date/ranking calculations in one service.
- Keep work proportional to the selected window and the authenticated user's accessible records; hydrate only displayed recipe summaries.
- Retain existing frontend styling, icons, translations, recipe imagery, and authentication conventions.

**Non-Goals:**

- No generic analytics framework, AI integration, history cache, preference snapshot store, or new charting package.
- No redesign of event permissions or legacy rating validation beyond the new provenance and insights contracts.
- No additional cooking events in the last-made PATCH endpoint and no change to scheduler deduplication semantics.

## Decisions

### 1. Add nullable provenance without replacing timeline types

Add nullable `cooking_source` to the timeline model with allowed schema values `manual` and `mealplan`; expose the usual camel-case API alias `cookingSource`. Preserve the existing `event_type` enum. Add an Alembic revision with null defaults and a composite `(user_id, cooking_source, timestamp)` index to support actor/source/window selection.

Extend the input/create/output schemas. Keep provenance read-only on update: accept omission and an identical value if necessary for a round-trip client, but reject any different value rather than silently ignoring it. Text/image updates preserve the stored value. Unknown create values return 422.

The existing manual component supplies `manual` for its primary and selected linked events. The timeline creation controller infers the current actor when omitted and returns 403 if a manual request names someone else; public creation of `mealplan` returns 422. The internal scheduler supplies `mealplan` directly using its existing actor. Generic events without provenance retain current behavior. The existing last-made PATCH remains separate, avoiding double recording.

Alternative rejected: a new `cooked` event type would mix semantic source with display categories and require changing current timeline filtering/badges. Parsing subjects would be locale-dependent and falsely classify free text. Moving event creation into last-made PATCH would duplicate the existing manual workflow and turn a state update into an unrequested history mutation.

### 2. Introduce a self-only endpoint and a narrow calculation boundary

Add `GET /api/users/self/cooking-insights` through a dedicated users controller using `UserAPIRouter` and `BaseUserController`, registered in `mealie/routes/users/__init__.py`. Register the static self path without a generic user-id variant. Derive actor and group solely from the authenticated user; reject identity/group overrides in query validation. Set `Cache-Control: private, no-store` explicitly; the existing CRUD header helper only applies when a body has `updatedAt`.

Proposed homes:

- `mealie/schema/user/cooking_insights.py`: query, recipe-evidence, collection, month, coverage, and response models.
- `mealie/repos/repository_cooking_history.py`: explicit actor/group-scoped evidence queries, surfaced through the repository factory.
- `mealie/services/recipe/cooking_insights_service.py`: normalization, eligibility, deduplication, sufficiency gates, ordering, and reason codes.
- `mealie/routes/users/cooking_insights.py`: validation, authenticated identity, response headers, and service invocation only.

Use SQLAlchemy expressions and bound parameters, not client-controlled query-filter strings. Every event/preference query joins a surviving recipe and requires `RecipeModel.group_id == authenticated_group_id` plus the relevant row's `user_id == authenticated_user_id`. Do not constrain recipe ownership to the actor's household, use public visibility flags as a substitute for authenticated read policy, or reuse unscoped ratings results. Fail closed if required actor/group context is absent, including for administrators.

Alternative rejected: frontend aggregation of paginated timeline/ratings APIs would be incomplete unless every page were fetched and would repeat privacy and ranking logic in the browser. A household analytics endpoint would require different attribution/privacy contracts from the selected personal scope.

### 3. Normalize local dates in Python and keep database reads narrow

Use `zoneinfo.ZoneInfo` and existing UTC-aware timestamp behavior from `NaiveDateTime`. Resolve date defaults once per request. The API takes a complete pair of local dates or neither, a valid zone, inferred inclusion, and the bounded section limit. Convert the start midnight and the midnight after the inclusive end into UTC query bounds. Calendar-date semantics deliberately include today's end-of-day manual events even before 23:59:59; future local dates do not count.

Retrieve only recipe id, timestamp, and source for classified window events, using streaming/batched rows rather than loading nested event schemas or comments/images. Accumulate local-date sets per recipe; a manual event wins if both sources exist on a recipe/day. Each selected linked recipe is its own recipe/day, not a second count for its parent. Monthly cooking-day totals sum recipe/day pairs; monthly active-date totals deduplicate across recipes as well.

Use a separate grouped aggregate query over eligible sources on or before the end boundary to get each recipe's minimum timestamp and per-source maximum timestamps, including dates before the selected start. Convert the maxima to local dates and select the later date, preferring recorded evidence when both sources have the same last date; this preserves source-aware last-date labels without reading an unbounded pre-window event history. Use the minima to find the first available classified date. Join current preference rows under the same actor/group rules. Check unclassified coverage with an actor/group/read-scoped existence query independently of the selected window; do not load or classify legacy subjects.

Hydrate the union of displayed recipe ids once with minimal navigation/image metadata. Query count must remain constant as the number of displayed recipes grows, with no per-recipe queries. Apply limits only after complete counts and deterministic ranking, and supply `total`/`truncated` per collection. The twelve month buckets are never truncated; their recurring-recipe collections use the same limit individually.

Alternative rejected: database-specific time-zone/date grouping would duplicate logic between SQLite and PostgreSQL. Loading all historical events for last-date lookups would make an old account increasingly expensive. Truncating raw events before calculating insights would silently distort rankings.

### 4. Keep ranking simple, deterministic, and evidenced

Implement the exact thresholds and tie-breakers in the insights spec as named service constants: 365-day default, 1,827-day maximum, two days for repeats, 30 days for neglect, seven inclusive local dates for recent-cooking exclusion, and the 730-day/twelve-active-date/two-year recurrence gate. Preference fields are current, not reconstructed as of a historical end date. Normalize invalid/non-finite legacy ratings only in the insight input; do not mutate them.

The service returns recorded and inferred-only counts, all-time-to-end last eligible dates, gaps relative to `endDate`, and current normalized personal preferences. A favorite lacking eligible history has a null last date/gap and a dedicated missing-history group. It is not called "never cooked."

Recommendations have three priority tiers from the spec, not a fitted or opaque score. Attach a primary reason code (`neglected_favorite`, `recurring_month`, or `liked_recipe`) and structured evidence. Add `no_recorded_history` and `includes_inferred_activity` flags where applicable. Unknown last dates sort after known gaps in otherwise tied recommendations. A valid poor rating excludes a favorite from recommendations but does not remove it from the descriptive favorite views.

Alternative rejected: a blended score or AI-generated reason would introduce tuning, nondeterminism, and explanations unsupported by the actual records. Hemisphere-based season labels would invent context the application does not have.

### 5. Return one bounded snapshot with a transparent coverage envelope

Response shape:

- `filters`: resolved start/end local dates, zone, inclusion policy, and limit.
- `coverage`: first eligible classified cooking date on or before the end date, `hasUnclassifiedEvents` across accessible personal history, window cooking-day/active-date totals, recorded/inferred-only totals, and the seasonal sufficiency flag. The first date describes available evidence, not the start of complete logging.
- `frequentMeals`, `neglectedFavorites`, `favoritesWithoutHistory`, and `recommendations`: `{ items, total, truncated }` collections with shared recipe/evidence models and reason fields where relevant.
- `monthlyHabits`: twelve ordered buckets, each with cooking-day and active-date counts and a bounded recurring-recipe collection; sufficient-history status is explicit.

Each displayed recipe carries id, slug, name, and image metadata usable by existing recipe image/link conventions. Never expose another actor's data or raw event comment/image contents. Recalculate on every request so ordinary edits appear on the next read. No shared cache or materialized insight table is introduced.

Alternative rejected: separate requests for each section complicate loading/error states and permit mismatched filters. Persisting a snapshot would require invalidation across timeline changes, favorite/rating updates, and recipe deletion.

### 6. Extend the current recipe experience without changing its design system

Add `frontend/pages/g/[groupSlug]/recipes/insights.vue` with group-only/authenticated access and an own-group navigation entry next to the recipe timeline in `DefaultLayout.vue`. Use the existing user API client in `frontend/lib/api/user/users.ts`, generated types, and a focused `use-cooking-insights` composable for filters and latest-request-only state. Clear personal data on logout/group changes; never reuse a response across identities. Detect the browser's IANA zone with a UTC fallback and send it explicitly.

Use a compact unframed page header and labeled date controls, preset ranges (30 days, 90 days, one year, three years), an inferred-activity checkbox, and tabs for the four views. Presets end on local today. Favorites without history form a separate group within the neglected-favorites view. Use existing recipe imagery and navigation components for repeated items, not nested section cards or a new hero. Use existing Vuetify/MDI icons and tooltips rather than introducing Lucide or another icon system.

For monthly history use labeled counts and restrained horizontal bars alongside an accessible table/list; no hover-only values or dependence on color alone. Preserve Mealie's existing theme/type tokens, keyboard focus, translations, and responsive wrapping. The design skill's search did not produce a verified relevant visualization match; these accessibility/layout choices use its general defaults and existing application conventions instead of importing its off-topic marketing recommendations.

Expose loading, retryable error, no-recorded-activity, no-repeat, no-neglected-favorite, no-recommendation, and insufficient-seasonal-history states independently. When results are limited, show the returned/eligible count and a bounded option to request up to 50; do not imply the visible items are the entire history. Coverage notes describe data limitations rather than application features. Translate reason codes on the client; do not add explanatory marketing copy or keyboard-shortcut prose.

Alternative rejected: reusing the group timeline as the data source changes the personal scope. New chart libraries and a new visual design system add dependencies without improving a twelve-bucket display.

## Risks / Trade-offs

- Legacy cooking history remains unclassified -> do not backfill from text; show coverage limitations and useful current-preference suggestions even before classified history accrues. A historical classification/backfill feature would require a separately reviewed change.
- Automatic events attribute a planner, not a verified cook -> keep inferred activity off by default and label source breakdown/evidence when included.
- Distinct recipe/day semantics collapse multiple servings or repeated meals on one date -> explicitly call the metric cooking days, not meal occurrences or portions.
- Time-zone/DST boundaries can change apparent dates -> derive UTC bounds from local midnights and test DST, month/year rollover, fractional-hour zones, and today's end-of-day timestamps on both databases.
- Raw repository SQL can bypass automatic group filtering -> require explicit joined actor/group predicates and isolation tests using another user in the same household, another household in the same group, and another group.
- Large selected histories can be expensive -> bound the window, stream narrow evidence rows, use grouped pre-window maxima and the composite index, hydrate displayed ids in one query, and verify constant query count with a seeded large fixture.
- Current ratings can disagree with past choices -> echo the historical end date and label preferences as current; no implied preference time travel.
- Shared worktree includes existing recipe and navigation edits -> integrate with those edits without reverting or restyling unrelated work; avoid global generation/formatting churn.

## Migration Plan

1. Add the nullable column and index through Alembic using patterns compatible with SQLite and PostgreSQL. Preserve all existing rows and defaults; do not rewrite subjects or assign provenance to old events.
2. Deploy schema/backend support first, then the manual frontend writer and insight page. During mixed-version operation old clients still produce null provenance and the page reports incomplete coverage. The scheduler can begin producing inferred classified records once backend support is deployed.
3. Generate only affected API types/schema exports/route helpers using existing `dev/code-generation` entry points, and update API documentation plus the existing API-usage documentation with provenance and query semantics.
4. Verify upgrade/downgrade and mixed-version timeline CRUD in disposable SQLite/PostgreSQL databases, then run the focused tests and existing lint/typecheck/CI gates. Do not migrate the user's live development database during proposal creation.
5. Roll back page/navigation and writers before removing schema support. Prefer leaving the harmless additive column/index while older code runs. An explicit downgrade drops only the new index/column and therefore loses provenance; document that loss and take a backup before downgrade. Existing timeline content remains intact.

## Validation Strategy

- Extend existing timeline API tests for null/default/invalid sources, manual actor enforcement, reserved inferred provenance, edit preservation, deletion effects, and legacy events.
- Extend existing scheduler tests for inferred source and unchanged rerun deduplication; verify the manual parent/linked writer submits source without adding a second event via last-made PATCH.
- Add deterministic service tests with fixed dates and explicit expected outputs for all four rankings, missing/invalid ratings, source overlap, before-window last dates, the exact 29/30-day and seven-date boundaries, leap days, recurrence gates, and month/year/DST conversions.
- Add self-endpoint tests beside existing user-recipe tests for authentication, input bounds, identity override rejection, isolation, deletion/read-scope changes, totals/truncation, no mutations, and read-after-edit results. Validate equivalent results under the existing SQLite/PostgreSQL matrix.
- Reuse existing Vitest/i18n helpers for API/composable tests: payload/time-zone propagation, latest-request-only results, source toggling, retry and empty states, reason localization, and parent/linked manual payloads. The current Vitest setup is not a complete Nuxt component-mount harness; do not add a broad test framework just for this page.
- Run browser acceptance after implementation at desktop and narrow mobile widths for navigation, recipe images/links, all states, keyboard controls, accessible monthly counts, and no overlap/overflow. None of these implementation checks are claimed as executed by this planning-only workflow.

## Implementation Verification Record

Implementation checks below were executed during the subsequent apply workflow on 2026-10-05; the planning-stage statement above remains historical context.

### Completed Checks

- Final focused backend suite: 71 tests passed on SQLite and 71 on an isolated PostgreSQL 16 instance, including timeline compatibility, scheduler provenance, query validation, deterministic rankings, actor/group isolation, read-after-edit behavior, null/legacy timestamps, and administration scope.
- Nullable migration upgrade/downgrade passed on disposable SQLite and PostgreSQL databases. Legacy rows retained null provenance and ordinary content survived downgrade. The revision follows the concurrently added leftover-planning revision, maintaining one migration head.
- A seeded 10,000-event/100-recipe fixture returned complete counts with five queries at limits 1 and 50 and at default/maximum windows. SQLite's query plan used the composite actor/source/timestamp index; PostgreSQL produced equivalent results and query counts.
- Repository-wide `ruff check mealie` and `mypy mealie` passed; mypy checked 419 source files. Owned backend files passed Ruff formatting checks.
- All frontend Vitest tests passed: 190 tests in 17 files at the final run. Owned insight/client/type/manual-writer/middleware files passed ESLint. Guard tests live under `frontend/tests`, outside runtime middleware discovery.
- Scoped schema/type/route generation and application imports passed. Generation uses relative output paths to support space-containing workspace paths, formats only affected TypeScript files, and cannot invoke broad lint with an empty output list. Shared provenance lives in the lightweight model module to avoid package-export import cycles.
- Live own-group view loaded successfully. Foreign-group navigation redirected without displaying personal results after fixing the existing guard to return its navigation result; signed-out and own-group guard cases passed unit tests.
- Isolated browser response fixtures exercised repeated meals, neglected favorites, separately labeled missing history, monthly sparse/recurring states, inferred inclusion, evidence-based recommendations, and preference-only suggestions. Twelve month rows and three-year preset behavior were verified, including a keyboard-opened preset control.
- Fresh page loads at CSS widths 375, 768, 1024, and 1440 had no horizontal overflow and all date controls fit. Desktop/mobile screenshots and actual recipe-image load checks passed. A stale desktop sidebar reservation observed during background-tab resizing was not reproduced on fresh mobile loads; no unrelated shell redesign was made.
- A 503 response hid stale counts and exposed retry; retry restored valid results. Latest-request and identity-change behavior passed focused Vitest tests. Browser fixtures/interceptors were removed and the QA page restored to live data.
- Manual parent/selected-linked cooking acceptance captured exactly two event POSTs carrying `manual`, two distinct recipe ids, the unchanged selected timestamp/comment, and the expected two last-made PATCHes. Writes were intercepted rather than persisted to the user's recipes.
- API documentation regenerated; its embedded JSON parsed and included the self endpoint and response schema. The query contract contains the five documented fields plus the existing shared language header. The usage guide documents coverage, current preferences, limits, and downgrade loss.

### Remaining Gate Blockers

- Full backend pytest was run and reported four failures in existing webhook tests: `test_event_listener_get_meals_by_date_range`, `test_get_meals_by_date_range`, `test_get_meals_by_date_range_single_day`, and `test_get_meals_by_date_range_no_overlap`. They raise `MealPlanError` from the concurrently changed leftover-planning path; cooking-insights tests passed. These unrelated failures were not changed or waived.
- Full frontend ESLint reported 236 indentation errors in the pre-existing shopping-list copy, CRUD, and sorting test files. `git diff --exit-code` confirmed those files were unchanged from HEAD. They were not reformatted as part of this change.
- Repository-wide Ruff formatting reported 23 unrelated files requiring formatting, including installed skill scripts, concurrent leftover-planning files, the users repository, and an existing backup test. Owned feature files were clean; unrelated files were left untouched.
- Task 7.3 remains unchecked because broad gates are not green. Task 7.6 remains unchecked pending gate clearance and final archive-readiness verification. Feature acceptance is complete, but the change is not claimed archive-ready.

### Deployment and Rollback Handoff

Apply the additive database migration before deploying the scheduler/manual writer and UI. Old payloads remain compatible and unclassified. Keep the nullable column/index during an application rollback when possible; explicit downgrade loses provenance while retaining timeline content. Preserve the single migration chain with the neighboring leftover-planning revision. PostgreSQL was installed for isolated testing, not configured as a persistent service; the temporary test server is stopped during handoff. Existing application servers remain available at `http://localhost:3000/g/home/recipes/insights`.