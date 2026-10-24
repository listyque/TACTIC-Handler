# Tactic Frame: Search and results

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

## Owners

| Responsibility | Handler | Stream |
| --- | --- | --- |
| Executed query, tabs, paging, selected records | Existing application/search-session controllers | Existing App/workspace state |
| Preset catalog, revisions, mutations, unknown replies | FilterEditorController | SearchLibrary and existing search-configuration API |
| Advanced-search composition | AdvancedSearchView and features/search native bricks | SearchLibrary dock and ConditionCards/ConditionValue |
| Tags, quick filters and suggestions | Existing application models and worker generations | Existing TagCloud/SearchQuickFilters/SearchLibrary read owners |
| Process tree | Existing schema/pipeline builder and ProcessFilterEditorController | ACL-checked visibility catalog and ProcessVisibility |
| Result metadata, child loading, selection and operations | Existing workspace result model/controllers | Existing ResultPresentation and object-operation owners |
| Task-status catalog and ordering | Existing pipeline/task organization | Root result-items response; no second metadata request owner |

## Behavior

- **Advanced Search** opens as a workspace dock. Applying keeps it open. Its
  first editable WHERE row remains available; the trailing plus adds another
  condition. Up/down moves preserve values and normalize the first row. Reset
  returns to an editable first row.
- Field suggestions debounce typing, retain field focus and accept Up/Down,
  Enter and Escape. Hiding the editor stops its timer and invalidates late reads.
  Null/empty relations disable the value editor. Server column names remain data.
- Task facets compile into one related-task expression, so process, assignee and
  status must match the same task. Generated cards identify Quick Filter ownership;
  detaching preserves the executable condition and removes the chip ownership.
  The existing read-only expression policy remains active in the search editor.
- Preset creation, update, rename, duplication, deletion and links retain the
  existing server revision checks. A lost mutation reply blocks another write
  until a fresh catalog reconciles it. Switching context invalidates old replies;
  drafts from two tabs of the same Search Type do not overwrite one another.
- Process visibility is local to the search tab. Cancel discards its draft;
  Save/Save and close change presentation without executing the object query.
  Repeated schema edges share the same logical setting. Ctrl/Shift and the
  togglers keep the native selection rules.
- Menus retain native view names and stable preset IDs. Sort by column uses
  actual columns. Task-status grouping uses configured status priority, followed
  by unknown statuses, No status and No task. Project labels are not translated.
- A single tile click selects; double click or its explicit Open action enters.
  Expansion, card navigation, versions, selection and scroll keep their existing
  owners. Only visible browser collection entries and the focused entry remain
  mounted; measurements from removed records are released. Home/End and vertical
  arrows move focus through virtualized entries.
- Handler retains native repository synchronization; Stream retains its Commit
  Queue entry and phone navigation. These are explicit capabilities. Standalone
  saved-search editing from Administration/Sidebar Editor remains a bounded
  dialog; it does not change the workspace dock into a modal window.

## Verification

Run the focused drivers under `tools/frame_search/` from the Stream development
checkout, with the actual Handler checkout supplied using `--handler-root`
where supported. The complete shared gate is:

```powershell
python tools/frame_foundation/check_platform.py --handler-root "../../TH"
```

Adjust that path relative to the working directory; in the two-repository
workspace, Stream commands run from `TS/tactic_stream` and Handler is `../../TH`.
Use isolated data, actual input, fresh source fingerprints and independent-package
checks. Generated reports belong in the ignored tool `output/` directories.
Historical release counts and captures are local archive material, not current
acceptance. Offscreen checks do not establish physical touch/IME, compositor,
DCC or deployment readiness; exercise those when the feature requires them.
