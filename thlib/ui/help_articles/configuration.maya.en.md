---
group: Configuration
icon: movie
order: 38
---
# Maya Scene configuration

## Maya integration

Select **Find Maya** to list installed Windows Maya versions, running processes,
existing version profiles, and the Stream integration registered for each profile.
Select a row and choose **Integrate into Maya**. Python 3 Maya (2022 and newer) is
required. Detection uses Autodesk installation locations, running executable paths,
and the current user's Maya profiles; `MAYA_APP_DIR` is respected.

The integration adds a separate **TACTIC_Stream** shelf with a Handler launch
button and an isolated module startup script for the connector. Existing startup
scripts, legacy shelves and custom scripts are preserved. Maya may ask you to trust
the new startup script according to its own security settings.
The launch button uses Handler's orange T logo with a TH overlay. Startup restores
that appearance only on owned launch buttons. After upgrading an existing
registration, select **Integrate into Maya** again and restart Maya to refresh it.

Changes apply on the next Maya start. The connector waits for this exact Handler
installation without launching it or opening its window automatically. The shelf
button opens the connected Handler, or starts the adjacent portable EXE. Update
Handler in place to retain the registration; after moving it, integrate again.
Multiple Handler installations do not share the connection. If another Handler
SDK is already loaded in Maya, save work and restart Maya before switching.

**Remove integration** removes only the files owned by this integration. Modified
integration files or a foreign shelf using the same name are preserved and reported.
Close Maya before removal so its open process cannot save a deleted shelf again.
Installation can be prepared while Maya is running and applies on its next start.
Existing processes are not injected into or restarted. Integration changes are applied immediately by these
buttons and are independent of the Configuration page's Apply/Discard actions.

Automatic discovery and portable EXE launching are Windows desktop features;
there is no browser/TACTIC Stream equivalent.

This entire integration belongs to the Maya DCC plugin. Enable or disable it on
**Configuration → DCC plugins**; plugin selection takes effect after restarting
Handler. Remove Maya registrations before disabling the plugin if they are no
longer needed; disabling a plugin does not delete external files or user data.

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
