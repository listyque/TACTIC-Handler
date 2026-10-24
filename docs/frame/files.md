# Tactic Frame: Files, check-in and queues

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

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

## Ownership and lifecycle requirements

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

## Verification

Run the focused drivers under `tools/frame_files/` from the Stream development
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
