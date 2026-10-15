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
Opening an object or process through its Tasks badge clears filters from the previous scope;
a process badge then applies only that process filter. An active filter colors the filter button
green (or the overflow button at narrow widths). If filters hide every task, the empty state
offers to clear them instead of suggesting task creation.

Selecting a task row updates Task Inspector for that exact task without changing the Inspector's
saved expanded or collapsed state. When one process has multiple tasks, its badge menu shows each
task's context, assignee, and status; the process row opens the task list from already loaded data.
Switching Search tabs that show the same object and process keeps the Inspector's loaded task and
notes; selecting a different context refreshes them.

A workflow **progress** process remains in the Task Inspector process menu, marked with the same
completion icon and approved/total count as the object's completion badge. Selecting it shows the
tasks of objects linked through the project schema and switches Task Manager's selected-object scope
to those objects; it does not create or edit a task on the parent.
Progress processes are not snapshot check-in destinations. If the workflow names a Search Type that
has no schema relationship to the selected object, the Inspector reports the missing relationship
instead of guessing which objects belong to it.

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
- Task filters and sorting run on the server before pagination. Loaded pages are merged into one
  group per stable key, so Load More does not repeat a group header.
- Quick-filter choices show each process, status, or other value once, with the task count for the
  current scope.
- Load More fetches the next matching page; unsaved task edits remain available when a filter
  changes.
- Hover editors are created only when needed. Task-row highlighting appears immediately, and status and assignee content stays in place when its editor appears.
- An empty status uses the same localized “No status” label in the table and hover editor; configured status names remain unchanged.
- Pressing a status or user editor keeps it active while its menu opens, so the pointer can move
  directly into the menu.
- Right-click a table column header to sort, group, or hide it. Any user can use
  **Configure columns** to open personal task-column settings in Configuration → Tasks.
- The table header's right-hand column button chooses visible task columns; the same action remains
  in the overflow menu when the table header is unavailable, such as in Gantt view.
- A draft Gantt schedule remains under Unscheduled Tasks until it is saved successfully.
- In Gantt, drag the protruding left or right grip to change a task's dates; drag the striped grip inside the bar to change completion.
- An empty Task Manager keeps its footer and shows a centered creation cue pointing toward +.
- The arrow remains anchored to the Create button while the dock is resized.
- The table is created asynchronously only when the active scope contains tasks; Gantt is created on
  first request and retained for smooth switching.
- The loading indicator remains until the first Task Manager table and its visible rows are ready;
  quick task rows are also laid out before presentation, so neither view cascades into place.
- User selectors combine task-specific choices with shared profile details, keep group sections and
  search aligned, and preserve the original choice when filtering.
- User choices are prepared when the selector is pressed, so its separate popup window never opens
  with an empty first frame.
- The Task Manager header keeps view switching, overflow, and refresh actions pinned to the right
  edge while secondary actions move into overflow at narrow widths.
- After restart, Task Manager resumes the last scope, filters, collapsed groups, calendar position
  and selected task separately for each project.
- Clearing task filters also leaves a specific user's scope opened from a profile badge and returns
  to Selected. Manually selectable scopes, including My Tasks, stay selected.
- Checked rows and unsaved edits are intentionally cleared.
- Task search remains visible in narrow layouts.
- The compact scope button stays beside Create instead of occupying the search field's flexible
  space; at the minimum width, scope selection remains available from overflow.


Gantt keeps its scroll viewport stable when a dock has fractional dimensions or the display uses 125% or 150% scale. An empty list with a fitting time range needs no canvas scrollbars; an overflowing list or range still scrolls normally. Resizing must not make the bars appear and disappear repeatedly.

## Project tasks without object selection

In full Task Manager, + also works when no object is selected. It creates a task owned only by the current project; no asset, shot or other work object is needed. The task uses the standard task status workflow and initially assigns the current user, so it appears in My tasks. Edit and save it using the existing task controls, then open Task Inspector as usual. In a Perforce-like file project, select it under Link tasks to changelist in the submit dialog. With an object selected, + keeps creating a task for that object.

