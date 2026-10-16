"""Isolated real Qt support views; fixtures supply data, never production settings."""

import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from thlib import environment
from thlib.ui.debug_logging import DebugLogController
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.ui_performance import UiPerformanceMonitor
from thlib.ui.workspace_models.records import RecordListModel
from tests.test_sidebar_editor_qml import SidebarEditorQmlTests


def controls(window):
    return {
        item.objectName(): item
        for item in SidebarEditorQmlTests.descendants(window.contentItem())
        if item.objectName() and item.isVisible()
    }


SCREENS = {
    "debug": "DebugLogView",
    "performance": "UiPerformanceView",
    "profile": "UserProfileView",
    "editor": "UserProfileEditorDialog",
    "sign_in": "LoginDialog",
    "presets": "ServerPresetsView",
    "updates": "UpdateView",
    "error": "ErrorDialog",
}


def variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def evaluate(engine, item, expression):
    script = QQmlExpression(QQmlEngine.contextForObject(item), item, expression)
    value, _ = script.evaluate()
    assert not script.hasError(), script.error().toString()
    return variant(value)


class Surface:
    def __init__(
        self,
        screen,
        width=1100,
        height=740,
        *,
        qml=None,
        language="en",
        dark=True,
        style="md3",
    ):
        self._closed = False
        try:
            self.create_surface(
                screen,
                width,
                height,
                qml=qml,
                language=language,
                dark=dark,
                style=style,
            )
        except BaseException:
            self.close()
            raise

    def create_surface(
        self,
        screen,
        width=1100,
        height=740,
        *,
        qml=None,
        language="en",
        dark=True,
        style="md3",
    ):
        self.app = gui_test_application()
        self.temporary = tempfile.TemporaryDirectory()
        self.previous_path = environment.env_mode.current_path
        environment.env_mode.current_path = self.temporary.name
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.components = []
        qml = qml or HANDLER / "thlib/ui/qml"
        self.controllers = self.create(
            ROOT / "tests/fixtures/FrameSupportControllers.qml"
        )
        self.debug = DebugLogController(Path(self.temporary.name))
        self.debug.set_recording_levels(self.debug.levels)
        self.debug.set_visible(True)
        self.debug.log(
            "ERROR",
            "Fixture request failed",
            group="server/query",
            command="print('fixture')",
            stacktrace="RuntimeError: fixture",
            details="Complete fixture details",
        )
        self.performance = UiPerformanceMonitor()
        self.performance._samples.append(
            dict(
                sampleId=1,
                action="Search tab: Assets",
                window="Main",
                handlerMs=12.5,
                frameMs=64.5,
                readyMs=82.0,
                details="Fixture details",
                slow=True,
                status="Ready",
            )
        )
        self.performance.set_visible(True)
        self.users = RecordListModel(
            (
                "login",
                "displayName",
                "initials",
                "email",
                "avatarUrl",
                "avatarColor",
                "groups",
                "primaryGroup",
                "current",
                "selected",
                "presenceKnown",
                "online",
                "lastSeen",
            )
        )
        self.users.replace(
            [
                dict(
                    login="artist",
                    displayName="Alice Artist",
                    initials="AA",
                    email="alice@example.test",
                    avatarUrl="",
                    avatarColor="#ad4242",
                    groups=["artists"],
                    primaryGroup="Artists",
                    current=True,
                    selected=True,
                    presenceKnown=True,
                    online=True,
                    lastSeen="",
                )
            ]
        )
        self.activity = RecordListModel(("searchKey",))
        self.groups = RecordListModel(
            ("code", "label", "description", "member", "accessLevel")
        )
        self.groups.replace(
            [
                dict(
                    code="artists",
                    label="Artists",
                    description="Production artists",
                    member=True,
                    accessLevel="low",
                ),
                dict(
                    code="reviewers",
                    label="Reviewers",
                    description="Review and approve",
                    member=False,
                    accessLevel="min",
                ),
            ]
        )
        self.presets = RecordListModel(("name", "isProtected", "isActive", "selected"))
        self.presets.replace(
            [
                dict(name="default", isProtected=True, isActive=True, selected=True),
                dict(name="studio", isProtected=False, isActive=False, selected=False),
            ]
        )
        self.releases = RecordListModel(
            ("version", "date", "changes", "misc", "archive", "selected", "kind")
        )
        self.releases.replace(
            [
                dict(
                    version="0.6.0.108",
                    date="Today",
                    changes="Fixture release notes",
                    misc="",
                    archive="fixture-release.zip",
                    selected=True,
                    kind="remote",
                )
            ]
        )
        context = self.engine.rootContext()
        for name in (
            "userController",
            "appController",
            "messagesController",
            "tasksController",
            "windowModel",
            "configurationController",
            "serverPresetsController",
            "updateController",
        ):
            context.setContextProperty(name, self.controllers.findChild(QObject, name))
        self.localization = self.create_data(
            "import QtQuick\nQtObject {property string current_language: "
            + json.dumps(language)
            + "}"
        )
        for name, value in dict(
            qml_icon_bindings(HANDLER, self.app),
            localizationController=self.localization,
            debugLog=self.debug,
            debugLogModel=self.debug.entries_model,
            debugEntryModel=self.debug.entries_model,
            debugGroupModel=self.debug.groups_model,
            debugSessionModel=self.debug.sessions_model,
            uiPerformance=self.performance,
            uiPerformanceModel=self.performance.model,
            userListModel=self.users,
            userActivityModel=self.activity,
            userGroupModel=self.groups,
            serverPresetsModel=self.presets,
            updateModel=self.releases,
        ).items():
            context.setContextProperty(name, value)
        self.theme = self.create(
            HANDLER / "thlib/ui/qml/Theme.qml",
            {
                "dark": dark,
                "styleName": style,
                "clickAnimationsEnabled": False,
                "hoverAnimationsEnabled": False,
                "fadeAnimationsEnabled": False,
                "popupAnimationsEnabled": False,
            },
        )
        self.window = QQuickWindow()
        self.window.resize(width, height)
        self.window.setTitle(
            "Application error" if screen == "error" else SCREENS[screen]
        )
        self.window.setColor(self.theme.property("workspace"))
        properties = {"theme": self.theme}
        if screen == "sign_in":
            properties["ownerWindow"] = self.window
        elif screen == "editor":
            properties["controller"] = self.controllers.findChild(
                QObject, "userController"
            )
        elif screen == "updates":
            properties["createMode"] = False
        self.view = self.create(qml / (SCREENS[screen] + ".qml"), properties)
        if screen == "sign_in":
            self.window.close()
            self.owner = self.window
            self.window = self.view
            self.window.resize(width, height)
            self.view_item = self.window.contentItem()
        elif screen == "editor":
            self.view.setParentItem(self.window.contentItem()) if isinstance(
                self.view, QQuickItem
            ) else self.view.setProperty("parent", self.window.contentItem())
            self.view.setProperty("width", min(680, width - 24))
            self.view.setProperty("height", min(690, height - 24))
            self.view_item = self.view.property("contentItem")
        else:
            self.view.setParentItem(self.window.contentItem())
            self.view.setWidth(width)
            self.view.setHeight(height)
            self.view_item = self.view
        self.window.show()
        if screen == "editor":
            evaluate(self.engine, self.view, "openForProfile()")
        self.screen = screen
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
            if self.window.isVisible():
                frame(self.window)
            else:
                self.app.processEvents()

    def item(self, name):
        result = controls(self.window).get(name)
        assert result is not None, (name, list(controls(self.window)))
        return result

    def model(self):
        name = "frameModel" if self.screen != "performance" else "frameModel"
        return variant(self.view.property(name))

    def close(self):
        if self._closed:
            return
        self._closed = True
        for name in ("debug", "performance"):
            owner = getattr(self, name, None)
            if owner:
                owner.shutdown()
        seen = set()
        for name in ("view", "window", "owner"):
            owner = getattr(self, name, None)
            if owner is None or owner in seen:
                continue
            seen.add(owner)
            if hasattr(owner, "close"):
                owner.close()
            owner.deleteLater()
        if getattr(self, "engine", None):
            self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        if hasattr(self, "previous_path"):
            environment.env_mode.current_path = self.previous_path
        if getattr(self, "temporary", None):
            self.temporary.cleanup()


def main():
    for screen in SCREENS:
        surface = None
        try:
            surface = Surface(screen)
            assert not surface.warnings, surface.warnings
            print(screen, "created", flush=True)
        finally:
            if surface:
                surface.close()


if __name__ == "__main__":
    main()
