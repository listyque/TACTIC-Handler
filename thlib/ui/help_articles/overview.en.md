---
group: Guide
icon: help
order: 1
---
# Overview

> TACTIC Handler is a desktop workspace for finding project objects, reviewing their files and tasks,
> communicating with the team, and preparing controlled TACTIC check-ins.

## Main controls

Use the project selector and navigation drawer to choose a working area. Search tabs keep
independent queries.

Dock panels can be resized, stacked, moved, detached, reopened, and reset from Configuration.

## Usage notes

- Most server work is asynchronous.
- A busy indicator means the request is still running; errors and detailed diagnostics are available
  in Notifications and Debug Log.
- Menus use submenus for grouped commands.
- Open them with the pointer or Right arrow; Left returns to the parent menu.
- The workspace menu groups panels and keeps layout presets separate.
- Task options group View, Sort, and Group.
- The sObject menu keeps Save from Clipboard in the basic list; Advanced menu also shows preview and
  maintenance actions.
- Scrollable views use one persistent scrollbar behavior.
- Dragging its thumb navigates only the data already loaded; another page loads after a wheel,
  touch, or flick gesture reaches the end.

## How the workspace is connected

```text
Navigation or Search tab
        ↓
Selected sObject / process / task / snapshot
        ↓
Snapshots · Tasks · Description · Notes · file and DCC actions
```

Selection has one workspace owner. Following docks consume that current context; they do not keep
unsynchronized private copies. A long-running response carries its request generation, so a result
for an older project, tab or selection is ignored.

## Data-changing workflow

Most writes are split into preparation and execution:

1. Select and validate the exact project object.
2. Prepare fields, files, relation or DCC result in an editor or queue.
3. Review the operation and its dependencies.
4. Apply, save or send explicitly.
5. Refresh the owning view from the server.

Closing an editor never means that an ambiguous or destructive operation succeeded.

## Files and DCC

Repository paths and transfers belong to Handler. A selected DCC client performs native scene
actions only. Save preparation can return a file and preview to Commit Queue, but Handler chooses the
version, transfers files and creates the TACTIC snapshot.

## Persistent and temporary state

Saved configuration, window geometry, dock layout and Search-tab state survive restart in their
respective owners. Current selection, checked queue rows, native modal context and unsaved destructive
operations are intentionally not restored as if they were still valid.
