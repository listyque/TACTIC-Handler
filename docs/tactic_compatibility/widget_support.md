# TACTIC table widget support

The built-in keys below come from TACTIC's `WidgetClassHandler` and
`TableElementClassHandler`. A project may also use any importable class path;
the client must preserve it even when no specialized Qt delegate exists.

| TACTIC widget family | Examples | Server compatibility | Qt presentation |
| --- | --- | --- | --- |
| Direct values | `simple`, `default`, `raw_data` | Native widget creation and `get_text_value()` | Text |
| Formatting | `format` | Native number/date/time/percent/currency formatting | Text |
| Expressions | `expression`, `expression_value` | Native TACTIC expression evaluation and preprocessing | Text |
| Relationships | foreign-key/default relationship widgets | Native related-object preprocessing and display template | Text |
| Links | `link` | Native link value/expression | Clickable link |
| Booleans | boolean schema types and checkbox handlers | Native value | Checkbox display; the configured edit input becomes a switch |
| Thumbnails | `ThumbWdg`, `pyasm.widget.ThumbWdg` | Native widget definition and preprocessing | `ItemPreview` through the shared sObject preview/cache pipeline |
| Notes | `tactic.ui.widget.DiscussionElementWdg` | Native discussion preprocessing and text export | Direct per-process note counts using the shared Notes panel; Add note for an empty cell |
| Object details | `tactic.ui.table.SObjectDetailElementWdg` | Native definition and `use_parent` target resolution | Details action using the shared SObject Info window |
| Check-in | `tactic.ui.table.CheckinButtonElementWdg` | Native target, process, context, check-in type and transfer mode options | Check-in action using the shared Drop Plate and standalone check-in controller |
| Tasks | `tactic.ui.table.TaskElementWdg` | Native task preprocessing, pipeline order, status colors and text export | Quick Task cards with inline workflow status and assignee editors; empty processes create tasks with native defaults |
| Completion | `completion`, `TaskCompletionWdg` | Native task preprocessing and percentage | Progress bar |
| Workflow values | task/statistic/work-hour custom classes | Native preprocessing and text value when provided | Text |
| Scripted values | `python` and custom table classes | Executed only by the configured TACTIC server widget | Text or explicit fallback/error |
| Explorer | `explorer`, `ExplorerElementWdg` | Native sandbox or client-repository path resolution | Opens the resolved folder |
| Files and metadata | `file_list`, `metadata` | Native target and widget options | Opens the target in the shared sObject report |
| Delete | `delete`, `DeleteElementWdg` | Native row availability | Shared dependency review before deletion |
| Visual/interactive web widgets | `button`, `gantt`, `drop_item`, `hidden_row`, `custom_layout`, `freeform_layout` | Definition and native text value preserved | Browser-only JavaScript, DOM, drag shelf or HTML layout is not executed in Qt |
| Edit inputs | `TextWdg`, `TextAreaWdg`, `SelectWdg`, checkbox, calendar/date, password and workflow selectors | Native `EditWdg` resolves the effective `edit`/`edit_definition` stack and option values | The same field catalog and Qt value editors as `EditSObject`; double-click opens the inline editor |

## Failure behavior

If a configured display class cannot be imported, initialized, preprocessed or
read as text, the server adapter returns the raw column value and an error on
that cell. It does not replace the class in XML, hide the column, or pretend the
fallback is equivalent.

## Adding a Qt delegate

Add a delegate only for a concrete widget contract that needs interaction or
non-text visuals. The server remains responsible for expressions and TACTIC
object access; the new delegate consumes a narrow QML-safe payload and must have
a real QML creation/interaction test.
