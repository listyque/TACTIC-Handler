# Watch Folders and Repository Editor contract

Historical visual-only implementation notes were removed. The controllers and
views below are the authoritative current workflow.

## Repository Editor

`RepositoryEditorController` and `RepositoryEditorView` edit the repository
configuration returned by `env_tactic.get_base_dirs()`. QML does not maintain a
second repository store.

Supported records include base, client, local, sandbox, and handoff
repositories, platform-specific paths, enabled state, default selection,
display name, and theme color.

- Validation runs through the local worker pool and checks directory existence
  and the required read/write access without recursively scanning content.
- An enabled invalid path remains visible and blocks Save with an actionable
  error.
- Save calls `env_tactic.save_base_dirs()`. The default repository uses the
  existing `repositoryComboBox` configuration key.
- Cancel discards the working copy and does not mutate the environment.
- After Save, Check-in/Out reloads repository choices and recomputes naming
  preview.
- The editor never changes an active Repository Sync task's resolved path.

Cross-platform paths, network shares, and repository changes during an active
operation require manual acceptance testing.

## Watch Folder ownership

`WatchFoldersController` and `WatchFoldersView` own the project Watch Folder
list, editing sessions, persistence, watcher lifecycle, manual scan, and
handoff to Drop Plate.

- The manager and item editor are separate native modal/resizable windows.
- The manager lists every enabled and disabled Watch Folder for the project.
- Clicking a row selects it; it does not open the editor implicitly.
- Edit opens the current record with its SObject already resolved.
- An item action on an existing Watch Folder edits that record rather than
  proposing an unrelated duplicate.
- Add is available only through an action with a complete target context; a
  decorative or nonfunctional plus button is not shown.

## Persistent format

Records use the project configuration API under `ui_watch_folder` and the
existing project-specific `watch_folders_dict` key.

The data includes stable target identity, title, Search Type, search key,
pipeline, relative path, repository codes, enabled state, process, context,
matching template, last check, and error. Independent controllers do not keep
unsynchronized copies of this dictionary.

## Editor validation

- The target SObject, project, pipeline/process/context, relative path, matching
  template, and one or more enabled repositories are explicit.
- Relative paths cannot be absolute, contain escaping `..` segments, or resolve
  outside a selected repository root.
- Duplicate target/path/repository identities are rejected.
- Removing the last repository from an existing record and saving removes the
  Watch Folder configuration while keeping repository directories and files.
- Availability and directory creation run in the local worker pool.
- Filesystem deletion resolves and verifies every absolute target under an
  intended repository before any destructive operation.
- Delete confirmation offers meaningful choices only: remove the configuration
  record, or remove the record and verified directories when that destructive
  option is valid. Cancel remains the dialog close path, not a third ambiguous
  action button.

## Watcher lifecycle

Each enabled record may be in Watching, Waiting, Stopped, or Error state.

- `Waiting` is a temporary bootstrap state when repository configuration is not
  loaded yet or the target/path is not currently resolvable.
- A missing or invalid repository code is an error, not infinite bootstrap.
- When repository configuration becomes available, waiting records are retried
  without losing saved rows.
- A record creates one recursive native watch for each selected repository path.
- Disable/remove detaches its watches. Project change and application shutdown
  stop the controller-owned observer deterministically.
- The global environment repository API is not patched to solve controller
  lifecycle timing.

## File events and scans

Created/moved files and manual recursive scan results are sent to
`DropPlateController`, where the active Matching Templates are applied.

- Watch Folders do not commit automatically.
- Event handling includes stability/debounce protection so a file still being
  written is not prepared prematurely.
- Directory scans, file inspection, and grouping run outside the GUI thread.
- Repeated event identity is deduplicated.
- Processing and errors are reflected in controller state and Debug Log.

## QML boundary

QML receives primitive roles and stable ids only. Native watcher objects,
SObjects, repository objects, FileObjects, and workers remain in Python.
Server-configured project/Search Type/process/context labels are displayed
unchanged.

## Verification

Automated tests cover early bootstrap with `base_dirs=None`, retry after
configuration load, invalid repository codes, CRUD identity, duplicate
prevention, enable/disable lifecycle, shutdown, configuration persistence, and
QML creation.

Manual tests cover network and read-only repositories, identical relative paths
in several repositories, slowly written sequence files, project switching,
active observer shutdown, and destructive removal containment.
