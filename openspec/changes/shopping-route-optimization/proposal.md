## Why

Shopping lists already support label-based sections and saved per-list label positions, but arranging an aisle route is hidden in an actions menu and relies on dragging. Shoppers need a predictable section sequence they can quickly adjust on a phone or keyboard without losing items, changing ingredient data, or accidentally saving a draft.

## What Changes

- Add a discoverable aisle-order action to the existing shopping-list detail page, retaining the current reorder entry point.
- Offer an explicit, preview-only suggested route using a deterministic catalogue of recognized section names, with produce and ambient goods before chilled and frozen sections. Preserve custom labels and allow manual overrides before saving.
- Keep dragging and add accessible move-up/move-down controls, stable focus, boundary states, and visible save feedback.
- Use an isolated reorder draft: cancel leaves the saved route unchanged; failed saves keep the draft available for retry; successful saves persist through the existing label-settings API.
- Group and order unchecked items by label identity rather than display-name object keys. Preserve within-section item order, retain unmatched items, keep No Label first, and keep checked items separate.
- Preserve saved routes across reloads and ordinary list updates; do not automatically replace a route when items or labels change.

## Capabilities

### New Capabilities

- `shopping-route-ordering`: Preview, edit, save, and follow a per-shopping-list aisle sequence based on existing labels, with deterministic suggestions and accessible reordering.

### Modified Capabilities

None. The main capability inventory is empty; this change documents the existing behavior it must preserve alongside its additions.

## Impact

- Frontend: `frontend/pages/shopping-lists/[id].vue`, `MultiPurposeLabelSection.vue`, and the shopping-list sorting, CRUD, copy, label, and page composables; frontend locale source strings and focused Vitest coverage.
- Persistence: reuse `ShoppingListsApi.updateLabelSettings` and `PUT /api/households/shopping/lists/{id}/label-settings`; retain `ShoppingListMultiPurposeLabel.position`. No new endpoint, database migration, external service, or runtime dependency is planned.
- Compatibility checks: existing shopping-list label integration tests, copy/export ordering, polling, offline item updates, and the documented No Label-first convention.
- Documentation: update the shopping-list section of `docs/docs/documentation/getting-started/features.md` to describe the route editor and suggestion limitations.

## Scope Assumptions And Non-Goals

- Planning proceeds with a conservative per-list scope because the user is unavailable to clarify. Existing labels are the store sections; users define their store's actual sequence.
- Suggestions are optional heuristics, not a verified floor plan or shortest path. The initial recognized-name catalogue uses the existing English seed names; other languages and custom names retain a deterministic fallback and remain fully manually orderable. UI controls remain localized.
- Reusable named store profiles, aisle coordinates or numbers, inferred labels for free-text items, cross-list route synchronization, new offline route-write queues, and optimal-distance claims are out of scope.
- This change contains planning artifacts only; implementation requires a subsequent apply request.