---
group: Configuration
icon: movie
order: 38
---
# Maya Scene configuration

> Maya Scene configuration controls defaults used by the connected Maya integration when it opens,
> saves, or prepares a scene for the standalone check-in workflow.

## Maya scene environment

| Setting | What it controls |
| --- | --- |
| **Current work directory** | Read-only project root reported by the selected Maya client when it connects. It updates when Handler reads the scene again and clears when that client disconnects. **No work directory selected** means no workspace has been reported. |
| **Maya saving format** | Default Maya ASCII or Maya Binary format offered when Maya prepares a scene for check-in. It does not convert an already opened scene by itself. |
| **Create Maya directories** | Prepares the standard Maya project folder structure when the check-in workflow requests it. |
| **Create playblast** | Prepares a Maya playblast image for the snapshot when the source workflow supports a playblast. |

## Window behavior

**Return focus after opening a scene** brings Maya to the foreground after open, import, or reference.
**Return focus after saving a scene** does the same after a save or check-in preparation. Disable a
switch when you want to remain in TACTIC Handler after that action.

These settings affect Maya DCC actions only. TACTIC Handler remains responsible for repository and
check-in work after Maya returns its preparation result.
