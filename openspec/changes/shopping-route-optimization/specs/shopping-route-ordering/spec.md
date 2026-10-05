## Purpose

Let shoppers build and follow a practical per-list aisle sequence using existing shopping-list labels, with predictable suggestions, accessible manual reordering, and safe persistence.

## ADDED Requirements

### Requirement: Discoverable per-list aisle editor

The system SHALL provide an aisle-order action on the shopping-list detail page and retain access through the existing reorder-labels action. The editor SHALL include all labels configured for that list, including sections with no unchecked items, and SHALL distinguish an editable draft from the saved route. It SHALL use existing labels rather than create store profiles or assign labels to items automatically.

#### Scenario: Open an existing list route
- **WHEN** a user opens the aisle-order editor for a list with a saved sequence
- **THEN** the editor displays that sequence without re-suggesting or saving an order
- **AND** labels with no unchecked items remain available for ordering

#### Scenario: List without labels
- **WHEN** a user opens the editor for a list with no configured labels
- **THEN** the editor presents an empty state with access to existing label management
- **AND** suggestion and save actions are unavailable

### Requirement: Explicit deterministic route suggestion

The system SHALL offer an explicit suggestion action that changes only the editor draft. The initial recognized-name catalogue SHALL cover the existing English seed section names using case-insensitive exact matching after trimming and collapsing whitespace, without substring, fuzzy, or ingredient inference. Recognized section families SHALL follow this order: produce; bakery and grains; ambient pantry and snacks; beverages; household and other; meat and seafood; dairy; frozen. Unrecognized labels SHALL retain their relative draft order between household/other and meat/seafood. Labels within each recognized family SHALL retain their relative draft order. Suggestions SHALL retain every configured label exactly once and SHALL NOT claim to represent a store floor plan or shortest path.

#### Scenario: Suggest a mixed route
- **WHEN** a user requests a suggestion for the draft [Frozen Foods, Dairy Products, Custom Aisle, Produce, Canned Goods]
- **THEN** the draft becomes [Produce, Canned Goods, Custom Aisle, Dairy Products, Frozen Foods]
- **AND** the saved route remains unchanged until a successful save

#### Scenario: Preserve custom and non-English labels
- **WHEN** labels have names outside the recognized catalogue, including non-English names
- **THEN** all such labels remain in their relative draft order in the fallback location
- **AND** the user can move them to any position manually

#### Scenario: Recognize normalized names without partial matches
- **WHEN** the draft contains labels named "  frozen   foods  " and "Frozen Foods Budget"
- **THEN** only the first label is classified as frozen by the suggestion
- **AND** neither stored label name is changed

#### Scenario: Repeat a suggestion
- **WHEN** a user requests a suggestion twice without intervening edits
- **THEN** the second suggestion produces the same sequence as the first

### Requirement: Accessible section reordering

The system SHALL support dragging and non-drag move-up/move-down controls with equivalent results. Controls SHALL be usable with keyboard and single-pointer input, have localized accessible names identifying the section and direction, expose unavailable boundary moves, and provide touch targets of at least 44 by 44 CSS pixels. After a move, focus SHALL remain associated with the moved section and the new position SHALL be announced to assistive technology.

#### Scenario: Move a section without dragging
- **WHEN** a user activates Move Up on the third section with a keyboard or touch
- **THEN** it exchanges positions with the second section
- **AND** focus stays with the moved section and its new position is announced

#### Scenario: Boundary movement
- **WHEN** the first section's Move Up or the last section's Move Down control is rendered
- **THEN** the corresponding move is unavailable and does not change the route

#### Scenario: Customize a suggested sequence
- **WHEN** a user manually moves Frozen Foods before Produce after requesting a suggestion
- **THEN** the draft follows the user's sequence without enforcing the suggested family order

### Requirement: Cancelable isolated draft

Editing the route SHALL NOT alter the saved route or displayed shopping sections before a successful save. Cancel, Escape, and other permitted dismissals SHALL discard unsaved draft changes. Reopening SHALL use the currently saved sequence. Closing an editor SHALL NOT leave background list refresh paused.

#### Scenario: Cancel after multiple changes
- **WHEN** a user requests a suggestion, makes manual moves, and cancels
- **THEN** the list still displays its original saved order
- **AND** reopening the editor shows the original saved sequence

#### Scenario: Dismiss without saving
- **WHEN** a user dismisses a changed draft using Escape or the dialog close control
- **THEN** no label-settings update is sent
- **AND** normal list refresh resumes

### Requirement: Reliable per-list route persistence

Saving SHALL update only label positions for the current list through its existing authorized label-settings operation. Save SHALL be unavailable for an unchanged draft, while a request is pending, or while offline. A successful save SHALL use the server-returned sequence, update the visible route, close the editor, and preserve that route across reloads. A failed save SHALL preserve the last confirmed route and the editable draft, report a localized error, and permit retry or cancellation. Closing the dialog SHALL be unavailable while saving to avoid ambiguous success.

#### Scenario: Save and reload
- **WHEN** a user successfully saves a changed aisle sequence and reloads the list
- **THEN** the list and editor display the saved sequence
- **AND** the request does not change item data or another list's route

#### Scenario: Failed save
- **WHEN** the label-settings operation fails or returns no confirmed list
- **THEN** the editor remains open with its unsaved sequence and an error
- **AND** the displayed list retains the last confirmed route
- **AND** retry and cancellation remain available after the request completes

#### Scenario: Offline route editing
- **WHEN** a user is offline with a locally available list
- **THEN** draft editing remains possible but Save is unavailable
- **AND** no route write is silently queued or reported as saved

#### Scenario: Authorization rejection
- **WHEN** the existing authorization rules reject a route save
- **THEN** no route change is reported as successful and the draft remains available

### Requirement: Identity-based complete section ordering

The list SHALL group unchecked items using label identity, sort configured sections by saved numeric position, and retain labels with equal display names as separate sections. Equal positions SHALL use label identity as a deterministic tie-breaker. Numeric-looking label names SHALL NOT override the saved sequence. Valid labeled items without matching settings SHALL remain visible after configured labeled sections, ordered by label identity; items whose label details cannot be resolved SHALL remain visible with a localized fallback heading. Truly unlabeled items SHALL remain in the existing No Label section at the top. Empty sections SHALL be omitted from the shopping view, not from the route editor. Every unchecked item SHALL appear exactly once.

#### Scenario: Identical display names
- **WHEN** two different label identities have the same display name and each has unchecked items
- **THEN** they appear as distinct sections at their respective saved positions
- **AND** neither section's items are merged, overwritten, or lost

#### Scenario: Numeric names and tied positions
- **WHEN** configured labels are named "10" and "2" or have equal saved positions
- **THEN** numeric name interpretation does not reorder the sections
- **AND** saved numeric positions and the identity tie-breaker determine the sequence

#### Scenario: Item whose label setting is missing
- **WHEN** an unchecked item has a label identity not present in the list's label settings
- **THEN** the item remains visible in a fallback section after configured sections
- **AND** it is not dropped from the shopping view or copied list

#### Scenario: Unlabeled and unresolved items
- **WHEN** a list contains truly unlabeled items and items with unresolved label details
- **THEN** truly unlabeled items appear in No Label first
- **AND** unresolved items remain visible under a fallback heading without being discarded

### Requirement: Preserve shopping semantics and exported route

Changing section order SHALL preserve quantities, item identities, label assignments, recipe references, checked status, and persisted within-section item positions. Checked items SHALL remain in their separate completed-items area. Both plain-text and Markdown copying SHALL follow the visible unchecked section and item sequence and retain distinct section identities even when headings match.

#### Scenario: Route changes without item changes
- **WHEN** a user saves a new section sequence containing manually ordered items and checked items
- **THEN** item data and within-section order remain unchanged
- **AND** checked items do not rejoin unchecked aisle sections

#### Scenario: Copy the saved shopping route
- **WHEN** a user copies the list as plain text or Markdown after saving a route
- **THEN** copied unchecked sections and items follow the visible saved route
- **AND** unlabeled and unmatched items are included exactly once

### Requirement: Preserve the route during ordinary updates

Ordinary list polling, item creation, recipe additions, checking or unchecking, and label renaming SHALL NOT trigger a suggestion or replace the saved route. Label renaming SHALL preserve its section identity and position. Existing label lifecycle behavior SHALL remain compatible: new labels become orderable without re-suggesting existing labels, and deleted labels do not leave disappearing or duplicated unchecked items. After route editing ends, refreshed server data SHALL reconcile any label changes that occurred during editing.

#### Scenario: Add ingredients and check items
- **WHEN** a user adds recipe ingredients or checks and unchecks items after saving a route
- **THEN** remaining unchecked sections continue to follow that route
- **AND** newly active configured sections appear at their saved positions

#### Scenario: Rename or delete a label
- **WHEN** a configured label is renamed or deleted and fresh list data is loaded
- **THEN** renaming retains the label's existing position
- **AND** deletion reconciles sections without hiding or duplicating surviving items

#### Scenario: Refresh after editing
- **WHEN** another user changes labels while the route editor is open and the editor subsequently closes
- **THEN** refresh resumes and current server labels and items are reconciled
- **AND** the UI does not imply that simultaneous route writes have conflict detection beyond the existing API behavior