---
group: Workflows
icon: search
order: 9
---
# Search and filters

> A Search tab is an independent query with its own conditions, result view, sorting, grouping,
> loaded pages, and scroll position.

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
| **Tab close button** | Closes a closable tab. |
| **Middle-click a tab** | Quickly closes a closable tab. |
| **All search tabs** | Appears when space runs out and lists every tab; activate or close one from the menu. |
| **Sort items** | Sorts by name A-Z, name Z-A, recently updated, or oldest updated. |
| **Group items** | Uses no grouping, SObject status, pipeline, or an available task status for a process. |
| **Change search results view** | Selects Continuous tree, Cards, Table, Compact rows, Versions on the right, or Versions at the bottom. |
| **Result actions** | In a narrow dock, combines Sort, Group, and View in one menu. |
| **Recently closed search tabs** | Restores a closed tab or clears history. The badge is the number of restorable tabs. |

### Search filters and presets menu

| Item | What it does |
| --- | --- |
| **Advanced Search** | Opens every condition for the current tab. |
| **Filter Processes** | Chooses which process and child branches are shown in the result tree. |
| **Saved search** | Loads the selected server preset into the current tab and executes it immediately. |
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
