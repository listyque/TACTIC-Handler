# Application UI: purpose and runtime behavior

This document maps the current user-facing application to its Python owners and
side effects. It describes the active QML application only; deleted QWidget
screens and migration-phase names are not runtime architecture.

A QML file or registered window is not considered functional unless its
controller, model, persistence, error, and lifecycle paths are connected and
tested.

## Composition and navigation

- `thlib/ui/application.py` is the composition root.
- `Main.qml` owns the native main window chrome and global application actions.
- `DockHost.qml` owns dock placement, stacking, floating, resize, and restored
  layout.
- `DockContentRegistry.qml` routes dock kinds to feature views only.
- `WorkspaceLayoutPresetController` stores named project-wide copies of the
  same `DockPanelModel` layout document in TACTIC `widget_config`. The workspace
  panel menu saves, replaces, applies, refreshes, and deletes them. Sidebar
  Search Tabs may reference a preset and apply it synchronously from the loaded
  project configuration when opened.
- `WindowHost.qml` and `FloatingWindow.qml` host native top-level functional
  windows.
- `WindowContent.qml` routes registered window kinds to their feature views.
- `ApplicationController` is the public QML-facing application facade; domain
  controllers own feature state and side effects.
- Shared controls live under `thlib/ui/qml/controls` and never depend on feature
  controllers.

Search results are the persistent workspace center. Other panels open from the
workspace menu, context actions, card/process/task actions, or dedicated
configuration/help routes.

Snapshot Browser has one persisted content mode owned by
`ApplicationController`: preview and files, preview only, or files only. Its
QML fills the available dock with the remaining surface, removes the hidden
file list from its model, and clears hidden preview image sources so a hidden
surface does not continue presentation work.

## Session, server, and projects

The session workflow includes server preset selection, ticket authentication,
connection state, project catalog, project selection, and bootstrap.

- Server/network operations run in the server pool.
- The active authenticated login is derived from the session ticket.
- Project records retain server-defined code, title, category, type, lifecycle,
  built-in/template state, preview, and statistics.
- Project preview loading is asynchronous and must not reset selection.
- Project Chooser and Configuration use the same catalog and filters.
- Project selection is one application navigation path; secondary windows do
  not maintain another current-project value.
- Server and UI configuration persists through the existing project
  configuration/environment APIs only.
- Repository storage has a dedicated Configuration route below Server. After
  online bootstrap, a missing current-platform path for the default repository
  produces one modal setup offer per launch; the offer routes to Configuration
  and does not persist dismissal.

Connection changes can replace the active ticket and reload project state.
Test them against an isolated server account.

## Search workspace

Search tabs own their Search Type, complete filter payload, query, paging,
presentation mode, sort/group mode, selection, and expansion state.

- Search and detail requests run outside the GUI thread and carry generation or
  request identity.
- A late page or detail response cannot update a different tab/selection.
- Continuous paging starts only after user scroll and does not reset scroll.
- Preview requests use native File metadata and repository freshness checks.
- Card, compact, and tree presentations consume the same workspace model.
- Regular snapshot rows show the Maya product version stored in legacy File
  metadata under `app_info.p` when it is available.
- Expanded process and child rows are lazy and preserve their own source
  identity.
- Sorting defaults to the established server/name behavior and explicit user
  selection.
- Grouping, including task-status grouping, is a presentation over the current
  result identity set unless its contract explicitly requires a server query.

Changing zoom or layout never issues a search or recreates server objects.

## Common search, Advanced Search, and filters

The common search field owns suggestions, tokens/tags, keyboard behavior, and
theme presentation.

Advanced Search is the visible source of the complete applied filter state:

- conditions preserve order and flat AND/OR operators;
- presets use the server `config/widget_config` contract;
- quick filters and tags become visible search conditions rather than hidden
  post-filters;
- supervisors can publish a quick-filter standard per sidebar entry in
  `config/widget_config`, with `view="quick_filters@" + section.entry_key`
  and global `login=""`; custom entries of one Search Type stay independent;
- everyone can save the current search tab's layout locally; supervisors have
  an additional server-default save button in the same editor;
- `groups` and `defaultSelections` form the single unversioned widget payload;
  partial or versioned payloads fail validation and have no migration reader;
- the standard editor opens as an owned native modal window, so its server
  policy draft cannot be mixed with changes in the underlying workspace;
- the shared standard owns group order, visibility, allowed values, and the
  starting selection for new ordinary search tabs;
- each user's later selection, including an explicitly empty selection, stays
  in the local search-tab cache; **Restore standard quick filters** releases
  that local override without changing the server record;
- hidden groups and disallowed values are server policy and are removed from
  local states when the shared configuration changes;
- My Tasks and selected-login filtering may use verified TEL expressions;
- Apply performs one common asynchronous search and resets paging;
- Cancel restores the editor snapshot and does not mutate the active tab;
- preset links serialize an explicit custom search identity suitable for
  navigation.

Project-defined Search Type, pipeline, process, status, group, user, and context
labels are displayed unchanged.

## Results and object details

Result item actions include selection, expansion, Snapshot Browser, tasks,
notes/messages, Add/Edit/Link/Delete/Duplicate, Check-in/Out, repository sync,
and database editing where permissions and context allow.

Ordinary selection may update dependent mini editors quietly. It must not show
a global detail-loading overlay or force unrelated Task Manager scopes to
reload.

`SObjectInfoController` owns the information window:

- identity and status summary appear first;
- task/process/status cards are interactive;
- task notes, children, snapshots grouped by process, files, activity, work
  hours by user, total hours, and cost use explicit sections;
- task activation opens/selects the correct task workspace and inspector;
- child and activity navigation uses the owning project, never an unrelated
  `sthpw` search tab;
- activity is scoped on the server to the selected object and combines object
  mutations, task field and status history, notes, snapshots, work hours,
  direct-child creation/deletion, and instance link/unlink transactions;
- parent references use the native `search_id` path when present, while the
  per-object `sobject_log` index and an identity-filtered transaction query are
  combined before any page limit; unrelated project traffic therefore cannot
  displace older object or child-link events;
- the Activity section loads fifty records initially and requests older pages
  when the shared report scrollbar reaches the end after a wheel, touch, or
  flick gesture; scrollbar-thumb dragging never triggers a server page;
- deleted related records remain readable from their transaction metadata,
  while live child and task events retain navigation to the useful editor;
- the full summary, icon-labelled section switcher, and active section share
  one continuous scrollbar; the summary never becomes a compact sticky header;
- summary, task, note, and snapshot dates use shared localized friendly labels,
  while their exact timestamps remain available on hover;
- duplicate summary layouts are not maintained.

Server mutations and downloads require an isolated test project/repository.

## Snapshot Browser and Repository Sync

Snapshot Browser projects native snapshots/files into QML-safe records and uses
native File methods for paths, repository identity, size, timestamp, preview,
and open behavior. File-menu commands retain the file selected at invocation
until the native popup finishes its delayed dispatch; Edit Info opens the
owning business sObject in the shared schema-driven editor.

Repository Sync owns discovery, queue state, progress, retries, partial files,
freshness validation, overwrite decisions, and local-state refresh.

- A current local file is returned immediately without an HTTP request, visible
  queue entry, completion log noise, or batch notification.
- Freshness compares existence, expected size, and server timestamp. Optional
  checksum validation is reserved for explicit full synchronization.
- Repository discovery and preset queries run outside the GUI thread.
- Presets are cached by project/Search Type and updated from the same editor
  result.
- Download completion updates only affected file/preview state.
- Queue shutdown cancels supported work and waits through its owned pools.

## Check-in / Check-out, Drop Plate, and Commit Queue

Check-in/Out owns target tabs, process/context, files, options, naming preview,
prepared payload, direct execution, and exact snapshot/file refresh.

Drop Plate asynchronously scans and groups files with the active Matching
Templates and explicitly hands checked groups to Commit Queue. It never commits
automatically.

Commit Queue owns prepared operation identity, editing, selection, reorder,
sequential run, progress, retry, safe cancellation boundaries, completed state,
and persistent unfinished payloads. It reuses the Check-in executor.

See the dedicated contracts for complete boundaries and acceptance cases.

## Tasks workspace

`TasksController` is the QML facade over one Python-owned task store.

The quick process editor and full Tasks Workspace share native task identity and
workflow catalogs. Supported scopes include current object, selected objects,
user/team, Search Type, and project. Scope changes are explicit.

The detailed workspace provides table, grouped, calendar, and Gantt
presentations, local sorting/filtering, Shift/Ctrl selection, staged edits,
bulk edits, task creation/deletion, history, notes entry points, and exact Task
Inspector synchronization. Opening notes for a concrete task updates that
context in the already visible Task Inspector without reflowing or resizing its
dock.

Large lists use reusable delegates and defer hover editors during scroll.
Progress cannot consume width needed by status and assignee columns.

## Notes, Messages, drafts, and notifications

Notes and status history form a bottom-anchored communication timeline for the
selected parent/process/task context. Enter sends and Ctrl+Enter inserts a line.

Draft text and attachments are persisted per target identity. Switching target,
closing the window, or restarting cannot discard or leak a draft into another
conversation.

File dialog, screenshot, clipboard, and drag/drop use one attachment staging
model. Existing files download through Repository Sync; uploads reuse the
shared check-in/Commit Queue workflow.

Notifications are a bounded presentation over controller events. They coalesce
progress and duplicates, retain full errors in Debug Log, and never replace
modal confirmations.

## SObject Add/Edit/Link/Delete

Add/Edit is server EditWdg-driven. QML delegates render normalized safe field
descriptors; Python owns widget metadata, validation, and native commit.

Link SObjects has separate available and linked panels, common search,
continuous paging, Shift/Ctrl selection, arrow movement, and visual drag/drop
in both directions. It computes and saves only the relation diff.

Deletion uses the universal dependency-aware deletion window. It resolves
human-readable dependent objects and statuses, preselects required dependencies,
and uses the existing SObject deletion APIs. Task deletion also discovers notes
belonging to the parent/process scope.

## Work hours, reports, calendar, and Gantt

Timesheet, work-hour reports, and cost reports use the shared task/work-hour
data owners and localized application strings. Server project labels remain
unchanged.

Calendar builds its initial month immediately and redraws without requiring a
month switch.

Gantt maintains persisted section membership until Save. Staging dates for an
unscheduled task does not move it into the scheduled group prematurely.
Date/progress changes support bounded undo/redo and verified working-day
behavior. Both ends of a scheduled task bar expose wider resize targets; these
edge targets take pointer priority when the progress handle coincides with them
at zero or full completion.

## Script Editor

The Script Editor provides a script tree, common tabs, source editor above
output, syntax highlighting, line numbers, find/replace, matching-token
highlight, completion, local/server execution confirmation, selected-text run,
persistent dirty drafts, output wrapping, text sizing, scrollbars, and bounded
local edit history. Saved versions are reconstructed on demand from the selected
`config/custom_script` object's native TACTIC transaction log. Selecting one
loads its source as an unsaved, locally undoable edit; saving creates the next
normal server revision.

The right panel switches between server scripts and a filterable class/function
outline. Python completion follows statically discoverable local imports and
members without importing project modules. Tab inserts spaces; Ctrl+Shift+K
deletes lines, Ctrl+Shift+O opens the outline, Alt+Up/Down navigates symbols,
F12 opens an in-file definition, and Ctrl+Enter runs the selection with either
the main or numeric-keypad Enter key.

Line numbers follow the source editor's native line geometry. Outline and
keyboard symbol navigation place the destination at the top of the viewport.
Panel sizes and visibility, output wrapping, the selected side panel, and font
size are restored with the Script Editor. New returns to an existing untouched
draft instead of accumulating blank tabs.

DCC Python persists that a script is intended for the selected capable DCC.
Local Python runs in TACTIC Handler, and Server Python keeps the existing
server-side path. The execution selector can temporarily override the saved
default. DCC source is staged in the tab's validated file under
`custom_scripts/.temp` only while it is new or modified. An unchanged saved
script runs directly from its synchronized project path. Neither route sends
Python source as a protocol command; an unavailable DCC is an explicit error,
not a silent Handler fallback. Closing or discarding a draft removes its
temporary file. DCC stdout and stderr stay visible in the DCC console and are
also returned to the active tab. New output automatically expands the Output
panel.

Server script deletion is available only from the tree context menu. Full
traceback is retained in Debug Log. The help topic documents every shortcut.

Script Triggers, opened from the Script Editor toolbar, stores project-wide
ordered rules in `config/trigger`. Any number of saved scripts may match one
Handler action and they run from top to bottom. A failing before-action script
blocks the action; after-action failures are logged while later rules continue.
Maya scene open/import/reference/save rules are labeled `Maya DCC`, accept only
DCC Python, and execute in the client performing that action. Other rules accept Local Python, Server Python,
or Server JS. Snapshot open/save rules wrap the standalone Handler operation,
including a repository download before opening. Optional Search Type, exact
search key, process, and context filters narrow a rule without changing
server-defined names.

## Configuration and Help

Configuration uses a native resizable window, semantic pages/sections,
descriptions, scrolling, validation, dirty state, Apply/Save/Cancel/Reset, and
one close guard. Each setting uses the same API/key as its runtime consumer.

Help is built-in user documentation backed by ordinary UTF-8 Markdown files in
`thlib/ui/help_articles`. Topic filenames end in the language code, for example
`checkin.en.md` and `checkin.ru.md`; a missing translation falls back to English.
The viewer renders headings, lists, links, quotes, tables, and fenced code, and
can open the current source file for manual editing and reload it immediately.
Every new or changed window, dock, workflow, and shortcut updates both language
files in the same change. Docks expose their relevant topic through a button or
drag-grip context menu.

## DCC integration and Handler Server

Standalone owns TACTIC, repository, and check-in. Thin DCC connectors expose
fixed native application actions and are routed by explicit client id.

A Maya bootstrap connects to an existing Handler or launches standalone as a
separate process with visible progress. Repeated start reuses the live client
and publishes its hot-reloaded capabilities without reconnecting; closing Maya
unregisters it. Maya-owned scene-open errors stay in Maya unless
the routed Handler command itself fails.

Generated Python, `eval`, and `exec` payloads are not a thin-client protocol.

## Persistence, logging, and lifecycle

Persistent UI settings and caches use `env_read_config`/`env_write_config` with
clear owners. There is no QSettings, registry, compatibility adapter, or
parallel format.

Debug Log stores full diagnostic events with compact on-disk field keys and
user-readable presentation. Credentials are redacted. Normal production volume
is controlled by event levels rather than truncating an event.
Transport timeouts and refused connections show concise, localized recovery
guidance in the error window. The original exception, runtime command, and
complete traceback remain unchanged in Debug Log for diagnosis.

Every long-lived worker, timer, watcher, popup, window, and process has explicit
shutdown ownership. Popup placement uses current invocation coordinates,
screen bounds, and shadow margins.

## Verification boundary

Safe offline checks cover model transformations, configuration isolation, QML
creation, layout, keyboard/touch interaction, lifecycle, and local temporary
files.

Live acceptance is required for authentication, permissions, server mutations,
repository transfer/check-in, network shares, DCC routing, and destructive
dependency deletion. Use only isolated test projects, repositories, and DCC
scenes.
