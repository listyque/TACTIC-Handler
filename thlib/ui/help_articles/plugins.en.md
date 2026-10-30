---
order: 39
---
# Plugins

Open **Administration → Plugins** and select the target project. The manager has
three steps: **Choose a package → Review its contents → Activate in project**.
A package is stored on the server; activation applies its manifest to one project.
The empty catalogue opens a getting-started screen, without an empty sidebar.
**Plugin guide** in the header opens these instructions at any time.

## Install a ready-made package

1. Choose **Install a package**. Select **ZIP file** to upload from this computer,
   or **Download link** to let the server fetch a URL. A package ZIP must contain
   `manifest.xml` and the plugin files. A publisher's SHA-256 or MD5 checksum is
   optional for URL downloads.
2. After upload, the package's **Overview** opens. Read its **Documentation** and
   inspect **Manifest XML**. Installing the files alone does not activate anything.
3. Choose **Review activation**. Check the package and project in the confirmation,
   then **Activate**. The manifest may create/change project data and run server
   code. The resulting status shows whether activation completed.

Activation requires a business project, not the `admin` or `sthpw` system project.
Only administrators with script-execution permission can change packages. Built-in
files are read-only; built-in package activation is still available.

## Create your own plugin

### Installable example: Workspace Pulse

`TS/examples/workspace_pulse` contains a complete reusable plugin. Build its ZIP
with `TS/tactic_stream/tools/build_workspace_pulse.py`, then install and activate
it through this manager. **Pulse** provides current-project task/deadline counters,
shared filters, charts and a searchable task queue. **VFX overview** discovers the
project's existing episode/scene/shot/asset types. Both pages use the existing
sidebar and native dashboard renderer in TH and TS, and remain editable through
the Page Editor and the internal agent. It creates no sample records or services.
Remove/Reload affects its configurations; export custom page edits first.

### Start a new package

1. Choose **Create your own plugin** on the start screen, or **New** in the catalogue.
2. Enter a title and unique code, for example `studio_tools`. Codes use letters,
   digits, underscores or hyphens; slash-separated package paths are also supported.
   Select a type and add a description. The Create and Cancel buttons remain visible
   while you scroll through the form.
3. **Create plugin** creates a DEV package and registers it as active in the selected
   project. **Overview** shows the actual result. Add files, documentation and manifest
   entries using the editor sections below.
4. Save your changes. To apply changed manifest data to the project, choose
   **More actions → Reload plugin** and read the confirmation. Saving a file and
   reloading a plugin are different operations.
5. Use **Export ZIP** to share the current package, or **Publish version** to create
   a separate release directory and ZIP. Publishing never overwrites a version or
   activates it automatically; DEV is not a release version.

Empty, Widget, Column and Theme retain the native package types. Widget starts
with a modern reusable item layout. Packages use existing renderers; installation
does not add a compiled QML/Vue renderer. **Project template** exports the selected
project through the native template creator instead of creating/activating a plugin.

## Edit and maintain packages

The catalogue shows title, version, path and project activation state. Search by
title/code/path, filter **Active in this project**, or collapse the catalogue.
Save or discard changes before changing a package or editor section. Save/Discard
appear in the header only when needed; a blocked or interrupted write requires
refreshing and checking the server result before trying again.

- **Overview** shows project activation, review links, distribution and package details.
- **Package details** edits the title and description. Existing code/version cannot
  change in place; use publication for a new version.
- **Manifest XML** uses the house source editor with find, replace and undo.
  Save changes the file; activation/reload applies its declared project data.
- **Files** browses folders, edits UTF-8 text, uploads/downloads files, creates
  files/folders, renames/moves relative paths and deletes entries. Replace file
  confirms overwriting the selected file with a local upload. The parent arrow
  returns to the containing folder. Text editing is limited to 2 MiB; download
  binary/larger files to edit locally. Uploading a ZIP here keeps it as a file;
  use Install a package to extract a plugin. The manifest cannot be renamed/deleted.
- **Documentation** opens existing `doc/index.html` or README source, or creates
  `README.md`. Legacy HTML is not executed in this editor.
- **More actions** contains Reload plugin, Remove from project, Clean project data,
  Clear .spt files and Delete package, as applicable. Reload removes/reinstalls
  project data. Remove/Clean delete manifest-defined data; package files stay on
  the server. Clear .spt removes generated dump files. Delete package removes its
  files/archives only when no project uses it. Each destructive operation explains
  its scope and requires confirmation.

Writes use the existing native Command/file/database journal; stale changes are
rejected. Installation and scripts are never retried automatically. The browser
uses authenticated PluginManagerCmd RPC and UploadServer; Handler uses the native
client transport. Both clients share the same Frame layout/state and do not poll
while idle. URL downloads and package files belong to the selected server.

Legacy SQL views, unknown manifest nodes and nested-plugin export remain explicit
backend errors; unsupported content is never reported as successfully installed.
