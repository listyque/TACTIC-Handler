---
group: Docks
icon: search
order: 26
---
# Search dock

> Search is the main project browser. Each tab keeps its own Search Type, filters, result layout,
> expanded rows, selection, paging mode and scroll position.

## What the dock follows

The active sidebar item chooses the Search Type or saved search. The selected result publishes the
current sObject, process and snapshot to the other docks. Returning to an already loaded tab reveals
its retained result surface instead of requesting and rebuilding every row.

## Top bar

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
- **Search filters and presets** edits the active tab's filters and saved presets.
- **All search tabs** finds or activates an open tab when the rail is long.
- Hovering a tab in the left rail expands it over the workspace without changing the dock layout.
- Closing a tab does not first activate it; the closed-tab history can restore it.
- A tab-specific script shelf overrides the common shelf only for that tab.

## Result presentation

The footer and overflow menu provide **Sort items**, **Group items**, **Change search results view**
and **Result actions**. Tree, list and card presentations use the same query and selection; changing
the view never edits project data.

Expanded hierarchy rows load related objects only when needed. Ctrl and Shift extend selection.
The context menu always applies to the item under the pointer; middle-click opens a new Search tab
only for sObject result items.

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
