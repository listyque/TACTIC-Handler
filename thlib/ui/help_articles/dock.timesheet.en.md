---
group: Docks
icon: calendar-month
order: 33
---
# Timesheet dock

> Timesheet records work hours against real tasks and reviews approval state for a selected week and
> accessible team members.

## Week and scope

Previous and next controls move by week; the date control opens a specific week. The user selector
limits visible entries to accessible team members. Refresh reloads the selected week and scope from
the server.

## Summary

The summary separates **Logged**, **Approved**, **Pending** and **Overtime**. These totals are derived
from work-hour records in the current scope. Built-in labels are localized; project user, process and
task names are displayed exactly as configured on the server.

## Entries and approval

- Select entries individually or as a group.
- **Approve** and **Pending** apply the corresponding state to selected records when permitted.
- **Clear selection** removes the selection without changing records.
- Edit updates the date, regular or overtime duration and comment.
- Delete removes the selected work-hour record after confirmation.

Bulk actions affect only selected visible identities, not every result implied by the current filter.

## Log time

Time can be logged only for an existing selected task. Confirm its parent object and process before
entering the work date, duration, overtime flag and comment. The entry becomes project data immediately
after a successful save.

## Typical workflow

1. Select the task in Tasks or Task Manager.
2. Open the intended week and user scope.
3. Add or edit the work-hour entry.
4. Review Pending totals and select entries for approval.
5. Open Work Reports for grouped analysis.

## States and permissions

- **No selected task** disables logging; select or create a task first.
- Approval controls depend on server permissions and may be unavailable for your own or other users' entries.
- A failed write keeps the editor values for retry.
- Empty totals mean no accessible work-hour records in the selected week, not necessarily no project work.
