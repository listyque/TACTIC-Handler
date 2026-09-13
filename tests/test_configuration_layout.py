from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator
from thlib.ui.editor_tools import ServerPresetsController
from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _ServerPresetWindowModel(QObject):
    @Slot(str)
    def open_help(self, _topic):
        pass

    @Slot(str)
    def close_window(self, _window_id):
        pass


class _ServerPresetConfigurationController(QObject):
    @Slot()
    def begin_session(self):
        pass


class _ConfigurationHelpWindowModel(QObject):
    def __init__(self):
        super().__init__()
        self.topics = []

    @Slot(str)
    def open_help(self, topic):
        self.topics.append(topic)


class ConfigurationLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_configuration_header_help_opens_current_page_article(self):
        source = (QML / "ConfigurationView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("return page.helpTopic", source)
        self.assertIn("return qsTr(page.description", source)

        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        pages = RecordListModel(
            ("title", "target", "icon", "description", "helpTopic"),
            [{
                "title": "Configuration",
                "target": "unregistered_page",
                "icon": "settings",
                "description": "External DCC settings",
                "helpTopic": "dcc_clients",
            }],
        )
        window_model = _ConfigurationHelpWindowModel()
        engine.rootContext().setContextProperty("configPageModel", pages)
        engine.rootContext().setContextProperty("windowModel", window_model)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import "." as App

ApplicationWindow {
    width: 760
    height: 560
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: configurationController
        signal confirmationRequested()
        property string current_page: "unregistered_page"
        property bool current_page_dirty: false
        property bool can_reset_current_page: false
        function select_page(pageId) { current_page = pageId }
        function reset_current() {}
        function apply_current() { return true }
        function save_and_close() {}
        function request_close() {}
        function discard_and_close() {}
    }

    App.ConfigurationView {
        objectName: "configurationView"
        anchors.fill: parent
        theme: theme
        windowId: "configuration"
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ConfigurationHelpTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(60)
            button = owner.findChild(
                QQuickItem, "configurationHelpButton"
            )
            self.assertIsNotNone(button)
            for width in (620, 980):
                owner.setWidth(width)
                QTest.qWait(30)
                position = button.mapToItem(
                    owner.contentItem(), QPointF(0, 0)
                )
                self.assertGreaterEqual(position.x(), 216)
                self.assertLessEqual(
                    position.x() + button.width(), width + 0.1
                )
                self.assertFalse(owner.grabWindow().isNull())
            QTest.mouseClick(
                owner,
                Qt.LeftButton,
                pos=button.mapToScene(QPointF(
                    button.width() / 2, button.height() / 2
                )).toPoint(),
            )
            self.assertEqual(window_model.topics, ["dcc_clients"])
        finally:
            owner.close()
            owner.deleteLater()
            pages.deleteLater()
            window_model.deleteLater()
            engine.deleteLater()

    def test_manifest_dcc_preferences_render_and_update(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "." as App

ApplicationWindow {
    width: 720
    height: 760
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: configurationController
        objectName: "mayaConfigurationControllerStub"
        signal sessionStarted()
        signal pageReset(string pageId)
        property var updatedValues: ({})
        function page_values(pageId) {
            return ({
                "scene_type": "mayaAscii",
                "create_maya_dirs": true,
                "focus_after_open": false
            })
        }
        function page_schema(pageId) {
            return ({
                "sections": [{
                    "title": "Scene",
                    "fields": [{
                        "key": "scene_type",
                        "type": "choice",
                        "title": "Scene format",
                        "default": "mayaBinary",
                        "choices": [
                            {"label": "Maya ASCII", "value": "mayaAscii"},
                            {"label": "Maya Binary", "value": "mayaBinary"}
                        ]
                    }, {
                        "key": "create_maya_dirs",
                        "type": "boolean",
                        "title": "Create Maya directories",
                        "default": false
                    }, {
                        "key": "focus_after_open",
                        "type": "boolean",
                        "title": "Return focus",
                        "default": true
                    }]
                }]
            })
        }
        function update_page(pageId, values) {
            updatedValues = values
        }
    }

    App.ConfigurationDccPage {
        objectName: "dccPreferencesPage"
        anchors.fill: parent
        theme: theme
        pageId: "dcc.maya"
        managed: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_DccPreferencesLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            visual_items = [owner.contentItem()]
            for item in visual_items:
                visual_items.extend(item.childItems())
            open_focus_switch = next(
                item for item in visual_items
                if item.objectName() == "dccSettingControl_focus_after_open"
            )
            directories_switch = next(
                item for item in visual_items
                if item.objectName() == "dccSettingControl_create_maya_dirs"
            )
            controller = owner.findChild(
                QObject, "mayaConfigurationControllerStub"
            )
            page = owner.findChild(QObject, "dccPreferencesPage")
            self.assertIsNotNone(open_focus_switch)
            self.assertIsNotNone(directories_switch)
            self.assertFalse(open_focus_switch.property("checked"))
            self.assertTrue(directories_switch.property("checked"))
            self.assertTrue(page.property("managed"))
            self.assertFalse(page.property("loadingValues"))
            scene = owner.contentItem()
            for width in (500, 720):
                owner.setProperty("width", width)
                QTest.qWait(40)
                for control in (
                    directories_switch, open_focus_switch,
                ):
                    position = control.mapToItem(scene, QPointF(0, 0))
                    self.assertGreaterEqual(position.x(), -0.1)
                    self.assertLessEqual(
                        position.x() + control.width(), width + 0.1
                    )
                self.assertFalse(owner.grabWindow().isNull())

            open_focus_switch.forceActiveFocus()
            QTest.keyClick(owner, Qt.Key_Space)
            QTest.qWait(20)
            self.assertTrue(open_focus_switch.property("checked"))
            values = controller.property("updatedValues")
            if hasattr(values, "toVariant"):
                values = values.toVariant()
            self.assertTrue(values["focus_after_open"])
            self.assertTrue(values["create_maya_dirs"])
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_task_preferences_load_surface_and_quick_view_choices(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 500
    height: 600
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: configurationController
        signal sessionStarted()
        signal pageReset(string pageId)
        function page_values(pageId) {
            return ({
                viewMode: "list", sortMode: "priority",
                groupMode: "process", quickViewMode: "compact",
                workspaceSurface: "browser", inspectorExpanded: false,
                columns: []
            })
        }
        function update_page(pageId, values) {}
    }

    App.ConfigurationTaskPreferencesPage {
        anchors.fill: parent
        theme: theme
        managed: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_TaskPreferencesLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            surface = owner.findChild(
                QQuickItem, "taskPreferencesSurfaceCombo"
            )
            quick_view = owner.findChild(
                QQuickItem, "taskPreferencesQuickViewCombo"
            )
            self.assertIsNotNone(surface)
            self.assertIsNotNone(quick_view)
            self.assertEqual(surface.property("currentIndex"), 1)
            self.assertEqual(quick_view.property("currentIndex"), 1)
            for width in (500, 760):
                owner.setProperty("width", width)
                QTest.qWait(30)
                self.assertFalse(owner.grabWindow().isNull())
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_appearance_picker_updates_independent_preferences(self):
        translator = CatalogTranslator(
            ROOT / "thlib" / "ui" / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 720
    height: 640
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: appController
        property var theme_options: [{
            "value": "md3", "label": "Material 3",
            "description": "Material 3"
        }]
        property var theme_accents: ({
            "md3": {"light": "steel", "dark": "steel"}
        })
        property var accent_presets: [{
            "value": "steel", "label": "Steel",
            "light": "#506070", "lightBase": "#f0f0f0",
            "dark": "#90a0b0", "darkBase": "#202224"
        }]
        property var icon_set_options: [{
            "value": "automatic", "label": "Automatic",
            "description": "Automatic"
        }]
    }
    QtObject {
        id: localizationController
        property var language_options: [{
            "value": "en", "label": "English"
        }]
    }
    QtObject {
        id: configurationController
        objectName: "configurationControllerStub"
        signal sessionStarted()
        signal pageReset(string pageId)
        property var updatedValues: ({})
        property string updatedPageId: ""
        function page_values(pageId) {
            return ({
                "closeToTray": true,
                "darkTheme": true,
                "themeStyle": "md3",
                "themeAccents": appController.theme_accents,
                "iconSet": "automatic",
                "clickAnimations": false,
                "hoverAnimations": true,
                "fadeAnimations": false,
                "popupAnimations": false,
                "renderBackend": "d3d11",
                "language": "en",
                "debugLogLevels": ["ERROR"],
                "configPath": "D:/TACTIC"
            })
        }
        function update_page(pageId, values) {
            updatedPageId = pageId
            updatedValues = values
        }
    }

    App.ConfigurationAppearancePage {
        anchors.fill: parent
        theme: theme
        managed: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_RenderBackendLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            combo = owner.findChild(QObject, "renderBackendCombo")
            controller = owner.findChild(
                QObject, "configurationControllerStub"
            )
            self.assertIsNotNone(combo)
            self.assertEqual(combo.property("count"), 6)
            self.assertEqual(combo.property("currentValue"), "d3d11")
            click_motion = owner.findChild(
                QObject, "clickAnimationsSwitch"
            )
            hover_motion = owner.findChild(
                QObject, "hoverAnimationsSwitch"
            )
            fade_motion = owner.findChild(
                QObject, "fadeAnimationsSwitch"
            )
            popup_motion = owner.findChild(
                QObject, "popupAnimationsSwitch"
            )
            self.assertIsNotNone(click_motion)
            self.assertIsNotNone(hover_motion)
            self.assertIsNotNone(fade_motion)
            self.assertFalse(click_motion.property("checked"))
            self.assertTrue(hover_motion.property("checked"))
            self.assertFalse(fade_motion.property("checked"))
            self.assertIsNotNone(popup_motion)
            self.assertFalse(popup_motion.property("checked"))

            combo.setProperty("currentIndex", 5)
            combo.activated.emit(5)
            QTest.qWait(20)
            values = controller.property("updatedValues")
            if hasattr(values, "toVariant"):
                values = values.toVariant()
            self.assertEqual(values["renderBackend"], "software")
            self.assertEqual(controller.property("updatedPageId"), "appearance")
            self.assertNotIn("closeToTray", values)
            self.assertNotIn("debugLogLevels", values)
            self.assertFalse(values["popupAnimations"])
            popup_motion.setProperty("checked", True)
            popup_motion.toggled.emit()
            self.assertTrue(
                controller.property("updatedValues").toVariant()["popupAnimations"]
            )
            for width in (460, 980):
                owner.setWidth(width)
                self.app.processEvents()
                flickable = popup_motion.parentItem()
                while flickable.property("contentY") is None:
                    flickable = flickable.parentItem()
                switch_position = popup_motion.mapToItem(flickable, QPointF(0, 0))
                flickable.setProperty("contentY", (
                    flickable.property("contentY") + switch_position.y()
                    - flickable.height() / 2
                ))
                self.app.processEvents()
                switch_position = popup_motion.mapToScene(QPointF(0, 0))
                self.assertGreaterEqual(switch_position.x(), 0)
                self.assertLessEqual(switch_position.x() + popup_motion.width(), width)
                self.assertGreaterEqual(switch_position.y(), 0)
                self.assertLessEqual(switch_position.y() + popup_motion.height(), owner.height())
                previous = popup_motion.property("checked")
                point = popup_motion.mapToScene(QPointF(
                    popup_motion.width() / 2, popup_motion.height() / 2,
                )).toPoint()
                QTest.mouseClick(owner, Qt.LeftButton, pos=point)
                values = controller.property("updatedValues").toVariant()
                self.assertEqual(values["popupAnimations"], not previous)
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_server_presets_layout_marks_active_and_reserves_scrollbar(self):
        translator = CatalogTranslator(
            ROOT / "thlib" / "ui" / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        workspace = SimpleNamespace(
            server_preset_model=RecordListModel(("label",))
        )
        presets_controller = ServerPresetsController(workspace)
        presets_controller._active_name = "default"
        presets_controller._drafts = {
            "default": {
                "server": "https://tactic.example",
                "user": "artist",
                "ticket": "stored-ticket",
                "site": {"site_name": "", "enabled": False},
                "proxy": {
                    "login": "", "pass": "", "server": "",
                    "enabled": False,
                },
            },
            "long-studio-server-preset": {
                "server": "https://studio.example",
                "user": "",
                "ticket": None,
                "site": {"site_name": "", "enabled": False},
                "proxy": {
                    "login": "", "pass": "", "server": "",
                    "enabled": False,
                },
            },
        }
        presets_controller._replace(
            ["default", "long-studio-server-preset"], "default"
        )
        window_model = _ServerPresetWindowModel()
        configuration_controller = _ServerPresetConfigurationController()
        context = engine.rootContext()
        context.setContextProperty(
            "serverPresetsController", presets_controller
        )
        context.setContextProperty(
            "serverPresetsModel", presets_controller.model
        )
        context.setContextProperty("windowModel", window_model)
        context.setContextProperty(
            "configurationController", configuration_controller
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 720
    height: 520
    visible: true

    App.Theme { id: theme; dark: true }

    App.ServerPresetsView {
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ServerPresetsLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for width in (720, 1040):
                owner.setWidth(width)
                QTest.qWait(40)
                presets = owner.findChild(QQuickItem, "serverPresetsList")
                details = owner.findChild(
                    QQuickItem, "serverPresetDetailsPane"
                )
                self.assertIsNotNone(presets)
                self.assertIsNotNone(details)
                visual_items = [presets]
                for item in visual_items:
                    visual_items.extend(item.childItems())
                row = next((
                    item for item in visual_items
                    if item.objectName() == "serverPresetRow"
                ), None)
                chip = next((
                    item for item in visual_items
                    if item.objectName() == "activeServerPresetChip"
                ), None)
                self.assertIsNotNone(row, {
                    "count": presets.property("count"),
                    "width": presets.property("width"),
                    "height": presets.property("height"),
                    "visible": presets.property("visible"),
                })
                self.assertIsNotNone(chip)
                self.assertGreater(float(presets.property("height")), 0.0)
                self.assertAlmostEqual(
                    float(presets.property("width"))
                        - float(row.property("width")),
                    14.0,
                    delta=0.5,
                )
                self.assertLessEqual(
                    chip.mapToScene(QPointF(chip.width(), 0)).x(),
                    row.mapToScene(QPointF(row.width(), 0)).x() + 0.5,
                )
                self.assertLess(
                    presets.mapToScene(QPointF(presets.width(), 0)).x(),
                    details.mapToScene(QPointF(0, 0)).x(),
                )
                self.assertEqual(chip.property("text"), "Активен")
        finally:
            owner.close()
            owner.deleteLater()
            presets_controller.deleteLater()
            workspace.server_preset_model.deleteLater()
            window_model.deleteLater()
            configuration_controller.deleteLater()
            engine.deleteLater()
            self.app.removeTranslator(translator)

    def test_checkin_rows_have_width_and_do_not_overlap(self):
        translator = CatalogTranslator(
            ROOT / "thlib" / "ui" / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 500
    height: 600
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: configurationController
        signal sessionStarted()
        signal pageReset(string pageId)
        function page_values(pageId) {
            return ({repositories: [{title: "Main", code: "main"}]})
        }
        function update_page(pageId, values) {}
    }
    QtObject {
        id: repositoryEditorController
        property string current_path: "D:/TACTIC/repository/project"
        function check_paths() {}
    }
    QtObject {
        id: windowModel
        function show_window(name) {}
    }

    App.CheckinOptionsPage {
        anchors.fill: parent
        theme: theme
        managed: false
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_CheckinLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            scene = owner.contentItem()
            for width in (500, 720):
                owner.setProperty("width", width)
                QTest.qWait(60)
                rows = []
                for item in owner.findChildren(QQuickItem):
                    if "SettingsRow" not in item.metaObject().className():
                        continue
                    position = item.mapToItem(scene, QPointF(0, 0))
                    rows.append((position.y(), item.height(), item.width()))

                rows.sort(key=lambda record: record[0])
                self.assertGreaterEqual(len(rows), 25)
                self.assertTrue(all(row[2] > 1 for row in rows))
                self.assertTrue(all(
                    current[0] + current[1] <= following[0] + 0.1
                    for current, following in zip(rows, rows[1:])
                ))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()
            self.app.removeTranslator(translator)

    def test_cache_page_reflows_and_keeps_its_shared_scrollbar(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 360
    height: 520
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: configurationController
        signal sessionStarted()
        signal pageReset(string pageId)
        function page_values(pageId) {
            return ({
                reference: true, search: true, snapshots: true,
                relations: true, tasks: true, notes: true,
                messages: true, activity: true, work_hours: true
            })
        }
        function update_page(pageId, values) {}
        function clear_data_cache() { return true }
    }
    QtObject {
        id: serverCacheController
        property bool busy: false
        property string message: ""
    }

    App.ConfigurationCachePage {
        anchors.fill: parent
        theme: theme
        managed: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_CachePageLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for width in (360, 760):
                owner.setProperty("width", width)
                QTest.qWait(80)
                image = owner.grabWindow()
                self.assertFalse(image.isNull())
                self.assertEqual(image.width(), width)
            scrollbars = [
                item for item in owner.findChildren(QQuickItem)
                if item.objectName() == "cacheScrollBar"
            ]
            self.assertTrue(scrollbars)
            scroll = owner.findChild(QQuickItem, "cacheScrollView")
            self.assertTrue(
                any(item.height() > 1 for item in scrollbars),
                "scroll=({}, {}, {}) bar=({}, {}, {})".format(
                    scroll.height() if scroll else -1,
                    scroll.property("contentHeight") if scroll else -1,
                    scroll.property("availableHeight") if scroll else -1,
                    scrollbars[0].height(),
                    scrollbars[0].property("hasOverflow"),
                    scrollbars[0].property("visible"),
                ),
            )
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_repository_page_reflows_and_keeps_primary_action_visible(self):
        translator = CatalogTranslator(
            ROOT / "thlib" / "ui" / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import QtQml.Models
import "." as App

Window {
    width: 480
    height: 580
    visible: true

    App.Theme { id: theme; dark: true }
    ListModel {
        id: repositoryEditorModel
        Component.onCompleted: {
            append({
                "title": "General", "code": "base",
                "windowsPath": "D:/TACTIC/repository",
                "linuxPath": "/mnt/tactic/repository",
                "active": true, "isDefault": true,
                "status": "unchecked", "statusText": "Not checked"
            })
            append({
                "title": "Local", "code": "local",
                "windowsPath": "D:/TACTIC/local",
                "linuxPath": "/mnt/tactic/local",
                "active": true, "isDefault": false,
                "status": "unchecked", "statusText": "Not checked"
            })
        }
    }
    QtObject {
        id: repositoryEditorController
        property bool configuration_required: false
        property bool configuration_loaded: true
        property string current_title: "General"
        property string current_path: "D:/TACTIC/repository"
        property int active_count: 2
        property bool busy: false
        property string message: ""
        function begin_edit() {}
        function check_paths() {}
    }
    QtObject {
        id: windowModel
        function show_window(name) {}
    }

    App.ConfigurationRepositoryPage {
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_RepositoryPageLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            scene = owner.contentItem()
            button = owner.findChild(QQuickItem, "openRepositoryEditorButton")
            self.assertIsNotNone(button)
            for width in (480, 820):
                owner.setProperty("width", width)
                QTest.qWait(80)
                position = button.mapToItem(scene, QPointF(0, 0))
                self.assertGreaterEqual(position.x(), -0.1)
                self.assertLessEqual(position.x() + button.width(), width + 0.1)
                self.assertGreater(button.height(), 20)
                image = owner.grabWindow()
                self.assertFalse(image.isNull())
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()
            self.app.removeTranslator(translator)

    def test_missing_repository_opens_one_modal_setup_prompt(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 640
    height: 480
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: applicationController
        signal server_state_changed()
        property string server_state: "online"
    }
    QtObject {
        id: configurationController
        function select_page(pageId) {}
    }
    QtObject {
        id: repositoryController
        signal configurationChanged()
        property bool configuration_loaded: true
        property bool configuration_required: true
        function begin_edit() {}
    }
    QtObject {
        id: windows
        function show_window(windowId) {}
    }

    App.RepositorySetupPrompt {
        anchors.fill: parent
        theme: theme
        applicationController: applicationController
        configurationController: configurationController
        repositoryController: repositoryController
        windows: windows
        smokeMode: false
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_RepositoryPromptTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            prompt = owner.findChild(QObject, "repositorySetupPrompt")
            self.assertIsNotNone(prompt)
            self.assertTrue(prompt.property("opened"))
            self.assertTrue(prompt.property("modal"))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_project_list_reflows_without_clipping_on_narrow_and_wide_windows(self):
        translator = CatalogTranslator(
            ROOT / "thlib" / "ui" / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import QtQml.Models
import "." as App

Window {
    width: 520
    height: 620
    visible: true

    App.Theme { id: theme; dark: true }
    ListModel {
        id: projectModel
        property bool showRetired: false
        property bool showTemplates: false
        property bool showBuiltins: false
        property int retiredCount: 1
        property int templateCount: 1
        property int builtinCount: 1
        property int visibleCount: count
        property int totalCount: count
        function setShowRetired(value) { showRetired = value }
        function setShowTemplates(value) { showTemplates = value }
        function setShowBuiltins(value) { showBuiltins = value }
        Component.onCompleted: {
            append({"projectDetails": {
                "code": "animation", "title": "Animation Project",
                "category": "Production", "projectType": "Animation",
                "status": "In progress", "systemStatus": "",
                "isBuiltin": false, "isTemplate": false,
                "isRetired": false, "isActive": true,
                "description": "A deliberately long project description for layout testing.",
                "preview": "", "initials": "AP"
            }})
            append({"projectDetails": {
                "code": "sthpw", "title": "TACTIC system project",
                "category": "System", "projectType": "built-in",
                "status": "", "systemStatus": "",
                "isBuiltin": true, "isTemplate": false,
                "isRetired": false, "isActive": true,
                "description": "Built-in project",
                "preview": "", "initials": "TS"
            }})
        }
    }
    QtObject {
        id: appController
        property string current_project_title: "Animation Project"
        function select_project(code) {}
        function edit_project(code) {}
    }
    QtObject {
        id: windowModel
        function show_window(name) {}
    }

    App.ConfigurationPage {
        anchors.fill: parent
        theme: theme
        pageId: "project"
        managed: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ProjectLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            scene = owner.contentItem()
            panel = owner.findChild(QQuickItem, "projectPanel")
            layout = owner.findChild(QQuickItem, "projectPageLayout")
            section = owner.findChild(QQuickItem, "projectCatalogSection")
            for width in (520, 980):
                owner.setProperty("width", width)
                QTest.qWait(100)
                project_list = owner.findChild(
                    QQuickItem, "configurationProjectList"
                )
                visual_items = []
                pending = [scene]
                while pending:
                    item = pending.pop()
                    visual_items.append(item)
                    pending.extend(item.childItems())
                cards = [
                    item for item in visual_items
                    if item.objectName() == "projectCard"
                ]
                self.assertIsNotNone(project_list)
                self.assertGreater(project_list.width(), 300)
                self.assertGreater(project_list.height(), 250)
                previews = [
                    item for item in visual_items
                    if item.objectName() == "projectCompactPreview"
                    and item.isVisible()
                ]
                self.assertGreaterEqual(len(previews), 2)
                self.assertTrue(all(
                    abs(item.width() - item.height()) < 0.1 for item in previews))
                self.assertEqual(project_list.property("count"), 2)
                self.assertGreaterEqual(len(cards), 2)
                for card in cards:
                    position = card.mapToItem(scene, QPointF(0, 0))
                    self.assertGreaterEqual(position.x(), -0.1)
                    self.assertLessEqual(
                        position.x() + card.width(), width + 0.1,
                        "card=({}, {}, {}) list=({}, {}, {}) window=({}, {}) scene={} panel={} layout={} section={}".format(
                            position.x(), card.width(), card.height(),
                            project_list.x(), project_list.width(), project_list.height(),
                            owner.width(), owner.height(), scene.width(),
                            panel.width() if panel else -1,
                            layout.width(), section.width(),
                        ),
                    )
                    self.assertGreater(card.width(), 280)
                    self.assertGreaterEqual(card.height(), 110)
                image = owner.grabWindow()
                self.assertFalse(image.isNull())
                self.assertEqual(image.width(), width)
            for toggle_name in (
                "projectFilterRetiredToggle",
                "projectFilterTemplatesToggle",
                "projectFilterBuiltinsToggle",
            ):
                toggle = owner.findChild(QObject, toggle_name)
                self.assertIsNotNone(toggle)
                self.assertFalse(toggle.property("checked"))
            action_buttons = [
                owner.findChild(QQuickItem, object_name)
                for object_name in (
                    "activateSelectedProjectButton",
                    "editSelectedProjectButton",
                    "createProjectButton",
                )
            ]
            self.assertTrue(all(action_buttons))
            self.assertTrue(all(button.isVisible() for button in action_buttons))
            button_bounds = [
                (
                    button.mapToItem(scene, QPointF(0, 0)).y(),
                    button.height(),
                )
                for button in action_buttons
            ]
            self.assertTrue(all(
                current_y + current_height + 7.5 <= following_y
                for (current_y, current_height), (following_y, _)
                in zip(button_bounds, button_bounds[1:])
            ))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()
            self.app.removeTranslator(translator)

    def test_quick_project_chooser_keeps_filters_and_square_previews_separate(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import "." as App

ApplicationWindow {
    width: 540
    height: 700
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: projectModel
        property bool showRetired: false
        property bool showTemplates: false
        property bool showBuiltins: false
        property int retiredCount: 1
        property int templateCount: 1
        property int builtinCount: 1
        property int visibleCount: 3
        property int totalCount: 5
        property var groups: [{
            "title": "Production",
            "projects": [
                {"code": "one", "title": "Project One",
                 "category": "Production", "projectType": "Animation",
                 "description": "First project", "preview": "",
                 "initials": "PO", "isBuiltin": false,
                 "isTemplate": false, "isRetired": false},
                {"code": "two", "title": "Project Two",
                 "category": "Production", "projectType": "VFX",
                 "description": "Second project", "preview": "",
                 "initials": "PT", "isBuiltin": false,
                 "isTemplate": false, "isRetired": false},
                {"code": "sthpw", "title": "TACTIC system",
                 "category": "System", "projectType": "built-in",
                 "description": "Built-in project", "preview": "",
                 "initials": "TS", "isBuiltin": true,
                 "isTemplate": false, "isRetired": false}
            ]
        }]
        function setShowRetired(value) { showRetired = value }
        function setShowTemplates(value) { showTemplates = value }
        function setShowBuiltins(value) { showBuiltins = value }
    }

    App.ProjectChooser {
        id: chooser
        theme: theme
        model: projectModel
    }
    Component.onCompleted: chooser.open()
}
''',
            QUrl.fromLocalFile(str(QML / "_ProjectChooserLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(150)
            scene = owner.contentItem()
            visual_items = []
            pending = [scene]
            while pending:
                item = pending.pop()
                visual_items.append(item)
                pending.extend(item.childItems())
            title = next(
                item for item in visual_items
                if item.objectName() == "projectChooserTitle"
            )
            filters = next(
                item for item in visual_items
                if item.objectName() == "projectFilterToggles"
            )
            previews = [
                item for item in visual_items
                if item.objectName() == "projectGridPreview"
                and item.isVisible()
            ]
            title_position = title.mapToItem(scene, QPointF(0, 0))
            filter_position = filters.mapToItem(scene, QPointF(0, 0))
            self.assertLessEqual(
                title_position.y() + title.height(),
                filter_position.y() + 0.1,
            )
            self.assertEqual(len(previews), 3)
            for preview in previews:
                position = preview.mapToItem(scene, QPointF(0, 0))
                self.assertAlmostEqual(preview.width(), preview.height())
                self.assertGreaterEqual(position.x(), -0.1)
                self.assertLessEqual(position.x() + preview.width(), 540.1)
            image = owner.grabWindow()
            self.assertFalse(image.isNull())
            self.assertEqual((image.width(), image.height()), (540, 700))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()
