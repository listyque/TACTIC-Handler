---
group: Administration
icon: edit
order: 37
---
# Sidebar Editor

> Sidebar Editor changes project navigation stored in TACTIC. Simple mode covers normal setup;
> Advanced XML edits the selected server element directly. Save deliberately—these changes affect
> users allowed to see the item.

## Header and modes

| Control | What it does |
| --- | --- |
| **Simple** | Shows Item, Access, and Technical pages for the selected sidebar element. |
| **XML** | Shows the selected element's raw XML. Use it only when the server widget needs a value not exposed by Simple mode. |
| **Help** | Opens this article. |
| **Reload sidebar** | Discards the loaded view and reads the server configuration again. It is disabled while work is running. |

Switching modes commits the currently focused Simple text field before replacing the editor. In XML
mode, **Apply XML** validates and applies the text to the selected draft element; it does not save
the whole sidebar to TACTIC until **Save** is pressed.

## Sidebar items

The left tree is the future navigation structure. Select a row to edit it; disclosure arrows expand
sections. The filter button switches between all project views and only the TACTIC Handler branch.

| Add control | Result |
| --- | --- |
| **Add link** | Adds a searchable navigation item. |
| **Add section** | Adds a group that can contain links. |
| **Add separator** | Adds a visible divider; separators remain selectable and movable. |

Above the settings, **Move up**, **Move down**, and **Delete item** act on the selected element. A
delete removes the draft row only until the sidebar is saved.

## Item page

| Setting | What it controls |
| --- | --- |
| **Title** | User-facing sidebar label. Changing it does not change the stable internal name. |
| **Icon** | Opens the searchable icon library. |
| **Visible in navigation** | Hides an item without deleting its configuration. |
| **Search Type** | Project objects opened by this link. A link without one stays dimmed and cannot open a search. |
| **Predefined search** | Saved query used as the starting filter, or no preset for an unfiltered tab. |
| **Default item view** | Initial tree, cards, compact rows, or split-version presentation. |
| **Workspace layout** | Server-saved dock arrangement applied when this link opens. Later returns may restore retained tab state. |
| **Script shelf** | Shared project shelf shown while this sidebar tab is active. |
| **Configure search** | Opens the real search workspace for this Search Type, where presets, Quick Filters, process visibility, sorting, grouping, and result view can be prepared. |

## Access page

**Who can see this item** contains every available login group. Check only groups that should receive
the item. **Manage groups and members** opens Administration; membership changes there are separate
from the sidebar draft. An empty list means no login groups were loaded from the server.

## Technical page

| Setting | Meaning |
| --- | --- |
| **Item type** | Link opens a search, Section groups children, Separator divides the list. |
| **Internal name** | Stable server identifier and owner of quick-filter defaults. Change Title for a visual rename. |
| **Child view** | `SideBarWdg` view containing a section's children. |
| **Icon name** | Raw server icon identifier; the Item page is safer for normal selection. |
| **Widget Type** | TACTIC web widget used by this link. Handler result presentation is configured on Item. |
| **Class Path** | Registered Python class for that TACTIC widget. |
| **View** | Server view rendered by the selected TACTIC widget. |

## Saving and discarding

The footer says whether the draft is current. **Discard** returns all sidebar drafts to the loaded
server state. **Save** commits them to TACTIC and refreshes project navigation. If a control is
disabled, select a compatible element first or wait for the current request to finish.
