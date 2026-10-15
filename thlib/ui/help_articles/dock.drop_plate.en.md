---
group: Docks
icon: move-to-inbox
order: 36
---
# Drop Plate dock

> Drop Plate turns local files and folders into explicit, reviewable check-in operations and sends
> only valid prepared rows to Commit Queue.

## Add files

Drop paths onto the plate, use **Add files**, choose a directory, or paste paths. Directory scanning
can include subfolders. Added entries remain local preparation data until they are sent to the queue.

## Preparation options

| Option | Effect |
| --- | --- |
| Include subfolders | Recursively discovers files below an added directory. |
| Group check-in | Prepares compatible files as one check-in operation. |
| Keep filename | Preserves the source filename instead of applying a naming template. |
| Extension filter | Limits visible or selected candidates by file type. |

Grouping is explicit. Dropping one queue document onto another does not merge operations.

## Match and review

Select the target sObject and process, then review every row's matching result. The plate shows file
groups, checked selection, target, context, type and any naming or validation message. Remove invalid
or unwanted rows before queueing.

A prepared file can be edited without changing the original on disk. Matching Templates and Naming
Editor own reusable server rules; Drop Plate only applies the selected rule to this preparation.

## Send to Commit Queue

1. Select the intended target in Search.
2. Add files or a directory.
3. Choose grouping and filename behavior.
4. Review matches and uncheck unwanted rows.
5. Correct every validation error.
6. Send valid operations to Commit Queue for final context, description and upload review.

## States and errors

- **No target** prevents queueing because the files have no TACTIC owner.
- Unsupported or unmatched files remain visible with an actionable message.
- Removing a prepared row removes it from this plate; it does not delete the source file.
- A directory scan or match request runs outside the UI thread and ignores stale results after scope changes.
- Commit Queue remains the owner of transfer, retry and final check-in.

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

## Versionless behavior

A grouped operation saves only a numbered snapshot, without latest/versionless copies. The same applies to the legacy `multi_file`, `dir` and `sequence` check-in types. Grouping retains the existing source-name and naming-template behavior. Separate ordinary file operations keep their versionless preference.
