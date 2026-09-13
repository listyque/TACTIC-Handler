# TACTIC table views

## XML coordinates

A table is not a list of database fields. Its coordinate is a Search Type plus
a view name, normally `table`. A stored record is `config/widget_config` with
`search_type`, `view`, optional `login`/priority metadata, and XML like:

```xml
<config>
  <table layout="TableLayoutWdg">
    <element name="code" title="Code" width="120"/>
    <element name="name"/>
  </table>
  <definition>
    <element name="name" edit="true">
      <display widget="format"><type>Plain Text</type></display>
    </element>
  </definition>
</config>
```

The views have separate responsibilities:

| View | Meaning |
| --- | --- |
| `table` or another named table view | Column membership, order and local attribute/display overrides |
| `definition` | Reusable display widget definitions for the Search Type |
| `edit` | Membership/order of fields in an edit layout |
| `edit_definition` | Input widget and action definitions used by edit/inline-edit flows |
| `color` | Per-element color expressions/mappings |
| `ALL/definition` | Database defaults shared by Search Types |
| `widget_type=column` records | Custom/predefined columns appended to table configuration |

Putting every `<display>` node into `view=table` is not equivalent to TACTIC:
it destroys the reusable definition layer and changes how other views inherit.

## Native resolution

`WidgetConfigView.get_by_search_type(search_type, view)` constructs an ordered
stack. In the 5.0 baseline it considers, in order, a deprecated site override,
the selected database view, the matching database `definition` or
`edit_definition`, the database `ALL` definition, the internal Search Type
`*-conf.xml`, generated schema defaults, and namespace/product default config.
Custom `widget_type=column` configs are appended by the table layout.

Resolution is deliberately asymmetric:

- the first non-definition view containing elements owns column membership and
  order;
- element attributes cascade individually from higher to lower priority;
- the first display/edit/action handler with options wins as one definition;
  options are not merged key by key;
- `definition` and `edit_definition` views expose their own element lists.

TACTIC-Handler therefore calls the native resolver on the server. Local
`ViewsConfig.get_view()` is useful for inspecting downloaded rows but is not a
substitute for effective table resolution.

## Runtime lifecycle

The web `TableLayoutWdg` creates one display widget per resolved element, gives
every widget the complete sObject list, runs `preprocess()` once, selects the
current row index, then asks the widget for its display. Export/simple display
uses `get_text_value()`.

`query_table_layout()` mirrors that data lifecycle inside TACTIC and returns:

- resolved attributes, widget key/class and options;
- resolved edit widget/action definitions;
- the selected and available column catalogs;
- native `get_text_value()` results for the requested sObjects;
- raw database view XML for lossless editing.

The client resolves the matching native `EditWdg` once with the same object
context used by `EditSObject`. Its `InputWidgets` payload is passed through
`SObjectEditorController.describe_field()`, so table editing and the object
form share widget class mapping, resolved select values, type conversion and
read-only rules. A `SelectWdg` with `values_expr` and `labels_expr` evaluates
both expressions through TACTIC `Search.eval(..., single=False)` and returns the
parallel option lists; `get_values()` remains the current field value and is
not treated as the option catalog.

`thlib/tactic_table_widgets.py` maps the returned native display class to a
Qt cell contract, following the same server-widget/client-counterpart split as
`EditSObject` and `thlib/tactic_widgets.py`. The QML table renders those
semantic cells. It never evaluates TACTIC expressions, imports server widget
classes or executes configured Python.

`pyasm.widget.ThumbWdg` resolves to a thumbnail cell. That cell reuses the
workspace model's existing sObject preview request, repository-cache and
`ItemPreview` rendering path; it does not fetch or decode images in the table
delegate.

`tactic.ui.widget.DiscussionElementWdg` resolves to a Notes cell. Counts already
hydrated on the native sObject are shown as direct per-process links, including
the ordinary `publish` branch. Labels preserve the exact server process or
process/context identifier, so `publish` and `publish/context` stay separate.
A link opens that process in the shared Notes panel without an intermediate
picker. An empty cell keeps the existing Add note action. The table does not
create another note query or discussion editor.

`tactic.ui.table.SObjectDetailElementWdg` resolves its `use_parent` target on
the server and opens that object in the existing SObject Info window.
`tactic.ui.table.CheckinButtonElementWdg` opens the existing Drop Plate with
the native target, process, context, check-in type and transfer mode from its
definition. TACTIC, repository and check-in work remains in the standalone
check-in controller.

`tactic.ui.table.TaskElementWdg` returns the tasks already preprocessed by the
native widget, including process, context, status, assignee, dates and native
status color. The table completes that payload with empty processes from the
object's native pipeline and presents the same quick status and assignee choices
as Task Manager. Compact typography, controls and spacing keep several processes
visible without making the table row taller. Editors are created only when a
visible card is hovered or activated. Choosing a value updates the existing
task, or creates the missing process task with its workflow defaults. The process
title still opens the exact task in the shared Task workspace, and overflow
reuses the process picker.

`TaskCompletionWdg` uses its native preprocessed percentage in a Qt progress
bar. Explorer paths are resolved by TACTIC and opened by the desktop client.
The `file_list`, `metadata`, and `delete` controls reuse the sObject report and
dependency-aware delete workflow instead of cloning those tools inside a cell.

## Column header menu

Right-clicking a header follows TACTIC's column-scoped menu instead of opening
the whole editor directly. Native `widget.is_sortable()` capability controls
ascending/descending actions; the same menu opens the selected element's
`definition`, opens the Column Manager, or removes the column from `view=table`.
Dragging a heading changes and saves its `view=table` order through that same
column controller. A pinned checkbox column uses the normal Search selection,
and the menu offers compact, comfortable and large local row heights without
changing server data or widget definitions.
Grouping, related-item actions and retired-row visibility remain absent until
their TACTIC query state and table presentation have real Qt owners; they are
not exposed as inert menu entries.

## Editing and commits

The editor keeps two independent operations:

1. Saving the table view writes membership, order, title and width to
   `view=table` while preserving unmanaged XML nodes.
2. Saving an element writes the complete `<element>` to `definition` or
   `edit_definition` through TACTIC `WidgetConfig.alter_xml_element()`.

The Columns Editor exposes `Table` and `EditSObject` definition targets. Its
Simple mode edits table presentation or the EditSObject input class, required,
read-only, empty-choice, description, default, values and labels options. It
also adds or removes the field in `view=edit`; `edit_definition` and `edit`
remain separate native TACTIC views. XML mode is the lossless editor for
unknown, nested and custom options. In the table, double-clicking an editable cell
loads its normalized editor only for that cell. Enter, a selection, or focus
loss commits through the existing single-object update path; Escape cancels.
Changing a Task Workflow status or assignee applies the same process/context
value to every selected sObject when two or more rows are selected; otherwise
it changes only the edited row.
Existing tasks use one native `update_multiple`; missing tasks are created with
their native process defaults. If a selected row does not expose that process
or value, nothing is submitted and the editor reports the incompatible row.

Advanced mode lazily reads the project's complete stored
`config/widget_config` catalog. It can filter the catalog to the current Search
Type or show every Search Type. The all-types scope has a Search Type selector
in addition to the view filter. Each record is identified by view, Search Type,
login, category and code. Simple mode exposes every existing XML element,
attribute and text value without pretending that unrelated TACTIC views share
one semantic form; XML mode changes structure and preserves exact source text
until a visual value is edited. Both modes save the exact selected stored
record, and switching records is disabled while it has unsaved changes. Refresh
explicitly queries TACTIC, while opening the normal editor adds no catalog
request.

The element name cannot silently change. The server reparses every write and
rejects duplicate elements in a full view.
Selection is retained by the element name, not its temporary row number, so a
reorder or model reload cannot leave the highlight attached to another
element's XML.

## Deliberate boundary

Qt does not reproduce TACTIC's browser DOM, JavaScript behaviors, shelves or
HTML layout engine. Server-side display computation is compatible; interactive
web-only controls require an explicit Qt delegate before they become
interactive. Unsupported behavior remains visible in metadata/XML instead of
being flattened or discarded.
