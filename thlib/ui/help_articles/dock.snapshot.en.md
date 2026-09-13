---
group: Docks
icon: snapshot
order: 27
---
# Snapshot Browser dock

> Snapshot Browser follows the selected sObject and process, showing published versions, previews,
> files and repository state without making the DCC responsible for synchronization.

## What the dock follows

Changing the Search selection reloads snapshots for that exact object. Changing a process or context
narrows the version list. A file selection belongs to one snapshot and never changes the current
sObject by itself.

## Layout modes

The options menu provides **Preview and Files**, **Preview Only** and **Files Only**. The selected mode
is remembered. A splitter controls the space shared by preview and file list; preview work and file
state discovery run outside the UI thread.

## Version and preview controls

- Choose the context and snapshot version from the header.
- Use previous and next preview arrows to move through the selected snapshot's previewable files.
- The preview action opens the original local file or its linked object.
- Edit info opens the owning sObject editor rather than editing a detached file record.

## File table

| Column or state | Meaning |
| --- | --- |
| Files | Server filename and file role within the snapshot. |
| Size | Discovered server metadata; transfer verification still uses response metadata. |
| Path | Resolved relative or absolute repository path. |
| Repo | Configured repository selected by the file object. |
| Local / missing / different | Whether the expected local file exists and matches known server information. |

File context actions can open, reveal, copy a path, synchronize, import or reference when the selected
DCC advertises the needed capability. Menus operate on the actual file object, preserving its repository
and identity rules.

## Synchronize and open

1. Select the required snapshot and file.
2. If the local copy is missing or stale, synchronize it through Handler.
3. Verify the repository destination and any conflict message.
4. Select the intended DCC client in the top bar.
5. Use Open, Import or Reference. Handler sends the prepared local path to that exact client.

## States and errors

- **Missing local file** offers repository synchronization; the DCC client never downloads it.
- **Repository unavailable** requires a valid repository in Configuration before Open or Sync can continue.
- **Different local file** is not overwritten silently; review the synchronization choice.
- **No preview** can be valid for a snapshot containing only non-previewable files.
- If selection changes during loading, the stale preview or file response is ignored.
