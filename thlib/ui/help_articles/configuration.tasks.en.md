---
group: Configuration
icon: tasks
order: 37
---
# Tasks configuration

> Tasks configuration defines the initial Task workspace presentation and the default Task Browser
> columns. Saved project or workspace state takes priority when it already exists.

## Task workspace defaults

| Setting | Choices and effect |
| --- | --- |
| **Initial task surface** | Opens **Quick Tasks** or the detailed **Task Browser** first. |
| **Quick Tasks presentation** | Uses editable process **Cards** or a **Compact list**. |
| **Initial view** | Opens **Table** or **Gantt** when Task Browser has no saved local view. |
| **Initial sorting** | Orders by Deadline, Recently changed, Process, Assignee, Status, Parent object, Priority, Milestone, or Supervisor before the user applies another sort. |
| **Initial grouping** | Groups by Process, Status, Assignee, Parent Object, Project, or Search Type, or uses **No Groups**. |
| **Task Inspector expanded** | Opens Task Inspector expanded when no saved dock state exists. |

## Task table columns

Each row controls one column. The checkbox shows or hides it; required columns such as **Object**
cannot be hidden. The numeric field sets width from 40 to 480 device-independent pixels. The two
arrow buttons move the column left or right in display order.

Dock and window geometry is restored separately for each workspace. Task scope, filters, collapsed
groups, calendar position, and selected task resume per project. Checked tasks and unsaved edits are
never restored.
