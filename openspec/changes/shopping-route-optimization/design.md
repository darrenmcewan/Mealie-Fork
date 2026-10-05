## Context

See `proposal.md` for motivation and scope assumptions, and `specs/shopping-route-ordering/spec.md` for the behavioral contract. This design is included because ordering changes span the page, sorting, editing lifecycle, label presentation, and copy consumers.

Observed local behavior:

- Nuxt 3/Vue 3, Vuetify, and `vue-draggable-plus` already support the shopping-list UI. `frontend/pages/shopping-lists/[id].vue` provides a drag-only reorder dialog in its actions menu.
- `use-shopping-list-page.ts` delegates ordering to `sub-composables/use-shopping-list-sorting.ts`. `updateItemsByLabel` returns an object keyed by label name and follows the response's label-settings array. Distinct IDs with the same name collide, numeric-looking names follow JavaScript object-key rules, and labeled items absent from settings can be dropped.
- `use-shopping-list-copy.ts`, `use-shopping-list-labels.ts`, and `updateIndexUncheckedByLabel` consume the same name-keyed representation.
- `use-shopping-list-crud.ts` assigns saved `labelSettings` directly to `localLabels` and changes positions in place. Reference equality is its save-change test. This does not isolate drafts or reliably express whether a route changed.
- `use-shopping-list-data.ts` polls every five seconds and uses `loadingCounter` to avoid replacing busy state. Item changes use the existing offline item-action queue; label-settings writes do not.
- `BaseDialog.vue` has `keepOpen`, `loading`, `submitDisabled`, `disableSubmitOnEnter`, and a custom `card-actions` slot. It otherwise auto-closes after submission, including an unsuccessful request once loading stops.
- The existing API client calls `PUT /api/households/shopping/lists/{id}/label-settings` with label-setting IDs, list IDs, label IDs, and positions, returning `ShoppingListOut`. SQLAlchemy stores per-list label positions. Backend label services create settings for new group labels; existing integration tests cover creation, deletion, saving positions, and sorted responses.
- The documentation promises No Label first. Crowdin's frontend source is `frontend/lang/messages/en-US.json`; `frontend/lang/locales/en-US.ts` loads it. Vitest uses jsdom and the `~` alias, with colocated composable tests and `frontend/tests/utils.ts` helpers.
- No main OpenSpec capabilities exist. Other active changes address recipe comparison and leftovers, not shopping route ordering. Existing working-tree UI edits must be preserved during implementation.

## Goals / Non-Goals

**Goals:**

- Treat the saved list-label positions as the only persisted route authority.
- Use one ordered, identity-based section representation for rendering, item moves, colors, and copying.
- Keep suggestion and grouping logic pure and independently testable, with no network or item mutation.
- Make route editing an isolated transaction over label positions with explicit success and failure handling.

**Non-Goals:**

- Do not alter food grouping, item merging, checked-item sorting, or the offline item queue.
- Do not modify backend authorization, label lifecycle, API schemas, or the shared dialog API.
- Do not build a generic route engine or introduce another ordering preference that can disagree with label positions.

## Decisions

### 1. Reuse per-list label settings

Continue using `ShoppingListsApi.updateLabelSettings`. Build the update payload from the draft's existing setting IDs, `shoppingListId`, and `labelId`, assigning contiguous zero-based positions. Do not send item updates, create labels, or change names. Adopt the returned `labelSettings` only on a confirmed success.

Alternative considered: named store routes with new models and endpoints. Rejected for this scope because existing per-list persistence supports the requested workflow without migration or cross-list ownership decisions. The per-list assumption is explicit and subject to review before implementation.

### 2. Produce an ordered section array keyed by identity

Replace the name-keyed section object with a local typed array containing a stable section key, nullable label ID, display name, optional color, and ordered items. Use `label:<UUID>` for labeled sections and a distinct `unlabeled` sentinel. Use the item label summary first and the settings summary as a fallback; unresolved labels retain their ID and a localized fallback heading.

In the sorting composable, export a pure section-building helper and retain a thin localized wrapper where needed. Group unchecked items by identity using a `Map`. Sort a copy of configured settings by numeric position, then label ID for ties. Emit No Label first, nonempty configured sections in saved order, and unmatched labeled sections sorted by label ID. Retain each item's incoming within-section sequence. Do not mutate item positions while building sections or saving a route.

Update all known consumers together: the page's section loop and draggable callbacks, the page composable's flattening and item-reorder handler, the copy composable, and label color/open-state lookup. Item moves address a section key, not a heading; copy iterates the section array and uses display names only when formatting headings. Keys stay stable across renaming and translation changes. The editor still includes all configured labels, independent of visible nonempty sections.

Alternative considered: retain an object but prefix label names to avoid integer-key sorting. Rejected because that still couples identity to mutable text, cannot safely distinguish duplicate names, and complicates complete fallback handling.

### 3. Use a small explicit suggestion catalogue

Add an exported pure suggestion helper beside the existing sorting logic rather than creating a service or dependency. Normalize a copied label name with Unicode normalization, trimming, whitespace collapsing, and case folding; match complete normalized names against this initial catalogue from the existing English label seed file:

| Rank | Family | Recognized names |
| --- | --- | --- |
| 0 | Produce | Produce, Fruits, Vegetables |
| 1 | Bakery and grains | Baked Goods, Grains |
| 2 | Ambient pantry and snacks | Canned Goods, Condiments, Confectionary, Health Foods, Snacks, Spices, Sweets |
| 3 | Beverages | Beverages, Alcohol |
| 4 | Household and other | Household, Other |
| 5 | Unrecognized | All names not explicitly recognized |
| 6 | Meat and seafood | Meat, Meat Products, Seafood |
| 7 | Dairy | Dairy Products |
| 8 | Frozen | Frozen Foods |

Use the input index as the secondary sort key within each rank. Return new records with new positions, preserving all IDs exactly once and leaving the input untouched. A second application is idempotent. Do not classify custom labels through substrings, call an LLM, import backend JSON at runtime, or assume that a label's display name is a universal taxonomy.

The catalogue is independent of the UI language: English seed names can be recognized in any UI locale; other names fall back unchanged relative to each other. The suggestion is an optional starting point, not a saved default or a physical map. Broader localized aliases require a later reviewed catalogue extension, not silent inference.

Alternative considered: alphabetic ordering or automatically suggesting whenever the list refreshes. Rejected because neither reflects a stable shopper-defined route. A one-click suggestion inside the editor leaves the final route under user control.

### 4. Own the draft and pending-save lifecycle locally

Keep route editing beside the current label CRUD functions. On open, clone label-setting records and nested label summaries, sort by saved positions, and capture the initial ordered label IDs. Track editor-open, save-pending, and save-error state separately from the shared loading counter. Dirty state compares ordered IDs, not object references. Manual moves and suggestion only update the draft.

Acquire one polling-pause contribution on the transition to open, and release it exactly once on close or unmount. A save attempt adds its own loading contribution and releases it in `finally`, including thrown errors and empty responses. An in-flight fetch must not overwrite either saved state or the draft while the editor is open. On confirmed success, update saved settings, rebuild sections without item sorting, finish the editor lifecycle, and refresh to reconcile current labels/items. On failure, keep the editor and draft, retain saved settings, show an error, and allow retry. Cancellation discards the draft and resumes refresh. Do not queue label writes in the item-action queue.

Bind the existing `BaseDialog` using `keepOpen`, saving feedback, and a route-local guarded model setter that rejects close requests while saving. Use `card-actions` to disable Cancel and Save during the request, and `disableSubmitOnEnter` so Enter on an arrow button cannot bubble into saving. All explicit Save handlers independently reject offline, unchanged, or pending requests. Finalize via the actual closed-state transition; do not decrement counters separately from both cancel and close emissions.

Alternative considered: optimistic updates to saved settings or changing `BaseDialog` globally. Rejected because failed writes must not appear saved and the dialog's existing slots and model contract allow a local solution.

### 5. Preserve the existing UI while making ordering operable

Add a compact icon-and-text aisle-order command near the existing list actions, not a separate page or decorative panel; keep the menu entry. Within the editor, retain drag handles and add up/down icon buttons through the current `$globals.icons` registry. Disable boundary moves. Keep rows keyed by setting identity, maintain focus on the moved row's usable control, and announce its resulting position through a localized polite live region. Include Suggest Order as an explicit command and Save/Cancel actions.

Use existing Vuetify spacing and colors, responsive dialog behavior, wrap-capable label names, and 44px controls. Distinguish the saved route from draft state through the dialog and standard status/error feedback, without adding an in-app tutorial or suggesting a measured shortest route. Add strings to the existing English Crowdin source, reuse existing fallback behavior for untranslated controls, and do not bulk-regenerate locales.

Alternative considered: drag handles alone or visible section controls throughout the shopping view. Rejected because drag-only excludes keyboard/single-pointer users, while permanent arrows clutter the shopping workflow.

### 6. Validate the owning slice, not a new test platform

Use colocated Vitest tests for the sorting/suggestion helpers and the existing CRUD/copy composables. Reuse `frontend/tests/utils.ts` for i18n where appropriate; explicitly import Vue primitives or stub necessary Nuxt globals in composable tests because the current Vitest configuration is jsdom, not a Nuxt test environment. Mock the existing API client and copy function; use controlled promises for pending, failure, and retry paths.

The cheapest discriminating check is a frozen-input fixture with scrambled label settings, numeric/equal display names, unmatched labels, and checked/unlabeled items. It must produce the expected identity sequence, include every unchecked item exactly once, and leave the input unchanged. A second focused check verifies that canceled or rejected saves do not change stored positions and do release polling state.

Run focused tests, touched-file ESLint, and the existing backend label integration module. Use browser validation for the real Vuetify dialog at desktop and narrow mobile widths: touch/keyboard reorder, focus and announcements, save failure, offline save disabling, dismissal while pending, route reload, copying, long labels, and the existing check/uncheck/item-drag interactions. No new browser-test dependency is required.

## Risks / Trade-offs

- [Actual stores differ from the generic sequence] -> Suggestions are explicit drafts; manual overrides are authoritative and no distance-saving claim is made.
- [English-only name recognition is limited] -> Record the limitation in proposal and docs; unrecognized names remain intact and manually orderable. Do not misclassify through substring matching.
- [Labels represent tools, recipes, or stores rather than aisles] -> Never suggest automatically or alter label assignments; recognize only the fixed catalogue.
- [Identity-array changes affect several consumers] -> Update render, item moves, copy, colors, and open-state handling as one bounded slice; test duplicate/numeric names and item-count invariants.
- [Cancel and close events can both fire] -> Use one idempotent editor finalizer and balanced `finally` blocks; test all dismissal and failure paths.
- [Concurrent label deletion or simultaneous saves] -> Keep existing API semantics, surface rejection without losing the draft, and refresh after closing. Last successful writes can win; no optimistic-locking guarantee is introduced.
- [Frozen draft during polling hides concurrent changes temporarily] -> Pause replacement only while editing, release the pause on every terminal path, and reconcile promptly after closing.
- [Existing uncommitted UI work] -> Preserve it; limit implementation edits to the described behavior and existing styling conventions.

## Migration Plan

1. Implement the frontend changes and focused tests without schema or backend changes. Existing routes remain the starting order; no suggestion runs on deployment.
2. Verify existing lists, new-label lifecycle, offline item behavior, and copy/export against the current API and label integration tests.
3. Deploy through the existing frontend pipeline. Existing list IDs, setting IDs, and positions require no conversion.
4. Roll back the frontend change if needed. Saved positions remain compatible with the previous reorder UI; no data rollback is necessary.