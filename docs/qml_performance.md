# QML rendering and lifecycle performance

QML performance is treated as a contract of the presentation layer, not as a
late visual cleanup. The hot paths are recyclable search delegates, task rows,
message timeline entries, retained dock content, and report pages with nested
models.

## Idle table cells

`features/tasks/TaskCellDisplay.qml` draws the geometry from shared
`tasks/cells.ui.mjs` with native text, rectangles and lazy avatar/indicator ports.
Idle values do not instantiate a recursive Frame renderer; `TaskTableEditorCell`
continues to own lazy editors, popup lifetime, mouse/touch input and pooling.
Keep labels, font metrics, colors and avatar geometry tied to the shared scene.

Empty `FrameBranch` scenes keep their renderer unloaded, including when a retained
branch later receives children. Search tables request `all_cells` only when a
column actually has a summary, and transfer that map once per recomputation.
`tests.profile_result_table` measures cold creation, working set, scrolling,
refresh and grouped expansion on isolated data. Object budgets and actual editor
input tests are regressions; timings remain diagnostics for the measured host.

## Native resize and overdraw

The desktop `Main.qml` disables `ApplicationWindow`'s automatic top safe-area
padding: Windows already places the content below its native title bar, and a
changing inset moved the entire top of the workspace while leaving its bottom
edge fixed during resize. The offline `tests.profile_main_resize` probe records
the real main window's top padding, top-bar origin, and frame intervals across
narrow and wide sizes; `tests.test_main_resize_qml` guards the layout contract.

The dock host no longer paints an extra window-sized background over the
window's own background. The empty-task arrow Canvas is limited to its drawing
bounds instead of allocating a surface as large as its dock. Other effects
found in the QML tree need a populated GPU capture before further changes.
Offscreen software frame timings are diagnostic only; inspect a live scene with
Qt's `QSG_VISUALIZE=overdraw` before claiming a device-specific FPS gain.

## Approved complexity review hot paths

`tests.profile_ui_responsiveness.review_hot_paths_benchmark()` reports seven-run
medians for deterministic offline fixtures. On 2026-09-07 (Python 3.14, Windows):

| Fixture | Median |
| --- | ---: |
| Script with an error on line 11 and 3,000 trailing lines, cold parse | 0.349 ms |
| Same script revision, cached parse | 0.0007 ms |
| Gantt, 2,000 intersecting tasks assigned to one user | 81.50 ms |
| Gantt, 2,000 tasks assigned to different users | 81.74 ms |

The earlier review measured approximately 543 ms versus 63 ms for the two Gantt
workloads. The new scan eliminates pairwise overlap comparisons; absolute timings
vary with machine load. The AST regression changed from 3,002 parse attempts to
at most three. One bounded eight-entry cache is shared by outline, imports and
completion. These are CPU measurements, not live-server latency or desktop FPS.

Tasks apply filtering/counting/ordering on the server and return a bounded page,
with scope-wide facets rather than the entire task inventory. The query currently
uses six grouped facets and six preset aggregates in one RPC; server SQL latency
still needs measurement on the deployment database. Hidden Gantt and Calendar
projections wait until their dock/view is presented.

SObject Info publishes detailed task/note/child/file/activity models only for the
active section; summary metadata remains available. Native file existence and
preview-path inspection run in a cancellable worker on first opening Snapshots.
Selection generations discard stale results. Preview downloads still use the
existing repository queue and native `File` preparation methods.

Shared `SearchField`, `ImagePicker`/`ImageFileDialog` and `SObjectFieldGrid` remove
duplicate UI/input/layout paths. Image selection state stays in the feature
controller. `UserFilter` uses Qt's native `SortFilterProxyModel`/`FunctionFilter`
(introduced in Qt 6.10, supported by the pinned Qt 6.11 toolchain); section headers
follow the filtered model. `RecordListModel.lookup` lazily indexes a role and
invalidates the index on model mutations. This avoids per-row directory scans.

Notes and Messages use one composer draft owner per composer and the existing
serial `ConfigWriteQueue`; context changes and shutdown flush pending drafts.
Commit Queue naming rows exist only while their details are expanded. Runtime
checks cover actual QML creation, input and narrow/wide geometry, not just source
assertions. See [the implementation checklist](ui_performance_rules.md).

## Earlier delegate baseline

The Workspace result delegate is instantiated through the real
`WorkspaceResultItem.qml` component with a real `Theme` and QML engine. A local
offscreen profile of 50 ordinary sObject rows showed the following representative
change during the rendering audit:

| Metric | Before | After |
| --- | ---: | ---: |
| QObjects per idle sObject row | 190 | 150 |
| QQuickItems per idle sObject row | 86 | 67 |
| 50-row warm construction burst | 125 ms | 78 ms |

Wall-clock values depend on the machine and Qt shader cache, so they are
diagnostic rather than a release threshold. Object counts are deterministic for
the supported Qt runtime and are enforced by
`tests/contracts/qml_render_budgets.json`.

## Rendering rules enforced by the implementation

- An idle ripple owns only its lightweight host and Loader. Its rectangle,
  animations, mask, shader source, and offscreen layer exist only during the
  click animation and are released when it finishes.
- Workspace drag/drop presentation is created only while a compatible drag is
  over the row. A normal row does not own the overlay Repeater or its delegates.
- Entity-specific controls are not merely hidden. Task/note actions are absent
  from file, snapshot, relation, and group rows.
- The same rule applies to the card view: task/note controls are instantiated
  only for sObject and process cards. File, snapshot, and relation cards do not
  retain those button, badge, tooltip, or ripple trees.
- Shared surfaces composite hover and pressed feedback into their existing
  rectangle instead of drawing a second translucent rectangle over every row or
  icon button.
- Preview fallback icons, initials, and busy indicators are mutually exclusive
  lazy states. An absent or pending image does not allocate an OpacityMask, and
  a ready image does not retain the fallback presentation trees.
- A grouped message whose avatar or tail is not shown does not decode the avatar,
  allocate an opacity mask, or create a Canvas texture.
- Shadows and other graphical effects inside repeated UI are created only for
  the active hover/elevated state. Persistent window/dialog shadows are allowed
  because their instance count is bounded.
- The TACTIC table resolves its columns before native cell payloads. Ordinary
  values therefore appear from the result model immediately; native cells load
  asynchronously and later pages request only missing search keys. QML crosses
  into Python once per visible row, and off-screen column controls stay unloaded.
- Closed action menus retain only their popup shell. Rows, icons, ripples,
  badges, and hover targets are created for the opened presentation and released
  again on close.

## Hidden presentation lifecycle

Retaining a dock instance is useful for immediate tab switching, but retention
does not grant permission to perform work.

- Views with server-backed initialization use a `presentationActive` gate and a
  one-shot `ensureLoaded()` path. A retained background dock cannot issue its
  first request, and showing the same retained view again does not repeat it.
- Dock and window presentation is owned by the composition layer. Individual
  retained QML pages must not independently mark activity, debug-log, snapshot,
  note, or task controllers visible; competing visibility writers can restart
  hidden model publication after the host has already suspended it.
- The sObject Info report creates only its current page. A page is retained after
  first use for immediate switching within the same object. When the selected
  sObject identity changes, hidden pages are released, so their Repeaters cannot
  rebuild against the new models while invisible.
- Search result and card previews release their image source when pooled, not
  merely when a retained tab is hidden. Returning to a warm tab must not decode
  its thumbnails again.
- Search row and card hover-animation arming uses a delegate-owned, one-shot
  timer, cancelled on pooling and destroyed with the delegate. Deferred work
  must not retain a callback into a deleted QML context. Runtime regressions in
  `tests.test_workspace_result_item` destroy both delegate types before their
  initial/rearmed callback and verify card cancellation and reuse.
- Controller-owned operations that must continue in the background, such as an
  explicit repository transfer or check-in, remain controller-owned and are not
  cancelled merely because their view is hidden.

## Input and operation diagnostics

The application menu's **UI responsiveness** window uses `UiPerformanceMonitor`.
Recording is paused by default and starts only after the user explicitly
selects **Resume measurements** in that window.
It observes mouse, keyboard, touch and wheel input at the native QQuickWindow
boundary. Filters are attached to individual windows, not every application
event, and there are no probes or configuration reads inside delegates. Text entered
by the user is never recorded. The last 250 samples live in memory and are only
published to the diagnostic list while its window is visible.

Input samples measure event-loop handling and the first frame synchronized after
the input in the **same window**. A frame from the diagnostics window cannot
complete a main-window measurement, and a frame already in flight cannot count
as input feedback. Named controller operations additionally measure a frame
synchronized after their completion when they belong to a live input dispatch.
Background model publications report controller work only, not a frame from
whichever unrelated window happens to have focus. Search navigation explicitly
owns its source-window frame span. Worker/network time is included only when
that operation explicitly spans loading. A missing frame is reported as such,
never as successful readiness. The 50 ms feedback target is diagnostic, not an
unverified guarantee on arbitrary machines.

Search switches publish their immediate feedback before applying the retained
workspace. Phase details separate tab rows, result surfaces, search chrome,
quick-filter publication, schema and selection restoration. `feedbackWaitMs`
reports the deliberate yield before navigation separately from `pythonMs`
(the sum of capture, synchronization and projection phases).

Warm navigation is presentation-only at both Search ownership levels. An outer
sidebar/Search Type section captures its dock workspace on leave and shutdown,
then restores it synchronously on return. Its assigned layout preset seeds only
the first opening. An inner result tab separately retains view, sort, group,
split, expansion, selection, and scroll state. Returning to either retained
owner must not repeat first-show initialization or issue a data or preset request;
explicit Refresh and declared configuration invalidation own reloads.

Search-session and opened-section persistence snapshots are prepared by their
runtime owner, then written by the dedicated configuration queue. JSON
serialization, flush, atomic replacement, and Windows replacement retries
therefore never block the Qt presentation thread during a tab switch. Pending
writes to the same document are coalesced to its newest immutable snapshot, and
shutdown drains the queue before the application configuration owner is
released.

The Search quick-filter and tag popups retain their bounded viewport controls
and current catalog's lightweight row geometry. They neither read the catalog
nor create/update chips while hidden; reopening updates the retained projection
from the controller. Already retained result lists keep their live scroll
coordinates rather than forceLayout/restore on every switch.

Task selection updates only selection/check roles, without rebuilding sorting,
groups, Gantt and calendar. Notes preserve positions for the last 24 object/process
contexts. Messages retain 12 recent conversation models and QML timelines, plus
the active loading timeline until its history can enter that bounded cache;
new live messages regroup only the last pair. Keyed notes, messages, activity and
notification models insert at the real position instead of rebinding every row
after a prepend. Explicit refresh and cache invalidation still own freshness.

Task group collapse is an identity-preserving row removal/insertion, never a
model reset. Changing sort or group order rebuilds only the loaded list
projection; Gantt is refreshed immediately only while presented and otherwise
marked dirty until it is opened. Discrete wheel input across shared list,
search-card and message surfaces uses the short direct-manipulation motion token
rather than the longer view-fade duration.

The four primary floating workspaces (tasks, Messages, activity, notifications)
remain instantiated after first use. Other closed editors keep their bounded
release lifecycle. Retained, hidden consumers must still suspend work.

Run `py -3.14 -m tests.profile_ui_responsiveness` for the offline real-frame
asset/episode-control and scroll benchmark, the 300-task selection/rebuild
comparison, and actual Task Browser collapse/regroup frames.
`tests.test_ui_responsiveness` covers identity, selection, bounded diagnostics
and window-frame correlation. `tests.test_retained_ui` exercises actual QML
input, closed filter publication, retained chat delegates and note viewports. Local fixture
timings do not replace the application's measurements with actual project data.

One offline software-renderer run at a 1100 x 1440 viewport (100 records per
retained search model, five measured switches per surface after warm-up) gave:

| Fixture | Median dispatch | Median rendered frame |
| --- | ---: | ---: |
| Assets, no extra item controls | 2.8 ms | 8.4 ms |
| Episodes, six persistent item controls | 2.4 ms | 7.7 ms |

The 300-task controller fixture measured 16.5 ms for a full projection rebuild
and 0.4 ms for selection-only publication. This comparison excludes QML and
server time. The hidden-filter regression additionally verifies zero catalog
reads after a closed popup's notify signal, and real reads after opening it.
These are reproducible diagnostics, not machine-independent latency assertions.

After replacing group resets with keyed reconciliation, one software-renderer
run of the 300-row Task Browser measured a 10.3 ms median collapse frame and a
30.9 ms median regroup frame. Search-list scrolling measured 5.5–5.9 ms median
frames in the same fixture; its user-visible settling time is controlled
separately by the shared short wheel-motion token.

The table fixture (100 rows, 12 mixed columns, 1100 x 720 software renderer)
reduced the initial visual tree from 4573 to 2097 QQuickItems. Twelve one-row
scroll frames measured 5.52 ms median and 11.27 ms maximum. The narrow real-QML
regression caps the initial tree and proves that off-screen controls stay lazy.

## Verification procedure

### Search table: task calendars and batch projection

`TacticTaskCards` creates its date editor on activation and releases it when
closed. Closed rows must not instantiate two DateFields (and their calendar
grids) each. The click-to-edit regression checks absence before activation,
successful date staging, and release after closing. Status, assignee and date
editing continue through the existing controller draft/save path.

`ColumnsEditorController._map_rows` indexes the current batch's sObjects once
by native search key. Task enrichment receives the matching object directly;
it does not scan the entire result list for every row. Cells without task
records do not resolve workflow choices. The index is local to publication,
not another persistent cache requiring invalidation.

Run `python -m tests.profile_result_table` for the isolated offline benchmark.
On Windows/Python 3.14 with Qt's software renderer, 500 result rows, 12 columns,
five tasks per row and a 1600 x 900 viewport produced these before/after results:

| Measurement | Before | After |
| --- | ---: | ---: |
| First presented table, median of three creations | 394 ms | 153 ms |
| Worst one-row scroll frame across 24 steps and three runs | 89 ms | 39 ms |
| First creation's native working-set increase | 107 MiB | 49 MiB |
| Eager date editors for ten initial row delegates | 10 | 0 |
| Median ordinary scroll frame | 8.9 ms | 9.4 ms |

The ordinary scroll median did not improve; the gain is first presentation and
delegate-creation spikes. Preview requests remained zero in this no-image
fixture, with the same 50 task cards. Visible-item counts alone miss the closed
calendar trees, so the benchmark also counts date editors and native memory.
Working-set deltas include allocator reuse and are not exact retained heap sizes.

A separate 2,000-row task-projection fixture with empty task lists isolates the
identity join: 277 ms and 2,001,000 identity reads became 3 ms and 2,000 reads.
It does not measure real workflow/date-label costs. These measurements exclude
server latency, image transfers and hardware-renderer behavior on live projects.

### Search table: grouped row recycling

The grouped benchmark now uses distinct task identities in every result row;
the previous repeated task payload hid delegate-recreation costs. It sends real
mouse clicks through `SearchResultTable` and `ResultTreeMixin.toggle_result_node`.
Only debounced persistence is replaced by a counter. Frame measurement ignores
frames emitted during input dispatch and waits for presentation after dispatch.

`TacticTaskCards` repeats the visible card count and binds each retained card to
its current record. Reassigning a recycled table row must not destroy all task
editors and avatars merely because its record array changed. Editors reset when
their task identity changes; date editing captures the owning node and closes
when its row is reassigned. Drafts remain controller-owned.

At 1800 x 1600, with 500 objects, ten groups and five distinct tasks per object,
six collapse/expand cycles in the offline software renderer measured:

| Measurement | Array-backed card repeater | Retained card slots |
| --- | ---: | ---: |
| Median collapse input-to-frame | 200 ms | 64 ms |
| New cards per collapse | 85 | 5 |
| Median expansion input-to-frame | 193 ms | 47 ms |
| New cards per warm expansion | 80 | 0 |

First expansion still creates new visible rows (278 ms in this fixture); this
change does not claim instantaneous cold creation. The regression uses object
identity and creation counts, not hardware-dependent timing limits, and checks
that a reused editor sends mutations to the new task only.

For changes to mass UI:

1. Instantiate the real QML with the real model boundary and record QObject,
   QQuickItem, and visible-item counts.
2. Inspect `layer.enabled`, `OpacityMask`, `DropShadow`, `Canvas`, large
   translucent subtrees, unconditional Repeaters, and hidden image sources.
3. Record request counts while the consumer is visible, retained but hidden, and
   reopened.
4. Exercise pooling, scrolling, tab switching, selection changes, and a real
   rendered frame. Treat warnings and binding loops as failures.
5. Add or tighten a deterministic object/request budget. Do not use a
   machine-dependent millisecond assertion as the regression test.
