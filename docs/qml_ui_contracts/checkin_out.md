# Check-in / Check-out contract

This document describes the current QML workflow. Historical QWidget audit
notes were removed after the QML implementation became authoritative.

## Ownership

- `CheckinOutController` owns the selected target, object tabs, process/context,
  staged files, options, naming preview, prepared payload, execution state, and
  refresh after completion.
- TACTIC and filesystem behavior stays in the native APIs:
  `tc.get_virtual_snapshot()`, `tc.inplace_checkin()`,
  `tc.checkin_snapshot()`, and the native `SObject`, `Snapshot`, and `File`
  methods.
- `RepositorySyncController` owns HTTP/local checkout and download state.
- `CommitQueueController` owns queued prepared operations. It reuses the same
  check-in executor; it does not implement a second check-in engine.
- DCC actions are routed to a selected thin client through fixed connector
  capabilities. The standalone process retains repository and TACTIC writes.
- Maya scene check-in follows the legacy save invariant: Save Scene queues a
  scene placeholder and the captured playblast; Commit Queue resolves and retains the
  virtual snapshot. Commit asks that same Maya client to rename and save the live
  scene to the resolved versioned path before standalone starts transfer/check-in.

## QML boundary

QML receives only search keys or tokens, project/Search Type strings,
process/context values, normalized paths, primitive options, display metadata,
repository codes, progress/state/error values, and safe file lists.

Raw `SObject`, `Snapshot`, `File`, project/schema objects, workers, callbacks,
virtual-snapshot dictionaries containing Python objects, and DCC scene objects
must remain in Python.

## Target and object tabs

- The dock maintains object work tabs and the selected workspace target.
- Mode, process, context, and tab state are persisted through
  `env_read_config`/`env_write_config`.
- Process choices come from native `SObject.get_all_processes()`.
- A restored tab whose source object is not present in the current model remains
  navigable, but its operations are disabled until the object is resolved.
- Selecting another result may update the target, but it never queues or starts
  a check-in implicitly.

## Check-in preparation

- File selection and drag/drop populate one Python-owned QML-safe file model.
  Each item exposes name, path, size, extension, and recognized file type.
- Selecting or dropping more than one file for Save Snapshot pauses before
  preparation and asks whether the current batch is one grouped snapshot or
  separate queued check-ins in source order. The answer is a per-batch override;
  it never rewrites the persistent Drop Plate grouping preference. A single file
  continues without confirmation.
- Result rows and cards reuse one antialiased drag/drop target. The object-icon
  zone is offered only when every dragged file is classified by TACTIC as a
  preview image (JPEG, PNG, or TIFF); other files expose only Publish and
  Attachment. The controller validates the same rule before queueing.
- Process, context, description, revision/version options, keep filename,
  update-versionless, preview generation, and repository selection are part of
  the preparation state.
- A newly targeted sObject or process starts on its base process context. The
  optional branch remains empty until the user adds one; targeting an existing
  snapshot preserves that snapshot's branch.
- Save Snapshot from an existing snapshot keeps its target and context but lets
  TACTIC allocate the next version. Add Revision alone reuses the selected
  snapshot's version number.
- Defaults come from the project configuration API and the current repository
  configuration. The first active default is the display repository `General`
  with native code `base`; payloads always retain the code rather than the
  display title.
- The selected process pipeline supplies `checkin_mode`. Native File metadata,
  including `name_part`, survives primitive queue serialization and is restored
  before virtual naming. Sequence, directory, and multi-file modes initially
  suppress versionless output as in the original workflow.
- Naming preview runs asynchronously through `env_inst.server_pool` and
  `tc.get_virtual_snapshot()`. Request identity prevents an old result from
  updating a new target or option set.
- The prepared payload is validated before it can be executed or sent to Commit
  Queue.
- Public `skey://` links are accepted at the executor boundary, but the scheme
  is removed from a copied payload before virtual naming and snapshot creation;
  TACTIC therefore receives `PROJECT/search_type?...`, never `skey://...` as a
  Search Type name. The UI link and caller-owned payload remain unchanged.
- Debug presentation may show a sanitized primitive payload, but never tickets,
  passwords, credentials, or private repository objects.
- Directory traversal and sequence grouping must run outside the GUI thread.
- Relation drops remain Ingest operations and do not show the snapshot grouping
  question. Before upload or mutation, Ingest queries the selected parent's
  existing children by the mapped filename column. A collision requires an
  explicit update, skip, duplicate, or cancel decision; update uses the exact
  returned Search Object key rather than a global filename match. Intra-batch
  duplicate names use the same decision path. A new Search Object, its publish
  snapshot, and its direct or instance relation to the expanded parent are
  committed in one TACTIC transaction. A relation failure aborts that
  transaction instead of reporting an unlinked child as successful.

## Check-in execution

- Execution stages are queued/preparing, copying, upload or snapshot, and a
  terminal completed/failed state.
- Work runs in `env_inst.commit_pool` and uses the existing TACTIC check-in
  functions; model updates return through queued Qt connections.
- A second start is rejected while an operation is active.
- The dock displays stage, current file, progress, and actionable failure text.
  Full traceback data is written to Debug Log.
- A failed payload remains available for a complete retry.
- Success refreshes the affected snapshot/file presentation without reloading
  unrelated search state.
- Native `attachment` snapshot data makes the built-in Attachment process
  visible even when the general "show built-in processes" option is disabled.
  A successful first attachment check-in materializes and reveals that process
  row in the retained result tree; an explicit process-visibility filter still
  hides it.
- Generated web and icon derivatives are written to temporary files, validated,
  and then replace their deterministic repository paths. A generation failure
  stops the check-in before snapshot creation and never reuses an older
  derivative left at the destination.
- A successful versionless update invalidates preview state for the affected
  snapshot and object. Local preview URLs carry the file timestamp and size as
  their content revision, so Qt cannot reuse a decoded image from the previous
  contents of the same versionless path.
- Copy, upload, and server calls are not claimed to be safely abortable.
  Shutdown prevents new stages and waits through the shared pool lifecycle.

## Commit Queue integration

- Sending a prepared operation to Commit Queue transfers one primitive payload plus
  the Python-side source identity. Maya placeholders are validated by the queue so
  its row appears before server naming finishes.
- Queue execution calls the same check-in executor as direct Check-in.
- There is no QWidget adapter, duplicate preparation path, or QML-only queue.

## Check-out and open

- Snapshot Browser selection is represented by safe model identities; native
  Snapshot and File objects remain in Python.
- Get/download uses Repository Sync with progress, retry, partial-file handling,
  size/timestamp freshness validation, and cancellation at supported boundaries.
- A current local file is reused without adding a visible queue row or issuing
  HTTP work.
- A conflicting local file requires an explicit Overwrite, Skip, or Cancel
  decision.
- Standalone Open calls native `File.open_file()` after the file is available.

## DCC open, import, and reference

- Open, Import, and Reference use the selected DCC client's registered fixed
  capability only after standalone has prepared the local file.
- Unsupported actions are disabled with a reason. Shared presentation code does
  not import Maya modules.
- Multiple clients are routed by client id; process-wide environment mode is not
  changed to emulate the remote application.

## Concurrency and stale results

- Naming and server discovery use `env_inst.server_pool`.
- Check-in stages use `env_inst.commit_pool`.
- Repository downloads use the Repository Sync worker pool.
- Every operation that can outlive a selection, tab, project, or controller
  carries request identity or cancellation state.
- A late completion cannot update a destroyed or different target.
- Preview discovery also carries a per-node request generation. Refreshing a
  stable versionless node invalidates the previous generation, so a preview
  worker started before the check-in cannot overwrite the refreshed image.

## Manual acceptance

Verify against an isolated project and repository:

- single file, multiple files, sequences, directories, and workarea modes;
- each allowed repository and naming rule;
- revision/versionless/keep-filename/explicit-filename and grouped check-in;
- local and HTTP checkout, local conflicts, and multi-file snapshots;
- naming, copy, upload, and snapshot failures followed by retry;
- closing the dock and application during each asynchronous stage;
- Maya open/import/reference with one and multiple connected clients;
- exact refresh of the affected snapshots and files after completion.
- first attachment check-in with built-in processes disabled, followed by
  closing and reopening the same object's tree; the Attachment process remains
  visible unless it was explicitly hidden in the process filter.
