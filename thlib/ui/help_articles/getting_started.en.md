---
group: Guide
icon: play-arrow
order: 2
---
# Getting started

> Connect to a TACTIC server, select a project, then choose a Search Type or saved search from the
> navigation drawer.

## Main controls

The top bar contains the project selector, connection state, selected DCC client, queue, activity,
theme, Configuration, and profile actions. The workspace below contains movable docks and search
tabs.

## Usage notes

- Open Configuration first when no server is configured.
- Project-defined Search Types, processes, statuses, groups, contexts, and pipelines are displayed
  exactly as supplied by TACTIC.
- TACTIC Handler runs as one desktop instance.
- Launching it again restores the existing main window, including when it is hidden in the system
  tray.
- On Windows, both launchers use the Handler taskbar icon.
- Restart Handler completely after an update to apply startup changes.

## First connection

1. Open **Configuration → Server**.
2. Select or create a server preset and verify its address, portal and proxy routing.
3. Use **Test** to check the visible draft without saving or requesting credentials.
4. Use **Generate ticket** to authenticate and save the server page.
5. Configure a usable default repository when Handler offers Repository setup.

Connection state and authentication are different: a reachable endpoint can still require a new
ticket, and a saved ticket can expire while the server remains reachable.

## Choose the workspace project

Open the project selector, filter retired, template or built-in projects only when needed, then
activate one project. Activation reloads sidebar Search Types, saved searches, tasks and project
metadata. Merely selecting a project card does not switch the workspace.

## Find and inspect work

1. Open a Search Type or saved search from the navigation drawer.
2. Narrow the result with text, tags, Quick Filters or Advanced Search.
3. Select an sObject to publish it to Snapshot Browser, Tasks, Description and Task Inspector.
4. Select its process, task, context, snapshot or file as the next operation requires.
5. Use the item's menu for edit, link, duplicate, delete, check-in or DCC actions allowed by the current state.

## Optional Maya connection

Start the installed Handler launcher from Maya. The top-bar DCC selector then shows application,
scene and PID. Select the intended process before Open, Import, Reference, Save, DCC scripts or DCC
triggers. Handler remains responsible for file synchronization and TACTIC check-in.

## If startup does not complete

- Open **Application Error** and copy its complete traceback.
- Open **Debug Log**, select the startup or connection group and copy the session path.
- Verify server address, VPN/proxy, active ticket and repository configuration separately.
- For Maya, inspect `maya.status()` and Maya's Script Editor output.
