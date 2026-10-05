## Purpose

Help users compare accessible saved recipes side by side and understand practical trade-offs using recorded data and explicitly labeled counts, without concealing uncertainty or inventing nutritional or difficulty claims.

## ADDED Requirements

### Requirement: Group-scoped recipe selection

The system SHALL allow users to select two to four distinct saved recipes from the current group's recipe explorer and Recipe Finder. Selection SHALL remain available across filtering, pagination, and navigation between those browsing surfaces within the same group. The system SHALL prevent duplicate selection and a fifth selection, allow removal and clearing, and enable opening comparison only with two to four selections. Selection SHALL be temporary browser state and SHALL reset on a full reload, group change, login, or logout.

#### Scenario: Select across browsing surfaces
- **WHEN** a user selects one recipe in the explorer, changes filters, and selects another in the same group's Recipe Finder
- **THEN** both selections remain present in selection order and the comparison action is enabled

#### Scenario: Enforce the limit without losing selection
- **WHEN** four recipes are selected and the user attempts to select a fifth recipe or re-add a selected recipe
- **THEN** the system preserves the four distinct selections and communicates the maximum for the fifth-selection attempt

#### Scenario: Remove and clear selections
- **WHEN** the user removes a selected recipe or clears the selection
- **THEN** the selection and count update immediately, and opening comparison is disabled if fewer than two recipes remain

#### Scenario: Reset selection context
- **WHEN** the user changes group, logs in or out, or fully reloads the application
- **THEN** prior selections and loaded comparison details are cleared

### Requirement: Read-only comparison of accessible recipes

The comparison SHALL show fresh full details only through the same authorization scope used for the current group's recipe browsing. It SHALL support authenticated own-group browsing and authorized public-group browsing without broadening access. Comparison SHALL NOT mutate recipes, preferences, ratings, pantry state, or backend data.

#### Scenario: Public comparison preserves access boundaries
- **WHEN** a visitor compares saved recipes from an accessible public group
- **THEN** only recipes and fields available through that group's existing public read permissions are shown, with no private-detail fallback

#### Scenario: Recipe becomes inaccessible
- **WHEN** a selected recipe has been deleted or is no longer accessible when comparison loads
- **THEN** its column shows an unavailable state without stale details, while accessible recipes remain visible

### Requirement: Aligned recipe comparison data

The comparison SHALL preserve selection order and show recipe identity, an image or neutral placeholder, and a link to each accessible recipe. It SHALL align preparation, cooking, and total time; servings and yield; ingredients; stored nutrition; group rating; ingredient-line and instruction-step counts; and required tools by named criterion. Cooking time SHALL use the existing recipe UI's cooking-time meaning; any additional, distinct stored cooking value SHALL be separately labeled rather than silently combined. Servings and yield SHALL remain separate recorded values without assumed equivalence or rescaling.

#### Scenario: Compare complete recipes
- **WHEN** two to four selected recipes load successfully
- **THEN** the same named criteria are shown for each recipe in selection order and each recipe can be opened from its identity link

#### Scenario: Distinct yield and timing values
- **WHEN** a recipe records four servings, a yield of twelve muffins, and distinct stored cooking-time values
- **THEN** servings and yield are displayed separately and the time values retain distinct labels without being summed or presented as equivalent

### Requirement: Explicit missing and unparseable data

The system SHALL display an explicit not-provided state for absent, null, empty, or whitespace-only metadata. It SHALL preserve non-empty raw text even when it cannot be interpreted numerically, identify it as not numerically comparable where relevant, and SHALL NOT replace missing values with zero or estimated values. An explicitly empty ingredient, instruction, or tool list SHALL be distinguished from an absent list.

#### Scenario: Missing time is not zero
- **WHEN** one recipe has no preparation time and another records a preparation time
- **THEN** the first shows not provided and is not described as faster or assigned a zero-minute time

#### Scenario: Preserve uncertain source text
- **WHEN** a duration contains a range, unsupported locale-specific text, or an ambiguous value such as "overnight"
- **THEN** the original value is displayed without a numeric difference or ranking for that criterion

#### Scenario: Empty list versus unavailable list
- **WHEN** one recipe explicitly has an empty instruction list and another omits instructions
- **THEN** the first has zero recorded instruction steps and the second has an unknown count

### Requirement: Conservative objective trade-offs

The system SHALL support numeric comparison of exact non-negative durations expressed as time-only ISO 8601 hours/minutes/seconds or case-insensitive English quantities with explicit hour, minute, or second units. Unitless values, ranges, calendar units, unsupported text, and negative or non-finite values SHALL NOT be numerically compared. Supported durations SHALL be compared in a common time unit while retaining the recorded display text. Total time SHALL use only its recorded value, not a sum of other fields.

Numeric highlights and differences SHALL be limited to recorded durations, known ingredient-line and instruction-step counts, and valid group ratings. They SHALL appear only when at least two recipes are selected and every selected recipe is successfully loaded and has a trustworthy value for that criterion. Highlights SHALL describe the specific criterion, handle ties explicitly, and SHALL NOT declare an overall winner or imply that shorter times, fewer counts, or higher ratings establish overall suitability.

#### Scenario: Compatible durations expose a practical difference
- **WHEN** all selected recipes have comparable preparation times, including "PT30M" and "1 hour"
- **THEN** the comparison preserves both raw values and identifies the thirty-minute difference and the shorter preparation time

#### Scenario: Missing participant suppresses ranking
- **WHEN** a selected recipe is still loading, unavailable, or lacks a comparable value for a criterion
- **THEN** no numeric highlight or difference is shown for that criterion, while the available raw values remain visible

#### Scenario: Equal values are not a unique best
- **WHEN** all selected recipes have the same comparable value for a criterion
- **THEN** the comparison communicates equality rather than highlighting one recipe as uniquely better

#### Scenario: Recorded total time is authoritative
- **WHEN** preparation and cooking times are present but total time is missing or inconsistent with their sum
- **THEN** comparison preserves the recorded total or not-provided state without deriving or replacing it

### Requirement: Ingredient and complexity transparency

The system SHALL display recorded ingredient lines with their quantities, units, notes, and grouping where available, and display recorded tools. Ingredient-line counts SHALL exclude section headings and empty placeholders but count duplicate substantive lines separately. Instruction-step counts SHALL count only steps with non-empty instruction text. These counts SHALL be explicitly labeled as recorded counts rather than difficulty scores. The system SHALL NOT infer ingredient substitutions, equivalence, allergens, dietary safety, effort, or skill level from these values.

#### Scenario: Grouped ingredients and blank steps
- **WHEN** a recipe includes two substantive ingredient lines, a section heading, an empty placeholder, and one non-empty instruction step
- **THEN** comparison shows two ingredient lines and one instruction step without counting the heading or placeholders

#### Scenario: Counts explain rather than judge complexity
- **WHEN** one recipe has fewer ingredients or instruction steps than another
- **THEN** comparison can show the count difference but does not label the recipe easier or assign a difficulty rating

### Requirement: Nutrition retains its recorded basis and visibility

The system SHALL show nutrition only when it is available and enabled by the recipe's existing nutrition-visibility setting. Shown values SHALL remain as entered and SHALL be labeled as having an unspecified basis unless that basis is explicitly present in the recorded value. Nutrition SHALL NOT be scaled by servings or yield, converted into a presumed per-serving value, used for numeric differences or rankings, or presented as verified dietary or medical advice. Hidden nutrition SHALL remain undisclosed even if present in a loaded response.

#### Scenario: Unknown nutrition basis
- **WHEN** recipes contain stored calories or nutrient text without a declared serving basis
- **THEN** comparison shows the raw values with an unspecified-basis indication and no numeric nutrition comparison

#### Scenario: Respect hidden nutrition
- **WHEN** a recipe disables nutrition display but its response still contains nutritional data
- **THEN** comparison indicates that nutrition is hidden without displaying those values

### Requirement: Common rating provenance

Comparison SHALL display the recorded group rating on its existing five-point scale with an explicit group-rating label. Personal ratings SHALL NOT silently replace group ratings in comparison. Zero, absent, or out-of-range ratings SHALL be displayed as unrated or unavailable, not as negative evidence of recipe quality, and SHALL be excluded from numeric highlights. The system SHALL NOT invent review counts or confidence levels.

#### Scenario: Personal rating does not change the comparison basis
- **WHEN** a user has a personal rating that differs from the recipe's stored group rating
- **THEN** the comparison displays the stored group rating and labels its source consistently across recipes

#### Scenario: Unrated recipe is not worst-rated
- **WHEN** one recipe has no recorded group rating or a zero rating
- **THEN** it is shown as unrated and no group-rating ranking is displayed for the selected set

### Requirement: Recoverable loading and selection states

The comparison SHALL show loading, unavailable, and retryable-error states independently for each selected recipe. A retry SHALL reload only that recipe. Removing a recipe SHALL remove its details and recompute all comparison highlights. A comparison route opened with fewer than two selections SHALL show a selection-needed state with a route back to browsing instead of fabricated columns or comparison claims. Late requests from a removed recipe or an earlier group/authentication context SHALL NOT repopulate the current comparison.

#### Scenario: Partial request failure
- **WHEN** one recipe read fails transiently while the others succeed
- **THEN** the successful columns remain visible, the failed column offers retry, and retry does not refetch successful columns

#### Scenario: Remove while a request is pending
- **WHEN** the user removes a recipe before its detail request completes
- **THEN** the late response does not restore the removed recipe or its values

#### Scenario: Empty or single selection
- **WHEN** the comparison route is opened directly with no selections or removal leaves fewer than two recipes
- **THEN** comparison claims are absent and the user can return to the current group's browsing view to select recipes

### Requirement: Responsive and accessible comparison

The comparison SHALL expose named criteria and recipe identities through semantic table relationships on desktop and an equivalent criterion-oriented layout on mobile. It SHALL remain usable at 360-pixel and 1440-pixel viewport widths without page-level horizontal overflow, clipped values, overlapping controls, or hidden recipe identity. Selection, comparison, removal, clearing, recipe links, and retries SHALL be keyboard-operable with visible focus and accessible names. Selection updates SHALL be announced without relying on color or hover. Long names and values SHALL wrap, and controls SHALL remain reachable without obscuring content. All new user-facing text SHALL be localizable.

#### Scenario: Keyboard-only workflow
- **WHEN** a keyboard user selects recipes, opens comparison, removes a recipe, and retries a failed read
- **THEN** each control has a descriptive accessible name and visible focus, selection changes are announced, and focus remains on a sensible reachable control

#### Scenario: Mobile comparison of four long-named recipes
- **WHEN** four recipes with long names and ingredient or nutrition text are compared at a 360-pixel viewport width
- **THEN** every criterion remains associated with its recipe, text wraps without clipping or overlap, and controls and data remain accessible without page-level horizontal scrolling