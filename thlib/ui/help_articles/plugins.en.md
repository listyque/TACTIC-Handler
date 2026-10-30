---
order: 39
---
# Plugins

Open **Administration → Plugins** and choose the target project. The catalogue
shows packages in the configured plugin and built-in directories, their versions
and activation state. Search by title, code or path; **Active in this project**
filters the catalogue. The arrow collapses the catalogue.

**New** creates a development package. Enter its title, unique code and
description, then choose **Create plugin**. Empty, Widget, Column and Theme keep
the original native package types; widget configuration starts with the modern
reusable item-layout format. Project template exports the selected project using
the existing template creator. These packages use existing renderers; installing
a package does not add a new compiled QML/Vue renderer.

**Install plugin → Browse ZIP** uploads a ZIP through Handler's existing TACTIC
client. A URL can instead download a ZIP on the server, optionally checked with
SHA-256 or MD5. Installing only adds the package; **Activate** separately applies
its manifest to the selected business project. Packages contain trusted server
code, so only administrators with script-execution permission can change them.
Built-in package files are read-only, but their project activation is available.

- **Information** edits the title and description. Existing code/version cannot
  be changed in place. Save or discard edits before changing tabs or packages.
- **Manifest XML** uses the house source editor with find, replace and undo.
  Save changes the file; activation/reload applies its declared project data.
- **Files** browses folders, edits UTF-8 text, uploads/downloads individual files,
  creates files/folders, renames or moves relative paths and deletes entries.
  **Replace file** confirms replacing the selected file with a local upload.
  The parent-folder button navigates back. Editing is limited to 2 MiB; binary
  or larger files can be downloaded. File upload preserves ZIPs as files; use
  Install plugin to extract a package. The manifest cannot be renamed/deleted.
- **Documentation** opens existing `doc/index.html` or README text, or creates
  `README.md`. It is editable source, not automatically executed plugin HTML.
- **Export ZIP** regenerates manifest-defined exports using native PluginCreator
  and opens the resulting download. **Publish version** copies to a new version
  directory and exports it. It never overwrites an existing version or activates
  it automatically. DEV cannot be published as a release version.
- **Reload plugin** removes/reinstalls the current project's plugin. **Remove
  from project** and **Clean project data** delete manifest-defined project data;
  read their confirmation before continuing. Files remain on the server.
- **Clear .spt files** removes generated dump files after confirmation. **Delete
  package** removes the package and matching archives only when no project uses it.

Every write uses the server's existing Command/file/database journal. Concurrent
changes reject stale saves. After an interrupted request, refresh and inspect the
server result before retrying; no installation or script is retried automatically.
Handler runs upload/RPC work off the GUI thread and does not poll while idle.

The manager uses the installed native backend's manifest support. Legacy SQL
views, unknown manifest nodes and nested-plugin export remain explicit backend
errors; unsupported contents are never reported as successfully installed.
