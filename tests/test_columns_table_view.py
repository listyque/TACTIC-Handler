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
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
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

    def _current_tab(self):
        return SimpleNamespace(stype=self.stype, sobjects=[], view_mode="table")

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
        self.select_all_calls = 0
        self.preview_requests = []
        self.revealed_previews = []
        self.table_widget_actions = []
        self.process_details = []
        self.task_details = []
        self.clear_selection_calls = 0
        self.field_updates = []
        self._result_sort_mode = "name_asc"

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

    @Slot(str, str, str, int, bool)
    def select_result_node(self, *args):
        self.selections.append(args)
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
                "title": "Rig", "process": "rig", "badgeCount": 1,
            },
            {
                "title": "Localized publish", "process": "publish",
                "badgeCount": 2,
            },
            {
                "title": "Localized publish context",
                "process": "publish/context", "badgeCount": 3,
            },
            {
                "title": "Model", "process": "model", "badgeCount": 1,
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
        self.focus_requests = []
        self.remove_calls = []
        self.move_calls = []
        self.editor_requests = []
        self.task_edits = []
        self._dirty = False
        self._busy = False
        self._error = ""
        self._cell_revision = 0
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

    @Property("QVariantList", notify=stateChanged)
    def visibleColumns(self):
        return self._columns

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

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
                        "bidStart": "", "bidEnd": "",
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
            get_action_options=lambda _name: {}
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
        config = SimpleNamespace(get_action_options=lambda _name: {})
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
        self.assertEqual(
            elements[0].find("./display/option").text, "keep"
        )
        self.assertEqual(elements[-1].get("internal"), "keep")
        self.assertFalse(controller.dirty)

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
        controller._add_task_workflow_rows(target_key, cells)

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
        self.assertIn("created task identity", controller.error)
        self.assertFalse(rig["hasTask"])

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
                ("demo/shot", "Shots"),
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
            query=lambda *_args: list(
                application.stype.project.views.config_dict
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
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
            controller.load_definition_catalog()
            catalog = controller.definitionCatalog
            self.assertEqual(len(catalog), 3)
            self.assertTrue(catalog[0]["current"])
            self.assertEqual(
                {record["searchType"] for record in catalog},
                {"demo/asset", "demo/shot"},
            )
            self.assertEqual(
                controller.definitionCatalogSearchTypes,
                [
                    {"value": "demo/asset", "label": "demo/asset (Assets)"},
                    {"value": "demo/note", "label": "demo/note (Notes)"},
                    {"value": "demo/shot", "label": "demo/shot (Shots)"},
                ],
            )
            next_stype = _SType()
            next_stype.project = application.stype.project
            next_stype.get_code = lambda: "demo/shot"
            application.stype = next_stype
            controller.reload()
            catalog = controller.definitionCatalog
            self.assertEqual(catalog[0]["searchType"], "demo/shot")
            self.assertTrue(catalog[0]["current"])
            row = next(
                record["row"] for record in catalog
                if record["code"] == "WIDGET003"
            )
            simple_rows = controller.catalog_simple_rows(
                '<config><table marker="old"><element name="code">'
                'Code</element></table></config>'
            )
            self.assertIn(
                ("attribute", "marker", "old"),
                {
                    (entry["kind"], entry["name"], entry["value"])
                    for entry in simple_rows
                },
            )
            updated = controller.update_catalog_simple_value(
                '<config><table marker="old"/></config>',
                "0", "attribute", "marker", "new",
            )
            self.assertEqual(
                ElementTree.fromstring(updated).find("table").get("marker"),
                "new",
            )
            updated = controller.update_catalog_simple_value(
                '<config><table><element name="code">Code</element>'
                '</table></config>',
                "0/0", "text", "# text", "Name",
            )
            self.assertEqual(
                ElementTree.fromstring(updated).find("table/element").text,
                "Name",
            )
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
            worker = object()
            controller._workers.add(worker)
            controller._busy = True

            controller._release(worker)

        self.assertEqual(controller._stype_code, "demo/shot")

    def test_columns_editor_resolves_native_edit_widget_payload(self):
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
                return_value={
                    "InputWidgets": _layout_payload()["inputWidgets"]
                },
            ) as execute,
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()

        args = execute.call_args.args[1]["args"]
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
            self.assertIn("Asset name", texts)
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
            inline_text = value_editor.findChild(
                QObject, "sobjectValueTextEditor"
            )
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
            QTest.qWait(20)
            named_items = {
                item.objectName(): item for item in _visual_items(table)
                if item.objectName()
            }
            if screenshot_dir:
                window.grabWindow().save(str(
                    Path(screenshot_dir) / "search-table-tasks.png"
                ))
            task_card = named_items["tableTaskRecord_0"]
            self.assertLessEqual(task_card.width(), 95)
            self.assertLessEqual(task_card.height(), 62)
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
            status_label = status_cell.findChild(
                QObject, "taskTableCellDisplayLabel"
            )
            self.assertIsNotNone(status_label, warnings)
            self.assertLessEqual(
                status_label.property("font").pointSizeF(), 8.25
            )
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
            self.assertIn("publish (2)", note_texts)
            self.assertIn("publish/context (3)", note_texts)
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
                button = named_items["tableCellAction_" + kind]
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
            self.assertEqual(table_controller.clear_selection_calls, 2)
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
                "row_height:68", "row_height:84",
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
                columns.focus_requests[-1], (0, "edit_definition")
            )
            self.assertEqual(
                table_controller.opened_windows[-1], "columns_editor"
            )
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
            self.assertEqual(
                table_controller.opened_windows[-1], "columns_editor"
            )
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

    def test_definition_editor_has_simple_editsobject_and_xml_modes(self):
        application = _Application(_SType())
        application.stype.project.get_stypes = lambda: {
            code: SimpleNamespace(
                get_code=lambda value=code: value,
                get_pretty_name=lambda value=title: value,
            )
            for code, title in (
                ("demo/asset", "Assets"),
                ("demo/shot", "Shots"),
                ("demo/note", "Notes"),
            )
        }
        application.stype.project.views.config_dict.append({
            "code": "WIDGET003", "view": "table", "login": "artist",
            "search_type": "demo/shot", "config": "<config><table/></config>",
        })
        catalog_updates = []
        catalog_server = SimpleNamespace(
            query=lambda *_args: list(
                application.stype.project.views.config_dict
            ),
            build_search_key=lambda _stype, code, **_kwargs:
                f"config/widget_config?code={code}",
            insert_update=lambda key, data, **kwargs:
                catalog_updates.append((key, data, kwargs)),
        )
        from thlib.environment import env_inst
        with (
            patch(
                "thlib.tactic_classes.get_table_layout",
                return_value=_layout_payload(),
            ),
            patch(
                "thlib.tactic_classes.server_start",
                return_value=catalog_server,
            ),
            patch.object(env_inst, "server_pool", _Pool()),
        ):
            controller = ColumnsEditorController(application)
            controller.reload()
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
            engine.rootContext().setContextProperty(
                "columnsEditorModel", controller.model
            )
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "ColumnsEditorView.qml"))
            )
            editor = component.createWithInitialProperties({
                "theme": theme, "width": 820, "height": 560,
            })
            self.assertIsNotNone(
                editor, [error.toString() for error in component.errors()]
            )
            window = QQuickWindow()
            editor.setParentItem(window.contentItem())
            window.resize(820, 560)
            window.show()
            try:
                screenshot_dir = os.environ.get(
                    "DEFINITION_EDITOR_SCREENSHOT_DIR"
                )
                QTest.qWait(60)
                simple_editor = editor.findChild(
                    QObject, "tacticDefinitionSimpleEditor"
                )
                self.assertIsNotNone(simple_editor)
                self.assertIsNone(editor.findChild(
                    QObject, "tacticElementDefinitionXml"
                ))
                self.assertEqual(editor.property("selectedName"), "custom")
                controller.move(1, -1)
                QTest.qWait(20)
                self.assertEqual(editor.property("selectedRow"), 0)
                self.assertEqual(editor.property("selectedName"), "custom")
                pending = [editor]
                code_row = None
                while pending:
                    item = pending.pop()
                    if item.objectName() == "tacticColumnRow_code":
                        code_row = item
                        break
                    pending.extend(item.childItems())
                self.assertIsNotNone(code_row)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    code_row.mapToScene(QPointF(
                        code_row.width() / 2, code_row.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                self.assertEqual(editor.property("selectedName"), "code")

                edit_mode = next((
                    item for item in _visual_items(editor)
                    if item.objectName()
                    == "segmentedButtonSegment_edit_definition"
                ), None)
                self.assertIsNotNone(edit_mode)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    edit_mode.mapToScene(QPointF(
                        edit_mode.width() / 2, edit_mode.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                self.assertEqual(
                    editor.property("definitionTarget"), "edit_definition"
                )
                self.assertIsNotNone(editor.findChild(
                    QObject, "tacticEditIncluded"
                ))
                input_widget = editor.findChild(
                    QObject, "tacticInputWidget"
                )
                self.assertIsNotNone(input_widget)
                self.assertEqual(
                    input_widget.property("currentValue"),
                    "pyasm.widget.input_wdg.TextWdg",
                )

                xml_mode = next((
                    item for item in _visual_items(editor)
                    if item.objectName() == "segmentedButtonSegment_xml"
                ), None)
                self.assertIsNotNone(xml_mode)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    xml_mode.mapToScene(QPointF(
                        xml_mode.width() / 2, xml_mode.height() / 2
                    )).toPoint(),
                )
                QTest.qWait(20)
                xml_editor = editor.findChild(
                    QObject, "tacticElementDefinitionXml"
                )
                self.assertIsNotNone(xml_editor)
                self.assertIn(
                    '<element name="code"', xml_editor.property("text")
                )
                selector = editor.findChild(
                    QQuickItem, "tableViewSelectorPanel"
                )
                definition = editor.findChild(
                    QQuickItem, "elementDefinitionPanel"
                )
                self.assertIsNotNone(selector)
                self.assertIsNotNone(definition)
                self.assertGreater(definition.x(), selector.x())
                self.assertLessEqual(selector.x() + selector.width(), 820)
                self.assertLessEqual(definition.x() + definition.width(), 820)
                editor.setWidth(520)
                editor.setHeight(680)
                window.resize(520, 680)
                QTest.qWait(30)
                self.assertGreater(definition.y(), selector.y())
                self.assertLessEqual(selector.x() + selector.width(), 520)
                self.assertLessEqual(
                    definition.x() + definition.width(), 520
                )

                editor.setWidth(820)
                editor.setHeight(560)
                window.resize(820, 560)
                QTest.qWait(30)
                advanced_mode = next((
                    item for item in _visual_items(editor)
                    if item.objectName()
                    == "segmentedButtonSegment_catalog"
                ), None)
                self.assertIsNotNone(advanced_mode)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    advanced_mode.mapToScene(QPointF(
                        advanced_mode.width() / 2,
                        advanced_mode.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(30)
                catalog = editor.findChild(
                    QObject, "definitionCatalogList"
                )
                self.assertIsNotNone(catalog)
                self.assertEqual(catalog.property("count"), 1)
                catalog_simple = editor.findChild(
                    QObject, "definitionCatalogSimpleList"
                )
                self.assertIsNotNone(catalog_simple)
                self.assertIsNone(editor.findChild(
                    QObject, "definitionCatalogXml"
                ))
                catalog_xml_mode = next((
                    item for item in _visual_items(editor)
                    if item.objectName() == "catalogEditorMode_xml"
                ), None)
                self.assertIsNotNone(catalog_xml_mode)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    catalog_xml_mode.mapToScene(QPointF(
                        catalog_xml_mode.width() / 2,
                        catalog_xml_mode.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(20)
                catalog_xml = editor.findChild(
                    QObject, "definitionCatalogXml"
                )
                self.assertIsNotNone(catalog_xml)
                self.assertIn("<table>", catalog_xml.property("text"))
                all_types = next((
                    item for item in _visual_items(editor)
                    if item.objectName() == "segmentedButtonSegment_all"
                ), None)
                self.assertIsNotNone(all_types)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    all_types.mapToScene(QPointF(
                        all_types.width() / 2, all_types.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(30)
                self.assertEqual(catalog.property("count"), 2)
                search_type_filter = editor.findChild(
                    QObject, "definitionCatalogSearchTypeFilter"
                )
                self.assertIsNotNone(search_type_filter)
                self.assertTrue(search_type_filter.isVisible())
                self.assertEqual(search_type_filter.property("count"), 4)
                editor.setProperty("catalogSearchType", "demo/note")
                QTest.qWait(20)
                self.assertEqual(catalog.property("count"), 0)
                self.assertEqual(
                    editor.property("selectedCatalogIdentity"), ""
                )
                editor.setProperty("catalogSearchType", "demo/shot")
                QTest.qWait(20)
                self.assertEqual(catalog.property("count"), 1)
                self.assertEqual(
                    editor.property("catalogRows").toVariant()[0][
                        "searchType"
                    ],
                    "demo/shot",
                )
                self.assertEqual(
                    search_type_filter.property("currentValue"), "demo/shot"
                )
                editor.setProperty("catalogSearchType", "demo/asset")
                QTest.qWait(20)
                editor.setProperty("catalogSearchType", "")
                QTest.qWait(20)
                self.assertEqual(
                    {record["searchType"] for record in
                     editor.property("catalogRows").toVariant()},
                    {"demo/asset", "demo/shot"},
                )
                catalog_xml.setProperty(
                    "text", '<config><table marker="advanced"/></config>'
                )
                QTest.qWait(20)
                save_catalog = editor.findChild(
                    QQuickItem, "saveDefinitionCatalogXml"
                )
                self.assertTrue(save_catalog.isEnabled())
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    save_catalog.mapToScene(QPointF(
                        save_catalog.width() / 2,
                        save_catalog.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(30)
                self.assertEqual(catalog_updates, [(
                    "config/widget_config?code=WIDGET001",
                    {
                        "config":
                            '<config><table marker="advanced"/></config>'
                    },
                    {"triggers": False},
                )])
                catalog_simple_mode = next((
                    item for item in _visual_items(editor)
                    if item.objectName() == "catalogEditorMode_simple"
                ), None)
                self.assertIsNotNone(catalog_simple_mode)
                QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier,
                    catalog_simple_mode.mapToScene(QPointF(
                        catalog_simple_mode.width() / 2,
                        catalog_simple_mode.height() / 2,
                    )).toPoint(),
                )
                QTest.qWait(20)
                self.assertIsNotNone(editor.findChild(
                    QObject, "definitionCatalogSimpleList"
                ))
                self.assertFalse(editor.property("catalogDirty"))
                catalog_panel = editor.findChild(
                    QQuickItem, "definitionCatalogPanel"
                )
                catalog_xml_panel = editor.findChild(
                    QQuickItem, "definitionCatalogXmlPanel"
                )
                self.assertGreater(catalog_xml_panel.x(), catalog_panel.x())
                if screenshot_dir:
                    window.grabWindow().save(str(
                        Path(screenshot_dir) / "definitions-all-wide.png"
                    ))
                editor.setWidth(520)
                editor.setHeight(680)
                window.resize(520, 680)
                QTest.qWait(30)
                self.assertGreater(catalog_xml_panel.y(), catalog_panel.y())
                if screenshot_dir:
                    window.grabWindow().save(str(
                        Path(screenshot_dir) / "definitions-all-narrow.png"
                    ))
                self.assertEqual(warnings, [])
            finally:
                window.close()
                editor.setParentItem(None)
                editor.deleteLater()
                window.deleteLater()


if __name__ == "__main__":
    unittest.main()
