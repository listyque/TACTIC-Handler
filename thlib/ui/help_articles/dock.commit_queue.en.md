---
group: Docks
icon: cloud-upload
order: 38
---
# Commit Queue dock

> Commit Queue is the final review and execution surface for prepared check-ins. The dock and the
> standalone Commit Queue window show the same application-owned queue.

## What a queue item contains

A row identifies the target sObject, process, context, files, previews, description, version plan and
preparation source. Expanding it exposes editable file and advanced options before upload.

DCC scene saves enter as preparation work: at execution time the selected client saves to the final
path, while Handler performs repository transfer and creates the TACTIC snapshot.

## Main controls

| Control | Behavior |
| --- | --- |
| Checked state | Chooses which prepared operations participate in **Send all**. |
| Auto-clear | Enabled by default; removes successful items while retaining failures for inspection. The switch remembers your choice. |
| Clear queue | Removes prepared rows after confirmation; it does not delete source files. |
| Send all | Runs every checked valid item in queue order. |
| Per-row menu | Edits, retries, removes or inspects that exact operation. |

Applying a field to checked items changes only currently checked queue identities. Removing a row
removes it completely; no hidden copy remains to influence later version calculation.

## Version and file review

The displayed version is calculated from current server snapshots and the operations still present
in this queue. Verify the prepared filename, versionless result, context, repository and preview
before sending. A server path collision is an error and is never solved by silently overwriting.

## Execution and retry

1. Expand the item and verify target, context, files and description.
2. Confirm the selected DCC client for DCC-prepared work.
3. Check the intended rows and press **Send all**, or run one row.
4. Keep failed rows, inspect their complete error and correct the cause.
5. Retry the same row only when the operation is safe to repeat.

## States and errors

- Invalid preparation cannot start and remains editable.
- A native DCC save may succeed before repository transfer or TACTIC check-in fails.
- Cancellation stops pending queue work without reporting success.
- Successful transfer does not permit a duplicate TACTIC path; version selection is refreshed before retry.
- Closing the dock does not cancel the application-owned queue.


## Server queue progress

The progress panel covers the entire submitted selection and stays visible independently of the selected row.
Preparation computes source checksums before transfer. Upload shows the current source path and counts
only files and bytes acknowledged by the server. Until all project manifests are prepared, transfer totals
remain unknown. Server check-in has its own completed/failed/cancelled counters and progress bar;
upload completion alone does not mean the snapshots have been saved.
Elapsed time and time without new progress distinguish an active transfer from a quiet wait.
When status requests fail, results remain unconfirmed and reads retry without repeating a check-in.
An interrupted upload can resume its existing batch with Retry. Closing Handler leaves accepted jobs
running on the server; after restart, the existing batches recover their authoritative results.
Before-hook checkpoints and removed rows coalesce into pending-cache saves; shutdown flushes them.
Completed server updates save once per response, preserving failed rows and Move source cleanup.
Server console INFO messages about job start and completion report normal queue activity.

Ordinary object Search tabs remain available in file projects. Managed file tables are accessed through the native file API; their schema and counts are available to administrators in Search Types. The Perforce-like workspace opens in the Commit Queue dock. It can stack with Search, move or detach through the existing dock controls. Maximize panel expands it over the working area; Restore panel restores the layout without rewriting saved split ratios. Cached project restoration selects the file interface before server refresh.
