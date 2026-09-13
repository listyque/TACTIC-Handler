---
group: Docks
icon: tasks
order: 28
---
# Tasks dock

> Tasks follows the selected sObject and edits its workflow tasks. The same header switches between
> compact cards, list and the full Task Manager without moving the primary controls.

## Scope and views

For a selected sObject, the dock loads configured workflow processes and their tasks. The three fixed
view segments are:

| View | Best for |
| --- | --- |
| Cards | Quick status, assignee, dates and progress changes per process. |
| List | A denser overview of many processes. |
| Full Task Manager | Server filtering, table, Gantt, Calendar, bulk editing and wider task details. |

Switching views keeps the same target and unsaved edits. Table, Gantt and Calendar controls belong to
the full workspace footer.

## Process rows

Each process row can reset or save edits, create a missing task, open related notes and expose edit or
delete actions. When a process has several tasks, select the intended task before editing.

Common editable fields include status, assignee, start and end dates, progress, priority and bid. The
available fields and values come from the project workflow. Status and assignee catalogs load on demand.

## Saving

- **Save** on a row commits that task.
- **Save all** commits every changed row owned by the current target.
- **Discard** restores server values for the chosen row.
- **Discard all** removes every unsaved task edit in the dock.
- Creating a task uses the process defaults; the full Task Editor exposes additional fields before creation.

Unsaved rows stay visibly marked. Selection changes do not silently commit them.

## Notes and work hours

Open Notes to make Task Inspector follow the exact parent, process and selected task. Work-hour actions
use that task identity; a process with no task must be created before time can be logged.

## Dates and loading

Date fields display a localized date and add time only when space permits. Focus the field to edit the
exact stored value. In long lists, scroll first and let the view settle before relying on hover actions.

## Errors and permissions

- Missing processes indicate that the selected object has no configured workflow or no accessible process.
- A save conflict leaves the local edit visible so it can be reviewed or discarded.
- Delete is shown only when the current account and task state permit it.
- An unavailable user, status or field is server configuration data and is never invented by the UI.
