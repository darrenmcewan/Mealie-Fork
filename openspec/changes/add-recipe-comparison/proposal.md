## Why

Choosing between saved recipes currently requires opening them individually and remembering their differences. A side-by-side comparison will help users make practical trade-offs without turning incomplete, free-text recipe data into misleading scores.

## What Changes

- Let users select two to four saved recipes while browsing the current group's recipe explorer or Recipe Finder, retain the selection while browsing that group, and open a dedicated comparison view.
- Compare preparation, cooking, and total time; servings and yield; ingredients; stored nutrition and ratings; instruction counts; and required tools. Use factual ingredient and instruction counts as labeled complexity proxies, not difficulty assessments.
- Make trade-offs visible through aligned rows and objective time, count, and rating differences only when values are known and compatible. Preserve source text and show explicit missing, unparseable, or non-comparable states instead of assuming zero.
- Treat stored nutrition as unverified, as-entered data with an unspecified comparison basis. Do not scale it, infer a per-serving basis, or rank recipes by it.
- Provide a responsive, keyboard-accessible comparison workflow with recipe links, removal, clear selection, loading, and per-recipe retry/unavailable states.
- Keep the feature read-only and reuse existing group-scoped recipe detail APIs and frontend conventions.

### Scope Assumptions

The user was unavailable to clarify scope. This proposal chooses two to four existing, saved recipes in the current group and factual comparison with labeled proxies. These assumptions are reviewable before implementation; comparison is available wherever the existing explorer/finder authorizes recipe reads, including public group browsing. Selection is temporary, group-scoped browser state, not a persisted user preference.

### Non-goals

External recipe discovery or pre-import comparison; inferred difficulty or an overall winner; AI summaries; dietary or medical recommendations; nutrition normalization; cost estimates; arbitrary extra-field comparison; new database fields, backend endpoints, or persisted comparison collections.

## Capabilities

### New Capabilities

- `recipe-comparison`: Select accessible saved recipes, view trustworthy side-by-side data, and understand objective differences while preserving missing-data and authorization boundaries.

### Modified Capabilities

None. The existing OpenSpec capability inventory is empty.

## Impact

- Frontend: Recipe Finder, the shared recipe explorer/list/card surfaces, a group-scoped comparison route and composable, localized comparison UI, and focused Vitest coverage.
- Data integration: Existing `RecipeSummary` values identify selections; full `Recipe` reads supply ingredients, instructions, and nutrition. Existing public versus authenticated API routing and nutrition visibility settings must be preserved.
- Compatibility: Additive, read-only behavior; no API contract, schema, or data migration changes. Preserve the current in-progress frontend styling changes.
- Verification: OpenSpec validation now; focused frontend tests, lint/type checks, and desktop/mobile browser acceptance during implementation. No new production dependency is expected.