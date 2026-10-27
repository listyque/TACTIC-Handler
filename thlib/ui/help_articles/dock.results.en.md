---
group: Docks
icon: search
order: 26
---
# Search dock

In an expanded relationship or process branch, use the small magnifier to the left of its title to search its immediate children. The popup has a clear button; Enter/Escape closes it. Other branches and records remain unchanged.

> Search is the main project browser. Each tab keeps its own Search Type, filters, result layout,
> expanded rows, selection, paging mode and scroll position.

## What the dock follows

The active sidebar item chooses the Search Type or saved search. The selected result publishes the
current sObject, process and snapshot to the other docks. Returning to an already loaded tab reveals
its retained result surface instead of requesting and rebuilding every row.

## Top bar

The dock move grip stays at the upper-left corner when Search and Snapshots are
stacked, so changing the active tab never moves the drag target.
Table date columns use the shared localized date display. Hover a date for its full date and time, without database microseconds.
The column settings button stays at the right of the header; scrollbars occupy separate gutters outside the table cells.
Table headers use the same compact uppercase style as Task Manager. As the table narrows, optional columns disappear in their configured hide order; order 1 hides first and order 0 keeps a column visible. Use **Auto Fit columns** to stretch the remaining columns across the available width, or open column settings to change widths and hide order.
Right-click a table header to sort ascending or descending, group by that column, or remove the current grouping. The grouped column is accented and marked in its header; group headers can be expanded and collapsed.
Collapsing a group preserves staged task changes. If a row is reused for another object, its open task editor closes rather than switching its edit target.
Table previews fill a circular frame, cropping the edges without stretching the image.

| Control | Purpose |
| --- | --- |
| Search field | Searches the current tab and provides server-backed suggestions. |
| Refresh current results | Repeats the current query without replacing its filters. |
| Script shelf | Shows the personal or shared script shelf for the current tab. |
| Tags | Adds or clears tag filters. Typing filters the loaded tag catalog. |
| Quick filters | Enables saved one-click conditions for this Search Type. |
| Workspace panels | Shows, hides or restores project docks. |

On narrow widths the essential search, refresh, Tags and Quick Filters controls remain available;
secondary actions move to the overflow menu.

## Search tabs

- **Add new search tab** opens another independent result context.
- **Search filters and presets** (funnel icon) edits the active tab's filters and saved presets.
- **All search tabs** finds or activates an open tab when the rail is long.
- Hovering a tab in the left rail expands it over the workspace without changing the dock layout.
- Closing a tab does not first activate it; the closed-tab history can restore it.
- A tab-specific script shelf overrides the common shelf only for that tab.

## Result presentation

The footer and overflow menu provide **Sort items**, **Group items**, **Change search results view**
and **Result actions**. In the compact menu, sorting, grouping and view choice open submenus;
refresh remains beside the search field. Tree, list and card presentations use the same query and
selection; changing the view never edits project data. An sObject subtitle shows its description,
the pipeline's
user-facing name and its configured category; the pipeline code is only a fallback.
Category names come from the field's configured values/labels (including expressions).
Their lookup runs in the search worker and is cached; refreshing results reloads it.
An unknown category retains its code.
Double-click tags or a multiline description to edit them in a wide panel.
Add tags with Enter or Add, remove them individually, and apply the draft with Save.
Cancel or Escape discards the draft; typing alone does not save changes.
Inline table editors use the full choice list of the underlying field, including
columns mapped to another field through the server's action configuration.
Loading field choices retries temporary server failures up to three attempts;
a persistent failure remains visible as an error.
The results table uses the same flat row styling and rounded header as Task Manager, with horizontal separators and a default row height of 58. Circular previews fit inside each row; widening their column does not enlarge the row by default.
Note entries use the process title and color configured by the active pipeline; the number at the right is the note count for that process.
In table view, **Fit to Preview** grows rows with the Preview column. The Compact, Comfortable and Large
presets set an explicit row height instead. Task Workflow keeps status and assignee controls separate;
cards keep a stable width. When the column cannot show every card, hovering over the Task Workflow cell opens
the same editable cards above the table. The centered task indicator opens Task Manager for the
object. Large rows also show each task's localized planned start and end dates;
click that date row to edit both values. Changing a task's status, assignee, or dates creates a local
draft for the selected rows.
The Save and Reset buttons appear above the table with an unsaved-task count.
Task calendars load only when you click the dates, rather than for every row when opening the table.
Save applies all staged task changes; Reset discards them. Failed saves retain
unconfirmed changes. Changing selection does not submit or discard the drafts.
Saving an object field updates only affected table rows, preserving scroll position and selection.
Hovering an overflowing task cell expands its cards over the same table row, extending sideways within the window. The inline cards are hidden while this overlay is open, so tasks are not shown twice. For multiple selected rows, hovering over a selected workflow cell expands the tasks of all visible selected rows. Other cells do not trigger expansion.
In card view, click a card to select it, use its action buttons directly, or click empty grid space to clear selection.
Object cards place the title and description below the top controls. Task and note buttons have their own footer, including when their counts are zero.
Card and preview corners remain rounded during scrolling.
Related-object cards always show Create and, for instance relations, Link actions.
Nonempty relations also offer an Open button; double-clicking the card opens the same contents.

Expanded hierarchy rows load related objects only when needed. Ctrl and Shift extend selection.
The context menu always applies to the item under the pointer; middle-click opens a new Search tab
only for sObject result items.
Delete appears only for an object created by the signed-in user less than one hour ago. For a
multi-selection, every selected object must qualify; the deletion dialog checks again before deleting.

## Paging and synchronization

| Control | Behavior |
| --- | --- |
| Previous / Next page | Moves through server pages in paged mode. |
| Page number | Jumps to a known page. |
| Page size | Changes the number requested per page. |
| Pages / Continuous | Chooses explicit pages or append-on-scroll loading. |
| Sync current Search Type | Refreshes server metadata and this Search Type's result state. |

Continuous loading appends the next page near the end. It does not imply that every server result is
already loaded; counts and bulk actions distinguish loaded rows from the complete query.

## Typical workflow

1. Open a Search Type or saved search from the sidebar.
2. Add text, tags, quick filters or Advanced Search rules.
3. Choose grouping and presentation without changing the query.
4. Select one or several results and use their context or overflow actions.
5. Inspect snapshots, tasks, description and notes in the following docks.

## Empty, loading and error states

- A loading overlay means the current generation is still pending; switching tabs does not apply a
  stale response to the newly selected tab.
- An empty result means the combined active filters returned no rows, not that the Search Type is missing.
- A server error preserves the tab and its filters so Refresh can retry the same query.
- If the layout or tab state is unusable, **Reset layout** restores dock geometry; it does not delete saved searches.

## Missing versionless

When a commit has no versionless snapshot, Search displays its absence without a file Online/Offline status. File availability belongs to an existing snapshot: an existing snapshot with unavailable files still displays File Offline.
