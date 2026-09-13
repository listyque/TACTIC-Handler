# Tools menu

Open the catalog through `…` → **Tools**. This menu is a temporary home for
surfaces that do not yet have a normal task-specific entry point. It is not a
second catalog of every window in the application.

Windows already reachable from the top bar, application menu, Configuration,
Administration, workspace panels, result actions, item context menus, or check-in
workflows must not be repeated here. Removing a duplicate menu link does not remove
the window, controller, or its normal entry point.

| Menu entry | QML component | Controller/model | Status |
|---|---|---|---|
| **Editors** ||||
| Columns Editor | `ColumnsEditorView.qml` | `ColumnsEditorController` | Available; edits shared TACTIC table and EditSObject definitions in Simple or XML mode |
| **Integrations and Service Tools** ||||
| Update | `UpdateView.qml` | `UpdateController` | Experimental; update requires confirmation |
| Create Update | `UpdateView.qml` | `UpdateController` | Experimental; creation requires a click |

The selected DCC connector may append capability-gated commands to this menu
through `DCC_MANIFEST["ui"]["tool_actions"]`. These entries are not duplicated
in `DEFAULT_MENUS` and disappear when the selected client lacks the capability.

Examples of canonical locations for removed duplicates:

- Messages, Activity Feed, and Notifications use the top bar; profile and users
  use the user menu.
- Configuration, Script Editor, Debug Log, Watch Folders, Repository Sync, and
  Handler Server use the application menu.
- Repository and server-preset editors are opened from Configuration. Naming and
  pipeline editors are opened from Administration or their owning workflow.
- Drop Plate, database editing, tasks, notes, time sheets, and reports are
  workspace panels.
- Add/Edit sObject and SObject Info are result or item actions. Commit Queue and
  matching templates are part of check-in workflows.

Tool-window routing errors are caught, reported with a short notification, and
written to Debug Log with a stack trace.
