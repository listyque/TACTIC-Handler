---
group: Workflows
icon: sobject
order: 12
---
# Creating and editing sObjects

> The object editor uses the active TACTIC EditWdg definition.

## Main controls

Each field keeps the server title, order, column, required and read-only state, option labels and
stored values. Text, multiline, boolean, select, user, project, process, pipeline, status, date,
password, parent, preview, and thumbnail widgets share one responsive Material form.

Status and process colors and task assignees follow the selected object's workflow configuration.

## Usage notes

- Fields stack in one ordered column in a narrow window.
- Widening either the Create or Edit window flows the existing field cards into two or three columns
  instead of stretching every control across the window.
- Each card still aligns its label beside the control when its own width allows it.
- The form and multiline fields show theme-aware scrollbars whenever their content exceeds the
  available height.
- Password editing never reveals the current value; leave it empty to keep the existing password.
- Unsupported custom server widgets remain visible and read-only instead of writing an incorrect
  fallback value.
