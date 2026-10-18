# Tactic Frame B12: files, check-in and repository queues

Status: **delivered**, 2026-10-18. Implementation and bounded release acceptance
passed on the final sources; hardware/deployment limits are listed below.

The original reference is Handler commit
`d1973ded2e30052effc851f91d05a716579b29bf`. Both products ship
independent portable copies. Native Qt controls, filesystem/DCC adapters,
repository rules, request generations, file identities, transfer journals and
mutation owners stay with their existing hosts.

## Scope and owners

| Surface | Handler | Stream | Acceptance |
| --- | --- | --- | --- |
| File workspace and navigation | `FileWorkspaceView`, navigation/catalog/tree/file rows | Production `fileWorkspace/FileWorkspaceInspection` and tree | Selection, project/view changes, retained tree/scroll, refresh and menus |
| Changelists, files and inspector | Changelist view/files, inspector/history | Inspection owner and inspector | Native stage/unstage/create/rename/delete; browser inspection, status/selection and file identity |
| File workspace operations | Submit/review/shelf/revert/target/revision/comparison dialogs | Native-only local workflow; browser inspection/admin | Actual native operations, conflicts, cancellation, reopen and uncertainty guards |
| Repository metadata | Depots, mappings, storage, streams/graph/editor and log | Depots, storage, inspection and log | Existing capabilities, validation and server effects; local workspace mappings stay native |
| Object check-in | `ItemCheckinDialogs`, check-in controller | `checkin/ObjectCheckin` | Group/individual, revision/append, preview/clipboard, permissions and files |
| Drop Plate | Drop Plate view and check-in preparation owner | `checkin/DropPlate` | Files/folders, grouping, patterns, target selection, preview/clipboard and queue handoff |
| Related ingest | Ingest files/rule/conflict views and controllers | `checkin/IngestFiles` | Rule selection/edit/save/delete, path filters, conflict decisions, real child publication |
| Matching templates | `MatchingTemplatesView` and controller | `checkin/MatchingTemplates` | Mandatory/locked rules, order, enable, custom mapping, pattern test, save/cancel |
| Commit Queue | Queue view, summary, action menus and progress | `checkin/CommitQueue` | Prepare/validate/upload/check-in, retry/cancel/recovery, unknown results and preview/naming |
| Repository Sync | Queue/editor and existing sync/preset controllers | Browser download capability only | Discovery, bounded parallel transfers, progress, retry/cancel/reopen, presets and large queues |
| Repository editor | Existing shared `configuration/repository.ui.mjs`; remaining team-path confirmation/setup | Existing RepositoryEditor and server settings | Real path validation, save/reset, custom entries and explicit shared-path confirmation |
| Screenshot tools | `ScreenshotMakerView` and screenshot controller | Commit Queue screen-capture/preview owner | Native region/clipboard, browser capture permission/cancel, preview ownership and cleanup |

Frame owns composition, layout, shared input/presentation rules and semantic
actions. Existing controllers/commands keep authoritative data, ACL, filesystem,
upload/check-in, validation and persistence. No second queue or transfer engine
is introduced. Browser reload can require file reselection; an unknown committed
write must be inspected before retry. Native filesystem synchronization and DCC
commands are not advertised as browser capabilities.

`App.vue` loads `FileWorkspaceInspection.vue`. The older browser
`FileWorkspace.vue` and its mappings editor have no production callers. Their
formatting-only edits were reverted after this was verified; they are not a
second live workspace to migrate or a source of browser local-file capabilities.

## Required acceptance

- Inspect original owners and every child form before replacing presentation.
- Exercise an actual file-to-check-in journey and queue cancel/retry/reopen,
  retaining file identity, repository rules, revision and unknown-result guards.
- Exercise File Workspace operations and native sync discovery/transfer/presets
  using temporary repositories and isolated configuration.
- Compare pinned original, current Qt and current Vue on matching fixtures,
  themes, languages, sizes and scales. Include empty/loading/error/disabled,
  narrow/phone composition and large-list virtualization. Record native-only
  capabilities separately.
- Run actual input checks, affected server/filesystem workflows, formatting,
  source freshness, independent packaging and the mandatory platform gate.
- Update EN/RU Help and release metadata, review both diffs, commit each product
  independently and verify the authorized NAS backups. Preserve unrelated work.

Physical touch, OS IME, compositor/DCC integrations and production PostgreSQL
require their own hardware/deployment acceptance; automated fixtures cannot
establish those boundaries.

## Implementation

Stream 0.112.165 and Handler 0.6.0.116 contain independent copies of 191
portable JavaScript modules and three JSON catalogs. New file responsibilities
are grouped under `shared_ui/features/files` and native
`qml/features/files/{queue,sync,screenshot,workspace}`. Public native Workspace
type names remain small facades; its largest new responsibility has fewer than
800 formatted lines. Five superseded native presenters were removed.

The production Workspace panes, tree/file rows, inspector/history, stream
table/graph/editor, Depot/Storage, native operation forms, Submit, Mappings,
Log, dialogs and navigation use the shared composition. Native keyboard/command
routing retains its existing owners. The browser production inspector, tree,
catalog/storage and log retain request generations, paging, ACL and writes;
local checkout, native Submit, mappings and DCC remain native capabilities.
Safe browser GC uses the existing house confirmation.

Matching Templates, Drop Plate, ingest/rules/conflicts, Object Check-in,
Commit Queue, native Repository Sync, repository confirmations and Screenshot
Maker likewise consume shared descriptions. Editable template mappings retain
custom process/context strings. Queue menus, duplicate decisions, preview
management, naming, progress, summaries and advanced forms are included.

Work tabs retain measured natural widths, close targets and a horizontal
scrollbar. Action captions use measured widths and narrow forms reflow.
Splitter movement previews locally; release commits once, while cancellation
restores the prior size without saving. Pointer cancellation, foreign-pointer
release and keyboard changes have actual input checks in both hosts.

The neutral catalog includes `choice-editable` and `checkbox-wrapped` examples.
The renderer reuses house TabButton, editable ComboBox, CheckBox, graph scaling
and character-wrapped text. It reveals focused form controls without creating
feature-specific replacements for base controls.

## Ownership and correctness fixes

- Browser queue validation, clipboard and capture retain their session,
  operation and source identity. Disposal/account changes invalidate callbacks;
  abandoned screen capture releases its tracks. Same-user renewal preserves
  editable files and marks a pending write unknown. A late validation cannot
  save another user's queue into the next account's recovery journal.
- Drop Plate clear/context/session/disposal invalidates asynchronous clipboard
  and directory intake, including stale context-menu selection.
- A committed upload whose reply is lost becomes `Result unknown`; automatic
  re-publication is disabled and inspection is offered. The connected journey
  verifies exactly one snapshot/version remains on the server.
- Native Sync presets update the actual server-returned search key instead of
  constructing a nonexistent `wdg_settings.code`. Real id-based preset
  create/update/delete runs through QML and XML-RPC.
- HTTP download errors close response streams and retain textual diagnostics.
  Repository Sync retains bounded parallelism, retries, cancellation and
  partial-file cleanup. The process tree reads the actual node key.
- Native screenshot tests draw/move/resize/redraw through pointer input and
  verify the existing controller's handoff after the overlay is hidden.
- The deferred ripple callback tolerates destruction of its control. The
  schedule dialog computes scene width from explicit paddings, avoiding a
  binding loop exposed by shared dialog metrics.

## Acceptance evidence

Generated evidence stays local and ignored; regenerate it after source changes.
The drivers reject changed source/archive fingerprints instead of blessing old
images. The original archive is a Git archive of the pinned commit above.

- `tools/frame_files/capture.py`, `frontend/tests/frame_files.mjs` and
  `tools/frame_files/report.py` build `tools/frame_files/output/index.html`.
  The complete matrix contains 300 current Qt/Vue pairs across three themes,
  light/dark, EN/RU and affected desktop/narrow sizes, plus 56 original/current
  native capability pairs. That is 712 native/original and 300 browser images.
  A separate 150% DPI matrix contains 50 Qt/Vue and 56 native capability pairs.
- Full-content comparisons check shared rectangles, typography, fills and
  control interiors. Commit Queue uses explicitly marked `shared-fragments`
  comparisons because native server-queue and local/DCC capability regions
  differ. Complete original/current screenshots remain visible beside them.
  Original screenshots are reference evidence, not assertions that every
  old/new pixel is identical; OS chrome/compositor shadows are outside scope.
- 137 owner/layout cases pass together with normal GC, and separately in
  isolated Qt processes.
  The mandatory gate separately exercises native queue/sync/screenshot/prompts,
  Object Check-in, Workspace layout and connected native/browser file journeys.
  **121/121 mandatory stages passed**, including the combined owner suite.
  The final gate's status is recorded in
  `tools/frame_foundation/output/platform/gate.json`.
- Real disposable-server checks cover uploaded check-in, append/revision and
  group guards, related ingest conflicts/rollback, native Workspace submission,
  shelves/history/file identity, browser inspection/catalog/storage, reload and
  lost-write-response handling. Native Sync downloads use localhost HTTP and
  preset publication uses the actual XML-RPC owner.
- Actual input includes custom mappings, keyboard focus, confirmation/stale-path
  guards, editable stream creation, retained tabs/splitters, clipboard/capture
  ownership and virtualized 1000-row queues. Browser file selection in the table
  journey opens the enabled Attach files button's real chooser rather than
  bypassing the loading guard with a hidden input.
- B12 quality comparison against the pinned original adds no structure/lint
  regressions: existing structure failures decrease from eleven to nine;
  unqualified warnings 5386→4951, unused imports 41→40, other category budgets
  unchanged. Native smoke has no font/runtime warnings. This does not claim
  the older accumulated foundation baseline is clean.
- EN/RU Help, control atlas and release metadata are updated. Independent
  packaging and the mandatory final platform gate pass. Build warnings about
  existing mixed static/dynamic imports remain informational; no new dependency
  or runtime bridge was introduced.

## Combined native owner regression

The combined 137-case owner/layout suite initially crashed with Windows access
violation during a later Screenshot Maker or Matching Templates scene, although
each module passed separately. A native DbgHelp stack identified
`QCoreApplication::notifyInternal2` called from the Windows timer dispatcher.
The receiver address matched Repository Sync's `_active_row_timer`, created by
`test_start_checked_dispatches_only_pool_capacity`.

That test replaced the controller's real QThreadPool with an inert fake and
left its active timers/queued work alive after the assertions. The fixture now
restores the real pool, invokes the normal shutdown owner and schedules QObject
deletion in cleanup, including assertion failures. Four complete combined runs
passed afterwards with ordinary Python GC and no diagnostic patches. The full
owner suite passes inside the mandatory platform gate; no GC/cache/rendering
workaround was added to either product. The complete 137-case suite also passes
on native Windows/OpenGL. Screenshot Maker now explicitly focuses its keyboard
scope after hiding the invoking windows, preserving Escape cancellation there.

Physical touch hardware, OS IME, desktop capture pixels, compositor/DCC and live
production PostgreSQL remain deployment acceptance limits. The native preset
integration process also reports Python exit-time uncollectable-object warnings;
its successful mutations do not establish warning-free resource teardown.

Three consecutive real preset mutation cycles additionally report zero runtime
uncollectable objects after normal collection; the interpreter-exit warning
above is recorded separately from those runtime observations.

## Reproduce the visual comparison

From the Stream root, prepare the immutable reference in a new work directory:

```powershell
New-Item -ItemType Directory -Force .tmp/b12 | Out-Null
git -C D:/code/th_codex archive --format=zip --output=D:/code/TACTIC_VUE/tactic_stream/.tmp/b12/original-handler.zip d1973ded2e30052effc851f91d05a716579b29bf
Expand-Archive -LiteralPath .tmp/b12/original-handler.zip -DestinationPath .tmp/b12/original
python -B -X utf8 tools/frame_files/capture.py
node frontend/tests/frame_files.mjs
python -B -X utf8 tools/frame_files/report.py
```

Use an empty reference directory; never overwrite the pinned original with staged
or current presenters. For the smaller 150% matrix set `QT_SCALE_FACTOR=1.5`,
`FILES_FRAME_OUTPUT=tools/frame_files/output/scale-1.5` and pass `--smoke` to
the native capture. Set `QT_QUICK_CONTROLS_STYLE=Basic` for native unit checks.
The platform gate is `tools/frame_foundation/check_platform.py --handler-root
D:/code/th_codex`; independent copies are checked by `tools/sync_tactic_frame.py`.
