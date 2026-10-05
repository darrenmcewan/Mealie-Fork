## Context

See `proposal.md` for motivation and scope assumptions, and `specs/recipe-comparison/spec.md` for the behavior contract. Design is required because selection crosses browsing surfaces and authorization contexts, and string-valued metadata needs explicit comparison rules.

Observed repository behavior:

- `frontend/pages/g/[groupSlug]/recipes/finder/index.vue` renders `RecipeSuggestion` entries containing `RecipeSummary`. It chooses `useUserApi()` for the user's own group and `usePublicExploreApi(groupSlug).explore` otherwise.
- `RecipeExplorerPage.vue` renders `RecipeCardSection.vue`, which chooses desktop or mobile cards and handles infinite loading. The finder renders `RecipeCardMobile.vue` through `RecipeSuggestion.vue`. The shared `RecipeCardActions.vue` is an existing home for independent card controls.
- `frontend/lib/api/types/recipe.ts` separates summaries from full `Recipe` details: only full details include ingredients, instructions, and nutrition. Time and nutrition values are optional, nullable strings. There is no dedicated difficulty or nutrition-basis field.
- `RecipeAPI` and `PublicRecipeApi` provide existing inherited detail reads. Their endpoints are `/api/recipes/{slug}` and `/api/explore/groups/{groupSlug}/recipes/{slug}` respectively.
- `RecipePageInfoCard.vue` and `RecipeTimeCard.vue` display `performTime` as cooking time rather than `cookTime`. `RecipePageOrganizers.vue` displays nutrition only when `settings.showNutrition` is enabled.
- `RecipeCardRating.vue` can substitute personal ratings for its supplied group rating. It is therefore not an appropriate renderer for a common-basis comparison rating.
- The nutrition FAQ states that recorded values are static and do not scale when servings/yield changes. The frontend uses Nuxt 3, Vue, Vuetify, MDI icons, i18n, and colocated Vitest tests with a jsdom environment. Existing ingredient tests exercise `parseIngredientText`, including its unformatted, sanitized output.
- The OpenSpec main capability inventory is empty. Many frontend files already have user changes; implementation must preserve those changes and avoid unrelated restyling.

## Goals / Non-Goals

**Goals:**
- Keep temporary selection state and asynchronous reads isolated from persistent user preferences and recipe-page editing state.
- Make comparison eligibility explicit and testable without rendering the entire application.
- Reuse existing browsing, image, ingredient-formatting, authorization, and styling conventions with opt-in integration points.

**Non-Goals:**
- No new backend service, schema fields, generated-type edits, persistent storage, or global redesign.
- No changes to existing rating semantics, recipe scaling, ingredient parsing, or cookbook/planner/search-dialog workflows outside the explicitly enabled comparison surfaces.

## Decisions

### 1. Temporary shared selection and a group-scoped route

Add `frontend/composables/recipes/use-recipe-comparison.ts` to own ordered selection and loading state, with request-safe Nuxt shared state rather than a module-level singleton or local storage. A selection stores only the recipe ID, slug, and minimum browser-authorized identity data needed by the toolbar. Deduplicate by ID, require a usable slug, and enforce four selections centrally. Do not rely solely on disabled UI controls for correctness.

Use `/g/{groupSlug}/recipes/compare`, implemented by `frontend/pages/g/[groupSlug]/recipes/compare/index.vue`. The route consumes shared selection; it does not accept arbitrary recipe IDs, URLs, or persisted deep links. A full reload intentionally returns a selection-needed state. Keep selections while filtering and paging or navigating between the explorer, finder, and comparison in the same group. Track group and authentication identity as a context key and clear state when either changes, even if the browser stays on the same group route.

Alternative: query-string selections would survive reload and enable sharing, but add stale-slug and access-validation behavior not needed for this initial scope. Persistent preferences would require lifecycle and migration semantics. Both are deferred.

### 2. Bounded full-detail reads in the existing access scope

On comparison entry, read every selected recipe's fresh detail using the same own-group/public client decision as browsing. At most four detail reads run concurrently. Never use a privileged own-group client as a fallback for public reads. Verify returned identity against the selected recipe and known group identity before displaying it; endpoint authorization remains authoritative. If identity mismatches, discard the response and show unavailable.

Maintain independent loading, ready, unavailable, and retryable-error records. Treat access/not-found failures as unavailable without revealing details; transient network/server failures support a per-column retry. Invalidate any previously loaded details before re-reading on comparison re-entry. Retrying one recipe must not reload successful columns. Removal or context reset deletes details immediately. Use context/request-generation checks to discard late results; use existing request cancellation support only if available, without changing shared clients.

Alternative: a batch comparison endpoint would duplicate existing authorization and add backend work. Fetching all recipe details while browsing would create unnecessary traffic. Four selected detail reads are sufficiently bounded.

### 3. One typed row model with explicit eligibility

Keep comparison-value construction and narrow duration recognition as exported pure functions in the same composable module initially. The module follows the repository's existing colocated composable/test pattern rather than introducing a generic comparison framework. Rows carry a stable criterion key, localized label, raw display value, availability/comparability state, optional numeric value, and source/unit metadata. The view does not interpret raw data itself.

Use the following mappings and rules:

| Criterion | Source and display | Numeric comparison |
| --- | --- | --- |
| Preparation time | `prepTime`, raw text | Exact supported duration only |
| Cooking time | `performTime`, matching the existing UI | Exact supported duration only |
| Additional stored cook time | `cookTime`, separately labeled when non-empty and distinct from `performTime` | None; do not merge or substitute |
| Total time | `totalTime`, raw text; never compute a sum | Exact supported duration only |
| Servings | `recipeServings`; non-positive/invalid values mean not provided | None; not an intrinsic advantage |
| Yield | `recipeYieldQuantity` and `recipeYield`, kept separate from servings | None; units/bases may differ |
| Ingredients | Recorded lines, grouping, quantity, units, notes, and recipe references | Recorded substantive line count only |
| Instructions | Count of steps with non-empty `text` | Recorded step count only |
| Tools | Recorded tool names | None |
| Group rating | `recipe.rating`, explicitly labeled, valid only in `(0, 5]` | Compare on the common five-point scale |
| Nutrition | Each typed nutrient key, as entered, only if `settings.showNutrition === true` | Never; basis is not reliably modeled |

For ingredients, reuse `parseIngredientText(ingredient, 1, false)` for formatted text without recipe scaling; retain title-only section headings but exclude them from counts. A substantive line must include actual food/reference or meaningful display/note/original text, not merely a default quantity. Count duplicate substantive lines separately. Preserve raw ingredient text when formatting cannot represent it; render safely as text rather than introducing unsanitized HTML. Missing arrays have unknown counts; explicit arrays with no substantive entries have zero recorded entries. Do not flatten referenced recipes or infer shared ingredients and substitutions.

For durations, recognize only full-string time-only ISO 8601 hours/minutes/seconds and explicit English hour/minute/second quantities, including their conventional plurals/abbreviations. Recognize decimal quantities with a dot, reject negative/non-finite values, repeated conflicting units, ranges, unitless numbers, unsupported prose, and calendar units. Normalize recognized values to seconds for comparison, preserving their recorded text. Use a conservative comparison-only recognizer, not a natural-language duration interpreter. Unsupported localized input remains visible without comparison. No production dependency is expected for this narrowly bounded recognition contract.

For nutrition, show raw typed fields and a concise data-basis indication; if a value itself contains a basis, preserve it without extrapolation. Do not append assumed units or a per-serving label. Missing settings fail closed for display. Hidden values must not enter the rendered row model or DOM. Do not use `RecipeCardRating` in this view because its personal-rating override would mix provenance; use a read-only value/scale representation instead.

Alternative: parsing arbitrary natural language, normalizing yield/ingredients, or assuming nutrient units would appear richer but invent unsupported equivalence. Raw display plus explicit eligibility is more defensible.

### 4. Criterion-specific differences, not a composite score

For duration/count/rating rows, enable highlights only when every selected recipe is ready and numerically eligible for that row. Compute extrema and deltas against the row's minimum for durations/counts or maximum for group ratings. Render precise labels such as shorter preparation time, fewer recorded steps, or higher group rating with unit-aware differences; describe ties rather than choosing the first recipe. All-equal values have an equality state. Keep recipe columns in selection order, not score order.

Any pending, missing, invalid, or unavailable participant disables that row's highlights until it is resolved or removed. This sacrifices some partial comparisons to prevent claims that ignore a selected recipe. Nutrition, servings, yield, extra cook-time data, and tools remain aligned facts with no ranking. Ingredient/step count labels do not assert real effort or difficulty.

Alternative: an overall score requires user priorities, weight calibration, trustworthy complete data, and explanation rules. It is explicitly outside scope.

### 5. Opt-in selection controls on existing browsing cards

Add an opt-in comparison-enabled prop defaulting to false through `RecipeCardSection`, `RecipeCard`, `RecipeCardMobile`, and `RecipeCardActions`. Enable it for the explorer and through `RecipeSuggestion` for both finder result groups. Bind the centralized selection state to a labeled checkbox independent of the recipe link and other actions; prevent selection interaction from navigating the card or changing the finder's missing-item checkboxes. Entries lacking a stable ID/slug cannot be selected.

Add one `RecipeComparisonToolbar.vue` under `frontend/components/Domain/Recipe/`, shared by explorer and finder. It shows the selection count, selected identities/removal, clear, and the comparison action. Keep it present when the current result set is empty so users can still access selections from an earlier filter. Make it in-flow with responsive wrapping instead of a fixed overlay that may obscure data. Reuse existing icons and CSS tokens; do not rewrite card layouts or apply comparison controls to search dialogs, planner, or unrelated reusable-card consumers by default.

Alternative: put comparison in the own-group action menu. That would hide it from public browsing and require more taps. A separate opt-in checkbox supports discovery and keyboard operation without changing existing actions.

### 6. A focused responsive comparison view

Add `RecipeComparisonView.vue` to render the common row model. Use a semantic desktop table with row/column headers, two to four recipe columns, wrap-safe cells, and existing `RecipeCardImage` rendering with reserved image dimensions. Include image placeholders, localized statuses, per-recipe links/removal/retry, and a browse/back action on the route. Do not use editable rating or nutrition components.

At small widths, switch to a criterion-oriented unframed layout: each criterion has a heading and one named recipe/value entry per selection. This keeps all recipes comparable without a four-column table overflowing the page. Only the active responsive representation is exposed to assistive technology. Keep identity visible in each mobile entry; use stable spacing, wrapping, and at least 44-pixel control targets. Avoid nested cards, hero copy, and in-app feature tutorials. Metadata-basis warnings describe uncertainty in the data rather than explaining app features.

Selection/removal updates use a polite live region. After removal, retain focus on the next remove control or the browse action; retry remains focusable during recovery. New text lives in the canonical frontend locale and uses existing fallback/locale-generation conventions rather than hand-editing generated locale types or every translation.

Alternative: a horizontally scrolling table would retain visual row alignment but make identities and controls harder to track on phones. Criterion-oriented mobile entries meet the no-page-overflow requirement while retaining the same data model.

### 7. Verification remains focused on the new behavior

Add `frontend/composables/recipes/use-recipe-comparison.test.ts` alongside existing tests. Cover pure normalization, row eligibility/highlight rules, selection bounds/context reset, and mocked API lifecycle, including stale responses and public-client isolation. Reuse `use-recipe-ingredients.test.ts` as a neighboring regression check for formatting; do not introduce a separate end-to-end test framework.

Use the existing Vitest jsdom configuration and mock Nuxt state/API bindings for controller tests. Exercise rendered controls, focus, semantics, and responsive layout in the existing running app through browser automation. Record desktop/mobile screenshots and assertions for overflow, long values, visibility, and selection behavior. If production data lacks pathological values, intercept existing detail requests with synthetic fixtures in the browser session; do not seed or alter users' recipes for QA.

## Risks / Trade-offs

- Free-text durations are diverse -> Preserve raw text and reject unrecognized formats instead of guessing; explicitly test common supported formats and unsupported examples.
- Nutrition provenance/basis is unmodeled -> Display as-entered values only, honor visibility, and omit numeric nutrition comparisons entirely.
- Recorded counts do not capture true difficulty -> Label counts narrowly and never produce a difficulty or suitability score.
- Detail reads are not an atomic multi-recipe snapshot -> Fetch fresh details on entry; do not imply concurrent edit locking or guaranteed cross-recipe consistency.
- Shared asynchronous state could survive an access change -> Clear details on context changes and discard results with obsolete request/context generations.
- Existing shared cards have many consumers and user edits -> Default comparison controls off, enable only the explorer/finder, and regression-check links, favorites, menus, and finder checkboxes.
- Reset-on-reload loses selection -> Treat this as intentional temporary-state behavior with an accessible return-to-browsing state; persistence is deferred.
- Mobile criterion repetition increases vertical length -> Use concise headings, repeat identity consistently, and preserve aligned desktop scanning without decorative containers.

## Migration Plan

1. Implement and verify the new frontend state/helpers and opt-in comparison UI against the capability scenarios.
2. Deploy through the ordinary frontend build; no migration, backend rollout, or data backfill is required.
3. Roll back by removing the opt-in entry controls and comparison route, or by reverting the feature commit when one is eventually created. Because comparison writes no backend state, rollback needs no data cleanup.

## Open Questions

None are blocking or deferred: selection scope, ephemeral lifetime, public-group support, cooking-field treatment, supported numeric criteria, and non-inferred complexity are decided above. The autonomous scope assumptions remain visible in the proposal for review before implementation.