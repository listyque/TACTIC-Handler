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
- In a portable build, installing an application update closes and reopens Handler automatically.

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

The built-in `sthpw` and `admin` projects show every Search Type in their project catalog that has
an existing table, even without a configured sidebar. Configured sidebar links keep their labels
and placement; any remaining Search Types appear as additional links.
Explicitly hidden or access-restricted sidebar links remain hidden.

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

## Project cards and keyboard

The project selector groups available projects by category. Active projects are shown by default; Retired, Templates and Built-in reveal their respective groups. Each card shows a preview, lifecycle, description, category and type; the current project is outlined. A missing category is translated, but server project/category names remain unchanged.

Focus a card and use the arrows or Home/End to move through visible projects; Enter/Space opens it. Escape closes the selector. Lists scroll independently with a reserved scrollbar gutter. Stream rearranges the same cards into two or one columns on a narrow screen.


## Profile and account editor

My Profile shows identity, groups, task counters, work-hour totals permitted by the server and recent activity. Users adds the searchable directory; search matches login, name, email and groups. Task/status/process buttons open tasks for the viewed account. Narrow windows keep the same details and a directory/back transition.

The child editor includes profile and account fields, address, a new password, avatar and group/access settings when permitted. Leave the new password empty to retain the current one. Cancel/Escape asks before discarding a changed draft; Keep editing preserves it. Save commits both editor pages through the existing account operation and revision checks; switching Profile/Groups does not discard the other page. An unknown write result disables another Save until Reload from server; entered passwords are cleared after submission or close. Server permissions decide which fields/actions are available. Handler immediately queues an avatar for an existing account; discarding text changes does not undo an already uploaded avatar. Stream submits its selected avatar with Save.

Recent activity initially shows six events. Show more reveals the remaining events already loaded for the profile; Show less returns to the preview without another request. Open full activity opens the separate activity feed. Long snapshot filenames remain available in the expanded events.

## Portable Windows bundle

`Handler.cmd` in the Stream bundle starts this native application with its
bundled Python and PySide6. The profile lives outside the program folder at
`%APPDATA%\TACTIC Stream\handler`; `TACTIC_HANDLER_SETTINGS_DIR` selects another
profile root. Server presets, login and project selection use the existing
Configuration workflow. For a local server, start Stream first and use its
window address. Remote connections do not require the local Stream EXE.
Close Handler and back up its profile before replacing the program folder.
