"""Sidebar editing, native icon popup geometry and themed selection."""

import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"))

from PySide6.QtCore import (
    QCoreApplication, QEvent, QObject, QPoint, QPointF, Property, Qt,
    QUrl, Signal,
)
from PySide6.QtGui import QFont, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest
from shiboken6 import isValid

from thlib.environment import env_mode
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator
from thlib.ui.models import NavigationEntry, NavigationModel
from thlib.ui.sidebar_editor import SidebarEditorController
from thlib.ui.workspace_models.windows import FloatingWindowModel, VisibleFloatingWindowModel
from tests.profile_ui_responsiveness import frame
from tests.qt_application import gui_test_application


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"


class _LayoutPresets(QObject):
    stateChanged = Signal()

    @Property("QVariantList", notify=stateChanged)
    def options(self):
        return [
            {"value": "", "label": "Do not change workspace layout"},
            {"value": "workspace_layout@review", "label": "Review"},
        ]

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False


class SidebarEditorQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()
        QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
        cls.app.setFont(QFont("Segoe UI", 10))
        cls.icons = qml_icon_bindings(ROOT, cls.app)

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.application = SimpleNamespace(
            can_administer=True,
            _registry=SimpleNamespace(register=lambda *_: None),
            navigation_model=NavigationModel(),
            window_model=FloatingWindowModel({}),
        )
        self.application.navigation_model.replace([NavigationEntry(
            key="demo/assets@my_tasks", title="My tasks", glyph="box", group="Project",
            command="open_sidebar_item", search_type="demo/assets", accent="#e35062",
        )])
        self.layout_presets = _LayoutPresets()
        self.controller = SidebarEditorController(
            self.application,
            SimpleNamespace(canManageUsers=True),
            layout_presets=self.layout_presets,
        )
        self.controller.begin_session = lambda: None
        self.controller.refresh_search_presets = lambda: None
        stype = SimpleNamespace(
            get_code=lambda: "demo/assets", get_pretty_name=lambda: "Assets",
            get_info=lambda: {"color": "#e35062"},
        )
        project = SimpleNamespace(get_stypes=lambda: {"demo/assets": stype})
        self.controller._loaded(("demo", "Demo", project, [{
            "code": "CONFIG0001", "search_type": "SideBarWdg", "view": "definition",
            "config": """<config><element name="my_tasks" title="My tasks" icon="FAS_BOX">
                <display class="LinkWdg"><layout_preset>workspace_layout@review</layout_preset></display><search_type>demo/assets</search_type>
                </element></config>""",
        }]))
        self.controller.select_entry(0)

    def scene(self, width=900, height=720, dark=True):
        translator = CatalogTranslator(QML.parent / "translations/ru.json")
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        context = self.engine.rootContext()
        for name, value in self.icons.items():
            context.setContextProperty(name, value)
        context.setContextProperty("sidebarEditorController", self.controller)
        context.setContextProperty("sidebarEntryModel", self.controller.entries)
        context.setContextProperty("sidebarSecurityGroupModel", self.controller.security_groups)
        context.setContextProperty("windowModel", self.application.window_model)
        self.component = QQmlComponent(self.engine)
        self.component.setData(b'''
import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    id: window
    width: 900; height: 720; visible: true
    property bool darkTheme: true
    App.Theme {
        id: theme; objectName: "testTheme"
        dark: window.darkTheme
        accentColor: "#bc7598"
        clickAnimationsEnabled: false; hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false; popupAnimationsEnabled: false
    }
    App.SidebarEditorView { anchors.fill: parent; theme: theme }
    App.NavigationDrawer {
        objectName: "testDrawer"
        theme: theme; model: []; sidebarEditingAvailable: true
    }
}
''', QUrl.fromLocalFile(str(QML / "_SidebarEditorTest.qml")))
        self.window = self.component.create()
        self.assertIsNotNone(self.window, "\n".join(e.toString() for e in self.component.errors()))
        self.addCleanup(self.close_scene)
        self.window.setProperty("darkTheme", dark)
        self.window.resize(width, height)
        self.window.requestActivate()
        frame(self.window)

    def close_scene(self):
        host = getattr(self, "native_host", None)
        if host is not None and isValid(host):
            host.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        if isValid(self.window):
            self.window.close()
            self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])

    @staticmethod
    def descendants(item):
        yield item
        for child in item.childItems():
            yield from SidebarEditorQmlTests.descendants(child)

    def item(self, name, window=None):
        return next(item for item in self.descendants((window or self.window).contentItem())
                    if item.objectName() == name)

    def click(self, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)

    def test_form_pages_and_actions_fit_narrow_and_wide_windows(self):
        self.scene(860, 600)
        help_button = self.item("sidebarEditorHelpButton")
        self.click(help_button)
        self.assertEqual(
            self.application.window_model.helpTopic, "sidebar_editor"
        )
        for width, height in ((860, 600), (1300, 900)):
            self.window.resize(width, height)
            frame(self.window)
            for page in ("item", "access", "technical"):
                self.click(self.item("segmentedButtonSegment_" + page))
                viewport = self.item("sidebarSettingsViewport")
                self.assertGreater(viewport.width(), 300)
                self.assertGreater(viewport.height(), 250)
                for item in self.descendants(viewport):
                    if not item.isVisible():
                        continue
                    kind = item.metaObject().className()
                    if kind.startswith(("Button_QML", "ComboBox_QML", "TextField_QML")):
                        point = item.mapToItem(viewport, QPointF(0, 0))
                        self.assertGreaterEqual(point.x(), 0, kind)
                        self.assertLessEqual(point.x() + item.width(), viewport.width() - 12, kind)
                save = self.item("sidebarSaveButton")
                bottom = save.mapToScene(QPointF(0, save.height())).y()
                self.assertLessEqual(bottom, height)
            self.click(self.item("segmentedButtonSegment_item"))
            target = os.environ.get("SIDEBAR_EDITOR_SCREENSHOT")
            if target:
                self.window.grabWindow().save(str(Path(target).with_stem(
                    Path(target).stem + "-" + str(width))))

    def test_title_edit_preserves_identity_and_enables_save(self):
        self.scene()
        field = self.item("sidebarTitleField")
        self.click(field)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for key in "Ready assets":
            QTest.keyClick(self.window, key)
        self.assertEqual(self.controller.selectedEntry["title"], "Ready assets")
        self.assertEqual(self.controller.selectedEntry["name"], "my_tasks")
        self.assertTrue(self.item("sidebarSaveButton").isEnabled())
        self.assertFalse(self.item("sidebarSearchSetupButton").isEnabled())

    def test_preset_dropdown_keeps_rows_inside_viewport_and_reserves_scrollbar(self):
        self.controller._replace_search_preset_options([
            {"view": "query_%s" % i, "title": "Saved search %s" % i}
            for i in range(20)
        ])
        self.scene()
        viewport = self.item("sidebarSettingsViewport")
        combo = self.item("sidebarSearchPreset")
        viewport.setProperty("contentY", 230)
        frame(self.window)
        popup = next(obj for obj in combo.findChildren(QObject)
                     if obj.metaObject().className().startswith("Popup_QML"))
        opened = QSignalSpy(popup.opened)
        self.click(combo)
        if not popup.property("opened"):
            self.assertTrue(opened.wait(1000))
        self.assertTrue(popup.property("opened"))
        options = combo.findChild(QQuickItem, "comboBoxPopupList")
        frame(self.window)
        self.assertGreater(options.height(), 100)
        self.assertLessEqual(popup.property("height"), 304)
        for row in self.descendants(options):
            if row.metaObject().className().startswith("ItemDelegate"):
                self.assertLessEqual(row.width(), options.width() - 12)
        from PySide6.QtCore import QMetaObject
        QMetaObject.invokeMethod(popup, "close")

    def test_workspace_layout_preset_is_visible_and_assignable(self):
        self.scene()
        viewport = self.item("sidebarSettingsViewport")
        viewport.setProperty("contentY", 300)
        frame(self.window)
        combo = self.item("sidebarLayoutPreset")

        self.assertEqual(
            combo.property("currentValue"), "workspace_layout@review",
        )
        combo.setProperty("currentIndex", 0)
        combo.activated.emit(0)

        self.assertEqual(
            self.controller.selectedEntry["layoutPreset"], "",
        )

    def test_access_list_uses_available_height_and_opens_group_manager(self):
        self.controller.security_groups.replace([
            {'code': 'G%s' % i, 'label': 'Group %s' % i, 'allowed': False}
            for i in range(50)
        ])
        self.scene(1300, 900)
        self.click(self.item('segmentedButtonSegment_access'))
        groups = self.item('sidebarAccessGroups')
        for width, height in ((1300, 900), (860, 600)):
            self.window.resize(width, height)
            frame(self.window)
            viewport = self.item('sidebarSettingsViewport')
            self.assertLessEqual(viewport.property('contentHeight'), viewport.height() + 1)
            # Native Windows clamps a requested 900-DIP window to the screen
            # at high DPI. Check the actual remaining height, not the request.
            bottom = groups.mapToItem(viewport, QPointF(0, groups.height())).y()
            self.assertGreaterEqual(bottom, viewport.height() - 24)
            self.assertGreater(groups.height(), 120)
            if self.window.height() >= 850:
                self.assertGreater(groups.height(), 400)
        self.click(self.item('manageSidebarGroups'))
        model = self.application.window_model
        self.assertTrue(next(window for window in model._windows
                             if window.window_id == 'administration').visible)

    def test_sidebar_selection_uses_theme_but_keeps_server_item_color(self):
        self.scene()
        theme = self.window.findChild(QObject, "testTheme")
        surface = self.item("sidebarRowSurface")
        title = self.item("sidebarRowTitle")
        row = next(item for item in self.descendants(self.window.contentItem())
                   if item.metaObject().className().startswith("SidebarTreeRow"))
        colors = []
        for dark in (True, False):
            self.window.setProperty("darkTheme", dark)
            frame(self.window)
            self.assertEqual(surface.property("color"), theme.property("contentSelection"))
            self.assertEqual(title.property("color"), theme.property("contentSelectionText"))
            self.assertEqual(row.property("accent"), "#e35062")
            colors.append(surface.property("color"))
        self.assertNotEqual(colors[0], colors[1])
        row.forceActiveFocus()
        self.assertEqual(QQmlProperty.read(surface, "border.width"), 1)
        QTest.keyClick(self.window, Qt.Key_Space)
        self.assertEqual(self.controller.selectedEntry["name"], "my_tasks")

    def test_drawer_edit_button_uses_pencil_and_accepts_touch(self):
        self.scene()
        drawer = self.item("testDrawer")
        drawer.setProperty("opened", True)
        frame(self.window)
        spy = QSignalSpy(drawer.editSidebarRequested)
        button = self.item("editSidebarButton")
        self.assertEqual(button.property("iconName"), "edit")
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
        QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
        frame(self.window)
        self.assertEqual(spy.count(), 1)
        self.assertFalse(drawer.property("opened"))

    def test_drawer_unconfigured_links_explain_disabled_state_and_never_activate(self):
        from tests.test_sidebar_navigation_targets import sidebar_entries, sidebar_project, SEARCH_KEY

        self.scene(640, 600)
        drawer = self.item("testDrawer")
        model = NavigationModel(sidebar_entries(sidebar_project()))
        model.setParent(self.window)
        drawer.setProperty("model", model)
        selected = QSignalSpy(drawer.selected)
        device = QTest.createTouchDevice()
        for width in (640, 1200):
            self.window.resize(width, 600)
            drawer.setProperty("opened", True)
            frame(self.window)
            rows = [item for item in self.descendants(drawer)
                    if item.metaObject().className().startswith("SidebarTreeRow")]
            unconfigured = next(row for row in rows if row.property("title") == 'Column Manager')
            search = next(row for row in rows if row.property("title") == 'Naming')
            before = selected.count()
            self.assertTrue(unconfigured.property('dimmed'))
            self.assertFalse(unconfigured.property('interactive'))
            self.assertFalse(unconfigured.property('activeFocusOnTab'))
            description = QQmlProperty(
                unconfigured, 'Accessible.description', QQmlEngine.contextForObject(unconfigured),
            ).read()
            self.assertIn('серч-тайп', description)
            self.click(unconfigured)
            unconfigured.forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            QTest.keyClick(self.window, Qt.Key_Return)
            point = unconfigured.mapToScene(QPointF(
                unconfigured.width() / 2, unconfigured.height() / 2)).toPoint()
            QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
            QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
            frame(self.window)
            self.assertEqual(selected.count(), before)
            self.assertTrue(drawer.property('opened'))
            self.assertTrue(search.property('interactive'))
            if width == 640:
                self.click(search)
            else:
                search.forceActiveFocus()
                QTest.keyClick(self.window, Qt.Key_Space)
                frame(self.window)
            self.assertEqual(selected.count(), before + 1)
            self.assertEqual(selected.at(before), [SEARCH_KEY, 'Naming', 'open_sidebar_item'])
            self.assertFalse(drawer.property('opened'))

    def test_native_window_host_starts_one_editor_session_on_each_open(self):
        self.scene()
        del self.controller.begin_session
        reloads = []
        self.controller.reload = lambda: reloads.append(True)
        self.windows = self.application.window_model
        self.visible_windows = VisibleFloatingWindowModel(self.windows)
        context = self.engine.rootContext()
        context.setContextProperty("windowModel", self.windows)
        context.setContextProperty("visibleWindowModel", self.visible_windows)
        component = QQmlComponent(self.engine)
        component.setData(b'''
import QtQuick
import "." as App
Item {
    id: root
    required property var owner
    required property var theme
    QtObject {
        id: windowAppearanceController
        function apply(window, dark, background, foreground) {}
    }
    QtObject { id: configurationController; signal closeAllowed() }
    App.WindowHost {
        ownerWindow: root.owner
        theme: root.theme
        workspaceEnabled: true
    }
}
''', QUrl.fromLocalFile(str(QML / "_SidebarHostTest.qml")))
        host = component.createWithInitialProperties({
            "owner": self.window, "theme": self.window.findChild(QObject, "testTheme"),
        })
        self.assertIsNotNone(host, [error.toString() for error in component.errors()])
        host.setParent(self.window)
        host.setParentItem(self.window.contentItem())
        self.native_host = host
        self.windows.show_window("sidebar_editor")
        native = next(window for window in self.app.allWindows()
                      if window.property("kind") == "sidebar_editor")
        frame(native)
        self.assertEqual(reloads, [True])
        self.assertEqual(native.modality(), Qt.WindowModal)
        self.assertIs(native.transientParent(), self.window)
        self.windows.close_window("sidebar_editor")
        self.windows.show_window("sidebar_editor")
        frame(native)
        self.assertEqual(reloads, [True, True])
        self.windows.close_window("sidebar_editor")

    def test_add_separator_uses_its_own_icon_and_can_be_selected(self):
        self.scene()
        button = self.item("sidebarAddSeparatorButton")
        self.assertEqual(button.property("iconName"), "sidebar-separator")
        self.click(button)
        self.assertEqual(self.controller.selectedEntry["entryType"], "separator")
        separator = next(item for item in self.descendants(self.window.contentItem())
                         if item.metaObject().className().startswith("SidebarTreeRow")
                         and item.property("rowType") == "separator")
        self.controller.select_entry(0)
        self.click(separator)
        self.assertEqual(self.controller.selectedEntry["entryType"], "separator")

    def test_scroll_to_search_actions_and_open_exact_sidebar_filters(self):
        events = []
        self.application.navigation_model.replace([NavigationEntry(
            key="demo/assets@my_tasks", title="My tasks", glyph="box", group="Project",
            command="open_sidebar_item", search_type="demo/assets",
        )])
        self.application.current_project_code = "demo"
        self.application.current_section_key = "another_tab"
        from thlib.ui.workspace_models.records import RecordListModel
        self.application.workspace_state = SimpleNamespace(
            result_surfaces_model=RecordListModel(("current", "resultModel")),
        )
        self.application._create_section = lambda key, *_: events.append(("create", key))
        self.application.window_model = SimpleNamespace(
            close_window=lambda key: events.append(("close", key)),
            show_window=lambda key: events.append(("show", key)),
            show_child_window=lambda key, parent: events.append(("show", key, parent)),
        )

        def activate(key):
            self.application.current_section_key = key

        self.application.activate_section = activate
        self.scene(860, 600)
        viewport = self.item("sidebarSettingsViewport")
        point = viewport.mapToScene(QPointF(viewport.width() / 2, viewport.height() / 2))
        QTest.mouseMove(self.window, point.toPoint())
        stopped = QSignalSpy(viewport.movementEnded)
        event = QWheelEvent(point, QPointF(self.window.mapToGlobal(point.toPoint())),
                            QPoint(), QPoint(0, -12000), Qt.NoButton, Qt.NoModifier,
                            Qt.NoScrollPhase, False)
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        QCoreApplication.sendEvent(self.window, event)
        if viewport.property("moving"):
            self.assertTrue(stopped.wait(2000))
        frame(self.window)
        self.assertGreater(viewport.property("contentY"), 0)
        button = self.item("sidebarSearchSetupButton")
        position = button.mapToItem(viewport, QPointF(0, 0))
        self.assertGreaterEqual(position.y(), 0)
        self.assertLessEqual(position.y() + button.height(), viewport.height())
        self.click(button)
        self.assertEqual(events, [
            ("create", "demo/assets@my_tasks"),
            ("show", "sidebar_search_preview", "sidebar_editor"),
        ])

    def test_icon_picker_has_grid_width_and_scrollbar_gutter(self):
        self.scene()
        picker = next(item for item in self.descendants(self.window.contentItem())
                      if item.metaObject().className().startswith("IconPickerButton"))
        button = next(item for item in picker.childItems()
                      if item.metaObject().className().startswith("CompactIconButton"))
        self.click(button)
        popup_window = next(window for window in self.app.allWindows()
                            if window is not self.window and window.isVisible())
        grid = next(item for item in self.descendants(popup_window.contentItem())
                    if item.metaObject().className().startswith("QQuickGridView"))
        set_selector = self.item("iconLibrarySetSelector", popup_window)
        self.assertFalse(set_selector.isVisible())
        self.assertGreaterEqual(grid.width(), 400, {
            "grid": grid.width(), "popup": popup_window.width(),
            "requested": picker.property("popupWidth"),
            "owner": self.window.width(),
            "popups": [
                {key: obj.property(key) for key in (
                    "width", "availableScreenWidth", "maximumAvailableWidth", "x", "y", "scale"
                )} for obj in picker.findChildren(QObject)
                if obj.metaObject().className().startswith("Popup_QML")
            ],
        })
        self.assertGreaterEqual(grid.property("rightMargin"), 12)
        self.assertGreater(grid.property("contentHeight"), grid.height())
        search = self.item("sidebarIconSearch", popup_window)
        point = search.mapToScene(QPointF(search.width() / 2, search.height() / 2))
        QTest.mouseClick(popup_window, Qt.LeftButton, pos=point.toPoint())
        for key in "camera":
            QTest.keyClick(popup_window, key)
        frame(self.window)
        self.assertGreaterEqual(grid.width(), 400)
        self.assertLess(grid.property("count"), 20)
        camera = next(item for item in self.descendants(grid)
                      if item.property("modelData") == "camera")
        point = camera.mapToScene(QPointF(camera.width() / 2, camera.height() / 2))
        QTest.mouseClick(popup_window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)
        self.assertEqual(self.controller.selectedEntry["icon"], "FAS_CAMERA")
        self.assertEqual(self.controller.selectedEntry["glyph"], "camera")


if __name__ == "__main__":
    unittest.main()
