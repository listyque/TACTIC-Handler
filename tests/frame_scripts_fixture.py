"""Offline production surfaces for B13 original/current comparisons."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.profile_ui_responsiveness import frame
from tests.test_frame_script_tools import QML, ScriptToolsTests
from tests.test_handler_server_controller import HandlerServerControllerTests
from tests.test_script_shelf import ScriptShelfTests, _button, _record
from tests.test_script_triggers import ScriptTriggerTests, _rule
from thlib.ui.dcc_options import DccOptionsController
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.script_editor import ScriptEditorController
from thlib.ui.workspace_models.records import RecordListModel

SCREENS = {
    "editor": "ScriptEditorView",
    "shelf": "ScriptShelfEditorView",
    "bar": "ScriptShelfBar",
    "triggers": "ScriptTriggerEditorView",
    "dcc": "DccOptionsView",
    "server": "HandlerServerView",
    "database": "DatabaseEditorView",
    "database_batch": "DatabaseBatchEditorView",
}


class Surface(ScriptToolsTests):
    def __init__(
        self,
        screen,
        width=900,
        height=650,
        *,
        qml=None,
        dark=True,
        style="md3",
        language="en",
        case="initial",
    ):
        super().__init__()
        self.setUpClass()
        self.setUp()
        self.screen = screen
        self.owner_fixture = None
        self.controller = None
        self.qml = Path(qml or QML)
        self.theme.setProperty("dark", dark)
        self.theme.setProperty("styleName", style)
        self.language = self.inline(
            'import QtQml; QtObject { property string current_language: "'
            + language
            + '" }'
        )
        context = self.engine.rootContext()
        context.setContextProperty("localizationController", self.language)
        self.icon_bindings = qml_icon_bindings(QML.parents[2], self.engine)
        for name, value in self.icon_bindings.items():
            context.setContextProperty(name, value)
        self.windows_owner = self.inline("""import QtQml
QtObject { signal windowVisibilityChanged(string windowId, bool visible)
function open_help(topic) {} function close_window(windowId) {} function show_window(windowId) {} }""")
        context.setContextProperty("windowModel", self.windows_owner)
        if screen == "editor":
            with (
                patch("thlib.ui.script_editor.env_read_config", return_value={}),
                patch("thlib.ui.script_editor.env_write_config"),
            ):
                self.controller = ScriptEditorController(None, Mock())
            self.controller.load = lambda: None
            self.controller.readSettings = lambda: None
            self.controller.writeSettings = lambda: None
            self.controller._write_settings = lambda: None
            self.controller.update_editor_state(
                "",
                "tools",
                "Selection example",
                "python",
                "for asset in selection:\n    print(asset)\n",
                "server",
            )
            context.setContextProperty("scriptEditorController", self.controller)
            context.setContextProperty("scriptEditorModel", self.controller.model)
            context.setContextProperty("scriptEditorTabModel", self.controller.tabs)
        elif screen in ("shelf", "bar"):
            fixture = ScriptShelfTests()
            fixture.setUp()
            self.owner_fixture = fixture
            self.controller = fixture.controller
            self.controller._project_code = "fixture"
            self.controller._sync_records(
                [
                    _record(
                        "script_shelf@global",
                        "Shared shelf",
                        [
                            _button("save", "tools/save"),
                            _button("publish", "tools/publish"),
                        ],
                    )
                ]
            )
            self.controller.set_editor_mode("shared")
            sidebar = self.inline("import QtQml; QtObject { property var scriptShelf }")
            sidebar.setProperty("scriptShelf", self.controller)
            context.setContextProperty("sidebarEditorController", sidebar)
            tree = RecordListModel(
                (
                    "token",
                    "nodeType",
                    "path",
                    "folder",
                    "title",
                    "language",
                    "depth",
                    "expanded",
                    "hasChildren",
                )
            )
            self.tree = tree
            context.setContextProperty("scriptEditorModel", tree)
            context.setContextProperty("scriptEditorController", fixture.editor)
            if case == "dirty":
                self.controller.add_button()
        elif screen == "triggers":
            fixture = ScriptTriggerTests()
            fixture.setUp()
            self.owner_fixture = fixture
            self.controller = fixture.controller
            self.controller.rules.replace(
                self.controller._present([_rule("first", "tools/one")])
            )
            self.controller.select(0)
            context.setContextProperty("scriptTriggerController", self.controller)
            context.setContextProperty("scriptTriggerModel", self.controller.model)
            context.setContextProperty("scriptEditorController", fixture.scripts)
            context.setContextProperty("scriptEditorModel", fixture.scripts.model)
        elif screen == "dcc":
            self.controller = DccOptionsController(
                SimpleNamespace(
                    window_model=SimpleNamespace(close_window=lambda _: None)
                ),
                lambda *args: True,
            )
            self.controller.attach_dcc_bridge(
                SimpleNamespace(
                    selectedClient="maya-one",
                    selectedApplicationType="maya",
                    has_dcc_capability=lambda _: True,
                    stateChanged=SimpleNamespace(connect=lambda _: None),
                )
            )
            with (
                patch("thlib.ui.dcc_options.env_read_config", return_value={}),
                patch("thlib.ui.dcc_options.read_dcc_preferences", return_value={}),
            ):
                self.controller.prepare_target("save", "node-a", "Asset A")
            context.setContextProperty("dccOptionsController", self.controller)
        elif screen == "server":
            fixture = HandlerServerControllerTests()
            fixture.setUp()
            self.owner_fixture = fixture
            self.controller = fixture.controller
            for name, value in {
                "handlerServerController": self.controller,
                "handlerClientModel": self.controller.clients,
                "handlerCapabilityModel": self.controller.capabilities,
                "handlerResultModel": self.controller.results,
            }.items():
                context.setContextProperty(name, value)
        if self.controller is not None:
            if case == "busy" and hasattr(self.controller, "_busy"):
                self.controller._busy = True
                self.controller.stateChanged.emit()
            if case == "error" and hasattr(self.controller, "_error"):
                self.controller._error = (
                    "Fixture request failed. Retry after reconnecting."
                )
                self.controller.stateChanged.emit()
        if case == "locked":
            if screen.startswith("database"):
                self.owner.setProperty("loading", True)
            elif screen == "dcc":
                self.controller._dcc_bridge.selectedClient = "maya-two"
            elif screen == "server":
                self.controller._error = (
                    "Fixture request failed. Retry after reconnecting."
                )
            elif self.controller is not None:
                self.controller._busy = True
            if self.controller is not None:
                self.controller.stateChanged.emit()
        properties = {"theme": self.theme, "width": width, "height": height}
        if screen == "bar":
            properties["controller"] = self.controller
        self.view = self.create(self.qml / (SCREENS[screen] + ".qml"), properties)
        from PySide6.QtQuick import QQuickWindow

        self.window = QQuickWindow()
        self.windows.append(self.window)
        self.window.setColor(
            self.theme.property(
                "surfaceContainerHigh" if screen == "bar" else "workspace"
            )
        )
        self.window.resize(width, height)
        self.view.setParentItem(self.window.contentItem())
        self.window.show()
        frame(self.window)

    def dispose(self):
        self.close()
        if isinstance(self.owner_fixture, HandlerServerControllerTests):
            self.owner_fixture.tearDown()
        elif isinstance(self.owner_fixture, ScriptShelfTests):
            self.owner_fixture.doCleanups()
        self.doCleanups = lambda: None
