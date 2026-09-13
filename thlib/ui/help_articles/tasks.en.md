---
group: Workflows
icon: tasks
order: 16
---
# Tasks and planning

> Task tools provide object-level task editing and project-wide table, Gantt, calendar, timesheet, and
> reporting views.

## Main controls

Use scope, team filters, quick filters, columns, sorting, grouping, bulk selection, status and
assignee editors, dates, progress, notes, and delete actions. A Tasks badge on an sObject or process
opens Task Manager in Selected scope.

Selecting a task row updates Task Inspector for that exact task without changing the Inspector's
saved expanded or collapsed state. When one process has multiple tasks, its badge menu shows each
task's context, assignee, and status; the process row opens the task list from already loaded data.

## Usage notes

- Only Selected scope follows sObject selection; project, Search Type, user, and team scopes stay
  unchanged while compact task editors continue to follow the selected result.
- Task note badges use the native per-process TACTIC counts.
- Edit sObject opens the schema-driven editor and always reloads the explicitly requested object,
  including when its window is already open.
- Delete opens the shared dependency editor, where TACTIC dependency defaults can be reviewed before
  removal.
- When deleting a Task, Notes from the same parent sObject and process appear as a checked
  dependency group; clear that group to keep them.
- Task links from Activity Feed, Object Info, and user profiles accept both native TACTIC search-key
  formats.
- Refreshing Selected scope without an sObject keeps the normal empty state and sends no server
  request.
- Selected scope follows the active Search tab and its selected objects, including multiple
  selection.
- The All Search Type action uses that tab's type even when its result list is empty.
- Hidden task views catch up when shown again; unsaved task edits are kept.
- Search Type task groups show the configured title while retaining the server code as their stable
  identity.
- Task filters, grouping and sorting run on the server before pagination.
- Load More fetches the next matching page; unsaved task edits remain available when a filter
  changes.
- Hover editors are created only when needed.
- Pressing a status or user editor keeps it active while its menu opens, so the pointer can move
  directly into the menu.
- Right-click a table column header for sorting, grouping, visibility, and column configuration.
- A draft Gantt schedule remains under Unscheduled Tasks until it is saved successfully.
- An empty Task Manager keeps its footer and shows a centered creation cue pointing toward +.
- The arrow remains anchored to the Create button while the dock is resized.
- The table is created asynchronously only when the active scope contains tasks; Gantt is created on
  first request and retained for smooth switching.
- The first loaded Task Manager table and quick task batch are laid out before presentation, so task
  rows do not cascade into view at startup.
- User selectors combine task-specific choices with shared profile details, keep group sections and
  search aligned, and preserve the original choice when filtering.
- User choices are prepared when the selector is pressed, so its separate popup window never opens
  with an empty first frame.
- The Task Manager header keeps view switching, overflow, and refresh actions pinned to the right
  edge while secondary actions move into overflow at narrow widths.
- After restart, Task Manager resumes the last scope, filters, collapsed groups, calendar position
  and selected task separately for each project.
- Checked rows and unsaved edits are intentionally cleared.
- Task search remains visible in narrow layouts.
- The compact scope button stays beside Create instead of occupying the search field's flexible
  space; at the minimum width, scope selection remains available from overflow.
