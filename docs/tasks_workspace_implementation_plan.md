# Tasks Workspace contract

This document records the current Tasks Workspace behavior and the decisions that
must survive future changes. It is not a development diary.

Visual references:

- [Current application UI](assets/tasks_workspace_current_ui_reference.png)
- [Approved workspace composition](assets/tasks_workspace_approved_mockup.png)

The current application defines the visual language. The mockup defines the
information hierarchy. Existing shared controls, theme values, dock behavior and
responsive rules take precedence over one-off mockup styling.

## User surfaces

- Quick Tasks is the compact process-oriented editor.
- Task Browser is the detailed table with scopes, filters, grouping, sorting,
  selection, bulk editing, Gantt and Calendar projections.
- Task Inspector is the collapsible task editor inside the Notes surface.
- Notes follows the exact selected task, parent and process.
- Snapshot Browser follows the shared task context without owning task state.
- User Profile shows a summary and opens Task Browser for detailed management.
- Supervisor scopes reuse the same task store and query contract.

All surfaces use one normalized task store and stable `task.code` identity.
Switching table/Gantt/Calendar presentation reuses the loaded page. Filters,
sorting and grouping change the server query: applying them only to a downloaded
inventory or to one page would produce incorrect results and ordering.

## Selection contract

Selecting a parent sObject requests its tasks in bounded pages. Selecting a process narrows
the view to that process. Multi-selection displays tasks for every selected parent.
A task activation carries the exact `(task code, parent key, process)` tuple into
Task Inspector, Notes, Gantt, Calendar and Snapshot Browser.

Only Selected scope follows Search selection. Project, Search Type, user and team
scopes remain explicitly chosen scopes. The Search Type scope action always uses
the active Search tab's native type and title, even when the tab is empty or its
sidebar entry represents a named preset; it does not derive the type from the
last detail payload. Search selection signals cover Ctrl/Shift selection and
Select All independently of asynchronous object details.

`TasksController.sync_presentation` derives active consumers from
`DockPanelModel.is_panel_presented`: Quick Tasks and Task Inspector consume the
process editors; Task Browser and Task Calendar consume the advanced task scope.
Switching the Tasks dock's surface updates these consumers even when the dock's
own visibility has not changed. Detached docks use the same path. Hidden scopes
defer selection projection and apply the latest selection when shown again;
single-object details reuse the existing Search request. Unsaved task changes
still block a context change. The obsolete `tasks_workspace` window does not own
task visibility. Controller wiring and real QML mouse/keyboard scope interactions
are covered by `tests.test_task_search_sync` in narrow and wide layouts.

Changing the selected result assigns a new detail-request generation immediately.
The previous worker is detached and cancelled; a queued cancellation must never
hold the selection slot or delay Task Inspector from following the latest click.

TACTIC permits multiple `sthpw/task` records for one parent/process. Ordinary notes
remain attached to the parent plus process/context, while status history belongs to
the exact task. A separate conversation per task would be new server behavior and
must be introduced explicitly through metadata rather than inferred by the UI.

## Data and server rules

- Use native TACTIC objects and the established batched task query.
- Task pages are bounded to 1..500 records. Scope, text, field/quick filters,
  presets, note presence, date constraints and global ordering are applied before
  count/offset/limit in `query_task_workspace_page`. Same-field quick choices and
  presets are OR groups; different filter groups are ANDed.
- Scope-wide grouped facet counts keep alternative filter choices available.
  Aggregate expressions use native `Search.add_column('count(*)',
  as_column='task_count')` after setting only that query's
  `Search.get_select().set_quoted_mode('none')`. Both `Search.add_column` and
  `Select.add_column` in TACTIC 4.9 lack the `quoted` keyword; simply omitting it
  would quote `count(*)` as an identifier. Projection/table names are fixed and
  scope filters are built before switching this Select's quoting mode. The
  SQL-backed regression in `tests.test_task_server_filters` enforces the 4.9
  signatures and verifies every facet count, including unassigned/empty values.
  Reference: native [Select](https://github.com/Southpaw-TACTIC/TACTIC/blob/4.9/src/pyasm/search/sql.py)
  and [Search](https://github.com/Southpaw-TACTIC/TACTIC/blob/4.9/src/pyasm/search/search.py).
  Parent titles are resolved on the server, including native cross-database
  search filters. Sorting resolves only parents referenced by the selected scope.
- Computed task ordering uses Select's native `( CASE ... END )` expression
  form; bare SQL expressions are treated as column identifiers by its order
  formatter. Unscheduled tasks remain last in both deadline directions, and
  `code` breaks ties before pagination. `tests.test_task_server_filters` verifies
  pagination and executes orders built by the audited native Select source.
- Filter changes debounce for 180 ms and immediately invalidate the previous
  request generation. Load More cannot append a page for an obsolete query.
  Hidden consumers defer the latest query until presentation resumes.
- Relative deadlines/presets use the requesting client's calendar day, included
  in the query cache key. A server in another timezone cannot silently change
  the meaning of Today; the next day's query does not reuse yesterday's facets.
- `TaskWorkspaceStore` owns page membership, facets and query-scoped cached
  results. Unmatched dirty tasks remain editable; checked/selected native objects
  are retained for actions without being inserted into the matching result page.
  A refreshed checked task uses fresh server data; an unsaved draft keeps its
  original baseline. These exceptions do not increase the server's match count.
- Never issue a server request per row or delegate.
- Python owns native objects; QML receives flat role records and stable codes.
- `code` is the identity; deprecated numeric ids are not generated.
- Worker results update models through Qt signals and stale request generations are
  discarded.
- Full snapshots, attachments, histories and work-hour details load lazily.
- Bulk edits modify only explicitly selected fields and never create missing tasks
  as a side effect.
- Workflow process definitions provide valid statuses, assignment groups, default
  duration, completion and expected work hours.
- Task schema/widget configuration is cached per project and invalidated explicitly.
- Task field-catalog requests use a parent only in object scope, taken from the
  resolved native sObject. Search Type, project, user, team and multiple-object
  scopes request `sthpw/task` configuration without `parent_key`; a scope token
  is not an object key. This rule applies to the initial load and catalog retries,
  and is covered by request-boundary tests in `tests.test_tasks_controller`.

## Responsive table

Task selectors open with one click, including the first interaction after hover.
`TaskTableEditorCell` keeps a closing editor resident through the shared release
debounce so a native popup focus transition cannot destroy ComboBox's queued
opening recovery. This lifecycle delay is independent of animation preferences;
scrolling and disabled editing still unload the editor immediately. The same owner
is used by sObject Task Workflow cells. Regression coverage in
`tests.test_task_combo_activation_qml` uses native popups, mouse/touch input,
Escape, and the real task table/model at narrow and wide sizes.
One coordinator releases every idle editor from a hovered row, not just its last
column. `UserAvatar` renders both lazy cell placeholders and active user selectors
from the same indexed user catalog. Profile updates refresh pictures, initials and
identity colors without hover; no selector or user-options list is created for
that update. The avatar regression compares assignee and supervisor presentation
before/after hover using a catalog populated after the table was constructed.

The table uses one shared column geometry for headers and rows. The object summary
stays compact so ordinary widths retain status, assignee, dates, progress, notes and
hours. Optional columns such as priority, milestone and supervisor are controlled by
the column menu.

At narrow widths, unavailable columns move into the expanded task editor rather
than being squeezed to zero. The row expander remains visible at the left and uses
the same closed/open chevrons as sObject rows. The expanded editor is one responsive
grid: fields flow across available columns and Description occupies a full-width
row. Creating and editing reuse the same form and validation.

New unsaved tasks remain at the top regardless of grouping. Their background and
save/discard state distinguish them from committed tasks.

Collapsing a group reconciles rows by stable task code and preserves surviving
delegates. It must not reset the table model. Sort/group changes request a new
globally ordered page; hidden Gantt presentation is refreshed when opened.

## Task Inspector

The header contains the title, task/process selector and standard dock actions.
Work Hours remains immediately below it. Expanding reveals status, assignee,
supervisor, start/deadline with time, progress, priority, milestone and description.
When the selected process has no task, the Inspector presents the workflow-default
task as an inline editable record and Save creates it immediately. Existing tasks
show Save and Discard only when the shared draft differs from server state. A
compact plus beside Edit keeps the complete schema-driven creation editor available.

The collapsed and expanded forms use the same task record, draft and save operation.
The full editor uses the same schema-driven form.

## Gantt and Calendar

Gantt and Calendar are projections of the loaded, server-filtered task collection,
not an implicit download of every task in the project. Load further pages to
include further matches. Selecting a Calendar day adds a server deadline filter.
The dock model owns Calendar visibility; a retained QML view cannot restart hidden
projection work. Hidden Gantt and Calendar models are marked dirty, not rebuilt.
Gantt supports pan on empty canvas, wheel zoom, direct task-bar scheduling and
visible milestones. Interactive controls consume pointer events before canvas pan.
Calendar displays tasks and milestones using workflow/status colors and opens the
same selected task context.

Neither view owns a second task cache. Edits return through the task controller and
refresh the shared projections after confirmation.

## Dock composition

Search occupies the compact left column, Tasks the wider center column, and Notes,
Calendar and Snapshot Browser share a reorderable right-side stack. Docks can be
stacked, reordered, swapped, floated and restored without recomputing unrelated
split ratios.

The Python dock model owns the split/stack tree, active tab, ratios and persisted
layout. QML owns only live pointer and visual state. Resize deltas use stable scene
coordinates and persist once when dragging ends. Restored geometry is clamped to
the shared minimum sizing policy. Reset Layout restores the complete default tree.

## Persistence

Task view, sort/group modes, visible columns and dock layout use the functional
controllers' existing settings keys. The working scope, query filters, collapsed
groups, calendar position and selected task are saved as one bounded session per
project, then restored before the first task query after startup. Checked rows,
unsaved task edits and server data are not part of that session. Configuration
exposes preferences; caches, drafts and per-tab transient state stay out of
Configuration.

## Acceptance

The workspace is accepted only when these scenarios pass without redundant server
requests or visual jumps (scope/filter changes and explicit saves require requests):

- select one parent, one process and several parents;
- switch table, Gantt and Calendar over an already loaded store;
- create, edit, discard and bulk-edit tasks;
- follow a task into Inspector, Notes and Snapshot Browser;
- resize through wide, ordinary and minimum supported widths;
- stack, reorder, float, close, restore and reset docks;
- reopen the application with persisted task and dock state;
- scroll and collapse large grouped task collections smoothly.

Environment-dependent mutation, permission, repository and DCC checks remain part
of the release acceptance contract rather than being inferred from QML loading.
`tests.test_task_server_filters` exercises predicates, grouping, counts, ordering
and pages against an in-memory SQL database; controller/QML tests cover request
generations, draft retention and presentation. The guarded read-only
`tests/run_live_server_procedure_smoke.py` additionally exercises filtered pages,
parent ordering and contextual note matching on the configured test project.
The note-presence correlation uses the deployed PostgreSQL TACTIC schema; SQLite
tests supply `split_part` for logic checks and do not certify another SQL backend.
