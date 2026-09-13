# Tasks, Notes, Messages, and notifications contract

This contract describes current QML ownership. Obsolete visual-only and QWidget
migration comparisons were removed.

## Tasks ownership

`TasksController` is the QML-facing facade. `TaskWorkspaceStore` owns source task
objects, parent indexes, flat records, paging, and request generation. Native
tasks and parent SObjects remain in Python.

Task creation uses the existing insert API with the correct `parent_key`.
Editing uses native `set_value()` and `commit(triggers=True)`. Deletion routes
through the universal SObject deletion workflow so dependencies, including
process notes, are discovered and confirmed together.

All server operations and reloads run through the server pool. QML receives
stable task/parent identity, primitive fields, choices, selection, loading,
dirty, conflict, and error roles.

## Quick task editor

- The process model contains every non-special pipeline process, including one
  that does not yet have a task.
- Workflow nodes such as action, condition, dependency, and progress are not
  shown as ordinary task rows.
- A missing task may stage status and assignee before explicit Save. Save creates
  the task for the selected parent.
- Multiple tasks on one process remain distinct by task code.
- Preferred task selection is the remembered task code, then a task assigned to
  the current login, then the first available task.
- Status choices come from the process task pipeline.
- Assignee choices honor the process login group and fall back to loaded logins
  only when no group restriction exists.
- Cards and compact rows are views of the same process model.
- Hover editors are deferred while scrolling and must not shift label geometry
  when instantiated.

## Detailed Tasks Workspace

Supported scopes include current object, explicit object, selected objects,
user, team, Search Type, and project.

- Current-object scope reuses loaded workspace tasks.
- Selected objects use the existing batched multiple-task query.
- User/team/project paging uses one task query per page.
- Parent data is batched by parent Search Type.
- Local search, grouping, sorting, quick filters, table projection, calendar,
  and Gantt projection do not query the server again.
- Group identity uses the stable server value, such as the process code. When
  different pipelines provide different labels or colors for that same value,
  the workspace chooses one deterministic, most-common presentation and keeps
  every matching row under one header and one collapse state.
- Scope and page requests use generation identity; stale results are discarded.
- Duplicate task codes replace the existing source record rather than creating
  another row.
- The active scope changes only through explicit mode/action commands. Ordinary
  SObject selection updates mini editors but does not refresh a non-selected
  task scope.

The project/user query currently has a bounded page size. Representative
large-project timings and optional schema columns remain live acceptance items.

## Task table interaction

- Active row selection and checkbox selection are separate.
- Ctrl toggles a checked row; Shift checks a visible range.
- Inline status/user editing stages a Python draft. Save commits changed task
  objects; Discard restores loaded values.
- Popup editors remain open while the pointer crosses from the row into the
  popup, including fast pointer movement.
- Column context menus are anchored to the invoked column and expose applicable
  sort, group, ungroup, and hide actions.
- Task, note, and message buttons use shared count-action controls and semantic
  badges.
- Delete one or checked tasks uses the common dependency-aware deletion window.

## Task identity and schema

Detailed rows are identified by task code/search key, not process. Two tasks
with the same parent and process remain two records in every grouping mode.

Confirmed commonly consumed columns include `code`, `search_type`,
`search_code`, `project_code`, `process`, `context`, `status`, `assigned`,
`description`, `bid_start_date`, `bid_end_date`, `pipeline_code`, and
`timestamp`.

Progress is enabled only when the active server schema provides `progress` or
`completion`. Optional priority, dependency, attachment, and version fields must
be checked against the active schema instead of hardcoded.

## Task selection and inspector

The Task Inspector follows the exact task selected in Task Manager. Selecting an
SObject may establish a preferred task, but the inspector's collapsed/expanded
state is user-owned and is not forced open.

An empty process remains editable: Task Inspector projects the same workflow-default
task row used by Quick Tasks, and Save creates it through that shared draft owner.
The small plus beside the current-task Edit action opens the complete schema-driven
creation editor without replacing the inline path.

Opening Tasks from an SObject or process switches Task Manager to the explicit
selected-object mode and selects that target. Note counts and message badges
load with the task data; they do not require a manual Refresh.

## Notes and status timeline

`CommunicationController` owns the selected target/process/task timeline. The
first task in a process uses the parent SObject/process note thread. When the
same process has additional contextual tasks, each additional task uses its own
`sthpw/task` parent note thread. Status history is always filtered to the exact
selected task code.

- Notes and status events load asynchronously and are ordered as a chat
  timeline anchored at the bottom.
- One message remains at the lower edge; new messages append at the bottom and
  move older content upward.
- Switching among tasks of the same process reuses the loaded branch set and
  changes both the visible notes and status events to the selected task.
- Task Manager badges use the same branch ownership: the primary task receives
  the parent/process count, while contextual tasks receive only their own
  task-parent counts. Incremental note events update only the owning branch.
- Enter sends; Ctrl+Enter inserts a newline.
- Plain text remains the server storage contract. Display escapes text and
  safely makes HTTP/HTTPS links clickable.
- Editing a note is unavailable unless a real server mutation contract exists.
- Deletion uses the universal dependency-aware SObject deletion workflow.
- Full errors go to Debug Log; concise errors remain inline and retryable.

## Communication drafts and attachments

Draft text and staged attachments are keyed by conversation/note target identity.

- Switching target never discards a non-empty draft silently.
- Text and attachments never leak into another conversation.
- Drafts survive closing Messages and application restart through the project
  configuration API.
- File dialog, clipboard, screenshot, and drag/drop feed the same staging model.
- Existing attachment snapshots display previews and download/open through
  Repository Sync.
- New local files use the shared attachment check-in/Commit Queue workflow;
  network and filesystem work never runs in the GUI thread.
- Opening Messages from Task Manager resolves the task/parent/process context
  directly, so attachments load even when no result item was selected first.

## Messages semantics

Where no independent addressable server conversation API exists, Messages is an
alternate presentation of the selected SObject/process communication history.
It must not fabricate user-to-user conversation identity, unread server state,
or a second note store.

Consecutive Messages from the same login within five minutes are presented as
one visual group. The first bubble owns the author label; the last bubble owns
the single external avatar and directional tail. Its tail-facing bottom corner
is square so the tail and bubble read as one continuous surface. Loading earlier history and
appending a live message recompute both group boundaries. This presentation rule
belongs only to Messages; Notes and Activity Feed retain their existing rows.

## Notifications

The notification stack is bounded and uses shared MD3 surfaces inside an
application-owned, frameless, always-on-top window at the bottom-right of the
available screen. It remains independent from the main window's visibility and
never delegates Messages or Activity Feed events to Windows notification
balloons. Message cards show the sender avatar, sender name, conversation title,
and excerpt; Activity Feed cards show the event preview or actor avatar, event
type, and summary.

- Supports info, warning, error, progress, and completion.
- Progress updates one stable card instead of producing a stream.
- Duplicate active events are coalesced; recently dismissed duplicates are
  rate-limited.
- Informational completion may auto-close; warnings and errors remain longer and
  can be dismissed.
- Timers have QObject ownership and stop on removal and shutdown.
- Full traceback remains in the originating controller's Debug Log.
- Modal confirmations remain separate native dialogs.

## Verification

Automated coverage includes no-task process rows, multiple task identity,
process-specific statuses, scope query budgets, paging deduplication, stale
results, Shift selection, draft save/discard, task deletion scope, note/status
selection, bottom-anchored timeline, draft isolation/persistence, attachment
DnD, Enter/Ctrl+Enter, popup lifetime, notifications, Python syntax, and QML
loading.

Manual acceptance covers workflow permissions, login groups, triggers,
representative large task sets, live note/attachment permissions, configured
repositories, and minimum-width/scroll performance.
