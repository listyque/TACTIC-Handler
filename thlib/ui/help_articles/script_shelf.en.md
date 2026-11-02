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

## Scope, drafts and shared controls

The shelf bar and editor share their Frame composition with Handler. Overflowing
buttons and lists retain visible scrollbars. Icon and script pickers use the
current button identity and editing scope; a delayed selection cannot change a
removed button or a different shelf. A native tab draft cannot be saved into a
different tab after the editing context changes. Discard or reopen the editor
before saving in the new context. Confirmed browser assignments immediately
show Used on this tab. Help opens the general Help window at this article.

## Buttons prepared by an external agent

The agent can prepare a Local Python draft and, with separate activation permission, publish its saved script and a shared shelf assigned to one existing sidebar entry. The effective shared buttons are retained in the new tab shelf; personal shelves and other tabs are preserved. The code executes in native Handler, not in the browser.

Local shelf scripts receive captured `TACTIC_SCRIPT_KWARGS`: `project_code`, `entryKey`, `tab_id` and selected `search_keys`. The context is captured when the button is pressed, so changing tabs before a worker finishes does not change its targets. The existing Frame example supports `show(records, modal=True)` using the current GUI engine and releases its window after close. Create UI on the GUI thread and submit slow work to existing workers; do not create another QApplication. Saving a draft and checking syntax do not execute or isolate its source.

## Where a script runs

Shelf buttons show a centered icon and their title without a TH badge.
TACTIC Stream shows only buttons the current user can execute there; local
Python and DCC actions are hidden. Saved shelf configurations are preserved
and can still be managed in the editor. Tooltips describe the runtime.
Server Python, Server JavaScript and browser JavaScript identify their runtime
in the tooltip; the Stream result window repeats it, including on errors.

The saved script language determines its runtime, not its folder or title.
Server Python is not a Handler script. A server trigger that expects event
`input` must run from its configured event; clicking a shelf button does not
provide a trigger payload.

## Custom script access by group

Open **Administration → Access rules → Custom scripts**, choose the project,
and clear the group checkboxes for prohibited scripts. The table includes every
active custom script: client scripts, server scripts, helpers and other stored
languages. Search filters script paths and group names. The **All** row denies
every custom script for that group. Save commits the draft; Reset discards it.
Checking a box again removes its own denial. Remove inherited or All-row denials
at their source. Any matching group denial wins; administrators are exempt.

Shelf buttons inherit their script's access, including personal shelves. No rule
means the previous access is preserved. Rules control explicit named execution;
they do not change language capabilities or imports inside an allowed script.
Refresh scripts/shelves after changing permissions or membership. Re-export an
old Maya shelf to remove obsolete visible buttons; the updated connector also
checks current permission when a cached button is clicked.

Rules retain the native group `access_rules` XML format with
`group="script_runner"`, `key="folder/title"`, `project="project_code"`,
`access="deny"`. Script bodies, schema and other native permissions are unchanged.
Legacy clients ignore this optional scope. Local Python and copied source are
not a security sandbox: server data permissions remain authoritative. Reconnect
old Maya sessions after updating Handler to load the updated connector.
