---
group: Configuration
icon: tasks
order: 37
---
# Tasks configuration

> Tasks configuration defines the initial Task workspace presentation. Saved project or workspace
> state takes priority when it already exists.

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

In **Configuration → Tasks**, choose each Task Browser column's visibility, width (40–480 pixels),
and order. Object always remains visible. Use **Apply** or **Save** to keep changes; **Reset**
discards the current draft. **Configure columns** in the task table opens this page directly.

Dock and window geometry is restored separately for each workspace. Task scope, filters, collapsed
groups, calendar position, and selected task resume per project. Checked tasks and unsaved edits are
never restored.
