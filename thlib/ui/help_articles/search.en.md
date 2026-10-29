---
group: Workflows
icon: search
order: 9
---
# Search and filters

> A Search tab is an independent query with its own conditions, result view, sorting, grouping,
> loaded pages, and scroll position.

On a fresh launch, the workspace contains only Search. Open the main menu and choose a Search Type
to begin. Closing the last Search Type leaves the workspace empty instead of reopening the previous
type. Other panels can be opened from the workspace panel menu when needed.

## How a query is assembled

A query can be built in layers. Every layer eventually appears as a condition in **Advanced
Search**:

```text
Text from the top search field
    AND selected tags
    AND Quick Filters
    AND manual field conditions
    AND **Expression conditions
```

These are not five independent searches. They form one query for the current tab. You can first
find objects by a word, narrow the result with Quick Filters, and finally add an exact condition in
Advanced Search.

> Field names, statuses, processes, and values come from the TACTIC server. The examples below show
> query structure; use the fields and values from your project.

## Top row

| Control | What it does |
| --- | --- |
| **Refresh current results** | Repeats the current tab's query and fetches current server data. |
| **Search field** | Searches name or title, keywords, and description when those fields exist on the current Search Type. |
| **Clear button in Search** | Clears the entered text. Press `Enter` to execute the cleared query. |
| **Script shelf** | Shows or hides the script shelf. See its separate Help topic for details. |
| **Tags** | Opens the tag catalog. Its badge is the number of selected tags. |
| **Quick filters** | Opens compact filters for the current tab. Its badge is the number of selected values. |
| **Help** | Opens this topic. |
| **Workspace panels** | Opens the panel menu for the current workspace. |

In a narrow dock, **Refresh** stays visible to the left of Search; Quick filters stay beside
the field. **More search actions** also provides Refresh, Script shelf, Tags, Help, and Workspace panels.

### Text search and suggestions

1. Start typing; suggestions appear after a short delay.
2. Use `Up` and `Down` to move through suggestions.
3. Press `Enter` on a suggestion for an exact name or title search.
4. Press `Enter` without a selected suggestion for a broad field search.
5. Middle-click a suggestion to open it in a new Search tab.
6. Press `Esc` to close suggestions without clearing the text.

A broad search for `chair` becomes an initial group similar to:

```text
WHERE name        Contains  chair
OR    keywords    Contains  chair
OR    description Contains  chair
```

If the Search Type uses `title` instead of `name`, Search uses `title`. Missing fields are omitted.

Repeating a top-field search replaces only this leading text group. Conditions appended after it
remain. Clearing the field likewise removes only the text part of the query.

## Search tabs and result actions

| Button or action | What it does |
| --- | --- |
| **Add new search tab** | Creates an independent tab and focuses Search. |
| **Search filters and presets** | Opens Advanced Search, Filter Processes, and Saved Search actions. |
| **Click a tab** | Activates that tab. |
| **Drag a tab** | Changes tab order. |
| **Tab close button** | Closes a closable tab. In a narrow dock it stays on the active tab; activate another tab first or use All search tabs to close it. |
| **Middle-click a tab** | Quickly closes a closable tab. |
| **All search tabs** | Appears when space runs out and lists every tab; activate or close one from the menu. |
| **Sort items** | Sorts by name A-Z, name Z-A, recently updated, or oldest updated. |
| **Group items** | Uses no grouping, SObject status, pipeline, or an available task status for a process. |
| **Change search results view** | Selects Continuous tree, Cards, Table, Compact rows, Versions on the right, or Versions at the bottom. |
| **Result actions** | In a narrow dock, opens Search filters and presets, Sort, Group, and View. |
| **Recently closed search tabs** | Appears when there are restorable tabs; restores one or clears history. The badge shows their count. |

In a narrow dock, tab titles use compact widths and long names are available in **All search tabs**.

### Table views

In Table mode, **Table views** lists the server-side table layouts available for the current
Search Type. Choosing one affects only the current Search tab. **Save current as new view** copies
the current columns, order, widths, and visibility into a named TACTIC table view; the new view is
then selected for that tab. Each tab remembers its own choice.

### Search filters and presets menu

| Item | What it does |
| --- | --- |
| **Advanced Search** | Opens every condition for the current tab. |
| **Filter Processes** | Chooses which process and child branches are shown in the result tree. |
| **Saved search** | Loads a search saved in TACTIC Handler into the current tab and executes it immediately. Native TACTIC web searches are not listed. |
| **Refresh saved searches** | Fetches the preset list again from the TACTIC server. |

In **Filter Processes**, tree checkboxes control visibility, **Save** applies changes, **Save and
close** applies and closes the window, and **Cancel** closes without saving.

## Tags

**Tags** shows a catalog for the complete current Search Type. The catalog is cached per project
and Search Type and is not narrowed by the active query.

| Button or control | What it does |
| --- | --- |
| **Tag chip** | Adds a tag; click again to remove it. Selected tags are joined with `OR`, while the tag group is appended to preceding conditions with `AND`. |
| **Clear tags** | Removes every selected tag. |
| **Reload tags** | Bypasses the cache and reloads the catalog from the server. |
| **Search tags** | Filters chips inside the popup only; it does not change Search results. |
| **Clear search** | Clears the local tag-catalog search. |

For example, `vehicle` and `red` append a group similar to:

```text
AND keywords Contains vehicle
OR  keywords Contains red
```

## Quick Filters

Quick Filters are a compact interface over ordinary Advanced Search conditions. Direct Search Type
fields become `Is` or `In` conditions. Task filters become one TEL condition so assignee, process,
and status must belong to the same task.

| Button or control | What it does |
| --- | --- |
| **Filter value** | Selects a value; click again to remove it. Multiple values of one direct field use `In`. |
| **All** | Clears the selection in that group. |
| **My Tasks** | Restricts results to objects with a task assigned to the current TACTIC user. |
| **Select users / Users** | Opens assignee selection for related task filters. |
| **Apply the shared default to this tab** | Discards this tab's personal setup and restores the published shared setup. It appears only after personalization. |
| **Clear quick filters** | Clears all selected Quick Filters in the current tab. |
| **Edit** | Opens the Quick Filter layout and default-selection editor. |

### Quick Filter editor

| Button or control | What it does |
| --- | --- |
| **Close on a selected value** | Removes one value from the edited default. |
| **Copy selection from current tab** | Copies the current tab's selection into the edited default. |
| **Clear selected filters** | Clears the entire edited default. |
| **Show hidden filters** | Shows groups that this user is allowed to restore. |
| **Group checkbox** | Shows or hides a whole group. |
| **Move up / Move down** | Reorders groups. |
| **Value chip** | Adds a value to the default; click again to remove it. |
| **Save** | Stores layout and selection locally for this Search tab. |
| **Save as defaults on server** | Available to supervisors; publishes this setup to users of the sidebar tab. |
| **Cancel** | Closes without saving current edits. |

Groups hidden by a supervisor are unavailable to regular users. Direct-field discovery includes
text and numeric fields with at most 64 distinct non-empty values. A field with one value remains
available. Reloading the catalog bypasses the cache without discarding unsaved editor changes.

## Advanced Search

Open **Search filters and presets → Advanced Search**. The query is displayed as condition cards.

### Top-panel buttons

| Button | What it does |
| --- | --- |
| **Chevron beside Search Filters** | Collapses or expands condition cards. |
| **Apply filters** | Compiles active cards, returns to the start of results, and executes the query. |
| **Add filter** | Adds a condition card. |
| **Reset filters** | Removes all conditions and leaves one empty starting card. |

### Condition card controls

| Control | What it does |
| --- | --- |
| **Left checkbox** | Temporarily enables or disables a manual condition without deleting it. |
| **WHERE** | Marks the first active condition and cannot be toggled. |
| **AND / OR** | Connects this card to preceding conditions. Click to switch between `AND` and `OR`. |
| **Field** | Selects a column of the current Search Type or the special `**Expression` field. |
| **Relation** | Selects a comparison supported by that field type. |
| **Value** | Enters a filter value. Ordinary fields offer server suggestions; `Enter` applies the complete query. |
| **Add on the first card** | Adds another condition. |
| **Remove on a card** | Removes that condition. |
| **Edit as custom filter** | Detaches a Quick Filter-generated card and turns it into an ordinary editable card. |
| **Remove quick filter** | Removes the generated card and its corresponding Quick Filter selection. |
| **Search tab name** | Renames only the current tab; it does not alter the query. |

A card without a field, a disabled card, or a card without a value is not sent to the server.
Relations such as **Is empty** are the exception because they require no value.

### Relations by field type

| Type | Main relations |
| --- | --- |
| Text | Is, Is not, Contains, Does not contain, Starts with, Ends with, In, Not in, Is empty, Is not empty, Is distinct. |
| Number and currency | Equal, Greater than, Less than, In, Not in, Is empty, Is not empty, Is distinct. |
| Date and time | Newer than, Older than, On, Is empty, Is not empty. |
| Login | Is, Is not, Contains, Does not contain, Starts with, Ends with, Is empty, Is not empty. |
| Timecode | Before, After, Equal, Is empty. |
| `**Expression` | Have, Do not have, Match (slow), Do not match (slow). |

## Layered Search: practical patterns

### Text plus exact fields

Enter `chair` in the top field, then add conditions in Advanced Search:

```text
WHERE name        Contains chair
OR    keywords    Contains chair
OR    description Contains chair
AND   status      Is       Ready
AND   priority    Greater than 2
```

The text remains broad while the final layers narrow structured data.

### Several accepted values

Use **In** for one field:

```text
WHERE status In Ready|In Progress|Review
```

The vertical bar separates list values. The same query can be built with several `status Is ...`
cards connected by `OR`.

### Text, a Quick Filter, and a related task

1. Search for `dragon` in the top field.
2. Select the needed direct object status in Quick Filters.
3. Enable **My Tasks** and the needed process there.
4. Open Advanced Search; text conditions and generated Quick Filters appear in one list.
5. If needed, click **Edit as custom filter** to alter a generated condition manually.

UI conditions form a flat chain: each card's `AND` or `OR` chip connects it to the preceding part.
There are no visual parentheses or nested groups. For complex parenthesized logic, use one
`**Expression` condition or split variants into separate tabs and Saved Search presets.

## `**Expression` and TEL

`**Expression` accepts a server-side TACTIC Expression Language (TEL) expression. It is neither
Python nor SQL.

### Have and Do not have

**Have** evaluates an expression that must return related SObjects, then keeps current Search Type
objects related to them. **Do not have** excludes those objects.

Objects with a task assigned to the current user:

```text
@SOBJECT(sthpw/task['assigned', '$LOGIN'])
```

Objects with a task in a specified process and status:

```text
@SOBJECT(sthpw/task['process', 'animation']['status', 'In Progress'])
```

Select `**Expression → Have`, paste the expression, then click **Apply filters**. `$LOGIN` is
substituted by the TACTIC server. The second example uses illustrative values; replace them with
real project process and status values.

### Match (slow) and Do not match (slow)

**Match (slow)** evaluates the expression separately for every object of the current Search Type
and keeps an object only when the result is exactly `True`. **Do not match (slow)** reverses it.

Examples:

```text
@GET(.priority) == 3
```

```text
@GET(.status) == 'Approved'
```

The dot in `.priority` and `.status` refers to the current object being tested. This mode is truly
slow: the server first loads every object of the Search Type and evaluates the expression for each.
Prefer **Have / Do not have** for relationships to tasks, snapshots, and other SObjects.

An invalid TEL expression produces a server query error. Correct the expression; the UI does not
guess or rewrite it.

## Saved Searches

A Saved Search is stored on the TACTIC server and carries the complete card set, including `AND`,
`OR`, and `**Expression`.
Only searches saved by TACTIC Handler appear here; native TACTIC web searches remain separate.

| Button or action | What it does |
| --- | --- |
| **Select a saved search** | Loads its cards into the editor. In Advanced Search, click **Apply filters** after selecting it. |
| **Update selected preset** | Overwrites the selected preset with current cards. |
| **Save as new preset** | Requests a name and creates a server preset. |
| **Saved search actions** | Opens the operations below. |
| **Rename preset** | Changes the selected preset's name. |
| **Duplicate preset** | Creates a copy under a new name. |
| **Copy saved search link** | Copies a link that opens this server search. |
| **Delete preset** | Deletes the preset from the server after confirmation. |
| **Refresh saved searches** | Fetches the list again from the server. |
| **Save / Cancel in the name dialog** | Confirms or cancels creation, rename, or duplication. |

Selecting a preset from the compact menu above results applies it immediately. Selecting it in the
Advanced Search preset bar only stages its cards, allowing review and edits before **Apply
filters**.

## Results footer

| Button or control | What it does |
| --- | --- |
| **Result range** | Shows the current range and total; a narrow dock reduces it to the total count. |
| **Previous page** | Goes to the previous page in Pages mode. |
| **Page numbers** | Open a specific page. Compact mode shows `current / total` instead. |
| **Next page** | Goes to the next page in Pages mode. |
| **Items per page** | Selects 20, 25, 50, or 100 items in expanded Pages mode. |
| **Pages / Continuous** | Switches between explicit pagination and loading when nearing the end. |
| **Sync current Search Type** | Opens Repository Sync for the current Search Type. |
| **New item** | Opens SObject creation for the current Search Type. |

In Continuous mode, dragging the scrollbar only moves through already loaded objects. Another page
is requested near the end. Loading preserves the current position and expanded items and stops at
the end of results.

## What Search remembers

Each tab independently keeps:

- query cards, Quick Filters, and selected tags;
- tab name, sorting, grouping, and result view;
- loading mode, page size, and loaded pages;
- dock and splitter layout;
- expanded items, selection, and scroll position.

Closing or hiding the window does not discard the last position. Switching Search tabs preserves
loaded panel content and editor state.

## Server search counters

Note and task-branch counters use native grouped searches instead of loading every note. Server privacy rules and parent/process counts stay authoritative. Custom Note classes keep their original row evaluation and getters. The original TACTIC uses its native Select; TACTIC Stream uses validated physical-column grouped counts without granting raw SQL access.

With TACTIC Stream, identical scripts of up to 65,536 characters can reuse immutable compiled code across requests. Each worker retains at most 32 entries; larger scripts keep their request-local cache. Each execution still reads the current saved/file source, checks access and creates fresh globals and inputs. Search result data and permission decisions are not cached by this optimization. Restart Handler and Stream after installing the paired update.

## Refreshing selected details

Handler refresh receives the current result page and the selected object’s tasks, notes, status history and snapshot files in one search response. If the selection is absent from the page, details follow the first result. Other objects keep lightweight previews until selected or expanded. **Refresh snapshots** still explicitly reads fresh server data; permission checks and cache invalidation remain active. Stream’s browser uses its native search and inspector commands rather than Handler’s Python procedure.

## Navigation input

Opening navigation keeps its scroll position and focuses the panel. Arrow keys enter the available rows. Use Up/Down, Home/End to move, Right/Left to expand/collapse a section or enter/leave it, and Enter/Space to open a view. Hidden/unavailable items and separators are skipped. Escape, the close button or the shaded workspace closes the panel and returns focus to the opener. Mouse auto-close is armed only after entering the panel; moving more than 120 pixels beyond its right edge then closes it. Touch does not trigger hover dismissal.

## Tab keyboard controls

On a search tab, Left/Right and Home/End select another tab. Delete closes a closable tab; Ctrl+Shift+Left/Right changes its position. Focus follows the selected surviving tab after closing or reordering. On the vertical section rail, Up/Down and Home/End move focus; Enter/Space activates the focused section. Delete closes a closable section and Ctrl+Shift+Up/Down reorders it. Existing tab history, context menus, loaded results and saved workspace state keep their existing behavior.

## Vertical section rail

On desktop, hover a section to reveal its name and Close button. Leaving the rail collapses the reveal after 350 ms; touch uses no hover. A first tap selects the section once. Drag an expanded row vertically to reorder it; Escape cancels the drag. Closing a row does not also select it.

Right click, Shift+F10 on a focused section, or a 500 ms touch hold opens Move section up/down and Close tab. Movement is disabled at the corresponding list boundary. Names and custom section colors remain project data. These operations use the same existing workspace state and saved layout. Stream retains its compact phone navigation instead of forcing the desktop rail onto a narrow screen.

## Workspace lifetime

Dock positions, splits, stacks and the active panel are restored from the existing saved workspace. Closing a dock hides it; reopen it through **Workspace panels** without replacing its loaded editor. Search tabs retain their own layout, selection and editor context. Escape cancels an unfinished move or resize.

Stream shows one panel at a time on a phone. Returning to desktop preserves its dock arrangement; returning to phone restores the chosen phone panel and staged edits, even when that dock is hidden on desktop. Handler keeps its native desktop layout.

Signing out or an expired session suspends background reads. A late reply from the previous login cannot restore its identity, permissions or workspace after another user signs in. A delayed sign-out reply cannot close the newer session. Unsaved edits still use the existing save/discard guards; signing out is not a way to persist a draft.

## Search dock and result controls

Open **Advanced Search** from the filter menu beside the Search tabs. It is a dock: move, stack, float or hide it through the ordinary panel controls. **Apply filters** updates the current tab and leaves the dock open. The first WHERE card stays editable; its plus adds a condition. Use the arrows to change condition order, and disable a card to compare results without deleting it. Value suggestions keep typing focus; Up/Down chooses a suggestion, Enter accepts it, and Escape dismisses the list.

Each search tab keeps its own draft. Closing and reopening the dock retains that draft during the session. Preset Save/Update/Rename/Duplicate/Delete use the existing server catalog. If the reply to a save is lost, refresh the catalog and check the saved entry before trying again; the editor blocks a duplicate write while its result is unknown.

**Group items → Task status by process** groups objects by the chosen process's task status, including separate No status and No task groups. Process/status names remain server data. **Sort by column** uses the actual Search Type columns. Page number, page size and Pages/Continuous are available from the result footer.

A single card click selects; double click or its Open action enters its contents. Long lists and card grids render only visible entries, preserving loaded data, expansion and selection. On a focused result, Home/End and Up/Down move through the collection, including offscreen entries. Phone navigation retains its explicit Back/Open controls.


## Initial view for legacy projects

Imported `project_view` sidebar searches open as tables when no explicit result mode is configured, matching the legacy ViewPanel default. A direct search for a configured type uses the same initial mode. Explicit sidebar modes and previously saved tab modes remain authoritative; switch the current tab through the result-view menu. Handler-specific sidebar definitions retain their client defaults.

In tables, a plain row click highlights the active record without checking it or opening the selected-record bar. Use Shift+click for a range or the row checkboxes to select individual records. The compact Deselect button at the left of the bar shows the checked count and removes all checks.

Table headers meet their rows without a dark spacer. Scrollbar space is reserved only when content overflows.

Result and task table headers show a thin vertical column-boundary grip, highlighted on hover.

Custom sidebar pages open directly in the workspace, including on a fresh launch. Their content replaces Search and its drag grip. A section label revealed by the mouse collapses after the pointer leaves; keyboard navigation keeps the focused section available.

Custom-card task and note icons show a count badge. Zero hides the badge; counts above 99 display 99+, while the tooltip keeps the exact count.

Object cards shade the preview behind their title and description, including
light images. Text uses the theme foreground instead of muted caption color.
Selected cards keep their selection tint; light themes use a light overlay with
dark text. The image, preview actions and card layout remain available.
