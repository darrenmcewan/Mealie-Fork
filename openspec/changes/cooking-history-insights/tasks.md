## 1. Structured Cooking Provenance

- [x] 1.1 Add nullable `cooking_source` to the timeline model and an Alembic revision with the actor/source/timestamp index; verify upgrade and downgrade in disposable SQLite and PostgreSQL databases preserve existing timeline content and leave legacy provenance null.
- [x] 1.2 Extend timeline schemas with the additive camel-case provenance field while retaining existing event types and omitted-field defaults; verify schema/API tests cover null, manual, inferred, unsupported values, and old payload compatibility.
- [x] 1.3 Enforce current-actor attribution for manual creation, reserve inferred creation for the internal scheduler, and preserve provenance on text/image updates; extend `tests/integration_tests/user_recipe_tests/test_recipe_timeline_events.py` and verify 403/422 cases, immutable provenance, ordinary CRUD compatibility, and deletion behavior.
- [x] 1.4 Mark scheduler-generated events as inferred without changing its existing actor/content/deduplication logic; extend `tests/unit_tests/services_tests/scheduler/tasks/test_create_timeline_events.py` and verify source values plus unchanged rerun counts and last-made behavior.

## 2. Scoped Evidence and Date Normalization

- [x] 2.1 Add the insights query and response schemas in `mealie/schema/user/cooking_insights.py`; verify tests for paired inclusive dates, 365-day defaults, 1,827-day maximum, future/reversed dates, valid IANA zones, limit bounds, and rejected identity/group overrides.
- [x] 2.2 Add and register a dedicated cooking-history repository with explicit authenticated actor and joined recipe-group predicates; verify repository/API tests exclude another user's records and cross-group preferences while retaining the actor's records on another household's readable recipe.
- [x] 2.3 Add streamed narrow window reads, grouped minima/per-source maxima for pre-window history, scoped legacy-event existence, current preferences, and one displayed-recipe hydration query; verify no subject parsing, no event-row pre-limit, correct null/deleted-recipe handling, and constant query count as recipe result size grows.
- [x] 2.4 Implement local-midnight UTC bounds, recipe/day deduplication, manual-over-inferred precedence, source-aware last dates, and active-date counts in `mealie/services/recipe/cooking_insights_service.py`; verify fixed-date tests cover today's end-of-day entry, DST, fractional-hour zones, leap days, month/year rollover, and inferred-only versus overlapping days.

## 3. Insight Calculations

- [x] 3.1 Implement frequently repeated meal eligibility, evidence, and deterministic ordering; verify service fixtures with one-day exclusions, repeated days, count/recency ties, identifier tie-breaks, and both source policies produce the specified ranked results.
- [x] 3.2 Implement neglected favorites and the separate favorites-without-history collection using eligible dates before or within the window; verify 29/30-day boundaries, out-of-window last dates, unknown gaps, current favorite changes, and exact rating/identifier tie-breaks.
- [x] 3.3 Implement twelve month buckets, active-date counts, recurring recipe/month evidence, and the 730-day/twelve-active-date/two-year sufficiency gate; verify sparse history, zero months, two-year recurrence, repeated same-date recipes, and bounded recurring collections match the spec.
- [x] 3.4 Implement recommendation eligibility, invalid-rating normalization, seven-date recent-cooking exclusion, three priority tiers, deterministic ties, and structured reasons; verify poor-rated favorites are excluded, favorite/high-rating missing-history cases remain truthful, empty preferences produce no invented suggestions, and historical end dates use current preferences.
- [x] 3.5 Assemble collection totals/truncation and coverage metadata after full calculation and before bounded hydration; verify limit 1/10/50 fixtures return complete eligible totals, twelve month buckets, source-aware evidence, and a legacy warning even when unclassified activity lies outside the selected window.

## 4. Self-Scoped API

- [x] 4.1 Add and register `GET /api/users/self/cooking-insights` using the existing users controller/router conventions and explicit private/no-store response headers; verify authenticated schema-valid responses, resolved filters, rejected invalid input/identity overrides, unauthenticated failure, and no generic other-user insights route.
- [x] 4.2 Add focused endpoint tests beside existing user-recipe integration tests using existing user/recipe fixtures; verify same-household, same-group other-household, and other-group isolation, current-group changes, administrator self scope, accessible shared recipes, deletion exclusion, and no writes during reads.
- [x] 4.3 Add read-after-edit integration scenarios spanning timeline CRUD and favorites/ratings; verify subsequent requests change counts, neglect, reasons, and ranking after deleting the last recipe/day record, removing a favorite, or lowering a rating without a background refresh.

## 5. Typed Frontend and Manual Writer

- [x] 5.1 Export new schemas and regenerate affected frontend API types and test route helpers through existing `dev/code-generation` entry points, then add the user API method in `frontend/lib/api/user/users.ts`; verify generated contracts include provenance and insight models and API client tests send the correct self path/query without unrelated generation churn.
- [x] 5.2 Update `RecipeLastMade.vue` to carry manual provenance on its existing parent and selected linked-recipe requests; verify focused payload/browser checks show one existing-flow event per selected recipe, no extra event through the last-made PATCH, and unchanged date/comment/image behavior.
- [x] 5.3 Add a focused cooking-insights composable with browser-zone detection/UTC fallback, validated filter state, bounded limits, retry, latest-request-only handling, and identity-change clearing; verify colocated Vitest tests using existing helpers cover query propagation, source toggling, rapid changes, errors, and logout/group changes.

## 6. Insight Page and Navigation

- [x] 6.1 Add the authenticated own-group insights page and navigation entry alongside the timeline in `DefaultLayout.vue`, preserving existing shared-worktree layout edits; verify own-group navigation/direct access works and unauthenticated/foreign-group navigation cannot show personal results in the wrong context.
- [x] 6.2 Build labeled date controls and 30-day/90-day/one-year/three-year presets, inferred-activity checkbox, bounded result-size control, and tabs for the four views; verify local date boundaries, keyboard interaction, current-filter/result agreement, and mobile wrapping in browser acceptance.
- [x] 6.3 Render ranked recipe imagery/links, distinct missing-history favorites, monthly labeled bars/table, source evidence, current-preference labels, and reason-code translations using existing UI conventions; verify displayed counts/order/reasons against seeded API responses and accessible monthly values without hover or color dependence.
- [x] 6.4 Add localized coverage, truncation, loading, retryable-error, empty-section, and insufficient-seasonal-history states; verify no-recorded-history and failed-request cases remain distinct, older history is not called never cooked, and stale responses cannot replace the current filter selection.

## 7. Integration Gates and Documentation

- [x] 7.1 Run focused provenance, scheduler, repository/service, and self-endpoint tests under SQLite and PostgreSQL using the existing backend test matrix; verify equivalent expected results and record passing focused pytest commands before running broader required gates.
- [x] 7.2 Seed a large disposable history fixture and inspect query count/plans for default and maximum windows; verify actor/source index usage where appropriate, constant query count as displayed recipes grow, no N+1 hydration or nested raw-event payloads, and unchanged rankings when result limits differ.
- [ ] 7.3 Run focused Vitest and ESLint on touched frontend paths plus backend Ruff formatting/lint and mypy, then the existing frontend/backend CI gates; verify all changed-slice checks pass, resolve regressions caused by this change, and identify unrelated pre-existing failures separately without global formatting churn.
- [x] 7.4 Perform end-to-end browser acceptance at 375px and desktop widths with recorded, inferred, sparse, legacy, preference-only, and error fixtures; verify recipe images/links, all four views, keyboard focus, no overlap/overflow, group/identity clearing, and changed ratings/events reflected on refresh.
- [x] 7.5 Update the API documentation and existing `docs/docs/documentation/getting-started/api-usage.md` with provenance, self-only filters, current preference semantics, partial legacy coverage, and downgrade loss; verify docs match schema examples and all documented response/filter fields.
- [ ] 7.6 Record final migration/mixed-version evidence and run `openspec validate cooking-history-insights --strict`; verify every acceptance scenario has passing test or browser evidence and leave deployment/rollback notes ready for review before archival.