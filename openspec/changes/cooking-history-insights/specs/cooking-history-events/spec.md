## Purpose

Provide a stable, backward-compatible way to distinguish explicitly recorded cooking from automatically inferred meal-plan activity without interpreting timeline display text.

## ADDED Requirements

### Requirement: Timeline events expose structured cooking provenance
Timeline events SHALL expose a nullable `cookingSource` with values `manual`, `mealplan`, or null independently of existing event types, subjects, comments, images, and timestamps. Omitted provenance SHALL default to null. Unsupported values SHALL be rejected with a validation error.

#### Scenario: Older clients continue to create ordinary events
- **WHEN** a client creates an event without `cookingSource`
- **THEN** creation succeeds under existing authorization rules and the returned event has null provenance without changing its existing fields

#### Scenario: Invalid provenance is rejected
- **WHEN** a client supplies an unsupported `cookingSource`
- **THEN** the API returns a validation error and does not create an event

### Requirement: Manual cooking is attributed to the authenticated actor
The existing "I Made This" action SHALL mark its primary and explicitly selected linked-recipe events as `manual` without creating additional copies or changing its existing household last-made updates. Manual events submitted through the authenticated timeline API SHALL belong to the authenticated user; a different supplied actor SHALL be rejected with a forbidden response. Public clients SHALL NOT create `mealplan` provenance.

#### Scenario: A user records cooking including linked recipes
- **WHEN** the user submits "I Made This" and selects a linked recipe
- **THEN** each existing timeline creation carries `manual`, the authenticated actor, and the selected timestamp, and each selected recipe receives only the events produced by that existing flow

#### Scenario: A client attempts to attribute cooking to somebody else
- **WHEN** a manual cooking request supplies another user's identifier
- **THEN** the API returns a forbidden response without recording cooking for that user

#### Scenario: A public client attempts to impersonate the scheduler
- **WHEN** a public timeline creation request supplies `cookingSource` equal to `mealplan`
- **THEN** the API returns a validation error without creating an event

### Requirement: Scheduled activity remains explicitly inferred
The automatic meal-plan timeline writer SHALL mark generated events as `mealplan`, preserving its existing actor attribution, display text, timestamp, last-made behavior, and duplicate suppression. Such events SHALL NOT assert that the attributed person actually cooked the meal.

#### Scenario: The scheduler processes a planned dinner
- **WHEN** the existing scheduler generates a timeline event from a meal-plan entry
- **THEN** that event is marked `mealplan` and retains the existing meal-plan actor and content

#### Scenario: The scheduler reruns
- **WHEN** the scheduler processes an entry already handled by its existing duplicate-suppression logic
- **THEN** adding provenance does not cause additional timeline entries

### Requirement: Legacy events remain unclassified
Existing timeline events SHALL retain null provenance after upgrade. The system SHALL NOT infer cooking from translated subjects, ordinary event types, or household last-made values. Existing events SHALL remain visible and editable under existing timeline permissions.

#### Scenario: An old event resembles a cooking record
- **WHEN** the application upgrades with an existing event whose subject resembles "made this"
- **THEN** that event remains unclassified and is excluded from cooking counts rather than heuristically backfilled

### Requirement: Text edits preserve cooking provenance
Editing an event's existing subject, message, or image SHALL preserve its cooking provenance. Timeline update requests SHALL NOT reclassify events; attempts to change provenance SHALL return a validation error. Removing an event under existing permissions SHALL remove its contribution on the next insights read.

#### Scenario: A cooking comment is edited
- **WHEN** a user updates the message or image of a manual cooking event
- **THEN** its `manual` provenance remains unchanged

#### Scenario: A user attempts to reclassify an event
- **WHEN** a timeline update requests different cooking provenance
- **THEN** the API rejects the reclassification without changing the stored event

#### Scenario: The last cooking event for a recipe and day is deleted
- **WHEN** the user deletes that event and requests insights again
- **THEN** that recipe/day no longer contributes to cooking history