"""Real Configuration/project QML; isolated owners and deterministic preview data."""

import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QObject, QEvent, QUrl, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from tests.test_configuration_appearance import AppearanceConfigurationTests
from tests.test_sidebar_editor_qml import SidebarEditorQmlTests
from tests.profile_ui_responsiveness import frame
from tests.frame_support_fixture import evaluate, variant
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.models import ProjectModel
from thlib.ui.project_creation import ProjectCreationController
from thlib.ui.project_editor import ProjectEditorController
from thlib.ui.repository_editor import RepositoryEditorController
from thlib.ui.cache_controller import ServerCacheController

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"

SCREENS = {
    "configuration": "ConfigurationView",
    "server": "ConfigurationServerPage",
    "checkin": "CheckinOptionsPage",
    "global": "ConfigurationGlobalPreferencesPage",
    "appearance": "ConfigurationAppearancePage",
    "cache": "ConfigurationCachePage",
    "tasks": "ConfigurationTaskPreferencesPage",
    "projects": "ConfigurationProjectPage",
    "repositories": "ConfigurationRepositoryPage",
    "repository_editor": "RepositoryEditorView",
    "wizard": "ProjectWizardView",
    "editor": "ProjectEditorView",
    "templates": "ProjectTemplatesView",
    "dcc": "ConfigurationDccPage",
}
PAGE_IDS = {
    "checkin": "checkin_preferences",
    "global": "global_preferences",
    "tasks": "tasks_preferences",
}


class Project:
    def __init__(self, code="cg", title="Computer Graphics", **info):
        self.code, self.title = code, title
        self.info = dict(
            code=code,
            title=title,
            description="Project fixture",
            category="Studio",
            type="production",
            **info,
        )

    def get_code(self):
        return self.code

    def get_title(self):
        return self.title

    def get_type(self):
        return self.info["type"]

    def get_info(self):
        return self.info

    def is_builtin(self):
        return bool(self.info.get("__builtin__"))

    def is_template(self):
        return bool(self.info.get("is_template"))

    def get_all_processes(self):
        return {}

    def get_process(self, _name):
        return None


class Windows(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot(str)
    def close_window(self, name):
        self.calls.append(("close", name))

    @Slot(str)
    def show_window(self, name):
        self.calls.append(("show", name))

    @Slot(str, str)
    def show_child_window(self, name, parent):
        self.calls.append(("child", name, parent))

    @Slot(str)
    def open_help(self, topic):
        self.calls.append(("help", topic))


class Repositories(RepositoryEditorController):
    @Slot()
    def begin_edit(self):
        if self.model.count():
            return
        records = [
            dict(
                alias="default",
                title="Main repository",
                code="default",
                windowsPath="D:/fixture/assets",
                linuxPath="/fixture/assets",
                active=True,
                isDefault=True,
                defaultEligible=True,
                status="available",
                statusText="Available",
                projectMapping="cg → default",
                selected=True,
                custom=False,
                color="#78a6c4",
            ),
            dict(
                alias="custom_0",
                title="Archive",
                code="archive",
                windowsPath="D:/fixture/archive",
                linuxPath="/fixture/archive",
                active=True,
                isDefault=False,
                defaultEligible=True,
                status="unchecked",
                statusText="Not checked",
                projectMapping="",
                selected=False,
                custom=True,
                color="#78a6c4",
            ),
        ]
        self.sync_calls = 0
        self.model.replace(records)
        self._original = self._snapshot()
        self._original_records = copy.deepcopy(records)
        self._set_configuration_summary(True, records)

    @Slot()
    def sync_team_repository_path(self):
        self.sync_calls += 1

    @Slot()
    def cancel(self):
        self.model.replace(copy.deepcopy(self._original_records))
        self.dirtyChanged.emit()


class Surface:
    def __init__(
        self,
        screen="appearance",
        width=1100,
        height=740,
        *,
        qml=None,
        language="en",
        dark=True,
        style="md3",
        server_control=None,
        database_resources=None,
    ):
        self.closed = False
        self.case = AppearanceConfigurationTests()
        self.case.server_control = server_control
        self.case.database_resources = database_resources
        self.case.setUpClass()
        self.case.setUp()
        self.app = self.case.app
        self.case.localization.set_language(language)
        self.engine = QQmlEngine()
        self.components = []
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.screen, self.language, self.dark, self.style = (
            screen,
            language,
            dark,
            style,
        )
        self.windows = Windows()
        self.projects = ProjectModel()
        self.projects.replace(
            [
                Project(),
                Project("library", "Asset library", is_template=True),
                Project("retired", "Archived project", s_status="retired"),
                Project("admin", "Administration", __builtin__=True),
            ]
        )
        self.cache = ServerCacheController()
        self.repositories = Repositories()
        self.repositories.begin_edit()
        self.creator = ProjectCreationController(SimpleNamespace())
        self.creator._catalog = dict(
            templates=[dict(value="library", label="Asset library", kind="project")],
            themes=[
                dict(
                    value="TACTIC/default_theme",
                    label="Server theme",
                    description="Fixture theme",
                )
            ],
            projectCodes=["cg", "retired"],
            installedTemplates=[
                dict(code="cg_template", path="fixture/templates/cg_template")
            ],
            defaultProject=dict(code="cg", title="Computer Graphics"),
        )
        self.editor = ProjectEditorController(
            lambda: dict(project=Project(), preview=""), None
        )
        self.editor.begin_session()
        application = self.case.controller
        props = dict(
            theme_options=application.theme_options,
            icon_set_options=application.icon_set_options,
            accent_presets=application.accent_presets,
        )
        source = (
            "import QtQuick\nQtObject {\n"
            + "\n".join(
                "property var " + name + ": " + json.dumps(value)
                for name, value in props.items()
            )
            + """
property bool has_ticket: true
property bool is_stream_server: true
property string server_api: "stream"
property bool authentication_required: false
property string login_name: "artist"
property string current_project_code: "cg"
property string current_project_title: "Computer Graphics"
function refresh_projects() {}
function select_project(code) {}
function deactivate_project() {}
function edit_project(code) {}
function request_authentication() {}
}"""
        )
        self.application = self.create_data(source)
        for name, value in dict(
            qml_icon_bindings(ROOT, self.app),
            appController=self.application,
            configurationController=self.case.config,
            localizationController=self.case.localization,
            activityFeedController=self.case.activity_notifications,
            messagesController=self.case.message_notifications,
            configPageModel=application.workspace_state.configuration_page_model,
            serverPresetModel=application.workspace_state.server_preset_model,
            windowModel=self.windows,
            projectModel=self.projects,
            projectCreationController=self.creator,
            projectEditorController=self.editor,
            repositoryEditorController=self.repositories,
            repositoryEditorModel=self.repositories.model,
            serverCacheController=self.cache,
        ).items():
            self.engine.rootContext().setContextProperty(name, value)
        config = self.case.config
        global_values = config.page_values("global_preferences")
        for target in (config._pending_values, config._original_values):
            target["global_preferences"] = global_values.copy()
            target["global_preferences"]["configPath"] = "D:/fixture/client"
        server = config._normalize_server(
            dict(
                serverUrl="http://fixture.invalid",
                presetName="default",
                rpcTransport="xmlrpc",
            )
        )
        config._original_values["server"] = server
        config._pending_values["server"] = copy.deepcopy(server)
        checkin = config._normalize_checkin({})
        config._original_values["checkin_preferences"] = checkin
        config._pending_values["checkin_preferences"] = copy.deepcopy(checkin)
        values = config.page_values("appearance")
        values.update(darkTheme=dark, themeStyle=style, language=language)
        config._pending_values["appearance"] = copy.deepcopy(values)
        config._original_values["appearance"] = copy.deepcopy(values)
        config.select_page(
            PAGE_IDS.get(screen, screen)
            if screen in PAGE_IDS or screen in config._pages
            else "server"
        )
        qml = qml or QML
        self.theme = self.create(
            qml / "Theme.qml",
            dict(
                dark=dark,
                styleName=style,
                clickAnimationsEnabled=False,
                hoverAnimationsEnabled=False,
                fadeAnimationsEnabled=False,
                popupAnimationsEnabled=False,
            ),
        )
        self.window = QQuickWindow()
        self.window.setWidth(width)
        self.window.setHeight(height)
        self.window.setColor(QColor(self.theme.property("workspace")))
        properties = dict(theme=self.theme)
        if screen == "configuration":
            properties["windowId"] = "configuration"
        if screen == "dcc":
            properties["pageId"] = next(
                key
                for key, value in config._dcc_pages.items()
                if value["application"] == "maya"
            )
            properties["managed"] = True
            config.select_page(properties["pageId"])
        if screen in ("server", "checkin", "global", "appearance", "cache", "tasks"):
            properties["managed"] = True
        self.view = self.create(qml / (SCREENS[screen] + ".qml"), properties)
        self.view.setParentItem(self.window.contentItem())
        self.view.setWidth(width)
        self.view.setHeight(height)
        self.window.show()
        self.settle()

    def create(self, path, properties=None):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(path)))
        assert component.isReady(), [error.toString() for error in component.errors()]
        value = component.createWithInitialProperties(properties or {})
        assert value is not None, [error.toString() for error in component.errors()]
        QObject.setParent(value, self.engine)
        self.components.append(component)
        return value

    def create_data(self, source):
        component = QQmlComponent(self.engine)
        component.setData(source.encode(), QUrl())
        assert component.isReady(), [error.toString() for error in component.errors()]
        value = component.create()
        assert value is not None
        QObject.setParent(value, self.engine)
        self.components.append(component)
        return value

    def settle(self):
        for _ in range(3):
            frame(self.window)

    def item(self, name):
        for item in SidebarEditorQmlTests.descendants(self.window.contentItem()):
            if item.objectName() == name:
                return item
        raise AssertionError("Missing actual QML item: " + name)

    def evaluate(self, expression):
        return evaluate(self.engine, self.view, expression)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.window.close()
        self.window.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.case.doCleanups()
