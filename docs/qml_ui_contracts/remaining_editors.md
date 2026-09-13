# Editor contracts

This document records the ownership of the remaining focused editors. Obsolete
WWidget migration notes were removed after the QML implementations became
authoritative.

## Columns Editor

`ColumnsEditorController` and `ColumnsEditorView` manage the shared TACTIC
`table`, `definition`, `edit`, and `edit_definition` views for the current
Search Type. The table definition drives the optional table result view and
Database Editor ordering; the edit views also drive EditSObject and inline
cell editors.

- Apply writes the project-wide `config/widget_config` row at
  `search_type + view=table`, then reads it back before updating the UI.
- Unknown element attributes, nested display/widget options, definition-only
  elements, and internal elements are preserved. Missing schema columns can
  be added to the view without changing the physical database schema.
- Multiple shared rows for the same coordinate are rejected instead of
  choosing one and overwriting another category or precedence layer.
- Apply updates the common columns model, table results, and Database Editor.
- Cancel restores the session snapshot; Reset restores the owned defaults.
- The result-table prototype renders sObjects only, supports horizontal and
  vertical scrolling, and uses the configured labels, order, and widths.
- Simple mode visually edits supported display/input widgets and common input
  options. It can include or remove a field from `view=edit`. XML mode preserves
  unsupported, custom, and nested options without flattening them.
- Column definitions change presentation, not physical database schema or
  server query semantics.

## SObject column value editing

The schema-driven field editor edits values of existing columns for one or
multiple selected SObjects.

- Integer and floating-point values validate before submission.
- System columns remain read-only.
- Mutations use existing `update_selected_item_fields()` and
  `update_multiple(..., triggers=True)` paths.
- Creating or altering a physical database column is intentionally unavailable
  because no verified schema-mutation and confirmation contract exists.

## Server Presets Editor

The native MD3 editor uses `env_server` and the existing preset format.

- Add/remove, protected `default`, Save, and Cancel are supported.
- The active preset is marked and must be switched from Configuration before it
  can be removed; the editor never leaves the live connection pointing at a
  deleted preset.
- Opening always starts from persisted values. Cancel and the native close
  button discard the current draft.
- Credentials are not stored in the view model or logs.
- Editing presets does not silently switch the current connection; Configuration
  owns reconnect/bootstrap.

## Screenshot Maker

The native top-level Screenshot Maker captures an explicitly selected desktop
region through the Qt screen API and attaches the PNG directly to the selected
editable Commit Queue operation. It is opened from that operation rather than
as a standalone catalog tool. Capture and cancel restore and reactivate the
same Commit Queue window that opened it.

Multi-screen coordinates, Windows scaling, hidden-window restoration, and DCC
host behavior require platform testing. Deprecated Qt 5 capture APIs are not
used as a new implementation path.

## Script Editor

The Script Editor owns local/server scripts, open tabs, dirty local drafts,
editor history, syntax support, execution confirmation, and output.

- Unsaved content persists through the project configuration API per tab.
- Local undo/redo remains separate from server-saved script history. Choosing a
  saved revision stages its source as an ordinary unsaved edit.
- The saved language is the default execution target: DCC Python requires the
  selected capable DCC, Local Python runs in TACTIC Handler, and Server Python
  remains server-side. Run in can temporarily override that default.
- DCC execution sends only a validated staging-file path through the Handler
  Server. Each tab owns one file under `custom_scripts/.temp`; a run overwrites
  it with the current buffer, including unsaved new or modified source. The
  selected client executes it on its native main thread. Closing or discarding
  the tab removes its staging file.
- DCC stdout and stderr remain visible in the DCC console and are mirrored to
  the active tab's Output panel.
- New output for the active tab expands the Output panel, including when its
  previous saved layout left that panel collapsed.
- Script Triggers opens from the toolbar as a separate resizable editor. Its
  ordered project rules use the shared controls, script-tree picker, and
  persistent scrollbars; only administrators can change the server document.
  Snapshot open/save are Handler actions and wrap the completed standalone
  file-open or check-in operation rather than a DCC command.
- Application Help has a dedicated Script Triggers topic describing ordered
  before/after execution, the trigger context, failure behavior, and copyable
  Python examples.
- Tab inserts four-column spaces. Ctrl+Shift+K deletes selected lines,
  Ctrl+Y redoes, Ctrl+Shift+O focuses the source outline, Alt+Up/Down moves
  between symbols, and F12 opens an in-file definition. Ctrl+Enter runs the
  selection with either Return key.
- Line numbers use the editor's actual line height. Symbol navigation aligns
  the destination with the top of the viewport whenever enough source remains.
- Split sizes, collapsed panels, output wrapping, outline selection, and editor
  font size survive closing and reopening the window. New reuses an existing
  untouched draft instead of creating duplicate blank tabs.
- The right panel switches between server scripts and the current source
  outline. Python completion statically follows local imports, current classes,
  `self` members, and the thin Handler API without executing imported modules.
- Full traceback goes to Debug Log and concise failure remains in the editor.
- Server scripts are deleted only from the script-tree context menu with
  confirmation.
- No script executes automatically on open or restore.
- Its common tabs, search, scrollbars, controls, theme, and help follow the
  shared UI contracts.

## Naming Editor and check-in preview

`NamingEditorController` and `NamingEditorView` own the existing `config/naming`
rule list, field editor, local template simulation and explicit server save.
Administration embeds this same editor in the selected Search Type's Naming tab,
without a child window or object requirement. Types without rules can create
their first rule here. Object and Commit Queue entry
points keep their object-scoped rule list and preview data. Unsaved rules stay
bound to their original project. See `docs/administration.md` for entry and
verification contracts.

The separate check-in naming preview remains backed by `CheckinOutController`
and `get_virtual_snapshot()`; local editor simulation does not replace TACTIC's
authoritative check-in naming resolution.

## Common editor requirements

- Functional editors are native top-level windows hosted by the shared window
  infrastructure.
- Each editor has one Python state owner and uses native TACTIC/configuration
  APIs directly.
- Server and filesystem work is asynchronous.
- Save, Cancel, dirty state, validation, close guard, scrolling, minimum size,
  symmetric spacing, and help routing are explicit.
- QML receives safe primitive/model data, never raw server objects or workers.
- New behavior and shortcuts are documented in the matching English and Russian
  Markdown files under `thlib/ui/help_articles`.
