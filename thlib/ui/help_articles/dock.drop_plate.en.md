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
