from __future__ import annotations

import os
from pathlib import Path
import json
import sys
from types import SimpleNamespace
from types import ModuleType
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import (
    QObject, QPointF, Property, QMetaObject, Qt, QUrl, Signal, Slot,
)
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib import tactic_table_widgets as table_widgets


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


def _visual_items(root):
    pending = [root]
    items = []
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


TABLE_XML = (
    '<config marker="keep"><table><element name="code" title="Code" '
    'width="96"><display class="LinkWdg"><option>keep</option></display>'
    '</element><element name="custom" expression="@GET(.name)"/>'
    '<element name="__search_key__" internal="keep"/></table>'
    '<other value="keep"/></config>'
)

DEFINITION_XML = (
    '<config><definition><element name="code" title="Code" width="96">'
    '<display widget="link"><icon>FA_LINK</icon></display></element>'
    '<element name="custom"><display widget="expression">'
    '<expression>@GET(.name)</expression></display></element>'
    '<element name="name" title="Asset name"><display widget="format">'
    '<type>Plain Text</type></display></element></definition></config>'
)


def _layout_payload(search_type="demo/asset"):
    columns = [
        {
            "name": "code", "title": "Code", "width": 96,
            "dataType": "varchar", "kind": "link", "attributes": {},
            "displayWidget": "link", "displayClass": "",
            "resolvedClass": "tactic.ui.table.LinkElementWdg",
            "displayOptions": {"icon": "FA_LINK"},
            "displayXml": (
                '<element name="code" title="Code" width="96">'
                '<display widget="link"><icon>FA_LINK</icon></display>'
                '</element>'
            ),
            "editWidget": "text", "editClass": "",
            "editOptions": {}, "editXml": "", "actionClass": "",
            "actionOptions": {}, "selected": True, "sortable": True,
        },
        {
            "name": "custom", "title": "Custom", "width": 160,
            "dataType": "varchar", "kind": "text", "attributes": {},
            "displayWidget": "expression", "displayClass": "",
            "resolvedClass": "tactic.ui.table.ExpressionElementWdg",
            "displayOptions": {"expression": "@GET(.name)"},
            "displayXml": (
                '<element name="custom"><display widget="expression">'
                '<expression>@GET(.name)</expression></display></element>'
            ),
            "editWidget": "", "editClass": "", "editOptions": {},
            "editXml": "", "actionClass": "", "actionOptions": {},
            "selected": True, "sortable": False,
        },
    ]
    name = {
        "name": "name", "title": "Asset name", "width": 160,
        "dataType": "varchar", "kind": "text", "attributes": {},
        "displayWidget": "format", "displayClass": "",
        "resolvedClass": "",
        "displayOptions": {"type": "Plain Text"},
        "displayXml": (
            '<element name="name" title="Asset name">'
            '<display widget="format"><type>Plain Text</type></display>'
            '</element>'
        ),
        "editWidget": "text", "editClass": "", "editOptions": {},
        "editXml": "", "actionClass": "", "actionOptions": {},
        "selected": False, "sortable": True,
    }
    return {
        "searchType": search_type,
        "view": "table",
        "columns": columns,
        "availableColumns": columns + [name],
        "rows": {
            "demo/asset?code=ASSET001": {
                "code": {
                    "text": "https://example.invalid/ASSET001",
                    "kind": "link", "href": "https://example.invalid/ASSET001",
                    "error": "",
                },
                "custom": {"text": "Oak", "kind": "text", "error": ""},
            }
        },
        "databaseViews": {
            "table": {"code": "WIDGET001", "config": TABLE_XML},
            "definition": {
                "code": "WIDGET002", "config": DEFINITION_XML,
            },
        },
        "inputWidgets": [
            {
                "name": "code",
                "title": "Code",
                "class_name": "pyasm.widget.input_wdg.TextWdg",
                "kwargs": {},
                "action_options": {},
            },
            {
                "name": "custom",
                "title": "Custom",
                "class_name": "pyasm.widget.input_wdg.SelectWdg",
                "values": ["oak", "pine"],
                "labels": ["Oak", "Pine"],
                "kwargs": {},
                "action_options": {},
            },
            {
                "name": "name",
                "title": "Asset name",
                "class_name": "pyasm.widget.input_wdg.TextWdg",
                "kwargs": {},
                "action_options": {},
            },
        ],
    }


class _Views:
    def __init__(self):
        self.config_dict = [{
            "code": "WIDGET001", "view": "table", "login": "",
            "search_type": "demo/asset", "config": TABLE_XML,
        }]


class _Project:
    def __init__(self):
        self.views = _Views()

    def get_config_views(self):
        return self.views


class _SType:
    def __init__(self):
        self.project = _Project()
        self.info = {"definition": {"table": TABLE_XML}}

    def get_code(self):
        return "demo/asset"

    def get_pretty_name(self):
        return "Assets"

    def get_columns_info(self):
        return {
            "code": {"data_type": "varchar", "label": "Code"},
            "name": {"data_type": "varchar", "label": "Name"},
        }

    def get_column_data_type(self, name):
        return self.get_columns_info().get(name, {}).get("data_type", "text")

    def get_definition(self, _name, processed=True):
        return self.info["definition"]["table"] if not processed else []

    def get_project(self):
        return self.project


class _Application(QObject):
    selected_node_changed = Signal()
    project_changed = Signal(str, str)
    results_view_changed = Signal()
    search_state_changed = Signal()

    def __init__(self, stype):
        super().__init__()
        self.stype = stype
        self.selected_node_id = ""
        self._current_project_code = "demo"
        self.workspace_model = SimpleNamespace(node_for=lambda _node_id: None)
        self.window_model = SimpleNamespace(
            is_window_visible=lambda _window_id: False
        )
        self.dock_model = SimpleNamespace(
            is_panel_presented=lambda _panel_id: False
        )
        self.workspace_state = SimpleNamespace(
            columns_model=RecordListModel(("title", "checked"))
        )
        self.debug_log = None
        self.notifications = []
        self.sort_modes = []
        self.search_cache_saves = 0
        self.tab = SimpleNamespace(
            stype=self.stype, sobjects=[], view_mode="table",
            table_view="table",
        )

    def _node_for_any(self, node_id):
        return self.workspace_model.node_for(node_id)

    def _current_tab(self):
        return self.tab

    def _save_search_cache(self):
        self.search_cache_saves += 1

    def _notify(self, message):
        self.notifications.append(message)

    def set_result_sort_mode(self, mode):
        self.sort_modes.append(mode)

    def update_selected_item_fields(self, _node_id, _values):
        pass


class _Server:
    def __init__(self):
        self.row = {
            "code": "WIDGET001", "view": "table", "login": "",
            "search_type": "demo/asset", "config": TABLE_XML,
        }

    def query(self, *_args):
        return [dict(self.row)]

    def build_search_key(self, *_args, **_kwargs):
        return "config/widget_config?code=WIDGET001"

    def insert_update(self, _search_key, data, triggers=True):
        self.row.update(data)

    def insert(self, _search_type, data, triggers=True):
        self.row.update(data)
        return dict(self.row)


class _Worker(QObject):
    result = Signal(object)
    error = Signal(object)
    finished = Signal()

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def start(self):
        try:
            self.result.emit(self.callback())
        except Exception as error:
            self.error.emit(({"exception": error, "traceback": "test"}, self))
        finally:
            self.finished.emit()

    def cancel(self):
        pass


class _Pool:
    is_stopped = False

    def add_task(self, callback):
        return _Worker(callback)

    def start(self):
        self.is_stopped = False


class _TableController(QObject):
    selected_node_changed = Signal()

    def __init__(self):
        super().__init__()
        self._selected = []
        self.selections = []
        self.actions = []
        self.double_clicks = []
        self.opened_windows = []
        self.columns_editor_requests = 0
        self.select_all_calls = 0
        self.preview_requests = []
        self.revealed_previews = []
        self.table_widget_actions = []
        self.process_details = []
        self.task_details = []
        self.clear_selection_calls = 0
        self.field_updates = []
        self._result_sort_mode = "name_asc"
        self._result_group_mode = "none"
        self.group_modes = []
        self.toggled_nodes = []

    @Property("QVariantList", notify=selected_node_changed)
    def selected_result_node_ids(self):
        return self._selected

    @Property(bool, constant=True)
    def has_more(self):
        return False

    @Property(str, constant=True)
    def loading_mode(self):
        return "pages"

    @Property(str, constant=True)
    def result_sort_mode(self):
        return self._result_sort_mode

    @Property(str, notify=selected_node_changed)
    def result_group_mode(self):
        return self._result_group_mode

    @Slot(str)
    def set_result_group_mode(self, mode):
        self._result_group_mode = mode
        self.group_modes.append(mode)
        self.selected_node_changed.emit()

    @Slot(str)
    def toggle_result_node(self, node_id):
        self.toggled_nodes.append(node_id)

    @Slot(str, str, str, int, bool)
    def select_result_node(self, *args):
        self.selections.append(args)
        if not args[4]:
            self._selected = [args[0]]
        self.selected_node_changed.emit()

    @Slot(str, result="QVariantList")
    def item_menu_actions(self, _node_id):
        return [{"title": "Open", "command": "open"}]

    @Slot(str, str)
    def invoke_item_action(self, command, node_id):
        self.actions.append((command, node_id))

    @Slot(str, str, "QVariantMap")
    def invoke_table_widget_action(self, kind, node_id, values):
        self.table_widget_actions.append((kind, node_id, dict(values)))

    @Slot(str, "QVariantMap")
    def update_selected_item_fields(self, node_id, values):
        self.field_updates.append((node_id, dict(values)))

    @Slot(str, str, str)
    def open_process_details(self, node_id, panel, process):
        self.process_details.append((node_id, panel, process))

    @Slot(str, str, str, str)
    def open_process_task_details(
        self, node_id, panel, process, task_code,
    ):
        self.task_details.append((node_id, panel, process, task_code))

    @Slot(str, str, result="QVariantList")
    def process_count_actions(self, _node_id, panel):
        if panel != "notes":
            return []
        return [
            {
                "title": "Rigging", "process": "rig", "badgeCount": 1,
                "accent": "#42a5f5",
            },
            {
                "title": "Localized publish", "process": "publish",
                "badgeCount": 2, "accent": "#66bb6a",
            },
            {
                "title": "Localized publish context",
                "process": "publish/context", "badgeCount": 3,
                "accent": "#ab47bc",
            },
            {
                "title": "Modeling", "process": "model", "badgeCount": 1,
                "accent": "#ffa726",
            },
        ]

    @Slot(str, int, result=bool)
    def handle_item_double_click(self, node_id, modifiers):
        self.double_clicks.append((node_id, modifiers))
        return True

    @Slot(str)
    def open_window(self, window_id):
        self.opened_windows.append(window_id)

    @Slot()
    def open_columns_editor(self):
        self.columns_editor_requests += 1

    @Slot()
    def select_all_result_siblings(self):
        self.select_all_calls += 1
        self._selected = ["asset"]
        self.selected_node_changed.emit()

    @Slot()
    def clear_result_selection(self):
        self.clear_selection_calls += 1
        self._selected = []
        self.selected_node_changed.emit()

    @Slot()
    def load_more(self):
        pass

    @Slot(str)
    def request_item_preview(self, node_id):
        self.preview_requests.append(node_id)

    @Slot(str)
    def mark_item_preview_revealed(self, node_id):
        self.revealed_previews.append(node_id)


class _TableColumns(QObject):
    stateChanged = Signal()
    cellRevisionChanged = Signal()

    def __init__(self):
        super().__init__()
        self.sessions = 0
        self.width_changes = []
        self.apply_calls = 0
        self.reload_calls = 0
        self.sort_calls = []
        self.group_calls = []
        self.focus_requests = []
        self.remove_calls = []
        self.move_calls = []
        self.editor_requests = []
        self.task_edits = []
        self.task_save_calls = 0
        self._dirty_task_count = 0
        self._dirty = False
        self._busy = False
        self._error = ""
        self._cell_revision = 0
        self.selected_table_views = []
        self.saved_table_views = []
        self._table_views = [{
            "view": "table", "title": "table", "current": True,
        }]
        self._columns = [
            {
                "row": 2, "name": "preview", "label": "Preview",
                "width": 64, "kind": "thumbnail", "dataType": "",
                "sortable": False,
            },
            {
                "row": 0, "name": "code", "label": "Code", "width": 180,
                "dataType": "varchar", "sortable": True,
            },
            {
                "row": 1, "name": "name", "label": "Asset name",
                "width": 220, "dataType": "varchar", "sortable": True,
                "editable": True,
            },
            {
                "row": 3, "name": "notes", "label": "Notes", "width": 72,
                "kind": "notes", "dataType": "", "sortable": False,
            },
            {
                "row": 4, "name": "detail", "label": "Details", "width": 54,
                "kind": "sobject_detail", "dataType": "",
                "sortable": False,
            },
            {
                "row": 5, "name": "checkin", "label": "Check-in", "width": 58,
                "kind": "checkin", "dataType": "", "sortable": False,
            },
            {
                "row": 6, "name": "tasks", "label": "Tasks", "width": 280,
                "kind": "tasks", "dataType": "", "sortable": False,
                "displayOptions": {"show_process": "true"},
            },
            {
                "row": 7, "name": "completion", "label": "Completion",
                "width": 160, "kind": "completion", "dataType": "",
                "sortable": False,
            },
            {
                "row": 8, "name": "explorer", "label": "Folder",
                "width": 54, "kind": "explorer", "dataType": "",
                "sortable": False,
            },
            {
                "row": 9, "name": "files", "label": "Files",
                "width": 54, "kind": "file_list", "dataType": "",
                "sortable": False,
            },
            {
                "row": 10, "name": "metadata", "label": "Metadata",
                "width": 54, "kind": "metadata", "dataType": "",
                "sortable": False,
            },
            {
                "row": 11, "name": "delete", "label": "Delete",
                "width": 54, "kind": "delete", "dataType": "",
                "sortable": False,
            },
        ]
        for column in self._columns:
            column["hideOrder"] = 0

    @Property("QVariantList", notify=stateChanged)
    def visibleColumns(self):
        return self._columns

    @Property("QVariantList", notify=stateChanged)
    def tableViews(self):
        return self._table_views

    @Property(str, notify=stateChanged)
    def currentTableView(self):
        return next((
            str(record["view"]) for record in self._table_views
            if record.get("current")
        ), "table")

    @Slot(int, result=bool)
    def select_table_view(self, row):
        self.selected_table_views.append(row)
        return True

    @Slot(str, result=bool)
    def save_table_view_as(self, title):
        self.saved_table_views.append(title)
        return True

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(int, notify=stateChanged)
    def dirtyTaskCount(self):
        return self._dirty_task_count

    @Slot()
    def save_task_changes(self):
        self.task_save_calls += 1
        self._dirty_task_count = 0
        self.stateChanged.emit()

    @Slot()
    def discard_task_changes(self):
        self._dirty_task_count = 0
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def dirty(self):
        return self._dirty

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(int, notify=cellRevisionChanged)
    def cellRevision(self):
        return self._cell_revision

    @Slot()
    def begin_session(self):
        self.sessions += 1

    @Slot()
    def reload(self):
        self.reload_calls += 1

    @Slot(str, str, result="QVariantMap")
    def cell_editor(self, _node_id, column):
        self.editor_requests.append((_node_id, column))
        if column != "name":
            return {}
        return {
            "fieldName": "name",
            "submitName": "name",
            "fieldType": "string",
            "fieldValue": "Oak",
            "fieldOptions": [],
            "fieldError": "",
        }

    @Slot(str, str, str, str, result="QVariantMap")
    def task_editor(self, _node_id, _process, _status, _assigned):
        return {
            "statusChoices": [
                {"label": "Pending", "value": "Pending", "color": "#888888"},
                {
                    "label": "In Progress", "value": "In Progress",
                    "color": "#4f8cff",
                },
                {"label": "Complete", "value": "Complete", "color": "#44aa66"},
            ],
            "userChoices": [
                {"label": "Not assigned", "value": ""},
                {"label": "Artist", "value": "artist"},
                {"label": "Supervisor", "value": "supervisor"},
            ],
        }

    @Slot(str, str, str, str, str, result=bool)
    def set_task_value(
        self, node_id, task_search_key, process, field, value,
    ):
        self.task_edits.append((
            node_id, task_search_key, process, field, value,
        ))
        return True

    @Slot(int, int)
    def set_width(self, row, width):
        self.width_changes.append((row, width))
        self._columns[row] = {**self._columns[row], "width": width}
        self._dirty = True
        self.stateChanged.emit()

    @Slot(result=bool)
    def apply(self):
        self.apply_calls += 1
        self._dirty = False
        self.stateChanged.emit()
        return True

    @Slot(int, bool)
    def sort_column(self, row, descending):
        self.sort_calls.append((row, descending))

    @Slot(int)
    def group_column(self, row):
        self.group_calls.append(row)

    @Slot(int, str)
    def request_column_focus(self, row, target):
        self.focus_requests.append((row, target))

    @Slot(int, result=bool)
    def remove_column(self, row):
        self.remove_calls.append(row)
        return True

    @Slot(int, int)
    def move(self, row, offset):
        self.move_calls.append((row, offset))

    @Slot(int, result="QVariantMap")
    def all_cells(self, _revision=0):
        return {}

    @Slot(str, str, result="QVariantMap")
    def cell(self, _search_key, column):
        if column == "preview":
            return {"text": "", "kind": "thumbnail"}
        if column == "notes":
            return {"text": "", "kind": "notes"}
        if column == "detail":
            return {
                "text": "", "kind": "sobject_detail",
                "targetSearchKey": "demo/asset?code=ASSET001",
            }
        if column == "checkin":
            return {
                "text": "", "kind": "checkin", "available": True,
                "targetSearchKey": "demo/asset?code=ASSET001",
                "process": "model", "context": "model",
            }
        if column == "tasks":
            return {
                "text": "model:In Progress:artist",
                "kind": "tasks",
                "tasks": [
                    {
                        "taskSearchKey": "sthpw/task?code=TASK001",
                        "taskCode": "TASK001", "process": "model",
                        "context": "model", "status": "In Progress",
                        "statusColor": "#4f8cff", "assigned": "artist",
                        "assignedLabel": "Artist", "hasTask": True,
                        "bidStart": "2026-09-01", "bidEnd": "2026-09-03",
                        "bidStartLabel": "1 Sep", "bidEndLabel": "3 Sep",
                        "bidStartFull": "1 September 2026",
                        "bidEndFull": "3 September 2026",
                    },
                    {
                        "taskSearchKey": "", "taskCode": "",
                        "process": "rig", "context": "rig",
                        "status": "Pending", "statusColor": "",
                        "processColor": "#8855aa", "assigned": "",
                        "assignedLabel": "Not assigned", "hasTask": False,
                        "bidStart": "", "bidEnd": "",
                    },
                ],
            }
        if column == "completion":
            return {
                "text": "75.0%", "kind": "completion", "percent": 75.0,
            }
        if column == "explorer":
            return {
                "text": "", "kind": "explorer", "available": True,
                "path": "D:/projects/demo",
            }
        if column == "files":
            return {"text": "", "kind": "file_list"}
        if column == "metadata":
            return {"text": "", "kind": "metadata"}
        if column == "delete":
            return {"text": "", "kind": "delete", "available": True}
        return {
            "text": "ASSET001" if column == "code" else "Oak",
            "kind": "text",
        }

    @Slot(str, int, result="QVariantMap")
    def row_cells(self, search_key, _revision):
        return {
            str(column["name"]): self.cell(search_key, str(column["name"]))
            for column in self._columns
        }


class ColumnsTableViewTests(unittest.TestCase):
    def test_loaded_cell_width_hint_respects_config_and_unsaved_widths(self):
        controller = ColumnsEditorController(_Application(_SType()))
        controller._table_widgets = {'schedule': table_widgets.TacticSimpleTableWidget()}
        controller.model.replace([dict(name='schedule', displayWidth=160)])
        payload = dict(columns=[dict(name='schedule', attributes={})],
                       rows={'A': {'schedule': dict(text='', widthHint=400)}})
        controller._table_rows_loaded(controller._row_request_id, payload)
        self.assertEqual(controller.model._records[0]['displayWidth'], 400)
        self.assertEqual(controller._source_records, controller.model._records)
        controller.model.replace([dict(name='schedule', displayWidth=220)])
        payload['columns'][0]['attributes']['width'] = '220px'
        controller._table_rows_loaded(controller._row_request_id, payload)
        self.assertEqual(controller.model._records[0]['displayWidth'], 220)
        payload['columns'][0]['attributes'] = {}
        controller._dirty = True
        controller._table_rows_loaded(controller._row_request_id, payload)
        self.assertEqual(controller.model._records[0]['displayWidth'], 220)
        self.assertTrue(controller._dirty)

    def test_group_collapse_reuses_existing_task_cards(self):
        from tests.profile_result_table import benchmark

        result = benchmark(self.app, width=1800, height=1600, grouped=True)
        # A header/object slot change may create one row's five cards, not
        # rebuild all 85 visible cards on every group click.
        self.assertLessEqual(max(result["groupClicks"]["collapse"]["newCards"]), 5)
        self.assertEqual(result["groupClicks"]["expand"]["newCards"][1:], [0] * 5)

    def test_table_projection_indexes_targets_once_per_batch(self):
        identity_reads = []
        workflow_targets = []

        def key(index):
            identity_reads.append(index)
            return str(index)

        targets = [SimpleNamespace(get_search_key=lambda i=i: key(i))
                   for i in range(40)]
        application = _Application(_SType())
        application._current_tab = lambda: SimpleNamespace(sobjects=targets)
        tasks = SimpleNamespace(
            _process_choices_for=lambda target: workflow_targets.append(target) or [],
        )
        controller = ColumnsEditorController(application, tasks)
        controller._table_widgets = {
            "tasks": table_widgets.TacticTaskTableWidget(),
            "name": table_widgets.TacticSimpleTableWidget(),
        }
        payload = {"rows": {str(i): {"tasks": {"tasks": []}}
                            for i in range(40)}}
        payload["rows"]["39"] = {"name": {"text": "No task column"}}
        payload["rows"]["missing"] = {"tasks": {"tasks": []}}
        rows = controller._map_rows(payload)
        self.assertEqual(identity_reads, list(range(40)))
        self.assertEqual(workflow_targets, targets[:39])
        self.assertEqual(rows["39"]["name"]["text"], "No task column")
        self.assertEqual(rows["missing"]["tasks"]["tasks"], [])

    def test_column_grouping_uses_rendered_table_values(self):
        application = _Application(_SType())
        model = WorkspaceItemModel()
        model.replace_nodes([
            WorkspaceNode(
                node_id="asset1", node_type="sobject", search_key="asset1",
                code="A1", title="Tree",
            ),
            WorkspaceNode(
                node_id="asset2", node_type="sobject", search_key="asset2",
                code="A2", title="Car",
            ),
        ])
        application.workspace_model = model
        application.group_modes = []

        def set_group_mode(mode):
            application.group_modes.append(mode)
            model.set_organization(group_mode=mode)

        application.set_result_group_mode = set_group_mode
        controller = ColumnsEditorController(application)
        controller.model._records = [{"name": "assets_category_code"}]
        controller._cells = {
            "asset1": {
                "assets_category_code": {"text": "Environment"},
            },
            "asset2": {
                "assets_category_code": {"text": "Vehicle"},
            },
        }

        controller.group_column(0)

        self.assertEqual(
            application.group_modes, ["column:assets_category_code"]
        )
        self.assertEqual(
            [group.title for group in model._root_groups],
            ["Environment", "Vehicle"],
        )

    def test_saved_table_fields_patch_rows_without_refresh(self):
        from unittest.mock import Mock
        from thlib.ui.controllers.item_editing import ItemEditingMixin

        key = "demo/asset?code=ASSET001"
        model = WorkspaceItemModel()
        node = WorkspaceNode(node_id=key, node_type="sobject", search_key=key, code="ASSET001",
                             title="Oak", values={"description": "old"})
        model.replace_nodes([node])
        resets = []
        model.modelReset.connect(lambda: resets.append(True))
        signal = Mock()
        owner = SimpleNamespace(
            _selected_update_started_at=0,
            _selected_update_triggers={"request": ("object.update", {
                "project_code": "demo", "values_by_search_key": {key: {"description": "new"}},
            })},
            _set_loading=Mock(), _notify=Mock(), _transaction_metrics=lambda *args: "",
            _current_tab=lambda: SimpleNamespace(view_mode="table"),
            _current_project_code="demo", workspace_model=model,
            item_fields_updated=signal, refresh_current=Mock(),
        )
        ItemEditingMixin._selected_update_result(owner, (
            [{"__search_key__": key, "description": "server value"}],
            ("request", 1, "description"),
        ))
        owner.refresh_current.assert_not_called()
        signal.emit.assert_called_once_with("demo", [key])
        self.assertEqual(resets, [])
        self.assertIs(model.node_for(key), node)
        self.assertEqual(node.subtitle, "server value")

    def test_changed_table_rows_are_queried_without_clearing_other_cells(self):
        application = _Application(_SType())
        application._current_project_code = "demo"
        application._current_tab = lambda: SimpleNamespace(view_mode="table", sobjects=[])
        controller = ColumnsEditorController(application)
        controller._stype_code = "demo/asset"
        controller._table_widgets = {"name": table_widgets.TacticSimpleTableWidget()}
        controller._data_types = {"name": "varchar"}
        controller._cells = {"edited": {"name": {"text": "old"}},
                             "untouched": {"name": {"text": "keep"}}}
        untouched = controller._cells["untouched"]
        from thlib.environment import env_inst
        with patch.object(env_inst, "server_pool", _Pool()), patch(
            "thlib.tactic_classes.get_table_layout",
            return_value={"rows": {"edited": {"name": {"text": "new"}}}},
        ) as query:
            controller._refresh_changed_rows("demo", ["edited"])
        self.assertEqual(query.call_args.kwargs["search_keys"], ["edited"])
        self.assertIs(controller._cells["untouched"], untouched)
        self.assertEqual(controller.cell("edited", "name")["text"], "new")

    def test_table_dates_use_shared_pretty_and_full_labels(self):
        from thlib.ui.activity import activity_timestamp_labels

        raw = "2024-03-27 00:01:02.977310"
        types = ["timestamp without time zone", "timestamp(6)", "date", "datetime"]
        owner = SimpleNamespace(
            _data_types={name: name for name in types},
            _table_widgets={name: table_widgets.TacticSimpleTableWidget() for name in types},
            _add_task_workflow_rows=lambda *args: None,
            _current_tab=lambda: None,
            _tasks_controller=None,
        )
        payload = {"rows": {"asset": {name: {"text": raw} for name in types}}}
        pretty, full = activity_timestamp_labels(raw)
        self.assertTrue(pretty)
        self.assertTrue(full)
        rows = ColumnsEditorController._map_rows(owner, payload)
        for cell in rows["asset"].values():
            self.assertEqual(cell["text"], pretty)
            self.assertEqual(cell["tooltip"], full)
            self.assertNotIn("977310", cell["tooltip"])
        self.assertEqual(payload["rows"]["asset"]["date"]["text"], raw)
        payload["rows"]["asset"]["date"]["text"] = ""
        self.assertEqual(ColumnsEditorController._map_rows(owner, payload)["asset"]["date"]["text"], "")

        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(errors))
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "Theme.qml")))
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "TacticTableCellDisplay.qml")))
        item = component.createWithInitialProperties({
            "theme": theme, "controller": None, "columnsController": None,
            "userModel": None, "nodeId": "asset", "kind": "text",
            "cell": rows["asset"]["date"], "textValue": pretty,
            "columnIndex": 0, "previewActive": False, "previewUrl": "",
            "previewRevealed": False, "title": "", "accent": "",
            "comments": 0, "tasks": 0, "displayOptions": {},
            "width": 240, "height": 64,
        })
        self.assertIsNotNone(item, component.errors())
        window = QQuickWindow()
        item.setParentItem(window.contentItem())
        window.resize(240, 64)
        window.show()
        try:
            tooltips = [child for child in item.findChildren(QObject)
                        if child.property("text") == full]
            self.assertTrue(tooltips)
            tooltips[0].setProperty("delay", 0)
            QTest.mouseMove(window, QPointF(100, 32).toPoint())
            QTest.qWait(30)
            self.assertTrue(tooltips[0].property("visible"))
            self.assertIn(pretty, [child.property("text") for child in _visual_items(item)])
            self.assertEqual(warnings, [])
        finally:
            window.close()
            item.setParentItem(None)
            item.deleteLater()
            window.deleteLater()

    def test_table_alias_reuses_full_input_field_choices(self):
        payload = _layout_payload()
        column = payload["columns"][1]
        column["actionOptions"] = {"column": "category_code"}
        source = payload["inputWidgets"][1]
        source["name"] = "category_code"
        owner = SimpleNamespace(
            _internal=set(), _protected=set(),
            _view_tree=ColumnsEditorController._view_tree,
            _width=ColumnsEditorController._width,
            _hide_order=ColumnsEditorController._hide_order,
        )
        stype = SimpleNamespace(get_columns_info=lambda: {})
        result = ColumnsEditorController._build_records(owner, stype, payload)
        editor = result[-1]["custom"]
        self.assertEqual(editor["values"], ["oak", "pine"])
        self.assertEqual(editor["labels"], ["Oak", "Pine"])
        self.assertEqual(editor["action_options"]["column"], "category_code")
        self.assertEqual(source["name"], "category_code")

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_edit_widget_query_returns_every_native_select_option(self):
        from thlib import tactic_query

        class FakeSelect:
            def __init__(self):
                self.name = "asset_type"
                self.title = "Asset type"
                self.kwargs = {}

            @staticmethod
            def get_class_name():
                return "pyasm.widget.input_wdg.SelectWdg"

            @staticmethod
            def get_values():
                return ["objects/environment"]

            @staticmethod
            def get_select_values():
                return (
                    ["Environment", "Equipment", "Vehicle"],
                    [
                        "objects/environment",
                        "objects/equipment",
                        "objects/vehicle",
                    ],
                )

        select = FakeSelect()
        edit = SimpleNamespace(
            element_descriptions=[],
            element_names=["asset_type"],
            element_titles=["Asset type"],
            input_prefix="edit",
            kwargs={},
            mode="edit",
            security_denied=False,
            title="Edit",
            explicit_display=lambda: None,
            get_widgets=lambda: [select],
        )
        common_module = ModuleType("pyasm.common")
        common_module.Common = SimpleNamespace(
            create_from_class_path=lambda *_args: edit
        )
        config = SimpleNamespace(
            get_action_options=lambda _name: {},
            get_action_handler=lambda _name: "",
        )
        widget_config_module = ModuleType("pyasm.widget.widget_config")
        widget_config_module.WidgetConfigView = SimpleNamespace(
            get_by_element_names=lambda *_args, **_kwargs: config
        )
        with patch.dict(sys.modules, {
            "pyasm": ModuleType("pyasm"),
            "pyasm.common": common_module,
            "pyasm.widget": ModuleType("pyasm.widget"),
            "pyasm.widget.widget_config": widget_config_module,
        }):
            result = json.loads(tactic_query.query_EditWdg(
                args={"view": "edit"}, search_type="demo/asset"
            ))

        source = result["InputWidgets"][0]
        self.assertEqual(source["labels"], [
            "Environment", "Equipment", "Vehicle",
        ])
        self.assertEqual(source["values"], [
            "objects/environment", "objects/equipment", "objects/vehicle",
        ])
        self.assertEqual(
            source["__display_values__"], ["objects/environment"]
        )

    def test_edit_widget_query_resolves_select_expression_options(self):
        from thlib import tactic_query

        class FakeSelect:
            name = "assets_category_code"
            title = "Assets category"
            kwargs = {
                "values_expr": "@GET(complex/assets_category.code)",
                "labels_expr": "@GET(complex/assets_category.name)",
                "empty": "-- Select --",
            }

            @staticmethod
            def get_class_name():
                return "pyasm.widget.input_wdg.SelectWdg"

            @staticmethod
            def get_values():
                return ["ENV"]

            @staticmethod
            def get_select_values():
                raise AssertionError("current selection is not the option list")

        select = FakeSelect()
        edit = SimpleNamespace(
            element_descriptions=[],
            element_names=["assets_category_code"],
            element_titles=["Assets category"],
            input_prefix="edit",
            kwargs={},
            mode="edit",
            security_denied=False,
            title="Edit",
            explicit_display=lambda: None,
            get_widgets=lambda: [select],
        )
        common_module = ModuleType("pyasm.common")
        common_module.Common = SimpleNamespace(
            create_from_class_path=lambda *_args: edit
        )
        search_module = ModuleType("pyasm.search")
        search_module.Search = SimpleNamespace(eval=lambda expression, **_kwargs: {
            "@GET(complex/assets_category.code)": ["ENV", "EQUIP"],
            "@GET(complex/assets_category.name)": [
                "Environment", "Equipment",
            ],
        }[expression])
        config = SimpleNamespace(
            get_action_options=lambda _name: {},
            get_action_handler=lambda _name: "",
        )
        widget_config_module = ModuleType("pyasm.widget.widget_config")
        widget_config_module.WidgetConfigView = SimpleNamespace(
            get_by_element_names=lambda *_args, **_kwargs: config
        )
        with patch.dict(sys.modules, {
            "pyasm": ModuleType("pyasm"),
            "pyasm.common": common_module,
            "pyasm.search": search_module,
            "pyasm.widget": ModuleType("pyasm.widget"),
            "pyasm.widget.widget_config": widget_config_module,
        }):
            result = json.loads(tactic_query.query_EditWdg(
                args={"view": "edit"}, search_type="demo/asset"
            ))

        source = result["InputWidgets"][0]
        self.assertEqual(source["values"], ["", "ENV", "EQUIP"])
        self.assertEqual(
            source["labels"], ["-- Select --", "Environment", "Equipment"]
        )
        self.assertEqual(
            source["__display_values__"], ["ENV"]
        )
        from thlib.tactic_widgets import TacticSelectWdg

        self.assertEqual(TacticSelectWdg(source).get_editor_options(), [
            {"label": "-- Select --", "value": ""},
            {"label": "Environment", "value": "ENV"},
            {"label": "Equipment", "value": "EQUIP"},
        ])

    def test_table_widgets_map_native_classes_after_server_resolution(self):
        link = table_widgets.create_widget({
            "resolvedClass": "tactic.ui.table.LinkElementWdg",
        })
        self.assertIsInstance(link, table_widgets.TacticLinkTableWidget)
        self.assertEqual(
            link.map_cell({"text": "https://example.invalid"}),
            {
                "text": "https://example.invalid",
                "error": "",
                "kind": "link",
                "href": "https://example.invalid",
            },
        )
        boolean = table_widgets.create_widget({
            "resolvedClass": "tactic.ui.common.SimpleTableElementWdg",
        })
        self.assertEqual(boolean.get_cell_kind("boolean"), "boolean")
        for class_name in (
            "ThumbWdg",
            "pyasm.widget.ThumbWdg",
            "pyasm.widget.file_wdg.ThumbWdg",
        ):
            thumbnail = table_widgets.create_widget({
                "resolvedClass": class_name,
            })
            self.assertIsInstance(
                thumbnail, table_widgets.TacticThumbTableWidget
            )
            self.assertEqual(thumbnail.get_cell_kind(), "thumbnail")
        for class_name in (
            "tactic.ui.widget.DiscussionElementWdg",
            "tactic.ui.widget.discussion_wdg.DiscussionElementWdg",
        ):
            notes = table_widgets.create_widget({
                "resolvedClass": class_name,
            })
            self.assertIsInstance(
                notes, table_widgets.TacticNotesTableWidget
            )
            self.assertEqual(notes.get_cell_kind(), "notes")
        for class_name in (
            "tactic.ui.table.SObjectDetailElementWdg",
            "tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg",
        ):
            detail = table_widgets.create_widget({
                "resolvedClass": class_name,
            })
            self.assertIsInstance(
                detail, table_widgets.TacticSObjectDetailTableWidget
            )
            self.assertEqual(detail.get_cell_kind(), "sobject_detail")
        for class_name in (
            "tactic.ui.table.CheckinButtonElementWdg",
            "tactic.ui.table.table_element_wdg.CheckinButtonElementWdg",
        ):
            checkin = table_widgets.create_widget({
                "resolvedClass": class_name,
            })
            self.assertIsInstance(
                checkin, table_widgets.TacticCheckinTableWidget
            )
            self.assertEqual(checkin.get_cell_kind(), "checkin")
        for class_name in (
            "tactic.ui.table.TaskElementWdg",
            "tactic.ui.table.task_element_wdg.TaskElementWdg",
        ):
            tasks = table_widgets.create_widget({
                "resolvedClass": class_name,
            })
            self.assertIsInstance(
                tasks, table_widgets.TacticTaskTableWidget
            )
            self.assertEqual(tasks.get_cell_kind(), "tasks")
            self.assertEqual(
                tasks.map_cell({
                    "text": "model:In Progress:artist",
                    "error": "",
                })["tasks"][0]["assigned"],
                "artist",
            )
        completion = table_widgets.create_widget({
            "resolvedClass": "tactic.ui.table.TaskCompletionWdg",
        })
        self.assertIsInstance(
            completion, table_widgets.TacticCompletionTableWidget
        )
        self.assertEqual(
            completion.map_cell({"text": "125.0%"})["percent"], 100.0
        )
        action_classes = {
            "tactic.ui.table.ExploreElementWdg": "explorer",
            "tactic.ui.table.SObjectFilesElementWdg": "file_list",
            "tactic.ui.table.MetadataElementWdg": "metadata",
            "tactic.ui.table.DeleteElementWdg": "delete",
        }
        for class_name, kind in action_classes.items():
            self.assertEqual(
                table_widgets.create_widget({
                    "resolvedClass": class_name,
                }).get_cell_kind(),
                kind,
            )

    def test_table_mode_allows_the_shared_preview_request_pipeline(self):
        from thlib.ui.controllers.snapshot_details import SnapshotDetailsMixin

        class Model:
            def __init__(self):
                self.requests = []

            def begin_preview_request(self, node_id):
                self.requests.append(node_id)
                return None

        workspace = Model()
        versions = Model()
        controller = SimpleNamespace(
            results_view_mode="table",
            workspace_model=workspace,
            versions_model=versions,
        )

        SnapshotDetailsMixin.request_item_preview(controller, "asset")

        self.assertEqual(workspace.requests, ["asset"])
        self.assertEqual(versions.requests, ["asset"])

    def test_server_table_query_uses_native_config_and_widget_lifecycle(self):
        from thlib import tactic_query

        class FakeSObject:
            def __init__(self):
                self.values = {
                    "code": "ASSET001", "active": True,
                    "pipeline_code": "asset",
                }

            def get_value(self, name, no_exception=True):
                return self.values.get(name)

        class FakeWidget:
            def __init__(self, name):
                self.name = name
                self.sobjects = []
                self.index = 0

            def set_sobjects(self, sobjects):
                self.sobjects = sobjects

            def preprocess(self):
                self.preprocessed = True

            def set_current_index(self, index):
                self.index = index

            def get_text_value(self):
                return self.sobjects[self.index].get_value(self.name)

            def is_sortable(self):
                return True

        class FakeTask:
            values = {
                "process": "model", "context": "model",
                "status": "In Progress", "assigned": "artist",
                "pipeline_code": "task", "bid_start_date": "2026-09-01",
                "bid_end_date": "2026-09-03",
            }

            @staticmethod
            def get_code():
                return "TASK001"

            def get_value(self, name, no_exception=True):
                return self.values.get(name)

        class TaskElementWdg(FakeWidget):
            status_colors = {"task": {"In Progress": "#4f8cff"}}

            def get_text_value(self):
                return "model:In Progress:artist"

            @staticmethod
            def get_tasks():
                return [FakeTask()]

            @staticmethod
            def get_width():
                return 250

            @staticmethod
            def is_sortable():
                return False

        class ExplorerElementWdg(FakeWidget):
            pass

        class FakeConfig:
            def __init__(self, view):
                self.view = view

            def get_element_names(self):
                if self.view == "edit":
                    return ["code", "reviewer"]
                if self.view == "edit_definition":
                    return ["reviewer"]
                return ["code", "active", "tasks", "explorer"]

            def get_element_titles(self):
                return ["Code", "Active", "Tasks", "Explorer"]

            def get_element_widths(self):
                return [120, 80, None]

            def get_element_attributes(self, name):
                if name == "tasks":
                    return {}
                return {"width": "120" if name == "code" else "80"}

            def get_display_handler(self, name):
                return {
                    "tasks": "tactic.ui.table.TaskElementWdg",
                    "explorer": "tactic.ui.table.ExplorerElementWdg",
                }.get(name, "tactic.ui.common.SimpleTableElementWdg")

            def get_widget_key(self, _name, _kind):
                return "simple"

            def get_type(self, name):
                return "boolean" if name == "active" else "varchar"

            def get_display_options(self, name):
                return {"mode": "repository"} if name == "explorer" else {}

            def get_element_xml(self, name):
                return f'<element name="{name}"/>'

            def get_action_handler(self, _name):
                return ""

            def get_action_options(self, _name):
                return {}

            def get_display_widget(self, name):
                if name == "tasks":
                    return TaskElementWdg(name)
                if name == "explorer":
                    return ExplorerElementWdg(name)
                return FakeWidget(name)

        class FakeWidgetConfigView:
            @staticmethod
            def get_by_search_type(_search_type, view, **_kwargs):
                return FakeConfig(view)

        class FakeSearchType:
            @staticmethod
            def get_columns(search_type, show_hidden=True):
                self.assertEqual(search_type, "demo/asset")
                self.assertFalse(show_hidden)
                return ["code", "active", "tasks", "explorer"]

            @staticmethod
            def get_tactic_type(_search_type, _column):
                return ""

        sobject = FakeSObject()
        search_module = ModuleType("pyasm.search")
        search_module.Search = SimpleNamespace(
            get_by_search_keys=lambda _keys, keep_order: [sobject]
        )
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda value, use_id: (
                "sthpw/task?code=TASK001"
                if isinstance(value, FakeTask)
                else "demo/asset?code=ASSET001"
            )
        )
        search_module.SearchType = FakeSearchType
        search_module.WidgetDbConfig = SimpleNamespace(
            get_by_search_type=lambda *_args: None
        )
        widget_module = ModuleType("pyasm.widget")
        widget_module.WidgetConfigView = FakeWidgetConfigView
        biz_module = ModuleType("pyasm.biz")
        biz_module.Project = SimpleNamespace(
            get_project_client_lib_dir=lambda _sobject, _snapshot: (
                "D:/projects/demo/assets/ASSET001"
            ),
        )
        pyasm_module = ModuleType("pyasm")
        server = SimpleNamespace(
            set_project=lambda _project: None,
            split_search_key=lambda _value: self.fail(
                "A bare Search Type must not be parsed as a search key"
            ),
        )
        with (
            patch.dict(sys.modules, {
                "pyasm": pyasm_module,
                "pyasm.search": search_module,
                "pyasm.widget": widget_module,
                "pyasm.biz": biz_module,
            }),
            patch.object(tactic_query, "server", server, create=True),
        ):
            payload = json.loads(tactic_query.query_table_layout(
                "demo/asset",
                search_keys=["demo/asset?code=ASSET001"],
                project_code="demo",
            ))

        self.assertEqual(
            [column["name"] for column in payload["columns"]],
            ["code", "active", "tasks", "explorer"],
        )
        self.assertTrue(payload["columns"][0]["sortable"])
        self.assertFalse(payload["columns"][2]["sortable"])
        self.assertEqual(payload["columns"][2]["width"], 250)
        available_by_name = {
            column["name"]: column
            for column in payload["availableColumns"]
        }
        self.assertIn("reviewer", available_by_name)
        self.assertTrue(available_by_name["reviewer"]["editSelected"])
        self.assertFalse(available_by_name["active"]["editSelected"])
        self.assertEqual(
            payload["rows"]["demo/asset?code=ASSET001"]["active"]["text"],
            "True",
        )
        self.assertEqual(
            payload["rows"]["demo/asset?code=ASSET001"]
            ["tasks"]["tasks"][0],
            {
                "taskSearchKey": "sthpw/task?code=TASK001",
                "taskCode": "TASK001", "process": "model",
                "context": "model", "status": "In Progress",
                "statusColor": "#4f8cff", "assigned": "artist",
                "bidStart": "2026-09-01", "bidEnd": "2026-09-03",
            },
        )
        self.assertEqual(
            payload["rows"]["demo/asset?code=ASSET001"]
            ["explorer"]["path"],
            "D:/projects/demo/assets/ASSET001",
        )

    def test_columns_editor_preserves_tactic_widget_xml_and_saves_shared_row(self):
        stype = _SType()
        application = _Application(stype)
        from thlib.environment import env_inst
        saved = {}

        def save_widget_config(_search_type, _view, **kwargs):
            saved.update(kwargs)
            return {"config": kwargs["config_xml"]}

        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=_layout_payload(),
            ),
            patch(
                "thlib.tactic_classes.save_widget_config",
                side_effect=save_widget_config,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            self.assertEqual(
                [record["name"] for record in controller.model._records],
                ["code", "custom", "name"],
            )
            self.assertEqual(
                [column["row"] for column in controller.visibleColumns],
                [0, 1],
            )
            self.assertFalse(controller.model._records[2]["displayVisible"])
            self.assertEqual(controller.model._records[0]["cellKind"], "link")
            self.assertTrue(controller.visibleColumns[0]["sortable"])
            self.assertEqual(controller.visibleColumns[0]["hideOrder"], 0)
            controller.move(0, 1)
            self.assertEqual(
                [record["name"] for record in controller.model._records],
                ["custom", "code", "name"],
            )
            controller.move(1, -1)
            controller.sort_column(0, True)
            self.assertEqual(
                application.sort_modes[-1], "column:code:desc"
            )
            self.assertEqual(
                controller.cell(
                    "demo/asset?code=ASSET001", "code"
                )["href"],
                "https://example.invalid/ASSET001",
            )
            controller.set_label(0, "Asset code")
            controller.set_width(0, 144)
            controller.set_hide_order(0, 2)
            controller.set_visible(1, False)
            controller.set_visible(2, True)
            self.assertTrue(controller.apply())

        root = ElementTree.fromstring(saved["config_xml"])
        self.assertEqual(root.get("marker"), "keep")
        self.assertEqual(root.find("other").get("value"), "keep")
        elements = root.findall("./table/element")
        self.assertEqual(
            [element.get("name") for element in elements],
            ["code", "name", "__search_key__"],
        )
        self.assertEqual(elements[0].get("title"), "Asset code")
        self.assertEqual(elements[0].get("width"), "144")
        self.assertEqual(elements[0].get("th_hide_order"), "2")
        self.assertEqual(
            elements[0].find("./display/option").text, "keep"
        )
        self.assertEqual(elements[-1].get("internal"), "keep")
        self.assertFalse(controller.dirty)

    def test_table_view_presets_are_native_and_selected_per_tab(self):
        stype = _SType()
        application = _Application(stype)
        preset_xml = TABLE_XML.replace(
            "<table>",
            '<th_table_review layout="TableLayoutWdg">',
        ).replace("</table>", "</th_table_review>").replace(
            '<config marker="keep">',
            '<config marker="keep" th_table_view_title="Review">',
        )
        stype.project.views.config_dict.append({
            "code": "WIDGET003", "view": "th_table_review", "login": "",
            "search_type": "demo/asset", "config": preset_xml,
        })
        stype.project.views.config_dict.append({
            "code": "WIDGET999", "view": "th_table_other", "login": "",
            "search_type": "demo/shot",
            "config": preset_xml.replace(
                "th_table_review", "th_table_other"
            ),
        })
        requested_views = []

        def get_table_layout(_search_type, **kwargs):
            view = kwargs.get("view", "table")
            requested_views.append(view)
            payload = _layout_payload()
            payload["view"] = view
            config = next(
                record["config"]
                for record in stype.project.views.config_dict
                if record["view"] == view
            )
            payload["databaseViews"][view] = {
                "code": "WIDGET", "config": config,
            }
            return payload

        def save_widget_config(_search_type, view, **kwargs):
            return {
                "code": "WIDGET004", "view": view,
                "config": kwargs["config_xml"],
            }

        from thlib.environment import env_inst
        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                side_effect=get_table_layout,
            ),
            patch(
                "thlib.tactic_classes.save_widget_config",
                side_effect=save_widget_config,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            review_row = next(
                row for row, record in enumerate(controller.tableViews)
                if record["view"] == "th_table_review"
            )
            self.assertNotIn(
                "th_table_other",
                [record["view"] for record in controller.tableViews],
            )
            self.assertTrue(controller.select_table_view(review_row))
            self.assertEqual(application.tab.table_view, "th_table_review")
            self.assertEqual(controller.currentTableView, "th_table_review")
            self.assertTrue(controller.save_table_view_as("Lighting Review"))
            first_tab = application.tab
            application.tab = SimpleNamespace(
                stype=stype, sobjects=[], view_mode="table",
                table_view="table",
            )
            controller.reload()
            self.assertEqual(controller.currentTableView, "table")
            self.assertEqual(
                first_tab.table_view, "th_table_lighting_review"
            )

        self.assertEqual(
            first_tab.table_view, "th_table_lighting_review"
        )
        self.assertIn("th_table_review", requested_views)
        self.assertIn("th_table_lighting_review", requested_views)
        self.assertGreaterEqual(application.search_cache_saves, 2)

    def test_task_workflow_adds_empty_process_and_creates_it_on_edit(self):
        target_key = "demo/asset?code=ASSET001"

        class Target:
            @staticmethod
            def get_search_key():
                return target_key

            @staticmethod
            def get_project():
                return SimpleNamespace(get_code=lambda: "demo")

        class TaskHelpers:
            @staticmethod
            def _process_choices_for(_target):
                return [
                    {"value": "model", "label": "Model", "color": "#5577aa"},
                    {"value": "rig", "label": "Rig", "color": "#8855aa"},
                ]

            @staticmethod
            def _process_task_defaults(_target, process):
                return {
                    "status": "Pending" if process == "rig" else "",
                    "assigned": "", "start": "", "end": "",
                }

            @staticmethod
            def _native_process_task_defaults(_target, process):
                return {"process": process, "context": process}

            @staticmethod
            def _login_label(login):
                return {"artist": "Artist"}.get(str(login or ""), "")

            @staticmethod
            def _status_choices_for(_target, _process):
                return [
                    {"label": "Pending", "value": "Pending", "color": "#999999"},
                    {"label": "Ready", "value": "Ready", "color": "#44aa66"},
                ]

            @staticmethod
            def _with_current_status(choices, _status, _fallback):
                return choices

            @staticmethod
            def _user_choices_for(_target, _process, include_login=""):
                return [
                    {"label": "Not assigned", "value": ""},
                    {"label": "Artist", "value": "artist"},
                ]

        target = Target()
        application = _Application(_SType())
        application._current_tab = lambda: SimpleNamespace(
            stype=application.stype, sobjects=[target], view_mode="table"
        )
        application.workspace_model = SimpleNamespace(
            node_for=lambda _node_id: SimpleNamespace(source=target)
        )
        controller = ColumnsEditorController(application, TaskHelpers())
        controller._stype_code = "demo/asset"
        cells = {"tasks": {"tasks": [{
            "taskSearchKey": "sthpw/task?code=TASK001",
            "taskCode": "TASK001", "process": "model",
            "status": "In Progress", "assigned": "artist",
        }]}}
        controller._add_task_workflow_rows(target, cells)

        self.assertEqual(
            [record["process"] for record in cells["tasks"]["tasks"]],
            ["model", "rig"],
        )
        rig = cells["tasks"]["tasks"][1]
        self.assertFalse(rig["hasTask"])
        self.assertEqual(rig["status"], "Pending")
        controller._cells = {target_key: cells}

        from thlib.environment import env_inst
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch("thlib.tactic_classes.insert_sobjects", return_value={}),
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset", "", "rig", "status", "Ready"
            ))
            self.assertTrue(controller.save_task_changes())
        self.assertIn("created task identity", controller.error)
        self.assertFalse(rig["hasTask"])
        self.assertEqual(controller.dirtyTaskCount, 1)

        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch(
                "thlib.tactic_classes.insert_sobjects",
                return_value={
                    "__search_key__": "sthpw/task?code=TASK002",
                    "code": "TASK002",
                },
            ) as insert,
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset", "", "rig", "status", "Ready"
            ))
            self.assertTrue(controller.save_task_changes())

        insert.assert_called_once()
        created = cells["tasks"]["tasks"][1]
        self.assertTrue(created["hasTask"])
        self.assertEqual(created["taskCode"], "TASK002")
        self.assertEqual(created["status"], "Ready")
        self.assertEqual(created["statusColor"], "#44aa66")

        updates = []
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch(
                "thlib.tactic_classes.server_start",
                return_value=SimpleNamespace(
                    update=lambda *args, **kwargs:
                    updates.append((args, kwargs)) or {}
                ),
            ) as server_start,
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset", created["taskSearchKey"], "rig",
                "assigned", "artist",
            ))
            self.assertTrue(controller.save_task_changes())

        server_start.assert_called_once_with(project="demo")
        self.assertEqual(updates, [(
            (
                "sthpw/task?code=TASK002",
                {"assigned": "artist"},
            ),
            {"triggers": True},
        )])
        self.assertEqual(created["assigned"], "artist")
        self.assertEqual(created["assignedLabel"], "Artist")

        updates.clear()
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch(
                "thlib.tactic_classes.server_start",
                return_value=SimpleNamespace(
                    update=lambda *args, **kwargs:
                    updates.append((args, kwargs)) or {}
                ),
            ),
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset", created["taskSearchKey"], "rig",
                "bid_start_date", "2026-09-01 09:00:00",
            ))
            self.assertTrue(controller.set_task_value(
                "asset", created["taskSearchKey"], "rig",
                "bid_end_date", "2026-09-03 18:00:00",
            ))
            draft = controller.row_cells(target_key)["tasks"]["tasks"][1]
            self.assertEqual(draft["bidStart"], "2026-09-01 09:00:00")
            self.assertEqual(draft["bidEnd"], "2026-09-03 18:00:00")
            self.assertTrue(draft["bidStartLabel"])
            self.assertTrue(draft["bidEndLabel"])
            self.assertTrue(controller.save_task_changes())

        self.assertEqual(updates[0][0][1], {
            "bid_start_date": "2026-09-01 09:00:00",
            "bid_end_date": "2026-09-03 18:00:00",
        })
        self.assertEqual(created["bidStart"], "2026-09-01 09:00:00")
        self.assertEqual(created["bidEnd"], "2026-09-03 18:00:00")

    def test_task_workflow_edits_every_selected_sobject(self):
        class Target:
            def __init__(self, code):
                self.code = code

            def get_search_key(self):
                return f"demo/asset?code={self.code}"

            @staticmethod
            def get_project():
                return SimpleNamespace(get_code=lambda: "demo")

        class TaskHelpers:
            @staticmethod
            def _native_process_task_defaults(_target, process):
                return {"process": process, "context": process}

            @staticmethod
            def _login_label(login):
                return str(login or "")

            @staticmethod
            def _status_choices_for(_target, _process):
                return [
                    {"value": "Pending", "color": "#999999"},
                    {"value": "Ready", "color": "#44aa66"},
                ]

            @staticmethod
            def _with_current_status(choices, _status, _fallback):
                return choices

            @staticmethod
            def _user_choices_for(_target, _process, include_login=""):
                return []

            @staticmethod
            def _process_choices_for(_target):
                return [{"value": "rig", "color": "#8855aa"}]

        targets = {
            f"asset{number}": Target(f"ASSET00{number}")
            for number in range(1, 4)
        }
        application = _Application(_SType())
        selected = list(targets)
        application._current_tab = lambda: SimpleNamespace(
            stype=application.stype,
            sobjects=list(targets.values()),
            selected_node_ids=selected,
            view_mode="table",
        )
        application.workspace_model = SimpleNamespace(
            node_for=lambda node_id: SimpleNamespace(
                source=targets.get(node_id)
            ) if node_id in targets else None
        )
        controller = ColumnsEditorController(application, TaskHelpers())
        controller._stype_code = "demo/asset"
        records = {}
        for number, target in enumerate(targets.values(), 1):
            existing = number < 3
            task = {
                "taskSearchKey": (
                    f"sthpw/task?code=TASK00{number}" if existing else ""
                ),
                "taskCode": f"TASK00{number}" if existing else "",
                "process": "rig",
                "context": "rig",
                "status": "Pending",
                "assigned": "",
                "hasTask": existing,
            }
            records[target.get_search_key()] = {"tasks": {"tasks": [task]}}
        controller._cells = records

        batches = []
        server = SimpleNamespace(
            update_multiple=lambda **kwargs: batches.append(kwargs),
        )
        from thlib.environment import env_inst
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch(
                "thlib.tactic_classes.insert_sobjects",
                return_value={
                    "__search_key__": "sthpw/task?code=TASK003",
                    "code": "TASK003",
                },
            ) as insert,
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset1", "sthpw/task?code=TASK001",
                "rig", "status", "Ready",
            ))
            self.assertEqual(batches, [])
            insert.assert_not_called()
            self.assertEqual(controller.dirtyTaskCount, 3)
            self.assertTrue(controller.set_task_value(
                "asset1", "sthpw/task?code=TASK001", "rig", "status", "Pending",
            ))
            self.assertEqual(controller.dirtyTaskCount, 0)
            self.assertTrue(controller.set_task_value(
                "asset1", "sthpw/task?code=TASK001", "rig", "status", "Ready",
            ))
            self.assertEqual(controller.row_cells("demo/asset?code=ASSET001")["tasks"]["tasks"][0]["status"], "Ready")
            self.assertEqual(records["demo/asset?code=ASSET001"]["tasks"]["tasks"][0]["status"], "Pending")
            controller.discard_task_changes()
            self.assertEqual(controller.dirtyTaskCount, 0)
            self.assertTrue(controller.set_task_value(
                "asset1", "sthpw/task?code=TASK001", "rig", "status", "Ready",
            ))
            self.assertTrue(controller.save_task_changes())

        self.assertEqual(batches, [{
            "data": {
                "sthpw/task?code=TASK001": {"status": "Ready"},
                "sthpw/task?code=TASK002": {"status": "Ready"},
            },
            "triggers": True,
        }])
        insert.assert_called_once_with(
            "sthpw/task", "demo",
            {"process": "rig", "context": "rig", "status": "Ready"},
            parent_key="demo/asset?code=ASSET003", triggers=True,
        )
        self.assertEqual(
            [
                row["tasks"]["tasks"][0]["status"]
                for row in records.values()
            ],
            ["Ready", "Ready", "Ready"],
        )
        self.assertEqual(application.notifications, ["Task saved"])

        selected[:] = ["asset2", "asset3"]
        batches.clear()
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch("thlib.server_cache.invalidate_domains"),
        ):
            self.assertTrue(controller.set_task_value(
                "asset1", "sthpw/task?code=TASK001",
                "rig", "status", "Pending",
            ))
            self.assertEqual(batches, [])
            self.assertTrue(controller.save_task_changes())
        self.assertEqual(batches, [{
            "data": {
                "sthpw/task?code=TASK002": {"status": "Pending"},
                "sthpw/task?code=TASK003": {"status": "Pending"},
            },
            "triggers": True,
        }])
        self.assertEqual(
            [
                row["tasks"]["tasks"][0]["status"]
                for row in records.values()
            ],
            ["Ready", "Pending", "Pending"],
        )

    def test_definition_catalog_lists_search_types_and_saves_exact_record(self):
        application = _Application(_SType())
        application.stype.project.get_stypes = lambda: {
            code: SimpleNamespace(
                get_code=lambda value=code: value,
                get_pretty_name=lambda value=title: value,
            )
            for code, title in (
                ("demo/asset", "Assets"),
                ("demo/note", "Notes"),
            )
        }
        application.stype.project.views.config_dict.extend([
            {
                "code": "WIDGET002", "view": "archive_assets", "login": "",
                "search_type": "demo/asset", "config": "<config/>",
            },
            {
                "code": "WIDGET003", "view": "table", "login": "artist",
                "search_type": "demo/shot", "config": "<config/>",
            },
        ])
        updates = []
        server = SimpleNamespace(
            query=lambda search_type, *_args, **_kwargs: (
                [{"code": "demo/shot", "title": "Shot Registry"}]
                if search_type == "sthpw/search_object"
                else list(application.stype.project.views.config_dict)
            ),
            build_search_key=lambda _stype, code, **_kwargs:
                f"config/widget_config?code={code}",
            insert_update=lambda key, data, **kwargs:
                updates.append((key, data, kwargs)),
        )
        from thlib.environment import env_inst
        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=_layout_payload(),
            ),
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch.object(env_inst, "server_pool", _Pool()),
            patch.object(
                env_inst, "get_project_by_code",
                return_value=application.stype.project,
            ),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            controller.load_definition_catalog("demo")
            catalog = controller.definitionCatalog
            self.assertEqual(len(catalog), 3)
            self.assertEqual(catalog[0]["searchType"], "demo/asset")
            self.assertNotIn("current", catalog[0])
            self.assertEqual(
                {record["searchType"] for record in catalog},
                {"demo/asset", "demo/shot"},
            )
            self.assertEqual(
                controller.definitionCatalogSearchTypes,
                [
                    {"value": "demo/asset", "label": "Assets · demo/asset"},
                    {"value": "demo/note", "label": "Notes · demo/note"},
                    {"value": "demo/shot", "label": "Shot Registry · demo/shot"},
                ],
            )
            next_stype = _SType()
            next_stype.project = application.stype.project
            next_stype.get_code = lambda: "demo/shot"
            application.stype = next_stype
            controller.reload()
            catalog = controller.definitionCatalog
            self.assertEqual(catalog[0]["searchType"], "demo/asset")
            row = next(
                record["row"] for record in catalog
                if record["code"] == "WIDGET003"
            )
            source = (
                '<config marker="keep"><!--keep--><table marker="keep">'
                '<element name="code" title="Code" hidden="false" '
                'width="146px" custom="keep"><display class="LinkWdg">'
                '<option>keep</option></display></element></table>'
                '<other value="keep"/></config>'
            )
            wizard = controller.catalog_wizard(source)
            self.assertTrue(wizard["supported"])
            self.assertEqual(wizard["view"], "table")
            self.assertEqual(wizard["elements"], [{
                "path": "1/0", "name": "code", "title": "Code",
                "visible": True, "width": 146, "widget": "LinkWdg",
            }])
            for field, value in (
                ("title", "Asset code"),
                ("visible", "false"),
                ("width", "208"),
                ("widget", "link"),
            ):
                source = controller.update_catalog_wizard(
                    source, "1/0", field, value
                )
            tree = ElementTree.fromstring(source)
            element = tree.find("table/element")
            self.assertEqual(element.get("title"), "Asset code")
            self.assertEqual(element.get("hidden"), "true")
            self.assertEqual(element.get("width"), "208")
            self.assertEqual(element.get("custom"), "keep")
            self.assertEqual(element.find("display").get("widget"), "link")
            self.assertEqual(element.findtext("display/option"), "keep")
            self.assertEqual(tree.find("other").get("value"), "keep")
            self.assertIn("<!--keep-->", source)
            self.assertFalse(controller.save_catalog_xml(row, "<config>"))
            self.assertTrue(controller.save_catalog_xml(
                row, "<config><table/></config>"
            ))

        self.assertEqual(updates, [(
            "config/widget_config?code=WIDGET003",
            {"config": "<config><table/></config>"},
            {"triggers": False},
        )])
        self.assertEqual(
            application.stype.project.views.config_dict[2]["config"],
            "<config><table/></config>",
        )
        application.stype.project.views.config_dict[2]["config"] = "<config><table marker=\"external\"/></config>"
        with (
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            self.assertTrue(controller.save_catalog_xml(row, "<config><table marker=\"stale\"/></config>"))
        self.assertIn("Reload before saving", controller.error)
        self.assertEqual(len(updates), 1)

    def test_catalog_unknown_write_requires_readback_and_local_start_failure_is_safe(self):
        application = _Application(_SType())
        controller = ColumnsEditorController(application)
        records = application.stype.project.views.config_dict
        controller._set_definition_catalog('demo', application.stype.project, records, {})
        controller._catalog_saving = True
        controller._failed(({'exception': 'Connection lost after write'}, None))
        self.assertTrue(controller.catalogUncertain)
        with patch.object(controller, '_run') as run:
            self.assertFalse(controller.save_catalog_xml(0, '<config/>'))
            run.assert_not_called()
        controller._set_definition_catalog('demo', application.stype.project, records, {})
        self.assertFalse(controller.catalogUncertain)
        with patch.object(controller, '_run', return_value=False):
            self.assertFalse(controller.save_catalog_xml(0, '<config/>'))
        self.assertFalse(controller.catalogUncertain)
        self.assertFalse(controller._catalog_saving)

    def test_definition_catalog_uses_selected_admin_project_not_search_tab(self):
        application = _Application(_SType())
        other_project = _Project()
        records = {
            "demo": [{
                "code": "DEMO001", "view": "table",
                "search_type": "demo/asset", "config": "<config/>",
            }],
            "other": [{
                "code": "OTHER001", "view": "table",
                "search_type": "other/shot", "config": "<config/>",
            }],
        }
        queried = []

        def server_start(*, project):
            queried.append(project)
            return SimpleNamespace(
                query=lambda *_args, **_kwargs: records[project]
            )

        from thlib.environment import env_inst
        with (
            patch.object(env_inst, "server_pool", _Pool()),
            patch.object(
                env_inst, "get_project_by_code",
                side_effect=lambda code: {
                    "demo": application.stype.project,
                    "other": other_project,
                }[code],
            ),
            patch("thlib.tactic_classes.server_start", side_effect=server_start),
        ):
            controller = ColumnsEditorController(application)
            with patch.object(
                controller, "_current_stype",
                side_effect=AssertionError("catalog must not use search tab"),
            ):
                controller.load_definition_catalog("other")
                stale_request = controller._catalog_request_id
                self.assertEqual(queried, ["other"])
                self.assertEqual(
                    controller.definitionCatalog[0]["searchType"],
                    "other/shot",
                )
                controller.load_definition_catalog("demo")
                controller._definition_catalog_loaded_from_server((
                    stale_request, "other", other_project, records["other"], {}
                ))
                self.assertEqual(queried, ["other", "demo"])
                self.assertEqual(
                    controller.definitionCatalog[0]["searchType"],
                    "demo/asset",
                )
                self.assertEqual(application._current_project_code, "demo")
                with patch.object(controller, "_run", return_value=True) as run:
                    controller.reload_definition_catalog("other")
                    controller.load_definition_catalog("other")
                    self.assertEqual(run.call_count, 1)

    def test_columns_editor_reloads_context_after_worker_finishes(self):
        application = _Application(_SType())
        from thlib.environment import env_inst
        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                side_effect=lambda search_type, **_kwargs: _layout_payload(
                    search_type
                ),
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            next_stype = _SType()
            next_stype.get_code = lambda: "demo/shot"
            application.stype = next_stype
            application.tab.stype = next_stype
            worker = object()
            controller._workers.add(worker)
            controller._busy = True

            controller._release(worker)

        self.assertEqual(controller._stype_code, "demo/shot")

    def test_columns_editor_resolves_native_edit_widget_payload(self):
        from xmlrpc.client import Fault
        application = _Application(_SType())
        sobject = SimpleNamespace(
            get_search_key=lambda: "demo/asset?code=ASSET001"
        )
        application._current_tab = lambda: SimpleNamespace(
            stype=application.stype,
            sobjects=[sobject],
            view_mode="table",
        )
        payload = _layout_payload()
        payload.pop("inputWidgets")
        from thlib.environment import env_inst

        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=payload,
            ),
            patch(
                "thlib.tactic_classes.execute_procedure_serverside",
                side_effect=[Fault(1, "('count of sudo: ', 0)"), {
                    "InputWidgets": _layout_payload()["inputWidgets"]
                }],
            ) as execute,
            patch("thlib.request_retry.time.sleep"),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()

        args = execute.call_args.args[1]["args"]
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(args["view"], "edit")
        self.assertEqual(
            args["search_key"], "demo/asset?code=ASSET001"
        )
        self.assertTrue(controller.model._records[1]["editable"])

    def test_appended_page_fetches_only_missing_table_cells(self):
        application = _Application(_SType())
        first = SimpleNamespace(
            get_search_key=lambda: "demo/asset?code=ASSET001"
        )
        second = SimpleNamespace(
            get_search_key=lambda: "demo/asset?code=ASSET002"
        )
        tab = SimpleNamespace(
            stype=application.stype, sobjects=[first], view_mode="table"
        )
        application._current_tab = lambda: tab
        base = _layout_payload()
        base_row = base["rows"]["demo/asset?code=ASSET001"]
        calls = []

        def get_table_layout(_search_type, **kwargs):
            keys = list(kwargs["search_keys"])
            calls.append(keys)
            payload = json.loads(json.dumps(base))
            payload["rows"] = {
                key: {
                    **json.loads(json.dumps(base_row)),
                    "custom": {
                        "text": "Pine" if key.endswith("002") else "Oak",
                        "kind": "text", "error": "",
                    },
                }
                for key in keys
            }
            return payload

        from thlib.environment import env_inst
        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                side_effect=get_table_layout,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            self.assertEqual(calls, [[], [first.get_search_key()]])
            tab.sobjects.append(second)
            application.search_state_changed.emit()

        self.assertEqual(calls[-1], [second.get_search_key()])
        self.assertEqual(
            controller.row_cells(second.get_search_key())["custom"]["text"],
            "Pine",
        )
        self.assertGreaterEqual(controller.cellRevision, 3)

    def test_element_definition_save_keeps_nested_options_and_target_view(self):
        application = _Application(_SType())
        from thlib.environment import env_inst
        saved = {}

        def save_widget_config(search_type, view, **kwargs):
            saved.update({"search_type": search_type, "view": view, **kwargs})
            return {"config": kwargs["element_xml"]}

        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=_layout_payload(),
            ),
            patch(
                "thlib.tactic_classes.save_widget_config",
                side_effect=save_widget_config,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            xml = controller.element_xml(0, "definition")
            element = ElementTree.fromstring(xml)
            element.find("display/icon").text = "FA_EXTERNAL_LINK"
            self.assertTrue(controller.save_element_xml(
                0, "definition",
                ElementTree.tostring(element, encoding="unicode"),
            ))

        self.assertEqual(saved["search_type"], "demo/asset")
        self.assertEqual(saved["view"], "definition")
        self.assertEqual(
            ElementTree.fromstring(saved["element_xml"])
            .find("display/icon").text,
            "FA_EXTERNAL_LINK",
        )

    def test_edit_definition_uses_shared_select_descriptor_and_edit_view(self):
        application = _Application(_SType())
        source = SimpleNamespace(
            get_info=lambda: {"custom": "pine"},
            get_value=lambda name: "pine" if name == "custom" else "",
        )
        application.workspace_model = SimpleNamespace(
            node_for=lambda node_id: SimpleNamespace(source=source)
            if node_id == "asset" else None
        )
        from thlib.environment import env_inst
        saved_views = []
        layout = _layout_payload()
        layout["databaseViews"].update({
            "edit": {
                "code": "WIDGET003",
                "config": (
                    '<config><edit><element name="code"/>'
                    '<element name="custom"/><element name="name"/>'
                    '</edit></config>'
                ),
            },
            "edit_definition": {
                "code": "WIDGET004",
                "config": (
                    '<config><edit_definition><element name="custom">'
                    '<display class="pyasm.widget.input_wdg.SelectWdg">'
                    '<values>oak|pine</values><keep>native</keep>'
                    '</display></element></edit_definition></config>'
                ),
            },
        })

        def save_widget_config(_search_type, view, **kwargs):
            saved_views.append((view, dict(kwargs)))
            return {"view": view}

        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=layout,
            ),
            patch(
                "thlib.tactic_classes.save_widget_config",
                side_effect=save_widget_config,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            descriptor = controller.cell_editor("asset", "custom")
            self.assertEqual(descriptor["fieldType"], "enum")
            self.assertEqual(descriptor["fieldValue"], "pine")
            self.assertEqual(
                descriptor["fieldOptions"],
                [
                    {"label": "Oak", "value": "oak"},
                    {"label": "Pine", "value": "pine"},
                ],
            )
            form = controller.element_form(1, "edit_definition")
            self.assertEqual(
                form["widget"], "pyasm.widget.input_wdg.SelectWdg"
            )
            self.assertEqual(form["values"], "oak|pine")
            self.assertTrue(controller.save_element_visual(
                1,
                "edit_definition",
                {
                    **form,
                    "included": False,
                    "required": True,
                    "description": "Choose a tree",
                    "labels": "Oak|Pine",
                },
            ))

        self.assertEqual(
            [view for view, _kwargs in saved_views],
            ["edit_definition", "edit"],
        )
        definition = ElementTree.fromstring(
            saved_views[0][1]["element_xml"]
        )
        self.assertEqual(
            definition.find("display").attrib,
            {"class": "pyasm.widget.input_wdg.SelectWdg"},
        )
        self.assertEqual(definition.findtext("display/keep"), "native")
        self.assertEqual(definition.findtext("display/required"), "true")
        self.assertEqual(
            definition.findtext("display/description"), "Choose a tree"
        )
        edit = ElementTree.fromstring(saved_views[1][1]["config_xml"])
        self.assertEqual(
            [element.get("name") for element in edit.findall(".//element")],
            ["code", "name"],
        )

    def test_table_projection_contains_only_sobjects(self):
        model = WorkspaceItemModel()
        model.replace_nodes([
            WorkspaceNode(
                node_id="asset", node_type="sobject", search_key="asset",
                code="ASSET", title="Asset",
            ),
            WorkspaceNode(
                node_id="process", node_type="process", search_key="asset",
                code="publish", title="Publish",
            ),
        ])
        model.show_table_rows()
        self.assertEqual([node.node_type for node in model._items], ["sobject"])

    def test_notes_are_centered_in_tall_table_cells(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "TacticTableCellDisplay.qml"))
        )
        cell = component.createWithInitialProperties({
            "theme": theme,
            "controller": _TableController(),
            "columnsController": _TableColumns(),
            "userModel": RecordListModel(("login",)),
            "nodeId": "asset",
            "kind": "notes",
            "cell": {},
            "textValue": "",
            "columnIndex": 0,
            "previewActive": False,
            "previewUrl": "",
            "previewRevealed": False,
            "title": "Asset",
            "accent": "",
            "comments": 7,
            "tasks": 0,
            "displayOptions": {},
            "width": 180,
            "height": 180,
        })
        self.assertIsNotNone(
            cell, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        cell.setParentItem(window.contentItem())
        window.resize(180, 180)
        window.show()
        QTest.qWait(20)
        note_list = cell.findChild(QQuickItem, "tableNoteList")
        self.assertAlmostEqual(
            note_list.y(), (cell.height() - note_list.height()) / 2, delta=1
        )
        note_record = next(
            item for item in _visual_items(cell)
            if item.objectName() == "tableNoteRecord_0"
        )
        self.assertEqual(note_record.property("processTitle"), "Rigging")
        self.assertEqual(note_record.property("accentColor").name(), "#42a5f5")
        cell.setHeight(58)
        QTest.qWait(1)
        self.assertEqual(note_list.y(), 4)
        self.assertGreater(note_list.property("contentHeight"), note_list.height())
        window.close()
        window.deleteLater()

    def test_table_preview_width_sizes_row_and_task_content_fits(self):
        engine = QQmlEngine()
        controller = _TableController()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id="asset", node_type="sobject",
            search_key="demo/asset?code=ASSET001", code="ASSET001",
            title="Tree", preview_source=object(),
        )])
        columns = _TableColumns()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
            "avatarColor", "email", "primaryGroup",
        ))
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml"))
        )
        table = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "columnsController": columns,
            "resultModel": model,
            "userModel": users,
            "presentationActive": True,
            "widthOverrides": {"preview": 128},
            "width": 900,
            "height": 240,
        })
        self.assertIsNotNone(
            table, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        table.setParentItem(window.contentItem())
        window.resize(900, 240)
        window.show()
        try:
            QTest.qWait(50)
            actions = table.findChild(QQuickItem, "tableTaskDraftActions")
            self.assertFalse(actions.isVisible())
            columns._dirty_task_count = 3
            columns.stateChanged.emit()
            QTest.qWait(20)
            self.assertTrue(actions.isVisible())
            save = table.findChild(QQuickItem, "saveTableTaskChanges")
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                             save.mapToScene(QPointF(save.width() / 2, save.height() / 2)).toPoint())
            self.assertEqual(columns.task_save_calls, 1)
            self.assertFalse(actions.isVisible())
            table.setProperty("widthOverrides", {"preview": 128})
            rows = table.findChild(QQuickItem, "searchResultsTableView")
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(100)
            self.assertEqual(table.property("effectiveRowHeight"), 58)
            header = table.findChild(QObject, "searchResultTableHeader")
            header_surface = table.findChild(QQuickItem, "tableHeaderSurface")
            self.assertEqual(header_surface.height(), 34)
            self.assertEqual(header_surface.property("radius"), 0)
            self.assertEqual(rows.x(), 0)
            self.assertEqual(rows.y(), 0)
            self.assertEqual(header_surface.property("color"), theme.property("surfaceContainer"))
            for item in _visual_items(table):
                if item.objectName() in {"tableSelectionSurface", "tableActionSurface"}:
                    self.assertEqual(QQmlProperty(item, "border.width").read(), 0)
            header.rowHeightRequested.emit(0)
            QTest.qWait(20)
            named = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertEqual(named["searchResultTableRow"].height(), 128)
            self.assertEqual(named["tableCellPreview"].width(), 120)
            preview = named["tableCellPreview"]
            self.assertTrue(preview.property("round"))
            self.assertEqual(preview.property("fillMode"), 2)  # PreserveAspectCrop
            self.assertEqual(preview.width(), preview.height())
            header = table.findChild(QObject, "searchResultTableHeader")
            header.rowHeightRequested.emit(52)
            QTest.qWait(20)
            self.assertEqual(preview.width(), 44)
            self.assertEqual(preview.height(), 44)
            self.assertAlmostEqual(
                preview.x() + preview.width() / 2,
                preview.parentItem().width() / 2,
            )
            self.assertEqual(
                next(
                    item for item in _visual_items(table)
                    if item.objectName() == "searchResultTableRow"
                ).height(),
                52,
            )
            header.rowHeightRequested.emit(0)
            QTest.qWait(20)
            self.assertEqual(
                next(
                    item for item in _visual_items(table)
                    if item.objectName() == "searchResultTableRow"
                ).height(),
                128,
            )
            table.setProperty("automaticRowHeight", False)
            table.setProperty("rowHeight", 68)
            table.setProperty("widthOverrides", {"preview": 64})
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(20)
            named = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertEqual(named["searchResultTableRow"].height(), 68)
            table.setProperty("rowHeight", 52)
            table.setProperty(
                "widthOverrides", {"preview": 48, "tasks": 170}
            )
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(100)
            named = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertEqual(named["searchResultTableRow"].height(), 52)
            status = named["tableTaskStatus_0"]
            assignee = named["tableTaskAssignee_0"]
            avatar = next((item for item in _visual_items(assignee)
                           if item.objectName() == "taskTableCellAvatar"), None)
            self.assertIsNotNone(avatar)
            self.assertLessEqual(status.y() + status.height(), assignee.y())
            self.assertLessEqual(avatar.height(), assignee.height() - 4)
            status_width = status.width()
            QTest.mouseMove(
                window,
                status.mapToScene(QPointF(
                    status.width() / 2, status.height() / 2
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(status.width(), status_width)
            self.assertFalse(status.property("editorLoaded"))
            row = named["searchResultTableRow"]
            preview_cell = named["tableCellPreview"]
            QTest.mouseMove(
                window,
                preview_cell.mapToScene(QPointF(
                    preview_cell.width() / 2, preview_cell.height() / 2
                )).toPoint(),
            )
            QTest.qWait(550)
            task_cell = next(
                item for item in _visual_items(table)
                if item.objectName() == "tableTaskCell"
            )
            task_preview = task_cell.findChild(
                QObject, "tableTaskCardsPreview"
            )
            self.assertIsNotNone(task_preview)
            self.assertFalse(task_preview.property("opened"))
            QTest.mouseMove(
                window,
                task_cell.mapToScene(QPointF(
                    10, task_cell.height() / 2
                )).toPoint(),
            )
            QTest.qWait(550)
            self.assertTrue(task_preview.property("opened"))
            QTest.mouseMove(
                window,
                preview_cell.mapToScene(QPointF(
                    preview_cell.width() / 2, preview_cell.height() / 2
                )).toPoint(),
            )
            QTest.qWait(550)
            self.assertFalse(task_preview.property("opened"))
            QTest.mouseMove(window, QPointF(890, 230).toPoint())
            # Multi-selection expands only the selected workflows together.
            model.replace_nodes([
                WorkspaceNode(
                    node_id=node_id, node_type="sobject",
                    search_key="demo/asset?code=" + node_id,
                    code=node_id, title=node_id,
                )
                for node_id in ("asset", "asset2", "asset3")
            ])
            controller._selected = ["asset", "asset2"]
            controller.selected_node_changed.emit()
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(100)
            task_cells = {
                item.property("nodeId"): item for item in _visual_items(table)
                if item.objectName() == "tableTaskCell"
            }
            self.assertEqual(set(task_cells), {"asset", "asset2", "asset3"})
            QTest.mouseMove(window, task_cells["asset"].mapToScene(
                QPointF(10, task_cells["asset"].height() / 2)).toPoint())
            QTest.qWait(650)
            for node_id, cell in task_cells.items():
                self.assertEqual(
                    cell.findChild(QObject, "tableTaskCardsPreview").property("opened"),
                    node_id in controller._selected, node_id,
                )
            # Leaving for another cell in the same selected row closes all.
            QTest.mouseMove(window, QPointF(65, task_cells["asset"].mapToScene(
                QPointF(0, task_cells["asset"].height() / 2)).y()).toPoint())
            QTest.qWait(550)
            for cell in task_cells.values():
                self.assertFalse(cell.findChild(
                    QObject, "tableTaskCardsPreview").property("opened"))
            model.set_organization(group_mode="column:code")
            model.show_table_rows()
            QMetaObject.invokeMethod(rows, "positionViewAtBeginning")
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(80)
            group_title = next((
                item for item in _visual_items(table)
                if item.objectName() == "searchResultTableGroupTitle"
            ), None)
            self.assertIsNotNone(
                group_title,
                [item.objectName() for item in _visual_items(table)
                 if item.objectName()],
            )
            self.assertIn(group_title.property("text"), {"asset", "asset2", "asset3"})
        finally:
            window.close()
            table.setParentItem(None)
            table.deleteLater()
            window.deleteLater()

    def test_task_cell_reflows_into_overflow_and_reveals_dates(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        columns = _TableColumns()
        controller = _TableController()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
            "avatarColor", "email", "primaryGroup",
        ))
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "TacticTaskCell.qml"))
        )
        cell = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "columnsController": columns,
            "userModel": users,
            "nodeId": "asset",
            "records": columns.cell("asset", "tasks")["tasks"],
            "taskCount": 1,
            "width": 280,
            "height": 90,
        })
        self.assertIsNotNone(
            cell, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        cell.setParentItem(window.contentItem())
        window.resize(300, 120)
        window.show()
        try:
            QTest.qWait(30)
            named = {
                item.objectName(): item for item in _visual_items(cell)
                if item.objectName()
            }
            first_card = named["tableTaskRecord_0"]
            dates = named["tableTaskDates_0"]
            menu = named["tableCellTasks"]
            self.assertEqual(first_card.width(), 107)
            self.assertTrue(dates.isVisible())
            self.assertFalse(menu.isVisible())

            self.assertIsNone(cell.findChild(QObject, "tableTaskDateEditor"))

            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                dates.mapToScene(QPointF(
                    dates.width() / 2, dates.height() / 2
                )).toPoint(),
            )
            QTest.qWait(300)
            date_editor = cell.findChild(QObject, "tableTaskDateEditor")
            self.assertIsNotNone(date_editor)
            self.assertTrue(date_editor.property("opened"), warnings)
            start_editor = date_editor.findChild(
                QObject, "tableTaskStartDateEditor"
            )
            self.assertIsNotNone(start_editor)
            start_editor.setProperty("text", "2026-09-02 10:00:00")
            QMetaObject.invokeMethod(start_editor, "editingFinished")
            QTest.qWait(20)
            self.assertIn((
                "asset", "sthpw/task?code=TASK001", "model",
                "bid_start_date", "2026-09-02 10:00:00",
            ), columns.task_edits)
            QMetaObject.invokeMethod(date_editor, "close")
            QTest.qWait(300)
            self.assertIsNone(cell.findChild(QObject, "tableTaskDateEditor"))

            cell.setProperty("width", 150)
            QTest.qWait(20)
            named = {
                item.objectName(): item for item in _visual_items(cell)
                if item.objectName()
            }
            first_card = named["tableTaskRecord_0"]
            menu = named["tableCellTasks"]
            self.assertTrue(menu.isVisible())
            self.assertEqual(menu.property("iconName"), "tasks")
            self.assertEqual(menu.property("count"), 1)
            self.assertLessEqual(
                first_card.x() + first_card.width(), menu.x()
            )
            self.assertAlmostEqual(
                menu.x() + menu.width() / 2,
                (
                    first_card.x() + first_card.width() + cell.width()
                ) / 2,
                delta=1,
            )
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                menu.mapToScene(QPointF(
                    menu.width() / 2, menu.height() / 2
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(
                controller.process_details[-1], ("asset", "tasks", "")
            )
            preview = cell.findChild(QObject, "tableTaskCardsPreview")
            self.assertIsNotNone(preview)
            self.assertFalse(preview.property("opened"))
            QTest.qWait(20)
            QTest.mouseMove(window, QPointF(290, 110).toPoint())
            QTest.qWait(20)

            QTest.mouseMove(
                window,
                cell.mapToScene(QPointF(10, cell.height() / 2)).toPoint(),
            )
            QTest.qWait(550)
            self.assertTrue(
                preview.property("opened"),
                (cell.property("hoverActive"), warnings),
            )
            preview_surface = preview.property("contentItem").property("item")
            popup_cards = [
                item.objectName() for item in _visual_items(preview_surface)
                if item.objectName().startswith("tableTaskRecord_")
            ]
            self.assertEqual(
                popup_cards, ["tableTaskRecord_1", "tableTaskRecord_0"]
            )
            inline_cards = cell.findChild(QQuickItem, "tableInlineTaskCards")
            self.assertEqual(inline_cards.opacity(), 0)
            expanded_card = next(item for item in _visual_items(preview_surface)
                                 if item.objectName() == "tableTaskRecord_0")
            self.assertLess(
                expanded_card.mapToScene(QPointF()).y(),
                cell.mapToScene(QPointF(0, cell.height())).y(),
            )
            QTest.mouseMove(window, QPointF(290, 110).toPoint())
            QTest.qWait(400)
            self.assertFalse(preview.property("opened"))
            self.assertEqual(inline_cards.opacity(), 1)

            cell.setProperty("width", 100)
            QTest.qWait(20)
            self.assertEqual(cell.property("visibleCardCount"), 0)
            self.assertAlmostEqual(
                menu.x() + menu.width() / 2, cell.width() / 2, delta=1
            )

            # A recycled row updates the existing cards instead of rebuilding
            # every editor/avatar. An open editor must not follow another task.
            cell.setProperty("width", 280)
            QTest.qWait(20)
            named = {item.objectName(): item for item in _visual_items(cell)
                     if item.objectName()}
            first_card = named["tableTaskRecord_0"]
            status_cell = named["tableTaskStatus_0"]
            status_cell.setProperty("editRequested", True)
            QTest.qWait(50)
            self.assertTrue(status_cell.property("editorLoaded"))
            records = columns.cell("asset", "tasks")["tasks"]
            records[0].update(taskCode="TASK002", taskSearchKey="sthpw/task?code=TASK002",
                              status="Complete", assigned="supervisor",
                              assignedLabel="Supervisor")
            cell.setProperty("records", records)
            cell.setProperty("nodeId", "asset2")
            QTest.qWait(50)
            named = {item.objectName(): item for item in _visual_items(cell)
                     if item.objectName()}
            self.assertIs(named["tableTaskRecord_0"], first_card)
            self.assertIs(named["tableTaskStatus_0"], status_cell)
            self.assertFalse(status_cell.property("editorLoaded"))
            self.assertEqual(status_cell.property("displayText"), "Complete")
            status_cell.setProperty("editRequested", True)
            QTest.qWait(50)
            editor = next(item for item in _visual_items(cell)
                          if item.objectName() == "tableTaskStatusEditor_0")
            editor.setProperty("currentIndex", 0)
            editor.activated.emit(0)
            self.assertEqual(columns.task_edits[-1], (
                "asset2", "sthpw/task?code=TASK002", "model", "status", "Pending",
            ))
            QMetaObject.invokeMethod(status_cell, "resetEditor")
            QTest.qWait(20)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            cell.setParentItem(None)
            cell.deleteLater()
            window.deleteLater()

    def test_table_columns_hide_by_priority_and_auto_fit_remaining_width(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id="asset", node_type="sobject", search_key="asset",
            code="ASSET001", title="Tree",
        )])
        columns = _TableColumns()
        columns._columns = [
            {
                "row": 0, "name": "code", "label": "Code",
                "width": 160, "dataType": "varchar", "sortable": True,
                "hideOrder": 0,
            },
            {
                "row": 1, "name": "notes", "label": "Notes",
                "width": 160, "dataType": "varchar", "sortable": True,
                "hideOrder": 2,
            },
            {
                "row": 2, "name": "category", "label": "Category",
                "width": 160, "dataType": "varchar", "sortable": True,
                "hideOrder": 1,
            },
        ]
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml"))
        )
        table = component.createWithInitialProperties({
            "theme": theme,
            "controller": _TableController(),
            "columnsController": columns,
            "resultModel": model,
            "width": 430,
            "height": 180,
        })
        self.assertIsNotNone(
            table, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        table.setParentItem(window.contentItem())
        window.resize(430, 180)
        window.show()
        try:
            rows = table.findChild(QQuickItem, "searchResultsTableView")
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(40)
            named = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertIn("tableColumnContextArea_code", named)
            self.assertNotIn("tableColumnContextArea_category", named)
            table.setWidth(650)
            window.resize(650, 180)
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(40)
            named = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertIn("tableColumnContextArea_category", named)
            label = named["tableColumnHeaderLabel_code"]
            self.assertEqual(label.property("text"), "CODE")
            button = named["autoFitTableColumnsButton"]
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                button.mapToScene(QPointF(
                    button.width() / 2, button.height() / 2
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertTrue(table.property("autoFitColumns"))
            self.assertGreater(
                named["tableColumnContextArea_code"].parentItem().width(),
                160,
            )
        finally:
            window.close()
            table.setParentItem(None)
            table.deleteLater()
            window.deleteLater()

    def test_table_header_sorts_and_groups_by_column(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id="asset", node_type="sobject", search_key="asset",
            code="ASSET001", title="Tree",
        )])
        controller = _TableController()
        columns = _TableColumns()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml"))
        )
        table = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "columnsController": columns,
            "resultModel": model,
            "width": 900,
            "height": 180,
        })
        self.assertIsNotNone(
            table, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        table.setParentItem(window.contentItem())
        window.resize(900, 180)
        window.show()
        try:
            QTest.qWait(40)
            area = next(
                item for item in _visual_items(table)
                if item.objectName() == "tableColumnContextArea_code"
            )
            QTest.mouseClick(
                window, Qt.RightButton, Qt.NoModifier,
                area.mapToScene(QPointF(
                    area.width() / 2, area.height() / 2
                )).toPoint(),
            )
            QTest.qWait(200)
            menu = table.findChild(QObject, "tableColumnContextMenu")
            actions = menu.property("actions").toVariant()
            commands = {
                action.get("command") for action in actions
                if isinstance(action, dict) and action.get("command")
            }
            self.assertTrue({
                "sort:ascending", "sort:descending", "group", "ungroup",
            }.issubset(commands))
            self.assertIn(
                "Sort A to Z",
                [action.get("title") for action in actions
                 if isinstance(action, dict)],
            )
            controller.set_result_group_mode("column:code")
            QTest.qWait(20)
            group_indicator = next(
                item for item in _visual_items(table)
                if item.objectName() == "tableColumnGroupIndicator_code"
            )
            self.assertTrue(group_indicator.isVisible())
            menu.triggered.emit("sort:descending")
            menu.triggered.emit("group")
            menu.triggered.emit("ungroup")
            menu.triggered.emit("edit_definition")
            self.assertEqual(columns.sort_calls[-1], (0, True))
            self.assertEqual(columns.group_calls[-1], 0)
            self.assertEqual(controller.group_modes[-1], "none")
            self.assertEqual(columns.focus_requests[-1], (0, "definition"))
        finally:
            window.close()
            table.setParentItem(None)
            table.deleteLater()
            window.deleteLater()

    def test_table_view_preset_menu_selects_current_tab_view(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        columns = _TableColumns()
        columns._table_views.append({
            "view": "th_table_review", "title": "Review",
            "current": False,
        })
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml"))
        )
        controller = _TableController()
        result_model = WorkspaceItemModel()
        table = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "columnsController": columns,
            "resultModel": result_model,
            "width": 720,
            "height": 180,
        })
        self.assertIsNotNone(
            table, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        table.setParentItem(window.contentItem())
        window.resize(720, 180)
        window.show()
        try:
            QTest.qWait(30)
            button = table.findChild(
                QQuickItem, "configureTableColumnsButton"
            )
            button.clicked.emit()
            QTest.qWait(20)
            menu = table.findChild(QObject, "tableViewPresetsMenu") \
                or window.findChild(QObject, "tableViewPresetsMenu")
            self.assertIsNotNone(menu, warnings)
            actions = menu.property("actions").toVariant()
            commands = [
                action.get("command") for action in actions
                if isinstance(action, dict) and action.get("command")
            ]
            self.assertIn("select:1", commands)
            self.assertIn("save_as", commands)
            menu.triggered.emit("select:1")
            QTest.qWait(20)
            self.assertEqual(columns.selected_table_views, [1])
            button.clicked.emit()
            QTest.qWait(20)
            menu = table.findChild(QObject, "tableViewPresetsMenu") \
                or window.findChild(QObject, "tableViewPresetsMenu")
            menu.triggered.emit("configure")
            self.assertEqual(columns.focus_requests, [(-1, "definition")])
            self.assertEqual(controller.columns_editor_requests, 1)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            table.setParentItem(None)
            table.deleteLater()
            window.deleteLater()

    def test_result_table_instantiates_real_qml_with_both_scrollbars(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id="asset", node_type="sobject",
            search_key="demo/asset?code=ASSET001", code="ASSET001",
            title="Tree", values={"code": "ASSET001", "name": "Oak"},
            comments=3,
            tasks=1,
            preview_source=object(),
        )])
        columns = _TableColumns()
        table_controller = _TableController()
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
            "avatarColor", "email", "primaryGroup",
        ))
        users.replace([{
            "login": "artist", "displayName": "Artist",
            "initials": "AR", "avatarUrl": "", "avatarColor": "",
            "email": "", "primaryGroup": "Artists",
        }])
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultTable.qml"))
        )
        table = component.createWithInitialProperties({
            "theme": theme,
            "controller": table_controller,
            "columnsController": columns,
            "resultModel": model,
            "userModel": users,
            "presentationActive": True,
            "width": 300,
            "height": 160,
        })
        self.assertIsNotNone(
            table, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        table.setParentItem(window.contentItem())
        window.resize(300, 160)
        window.show()
        try:
            screenshot_dir = os.environ.get("TABLE_VIEW_SCREENSHOT_DIR")
            QTest.qWait(50)
            rows = table.findChild(QQuickItem, "searchResultsTableView")
            self.assertIsNotNone(rows)
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(50)
            self.assertEqual(rows.property("count"), 1)
            self.assertGreater(rows.property("contentWidth"), rows.width())
            vertical = table.findChild(QQuickItem, "tableVerticalScrollBar")
            horizontal = table.findChild(QQuickItem, "tableHorizontalScrollBar")
            for width in (300, 1100):
                table.setWidth(width)
                window.resize(width, 160)
                QTest.qWait(20)
                self.assertGreaterEqual(
                    vertical.mapToScene(QPointF()).x(),
                    rows.mapToScene(QPointF(rows.width(), 0)).x() + 4,
                )
                self.assertGreaterEqual(
                    horizontal.mapToScene(QPointF()).y(),
                    rows.mapToScene(QPointF(0, rows.height())).y() + 4,
                )
                button = table.findChild(QQuickItem, "configureTableColumnsButton")
                self.assertTrue(button.isVisible())
                self.assertTrue(button.isEnabled())
                center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
                self.assertLess(center.x() + button.width() / 2, vertical.mapToScene(QPointF()).x())
                button.clicked.emit()
                QTest.qWait(20)
                menu = table.findChild(QObject, "tableViewPresetsMenu") \
                    or window.findChild(QObject, "tableViewPresetsMenu")
                self.assertIsNotNone(menu, warnings)
                menu.triggered.emit("configure")
                QTest.qWait(20)
                self.assertEqual(
                    table_controller.columns_editor_requests,
                    1 if width == 300 else 2,
                )
            table.setWidth(300)
            window.resize(300, 160)
            QMetaObject.invokeMethod(rows, "forceLayout")
            QTest.qWait(40)
            table_controller.opened_windows.clear()
            self.assertEqual(warnings, [])
            self.assertIsNotNone(
                table.findChild(QObject, "tableVerticalScrollBar")
            )
            self.assertIsNotNone(
                table.findChild(QObject, "tableHorizontalScrollBar")
            )
            texts = set()
            named_items = {}
            for item in _visual_items(table):
                if item.property("text") is not None:
                    texts.add(str(item.property("text")))
                if item.objectName():
                    named_items.setdefault(item.objectName(), item)
            self.assertLessEqual(len(_visual_items(table)), 250)
            self.assertIn("ASSET NAME", texts)
            self.assertIn("ASSET001", texts)
            self.assertIsNotNone(
                named_items.get("searchResultTableHeader")
            )
            self.assertIsNotNone(
                named_items.get("configureTableColumnsButton")
            )
            self.assertIsNotNone(
                named_items.get("tableColumnResize_code")
            )
            self.assertIsNotNone(
                named_items.get("tableColumnContextArea_code")
            )
            self.assertIsNotNone(
                named_items.get("searchResultTableActions")
            )
            self.assertIsNotNone(named_items.get("tableSelectionAll"))
            self.assertIsNotNone(named_items.get("tableSelection_asset"))
            self.assertIsNotNone(named_items.get("tableCellPreview"))
            self.assertIsNone(named_items.get("tableCellNotes"))
            self.assertIn("asset", table_controller.preview_requests)
            rows.setProperty("contentX", 250)
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            edit_area = named_items["tableCellEditArea_name"]
            QTest.mouseDClick(
                window, Qt.LeftButton, Qt.NoModifier,
                edit_area.mapToScene(QPointF(
                    edit_area.width() / 2, edit_area.height() / 2
                )).toPoint(),
            )
            QTest.qWait(30)
            self.assertEqual(
                columns.editor_requests[-1:], [("asset", "name")]
            )
            inline_loader = named_items["tableCellEditor_name"]
            self.assertTrue(
                inline_loader.property("active"),
                (inline_loader.property("item"), warnings),
            )
            value_editor = inline_loader.property("item")
            self.assertIsNotNone(value_editor, warnings)
            inline_text = next((item for item in _visual_items(value_editor)
                if item.objectName() == "tableInlineValue"), None)
            self.assertIsNotNone(inline_text, warnings)
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            text_input = QInputMethodEvent()
            text_input.setCommitString("Pine")
            QGuiApplication.sendEvent(inline_text, text_input)
            QTest.keyClick(window, Qt.Key_Return)
            QTest.qWait(30)
            self.assertEqual(
                table_controller.field_updates[-1],
                ("asset", {"name": "Pine"}),
            )
            self.assertEqual(table_controller.double_clicks, [])
            menu_requests = []
            process_menu_requests = []
            table.actionMenuRequested.connect(
                lambda *args: menu_requests.append(args)
            )
            table.processCountMenuRequested.connect(
                lambda *args: process_menu_requests.append(args)
            )
            rows.setProperty("contentX", 480)
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            for object_name, kind in (
                ("tableCellSObjectDetail", "sobject_detail"),
                ("tableCellCheckin", "checkin"),
            ):
                button = named_items[object_name]
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    button.mapToScene(QPointF(
                        button.width() / 2, button.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                self.assertEqual(
                    table_controller.table_widget_actions[-1][:2],
                    (kind, "asset"),
                )
            rows.setProperty("contentX", 700)
            table.setProperty("rowHeight", 104)
            QMetaObject.invokeMethod(rows, "forceLayout")
            frame(window)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            if screenshot_dir:
                window.grabWindow().save(str(
                    Path(screenshot_dir) / "search-table-tasks.png"
                ))
            task_card = named_items["tableTaskRecord_0"]
            self.assertLessEqual(task_card.width(), 107)
            self.assertLessEqual(task_card.height(), 88)
            task_dates = named_items["tableTaskDates_0"]
            self.assertTrue(task_dates.isVisible())
            self.assertIn("1 Sep – 3 Sep", {
                str(item.property("text")) for item in _visual_items(task_dates)
                if item.property("text") is not None
            })
            task_header = named_items["tableTaskHeader_0"]
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                task_header.mapToScene(QPointF(
                    task_header.width() / 2, task_header.height() / 2
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(
                table_controller.task_details[-1],
                ("asset", "tasks", "model", "TASK001"),
            )
            status_cell = named_items["tableTaskStatus_0"]
            status_label = next((item for item in _visual_items(status_cell)
                                 if item.objectName() == "taskTableCellDisplayLabel"), None)
            self.assertIsNotNone(status_label, warnings)
            self.assertEqual(status_label.property("font").pixelSize(), 11)
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                status_cell.mapToScene(QPointF(
                    status_cell.width() / 2, status_cell.height() / 2
                )).toPoint(),
            )
            status_cell.setProperty("editRequested", True)
            QTest.qWait(50)
            status_editor = next((
                item for item in _visual_items(table)
                if item.objectName() == "tableTaskStatusEditor_0"
            ), None)
            self.assertIsNotNone(status_editor, warnings)
            self.assertLessEqual(
                status_editor.property("font").pointSizeF(), 8.25
            )
            status_editor.setProperty("currentIndex", 2)
            status_editor.activated.emit(2)
            QTest.qWait(20)
            self.assertEqual(
                columns.task_edits[-1],
                (
                    "asset", "sthpw/task?code=TASK001", "model",
                    "status", "Complete",
                ),
            )
            assignee_cell = next(item for item in _visual_items(table)
                                 if item.objectName() == "tableTaskAssignee_0")
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                             assignee_cell.mapToScene(QPointF(assignee_cell.width()/2, assignee_cell.height()/2)).toPoint())
            assignee_cell.setProperty("editRequested", True)
            QTest.qWait(50)
            assignee_editor = next((
                item for item in _visual_items(table)
                if item.objectName() == "tableTaskAssigneeEditor_0"
            ), None)
            self.assertIsNotNone(assignee_editor, warnings)
            assignee_editor.setProperty("currentIndex", 2)
            assignee_editor.activated.emit(2)
            QTest.qWait(20)
            self.assertEqual(
                columns.task_edits[-1],
                (
                    "asset", "sthpw/task?code=TASK001", "model",
                    "assigned", "supervisor",
                ),
            )
            table.setProperty("rowHeight", 68)
            QMetaObject.invokeMethod(rows, "forceLayout")
            rows.setProperty("contentX", 430)
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            if screenshot_dir:
                window.grabWindow().save(str(
                    Path(screenshot_dir) / "search-table-notes.png"
                ))
            note_texts = {
                str(item.property("text")) for item in _visual_items(table)
                if item.property("text") is not None
            }
            self.assertIn("Localized publish", note_texts)
            self.assertIn("Localized publish context", note_texts)
            self.assertNotIn("Notes (2)", note_texts)
            self.assertGreater(
                named_items["tableNoteList"].property("contentHeight"),
                named_items["tableNoteList"].height(),
            )
            notes_record = named_items["tableNoteRecord_0"]
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                notes_record.mapToScene(QPointF(
                    notes_record.width() / 2, notes_record.height() / 2
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(
                table_controller.process_details[-1],
                ("asset", "notes", "rig"),
            )
            rows.setProperty("contentX", 880)
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            self.assertIsNotNone(named_items.get("tableCellCompletion"))
            self.assertGreater(
                named_items["tableCellCompletionFill"].width(), 0
            )
            rows.setProperty(
                "contentX", rows.property("contentWidth") - rows.width()
            )
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            for kind in ("explorer", "file_list", "metadata", "delete"):
                column_name = 'files' if kind == 'file_list' else kind
                header = next(item for item in _visual_items(table)
                              if item.objectName() == 'tableColumnHeaderLabel_' + column_name)
                relative = header.mapToItem(rows, QPointF(header.width()/2, 0)).x()
                rows.setProperty("contentX", max(0, min(rows.property("contentWidth")-rows.width(), rows.property("contentX")+relative-rows.width()/2)))
                QTest.qWait(20)
                button = next(item for item in _visual_items(table)
                              if item.objectName() == 'tableCellAction_' + kind)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    button.mapToScene(QPointF(
                        button.width() / 2, button.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                self.assertEqual(
                    table_controller.table_widget_actions[-1][:2],
                    (kind, "asset"),
                )
            rows.setProperty("contentX", 0)
            QTest.qWait(20)
            row = named_items["searchResultTableRow"]
            row_selection = named_items["tableSelection_asset"]
            table_controller.clear_result_selection()
            QTest.qWait(20)
            point = row.mapToScene(QPointF(100, row.height() / 2)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
            QTest.qWait(20)
            self.assertFalse(row.property("selected"))
            QTest.mouseClick(window, Qt.LeftButton, Qt.ShiftModifier, point)
            QTest.qWait(20)
            self.assertTrue(row.property("selected"))
            clear = table.findChild(QQuickItem, "clearTableSelection")
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                             clear.mapToScene(QPointF(clear.width() / 2, clear.height() / 2)).toPoint())
            QTest.qWait(20)
            self.assertFalse(row.property("selected"))
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                row_selection.mapToScene(QPointF(
                    row_selection.width() / 2,
                    row_selection.height() / 2,
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertTrue(row_selection.property("checked"))
            select_all = named_items["tableSelectionAll"]
            self.assertTrue(select_all.property("checked"))
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                select_all.mapToScene(QPointF(
                    select_all.width() / 2,
                    select_all.height() / 2,
                )).toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(table_controller.clear_selection_calls, 3)
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                select_all.mapToScene(QPointF(
                    select_all.width() / 2,
                    select_all.height() / 2,
                )).toPoint(),
            )
            QTest.qWait(40)
            self.assertEqual(table_controller.select_all_calls, 1)
            self.assertTrue(row.property("selected"))
            row_point = row.mapToScene(QPointF(40, row.height() / 2))
            QTest.mouseClick(
                window, Qt.RightButton, Qt.NoModifier, row_point.toPoint()
            )
            QTest.qWait(20)
            self.assertEqual(table_controller.selections[-1][0], "asset")
            self.assertEqual(menu_requests[-1][0], "asset")
            self.assertTrue(row.property("selected"))

            header_area = named_items["tableColumnContextArea_code"]
            QTest.mouseClick(
                window, Qt.RightButton, Qt.NoModifier,
                header_area.mapToScene(QPointF(
                    header_area.width() / 2, header_area.height() / 2
                )).toPoint(),
            )
            QTest.qWait(250)
            context_column = named_items[
                "searchResultTableHeader"
            ].property("columnContext")
            self.assertEqual(context_column.get("name"), "code")
            column_menu = table.findChild(
                QObject, "tableColumnContextMenu"
            )
            self.assertIsNotNone(column_menu)
            self.assertTrue(column_menu.property("opened"))
            column_actions = column_menu.property("actions").toVariant()
            self.assertTrue({
                "sort:ascending", "sort:descending", "edit_definition",
                "columns", "remove", "row_height:52",
                "row_height:68", "row_height:84", "row_height:0",
            }.issubset({
                action.get("command") for action in column_actions
                if isinstance(action, dict) and action.get("command")
            }))
            self.assertEqual(table_controller.opened_windows, [])
            column_menu.triggered.emit("sort:ascending")
            self.assertEqual(columns.sort_calls[-1], (0, False))
            column_menu.triggered.emit("row_height:84")
            self.assertEqual(row.height(), 84)
            column_menu.triggered.emit("edit_definition")
            self.assertEqual(
                columns.focus_requests[-1], (0, "definition")
            )
            self.assertEqual(table_controller.columns_editor_requests, 3)
            column_menu.close()
            QTest.qWait(250)

            table.setWidth(500)
            window.resize(500, 160)
            QTest.qWait(30)
            code_header = named_items["tableColumnContextArea_code"]
            name_header = named_items["tableColumnContextArea_name"]
            drag_start = code_header.mapToScene(QPointF(
                code_header.width() / 2, code_header.height() / 2
            ))
            drag_end = name_header.mapToScene(QPointF(
                name_header.width() / 2, name_header.height() / 2
            ))
            QTest.mousePress(
                window, Qt.LeftButton, Qt.NoModifier, drag_start.toPoint()
            )
            QTest.mouseMove(window, drag_end.toPoint(), 20)
            QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier, drag_end.toPoint()
            )
            QTest.qWait(20)
            self.assertTrue(columns.move_calls)
            self.assertEqual(columns.move_calls[-1], (0, 1))
            self.assertEqual(columns.apply_calls, 1)

            configure = named_items["configureTableColumnsButton"]
            configure_left = configure.mapToScene(QPointF()).x()
            viewport_left = rows.mapToScene(QPointF()).x()
            self.assertGreaterEqual(configure_left, viewport_left)
            self.assertLessEqual(
                configure_left + configure.width(),
                viewport_left + rows.width(),
            )
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier,
                configure.mapToScene(QPointF(
                    configure.width() / 2, configure.height() / 2
                )).toPoint(),
            )
            menu = table.findChild(QObject, "tableViewPresetsMenu") or window.findChild(QObject, "tableViewPresetsMenu")
            menu.triggered.emit("configure")
            self.assertEqual(table_controller.columns_editor_requests, 4)
            menu.close()
            QTest.qWait(20)
            rows.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Return)
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            self.assertEqual(table_controller.double_clicks[-1][0], "asset")
            self.assertEqual(table_controller.select_all_calls, 2)

            resize = named_items["tableColumnResize_code"]
            resize_start = resize.mapToScene(
                QPointF(resize.width() / 2, resize.height() / 2)
            )
            resize_end = resize_start + QPointF(32, 0)
            QTest.mousePress(
                window, Qt.LeftButton, Qt.NoModifier,
                resize_start.toPoint(),
            )
            QTest.mouseMove(window, resize_end.toPoint(), 20)
            QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier,
                resize_end.toPoint(),
            )
            QTest.qWait(20)
            self.assertEqual(columns.width_changes[-1], (0, 212))
            self.assertEqual(columns.apply_calls, 2)
            if screenshot_dir:
                window.grabWindow().save(str(
                    Path(screenshot_dir) / "search-table-narrow.png"
                ))
                table.setWidth(900)
                table.setHeight(420)
                window.resize(900, 420)
                QTest.qWait(40)
                window.grabWindow().save(str(
                    Path(screenshot_dir) / "search-table-wide.png"
                ))
            columns._columns = []
            columns._busy = True
            columns.stateChanged.emit()
            QTest.qWait(20)
            self.assertTrue(named_items["tableColumnsLoading"].isVisible())
            columns._busy = False
            columns._error = "TACTIC table failed"
            columns.stateChanged.emit()
            QTest.qWait(20)
            self.assertTrue(named_items["tableColumnsEmptyState"].isVisible())
            self.assertGreaterEqual(columns.sessions, 1)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            table.setParentItem(None)
            table.deleteLater()
            window.deleteLater()

    def test_unsupported_definition_message_is_centered_in_editor(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/columns/columns.ui.mjs" as UI
import "tactic_frame/features/administration/columns/columns.state.mjs" as State
Item {
    id: root
    required property var theme
    Frame.FrameView {
        anchors.fill: parent; theme: root.theme
        scene: UI.describe({ready:true,canWrite:false,records:[],typeOptions:[],selected:{identity:"fixture",view:"archive_assets"},wizard:{supported:false},elements:[],element:{},widgetOptions:[],xml:"<config/>"},Object.assign(State.initial(),{editing:true}),width,height,"en")
        models: ({definitions:[],columns:[]})
    }
}
''', QUrl.fromLocalFile(str(QML / "_FrameColumnsEmptyTest.qml")))
        editor = component.createWithInitialProperties({"theme":theme})
        self.assertIsNotNone(
            editor, [error.toString() for error in component.errors()]
        )
        window = QQuickWindow()
        editor.setParentItem(window.contentItem())
        window.show()
        try:
            for width in (520, 1100):
                window.resize(width, 700)
                editor.setWidth(width)
                editor.setHeight(700)
                QTest.qWait(30)
                empty = next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogWizardEmpty"),None)
                self.assertIsNotNone(empty)
                panel = next(item for item in _visual_items(editor) if item.objectName() == "definitionEditorPanel")
                center = empty.mapToItem(
                    panel, QPointF(empty.width() / 2, empty.height() / 2)
                )
                self.assertAlmostEqual(
                    center.x(), panel.width() / 2, delta=1,
                    msg=(
                        f"editor={editor.width()} empty={empty.width()} "
                        f"parent={empty.parentItem().width()} "
                        f"root={empty.parentItem().parentItem().width()}"
                    ),
                )
        finally:
            window.close()
            editor.setParentItem(None)
            editor.deleteLater()
            window.deleteLater()
            engine.deleteLater()

    def test_catalog_reorder_preserves_custom_xml_and_rejects_out_of_bounds_moves(self):
        controller = ColumnsEditorController(_Application(_SType()))
        source = ('<config custom="kept"><!--keep--><table custom="view">'
                  '<element name="code" custom="field"><display widget="text"><option>keep</option></display></element>'
                  '<!--between--><extension value="kept"/><element name="name"/>'
                  '</table><other value="kept"/></config>')
        rows = controller.catalog_wizard(source)['elements']
        moved = controller.update_catalog_wizard(source, rows[0]['path'], 'move', '1')
        self.assertEqual([row['name'] for row in controller.catalog_wizard(moved)['elements']], ['name', 'code'])
        for fragment in ('<!--keep-->', '<!--between-->', 'custom="kept"', 'custom="field"',
                         '<option>keep</option>', '<extension value="kept"/>', '<other value="kept"/>'):
            self.assertIn(fragment, moved)
        code = controller.catalog_wizard(moved)['elements'][1]
        restored = controller.update_catalog_wizard(moved, code['path'], 'move', '-1')
        self.assertEqual([row['name'] for row in controller.catalog_wizard(restored)['elements']], ['code', 'name'])
        first = controller.catalog_wizard(restored)['elements'][0]
        for offset in ('-1', '0', '2', 'wrong'):
            self.assertEqual(controller.update_catalog_wizard(restored, first['path'], 'move', offset), '')
        self.assertIn('custom="field"', restored)

    def test_column_focus_finds_display_definition_and_custom_view(self):
        application = _Application(_SType())
        controller = ColumnsEditorController(application)
        records = [
            dict(code="TABLE", search_type="demo/asset", view="table",
                 config='<config><table><element name="submit"/></table></config>'),
            dict(code="DISPLAY", search_type="demo/asset", view="definition",
                 config='<config><definition><element name="submit"><display class="SubmissionLinkTableElement"/></element></definition></config>'),
            dict(code="INPUT", search_type="demo/asset", view="edit_definition",
                 config='<config><edit_definition><element name="name"/></edit_definition></config>'),
            dict(code="CUSTOM", search_type="demo/asset", view="asset_list",
                 config='<config><asset_list><element name="submit"><display class="custom.SubmitWdg"/></element></asset_list></config>'),
        ]
        controller._set_definition_catalog('demo', application.stype.project, records, {})
        controller.load_definition_catalog = lambda *_: None
        controller._stype_code = 'demo/asset'
        controller._view = 'table'
        controller.model.replace([{'name': 'submit'}, {'name': 'missing'}])
        controller.request_column_focus(0, 'definition')
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        engine.rootContext().setContextProperty('columnsEditorController', controller)
        theme = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml'))).createWithInitialProperties({'dark': True})
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'features/administration/columns/ColumnsEditorView.qml')))
        editor = component.createWithInitialProperties(dict(theme=theme, projectCode='demo', width=1100, height=700))
        self.assertIsNotNone(editor, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        editor.setParentItem(window.contentItem())
        window.resize(1100, 700)
        window.show()
        try:
            QTest.qWait(60)
            self.assertEqual(editor.property('selectedCatalog')['code'], 'DISPLAY')
            self.assertEqual(editor.property('element')['name'], 'submit')
            identifier = next(item for item in _visual_items(editor) if item.objectName() == 'definitionWidgetIdentifier')
            self.assertEqual(identifier.property('text'), 'SubmissionLinkTableElement')
            controller._view = 'asset_list'
            controller.request_column_focus(0, 'definition')
            QTest.qWait(20)
            self.assertEqual(editor.property('selectedCatalog')['code'], 'CUSTOM')
            self.assertEqual(editor.property('element')['widget'], 'custom.SubmitWdg')
            controller.request_column_focus(1, 'definition')
            QTest.qWait(20)
            self.assertFalse(editor.property('selectedCatalogIdentity'))
            self.assertIn('not found', editor.property('focusError'))
            self.assertFalse(controller.focusPending)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            editor.setParentItem(None)
            editor.deleteLater()
            window.deleteLater()
            controller.shutdown()
            engine.deleteLater()

    def test_administration_columns_editor_uses_project_catalog_only(self):
        application = _Application(_SType())
        application.stype.project.views.config_dict.append({
            "code": "WIDGET003", "view": "table", "login": "artist",
            "search_type": "demo/shot", "config": (
                '<config><table><element name="code" title="Code"/>'
                '<element name="name" title="Name"/></table></config>'
            ),
        })
        application.stype.project.views.config_dict.append({
            "code": "WIDGET004", "view": "table", "login": "",
            "search_type": "demo/shot", "config": "<config><table/></config>",
        })
        updates = []
        server = SimpleNamespace(
            query=lambda search_type, *_args, **_kwargs: (
                [
                    {"code": "demo/asset", "title": "Assets"},
                    {"code": "demo/shot", "title": "Shots"},
                ] if search_type == "sthpw/search_object" else list(
                    application.stype.project.views.config_dict
                )
            ),
            build_search_key=lambda _stype, code, **_kwargs:
                f"config/widget_config?code={code}",
            insert_update=lambda key, data, **kwargs:
                updates.append((key, data, kwargs)),
        )
        from thlib.environment import env_inst
        with (
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch.object(env_inst, "server_pool", _Pool()),
            patch.object(
                env_inst, "get_project_by_code",
                return_value=application.stype.project,
            ),
        ):
            controller = ColumnsEditorController(application)
            controller._stype_code = "demo/shot"
            controller._view = "table"
            controller._database_views = {"table": {"code": "WIDGET003"}}
            controller.model.replace([
                {"name": "code"}, {"name": "name"},
            ])
            controller.request_column_focus(1, "definition")
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(
                lambda errors: warnings.extend(
                    error.toString() for error in errors
                )
            )
            engine.rootContext().setContextProperty(
                "columnsEditorController", controller
            )
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "features/administration/columns/ColumnsEditorView.qml"))
            )
            editor = component.createWithInitialProperties({
                "theme": theme, "projectCode": "demo",
                "width": 1100, "height": 700,
            })
            self.assertIsNotNone(
                editor, [error.toString() for error in component.errors()]
            )
            window = QQuickWindow()
            editor.setParentItem(window.contentItem())
            window.resize(1100, 700)
            window.show()
            try:
                QTest.qWait(60)
                catalog = next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogList"), None)
                self.assertIsNotNone(catalog, warnings)
                self.assertEqual(catalog.property("count"), 2)
                self.assertEqual(editor.property("ui").toVariant()["searchType"], "demo/shot")
                self.assertEqual(editor.property("selectedCatalog")["code"], "WIDGET003")
                self.assertFalse(controller.focusPending)
                self.assertIsNone(next((item for item in _visual_items(editor) if item.objectName() == "tableViewSelectorPanel"), None))
                self.assertFalse(any(
                    item.objectName() in (
                        "segmentedButtonSegment_current",
                        "segmentedButtonSegment_catalog",
                        "segmentedButtonSegment_all",
                    )
                    for item in _visual_items(editor)
                ))
                search_type_filter = next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogSearchTypeFilter"), None)
                self.assertIsNotNone(search_type_filter)
                self.assertTrue(search_type_filter.isVisible())
                self.assertEqual(search_type_filter.property("count"), 3)
                self.assertEqual(
                    search_type_filter.property("currentText"),
                    "Shots · demo/shot",
                )
                self.assertEqual(
                    search_type_filter.property("currentValue"), "demo/shot"
                )
                self.assertEqual(
                    [row["label"] for row in
                     controller.definitionCatalogSearchTypes],
                    ["Assets · demo/asset", "Shots · demo/shot"],
                )
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    search_type_filter.mapToScene(QPointF(
                        search_type_filter.width() / 2,
                        search_type_filter.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(30)
                popup = search_type_filter.findChild(QObject, "comboBoxPopup")
                self.assertIsNotNone(popup)
                self.assertTrue(popup.property("visible"))
                popup.close()
                search_type_filter.setProperty("currentIndex", 2)
                search_type_filter.activated.emit(2)
                QTest.qWait(20)
                self.assertEqual(catalog.property("count"), 2)
                self.assertEqual(
                    editor.property("selectedCatalog")["searchType"],
                    "demo/shot",
                )
                search_type_filter.setProperty("currentIndex", 0)
                search_type_filter.activated.emit(0)
                QTest.qWait(20)
                controller.request_column_focus(1, "definition")
                QTest.qWait(20)
                self.assertEqual(editor.property("ui").toVariant()["searchType"], "demo/shot")
                self.assertEqual(editor.property("selectedCatalog")["code"], "WIDGET003")
                self.assertEqual(editor.property("ui").toVariant()["path"], "0/1")
                self.assertFalse(controller.focusPending)
                output = os.environ.get("COLUMNS_SCREENSHOTS")
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    window.grabWindow().save(str(Path(output) / "columns_wide.png"))
                controller._stype_code = ""
                xml_mode = next(
                    item for item in _visual_items(editor)
                    if item.objectName() == "definitionCatalogMode_xml"
                )
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    xml_mode.mapToScene(QPointF(
                        xml_mode.width() / 2, xml_mode.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                xml_editor = next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogXml"), None)
                self.assertIsNotNone(xml_editor)
                window.requestActivate()
                QTest.qWait(20)
                xml_editor.focusEditor()
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                for character in '<config><table marker="advanced"/></config>':
                    QTest.keyClick(window, character)
                QTest.qWait(20)
                save = next((item for item in _visual_items(editor) if item.objectName() == "adminSaveDocument"), None)
                self.assertTrue(save.isEnabled())
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    save.mapToScene(QPointF(
                        save.width() / 2, save.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(30)
                confirm = next(item for item in _visual_items(editor) if item.objectName() == "adminConfirmSave")
                QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, confirm.mapToScene(QPointF(confirm.width()/2,confirm.height()/2)).toPoint())
                QTest.qWait(30)
                self.assertEqual(len(updates), 1)
                self.assertEqual(
                    updates[0][1]["config"],
                    '<config><table marker="advanced"/></config>',
                )
                editor.setProperty("catalogXmlText", "<config/>")
                revert = next((item for item in _visual_items(editor) if item.objectName() == "adminDiscardDocument"), None)
                self.assertTrue(revert.isEnabled())
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    revert.mapToScene(QPointF(
                        revert.width() / 2, revert.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(30)
                confirm = next(item for item in _visual_items(editor) if item.objectName() == "adminConfirmSave")
                QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, confirm.mapToScene(QPointF(confirm.width()/2,confirm.height()/2)).toPoint())
                QTest.qWait(30)
                self.assertEqual(
                    editor.property("catalogXmlText"),
                    editor.property("catalogXmlOriginal"),
                )
                catalog_panel = next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogPanel"), None)
                catalog_editor = next((item for item in _visual_items(editor) if item.objectName() == "definitionEditorPanel"), None)
                self.assertGreater(catalog_editor.mapToScene(QPointF()).x(), catalog_panel.mapToScene(QPointF()).x())
                editor.setWidth(520)
                editor.setHeight(680)
                window.resize(520, 680)
                QTest.qWait(30)
                self.assertIsNone(next((item for item in _visual_items(editor) if item.objectName() == "definitionCatalogPanel"), None))
                self.assertIsNotNone(next((item for item in _visual_items(editor) if item.objectName() == "columnsBack"), None))
                if output:
                    window.grabWindow().save(str(Path(output) / "columns_narrow.png"))
                self.assertEqual(warnings, [])
            finally:
                window.close()
                editor.setParentItem(None)
                editor.deleteLater()
                window.deleteLater()
                controller.shutdown()
                engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
