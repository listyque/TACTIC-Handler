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

Built-in TACTIC projects are visible but read-only. A replacement preview is prepared through the
normal Commit Queue instead of being uploaded from the UI thread.

Choose image stages a replacement preview. Undo image selection restores the previous preview before
saving.

## Usage notes

- Create new project opens the native multi-step wizard.
- The wizard reserves steps for name and code, template, preview, categories, and review.
- Project creation remains a UI foundation only: Create project is disabled, while editing existing
  projects is functional.
