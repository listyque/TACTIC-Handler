---
group: Configuration
icon: database
order: 31
---
# Repository configuration

> Repository configuration maps TACTIC storage locations to paths available on this workstation.
> Snapshots, previews, check-in, check-out, and Repository Sync depend on these paths.

## Repository storage

The status card shows the current default repository and its path for the running platform. **Setup
required** means no usable default path is available; **Configured** means the current mapping can be
used; **Loading** means server repository definitions are still being read.

| Control | What it does |
| --- | --- |
| **Open Repository Editor** | Opens all repository definitions for editing. |
| **Check paths** | Creates missing directories for enabled current-platform paths, then checks access and updates each status. Creation failures show the filesystem error. Blank paths are rejected. |
| **Active repositories** | Lists enabled repositories, their native TACTIC codes, current-platform paths, default marker, and last path-check result. |

## Repository Editor fields

Local is disabled by default for new repository settings. Existing saved enablement is preserved.

| Field | Meaning |
| --- | --- |
| **Add custom repository** | Adds a local draft repository definition. Server-provided definitions remain intact. |
| **Enabled** | Makes this location available to file operations and repository selectors. |
| **Default** | Destination used when an operation does not explicitly choose another repository. Only one enabled repository should be the default. |
| **Display name** | User-facing label for a custom repository. It does not replace the native server code. |
| **Windows path / Linux path** | Absolute platform-specific root for the same TACTIC repository. Configure only paths that genuinely point to that storage. |
| **Remove custom repository** | Removes only the selected custom draft; built-in server definitions cannot be deleted here. |
| **Project mappings** | Shows which projects and server definitions use the location. These are diagnostics, not names to rewrite locally. |
| **Save / Cancel** | Save writes the mappings into the active server preset; Cancel closes without writing the drafts. |

If the active server preset has no usable default repository, TACTIC Handler offers this page once
per launch. Choosing **Later** postpones setup; it does not mark the repository as configured.

## Waiting for a repository

If a local repository root is blank, relative or unavailable, background previews
and Repository Sync wait for repository setup. No HTTP download or automatic
root-directory creation is attempted, and this expected state does not add
repeated download errors to Notifications or Debug Log. Other available
repositories continue working.

Open **Repository Editor**, select an absolute local folder and save the mapping.
Use **Check paths** to create/check the folder explicitly. After the configuration
is applied, previews are requested using the current paths and transfers waiting
in the sync queue resume with their existing file identity. Repeated refreshes
or Retry do not retry an unavailable root until repository configuration is
applied. Real transfer errors with an available root remain visible.

## Local paths and saving

The server's `/opt/...` path is server metadata, not a Windows repository folder.
Handler keeps valid local mappings on reload and leaves an incompatible server
default unset. A missing local folder shows a static preview placeholder, not an
endless loading animation, while it waits for configuration.

On Windows, edit **Windows path** in Repository Editor, select the intended
**Default**, and click **Save**. Saving checks and creates the entered folder in
a background worker; the UI stays responsive. Only changed/enabled paths and the
default location need checking. An unrelated unchanged unavailable mapping does
not prevent saving the folder you are configuring. If creation/access fails, the
previous mapping remains in use and the editor displays the reason. Settings
are written after validation and remain saved after restarting/reloading.
The separate **Check paths** action is optional.
