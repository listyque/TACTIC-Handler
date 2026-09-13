# Filter Editor contract

## Format and server semantics

- A working row has the TACTIC Search View form
  `(enabled, (column, relation, value), op)`. The first row uses `begin`; later
  rows use `and` or `or`.
- The search payload remains a flat interleaved list of tuples and operators.
  The server format has no parentheses or nested groups:
  `pack_tactic_search_view` stores only level `0`.
- Operators come from `tactic_classes.get_match_list_by_type`; QML does not
  invent its own operators.
- A preset is stored in `config/widget_config` with
  `category=search_filter`, the current `search_type`,
  `view=link_search:<preset>:<tab>`, and the XML/JSON format produced by
  `pack_tactic_search_view`.
- On reopen, QML parses `search_ops` and preserves row order and mixed AND/OR.
  This corrects OR loss in `unpack_tactic_search_view` without changing
  the server format.

## Implemented scenarios

| Area | QML behavior |
|---|---|
| Conditions and value types | Add, remove, enabled state, column-aware operator, value editing, and numeric/boolean validation |
| AND/OR and groups | Mixed flat ordering is preserved; nested groups are intentionally absent, matching the server format |
| Empty filter | One empty default row is valid and produces an empty search payload |
| Errors | Missing column, unknown operator, an empty value in a complex filter, and an invalid number block Apply and Save |
| Presets | Asynchronous load, create, update, title rename, duplicate, and delete through the existing server pool |
| Reopen | An XML/JSON preset restores enabled state, row order, and `search_ops` |
| Advanced Search | Apply replaces the active tab model and executes exactly one existing asynchronous search |
| Search options | The tab title is edited in the draft and applied with the filter |
| Process filter | Child Search Types, pipeline processes, and built-ins; the project/tab ignore dictionary is compatible with `process_ignore_dict` |

## Integration and state

- The search tab is the only source of search state: its name is the search
  name and its filter payload contains all applied layers.
- Every UI action that changes the displayed server result set must add, change,
  or remove visible Advanced Search rows and then call the shared
  `apply_search_filters`. Hidden local filtering of already loaded SObjects is
  not a search.
- Search suggestions, quick filters, the tag cloud, and future search controls
  must use one TACTIC Search View condition format. After applying them, the
  user must see the corresponding conditions in Advanced Search.
- Multiple conditions explicitly preserve AND/OR and order. If the flat format
  cannot express the required semantics, use a supported TACTIC
  expression rather than QML-only logic.
- System searches such as My Tasks may build `_expression`, but the expression
  remains a normal visible filter layer in the active tab.
- The controller owns only QML-safe draft records. TACTIC projects and Search
  Types remain in Python and are never passed to delegates.
- Preset network operations run through `env_inst.server_pool`; the GUI thread
  receives only lists of dictionaries.
- A preset response is matched against `(project, search_type, tab)`. A late
  response after context change is discarded, and Apply requires reopening the
  editor.
- A preset deleted on the server disappears after refresh. Deleting a record
  that is already absent completes as a safe list refresh.
- Cancel restores the condition and title snapshot, does not change Advanced
  Search, and does not write the process filter.
- Apply stores the native `process_ignore_dict`, passes it to the
  workspace model, resets cache and pagination, and starts the common search.
- Selecting a preset only loads it into the draft; applying it to a search still
  requires Apply.

## Verification results

| Scenario | Status |
|---|---|
| Empty filter or one condition | Implemented |
| Multiple AND or multiple OR conditions | Implemented; order is preserved |
| Mixed AND/OR at level 0 | Implemented |
| Nested groups | Intentionally absent from the TACTIC Search View contract |
| Invalid value or missing column | Python validation |
| Deleted preset | Safe refresh without restoring a synthetic record |
| Project/Search Type/tab change | Stale-result guard and Apply disabled for the old draft |

Live TACTIC verification requires insert/update/delete permission for
`config/widget_config`, the selected project's pipeline display, and reading
the same `process_ignore_dict` through the QML interface.

## Tag cloud

- Selected tags become visible `<tag column> LIKE %value%` rows in Advanced
  Search; multiple tags are joined with OR.
- Changing the tag selection preserves other tab rows, updates the shared
  TACTIC Search View payload, and performs the normal server search.
- Tag-frequency queries exclude rows created by the tag cloud itself, allowing
  the user to add a neighboring tag without losing the original cloud.

## Quick Filters

- Edit opens the native modal editor for every user. Supervisors see one
  **Save as defaults on server** action; regular users see **Save**, which only
  commits the current tab's layout and selection. The server visibility policy
  is applied before building a regular user's model and again at local save.
  Server-hidden entries cannot be revealed by the user's Show hidden toggle.
- Catalog completion refreshes an open editor without discarding pending edits;
  the closed editor does not build or refresh groups.
- The catalog is discovered from categorical columns in
  `SearchType.get_columns_info()` and distinct values across the whole Search
  Type. It is not an XML list and is not narrowed to the loaded result page.
- Text and numeric storage types are eligible: one to 64 distinct non-empty
  values form a group. Identity, descriptive/technical payload, path, date and
  high-cardinality columns are excluded; schema-provided choices remain
  available even when no current row uses one. Zero and false are real values.
- Direct facets become visible `=` or `in` Advanced Search rows. Process,
  status, and assignee facets become one verified related-task TEL row so all
  selected task values must match the same task.
- Catalog reads use the shared reference cache scoped by project and Search
  Type and validate the facet-column definitions. Reload bypasses that cache,
  and reference invalidation drops the hot
  projection.
- Applying or removing a generated row restores or clears the matching chips.
  Detaching a generated row keeps the server condition but makes it an ordinary
  custom Advanced Search rule.
