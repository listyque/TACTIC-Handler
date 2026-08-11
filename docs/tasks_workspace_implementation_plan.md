# Tasks Workspace implementation plan

## Status and visual contract

This document is the staged implementation contract for the Tasks Workspace.
No stage should silently expand into a later stage. Each stage must remain usable
after completion and must preserve the existing quick task editor.

Visual references:

- [Current modern UI](assets/tasks_workspace_current_ui_reference.png)
- [Approved Tasks Workspace mockup](assets/tasks_workspace_approved_mockup.png)

The current UI image is the source of truth for the application visual language.
The mockup is the source of truth for the proposed information architecture. If
they conflict, preserve the real application's controls, dimensions, theme and
dock behavior while following the mockup's placement of task functionality.

### Integration checkpoint — 2026-08-09

- Tasks Workspace now uses the existing Tasks Dock instead of a parallel
  standalone window.
- The dock has Quick and Browser surfaces; Quick preserves the process editor,
  while Browser contains the detailed table, filters, bulk editing and Gantt.
- Selecting a Browser row updates the shared task context used by Notes Task
  Inspector and Snapshot Browser, including rows belonging to another parent.
- Calendar remains an independent dock and Snapshot Browser remains shared.
- Stages 2–10 describe implemented functional slices, but their visual status is
  not accepted until the assembled dock layout is compared with the approved
  mockup at wide, ordinary and minimum supported window sizes.
- Stage 11 remains paused until that visual/dock acceptance pass is complete.

### Fixed decisions

- The existing quick process task editor remains the fast editing surface.
- Task Browser becomes the detailed table and management surface.
- The same task data feeds cards, rows, table, Gantt, Calendar, User Profile and
  supervisor views.
- Task Inspector is a collapsible section at the top of Notes, not another dock.
- Snapshot Browser remains a reusable dock/view and follows the selected task.
- Gantt is a Task Browser view, initially read-only.
- Calendar is a separate dock that uses the same filtered task data.
- There is no Results Dock.
- Quick Filters use the existing compact popup and chip language.
- Calendar and Snapshot Browser do not create a permanent fourth-column layout.
- Sources contain English strings; localization supplies other languages.
- Existing theme colors, controls, icons, menus, shadows and animations are reused.

### Dock layout correction

- The approved three-column composition requires structural split and tab-stack
  nodes; the former five fixed dock areas are not the target architecture.
- Notes, Calendar and Snapshot Browser remain independent docks but share one
  right-side stack and can be reordered or dragged out of that stack.
- Task Inspector and the selected sObject/process header form one collapsible
  component inside Notes. The collapsed form keeps the sObject preview, clickable
  title, active process/context, status and progress. The expanded form adds all
  task fields and task selection when a process has more than one task.
- Opening, closing or moving a dock must not recompute unrelated split ratios.
- Dock layout refactor stage 1 is complete: Python now owns a split/stack tree,
  preserves hidden branches and synchronizes committed resize ratios.
- Dock layout refactor stage 2 is complete: a dock can be inserted against a
  concrete target edge and root-edge drops remain available. This stage also
  introduced ratio-preserving panel swaps; stage 3 exposes them through the
  target title while reserving center drop for tabification.
- Dock layout refactor stage 3 is complete: center drop now creates a visible
  tab stack, dropping over the target title swaps panel positions, tabs can be
  activated and reordered, and a tab can be floated by dragging it out or by
  its explicit action. Closing or floating the active tab selects the next
  available member. Inactive stack content remains instantiated so switching
  tabs does not recreate views or restart their data loading.
- Dock layout refactor stage 4 is complete: resize handles resolve the deepest
  owning split node instead of guessing adjacent rectangles, update only that
  split ratio and calculate limits from both complete child subtrees. Stack
  minimums use the largest visible member; split minimums are combined along
  the split axis. Pointer previews never write QSettings and the final ratio is
  saved once on release. Host resize clamps the full tree in one pass.
- Dock layout refactor stage 5 is complete: `workspace/dockLayoutV2` persists
  the structural split/stack tree, split ratios, stack order and active tabs
  together with floating and detached window state. The reader validates and
  repairs unknown panels, duplicate references, invalid ratios and obsolete
  geometry. No pre-release layout formats are retained or written.
- Dock layout refactor stage 6 is complete: stacked docks use the existing dock
  title row as their tab strip instead of adding a second chrome row. Tabs keep
  readable semantic titles, share the available header width, scroll only when
  the minimum usable tab width cannot fit, and leave active-dock actions aligned
  at the right edge.
- Dock layout refactor stage 7 is complete: the default workspace now matches
  the approved three-column composition. Search occupies the compact left
  column, Tasks owns the wider center column, and Notes, Calendar and Snapshots
  share the right stack with Notes active. Description keeps a dormant position
  in that stack and becomes a tab only when opened. Reset workspace layout
  restores this complete structure and all of its visibility states.
- Dock layout refactor stage 8 is complete: Notes no longer has a separate
  sObject/process toolbar above Task Inspector. One collapsible Inspector now
  owns the selected sObject preview and clickable title, process/context
  selector, current task status, assignee and progress. Its expanded surface
  adds task selection, dates, history count, progress detail, description and
  the existing full-editor action. It reuses the Search model preview and the
  established Notes/task controllers without another query or task model.
- Dock layout refactor stage 9 is complete: host-size clamping is now a
  temporary geometry projection and never overwrites the user's preferred
  split ratios. Returning from a narrow or restored window therefore restores
  the chosen layout. Docked minimum widths match the existing compact Search,
  Tasks and right-stack presentations, while floating windows retain their
  larger standalone limits. The approved three-column ratios remain unchanged
  at 1000 px and degrade proportionally only below their combined usable width.
- Dock layout refactor stage 10 is complete: Search, Tasks and the right stack
  now share one 96 px working-header baseline. The Tasks embedded toolbar uses
  the remaining height below common dock chrome, while collapsed Task Inspector
  uses the same remainder. Embedded Tasks keeps only horizontal content insets.
  Task table, Gantt, Search and Notes also share the common 58 px footer height,
  so both horizontal composition lines remain stable across view switches.
- Dock layout refactor stage 11 is complete: the Tasks toolbar now keeps the
  approved Object, Selection, My Tasks, Project and Team scopes visible at a
  normal center-column width and collapses them only below 820 px. Grouping,
  sorting and direct process/status selectors enter progressively instead of
  competing for the search field at the same breakpoint. Every displaced
  action remains available through Quick Filters or the existing overflow menu.
- Dock layout refactor stage 12 is complete: Table, Gantt and Calendar navigation
  now uses one shared mode switcher in the common Tasks footer, matching the
  approved information hierarchy and freeing the search/filter toolbar for its
  primary controls. Table and Gantt reuse the same component; below 380 px the
  footer switcher yields space and the same commands remain in overflow.
- Dock layout refactor stage 13 is complete: the Tasks dock title now identifies
  its active object, selection, user, team or project scope instead of showing a
  generic browser label. The footer reports projected task and process counts;
  pagination remains a separate loaded/total indicator, so filtered, loaded and
  server-total values are no longer presented as one ambiguous number.
- Dock layout refactor stage 14 is complete: bulk editing keeps its compact
  selection bar, while secondary date, progress and description fields now use
  a responsive popup in the application overlay. Its controls wrap below
  420 px and the surface is clamped to the window instead of the Tasks item,
  preventing clipping at minimum dock width.
- Dock layout refactor stage 15 is complete: Task Browser columns now use wide,
  dense and compact width limits. Process, assignee, dates and progress remain
  visible at ordinary center-column widths; version joins when enough room is
  available. At minimum width the table reduces to Object and Status with
  tighter shared spacing instead of overflowing or squeezing controls randomly.
- Dock layout refactor stage 16 is complete: expanded Task Inspector reuses the
  quick editor's selected-task record, pipeline status/user choices, draft,
  validation and asynchronous save path. Status and assignee are editable in
  place, with explicit Save and Discard actions. Selecting another task in Notes
  synchronizes the quick editor by stable task code without another server query.
- Dock layout refactor stage 17 is complete: deadline and progress in the expanded
  Task Inspector now use the same quick-editor draft and commit operation as status
  and assignee. Date ordering, accepted date syntax, progress range and schema
  support are validated before the worker starts; invalid input remains staged and
  visible until corrected or discarded. Field names are mapped to the existing
  `bid_end_date` and project task progress columns only in Python.
- Dock layout refactor stage 18 is complete: task activation now has one ordered
  `(task code, parent key, process)` route from Quick, Browser, Gantt and Calendar
  into Notes. The adapter preserves the Notes controller's public argument order,
  while Notes buttons and quick multi-task selection carry the exact task code.
  Selecting a task therefore updates the Notes process, Task Inspector and
  task-specific status history without requiring a second click or refresh.

### Server semantics that must not be hidden

The original interface supports multiple `sthpw/task` objects for one sObject
process. Its ordinary notes, however, are queried and created using the parent
sObject plus `process/context`, not a task code. Status history belongs to the
specific task. Therefore the first implementation keeps process notes shared and
switches task-specific Inspector and status history when another task is chosen.

A separate conversation per task would be a new server-side behavior. If it is
approved later, it should use an explicit `task_code` in note metadata and receive
its own migration and visibility rules. It must not be introduced accidentally as
part of the visual Tasks Workspace work.

## Shared implementation rules

- Use native TACTIC object APIs and the established batched query paths.
- Do not build per-row server queries.
- Do not pass TACTIC objects into QML delegates.
- Python owns task objects and exposes flat records and stable task codes to QML.
- `task.code` is the row identity. Process alone is not an identity.
- Worker results reach QML models through queued signals.
- Changing view, grouping, sorting or local filters performs no server request.
- Existing workspace task data is reused when its scope and freshness are valid.
- Heavy related data such as full snapshots, attachments and histories is lazy.
- Bulk operations never create missing tasks as an implicit side effect.
- Existing task pipelines determine valid statuses and assignable login groups.
- Restored dock sizes are clamped to usable minimum dimensions.
- Any persistent user-facing option must also appear in Configuration.

## Stage 0 — Baseline and regression harness

Status: completed on 2026-08-04. The recorded baseline and remaining live-server
checks are in `docs/qml_ui_contracts/communication.md`.

### Scope

- Record current quick editor behavior for one task, no task and multiple tasks.
- Record current Notes selection, status history and process switching behavior.
- Add focused smoke coverage for task record identity, grouping and selection.
- Measure current task queries for one object, multiple objects, project and user.
- Confirm which optional task columns exist in the active server schema.

### Deliverables

- A short baseline section in the task/communication contract.
- Fixtures or lightweight test records for mixed task pipelines.
- A query-count baseline that can detect N+1 regressions.

### Acceptance

- No functional or visual change.
- Existing quick Tasks and Notes continue to open and save.
- Known schema-dependent columns are explicitly listed.

## Stage 1 — Canonical task workspace store

Status: completed on 2026-08-04. `TaskWorkspaceStore` now owns the detailed
task source, stable identities, parent indexes, paging state and request
generation while `TasksController` retains its existing QML-facing API.

### Scope

Create one Python-owned task workspace state used by all detailed task views.
Keep the existing public `TasksController` QML API working while responsibilities
are separated only where they have independent state and lifecycle.

Supported scopes:

- current sObject;
- selected sObjects;
- current user;
- chosen user;
- login group/team;
- current project.

Each task record should provide, when available:

- task code and search key;
- parent search type, code, search key, title and preview URL;
- project;
- process, label, color, type and task pipeline;
- context;
- status, color and valid status choices;
- assignee login, display name and avatar;
- start, deadline, progress and due state;
- description;
- note count;
- latest snapshot/version summary;
- selection, dirty, loading, error and conflict state.

### Query strategy

- Current object reuses loaded workspace tasks when valid.
- Multiple objects use the existing multiple-task query path.
- User/team/project scopes query `sthpw/task` once per page.
- Parent objects are loaded in batches grouped by search type and code.
- Status and user catalogs come from loaded pipeline/login data.
- Results support incremental pages rather than a permanent 500-row ceiling.

### Acceptance

- Switching local views performs zero new server calls.
- Repeated task codes cannot appear as duplicate rows.
- Multiple tasks on one process remain distinct.
- Stale worker results cannot replace a newer scope.
- Quick editor behavior is unchanged.

Implementation notes:

- object scope reuses `WorkspaceState._task_sobjects` without a new request;
- multiple-object scope keeps the established batched task query;
- user, team and project scopes load one task page and batch lightweight parents
  by search type; full snapshot and attachment payloads remain lazy;
- parent identity is `(search_type, project_code, code)`, so equal codes from
  different types cannot collide;
- view sorting, grouping and filters operate on flat records and perform no
  server request;
- `advancedHasMore`, `advancedLoadedCount` and `advancedTotalCount` expose the
  incremental paging contract without changing the current presentation.

## Stage 2 — Detailed Task Browser table

Status: functionally complete; dock integration corrected on 2026-08-09. The
approved compact table/list hybrid in `TaskBrowserTable.qml` is now the Browser
surface of the existing Tasks Dock. Quick task cards and compact rows remain a
separate surface. Final visual acceptance remains manual.

### Scope

Replace the current advanced list presentation with the approved table/list
hybrid while retaining the current dock infrastructure.

Initial columns:

- selection;
- parent object preview and name;
- task/process;
- status;
- assignee;
- start/deadline;
- progress;
- latest version;
- notes;
- overflow actions.

Optional columns are added only when verified in the schema: priority, task type,
attachments and dependencies.

### Interaction

- Single click selects the active task.
- Ctrl-click toggles rows; Shift-click selects a range.
- Checkbox selection is independent of the active Inspector row.
- Double-click or the open action navigates to the parent sObject.
- Status and assignee use the existing compact MD3 selectors.
- Inline changes are staged and expose Save/Discard rather than saving per binding.
- Missing task slots stay in the quick editor; the detailed table lists real tasks
  unless a later explicit “show missing tasks” mode is approved.

### Layout acceptance

- It matches the approved three-column reference at common window sizes.
- Dock headers and bottom bars share baselines with sObjects and Notes.
- Narrow widths reflow or hide secondary columns without overlapping controls.
- No spreadsheet grid, thick black borders or large blue selection blocks.
- Row virtualization does not replay expensive entrance animations on scrolling.

Implementation notes:

- active row and checkbox selection are independent; Ctrl-click toggles checked
  rows and Shift-click checks the visible range from the last anchor;
- status and assignee changes are local drafts until the shared Save or Discard
  action is used;
- the table reuses `SmoothListView` delegates and disables preview entrance
  animation, so recycled rows do not replay expensive effects;
- parent object, task/process and status remain visible at the minimum width;
  assignee, dates, progress and version hide progressively without overlap;
- Calendar, Gantt, bulk editing and Task Inspector are intentionally not embedded
  in this view because they belong to later approved stages.

## Stage 3 — Selection and bulk editing

Status: completed on 2026-08-04. Checked rows now open a contextual bulk bar;
the operation addresses exact task search keys and never creates a missing task.

### Scope

Add a contextual bulk bar that appears only when task rows are checked.

Supported first-pass fields:

- status;
- assignee;
- start;
- deadline;
- progress;
- description only if explicitly enabled for the operation.

### Safety and validation

- Every field has a separate enable switch; disabled fields remain unchanged.
- Mixed values display as mixed, never as an arbitrary first-row value.
- Status is validated against every selected task pipeline.
- Assignee is validated against every process login-group restriction.
- The preview reports eligible, skipped, invalid and unchanged tasks.
- Existing multiple-edit API is preferred; no duplicate update loop in QML.
- Partial server errors remain attached to affected rows.
- Apply cannot run twice and failed rows remain selected for retry.
- Creating missing tasks is a separate named command with separate confirmation.

### Acceptance

- Bulk operations affect exactly the checked task codes.
- Filtering after selection cannot silently expand the operation.
- A mixed-pipeline selection cannot save an invalid common status.
- Refresh updates only affected task rows and related summaries.

Implementation notes:

- status and assignee options are the intersection of the choices permitted by
  every checked task; a mixed-pipeline value outside that intersection blocks
  Apply and marks the affected rows;
- status, assignee, start, deadline, progress and description each have an
  independent enable switch, and mixed values require an explicit replacement;
- the preview distinguishes eligible, unchanged, invalid and skipped tasks;
- a single existing `update_multiple` server request is built from the checked
  task search keys, so filtering cannot expand the operation and no parent-based
  task creation path is involved;
- successful and unchanged rows leave the selection, while a failed batch keeps
  its rows checked with per-row errors for retry;
- list updates use role-level `dataChanged` emissions from `RecordListModel` and
  do not trigger a full server reload.

## Stage 4 — Grouping, sorting and Quick Filters

Status: completed on 2026-08-04. All Stage 4 operations run over the loaded
`TaskWorkspaceStore`; changing filters, grouping, sorting or collapsed groups
does not schedule a worker or issue a server request.

### Scope

All operations in this stage are local over the loaded store.

Grouping:

- process;
- assignee;
- status;
- parent object;
- project/search type when the scope contains them;
- none.

Sorting:

- deadline;
- recently changed;
- process;
- assignee;
- status;
- parent object.

Quick Filter popup:

- All;
- My Tasks;
- Unassigned;
- Overdue;
- Today;
- Review;
- process chips;
- status chips;
- assignee chips in supervisor scope.

### Behavior

- Chips are generated from loaded catalogs and task data, not hardcoded workflow
  status names.
- Active filters are visible without reopening the popup.
- “All” clears the compatible quick-filter layer.
- Search text, quick filters and advanced filters compose predictably.
- The popup toggles on the same button, closes after an action when appropriate,
  and closes on outside click or Escape.

### Acceptance

- No server calls when filtering, grouping or sorting.
- Selection remains stable by task code.
- Group headers show counts and can collapse without destroying delegates.

Implementation notes:

- Quick Filter groups are built from the loaded task records and pipeline/user
  catalogs; process, status and supervisor assignee chips are never hardcoded;
- preset chips compose as an OR group, while preset/process/status/assignee
  groups compose with each other and with search text and field filters;
- active filters remain visible as removable chips below the toolbar, while All
  clears only the Quick Filter layer;
- sorting supports deadline, recent changes, process, assignee, status and
  parent object; grouping supports process, assignee, status, parent object and,
  when present in the scope, project and search type;
- group metadata is stored as roles on the existing task rows, so collapse keeps
  row delegates and stable task-code selection rather than rebuilding a second
  grouped model;
- filtering no longer clears the active task merely because its row is hidden.

## Stage 5 — Task Inspector integrated with Notes

Status: completed on 2026-08-09. Notes keep their process-scoped conversation,
while the fixed Inspector selects one exact task by `task.code` and displays only
that task's status history.

### Scope

Add a compact, collapsible Task Inspector above the existing Notes history.

Inspector fields:

- task/context selector when the process has multiple tasks;
- parent object and process;
- status and assignee;
- start/deadline;
- progress;
- description summary;
- open full editor action;
- task-specific status history summary.

### Notes behavior

- Selecting a process chooses the preferred task using the original rules and a
  stable remembered task code.
- Selecting another task changes Inspector and status log immediately.
- Process notes remain visible as the original shared process thread.
- The Notes composer and attachment behavior remain unchanged.
- Notes are not reloaded when only Inspector expansion changes.
- The selected task and process are preserved when the dock is reopened.

### Acceptance

- Multiple tasks on one process can be selected explicitly.
- Status events are taken only from the chosen task.
- Notes do not disappear merely because another task is chosen.
- The Inspector collapses to one compact summary row.

Implementation notes:

- preferred task selection follows the established order: remembered task code,
  task assigned to the current login, then the first task in the process;
- multiple tasks are exposed through a compact selector with context, assignee,
  status and code, so equal process/context rows remain distinguishable;
- switching the selected task is local: it reuses loaded task objects and note
  records, changes only the task-specific status events and performs no request;
- the Inspector is fixed between the Notes header and history instead of being a
  scrolling list header; its expanded state continues to use the existing dock
  preference;
- the full editor action addresses the selected task by code, not by a mutable
  workspace row index;
- workspace task-model updates refresh the Inspector from the existing Python
  objects without creating a second task model or task-scoped notes format.

## Stage 6 — User and supervisor workspaces

Status: completed on 2026-08-09. Personal and team dashboards now use the
canonical `TaskWorkspaceStore`; User Profile consumes a compact projection of
that same source instead of issuing its own `sthpw/task` query.

### User presets

- My Tasks;
- Today;
- Overdue;
- Waiting for Review;
- Recently Updated;
- selected project/object scope.

### Supervisor presets

- team/login-group tasks;
- per-user workload;
- unassigned tasks;
- overdue tasks;
- status distribution;
- review queue;
- bulk assignment and deadlines.

### Rules

- Supervisor availability follows existing permissions and login groups, not a
  hardcoded display name such as “admin”.
- User Profile opens the same store filtered by that login.
- Team switches are scopes, not new task controllers.
- Workload summaries are derived from loaded/paged task data and clearly state
  their scope; they are not presented as global totals when incomplete.

### Acceptance

- Opening tasks from User Profile selects the correct user scope.
- Supervisor and personal dashboards share identical task row components.
- Restricted actions remain disabled with a clear reason.

Implementation notes:

- My Tasks, Today, Overdue, Review and Recently Updated are local presets over
  the loaded task page; changing them does not issue a server request;
- team scopes are built only from the current login's native
  `get_login_groups()` memberships and load members with one task query, rather
  than exposing every globally configured login group;
- per-user workload, unassigned, overdue and status summaries are derived from
  the current store page and the UI explicitly marks a paged result as partial;
- the User Profile task preview is capped to a compact twelve-row projection,
  while its count and Open Task Workspace action address the same user scope;
- opening a user scope that is already loaded does not query it again, and a
  scope change is rejected while staged task edits are unsaved;
- database assumptions were checked against `docs/tactic_database`: task writes
  continue through the existing task APIs, `status_log` remains read-only, and
  login-group membership is read through the existing object model;
- team access is not inferred from labels such as admin or supervisor. Invalid
  or unavailable group scopes are blocked before querying; server-side TACTIC
  permissions remain authoritative for task mutations.

## Stage 7 — Interactive Gantt view

Status: completed on 2026-08-09. `TaskGanttView.qml` is a virtualized,
editable projection of the filtered `TaskWorkspaceStore`; switching between
the table and Gantt performs no server request. Schedule editing was completed
on 2026-08-09 without introducing a separate task-write path.

### Scope

- Reuse current scope, filters, grouping, selection and task records.
- Display task rows against a date scale using start and deadline.
- Show progress inside bars and status/process colors consistently.
- Represent unscheduled tasks in a separate compact section.
- Display dependencies and milestones only if confirmed by native schema/API.
- Clicking a bar selects the same task and updates Inspector/Notes.
- Dragging a bar moves its start and deadline together; dragging either edge
  changes the corresponding date.
- Dragging an unscheduled task onto the timeline creates its initial one-day
  schedule.
- Ctrl+wheel and the footer controls zoom around the pointer/viewport centre;
  Shift+wheel, the header and middle-button dragging pan the timeline.

### Non-goals for this stage

- creating dependencies;
- automatic scheduling;
- critical-path calculation.

### Acceptance

- Opening Gantt performs no duplicate task query.
- Horizontal and vertical scrolling remain synchronized and smooth.
- Large ranges do not instantiate an object for every day/task intersection.

Implementation notes:

- the date range and bar geometry are calculated once in Python from the
  already filtered rows; QML receives flat day offsets and durations rather
  than task objects or date calculations in delegates;
- scheduled rows and tasks with a missing/invalid start or deadline are shown
  in separate sections while retaining the active grouping and collapsed state;
- one virtualized vertical list owns both labels and bars, so vertical scrolling
  cannot drift; a single shared horizontal offset drives the header, grid and
  every visible bar;
- scale markers are adaptive weekly, biweekly or four-week ticks plus month
  boundaries. The view never creates a day-by-task cell matrix;
- bar progress uses the task progress/completion value and the established
  status/process colors;
- drag and resize gestures only stage `bid_start_date` and `bid_end_date` in
  the shared Task Browser draft model. The existing Save/Discard controls own
  validation, asynchronous commit, error reporting and conflict handling;
- no network request runs during pointer movement. Date changes are committed
  only after the user presses Save;
- task activation reuses the existing stable task-code selection and forwards
  the selected task to the Notes Inspector when the same parent sObject is open;
- `milestone_code` and `depend_id` exist in the documented 5.0 task schema, but
  dependencies and milestones remain hidden until their populated live-server
  semantics are confirmed through the native APIs.

### Extended planning controls (2026-08-09)

- Checked scheduled tasks can be shifted together, aligned by start or
  deadline, distributed sequentially, and extended or shortened from one
  compact bulk menu. All changes remain drafts until the existing shared Save.
- Gantt-only undo/redo restores schedule and progress drafts without discarding
  status, assignee, or other Task Browser edits. The history is bounded and is
  cleared after a successful save or a full discard.
- Collapsed groups show a summary range and average progress. The same summary
  becomes a workload overview when tasks are temporarily grouped by assignee.
- Calendar-day and weekday planning are switchable per session. Weekends are
  shaded, workday moves preserve workday duration, and weekend deadlines,
  overdue tasks, missing assignees, invalid schedules, and overlapping work for
  one assignee are surfaced without automatic rescheduling.
- Timeline presets cover fit, days, weeks, months, and quarters. A compact
  overview strip shows the full range, viewport, today, warnings, and aggregated
  bars for large result sets without creating a second task model.
- Progress can be dragged directly on a task bar when the installed task schema
  exposes `progress` or `completion`; it is staged and saved through the same
  schema-aware task update path as the other task edits.
- Dependencies, milestones, baselines, holidays from `special_day`, and saved
  planning scenarios are intentionally not written yet. The database inventory
  confirms their columns/tables, but not the installed server's populated
  semantics or the native mutation contract required to implement them safely.

## Stage 8 — Calendar dock

Status: completed on 2026-08-09. The month calendar is a separate workspace
dock backed by the current `TaskWorkspaceStore` projection.

### Scope

- Separate dock using the same task store and filters.
- Month view first; week view can follow after the month behavior is stable.
- Colored task/status markers, overdue state and per-day counts.
- Clicking a day filters/highlights Task Browser.
- Clicking a task selects it and opens Inspector/Notes.
- Today and month navigation use the shared date policy/time zone.

### Acceptance

- Calendar navigation does not query the server for already loaded ranges.
- It remains usable at the shared minimum dock width.
- Calendar state survives dock close/reopen without overriding per-window filters.

### Implemented

- the dock uses the same filtered records as Task Browser and Gantt; changing
  month only rebuilds 42 local calendar cells and never starts a server worker;
- deadlines are grouped by day with status colors, overdue counts and a compact
  dot layout at the shared 380 px minimum dock width;
- wider cells expose compact task markers without creating a task-by-day matrix;
- selecting a day applies the existing day filter to Task Browser while the
  calendar itself retains the full filtered month, and selecting it again clears
  that day filter;
- task activation reuses the stable task-code selection signal, remembers the
  exact task for its parent/process and opens the existing Notes dock;
- month, selected day and filtered scope live in the Python controller, so dock
  close/reopen does not reset them or introduce a separate QML preference store;
- week view remains intentionally deferred until month behavior is validated in
  normal use.

## Stage 9 — Snapshot Browser task context

Status: completed on 2026-08-09. Task selection now projects its parent,
process and context into the existing Snapshot Browser without creating a
second snapshot model.

### Scope

- Reuse the existing Snapshot Browser rather than creating a task-specific copy.
- Follow selected parent sObject, process and context.
- Show icon/preview priority using native File/Snapshot behavior.
- Surface latest version and file count in the task row only from summary data.
- Load full file/version detail only when Snapshot Browser is visible.

### Acceptance

- Selecting another task does not duplicate files or snapshots.
- Cached summaries invalidate when check-in completes for the affected context.
- Preview loading does not block Task Browser scrolling.

### Implemented

- task rows use a cached per-parent/process summary from the parent objects
  already returned by the batched task query; rows expose latest version,
  snapshot count and latest-snapshot file count without passing snapshots or
  files into QML delegates;
- activating a task reuses the shared Snapshot Browser controller and models,
  while keeping the source TACTIC object on the Python side;
- the full snapshot query starts through the existing server pool only when the
  Snapshot Browser dock is visible; its result is published on the GUI thread,
  cached per loaded parent object and reused when switching processes;
- the browser follows the exact task process and context, while the native icon
  snapshot is used only as the first preview candidate and is not duplicated in
  the task process file list;
- snapshot and file rows retain their native File/Snapshot path, repository,
  preview and size behavior; duplicate snapshot/file codes and duplicate preview
  URLs are removed when the projection is built;
- closing and reopening either docked or detached Snapshot Browser emits one
  visibility transition, so hidden docks do not start detail work and reopening
  synchronizes the last active task;
- successful check-in invalidates only the affected parent/process summary;
  when that context is already displayed, the existing Snapshot Browser refresh
  owns the query and emits the same address-local summary update;
- focused tests cover icon preview priority, duplicate suppression, lazy full
  projection, one summary calculation per parent/process and reuse of the shared
  Snapshot Browser loader.

## Stage 10 — Persistence and Configuration coverage

Status: completed on 2026-08-09. Tasks Workspace preferences now use the
existing `TACTIC-Handler/modern-qml` settings store and have a dedicated Tasks
page in Configuration.

Persist as workspace/user preferences:

- selected Task Browser view;
- visible columns, widths and order;
- grouping and sorting;
- Inspector expanded state;
- dock geometry and layout;
- Calendar view;
- optional dashboard preset.

Do not persist as global configuration:

- active row;
- checked task codes;
- temporary bulk values;
- loading/error state;
- cached task pages.

Any newly persistent user-facing setting must receive a logical control in the
existing Configuration UI and use the same key/API as the functional view.

### Acceptance

- Existing user settings are not overwritten by new defaults.
- Corrupt/obsolete geometry is clamped to current minimum sizes.
- Per-window customization is not overridden without an explicit Apply to All.

### Implemented

- Task Browser view, sorting, grouping and the ordered column definition are
  loaded before the first model projection and saved through one controller;
- every task column has one normalized key, label, visibility flag, width and
  order; Object and Status remain required, widths are clamped, unknown or
  duplicate keys are ignored and missing columns receive current defaults;
- the table header and row use the same ordered GridLayout projection, so a
  Configuration change cannot desynchronize labels from controls;
- responsive hiding remains an additional safety layer at narrow widths and
  never changes the stored user preference;
- the existing Notes Task Inspector preference is exposed on the same Tasks
  Configuration page and applies immediately through its owning controller;
- dock and floating-window geometry continue to use the shared workspace models,
  including their existing minimum-size clamp; no second geometry store was
  introduced;
- active rows, checked tasks, bulk drafts, temporary filters, loading state and
  the currently displayed calendar month remain session state and are not saved;
- Calendar currently has one supported month view, so no meaningless persistent
  selector is written before another view exists; dashboard presets remain
  optional and were not added;
- QSettings restoration and QML compilation are covered by regression tests,
  including reordered columns and confirmation that transient task state is not
  written.

## Stage 11 — Incremental updates, conflicts and performance

Status: completed on 2026-08-09. Tasks reuse the shared five-second server
update stream; affected task codes are coalesced into one asynchronous query,
while note and snapshot summaries update the matching process rows directly.

### Scope

- Apply server update events to affected task codes only.
- Update note/snapshot counts without reloading the table.
- Detect dirty-row conflicts when a server update arrives.
- Add incremental page loading for project/team scopes.
- Measure delegate count, model resets, QML signals and query count.
- Throttle progress and live-update signals.

### Acceptance

- Switching cached scopes and views is visually immediate.
- No full model reset for one task update.
- No animation restarts when rows return through viewport virtualization.
- No network or filesystem work occurs in the GUI thread.
- Reopening/closing docks leaves no workers, timers or signal connections behind.

Implementation notes:

- the server update service requests activity on every poll only while Tasks or
  Activity Feed needs it; opening Tasks does not create another poller;
- status and task change events are deduplicated by task code and resolved in a
  single `sthpw/task` query after a short coalescing interval;
- note counts use exact values from the open Notes context and deduplicate its
  note codes against live events; remote note events update only matching
  parent/process rows;
- publication events refresh the affected parent's native snapshot cache in the
  worker pool, then update snapshot roles without reloading the task table;
- a dirty task changed by the server enters an explicit conflict state. Saving
  is blocked until the user chooses the server version or rebases local edits
  onto the latest server object;
- project, team and user scopes retain incremental pages and report the logical
  query count for each page; filtering, sorting and grouping remain local;
- the shared record model now supports one batched role update per row. Task
  performance counters expose delegate rows, projection rebuilds, model resets,
  data changes, structure changes, controller signals and server queries for
  regression diagnostics;
- closing Tasks cancels its pending load/live workers and coalescing timer;
  application shutdown also cancels task workers and the shared update worker;
- regression coverage verifies that a one-task live update emits data changes
  without a model reset, note counts update incrementally, conflicts require an
  explicit resolution, and all Task/QML components still compile.

## Stage 12 — Production polish and regression pass

Status: completed on 2026-08-09. The final pass keeps the approved three-dock
composition, closes the confirmed empty/error/obsolete-data edge cases and
adds a compact toolbar/table layout at the minimum Tasks dock width.

Implementation notes:

- clearing the current sObject is now a normal empty scope with a specific
  prompt; it no longer presents a server-style error or retains stale totals;
- a task status removed from its current pipeline remains visible as
  unavailable, so an existing task is never shown as status-less, while that
  obsolete value is excluded from bulk assignment choices;
- missing logins remain readable by their stored login with an empty avatar;
  no replacement user or invented identity is assigned;
- a failed refresh leaves the last complete task page visible, stops loading
  state and reports the failure, preserving a useful offline/read-only view;
- the embedded toolbar moves quick editor, view, calendar, sorting, grouping
  and filter reset actions into the shared overflow menu at narrow widths;
  the mandatory object/status table columns are clamped for the minimum dock;
- Notes bubbles now retain equal inner horizontal air on both sides without
  changing the established aligned dock header and composer baselines;
- automated coverage includes empty selection, absent tasks, multiple tasks,
  batched multi-object/mixed-type loading, removed status, missing assignee,
  partial bulk failure, live note/snapshot updates, old preferences, minimum
  width and background-work cancellation;
- the focused Tasks/Notes/communication/dock suite passes, all related QML
  components instantiate offscreen without warnings, and the existing
  QWidget Tasks and Notes modules still import unchanged.

### Scenarios

- no selected object;
- one object with no tasks;
- one task per process;
- multiple tasks per process;
- multiple selected objects;
- mixed search types and pipelines;
- missing user/avatar;
- invalid or removed status;
- insufficient permission;
- offline/server error;
- partial bulk failure;
- new snapshot/note while open;
- narrow main window;
- saved layout from an older version;
- repeated open/close;
- legacy Tasks and Notes.

### Visual acceptance

- Compare each completed state against both saved visual references.
- Use the current modern UI as the control/style source.
- Keep dock header and footer baselines aligned.
- Preserve compact density with small vertical breathing room.
- Use subtle selection surfaces, semantic icons and soft shadows.
- Avoid thick outlines, bright full-row blue and duplicated labels.

### Technical acceptance

- Python syntax and targeted task tests pass.
- QML loads without warnings.
- No binding loops or destroyed-object access.
- Worker signals are queued.
- Legacy Tasks/Notes behavior remains available.
- No new QWidget dependency enters the modern presentation layer.

## Recommended delivery sequence

The stages should be requested and implemented in this order:

1. Stage 0 — baseline;
2. Stage 1 — shared store;
3. Stage 2 — detailed table;
4. Stage 3 — bulk editing;
5. Stage 4 — grouping and Quick Filters;
6. Stage 5 — Inspector and Notes task selection;
7. Stage 6 — user/supervisor scopes;
8. Stage 7 — Gantt;
9. Stage 8 — Calendar;
10. Stage 9 — Snapshot Browser integration;
11. Stage 10 — persistence and Configuration;
12. Stage 11 — incremental updates/performance;
13. Stage 12 — final regression and polish.

Stages 0–5 form the first complete production slice. Stages 7 and 8 should not
begin before the shared store, selection and filters are stable.
