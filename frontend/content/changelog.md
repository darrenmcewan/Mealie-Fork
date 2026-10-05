## 2026-10-05 - Unreleased

### Added

- **Cooking insights:** Explore repeated meals, neglected favorites, monthly habits, and explainable personal recommendations from recorded cooking days and current ratings and favorites. Filter by date range and optionally include clearly labeled inferred meal-plan activity. Older unclassified timeline events are excluded, with coverage limits shown.
- **Shopping-route ordering:** Save a per-list aisle sequence with optional suggestions for recognized English labels, drag handles, and keyboard-accessible up/down controls. Custom labels remain manually orderable.
- **Recipe comparison:** Compare two to four saved recipes side by side from the recipe library or Recipe Finder, including recorded times, servings and yield, ingredients, tools, visible nutrition, group ratings, and ingredient and instruction counts. Missing data is explicit; no difficulty score, overall winner, or nutrition ranking is inferred.
- **Changelog:** App update documentation is available from the left sidebar.

### Changed

- **App navigation:** A persistent desktop sidebar and dismissible mobile drawer bring recipes, meal planning, shopping lists, and cookbooks together. Profile, settings, language, and theme controls are grouped at the bottom.
- **Recipe library:** Updated recipe cards, search and filter layouts, and cookbook pages with clearer typography and consistent controls.
- **Recipe pages:** Refined recipe headers, ingredient lists, serving controls, and instruction layouts.
- **Meal planner and shopping lists:** Updated page layouts, dialogs, and list controls to match the rest of the app.
- **Account pages:** Refreshed sign-in, registration, password recovery, and profile forms.

### Fixed

- **Aisle-order editing:** Cancel discards unsaved changes without altering the saved route. Failed saves retain the draft for retry, and saving is disabled while offline.
- **Theme switching:** Restored light and dark mode initialization while retaining saved theme preferences.
- **Shopping list sections:** Group items by label identity rather than display name, keeping equally named labels separate and following the saved section order.
- **Copying shopping lists:** Plain-text and Markdown copies follow the displayed section order and leave out checked items.
