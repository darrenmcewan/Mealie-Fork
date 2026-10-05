## Why

Mealie can schedule recipes and notes, but it cannot record how many portions a meal will produce or connect its expected leftovers to a later lunch or dinner. Making those connections explicit helps households plan batch cooking and avoid planning the same leftover portions more than once.

## What Changes

- Add optional expected prepared and eaten portion counts to ordinary meal-plan entries; show expected, reserved, and still-unallocated leftovers without treating missing counts as zero.
- Let users select a source meal and reserve its portions for a manually chosen later date and existing meal type, including lunch. Follow-ups retain their source's recipe or note identity and are visibly marked as leftover meals.
- Calculate availability across the household's complete plan, not only the visible calendar range; prevent over-allocation, cross-household links, chains, and follow-ups on or before the source date.
- Preserve valid links when entries change; reject source changes or deletion that would invalidate reservations until users edit or remove the affected follow-ups. Removing a follow-up releases its allocation.
- Keep existing recipe, note, and random planning compatible when leftover fields are absent.
- Review assumptions: the user delegated scope choices because they were unavailable. Version one uses whole-number expected portions and user-directed scheduling, not confirmed post-cooking stock or automatic recommendations.
- Non-goals: automatic calendar filling, expiry or food-safety advice, inventory tracking, fractional portions, cross-household sharing, recipe/ingredient scaling, shopping-list automation, and same-day follow-ups.

## Capabilities

### New Capabilities

- `leftover-aware-planning`: Optional expected portion tracking, household-scoped leftover availability, and linked future meals with allocation and lifecycle safeguards.

### Modified Capabilities

None. The project currently has no main capability specs to modify.

## Impact

- Backend: extend `GroupMealPlan`, the meal-plan schemas, `RepositoryMeals`, and `/api/households/mealplans` handling with a nullable-field Alembic migration and transactional allocation validation. Existing rows remain ordinary untracked meals.
- Frontend: extend the existing planner editor and calendar view, meal-plan composable and API client, generated TypeScript contracts, and localized strings while preserving the current Vuetify layout and existing worktree changes.
- Verification: extend nearby schema and meal-plan integration tests, add focused frontend tests in the existing Vitest structure, and verify household isolation, concurrent reservations, date-range boundaries, and legacy payloads.
- Documentation: document the planner's forecast-versus-actual distinction and follow-up workflow in the existing user-facing feature documentation. No new runtime dependency or change to recipe and shopping-list APIs is intended.