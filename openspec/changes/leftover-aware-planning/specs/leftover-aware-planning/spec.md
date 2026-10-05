## Purpose

Let households record expected meal portions and deliberately allocate predicted leftovers to later lunches or other meals, without double-booking portions or presenting forecasts as confirmed food inventory.

## ADDED Requirements

### Requirement: Optional expected portion tracking
The system SHALL allow an ordinary recipe-backed or note-only meal to record prepared and eaten portions together. Prepared portions MUST be a positive whole number; eaten portions MUST be a nonnegative whole number no greater than prepared portions. An untracked meal SHALL have both counts absent and SHALL NOT be represented as having zero leftovers. Expected leftovers SHALL equal prepared portions minus eaten portions.

#### Scenario: Record portions for a recipe meal
- **WHEN** a user saves a dinner with six prepared portions and four eaten portions
- **THEN** the saved meal reports two expected leftover portions

#### Scenario: Record portions for a note-only meal
- **WHEN** a user saves a titled note meal with five prepared portions and three eaten portions
- **THEN** the saved meal reports two expected leftover portions without requiring a recipe

#### Scenario: Preserve an untracked meal
- **WHEN** an ordinary meal is created without portion counts
- **THEN** the meal remains untracked and does not advertise leftover availability

#### Scenario: Distinguish tracked zero from unknown
- **WHEN** a meal has four prepared portions and four eaten portions
- **THEN** the meal reports zero expected leftovers rather than unknown availability

#### Scenario: Reject invalid counts
- **WHEN** a user supplies only one ordinary-meal count, fractional counts, zero prepared portions, negative eaten portions, or more eaten than prepared portions
- **THEN** the system rejects the request without changing the meal

### Requirement: Household-wide allocation accounting
For each tracked source meal, the system SHALL report its expected leftovers, the sum of portions reserved by all linked follow-ups, and the remaining unallocated portions. Remaining portions SHALL equal expected leftovers minus reserved portions and MUST NOT be negative. Totals SHALL include linked meals outside the displayed calendar range and SHALL remain allocations regardless of whether a follow-up date has passed.

#### Scenario: Allocate portions to multiple follow-ups
- **WHEN** a meal prepares eight portions, uses four at the source meal, and has follow-ups reserving one and two portions
- **THEN** its totals are four expected, three reserved, and one unallocated leftover portion

#### Scenario: Count allocations outside the visible range
- **WHEN** a source is displayed this week and a linked meal outside this week reserves its last two portions
- **THEN** the displayed source has zero unallocated portions

#### Scenario: Do not restore portions when a date passes
- **WHEN** a linked lunch date passes without the link being removed
- **THEN** its reserved portions remain allocated and are not offered to another meal

### Requirement: User-directed scheduling of linked meals
The system SHALL let a user select an eligible source meal and reserve a positive whole-number portion count for a manually chosen later calendar date and one of the existing breakfast, lunch, dinner, or side meal types. The follow-up SHALL identify its source and retain the source's recipe identity or note title and text. It SHALL NOT produce a new batch of leftovers. Planning availability SHALL be discoverable even when the source is outside the target calendar range. No follow-up SHALL be created without an explicit user save.

#### Scenario: Schedule lunch from expected leftovers
- **WHEN** a user selects a dinner with two unallocated portions and saves a lunch for the following day using two portions
- **THEN** the system creates a lunch linked to that dinner and the source's unallocated count becomes zero

#### Scenario: Reuse a note-only source
- **WHEN** a user schedules a later dinner using a tracked note-only source
- **THEN** the follow-up retains the source's note identity and records its reserved portion count

#### Scenario: Find a source in the previous week
- **WHEN** a user schedules a meal in a new calendar week
- **THEN** eligible tracked sources from earlier dates can be selected without navigating the calendar back to their week

#### Scenario: Leave the plan unchanged on cancellation
- **WHEN** a user opens leftover scheduling and cancels without saving
- **THEN** no meal is created and no portions are reserved

### Requirement: Valid source links and chronology
A follow-up's source MUST be an existing tracked ordinary meal with sufficient expected leftovers. The system SHALL reject self-links, links to other follow-ups, links to untracked sources, new reservations without sufficient unallocated capacity, and follow-up dates on or before the source date. When editing an existing follow-up, source discovery and validation SHALL include that follow-up's current reservation in its editable capacity without changing the source's reported allocation totals. A follow-up SHALL have no prepared portion count; its eaten portion count SHALL represent its positive reservation. A recipe or note identity inconsistent with the source MUST be rejected.

#### Scenario: Reject an earlier or same-day follow-up
- **WHEN** a user tries to schedule a follow-up on or before the source meal's calendar date
- **THEN** the system rejects the change and preserves all existing entries and allocations

#### Scenario: Reject invalid source relationships
- **WHEN** a user creates a new link to itself, another follow-up, an untracked meal, or a source with no unallocated portions
- **THEN** the system rejects the link without creating or changing an allocation

#### Scenario: Edit a fully allocated follow-up
- **WHEN** a user edits a two-portion lunch that already reserves all two expected portions of its source
- **THEN** source selection still includes that source with two editable portions while its ordinary unallocated count remains zero

#### Scenario: Reject a mismatched recipe
- **WHEN** a follow-up references a source recipe but supplies a different recipe identity
- **THEN** the system rejects the request rather than treating the follow-up as newly cooked food

### Requirement: Atomic reservation limits
The system SHALL reject any create, update, or source change that would make total reserved portions exceed expected leftovers. It SHALL evaluate follow-up updates by replacing the existing reservation rather than counting it twice. Concurrent requests MUST NOT both succeed when their combined reservations exceed a source's capacity. A rejected operation SHALL leave all affected meals and allocations unchanged.

#### Scenario: Reject oversubscription
- **WHEN** only one unallocated portion remains and a user requests two portions
- **THEN** the system returns an allocation conflict and does not save the follow-up

#### Scenario: Update an existing reservation
- **WHEN** a source has two expected leftovers and its only follow-up changes its reservation from one to two portions
- **THEN** the change succeeds with two reserved and zero unallocated portions

#### Scenario: Serialize competing reservations
- **WHEN** two users concurrently reserve the same last portion
- **THEN** at most one reservation succeeds and the other receives a retryable conflict without oversubscription

### Requirement: Safe linked-meal lifecycle
Deleting a follow-up or explicitly changing it into an ordinary meal SHALL release its allocation. Reassigning it to another source SHALL release the old reservation and reserve the new one atomically. Source count or date changes SHALL succeed only when every existing reservation remains valid. The system SHALL reject deleting a source, disabling its tracking, changing its recipe or note identity, or turning it into a follow-up while it has dependents; it SHALL NOT silently delete, detach, reschedule, or reduce those dependents.

#### Scenario: Delete a follow-up
- **WHEN** a user deletes a lunch reserving two portions
- **THEN** the lunch is removed and two portions become unallocated at its source

#### Scenario: Reassign a follow-up successfully
- **WHEN** a user moves a one-portion follow-up to another eligible source with sufficient capacity
- **THEN** the old source regains one portion and the new source reserves one portion in the same successful operation

#### Scenario: Preserve the old reservation after failed reassignment
- **WHEN** a user reassigns a follow-up to a source without enough capacity
- **THEN** the reassignment fails and the original link and both sources' totals are unchanged

#### Scenario: Reject a source edit that reduces capacity too far
- **WHEN** a source with two reserved portions is edited to yield only one expected leftover portion
- **THEN** the system rejects the edit and identifies the linked-meal conflict

#### Scenario: Reject moving a source past its follow-up
- **WHEN** a user changes a source date to the same date as or a later date than an existing follow-up
- **THEN** the system rejects the move and retains the original dates

#### Scenario: Reject removing or replacing a referenced source
- **WHEN** a user deletes a source or changes its tracking, recipe, note identity, or role while follow-ups remain linked
- **THEN** the system rejects the operation and requires the affected follow-ups to be edited or removed first

#### Scenario: Accept a safe capacity increase
- **WHEN** a source changes from six prepared and four eaten portions to eight prepared and four eaten portions while two portions are reserved
- **THEN** existing links remain intact and unallocated portions increase from zero to two

### Requirement: Household isolation
The system SHALL scope source discovery, source references, allocation totals, and mutations to the authenticated user's household. It SHALL NOT expose source metadata or accept links across households, even within the same group. A foreign source reference SHALL be indistinguishable from a nonexistent source reference.

#### Scenario: Prevent a same-group cross-household link
- **WHEN** a user attempts to link a follow-up to a source in another household in the same group
- **THEN** the request is rejected as not found and no source details or allocation totals are disclosed

#### Scenario: Isolate discovery results
- **WHEN** a user requests eligible leftover sources for a target date
- **THEN** results contain only eligible sources belonging to that user's household

### Requirement: Backward-compatible untracked planning
Existing stored meals and create or random-meal requests without leftover fields SHALL retain their current behavior. Update requests omitting the new fields SHALL preserve existing portion metadata and source links; explicit nulls SHALL request clearing subject to linked-meal safeguards. Existing recipe-or-title validation SHALL continue to apply. Invalid legacy edits to a linked meal SHALL fail without corrupting the relationship.

#### Scenario: Keep legacy recipe and note creation working
- **WHEN** an existing client creates a valid recipe meal or titled note without leftover fields
- **THEN** creation succeeds as an ordinary untracked meal

#### Scenario: Keep random planning unchanged
- **WHEN** a user requests a random meal using the existing planner rules
- **THEN** the system creates an untracked ordinary recipe meal and does not allocate any leftovers

#### Scenario: Preserve new metadata on an older-client update
- **WHEN** an existing client updates a meal's valid date or meal type without supplying new leftover fields
- **THEN** the existing portion counts and source link remain intact

#### Scenario: Explicitly disable unused tracking
- **WHEN** a user explicitly clears both counts on a source with no linked follow-ups
- **THEN** the meal becomes untracked without changing its recipe or note identity

### Requirement: Clear and accessible planner interactions
The planner's edit and view modes SHALL distinguish ordinary meals with expected leftovers from linked meals consuming them, display relevant portion counts and source references, and label leftover availability as expected rather than confirmed inventory. Portion controls SHALL have visible labels, whole-number validation, and keyboard access. Save failures SHALL keep the dialog open and preserve entered values; rejected date moves SHALL restore the displayed saved plan. Scheduling SHALL work without drag-and-drop and SHALL not create new recipe, ingredient, or shopping-list data.

#### Scenario: Show source and allocation in the calendar
- **WHEN** a user views a source dinner and its linked lunch
- **THEN** the source shows expected and unallocated portions and the lunch shows its reserved portions and source reference

#### Scenario: Preserve input after a conflict
- **WHEN** saving a follow-up fails because another user reserved the requested portions first
- **THEN** the editor remains open, entered values are retained, current availability is refreshed, and a localized conflict is shown

#### Scenario: Restore a rejected drag move
- **WHEN** a user drags a follow-up to an invalid date and the server rejects it
- **THEN** the calendar restores the saved date and displays the failure rather than leaving an unsaved move visible

#### Scenario: Schedule with a keyboard on a narrow viewport
- **WHEN** a keyboard user schedules leftovers on a mobile-width planner
- **THEN** source, date, meal type, portions, and save controls remain reachable, labeled, and usable without horizontal overflow or dragging

#### Scenario: Do not imply actual stock or trigger ingredient work
- **WHEN** expected leftovers are displayed or a linked meal is saved
- **THEN** the planner does not claim the food is confirmed available or safe to eat and does not automatically scale recipes or add shopping-list ingredients