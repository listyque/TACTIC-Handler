# TACTIC compatibility map

This directory records the TACTIC structures that TACTIC-Handler consumes or
edits. It is an implementation contract, not a generic TACTIC manual.

The source baseline is the official TACTIC `5.0` branch at commit
[`17c78e0`](https://github.com/Southpaw-TACTIC/TACTIC/tree/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596).
Database observations are documented separately in
[`../tactic_database/`](../tactic_database/README.md).

## Source module map

| TACTIC module | Responsibility | TACTIC-Handler boundary |
| --- | --- | --- |
| [`pyasm/widget/widget_config.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/pyasm/widget/widget_config.py) | `WidgetConfig` XML access and `WidgetConfigView` cascading resolution | Called inside server procedures; never duplicated in QML |
| [`pyasm/search/widget_db_config.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/pyasm/search/widget_db_config.py) | `config/widget_config` lookup, priority merge and commits | Native reads and element/view writes |
| [`tactic/ui/panel/base_table_layout_wdg.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/tactic/ui/panel/base_table_layout_wdg.py) | Table configuration, explicit column overrides and custom columns | Behavioral reference for table projection |
| [`tactic/ui/panel/table_layout_wdg.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/tactic/ui/panel/table_layout_wdg.py) | Widget lifecycle, rows, sorting, grouping, resize and inline edit | Native widget value lifecycle is reused; web DOM behavior is not copied |
| [`tactic/ui/panel/layout_wdg.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/tactic/ui/panel/layout_wdg.py) | Add/predefined-column workflow | Reference for the available/current column split |
| [`tactic/ui/manager/element_definition_wdg.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/tactic/ui/manager/element_definition_wdg.py) | Display/edit/action definition editor and raw XML mode | Reference for form fields, save targets and round-trip rules |
| [`tactic/ui/common/widget_class_handler.py`](https://github.com/Southpaw-TACTIC/TACTIC/blob/17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596/src/tactic/ui/common/widget_class_handler.py) | Built-in widget-key registry | Widget taxonomy; arbitrary class paths remain valid |
| `pyasm/search`, `pyasm/biz` | Search, schema, projects, snapshots and pipelines | Existing server procedures and hydrated TACTIC objects |
| `tactic/ui/table` | Specialized display widgets | Executed on the TACTIC server when a table is resolved |

## Compatibility rule

Transported server procedures import common exceptions through the public
`pyasm.common` exports. Legacy TACTIC defines `SecurityException` in
`common_exception.py` and re-exports it; Stream's `pyasm.common.errors` module is
not a portable server dependency. Raw-table procedure regressions run both
product sources without that module and retain the administrator guard.

Server-side aggregate procedures use the legacy `Search.add_column` signature:
set `Search.get_select().set_quoted_mode('none')` before adding a fixed aggregate
expression without a `quoted` keyword. This includes security-group journal
revision markers as well as note counts and work-hour summaries. Group catalog
checks run against the strict legacy signature and real Stream SQL, comparing
batched markers with each group's latest journal revision.

TACTIC is authoritative for search types, configuration precedence, widget
classes, expressions and display values. The desktop client transports a
QML-safe description of the resolved result. It must not invent a second XML
schema or maintain a hand-written clone of `WidgetConfigView`.

The local ownership is intentionally small:

- `thlib/tactic_query.py`: code executed in the TACTIC runtime;
- `thlib/tactic_classes.py`: client-call boundary;
- `thlib/tactic_table_widgets.py`: TACTIC display-widget to Qt-cell registry;
- `thlib/ui/columns_editor.py`: table projection and editable DB overrides;
- `thlib/ui/tactic_definition.py`: lossless visual-form/XML transformations for
  `definition`, `edit_definition`, and `edit`;
- `thlib/ui/qml/SearchResultTable.qml`: Qt cell presentation;
- `thlib/ui/qml/features/administration/columns/ColumnsEditorView.qml`: Administration project definition catalog
  with wizard and lossless XML editing.

See [Table views](table_views.md) and [Widget support](widget_support.md).
