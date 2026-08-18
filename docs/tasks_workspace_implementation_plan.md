# Tasks Workspace contract

This document records the current Tasks Workspace behavior and the decisions that
must survive future changes. It is not a development diary.

Visual references:

- [Current modern UI](assets/tasks_workspace_current_ui_reference.png)
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

All surfaces use one normalized task collection and stable `task.code` identity.
Changing presentation, grouping, sorting or local filters must not issue a server
request.

## Selection contract

Selecting a parent sObject displays all of its tasks. Selecting a process narrows
the view to that process. Multi-selection displays tasks for every selected parent.
A task activation carries the exact `(task code, parent key, process)` tuple into
Task Inspector, Notes, Gantt, Calendar and Snapshot Browser.

TACTIC permits multiple `sthpw/task` records for one parent/process. Ordinary notes
remain attached to the parent plus process/context, while status history belongs to
the exact task. A separate conversation per task would be new server behavior and
must be introduced explicitly through metadata rather than inferred by the UI.

## Data and server rules

- Use native TACTIC objects and the established batched task query.
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

## Responsive table

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

## Task Inspector

The header contains the title, task/process selector and standard dock actions.
Work Hours remains immediately below it. Expanding reveals status, assignee,
supervisor, start/deadline with time, progress, priority, milestone and description.
Save and Discard appear only when the shared draft differs from server state.

The collapsed and expanded forms use the same task record, draft and save operation.
Opening the full editor uses the identical schema-driven form rather than a second
task-creation path.

## Gantt and Calendar

Gantt and Calendar are projections of the currently filtered task collection.
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

Task view, scope, sort/group modes, visible columns, filters and dock layout use the
functional controllers' existing settings keys. Configuration exposes every
user-facing persistent option; caches, drafts and per-tab transient state stay out
of Configuration.

## Acceptance

The workspace is accepted only when these scenarios pass without additional server
requests or visual jumps:

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
