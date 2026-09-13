---
group: Workflows
icon: code
order: 20
---
# Script shelf

> The shelf provides quick access to saved scripts from the Search workspace.

## Personal and shared shelves

A personal shelf belongs to the current user. Supervisors configure shared shelves for the project.
Either mode can use one shelf for every tab or a separate shelf for a specific sidebar tab.
The project-wide shelf is always named **Shared shelf** and cannot be renamed or deleted. Shelves
assigned to individual tabs have their own editable names.

## Setup

1. Open the shelf editor.
2. Choose personal or shared mode and its scope.
3. For a shared tab shelf, select an existing shelf or create a new one.
4. Add saved scripts from the tree, then set each label, tooltip, and icon.
5. Arrange the buttons and save the shelf.
6. Use **Apply to this tab** to activate a saved shared shelf for the current sidebar tab.

The editor heading always names the shelf currently being changed. The delete button and its
confirmation repeat that exact name, so another shared shelf cannot be mistaken for the target.

The shelf button is beside the Search field. Use its horizontal scrollbar when the actions exceed
the available width.

When Maya is connected, the editor can also create or update a native Maya shelf. Its first button
starts TACTIC Handler; the remaining buttons mirror the configured actions from the current shelf.

## Scope resolution

The compact switch chooses **Personal** or **Shared**. Within either owner, Handler first looks for a
shelf assigned to the current sidebar tab and otherwise shows the owner's common shelf. A tab-specific
assignment does not become a sidebar preset and does not affect other tabs.

Shared shelves and their tab assignments are project configuration. Personal shelves belong to the
signed-in user. Saving one owner never rewrites the other owner's document.

## Button design

Every action has a fixed 36 × 36 area, one icon, a compact elided label and a full tooltip. Keep the
visible label short and use the tooltip to describe inputs, side effects and expected result. Dragging
changes only order.

The Search shelf scrolls horizontally when actions exceed the available width; buttons do not shrink
to unreadable sizes.

## Create or update a Maya shelf

This action appears only for a connected Maya client that advertises `create_script_shelf`. Enter a
visible Maya shelf name. If it already exists, confirm Update; Handler replaces generated buttons
instead of creating a hashed duplicate.

The first Maya button starts or reveals Handler. Remaining buttons keep label, tooltip, project path,
order and rendered icon. Maya persists the tab through its native shelf mechanism.

## Missing shelf or buttons

- Confirm Personal/Shared and the current sidebar tab before editing.
- A tab-specific empty shelf intentionally overrides the common one.
- Unsaved editor changes do not replace the active shelf.
- If a server script was deleted, refresh and remove or repair the stale shelf action.
