## Context

See `proposal.md` for motivation and `specs/leftover-aware-planning/spec.md` for the behavior contract. This document is a proposed implementation, not a description of existing leftover functionality.

Observed implementation:

- `mealie/db/models/household/mealplan.py` stores dates, meal types, recipe-or-note content, and a user reference. Household ownership is derived through the user, not a concrete meal-plan household column.
- `mealie/schema/meal_plan/new_meal.py` provides create/save/update/read schemas and the breakfast, lunch, dinner, and side enum. Entries require a recipe or title and use integer IDs.
- `mealie/routes/households/controller_mealplan.py` uses `RepositoryMeals` through CRUD mixins and publishes meal-created events. `RepositoryMeals` currently adds date-based reads to `HouseholdRepositoryGeneric`.
- `mealie/repos/repository_generic.py` commits inside create, update, and delete. Calling these methods after a separate availability check would not protect against concurrent reservations.
- The planner editor, view, API client, and `use-group-mealplan.ts` already cover recipe/note creation, random planning, edits, date navigation, and drag moves. The editor currently resets the dialog before an asynchronous save result is known, and a failed move can leave local state ahead of the saved plan.
- Recipe servings are a float with a default of zero, so they are not reliable whole-number prepared-portion defaults. Counts will be explicitly entered and will not mutate recipe servings.
- Nearby schema and household meal-plan integration tests exist; frontend tooling uses Nuxt 3, Vue, Vuetify, and Vitest. Feature documentation currently suggests note-only entries for leftovers and calls one meal type Snack, whereas the current API enum is `side`; this change follows the API enum without introducing another type.
- `openspec list --specs` found no main capability specs. Existing frontend worktree edits must be preserved during later implementation.

## Goals / Non-Goals

**Goals:**

- Keep portion allocation inside the existing household meal-plan ownership boundary and make its writes atomic on supported SQLite and PostgreSQL deployments.
- Derive availability from source counts and persisted links rather than maintaining an independent stock balance.
- Add optional API fields and a discovery read without replacing the existing planner workflow or generic repository behavior for unrelated entities.

**Non-Goals:**

- No inventory subsystem, background scheduler, new meal-type enum, recipe-serving conversion, or new frontend design system.
- No claim that a past planned meal was cooked or that predicted leftovers are currently present or safe. Product exclusions are listed in the proposal.
- No broad generic-repository refactor or unrelated cleanup of the ongoing frontend redesign.

## Decisions

### 1. Extend meal-plan rows instead of introducing a stock ledger

Add nullable integer columns `prepared_portions`, `eaten_portions`, and `leftover_source_id` to `group_meal_plans`. The source ID is an indexed self-reference with restrictive deletion, not cascading deletion. Use named constraints and the repository's migration conventions, including SQLite-compatible batch operations when needed.

Entry shapes:

| Role | Prepared portions | Eaten portions | Source |
| --- | --- | --- | --- |
| Ordinary untracked meal | null | null | null |
| Ordinary tracked meal | positive integer | integer from zero through prepared | null |
| Leftover follow-up | null | positive integer reservation | ordinary tracked source ID |

Add a non-null internal integer `leftover_revision` with a zero default for concurrency guarding. It is not exposed as food stock or a public editable field. Add database checks for row-local portion shapes and nonnegative revisions; source ownership, chronology, identity, and aggregate limits are transactional validations. Reject booleans, fractional values, and values outside the database integer range at the API boundary.

Expose camel-case optional fields through the existing schema alias conventions. Reads add nullable `expectedLeftovers`, `reservedLeftovers`, and `availableLeftovers` for tracked sources, plus a lightweight source reference on follow-ups. The reference includes ID, date, meal type, recipe identity or note identity, but not recursive follow-up collections. Do not feed read-only computed fields back into model updates.

Alternative: a separate leftover-batch table and stock ledger would support actual consumption, expiry, and multiple batches, but adds lifecycle complexity not needed for forecast planning. A source-link model directly expresses the one-batch, many-follow-ups requirement.

### 2. Derive totals across the entire household

For each source, expected equals prepared minus eaten, reserved is the sum of every linked entry's eaten count, and available equals expected minus reserved. Do not filter reservations by current date or the displayed planner window. Do not restore portions merely because a reservation date passes.

Use grouped aggregate queries and eager-load lightweight source references to enrich list, single-entry, mutation, and today responses without per-entry queries. Household scoping must use the existing user-derived ownership relationship; never assume a physical `group_meal_plans.household_id` column. Load an out-of-range source independently when returning a follow-up.

Alternative: client-side totals would miss out-of-range reservations and allow conflicting writes. Persisting a separate available count would create another value that could drift from links.

### 3. Make all affected writes participate in one guarded transaction

Implement the allocation-aware create/update/delete operations in `RepositoryMeals`, using its existing session and ownership filters. Keep the HTTP controller responsible for request mapping, exception translation, and publishing events only after a successful commit. Do not call a generic committing CRUD operation midway through allocation validation.

For a mutation, identify the target entry and old/new source IDs. Acquire guards for existing affected rows in sorted ID order using a scoped conditional update of `leftover_revision` from the observed value to the next value. This acquires a write lock and prevents a stale transaction from proceeding; a zero affected-row count means retryable conflict. Refresh guarded rows from the database before re-evaluating their roles, ownership, dependent links, and reservation sums. Revalidate that the initially identified source set still matches the refreshed entry; if not, roll back with a conflict rather than accessing an unguarded source.

Every linked create/change/delete guards its source; every ordinary source update/delete guards that source even when no follow-ups were seen initially. Reassignment guards both sources and the target. Check the merged proposed entry against current totals, excluding its old reservation when replacing it, then flush and commit once. Roll back every error, including failed guard acquisition, so old allocations are never partially released.

This guarded-update approach works with PostgreSQL row write locks and SQLite's serialized writers without relying on SQLite support for `SELECT FOR UPDATE`. Translate only recognized lock/busy or stale-revision outcomes to a localized retryable 409; unexpected database errors remain server errors. Do not add automatic retries that could replay meal-created events. Use separate-session concurrency tests to prove the last-portion case on both databases.

Alternative: validation-only reads are racy. PostgreSQL-only row locks would not satisfy SQLite deployments. A conditional revision guard avoids a new reservation-counter ledger while providing a concrete cross-database serialization point.

### 4. Add discovery while reusing the existing write routes

Add `GET /api/households/mealplans/leftovers` before the integer item-ID route. Require `target_date` and support normal pagination. Return only ordinary tracked meals in the caller's household with source date strictly before the target and positive `allocatablePortions` after applying the edit credit described below. Include source identity, date, actual allocation totals, and `allocatablePortions`.

Allow an optional household-scoped `editing_entry_id`. For a currently linked entry, `allocatablePortions` includes that entry's existing reservation at its current source; ordinary totals remain unchanged. This keeps a fully allocated current source selectable while editing. Resolve invalid or foreign editing IDs identically as not found. The initial source query is not limited to the calendar range, and no arbitrary freshness cutoff is implied.

Continue using POST/PUT/DELETE at the existing meal-plan routes. Payloads contain optional `preparedPortions`, `eatenPortions`, and `leftoverSourceId`, plus the existing date, meal type, and recipe/title fields. The UI copies source identity; the server checks it rather than trusting it. Follow-ups default to lunch on the next calendar day when opened from a source, but the user chooses and explicitly saves the final date and type.

Use existing success status codes. Return 422 for malformed portion shapes or intrinsic link/date validation, 404 for a missing or foreign source, and 409 for allocation, dependent-entry, or concurrency conflicts. Conflict payloads identify accessible affected meal IDs using the existing error envelope conventions and never expose foreign metadata. Discovery is advisory; writes always revalidate.

Alternative: a separate follow-up creation route would duplicate ordinary meal-plan create behavior and events. Automatic date suggestions would require preference and recommendation scope that was not selected.

### 5. Preserve omitted fields and protect source identity

On create, omitted new fields mean an untracked meal. On update, inspect explicitly provided fields before casting schemas, merge omitted new fields with the stored entry, and validate the merged result. Explicit nulls request clearing. Existing complete legacy identity/date/type fields remain required as today; only new metadata gets omission-preserving semantics. Do not allow payload group/user ownership fields to redirect an entry or its source to another household.

Clearing a follow-up's source releases its reservation and requires valid ordinary counts (both null or a valid pair). A follow-up cannot become a producing source while it still has a source reference. Reject source recipe/title/text changes while dependents exist instead of silently rewriting copied follow-up identities. Reject source deletion, disabling tracking, or moving its date beyond a dependent; safe count/date changes retain all links. Ordinary unlinked entries retain existing edit behavior.

Alternative: default-null PUT replacement would erase new metadata when an older client updates a meal. Automatic cascade or detach would silently change users' meal plans.

### 6. Extend the current planner, including its failure states

In the existing create/edit dialog, add a binary portion-tracking control for ordinary meals and visibly labeled numeric prepared/eaten inputs. Show derived expected leftovers before save. Add an explicit leftover-source mode using paginated discovery, date and meal-type controls, a whole-number reservation input, and source availability. Disable recipe/title substitution while linked. From a source entry, provide an icon-plus-command action to schedule its leftovers; exhausted sources do not offer an enabled creation action.

Use the existing Vuetify and global icon patterns, translated labels, and restrained planner layout. Edit and view cards show expected/unallocated counts on sources and a textual leftover marker, portions, and a navigable source-date reference on follow-ups. Do not rely on color or hover alone. Keep keyboard-accessible scheduling independent of dragging, controls at existing touch sizes, and labels/counts wrapping on narrow layouts.

Make `createOne`, `updateOne`, and `deleteOne` return a usable success/error outcome and await them in the dialog before closing or refreshing. Preserve values on failure and refresh discovery counts after conflicts. Date drag and meal-type actions must preserve new metadata; on a rejected move, refresh the saved plan to remove the optimistic local change. After any successful allocation mutation, refresh the visible calendar and active discovery state.

Follow-up recipe cards can still open recipes and retain existing explicit recipe actions. This change triggers no ingredient or shopping-list operation and does not globally alter shared recipe cards.

Alternative: a separate leftover dashboard would fragment planning and duplicate calendar navigation. Applying failure handling only to the new mode would leave existing move/type paths able to misrepresent rejected linked-entry edits.

## Risks / Trade-offs

- Predicted food can differ from reality -> consistently label it expected, show the source date, retain manual adjustments, and make no expiry or safety assertions. There is no automatic ageing or stock reconciliation.
- Guarded transactions can conflict under simultaneous edits -> deterministic guard ordering, brief transactions, rollback, retryable localized errors, and separate-session concurrency coverage on SQLite and PostgreSQL.
- Null defaults and inherited schema mapping can erase metadata -> capture provided-field intent before mapper casts and test raw older-client PUT payloads.
- Ownership comes through users -> reuse household-scoped lookups and test same-group cross-household IDs for discovery, reads, writes, and error details.
- Additional read enrichment can become N+1 -> grouped sums and eager source loading across a page, including sources outside the visible window.
- Restrictive self-links affect migrations and household-wide deletion/import order -> verify the existing full-backup round trip and household teardown with links; preserve dependency order or deliberate bulk cleanup without weakening interactive source-deletion safeguards.
- Existing frontend edits overlap planned files -> later implementation must read and extend the then-current planner instead of restoring HEAD or replacing its layout.

## Migration Plan

1. Add nullable portion/source columns, named constraints, source index, restrictive self-reference, and an internal revision default. Do not backfill recipe yields or infer leftovers for existing rows.
2. Deploy backend schema, guarded CRUD, enriched reads, and discovery together. Verify existing migrations, untracked rows, random planning, and old request payloads on SQLite and PostgreSQL.
3. Regenerate API TypeScript contracts using the existing generation workflow, then deploy the planner interactions and localizations. Existing clients can continue using ordinary meal requests while the new UI is rolled out.
4. Run the focused allocation/compatibility/isolation/concurrency tests, full-backup round trip with links, and desktop/mobile planner checks before release.
5. Prefer rollback to a fixed backend version that understands the new columns. An older backend ignores reservation safeguards even if the columns remain, so do not treat an unrestricted old-version rollback as safe. Before schema downgrade, take a backup and deliberately detach follow-up links while preserving their normal date/recipe/note entries; dropping columns loses planning metadata and requires operator acknowledgement.

## Verification Strategy

- Extend `tests/unit_tests/schema_tests/test_meal_plan.py` for valid role shapes, whole-number validation, and provided-versus-omitted metadata.
- Extend `tests/integration_tests/user_household_tests/test_group_mealplan.py` for CRUD arithmetic, discovery beyond date windows, editing a fully reserved source, invalid source/date/identity, rollback on failed reassignment, legacy PUT behavior, and existing random/note workflows.
- Reuse existing multitenant fixture patterns for same-group household isolation. Use separate sessions and real transaction overlap for the last-portion and source-edit-versus-reservation tests; an in-memory fake is insufficient.
- Add focused composable tests beside `use-group-mealplan.ts` using existing Vitest conventions for awaited outcomes, metadata-preserving updates, and refresh/failure state. Use browser QA for dialog and drag behavior rather than adding a new component-testing framework.
- Verify migration upgrade/downgrade and existing full-backup behavior with linked data. Run touched-file lint and the existing frontend build/type validation workflow after regenerating types.
- Browser acceptance: prepare six/eat four; schedule two for next-day lunch; reject another reservation; show zero availability across weeks; reject then restore an invalid move; delete lunch and regain two portions. Repeat with a note-only source and keyboard-only controls at desktop and mobile widths.

## Implementation Verification

- SQLite and isolated PostgreSQL migration probes verified nullable defaults, count checks, restrictive source deletion, and downgrade preserving detached ordinary meal content.
- Schema and API tests cover meal roles, whole-number validation, omitted/null intent, allocation totals, invalid links, lifecycle, events, household isolation, pagination, batched reads, and legacy planning. Separate-session overlapping transactions passed on both databases for last-portion claims and source capacity edits.
- Full-backup restore preserves linked meal IDs, counts, and derived totals. PostgreSQL owner deletion required explicit transactional cleanup in `RepositoryUsers.delete`: delete the departing user's follow-ups first and detach other users' follow-ups from departing sources while preserving them as untracked meals. Tests verify this on both databases; interactive source deletion remains restrictive.
- Frontend tests cover awaited mutation/refresh results, retained errors, metadata-preserving type changes, loading cleanup, and omission of absent discovery parameters. Only the meal-plan contract was regenerated. A concurrently supplied generator path fix was retained and verified rather than replaced.
- Live browser acceptance covered note and recipe batches, six prepared/four eaten, next-day lunch, competing-reservation 409 with input retained, fully reserved edits, invalid drag 422 with saved date restored, deletion releasing portions, and out-of-week source selection/navigation. Recipe servings remained unchanged. Keyboard scheduling worked at an emulated 390px viewport with a 390px document/dialog; desktop and mobile screenshots showed readable, nonoverlapping controls and loaded recipe images.
- Browser checks found and fixed an undefined optional discovery parameter, exhausted-source label fallback, and URL-date initialization occurring after the first fetch. Explicit selected-source discovery also keeps an entry editable when its source is on another page.

### Final Gates and Requirement Coverage

- Final affected regression slice: 72 passing Python tests covering schemas, meal plans/rules, concurrency on both databases, and full-backup fixtures. Existing admin/user/multitenant slice: 22 passing tests. The existing user CRUD tests mutate the shared admin name, so the admin initialization test must run first; the reverse-order failure was confirmed as fixture state and not fixed in this change.
- Frontend: five passing focused Vitest tests, touched-file ESLint, and production Nuxt build. Backend: mypy passes all 419 source files, touched-file Ruff passes, and editor diagnostics are clear. Existing naive-datetime lint warnings in the unchanged schema test cases are outside this change.
- Acceptance-only meal IDs 2, 3, 4, and 5 were deleted through scoped API requests after checking their identities. The pre-existing meal was preserved. The disposable PostgreSQL instance was stopped.

| Requirement | Implementation and verification |
| --- | --- |
| Optional expected portion tracking | Model constraints, create/save validation, schema tests, and live recipe/note previews |
| Household-wide allocation accounting | Grouped enrichment; out-of-range, past-allocation, and batched-read tests; cross-week browser totals |
| User-directed scheduling of linked meals | Discovery API/client and explicit dialog save; keyboard recipe/note and out-of-week acceptance |
| Valid source links and chronology | Source validation and edit-credit discovery; invalid date/identity/self/chain/untracked tests; fully allocated edit acceptance |
| Atomic reservation limits | Conditional revision guards and one commit; overlapping SQLite/PostgreSQL tests and competing-reservation browser check |
| Safe linked-meal lifecycle | Source safeguards, atomic update/delete/reassignment, and lifecycle tests; invalid source edit and drag recovery; backup and owner cleanup |
| Household isolation | Scoped lookup/guards/aggregates; same-group foreign IDs and discovery tests with identical missing responses |
| Backward-compatible untracked planning | Omission-aware metadata merge, explicit null handling, and existing recipe/note/random/rules tests |
| Clear and accessible planner interactions | Awaited outcomes and retained inputs; desktop/390px screenshots, keyboard scheduling, source links, loaded recipe media, and no automatic ingredient actions |

Completeness, correctness, and coherence review found no unresolved feature blockers. All 25 implementation tasks are complete; expected-only and manual-scheduling boundaries remain unchanged.