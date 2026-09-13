# Release acceptance checklist

This checklist covers behavior that cannot be verified honestly by offline
smoke tests. Perform every change in an isolated `th_test_*` project and test
repository. Never use production projects.

Record each group through `tests/record_release_acceptance.py`, including the
reviewer name, UTC time, and concrete evidence such as a log, screenshot,
created object codes, or environment description.

## Session and navigation

- Sign in with a valid ticket, sign out, and sign in again.
- Switch the server preset and confirm that the old ticket is not reused.
- Open a project, run a search, and navigate through both `skey` and `code`.
- Verify an existing filtered search tab and fallback to a new suitable tab.
- Simulate connection loss and confirm that the UI recovers without resetting
  user settings.

## Server procedure compatibility

- Run `tests/run_live_server_procedure_smoke.py` on a supported server.
- Confirm task workspace, conversations, user activity, and batched server
  updates execute without server-side `SyntaxError`, `Undefined`, or API
  differences.
- Store the TACTIC and server-side Python versions in the evidence.

## Server mutations

- Create, edit, link, and delete a test SObject through the standard API.
- Create and edit a task, milestone, work-hour record, and note.
- Send, edit, delete, and read a chat message; verify reply, pin, reaction, and
  attachment metadata.
- Edit a test user and their groups with an authorized account.
- Repeat a forbidden action as a regular user and verify an actionable error.
- Refresh the relevant view after every operation and verify the committed
  server value, not only optimistic state.

## Files, repository, and check-in

- Verify platform mapping and creation of missing repository directories.
- Download an HTTP preview/file, validate response size, and verify reuse of
  the local file.
- Exercise Check-in, Check-out, Commit Queue, and Drop Plate for a single file,
  a sequence, and a grouped operation.
- Verify screenshots, clipboard previews, generated previews, and naming
  results.
- Cancel and retry a transfer, and close its window while it is active.
- Confirm retry does not duplicate a snapshot or path and that completed queue
  entries follow Auto-clean.

## Windows lifecycle

- Open, close, and reopen each major window at least twice.
- Verify minimum sizes, dock resize/stack/float/reset, and geometry restoration.
- Close the main window with a connected DCC client and restore it from the
  system tray.
- Close the application during server polling, Repository Sync, and a worker
  operation.
- Restart and confirm saved settings without changing unrelated keys.

## Clean environment

- Run `tests/run_clean_environment_smoke.py` on a clean supported Python.
- Confirm installation uses only `requirements.txt` or the controlled
  wheelhouse.
- Start `launch.py` and `launch.pyw` from a different working directory.
- Store Python, PySide6, and Windows versions in the evidence.

## Maya thin client

- Start standalone without manually entering an endpoint, then connect one and
  multiple Maya clients.
- Verify discovery, active-client switching, capabilities, disconnect, and
  reconnect.
- Exercise open, import, reference, save, current scene, and playblast
  preparation.
- Confirm TACTIC upload remains in standalone and Maya receives only fixed
  native actions.
- Verify timeout, structured error, and request id in the shared Debug Log.

## Visual and localization

- Verify dark and light themes and both English and Russian UI.
- Confirm server, project, Search Type, process, and status names are not
  translated as static application strings.
- Verify wide, ordinary, and minimum widths without overlaps or unreachable
  actions.
- Verify pointing-hand cursors for active controls and text cursors for input
  fields.
- Run QML with a clean log and confirm there are no binding, property, or
  handler warnings.

## Release candidate command

```powershell
python tests/run_release_gate.py --require-manual `
  --manual-results .release/acceptance.json
```

A group that has not passed does not by itself indicate poor architecture. It
means evidence is missing for that environment or the scenario has a confirmed
defect.
