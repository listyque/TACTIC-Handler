# Commit Queue contract

This document describes the current Python-owned queue. Historical notes about
the superseded visual-only QML model and QWidget queue were removed.

## Ownership and data boundary

- `CommitQueueController` is the only owner of queued operations.
- `CommitQueueModel` exposes primitive QML roles and a stable `operationId`.
- A queue item stores a validated preparation payload from
  `CheckinOutController`. QML does not build or copy a second payload.
- Native SObjects, Files, workers, callbacks, screenshots, and calculated
  virtual snapshots are not serialized or exposed as model roles.
- Execution reuses `CheckinOutController` and `env_inst.commit_pool`; Commit
  Queue is orchestration, not another check-in engine.

## Item identity and duplicates

- Stable identity combines the target object and prepared files, not display
  title or row index.
- Re-adding the same identity updates the existing prepared item instead of
  creating a duplicate.
- Different operations may share a target when their prepared file identity or
  operation semantics differ.

## Supported preparation operations

- Add one validated operation from Check-in/Out.
- Select one or multiple queue items.
- Edit allowed pre-run fields such as description, context, version, and
  supported versionless/filename/preview options.
- Context editing follows the original TACTIC workflow: the operation keeps the
  full `process[/branch]` value required by snapshot APIs, while the summary
  presents and edits only the optional branch. The base process is shown as
  `Add context`, not as a populated custom context.
- Repository selectors present configured display titles such as `General`
  while the operation payload retains the native TACTIC repository code such
  as `base`.
- The process pipeline owns `checkin_mode`. Sequence, directory, and multi-file
  operations start with versionless output disabled, matching the original
  check-in rules.
- Any edit that affects naming marks the item `Needs validation`. The next run
  performs full validation and does not reuse stale calculated paths.
- Remove an idle item, clear eligible items, and reorder only items that have
  not started.
- A running item remains fixed and cannot be dragged onto or merged with another
  row.

## Execution

- Run one item, checked items, or every unfinished item.
- Batch execution is sequential. Only one item uses the check-in executor at a
  time.
- An active operation id prevents double start.
- Success advances to the next eligible item.
- Failure stops the batch and leaves the item in a retryable failed state.
- Retry performs full preparation validation before execution.
- Completed entries remain visible until explicit removal or configured
  Auto-clean behavior.
- With Auto-clean enabled, successful entries are removed as they finish and
  the Commit Queue window closes only when the entire visible queue has
  completed successfully. A failed or cancelled entry keeps the window open
  for review and retry.

## Model state

Each visible item provides the display fields needed by QML, including title,
target, context, repository, checked/selected state, stage, progress, error,
and terminal status. The full operation payload remains Python-owned.

The queue supports clear empty, waiting, active, failed, and completed
presentation states. Actions disabled by active state remain visibly disabled
and cannot be triggered through keyboard, mouse, touch, or context menus.

## Progress, failure, and cancellation

- Executor progress and stage changes update the active model row and aggregate
  queue status.
- Full exceptions and tracebacks go to Debug Log; rows expose a concise
  actionable error.
- Cancel removes pending batch continuation and requests a stop at the next safe
  boundary between prepare/copy/snapshot stages.
- An already-running server call is never described as forcibly cancelled when
  the pool has no safe abort API.
- Shutdown stops scheduling new items, persists eligible pending state, and then
  follows the shared worker-pool shutdown lifecycle.

## Persistence

- Unfinished primitive payloads are stored under
  `cache/commit_queue/pending.json` through the project configuration API.
- Restored records return to Prepared state and are fully revalidated before
  execution.
- Python objects, workers, callbacks, and virtual snapshots are never persisted.
- Completed transient history is not restored as pending work.

## Refresh after completion

A successful operation refreshes only the affected snapshot/file presentation
when it is visible. Commit Queue does not reload the entire search model or
change unrelated selection state.

## QML composition

The dock uses the shared header/footer, selection color, controls, scrollbars,
menus, drag feedback, and MD3 surfaces. Document rows cannot be dropped onto
one another. Reorder feedback indicates the insertion target and preserves
scroll position.

The initial state uses progressive disclosure. With no selected operation, the
files subpanel and full operation editor are hidden and a short source hint is
shown instead. Reorder and destructive queue actions appear only when they can
operate on current rows. Selecting an operation reveals its unchanged editing
and submission workflow.

The horizontal split owns both panel widths. Layout children opt out of their
implicit minimum width where text can elide, and secondary toolbar/footer
actions become icon-only buttons below the panel's measured compact breakpoint.
Neither panel may paint or place an interactive control across the split handle.

## Automated and manual verification

Automated tests cover sequence ordering, double-start protection, failed/retry,
duplicate identity, persistence restoration, removal of completed items, and
shutdown behavior. The real QML view is also exercised at narrow width with the
Russian catalog installed; toolbar, files panel, and action footer geometry must
remain inside their owning split panel.

Verify manually with an isolated TACTIC project:

- real inplace, preallocated, and upload check-ins;
- naming, copy, upload, and snapshot failure in the middle of a batch;
- close/reopen during waiting and active stages;
- cancellation at each advertised safe boundary;
- row reorder and drag feedback at narrow and wide dock sizes;
- refresh of an open nested snapshot/file panel after success.
