# UI complexity review implementation

This tracks the twelve approved review items, implemented on 2026-09-07.
Checked means implemented and covered by focused offline regression tests, not
certified against a live deployment.

1. [x] Server-side task filters, ordering and pagination, preserving drafts.
2. [x] Demand-driven task projections (list, Gantt, calendar).
3. [x] Shared bounded script AST cache and error-position prefix recovery.
4. [x] Linear overlap detection after sorting Gantt intervals.
5. [x] Demand-driven sObject information and worker-owned file inspection.
6. [x] Shared search field presentation and input behavior.
7. [x] Shared image selection with controller-owned staged state.
8. [x] Shared user filtering/grouping and identity lookup.
9. [x] Shared composer draft persistence through ConfigWriteQueue.
10. [x] Shared compact field layout for edit/create/duplicate forms.
11. [x] Lazy commit queue naming details.
12. [x] Remove shadowed client method and unreachable protocol branch.

## Ownership and checks

1. `query_task_workspace_page` applies predicates and global ordering before
   count/offset/limit (maximum 500). Scope-wide facets retain alternative choices;
   native cross-database search filters resolve parent titles. `TaskWorkspaceStore`
   owns query cache, membership and facets. Dirty tasks stay editable without
   counting as server matches. Tests exercise real SQL predicates/pagination,
   native procedure serialization, generation invalidation and retained drafts.
2. `TasksController` maintains cheap row projections and marks hidden Gantt and
   Calendar projections dirty. Dock presentation is the visibility authority.
   Tests assert no hidden projection calls; browsing calendar months without a
   day filter does not queue an identical server request.
3. `script_editor_features._safe_tree` shares eight cached revisions between
   parsing consumers. Recovery jumps to the syntax error instead of retrying
   every trailing line. The regression failed before the fix with 3,002 parse
   attempts and now takes at most three; changed revisions are not stale.
4. `task_data.gantt_layout` marks overlaps with a sorted interval sweep, not all
   pairs. A seeded pairwise reference covers nested/touching intervals and users.
5. `SObjectInfoController` publishes only active detail models and inspects native
   files in a cancellable worker. Existing repository preparation is reused.
   Tests cover worker thread, page activation, stale results and real report QML.
6. `controls/SearchField` replaces duplicate search icon/clear/input blocks in
   tasks, knowledge navigation, user administration, definitions and native Search.
   Feature-specific suggestion handling and debounce remain with their owners.
   Real mouse/keyboard checks cover clear, Escape, read-only and middle-click
   suggestion navigation.
7. `controls/ImagePicker` reuses `ItemPreview` and `ImageFileDialog`. Project and
   Search Type editors own staged selection; sObject forms reuse the same native
   dialog. Runtime checks accept a real temporary image and undo selection through
   the actual project controller at narrow and wide widths.
8. `UserFilter` uses Qt's native proxy and list sections; `UserSearch.js`
   shares matching with choice-based user controls. `RecordListModel.lookup`
   indexes identities with model-driven invalidation. Tests cover real directory
   search/group counts, choice identity and update/remove/reset invalidation.
9. `ComposerDrafts` owns context-scoped text while attachments keep their existing
   owner. Notes/Messages inject the application's existing `ConfigWriteQueue`.
   Tests cover independent contexts/namespaces, shutdown restoration and writes
   outside the GUI thread.
10. `SObjectFieldGrid` replaces duplicate edit/create/duplicate placement loops.
    It retains native field delegates, roles, validation and stable object names;
    real forms are tested at narrow/wide widths. The duplicate procedure's missing
    native `SearchType` import found by the regression run was restored.
11. `CommitQueueView` creates naming rows only while expanded. Runtime tests walk
    visual children and verify absent/present/released delegates.
12. The shadowed `refresh_capabilities` method and unreachable capabilities branch
    were deleted from Handler Server. Existing transport tests cover updates.

## Verification

Focused runs passed **478 tests** across task query/store/data/catalog/controllers,
task selection/Gantt/QML, script parsing/editor, Handler Server, configuration
queue, shared controls, users, project metadata, commit layout, sObject forms and
reporting, Notes/Messages and native TACTIC objects. A further 10 localization
checks passed. QML modules were also run separately to avoid cross-module native
Qt lifetime contamination during diagnosis. The profile fixture had deferred
native-filter destruction beyond its QML engine lifetime; teardown now releases
the view before the engine/models. The combined 160-test shared-control/form/chat
run passes as well, not only the isolated module runs.
The final combined run passed all **488 tests in 24.35 seconds**. The printed
`run button script error` traceback is the intentional Script Editor error-path
fixture; the runner exits successfully.

`tests.test_qml_smoke_harness` passed both checks: every registered window opened,
reopened and shut down in an isolated offline application. `tests.test_qml_lint`
passed without increasing the recorded warning budget. GUI tests suppress native
Windows error dialogs and use offscreen/software rendering; they do not launch
the production application or modify production settings.

The global `tests.test_ui_structure` suite is **not green**: 51/53 checks pass.
Its remaining checks concern the existing Knowledge Base-specific DockPanel
binding and architecture-size debt (29 files against the old size budgets).
Those unrelated paths/budgets were not rewritten or relaxed to obtain a green run.

The guarded live server smoke now includes filtered pages, object ordering and
contextual note matching. It was **not run**: no isolated TACTIC test project was
configured. Live SQL latency, deployment permissions, desktop GPU/DPI and DCC
behavior are not inferred from the offline checks.

See [performance fixtures and measured medians](qml_performance.md),
[task query/presentation contract](tasks_workspace_implementation_plan.md) and
[shared component ownership](ui_component_map.md). Synthetic Python timings are
not production frame rates; no claim of instant server responses is made.
