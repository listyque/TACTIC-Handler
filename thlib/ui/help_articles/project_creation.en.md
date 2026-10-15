---
group: Workflows
icon: create-new-folder
order: 24
---
# Project settings and creation

> Project Settings and the quick chooser show active, archived, template, and built-in TACTIC
> projects. Cards explain the project category, type, lifecycle, code, description, server status, and
> square repository web preview. Retired, Templates, and Built-in filters are disabled by default and
> shared by both views; their controls reflow without overlapping the project list.

## Main controls

Select and activate an existing project. Edit selected project opens a native modal editor for its
name, category, type, description, template flag, archive/reactivate state, and preview image.

In Configuration > Projects, Deactivate current project clears the active workspace without
signing out, archiving, or deleting the server project. Select a project to activate it again.
Create template archive exports the selected editable project through TACTIC's native template
command; it does not need to be marked as a template. The archive is stored on the server and
contains configuration and structure, not production objects, tasks, or snapshots. This action
is beside Edit and Create, not inside the new-project wizard. Compact layouts use labeled tooltips.

Built-in TACTIC projects are visible but read-only. A replacement preview is prepared through the
normal Commit Queue instead of being uploaded from the UI thread.

Choose image stages a replacement preview. Undo image selection restores the previous preview before
saving.

Project Editor and the creation wizard fill the native window's bottom edge without
an inset corner gap, including while resizing.

## Usage notes

- Create new project opens the native multi-step wizard.
- The four steps are Details, Preview Image, Template and Review. They use the application's
  shared MD3 navigation, grouped setting rows and action buttons. The step rail becomes compact
  in a narrow window; hover its icons to identify the steps.
- Click an earlier step to revise it. Future steps remain disabled until you advance with Next.
  Review shows the selected preview, title, code, description, category and labeled project settings.
- The action footer stays flush with the bottom window edge while resizing; the native window frame owns its outer corners.
- Enter a title (up to 100 characters) and a unique code (up to 30 ASCII letters, numbers or
  underscores, not starting with a number). Retired projects also reserve their codes.
  Add an optional description and category on the first step; both are saved to the created project.
- The optional image is uploaded when creating the project, then checked in by TACTIC.
- Choose an empty project, a server project template, an installed ZIP archive, or a built-in
  template. Server-defined names are displayed unchanged.
  The selector, template actions and explanatory note have consistent spacing inside the card.
- Details includes the Search Type namespace, template flag and main-project flag for empty projects.
  Namespace prefixes new Search Types (for example studio/shot); blank uses the project code.
  It does not rename the project; sthpw and prod are reserved.
  The Template step defaults to No theme. Themes affect only the TACTIC web interface, not
  TACTIC-Handler's appearance. Changing the main
  project may require restarting TACTIC. Template copies use their own configuration instead.
- Manage templates installs, downloads and removes server packages. Create template archive on
  the Projects configuration page captures the selected project's current configuration.
  Removing a package does not remove existing projects.
- Create project saves the project and opens it. The project catalog refreshes after creation.
- Creation uses native TACTIC commands in a background worker and is never automatically retried.
  If creation succeeds but saving its metadata or opening fails, Retry opening project completes
  those steps without creating a second project.
  If TACTIC reports a creation failure, inspect the server error and refresh the catalog before
  trying again: native creation commands can commit some changes before failing.
