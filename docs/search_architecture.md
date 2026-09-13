# Search architecture

Search Tab is the single owner of a running search. Its `filter_records` are
the canonical definition shown by Advanced Search and saved by Search Views.
TACTIC query filters are always derived from those records.

## Sidebar search setup

`SidebarEditorView` keeps the navigation tree beside a settings form composed
from the same `ConfigurationSection` and `SettingsRow` controls as Configuration.
`SidebarEntrySettings` owns the Item/Access/Technical presentation, while
`SidebarTechnicalSettings` keeps server widget details out of normal setup.
The XML editor still edits the selected native element, not a parallel format.
`SidebarEditorController` starts a session from the window model's visibility
signal. Neither the QML loader nor `FloatingWindow` starts a second reload;
first opening and reopening a retained window each start exactly one session.

`SidebarSearchMixin` owns the Search Type preset-library workflow and the native
modal `sidebar_search_preview` window. The single **Configure search** button
opens `AdvancedSearchView`, `SearchResultsPane` and the existing Quick Filter
popup/editor. `SearchPresetBar` owns the shared preset picker and its actions.
`SearchResultMenus` shares the ordinary workspace's process-visibility editor,
saved-search selection, sorting and grouping menus with the preview. Opening a
menu uses the loaded catalog; selecting a saved search applies its conditions
through the active tab's existing query path. Refresh keeps the Search Type's
full preset library scope. The Advanced Search action reveals and focuses the
editor already beside the results rather than opening a duplicate editor.
Long menu lists use the shared scrollbar with a reserved content gutter;
short menus retain their full row width without a scrollbar.
The preview's proxy selects only the current tab from the retained surface
registry.
`SearchResultsPane` is also used by the ordinary Search workspace. It presents
the same `WorkspaceResultItem` and `WorkspaceCard` delegates, tree expansion,
selection, process menus, card navigation and split versions views. All five
view modes are available. A preview view-mode change updates the running tab
and stages the sidebar item's `display/view_mode`; saving Sidebar Editor
publishes that default, while viewing results alone writes nothing to TACTIC.

Workspace dock layouts use the existing `DockPanelModel` document unchanged:
`panels` plus the native layout tree. Project-wide presets are stored as global
`config/widget_config` records with category `workspace_layout`, Search Type
`SideBarWdg`, and a unique `workspace_layout@…` view. A sidebar Search Tab stores
only that view in `display/layout_preset`. Each outer sidebar/Search Type section
owns one cached dock document. Leaving a section captures its current document;
normal shutdown captures the active section before QML teardown. Returning to
an initialized section restores that document synchronously without repeating
first-show initialization or issuing a server request.

The assigned `layout_preset` is only the seed for a section's first opening. It
must not be reapplied when returning to that section or overwrite the user's
later in-session arrangement. The controller projects presets from the
already-loaded project `ViewsConfig`, so the first seed also requires no network
request. Supervisors manage presets from the workspace panel menu; assigned
presets must be unlinked before deletion. Explicit Refresh and declared
configuration invalidation remain the only paths that reload affected data.

This outer-section document is separate from inner Search Tab state. Each inner
result tab continues to own its view mode, sorting, grouping, result split,
expanded rows, selection, and scroll position. Warm switches at either level
restore the retained owner synchronously rather than sharing or reconstructing
its state.

Before a section selection is restored, the dock model pre-hides only outgoing
panels that are absent from the target layout. It then restores the target
selection and applies the complete target layout. This two-phase publication
keeps hidden task, snapshot, article, and editor models attached to their live
QML delegates, while newly visible panels observe only the target context.
No transient layout is persisted and no timer participates in the switch.

The preview waits for the exact project and sidebar key before loading its
controllers. Closing it restores the previous section, and switching project
invalidates the preview. Existing tabs retain query and personal filter state.
Unsaved sidebar XML must be saved first. Paging uses the application's current
page/infinite mode; closing the preview does not reload a hidden preset library.
Native child windows are parented to the invoking editor, including the Quick
Filter and process-visibility editors opened from the preview. Process editing
starts its session before showing the window and saves the existing local
`process_ignore_dict` for that exact sidebar tab, not for neighboring searches.
Sorting and grouping also use the active tab's existing state and result model.

The native `search_view` remains the initial query, with Quick Filters adding
their ordinary Advanced Search records in that tab. Supervisor defaults still
use `quick_filters@<section.entry_key>` in `config/widget_config`; two links to
the same Search Type can therefore have different defaults. The ordinary Save
action continues to save only the current tab's personal layout and selection.

The icon library binds both explicit and implicit popup dimensions, since a
native popup can replace its explicit size when its model populates. Its grid
adapts its columns to the available width and reserves the shared scrollbar
gutter. Both the drawer and editor use `SidebarTreeRow` with the theme's
`contentSelection`/`contentSelectionText` pair, preserving server item colors.

Verification: `test_sidebar_editor_qml` exercises actual input, narrow/wide
localized layouts, native icon popup dimensions and separator selection;
`test_sidebar_search_workspace` exercises real Search and Quick Filter
controller wiring without server requests for preview navigation.
`test_editor_windows_qml` opens the actual preview and exercises all five modes,
object selection, preset selection/application/refresh, Quick Filters,
process-visibility editing/persistence, sorting, grouping and nested modal
ownership at narrow/wide sizes, including native Windows at 150% scale.

## Search entry points

The primary search field edits only the first `name` record. Advanced Search
edits the complete record list. A saved preset restores that same list.
Sidebar entries only provide an initial Search View and open a Search Tab;
they do not implement another search or filtering engine.

All entry points use `thlib.ui.search_contract`:

`sidebar / primary field / Advanced Search / preset / relation / skey`

`-> filter records -> SearchTabSession -> executable TACTIC filters`

Server serialization and discovery of TACTIC Search Views remains
in `thlib.ui.search_presets`; it is storage, not a second runtime model.

## Continuous loading

`SearchResultSurface` arms the shared scrollbar's pagination permit directly
from wheel input, including trackpad pixel deltas. It must not depend on the
scroll animation starting: disabled animations still require another page
when the user reaches the end. The shared scrollbar owns the permit and blocks
it while its thumb is dragged; restoring a viewport or revealing a retained
tab does not request another page.

New pages use the existing model append path. SQL name order and the display's
natural name order can differ, so incoming rows can belong between existing
ones. `WorkspaceItemModel` reconciles the changed range by node identity,
inserting new ranges without removing unchanged interior rows. This preserves
expanded nodes, selection, live delegates, and the viewport's visible anchor.

The controller owns exhaustion; the surfaces stop pagination when `has_more`
is false. `tests.test_search_pagination_qml` exercises real wheel, touch, and
scrollbar input against the list and grid with and without motion, verifies
sorted appends, and checks full, short, and empty final pages through the real
controller with an isolated worker boundary.

## Session restoration

Each Search Tab persists its loaded page offsets, paging cursor, total,
exhaustion state, expanded tree state, selected node ids, and list/tile
viewport. The tab configuration stores only this presentation metadata.
Server sObject dictionaries remain owned by `thlib.server_cache`.

On application startup, every saved page of the active continuous search is
rehydrated together through its exact cache-first query on a worker thread.
Only an absent or invalidated page is fetched from the server, and the restored
projection is applied once rather than page by page. Expanded branches and the
final viewport are restored afterwards. Explicit Refresh still bypasses and
replaces cached data.

Before QML teardown, the application captures the live viewport into the active
Search Tab, even if its dock or window is hidden. Normal controller shutdown
persists that captured state after QML is gone. Autosave must not replace saved
coordinates while the tab is unloaded or its expanded branches are still being
restored. `InitialBatchPresentation` retains requested coordinates until its view
has rows, geometry, and visibility; capture returns those pending coordinates
rather than an intermediate zero. A newly created Search view requests the current
tab's saved viewport once, covering cache results that arrived before the view.
Warm tab switches keep the existing surfaces and do not use that creation hook.
`tests/test_search_viewport_restore.py` verifies the real QML input/capture path,
configuration round trips, delayed layout, hidden views, and restoration-time
autosave; the entrypoint ordering is guarded by `test_application_runtime.py`.

Switching between already loaded Search Tabs is a single presentation
transaction. The controller captures the outgoing viewport, swaps the cached
projection, and restores the incoming viewport before yielding to the next
rendered frame. Transient delegate and shared-scrollbar animations are
suppressed only for that transaction; ordinary interaction motion is not.
The latest controller phase timing and click-to-first-frame latency are exposed
by `search_tab_switch_monitor.metrics` and accumulated under the
`ui.search_tab_switch` runtime metric. When LOG recording is enabled, the same
breakdown is written to the `performance/search-tabs` Debug Log group.

Search Tab activation must not warm presentation owned by a closed native
window or rebuild an editor catalog that is not being edited. The sObject Info
report therefore marks its projection dirty while its window is closed, and
the Quick Filter editor discovers its groups only when its modal session opens.

Advanced Search suggestions return the record list as one worker result field
(`(records,)`); `OperationWorker.add_result_data` appends the request metadata.
The suggestion consumer receives `(records, metadata)`, including empty lists.
`test_advanced_search_suggestions` verifies this through the real thread pool,
model population and accepting a suggested value. Ordinary Search and the
sObject linker use the same worker result convention.

Submitting the main Search field with Enter uses `search_suggestion_spec`, the
same Search Type column discovery as autocomplete. The primary Advanced Search
group is title/name (falling back to code), keywords and description joined with
OR, omitting unavailable columns. It consists of ordinary editable filter cards,
not a separate hidden query. Selecting a specific suggestion instead produces an
exact match on its title/name column. Middle-clicking a main Search suggestion
opens a new independent Search Tab with an exact match on the object's stable
`code`; it does not accept or replace the current tab's search.
Search reads use the shared bounded retry boundary for temporary gateway and
TACTIC worker `Sudo` context faults. Mutating procedures remain single-shot.

`set_primary_name` replaces the leading text group rather than accumulating
previous searches. Its companion cards have the same value and relation as the
first card and use OR on suggestion fields. Other conditions remain unchanged;
clearing the main search leaves a single empty first-row placeholder.
The input timer stops on Enter so a submitted search does not reopen autocomplete.
`test_primary_search_filter` covers field discovery, repeat/clear, exact selection,
unrelated constraints and preset round trips; `test_search_text_qml` presses Enter
in the real Search field and checks the resulting Advanced Search cards.

## Quick Filter presentation

The popup's **Edit** entry opens the current tab's layout and selection in the
native modal editor. **Save** is available to everyone, including supervisors,
and commits only the current search tab's selection and `quick_filter_layout`
through the existing Search tab persistence owner. Supervisors additionally have
**Save as defaults on server**, which publishes the same draft for all users of
this sidebar entry. Publishing does not discard the draft or overwrite an
existing personal layout; the supervisor can still save that draft locally.

Server identity is `(project, search_type, category="quick_filters",
view="quick_filters@" + section.entry_key, login="")`. The stable sidebar key
contains its server item name, e.g. `demo/asset@my_tasks`, not its translated
title or a runtime search-tab id. Two entries for one Search Type have independent
policies and defaults. Configuration caches and invalidation use this scope;
the facet catalog remains shared by project/Search Type.

TACTIC's `WidgetDbConfig.validate()` and `get_view_node()` use
`<config><view name="...">...</view></config>` for view names containing `@`.
The prefix guarantees this contract for plain Search Type entries too. JSON
`values` live directly inside that named view, and reads require its exact name.
The old fixed `<quick_filters>` wrapper and `quick_filters:` prefix are not read
or written. Do not disable validation/triggers to accept a mismatched wrapper.
The test server validates both inserts and updates against this native contract;
tests include plain entries, custom sidebar codes, XML escaping and wrong views.
Reference: [WidgetDbConfig](https://github.com/Southpaw-TACTIC/TACTIC/blob/5.0/src/pyasm/search/widget_db_config.py).

The catalog applies the shared policy before constructing a regular user's editor
model. Server-hidden groups and options are absent from that model, not merely
unchecked or invisible QML items. A local layout can hide/reorder the remaining
entries but cannot reintroduce forbidden ones. The local save boundary clamps the
draft again against the current server policy and rejects a different tab id.
Applying the shared default clears the current tab's local layout; other tabs
and the server default remain unchanged.

Facet discovery accepts text and numeric fields as well as categorical strings:
SQL storage types alone do not determine whether a field is categorical. The
catalog retains one to 64 distinct non-empty values, including a single non-empty
value alongside unset rows. Values and server-defined labels are not reinterpreted;
NULL is not inferred to mean yes/no. Technical identity/path/date/blob fields
remain excluded. Discovery stops retaining values once a field exceeds the limit.
Reference-cache payloads retain the facet-column definitions used to build them;
a different or missing definition triggers rediscovery instead of reusing an
incomplete catalog. No versioned format or migration is involved.

The supervisor editor remains a native modal window. Its flat group/chip layout
has one shared scroll viewport, a reserved scrollbar gutter and wrapping footer
actions. Group checkboxes control visibility; disabled groups disappear from the
normal view. **Show hidden filters** reveals only groups available to the editor's
authority: supervisors can restore server-hidden groups, regular users only
their locally hidden ones. Value chips select or deselect the draft's filters;
neither action hides a chip. Their selected state is projected from the same
selection owner used by copy, clear and individual removal. Selecting a value
available to this editor also restores its inclusion if it was locally disabled;
regular users never receive server-forbidden values in the editor model.
The local and server-default save actions serialize that same draft selection.

Opening the editor requests the existing shared facet/task catalog. While open,
`quick_filters_changed` refreshes the model when delayed results arrive, merging
an existing draft by stable group/option identity. Busy/error/empty states are
visible. Closed editors do not rebuild groups on catalog notifications.
The controller starts/discards the session from the window model's explicit
visibility signal. QML construction is not a session boundary: the window proxy
briefly retains closed windows, so reopening must work without recreating QML.
Regressions use the real `WindowHost`, visibility proxy and content loaders, with
both the real Search controller and isolated server fixtures. They cover first
creation, rapid reopen, delayed catalog arrival and mouse/keyboard/touch input.

`QuickFilterEditorController` owns the draft and the server write/read sequence.
It queries the exact project/type/view/category coordinate, accepts both NULL and
empty shared logins, and excludes personal rows. Saving verifies the stored XML
before reporting success. A widget-config invalidation during a request schedules
one follow-up read instead of racing the write or applying the invalidated result.
Background reads do not replace a dirty editor draft. Serialization retains policy
for groups and allowed values absent from the current catalog. These are current
format invariants, not compatibility readers or data migrations.

`test_quick_filter_editor` exercises delayed reads/writes, invalidation, read-back
failure, shared/personal coordinates and partial catalogs. The real QML editor
tests cover both save authorities, delayed catalog arrival, individual removal,
hidden-entry restoration, mouse, keyboard, touch, Russian narrow/wide geometry,
modal ownership and scrolling. `test_quick_filter_personal_layout` exercises the
real Search controller, clamps malicious local selections, verifies that another
tab stays unchanged and round-trips the layout through Search tab persistence.

`SearchQuickFilterPopup` uses the existing cached facet/task request path and
`QuickFilterCatalog.groups`. It does not add a second data cache or alter
Advanced Search generation, supervisor policy, assignee selection or refresh.
The previous Flow/Repeater created all options on every opening, including
hidden user-picker buttons for ordinary groups. With 60 cached facet options,
data preparation took less than 1 ms but 97 controls and Material's inherited
enter transition delayed full readiness to about 400 ms (about 940 ms for 320
options).

The popup retains current group containers and uses `QuickFilterOptions` to
pack exact rows with one non-presented instance of the existing chip control.
Only intersecting rows create buttons; scrolling reuses row slots and releases
offscreen groups' controls. Group coordinates are settled before the first
viewport allocation, so new groups at their temporary y=0 do not each create a
viewport of buttons. The original `ScrollablePopup` still owns the native
window, clipping, bounded height and reserved shared scrollbar. No estimated
list height or additional paged query is involved.

Closing freezes this bounded presentation. Hidden notifications do not read
the groups or lay out chips. Reopening reads the current controller projection,
updates selections and remeasures only changed labels/markers, width, font or
DPI. Local enter/exit suppression makes the first populated frame usable;
other popup styles and editor hosting are unchanged. Mouse, keyboard and touch
still invoke the original filter commands; Tab crosses offscreen rows/groups.

`tests.test_quick_filter_popup_qml` drives the real Search button with cached
facets, native text and bundled icon fonts. It covers first-frame readiness,
bounded creation, retention, hidden updates, generated Advanced Search rules,
clear, shared visibility policy, assignee rows, keyboard/touch, exact scroll
extent, thumb navigation and Russian/narrow layouts. The native Windows suite
also runs at 150% scale. `--benchmark` separates cache reads, group construction,
input dispatch and the first populated frame, including 300 cached sObjects
and their task facets. An offscreen Software run measured roughly 50-70 ms cold
and 3-6 ms warm for 60/320 options, with 25-29 buttons rather than 97/357.
Native Windows/OpenGL measured roughly 120-160 ms cold and 67-70 ms warm,
including native-window presentation waits. These are reproducible fixture
measurements, not a guarantee for every machine or graphics backend.

## Tag cloud presentation

`request_tag_cloud` uses the existing per-project/Search-Type catalog cache.
`TagCloudPopup` resolves that data before opening, without a second tag query.
The old Flow/Repeater created a button for every cached tag on every opening;
the cache avoided transport but not that synchronous QML construction.

The popup measures wrapping with one non-presented `QuickFilterChip`, retains
only the current catalog's row geometry, and presents a viewport-sized pool of
the same shared chips. A binary search selects rows intersecting the viewport.
Rows have exact positions and height, so the original `ScrollablePopup` owns
the full content extent, clipping and reserved scrollbar gutter. This avoids
variable-height ListView estimates changing the thumb size at the end of the
weighted cloud. Neither scrolling nor opening requests more catalog pages.

The pool remains instantiated but hidden between openings. Catalog notifications
are disconnected from presentation while closed. Reopening compares the current
tags/weights and updates selection; changed catalogs, width, font, locale or DPI
invalidate geometry. This is a view projection, not another persistent data
cache. Explicit Reload still uses the controller's force-refresh worker path.
Tab/Shift+Tab scroll to offscreen chips without eagerly creating the whole cloud.
The tag search field filters the entire cached catalog by a case-insensitive
substring. It is a local presentation filter, not an Advanced Search constraint:
typing or clearing it never changes selected tags or requests the server.
Matching chips keep their original tag identities, weights and selection state;
keyboard traversal follows the filtered order. The field is focused and cleared
on opening. Changing the query returns the viewport to the top without changing
the popup's fixed height or instantiating offscreen chips.
The tag popup locally suppresses inherited Material enter/exit transitions;
shared popup defaults are unchanged.

`tests.test_tag_cloud_qml` exercises the real Search button and cached controller
with real icon fonts, native text and Material: viewport-bounded creation,
mouse/keyboard/touch, wheel and thumb scrolling to the final tag, stable extent,
selection/reset, local search/clear, filtered keyboard navigation, reload, empty
state, reopen, resize and Russian layout. Server
access is forbidden in the fixture except for a separately controlled refresh
worker. It also runs with `QT_QPA_PLATFORM=windows` and `QT_SCALE_FACTOR=1.5`.

Run `py -3.14 -m tests.test_tag_cloud_qml --benchmark` to separate cache reads,
dispatch and the first populated frame. In the offscreen/software fixture,
1,000 cached tags previously created 1,000 buttons and took about 2.1 seconds;
the cache read itself was 0.15 ms. The viewport pool creates 11-13 buttons in
that geometry: about 51 ms cold and 7 ms warm. Native Windows/OpenGL measured
about 116 ms cold and 67 ms warm on the same machine, including presentation
waits. These are fixture measurements, not an all-backend 50 ms guarantee;
the change does not modify renderer or VSync settings.

## Live check-in branch refresh

A successful check-in from the current session refreshes only the matching
snapshot branch while the exact parent tree remains selected. Existing process
and ancestor nodes are retained to preserve selection and delegate identity.
Because those nodes are mutated in place, the model explicitly publishes their
expanded, child-presence, child-count, and control roles after reconciling the
flat tree. The visible process row therefore reflects its first or newest
snapshot immediately without closing and reopening the branch. Hidden, replaced,
or abandoned trees are not repainted.

## sObject badge menus

Task and note process pickers read the native sObject's already-loaded per-process
counts and pipeline metadata. Opening the picker does not fetch tasks/notes or
change Search selection; choosing a process opens its details through the existing
controller action. Publish remains first, including a zero count.

`ActionMenu` owns the compact item-action menus' presentation lifecycle. Only
`processPickerStyle` menus suppress inherited enter/exit transitions and retain
their row delegates between openings. Index bindings update the latest actions
without rebuilding an equal-sized menu. These are the two shared menus in Search,
not additional menus per result. Ordinary/context menus retain their style's
transitions and release their rows when closed.

Search's two compact item-action menus use the shared popup's existing in-window
Overlay path. This avoids creating/synchronizing a second graphics window on
activation and leaves native hosting unchanged for context menus and other
popups. The pointer is computed from the planned coordinates before `open()`;
reading a hidden Popup's `x`/`y` back can return its previous position. Menus
flip above the anchor near the owner's lower edge and stay inside the window.

The application uses Material: its inherited Popup enter transition lasts 220 ms,
and `opened` is false until it finishes. Gating the process rows on `opened` made
the first popup frame empty, despite all counts already being available.
`tests.test_process_menu_latency` exercises real Search badge input with Material,
checks populated rows in the first frame, unchanged selection, current commands,
retained delegate identities, narrow/wide layout, and mouse/keyboard/touch input.
No server request is allowed in this fixture.

Run `py -3.14 -m tests.test_process_menu_latency --benchmark` for separate timings
of count lookup, input dispatch, first popup frame, and first frame with rows.
Use `QT_QUICK_CONTROLS_STYLE=Material`; `QT_QPA_PLATFORM=windows` exercises a
real Windows owner instead of the default offscreen fixture. The benchmark
uses the application's rendering policy and native text unless the backend is
overridden. Mouse events go through Qt's event queue so synchronous Python test
input does not block the threaded renderer. Timings start at mouse release,
which activates the badge; press-to-release time is reported separately.

The Material baseline waited about 220 ms before showing rows. The final
offscreen/software fixture with the application's icon fonts measured about
12 ms to content on repeat openings and 35 ms on its first opening. Native
OpenGL measurements still exposed a presentation wait, rather than expensive
row drawing; they did not establish an instant first-frame guarantee. The popup
change does not alter global renderer/VSync settings, and software measurements
must not be presented as an all-backend latency guarantee.
