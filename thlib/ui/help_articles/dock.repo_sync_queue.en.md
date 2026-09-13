---
group: Docks
icon: sync
order: 37
---
# Repository Sync Queue dock

> Repository Sync Queue shows prepared file transfers between configured repositories and the local
> workstation, including progress, conflicts, cancellation and retry.

## Queue contents

Every row retains the source file object's identity, repository, path and intended destination.
Discovery can add many files, but transfer starts only for explicit queue operations.

The queue reports waiting, running, completed, cancelled and failed states, transferred bytes and an
actionable error. Removing a queued row does not delete its source or an already completed local file.

## Controls

- Start or pause eligible queue work.
- Cancel an active or waiting transfer.
- Retry a failed item after correcting its cause.
- Remove completed or unwanted rows.
- Open the Repository Sync window to discover and prepare a broader scope.

## Conflicts and verification

Existing destination files follow the chosen conflict policy; they are never overwritten merely
because a row appeared in the queue. Snapshot metadata helps discovery, while completed HTTP
transfers are verified against response metadata.

## Typical workflow

1. Prepare files from Snapshot Browser or Repository Sync.
2. Review source repository and local destination.
3. Resolve conflict choices before starting.
4. Watch per-file and total progress.
5. Retry only after repository, path, permission or connection errors are corrected.

## Errors

- Missing repository configuration blocks the row before transfer.
- Cancellation is a normal terminal state, not an application error.
- A temporary network failure keeps the source identity for retry.
- Credentials and tokens never appear in the visible detail or Debug Log.
