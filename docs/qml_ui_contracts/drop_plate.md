# Drop Plate and Matching Templates contract

## Ownership

- `DropPlateController` owns path intake, asynchronous directory scanning,
  deduplication, MatchTemplate grouping, Python FileObject identity, selection,
  process/context assignment, and preparation for Commit Queue.
- `MatchingTemplatesController` owns the ordered template catalog, validation,
  editing session, persistence, and rematch notification.
- QML owns only presentation and interaction. It never walks directories,
  evaluates matching expressions, or stores native FileObjects.
- Check-in naming and repository target resolution remain in
  `CheckinOutController`. Drop Plate does not create a separate queue or commit
  directly.

## File intake

- Shared file and folder dialogs and DropArea pass local URLs to Python.
- Directory scanning, recursive collection, metadata inspection, and matching
  run in `env_inst.local_pool`.
- Stale scan/rematch results are ignored by request identity.
- Duplicate physical source identities are rejected before model mutation.
- Inaccessible paths and scan failures produce visible per-group or operation
  errors rather than disappearing silently.
- Symlink/reparse handling must avoid recursion loops and unintended traversal.

## Group model

The QML-safe group model exposes stable `groupId` and presentation roles such
as display path/name, source count, total size, matching type, extension,
frame range, UV/UDIM tiles, layer summary, process, context, checked state,
loading state, and error.

Native FileObjects and full source metadata remain in Python under `groupId`.
Rows may be removed or cleared without leaving stale indexes. Scroll and
selection remain stable while asynchronous metadata arrives.

## Sequences and grouping

- Matching supports the verified MatchTemplate vocabulary for individual files,
  frame sequences, UV, UDIM, layer, and combined forms.
- Configured template priority is preserved through ordered deduplication.
- Grouped and individual check-in semantics are explicit in the prepared
  payload.
- Save Snapshot and item drops containing multiple input files require a
  per-batch choice before preparation. Grouped mode emits one operation for
  each process/context target; separate mode emits matched groups in source
  order. The choice does not persist or alter the Drop Plate default.
- Padding comes from the active matching/check-in configuration; it is not
  hardcoded in QML.
- Process and context come from the current Check-in target and may be adjusted
  through supported controller choices.

## Commit Queue handoff

Checked groups are converted into serializable preparation payloads containing
source paths, selected template identity, safe metadata, process, and context.
They are added to the existing `CommitQueueController`.

Drop Plate never starts check-in itself. Queue duplicate checks run again on
the final stable operation identity. Successful queue completion may clear or
uncheck groups according to the active user setting.

## Matching Templates Editor

The native functional window provides:

- create and duplicate;
- pattern editing and filename test;
- enable/disable;
- ordered priority;
- process/context mapping;
- delete for non-required templates;
- Save and Cancel.

Required `$FILENAME` and `$FILENAME.$EXT` templates cannot be removed or
disabled. Patterns retain native MatchTemplate syntax; QML does not translate
them into a second expression language.

Save persists the ordered project template list through the configuration API
and emits `templatesChanged`. Open Drop Plate groups are rematched
asynchronously from their original paths. Cancel restores the last saved
version and does not rematch.

## QML behavior

- The dock uses shared controls, selection state, scrollbars, loading/error
  indicators, drag feedback, and symmetric spacing.
- File/folder drop feedback clearly identifies the accepted action.
- Add, remove, clear, template editor, process/context, and queue actions are
  real controller commands, not notice-only placeholders.
- A compact layout preserves primary actions and moves secondary actions into
  the semantic overflow menu.
- Row height and delegate creation remain bounded for large scans.

## Automated verification

Tests cover recursive collection, loop-safe path handling, deduplication,
sequence/UV/UDIM/layer grouping, stable priority, CRUD validation, Save/Cancel,
pattern testing, payload serialization, rematch generation, Python syntax, and
QML offscreen loading.

## Manual acceptance

Use an isolated directory and test project to verify:

- large and nested directories, reparse points, and inaccessible paths;
- mixed individual files, sequences, layers, UV, and UDIM with supported
  padding;
- conflicting enabled templates and equal names from different directories;
- repeated drag/drop and removal while scanning;
- process/context mapping and grouped versus individual queue payloads;
- rematch of a large open Drop Plate after template Save;
- real sequence check-in through Commit Queue;
- minimum-width layout, scrollbars, and drag feedback.
