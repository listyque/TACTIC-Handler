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
| **Check paths** | Tests every enabled path for the current platform and updates each status. It does not create missing directories. |
| **Active repositories** | Lists enabled repositories, their native TACTIC codes, current-platform paths, default marker, and last path-check result. |

## Repository Editor fields

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
