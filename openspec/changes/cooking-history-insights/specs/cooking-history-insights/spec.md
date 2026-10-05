## Purpose

Help users understand their own recorded cooking habits and revisit recipes they like through access-scoped, reproducible insights with evidence and explicit coverage limits.

## ADDED Requirements

### Requirement: Insights are personal and access scoped
The system SHALL provide an authenticated read-only insights API for the signed-in user. All cooking events and preference signals SHALL be scoped to that actor and recipes currently readable by that actor in their current group. Other users' events, ratings, and favorites SHALL NOT affect results. The API SHALL NOT allow caller-supplied user or group overrides. Deleted or inaccessible recipes SHALL be excluded from rows, counts, and evidence.

#### Scenario: Another household member has different habits
- **WHEN** two users request insights for the same shared recipe
- **THEN** each response uses only that user's events, ratings, and favorites even if both users share a household

#### Scenario: A recipe is no longer accessible
- **WHEN** a previously recorded recipe is deleted or becomes unreadable by the user
- **THEN** subsequent responses exclude it from all results and totals

#### Scenario: A request is unauthenticated or attempts an identity override
- **WHEN** an unauthenticated caller requests insights or an authenticated caller supplies a user/group override
- **THEN** the API returns the existing authentication failure or a validation error respectively and discloses no other user's insight data

### Requirement: Insight windows and output size are bounded
The API SHALL accept inclusive `startDate` and `endDate`, a valid IANA `timeZone` defaulting to UTC, `includeInferred` defaulting to false, and `limit` defaulting to 10 with bounds 1 through 50. With no dates, the effective window SHALL cover the latest 365 local calendar days including today. End dates SHALL NOT exceed today in the requested time zone; reversed windows, windows longer than 1,827 inclusive days, incomplete date pairs, invalid zones, and invalid limits SHALL return validation errors. Responses SHALL echo effective filters and report each ranked section's total eligible items and whether its result was truncated. Monthly buckets SHALL always include all twelve months.

#### Scenario: Default filters are resolved
- **WHEN** the user requests insights without dates or a time zone
- **THEN** the API returns a 365-day UTC window, recorded-only scope, at most ten items per ranked section, and the resolved filters

#### Scenario: Invalid input is rejected
- **WHEN** the request contains a reversed or oversized window, a future end date, an incomplete date pair, an unknown time zone, or a limit outside 1 through 50
- **THEN** the API returns a validation error rather than broadening, silently correcting, or partially evaluating the request

### Requirement: Cooking counts use distinct local recipe days
Within the selected inclusive local dates, counts SHALL use distinct `(recipe, local calendar date)` pairs of classified cooking events for the authenticated actor. Recorded-only mode SHALL include `manual` events; inferred-inclusive mode SHALL additionally include `mealplan` events. A recipe/day containing both sources SHALL count once as recorded, not as inferred-only. Null timestamps, unclassified events, and local dates after the effective end date SHALL NOT contribute. The same source policy SHALL govern last-recorded dates before or within the window, neglect, recent-cooking exclusion, and recommendation evidence. The system SHALL NOT derive personal cooking history from household last-made state.

#### Scenario: Multiple entries occur on the same recipe and date
- **WHEN** two manual events and one inferred event reference the same recipe and local date
- **THEN** inferred-inclusive mode counts one recorded cooking day and zero additional inferred-only cooking days

#### Scenario: A scheduled meal has no manual confirmation
- **WHEN** a recipe has only a classified meal-plan event on a date
- **THEN** recorded-only mode excludes that date and inferred-inclusive mode includes one visibly inferred-only cooking day

#### Scenario: A user records cooking today with an end-of-day timestamp
- **WHEN** an event timestamp falls later today in the requested local time zone
- **THEN** it counts for today despite being later than the request's wall-clock time

#### Scenario: A timestamp crosses a month boundary in another time zone
- **WHEN** an event falls in different local calendar months in UTC and the requested time zone
- **THEN** window membership, deduplication, monthly counts, and gap calculations consistently use the requested time zone

### Requirement: Frequently repeated meals show reproducible evidence
The frequently repeated section SHALL contain recipes with at least two cooking days in the selected window, ordered by cooking-day count descending, last in-window cooking date descending, and recipe identifier ascending. Each item SHALL include recipe navigation data, cooking-day count, recorded versus inferred-only breakdown, last eligible cooking date on or before `endDate`, and current personal rating/favorite status.

#### Scenario: Repeat counts tie
- **WHEN** two recipes have the same number of in-window cooking days
- **THEN** the more recently recorded recipe appears first and remaining ties use recipe identifiers deterministically

#### Scenario: No recipe was recorded twice
- **WHEN** every eligible recipe has fewer than two in-window cooking days
- **THEN** the section is empty without substituting single-use recipes or unrelated timeline entries

### Requirement: Neglected favorites distinguish missing history from elapsed time
The neglected section SHALL include current personal favorites with a known eligible cooking date on or before `endDate` whose local-date gap is at least 30 days. It SHALL look before `startDate` for the last eligible cooking date and order results by gap descending, valid personal rating descending with missing ratings last, and recipe identifier ascending. Favorites with no eligible cooking record SHALL appear in a separately labeled "No recorded cooking" group, ordered by valid personal rating descending and recipe identifier ascending, and SHALL NOT be labeled never cooked or assigned a fabricated gap.

#### Scenario: A favorite was last recorded before the selected window
- **WHEN** its most recent eligible cooking date is 45 days before `endDate` and precedes `startDate`
- **THEN** the recipe qualifies as neglected with a 45-day gap rather than as missing history

#### Scenario: Neglect reaches its exact boundary
- **WHEN** favorites have gaps of 29 and 30 days
- **THEN** only the favorite with a 30-day gap qualifies as neglected

#### Scenario: A favorite has only unclassified legacy events
- **WHEN** no eligible classified record exists for that favorite
- **THEN** it appears as "No recorded cooking" without asserting that it has never been cooked

### Requirement: Seasonal habits describe calendar-month observations
The seasonal section SHALL return January through December cooking-day totals from the selected window and counts of distinct local dates with any cooking activity. It SHALL claim sufficient recurring-history evidence only when the selected window spans at least 730 inclusive days and contains activity on at least twelve distinct local dates across at least two calendar years. Recurring recipe/month entries SHALL additionally require that recipe to have cooking days in that month in at least two distinct years. Entries SHALL rank by years observed descending, cooking-day count descending, and recipe identifier ascending. Sparse history SHALL still show observed monthly totals with an insufficient-history state, not climate, ingredient-seasonality, or future-behavior claims.

#### Scenario: A recipe recurs in the same month across years
- **WHEN** the history passes the sufficiency gate and a recipe has cooking days in October in two different years
- **THEN** it qualifies for October's recurring-recipe list with both its count and years-observed evidence

#### Scenario: A busy single month is mistaken for seasonality
- **WHEN** many cooking days occur in one year but the sufficiency gate is not met
- **THEN** monthly totals remain visible but no recurring-seasonality claim is presented

### Requirement: Personal recommendations are deterministic and explainable
Recommendation candidates SHALL be currently readable recipes that are favorites or have a finite personal rating from 4 through 5 inclusive. A finite rating from 0 inclusive to less than 3 SHALL exclude a recipe even if it is a favorite; ratings outside 0 through 5 or non-finite values SHALL be treated as missing for insights without rewriting stored preferences. Candidates with eligible cooking dates in the final seven local dates ending at `endDate` SHALL be excluded. Remaining candidates SHALL rank in priority order: neglected favorites; recipes recurring in the end date's calendar month when seasonal evidence is sufficient; other liked recipes. Ties SHALL use favorite status first, valid rating descending with missing ratings last, known cooking gap descending with unknown gaps last, then recipe identifier ascending. Results SHALL contain structured reason codes and supporting dates/counts/ratings, with localized explanations in the interface. They SHALL NOT invent preferences, infer nutrition needs, call an external AI service, or modify a meal plan.

#### Scenario: A highly rated meal was recorded yesterday
- **WHEN** the meal otherwise qualifies but has an eligible cooking date in the final seven local dates
- **THEN** the recommendation list excludes it

#### Scenario: A favorite also has a poor rating
- **WHEN** its current finite personal rating is 2
- **THEN** it is not recommended despite its favorite status

#### Scenario: Preferences exist but cooking records do not
- **WHEN** a user has a favorite or valid high rating without eligible cooking history
- **THEN** the recipe can be suggested as a liked recipe with an explicit missing-history explanation, not as a proven neglected or seasonal meal

#### Scenario: A user has neither favorites nor qualifying ratings
- **WHEN** recommendation candidates are empty
- **THEN** the system returns an empty recommendation section without borrowing another user's preferences or filling it randomly

### Requirement: The insight view exposes evidence and resilient states
An authenticated Cooking Insights page SHALL be reachable from existing recipe navigation and link each result to its recipe. It SHALL provide labeled date-window controls, a clearly labeled inferred-activity checkbox defaulting off, and all four views without a marketing landing screen. Loading, retryable errors, empty sections, insufficient seasonal history, and legacy coverage limits SHALL be distinct states. No data SHALL be displayed as zero because a request failed. The view SHALL show that preferences are current and gaps are relative to the selected end date. It SHALL retain Mealie's existing design conventions, support keyboard interaction and narrow viewports, and provide text/table equivalents for monthly visualizations. A filter change SHALL NOT allow an older response to replace the current selection's results.

#### Scenario: History predates structured cooking provenance
- **WHEN** accessible unclassified events exist for the current actor
- **THEN** the view explains that older unclassified timeline activity is excluded and that counts describe recorded activity, not complete lifetime cooking

#### Scenario: A request fails after successful results
- **WHEN** a new insights request fails
- **THEN** the page shows a retryable error without presenting stale results as current or converting the failure to zero counts

#### Scenario: Filters change rapidly on a narrow screen
- **WHEN** the user changes the date range or inferred-activity checkbox while an earlier request is pending
- **THEN** only the latest selection's response is rendered and controls, recipe links, and monthly data remain usable without horizontal page overflow

### Requirement: Subsequent reads reflect current stored evidence
Subsequent insights requests SHALL reflect changes to classified events and current ratings/favorites without requiring a background refresh job. Read operations SHALL NOT create events, modify ratings, or persist recommendations.

#### Scenario: A preference or cooking record changes
- **WHEN** the user removes a favorite, changes a rating, or removes cooking evidence and requests insights again
- **THEN** the response recalculates affected eligibility, ordering, and evidence from current data