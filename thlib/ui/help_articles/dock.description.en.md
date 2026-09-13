---
group: Docks
icon: description
order: 29
---
# Description dock

> Description shows and edits the text associated with the current sObject, process or snapshot and
> can pin one text as the description used by the next check-in.

## Current target

The header names the exact object and scope whose description is displayed. Search, process and
snapshot selection can each change that target. Entering edit mode creates a local draft; changing
selection never silently writes it to another object.

## Controls

| Control | Behavior |
| --- | --- |
| **Edit** | Opens the current text as a draft. |
| **Save** | Commits that draft to its current target. |
| **Cancel** | Discards only the current draft and reloads the saved text. |
| **Pin** | Keeps this description as the check-in description while selection changes. |
| **Unpin** | Returns check-in description selection to the current context. |

The dock distinguishes **Editing**, **Unsaved**, **Saving** and **Used for check-in**. A pinned value is
not copied into another object's description; it is only selected as Commit Queue input.

## Typical workflow

1. Select the required object, process or snapshot.
2. Confirm the target title before editing.
3. Edit and Save the stored description.
4. Pin it only when it should follow the next prepared check-in.
5. Unpin after the check-in when the current selection should take over again.

## States and errors

- **No description** means the selected target has no saved text yet.
- **No target** means the workspace has not published a compatible selection.
- A save error preserves the draft for correction and retry.
- Closing or hiding the dock does not implicitly save edited text.
