---
group: Guide
icon: table
order: 93
---

# Tables

Column headings, plain values and status chips share a centered column axis by default. Explicit display options `justify` or `align` keep their `left`, `center` or `right` alignment. Wrapped labels retain that alignment when the column is resized.

Main and embedded tables share the same square header, context menus, editors,
selection and virtualized rows. A normal click focuses a row; checkboxes or Shift
select records for bulk actions. Double-click opens the object or its cell editor.

Auto Fit distributes the available width across all configured columns. Explicitly
hidden columns remain hidden. When minimum widths cannot fit, use the horizontal
scrollbar. Resize column boundaries or use their keyboard controls to adjust widths.

Dashboard table height includes its title, search, rows and footer. Page containers
add no implicit side gutters. Quiet separators, subtle alternating surfaces and
passive status badges remain readable in both themes; status edits keep their
existing input and server permissions.

Width-only changes do not add Undo or activity-history entries. Structural column
changes still use the native configuration journal. See [Page and item layouts](item_layouts.en.md).

Workflow hover previews use compact cards with editable dates, status and assignee. The preview arranges smaller cards in one to three columns with equal gaps and padding. Additional rows scroll vertically inside the bounded preview. Task Manager remains available in its separate footer. The count button remains a direct Task Manager action and does not trigger expansion; the same action is available in the preview. Compact table row height stays unchanged.

Only the cell under the pointer expands; selecting other rows does not open their previews. Bulk task editing still uses the selected rows.

The active expanded related table is raised with a shadow; the remaining parent table is dimmed. Click the dimmed area or Close to collapse it. If search is disabled for that view, no empty toolbar is reserved: remaining actions use the footer. Enabled search uses the main suggestion field within the current relation.

### Pipeline progress nodes

A progress node is an aggregate, with a ring and a completed-object/total-object count. It has no task status, assignee or dates. Click the ring or heading to open its related tasks in Task Inspector. An unconfigured or unavailable relation shows N/A; an accessible empty scope shows 0/0.

Counts follow the configured related Search Type, process, pipeline and local/global scope. For objects with pipelines, completion comes from their workflow status messages, as in legacy TACTIC. For objects without pipelines, Complete object/task statuses are used. Multiple completed tasks on one object count once. Ordinary task cards retain their inline editors, with aligned quiet rows and a single process accent.

The primary search toolbar keeps round buttons for Refresh, Script shelf, Tags, Quick filters, Help and Workspace panels. Local service toolbar buttons remain square.
