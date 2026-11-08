---
group: Workflows
icon: publish
order: 16
---
# Commit Queue

**Server queue** is available only after TACTIC Stream is confirmed for the
current connection. Legacy uses client check-in. Previously saved remote batches
remain stored until you reconnect to their Stream server; switching to Legacy
does not resubmit or cancel them.

An interrupted server worker can report **Result unknown**. Check the target
in Snapshot Browser before preparing a new publication. Retry is unavailable
for this result.

> Commit Queue is the final review and execution point for prepared check-ins. Nothing is submitted
> merely by adding it: select an operation, verify its files and destination, then choose a commit
> action.

## Queue toolbar

| Control | What it does |
| --- | --- |
| **Help** | Opens this article. |
| **Auto-clean** | Removes each successful operation automatically. Failed or cancelled operations remain for diagnosis or retry. |
| **Move operation up / down** | Changes execution order for the selected queue row. The buttons appear only when more than one operation exists. |
| **Clear completed** | Removes completed rows and leaves prepared, running, failed, and cancelled work untouched. |
| **Clear queue** | Removes every prepared, failed, and completed operation after confirmation. It does not submit anything. |

Each queue row shows its check state, target, context, file count, status, and progress. Select a row
to edit it. The close button removes only that operation. Checked rows are used by **Commit selected**
and by batch editing; selecting a row is not the same as checking it.

## Files pane

The lower-left pane lists source files belonging to the selected operation. Its close button removes
that file from this operation only. Removing the last required file can make an operation invalid;
the source file on disk is not deleted.

## Operation summary and previews

The summary identifies the target object and snapshot status. **Add context** edits only the branch
below the base process. Preview actions are:

| Action | Result |
| --- | --- |
| **Capture screenshot** | Opens Screenshot Maker and attaches the captured image to this operation. |
| **Choose preview images** | Selects one or more existing images. |
| **Paste preview image from clipboard** | Adds the current clipboard image when one is available. |
| **Manage selected previews** | Opens the full preview list, where an individual image can be removed. |
| **Clear operation previews** | Removes all attached previews from the operation, not from disk. |

At narrow widths, secondary preview actions move into the three-dot menu without changing their
behavior.

## Basic and advanced settings

**Description** becomes snapshot metadata. **Advanced options** exposes:

| Field | Meaning |
| --- | --- |
| **Repository** | Destination repository. Titles are shown to the user; native TACTIC codes remain internal. |
| **Version** | Explicit numeric version. Leave it empty or zero when automatic allocation should be used. |
| **Method** | Preallocate, In-Place, Copy, Move, or Upload transfer contract for this operation. |
| **Filename** | Explicit destination name. Leave it empty to use naming rules; it is disabled when context is the filename. |
| **Update versionless** | Refreshes the versionless/latest snapshot along with the numbered version. |
| **Commit versionless only** | Produces only the versionless result. |
| **Keep source filename** | Preserves source names instead of applying generated names. |
| **Use context as filename** | Derives the filename from snapshot context. |
| **Generate previews** | Produces supported thumbnail and preview derivatives. |

When **Apply every edit to checked items** is enabled, every change below it applies to the current
operation and all checked rows. Review the checked set before editing.

## Naming preview

The filename row expands to show the source name plus predicted versioned and versionless paths for
every file. **Naming Editor** changes the templates used to generate them. A waiting label means the
operation has not produced a naming preview yet; it is not a committed path.

## Starting and controlling work

| Control | What it does |
| --- | --- |
| **Commit all** | Starts every ready operation in queue order. |
| **More send actions → Commit current** | Starts only the selected operation. |
| **More send actions → Commit selected** | Starts checked ready operations. |
| **Cancel** | Requests cancellation of the running work. |
| **Retry** | Re-runs a failed or cancelled operation after its cause is corrected. |

A duplicate prompt pauses preparation: **Replace** targets the matching item, **Add another** keeps a
separate duplicate, and **Ignore duplicate** dismisses that duplicate decision. Read the operation
error before retrying; the queue keeps full failure details rather than treating a failed row as
completed.


## Optional server queue in Tactic Handler

In the desktop Handler Commit Queue, **Server queue** sends file parts and
metadata to TACTIC Stream. It is off by default; the existing client check-in path remains
available.

- Chunks contain up to 50 parts or 32 MiB; a large file is split into 16 MiB parts.
- One native check-in starts only after all its files arrive. Several check-ins share a
  batch, and one status request reads changes for all active batches once per second.
- Native server naming allocates actual versions and filenames when each operation runs.
  There is no per-operation client naming/start/save/finish RPC chain in this mode.
- The existing `sthpw/queue`, `Queue` and `JobTask` execute the fixed check-in command
  sequentially. Enable the existing **queue service** in Server Configuration and restart
  the monitor after updating the server. No new broker or changelist table is installed.
- Jobs execute as their submitting user. Project, parent, repository and Python script
  grants are checked again when the job runs; administrator polling does not elevate it.
  Native callbacks, triggers, SQL rollback and repository file history are retained.
  Upload progress itself is persisted without duplicating the manifest into Undo history.
- Accepted chunk identities survive client restarts. After an interrupted upload, **Retry**
  resends the original batch and identical chunks, rather than starting another check-in.
  Closing Handler leaves accepted work on the server; reopening recovers its results.
- **Cancel** rejects further parts and stops unstarted operations. An operation already
  running completes normally. Worker failure produces an error requiring inspection;
  mutating scripts are never retried automatically because external effects may remain.
- Copy keeps source files. Move removes them only after successful server confirmation
  and a second checksum check. Changed source files are kept with an error message.
- DCC scene preparation, non-file snapshots and client-only repositories use legacy mode.
  A batch is limited to 2,000 operations / 10,000 files; multipart metadata is limited to
  1 MiB per field and the whole HTTP request to 64 MiB. This is not a 100,000-file promise.

The fixed endpoints are `/admin/checkin-queue/submit` (multipart parts plus a JSON manifest),
`/admin/checkin-queue/updates` (all batch ids plus revision cursors), and
`/admin/checkin-queue/cancel` (one batch id). All require a ticket and project. Results belong
only to the submitting user. `api_method_restricted` and `api_cmd_restricted` still apply.
Failed and incomplete staging data remains under the configured temporary directory for
inspection; successful staging files are removed after commit. Native cross-database
partial commits and effects outside TACTIC are not covered by a distributed transaction.

The server queue accepts a single group above 1,000 files within the existing 10,000-file batch limit.
This requires the updated server; the browser matching limit remains 1,000 files.

## Preparing many Separate files

Separate adds the selected operations with one queue-model insertion and one pending-cache save.
Legacy naming preview runs in portions of up to 50 operations, with one portion in flight.
Each file still executes its own native naming rules and callbacks; results are not shared or cached across files.
Editing a row invalidates its older response. Removing a row does not start further previews for it; shutting down Handler stops dispatching new portions.
Preview updates coalesce into cache saves; closing Handler flushes pending state.
A local preparation failure affects that row. A server naming failure aborts its whole request portion
through the native transaction, including callback writes; other portions can continue. Fix the cause before retrying.
Actual legacy check-in resolves naming again, so the preview reserves neither a version nor a final path.
With **Server queue** enabled there are no client virtual-snapshot preview requests.
Restart Handler after updating. If Server Queries uses the optional plugin mode, deploy the matching query plugin from the updated client.


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

Explicitly clearing an idle queue also resets its overall progress. Clear queue remains available when automatic cleanup has removed every row but the final counters are still shown. Clearing the last completed rows also hides the progress panel. Automatic cleanup itself retains the final counters; active server jobs keep their progress and recovery state.

The horizontal splitter position is saved after releasing the handle and restored when the window or application reopens. Narrowing the window temporarily limits panel widths without replacing your saved split; widening restores it. Auto-clean has its own row below the toolbar. In a narrow details panel, Commit all uses its icon with a tooltip so send actions stay visible.

## Refreshing results while the queue runs

In both ordinary and server queue modes, file progress, operation results and errors update as work proceeds. The result tree, Snapshot Browser, task summaries and Search Type previews refresh after the entire running selection finishes or stops. Successful check-ins are combined by object/context, and client data caches are invalidated once per affected project. Completion hooks and API results still run for each saved snapshot.

Cancellation waits for the active operation to reach its safe stopping point before refreshing confirmed results. If a later operation fails, earlier successful saves still become visible. A failed server status request refreshes already confirmed saves; unknown outcomes keep their recovery state and continue status polling without repeating check-ins. Move source cleanup is part of completion.

Automatic background server polling pauses during queue execution, including activity and notification updates; these catch up when execution stops. Queue status polling continues to report progress. A background response already in flight is retained until resume, and its cache cursor is saved only after delivery. Signing out or changing the project discards obsolete deferred responses.

## Versionless behavior

For `multi_file`, `dir` and `sequence` check-ins, and grouped Drop Plate operations, both versionless controls are disabled. Only the numbered snapshot and its files are saved, in both legacy and server queue modes. Ordinary file check-ins keep the selected versionless preferences. Editing all checked items cannot enable versionless on an incompatible operation. Previously submitted server work keeps its original contract.

## Narrow docks and session changes

In a narrow dock, switch between **QUEUE** and **Operation details**. The QUEUE
page contains the selected operation's source files, **Choose source files
again** and **Directory**. After a browser reload, choose the same paths and
file sizes before returning to Operation details to send the operation.

A delayed clipboard, screen-capture or validation result belongs to the session
and operation that started it. It cannot change another account's queue. A
renewed browser session retains the same user's selected local files; an
interrupted upload can be retried. If the session changes while a publication
reply is pending, its result is unknown: inspect Snapshot Browser before
preparing another publication. The queue does not automatically repeat that write.
