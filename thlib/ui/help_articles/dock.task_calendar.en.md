---
group: Docks
icon: calendar-month
order: 32
---
# Task Calendar dock

> Task Calendar summarizes scheduled tasks by day and turns a selected date into a server-side task
> filter for the active task scope.

## Calendar navigation

Use previous and next month to move through time, **Today** to return to the current month, and the
clear action to remove the selected day. A day cell shows matching loaded tasks and a compact
`+ more` indicator when they exceed the visible limit.

Selecting a day applies its date boundary to Task Manager on the server. It is not merely a visual
highlight. Clearing the date restores the previous non-date task scope.

## What is counted

Calendar and Gantt operate on matching task data available to the current workspace. If the task
browser has more server pages, load them when the view needs the complete matching set. The selected
day message states which date is currently filtering tasks.

## Typical workflow

1. Open the required task scope or Search selection.
2. Navigate to the required month.
3. Select a day to filter matching deadlines or scheduled work.
4. Open a task in Tasks or Task Inspector for editing.
5. Clear the date to return to the wider task result.

## States and errors

- An empty day means no accessible task matches the active scope and date.
- Tasks without usable start or end dates cannot be positioned reliably in the calendar.
- Server filtering keeps the selected day while loading; an error does not silently switch dates.
- Date labels follow the interface locale, while stored task dates remain project data.

## Shared scheduling

Gantt and the separate Task Calendar dock use the same Frame layout in Handler
and Stream. Use the pencil on a task to edit its schedule without dragging.
Apply to draft stages dates and progress together; Save task changes performs
the existing server write. Undo/Redo affect pending schedule edits and preserve
other task drafts. Escape cancels an unfinished pointer gesture.

Calendar month navigation and Agenda keep the current task owner. Select a day
to filter Task Browser; clear it to return. Calendar does not replace Gantt.
Dependency connectors show actual links between loaded, visible scheduled tasks;
they do not infer missing tasks or cascade schedule changes automatically.
Project milestones retain their linked-task plan and existing save/conflict
controls. Native milestone SObject storage and browser revision review remain
separate client capabilities.
