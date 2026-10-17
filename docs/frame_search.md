# Tactic Frame B06: Search and card results

The search header, condition cards and their suggestions, preset bar/name form,
quick-filter and tag headers, filter editor parts, process visibility, result
menus, paging and result-card geometry now use the independent Frame descriptions
under `features/search`. The reusable variable-height collection geometry lives
under `controls/lists/collection.mjs`. Native Qt keeps ListView/GridView;
the browser uses the house `VirtualCollection` adapter. There is no WebEngine,
runtime checkout dependency or replacement query engine.

Frame forwards an optional host-local event source separately from the action:
an HTMLElement in Vue or the native item in QML. Child scenes and virtual lists
preserve it for popup anchoring; it is never persisted as search state.

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

The local comparison is `tools/frame_search/output/index.html`. Its JSON records
source hashes and identifies the reference archive: Handler HEAD before B06,
which already includes previous Frame batches. It is not the pre-Frame archive.
The matrix covers three themes, light/dark, EN/RU and 360/800 logical-pixel
component widths. Fixed-width card captures use a desktop viewport; actual phone
input is checked separately by the CG and transport journeys.

Advanced Search, the footer, popup headers and process actions compare real Qt/browser
geometry, typography and colors. Card/editor screenshots are visual evidence,
not a claim that all raster pixels match between text renderers. The browser
driver exercises 100, 1,000 and 10,000 entries, bounded delegate counts, scrolling
and offscreen keyboard focus. Its elapsed time includes driver work and is not
a frame-rate benchmark.

Reproduce from the development checkout, with isolated test data:

```powershell
.venv/Scripts/python.exe tools/format_tactic_frame.py --check --handler-root D:/code/th_codex
.venv/Scripts/python.exe tools/sync_tactic_frame.py --check --handler-root D:/code/th_codex
.venv/Scripts/python.exe tools/frame_foundation/check_platform.py --handler-root D:/code/th_codex
.venv/Scripts/python.exe tools/frame_search/capture.py
node frontend/tests/frame_search.mjs
.venv/Scripts/python.exe tools/frame_search/report.py
```

`test_search_configuration`, `test_cg_template` and the transport search,
library, visibility, tag and workspace journeys check backend effects, security,
state and unknown writes separately from screenshots. The CG delivery journey
also exercises real relationships, versions, grouping, six views and touch.
Native search, popup, editor, paging and card tests exercise the actual controls.

The B06 release matrix contains 96 archived and 192 current QML captures with
192 Vue pairs. The editor and shared popup/footer controls check geometry,
typography and colors. Object tiles additionally check fallback/gradient colors
and persistent task/note badges. The native search suite has 121 tests. Real
server journeys cover managed-filter detachment, lost save replies, independent
tab drafts, stacked dock reactivation, cache reload failures and stale replies,
continuous paging and retained selection/scroll. The CG journey uses 32 objects,
13 tasks, 47 notes and 45 relationships, with versions, all six views and touch.

Browser continuous paging observes the visible table's own viewport. Retained
tables restore their offset when revealed and do not persist a hidden DOM reset
over the tab's saved scroll position. The mobile tag cloud uses the visible
command as its popup anchor and returns focus to the phone action menu.
The collection observes its scrolling viewport as well as its delegates, so
changing a dock or keyboard height updates the mounted range without a window resize.
Snapshot filenames keep their natural width independently of the shortened
label, so a name that fits is restored instead of remaining over-elided.

Two existing retained-UI failures reproduce against archived QML: the message
fixture omits the required `hasWebPreview` role, and the floating-window proxy
test expects an obsolete row count. They are not search regressions. Existing
whole-repository lint/structure debt remains recorded by the platform baseline.

Table View/cell migration is B07. Nested legacy saved-search groups that cannot
be represented by the existing flat condition editor remain explicitly rejected;
they are not silently flattened or counted as supported.
