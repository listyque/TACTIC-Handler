---
group: Configuration
icon: projects
order: 32
---
# Projects configuration

> Projects selects the workspace project and provides direct access to project creation and editing.
> The selection is shared with the project chooser in the main window.

Opening this page refreshes the project catalog from TACTIC, so newly created, retired, and
template projects are shown according to the filters without restarting the application.

## Available projects

| Control | What it does |
| --- | --- |
| **Retired** filter | Includes projects marked retired. It does not reactivate them. |
| **Templates** filter | Includes project templates in the list. |
| **Built-in** filter | Includes TACTIC system projects. Built-in projects can be activated but are not edited here. |
| **Project card** | Selects a project for inspection. Double-clicking activates it. The card shows server title, code, category, type, status, and description when supplied. |

## Workspace project

**Current** identifies the project used by the workspace now. **Activate selected project** switches
the entire workspace to the selected project, so Search Types, navigation, tasks, and project data
reload for that context. **Edit selected project** opens the project editor and is disabled for
built-in projects. **Create new project** opens the four-step TACTIC project creation wizard.

Selecting a card is harmless; the project changes only after activation or a double-click.

## Project editor

Edit selected project opens a modal editor with an immutable code, title, category, type, description, archived/template flags and image selection. Closing a changed form offers Keep editing or Discard changes. Save uses the existing native command and image owner. Stream retains additional status/palette fields; unsupported custom inputs block Save explicitly. Archiving uses the native retire operation and its history, not a direct status update. Activation remains a separate immediate workspace operation.
