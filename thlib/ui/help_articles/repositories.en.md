---
group: Workflows
icon: repository-sync
order: 18
---
# Repositories and Watch Folders

> Repository tools manage local/server paths, synchronize files, and automate folder-driven check-ins.

## Main controls

Repository Editor configures repositories. Repository Sync builds compatible process presets and
controls download scope.

Repository Sync Queue shows transfers and errors. Watch Folders lists active configurations; its
separate editor binds a selected sObject, repository paths, processes, and check-in rules.

## Usage notes

- Repository Sync uses the server's TACTIC process-preset format.
- Watch Folder removal can keep or remove repository files; read the confirmation carefully.

## Repository ownership

A TACTIC file object determines its repository identity and path semantics. Handler asks that object
for preview, local path, size and preparation data; it does not reconstruct those values from a
displayed filename. Platform mappings translate one repository to the actual Windows or Linux root.

## Repository Editor

Use the editor to inspect server definitions and add local custom mappings. Enable only reachable
locations, choose one valid default and verify paths for the current platform. Saving writes the
mapping to the active server preset; Cancel discards the editor draft.

## Repository Sync

Repository Sync begins with an object and process preset, discovers compatible snapshots and files,
then prepares explicit queue transfers. Scope controls whether versions, related children and preset
subtrees participate. Discovery does not copy files and can be cancelled without deleting anything.

The queue owns concurrency, progress, conflict policy, cancellation and retry. A completed download
is checked against response metadata rather than trusting discovery size alone.

## Watch Folders

A watched folder definition binds one explicit local root to a project and matching/check-in rules.
Monitoring finds candidates but does not bypass normal validation or Commit Queue. Disabling a
definition preserves it; deleting a definition does not implicitly delete the watched directory.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No usable repository | Configure and enable a current-platform path and a valid default. |
| Snapshot exists but local file is missing | Open Snapshot Browser or Repository Sync and queue a download. |
| Existing destination conflict | Review the conflict policy; do not assume the queue may overwrite it. |
| Discovery fails for one file | Inspect that file object's repository code and Debug Log traceback. |
| Watcher sees nothing | Verify enabled state, exact local root, project scope and matching rules. |
