---
reference: Handler
group: Administration
icon: edit
order: 37
---
# Sidebar Editor

Tree labels and their secondary text keep a clear gap from icons, including nested entries.

> Sidebar Editor changes project navigation stored in TACTIC. Simple mode covers normal setup;
> Advanced XML edits the selected server element directly. Save deliberately—these changes affect
> users allowed to see the item.

The project editor changes the shared definition layer; login-specific definitions are preserved. Root views follow the same source selection as runtime navigation.

Open it from the **Sidebar Editor** section of Administration. The project selector in
Administration controls which project's sidebar is edited; the main search tab does not.

## Header and modes

| Control | What it does |
| --- | --- |
| **TH / TACTIC** | Chooses the independent TACTIC Handler sidebar or the native web TACTIC `project_view`. |
| **Simple** | Shows Item, Access, and Technical pages for the selected sidebar element. |
| **XML** | Shows the selected element's raw XML. Use it only when the server widget needs a value not exposed by Simple mode. |
| **Help** | Opens this article in the shared Help window. |
| **Reload sidebar** | Discards the loaded view and reads the server configuration again. It is disabled while work is running. |

Switching modes commits the currently focused Simple text field before replacing the editor. In XML
mode, **Apply XML** validates and applies the text to the selected draft element; it does not save
the whole sidebar to TACTIC until **Save** is pressed.

## Sidebar items

The left tree is the future navigation structure. Select a row to edit it; disclosure arrows expand
sections. The TH sidebar is stored in the standalone `tactic_handler` view and is no longer treated
as a subsection of the native TACTIC `project_view`.

For any project without a configured sidebar, navigation lists the project's loaded Search Types.
This automatic catalog is not written into sidebar XML. A saved Handler sidebar, including an
explicitly empty one, takes precedence; access-filtered links are not restored by the catalog.
Unresolved default web-sidebar links without element definitions do not suppress this catalog.

While editing TH, the group selector can show **All groups** or preview the sidebar exactly for one
login group. The preview filters by draft access; navigation-hidden items stay dimmed in the editor
so they can be selected and restored. A new item
created while a group is selected is granted to that group; switch back to **All groups** to inspect
or edit entries hidden from the selected group. This selector changes only the editor preview: item
access rules remain the single saved source of group visibility.

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
| **Visible in navigation** | Hides an item in navigation without deleting its configuration; the editor keeps it dimmed. |
| **Search Type** | Project objects opened by this link. A link without one stays dimmed and cannot open a search. |
| **Predefined search** | Saved query used as the starting filter, or no preset for an unfiltered tab. |
| **Default item view** | Initial tree, cards, compact rows, or split-version presentation. |
| **Workspace layout** | Server-saved dock arrangement applied when this link opens. Later returns may restore retained tab state. |
| **Script shelf** | Shared project shelf shown while this sidebar tab is active. |
| **Configure search** | Opens the real search workspace for this Search Type. Its preset list includes only searches saved in TACTIC Handler; Refresh reloads that same list. Quick Filters, process visibility, sorting, grouping, and result view can also be prepared here. |

## Access page

**Who can see this item** contains every available login group. Check only groups that should receive
the item. These same draft values drive the TH group preview immediately. **Manage groups and
members** switches to the Groups section; membership changes there are separate from the sidebar draft. An
empty list means no login groups were loaded from the server.

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

An assigned Saved Search initializes the item's first search tab; it is not
opened again as an extra tab. Reopening the sidebar item retains its active tab,
filters and drafts. Other saved searches remain separate even if their titles
match. Use **+** to create an additional personal search.

The footer says whether the draft is current. **Discard** returns all sidebar drafts to the loaded
server state. **Save** commits them to TACTIC and refreshes project navigation. If a control is
disabled, select a compatible element first or wait for the current request to finish.

Navigation badge icons follow the theme text color, including on light Search Type accents. This does not change the configured type color.
