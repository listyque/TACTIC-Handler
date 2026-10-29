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

from thlib import tactic_classes as tc
from thlib.environment import env_mode
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator
from thlib.ui.models import NavigationEntry, NavigationModel
from thlib.ui.sidebar_editor import SidebarEditorController
from thlib.ui.workspace_models.windows import FloatingWindowModel
from tests.profile_ui_responsiveness import frame
from tests.qt_application import gui_test_application, run_native_windows_test


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
        }, {
            "code": "CONFIG0002", "search_type": "SideBarWdg",
            "view": "tactic_handler",
            "config": "<config><element name='my_tasks'/></config>",
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
        for width, height in ((860, 600), (1300, 900)):
            self.window.resize(width, height)
            frame(self.window)
            for page in ("item", "access", "technical"):
                self.click(self.item("sidebarPages_" + page))
                viewport = self.item("sidebarAccessGroups" if page == "access" else "sidebarSettingsViewport")
                self.assertGreater(viewport.width(), 300)
                self.assertGreater(viewport.height(), 150 if page == "access" else 250)
                for item in self.descendants(viewport):
                    if not item.isVisible():
                        continue
                    kind = item.metaObject().className()
                    if kind.startswith(("Button_QML", "ComboBox_QML", "TextField_QML")):
                        point = item.mapToItem(viewport, QPointF(0, 0))
                        self.assertGreaterEqual(point.x(), 0, kind)
                        self.assertLessEqual(point.x() + item.width(), viewport.width() - 12, kind)
                save = self.item("adminSaveDocument")
                bottom = save.mapToScene(QPointF(0, save.height())).y()
                self.assertLessEqual(bottom, height)
            self.click(self.item("sidebarPages_item"))
            target = os.environ.get("SIDEBAR_EDITOR_SCREENSHOT")
            if target:
                self.window.grabWindow().save(str(Path(target).with_stem(
                    Path(target).stem + "-" + str(width))))

    def test_tree_text_keeps_gap_from_icons_and_folder_toggles(self):
        self.controller.add_entry('section')
        self.controller.update_selected('title', 'Episodes')
        self.controller.add_entry('link')
        self.controller.update_selected('title', 'Ready to Sound')
        self.controller.update_selected('searchType', 'demo/assets')
        self.scene()
        self.assertTrue(any(row['depth'] > 0 for row in self.controller.entryRecords))
        for width in (860, 1300):
            self.window.resize(width, 720)
            frame(self.window)
            for row in self.controller.entryRecords:
                if not row['entryVisible']:
                    continue
                icon = self.item('sidebarEntryIcon_' + str(row['index']))
                right = icon.mapToScene(QPointF(icon.width(), 0)).x()
                title = self.item('sidebarEntryTitle_' + str(row['index']))
                self.assertGreaterEqual(title.mapToScene(QPointF()).x() - right, 12)
                if row['searchType']:
                    detail = self.item('sidebarEntryType_' + str(row['index']))
                    self.assertEqual(detail.mapToScene(QPointF()).x(), title.mapToScene(QPointF()).x())
                if row['entryType'] == 'section':
                    toggle = self.item('sidebarEntryToggle_' + str(row['index']))
                    self.assertLessEqual(title.mapToScene(QPointF(title.width(), 0)).x(), toggle.mapToScene(QPointF()).x() - 8)

    def test_title_edit_preserves_identity_and_enables_save(self):
        self.scene()
        field = self.item("sidebarTitleField")
        self.click(field)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for key in "Ready assets":
            QTest.keyClick(self.window, key)
        self.assertTrue(self.controller.dirty)
        self.assertEqual(field.property("text"), "Ready assets")
        self.click(self.item("sidebarPages_technical"))
        self.assertEqual(self.controller.selectedEntry["title"], "Ready assets")
        self.assertEqual(self.controller.selectedEntry["name"], "my_tasks")
        self.assertTrue(self.item("adminSaveDocument").isEnabled())
        self.click(self.item("sidebarPages_item"))
        self.assertFalse(self.item("sidebarSearchSetupButton").isEnabled())

    def test_unapplied_invalid_xml_is_dirty_and_survives_mode_change_until_discard(self):
        self.scene()
        self.click(self.item('sidebarModeSelector_xml'))
        area = self.item('sidebarXml')
        self.window.requestActivate()
        area.focusEditor()
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in '<element name="broken">':
            QTest.keyClick(self.window, character)
            frame(self.window)
        self.assertTrue(self.controller.dirty)
        self.click(self.item('sidebarModeSelector_simple'))
        self.assertTrue(self.controller.error)
        self.assertIsNotNone(self.item('sidebarXml'))
        self.assertEqual(self.controller.selectedEntry['name'], 'my_tasks')
        self.click(self.item('adminDiscardDocument'))
        self.click(self.item('adminConfirmSave'))
        self.assertFalse(self.controller.dirty)
        self.assertEqual(self.controller.error, '')
        self.assertIsNotNone(self.item('sidebarTitleField'))

    def test_source_switch_and_group_preview_use_the_live_tree(self):
        class Group:
            @staticmethod
            def get_info():
                return {
                    "access_rules": (
                        "<rules><rule group='link' element='my_tasks' "
                        "access='allow' project='demo'/></rules>"
                    )
                }

            @staticmethod
            def get_login_group():
                return "animator"

            @staticmethod
            def get_pretty_name():
                return "Animators"

        self.controller._security_objects = {"animator": Group()}
        self.controller._rebuild_entries()
        self.scene()

        self.click(self.item("sidebarSourceSelector_tactic"))
        self.assertEqual(self.controller.sidebarSource, "tactic")
        self.click(self.item("sidebarSourceSelector_handler"))
        self.assertEqual(self.controller.sidebarSource, "handler")

        preview = self.item("sidebarGroupPreview")
        self.assertGreaterEqual(preview.width(), 220)
        preview.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(self.window, Qt.Key_Down)
        frame(self.window)
        self.assertEqual(self.controller.previewGroup, "animator")
        self.assertEqual(self.controller.visibleEntryCount, 1)

    def test_hidden_entry_stays_dimmed_and_editable_in_group_preview(self):
        class Group:
            @staticmethod
            def get_info():
                return {
                    "access_rules": (
                        "<rules><rule group='link' element='my_tasks' "
                        "access='allow' project='demo'/></rules>"
                    )
                }

            @staticmethod
            def get_login_group():
                return "animator"

            @staticmethod
            def get_pretty_name():
                return "Animators"

        self.controller._security_objects = {"animator": Group()}
        self.controller.set_preview_group("animator")
        self.scene()

        check = self.item("sidebarEntryVisibleCheck")
        viewport = self.item("sidebarSettingsViewport")
        viewport.setProperty("contentY", check.mapToItem(viewport, QPointF()).y() - 12)
        frame(self.window)
        self.click(check)

        row = self.item("sidebarEditorEntry_0")
        self.assertTrue(row.isVisible())
        opacity = 1
        parent = row
        while parent:
            opacity *= parent.opacity()
            parent = parent.parentItem()
        self.assertFalse(self.controller.selectedEntry["isVisible"])
        self.assertEqual(opacity, 0.5)
        self.assertFalse(self.controller.selectedEntry["isVisible"])

    def test_preset_dropdown_keeps_rows_inside_viewport_and_reserves_scrollbar(self):
        # Offscreen's first native popup loses focus during activation. Exercise
        # Popup.Window on Windows, isolated from other suites' Qt global state.
        if run_native_windows_test(self):
            return

        self.controller._replace_search_preset_options([
            {"view": "query_%s" % i, "title": "Saved search %s" % i}
            for i in range(20)
        ])
        self.scene()
        viewport = self.item("sidebarSettingsViewport")
        combo = self.item("sidebarSearchPreset")
        viewport.setProperty("contentY", combo.mapToItem(viewport, QPointF()).y() + viewport.property("contentY") - 12)
        frame(self.window)
        popup = combo.findChild(QObject, "comboBoxPopup")
        self.assertIsNotNone(popup)
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

    def test_access_list_uses_available_height_and_requests_group_section(self):
        self.controller.security_groups.replace([
            {'code': 'G%s' % i, 'label': 'Group %s' % i, 'allowed': False}
            for i in range(50)
        ])
        self.scene(1300, 900)
        self.click(self.item('sidebarPages_access'))
        groups = self.item('sidebarAccessGroups')
        for width, height in ((1300, 900), (860, 600)):
            self.window.resize(width, height)
            frame(self.window)
            viewport = groups.parentItem().parentItem()
            # Native Windows clamps a requested 900-DIP window to the screen
            # at high DPI. Check the actual remaining height, not the request.
            bottom = groups.mapToItem(viewport, QPointF(0, groups.height())).y()
            self.assertGreaterEqual(bottom, viewport.height() - 24)
            self.assertGreater(groups.height(), 120)
            if self.window.height() >= 850:
                self.assertGreater(groups.height(), 360)
        requested = QSignalSpy(self.controller.groupManagementRequested)
        self.click(self.item('manageSidebarGroups'))
        self.assertEqual(requested.count(), 1)

    def test_sidebar_selection_uses_theme_but_keeps_server_item_color(self):
        self.scene()
        theme = self.window.findChild(QObject, "testTheme")
        row = self.item("sidebarEditorEntry_0")
        surface = next(item for item in self.descendants(row) if item.metaObject().className().startswith("ItemSurface"))
        title = self.item("sidebarEntryTitle_0")
        colors = []
        for dark in (True, False):
            self.window.setProperty("darkTheme", dark)
            frame(self.window)
            self.assertEqual(surface.property("baseColor"), theme.property("contentSelection"))
            self.assertEqual(title.property("color"), theme.property("primaryText"))
            self.assertEqual(self.item("sidebarEntryIcon_0").property("accent").name(), "#e35062")
            colors.append(surface.property("baseColor"))
        self.assertNotEqual(colors[0], colors[1])
        row.forceActiveFocus()
        self.assertTrue(row.hasActiveFocus())
        QTest.keyClick(self.window, Qt.Key_Space)
        self.assertEqual(self.controller.selectedEntry["name"], "my_tasks")

    def test_drawer_edit_button_uses_pencil_and_accepts_touch(self):
        self.scene()
        drawer = self.item("testDrawer")
        drawer.open()
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
            drawer.open()
            frame(self.window)
            rows = [item for item in self.descendants(drawer)
                    if item.property("rowType") is not None and item.isVisible()]
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
                self.window.requestActivate()
                search.forceActiveFocus()
                frame(self.window)
                self.assertTrue(search.hasActiveFocus())
                QTest.keyClick(self.window, Qt.Key_Space)
                frame(self.window)
            self.assertEqual(selected.count(), before + 1)
            self.assertEqual(selected.at(before), [SEARCH_KEY, 'Naming', 'open_sidebar_item'])
            self.assertFalse(drawer.property('opened'))

    def test_builtin_catalog_links_render_and_open_without_sidebar_widget(self):
        project = tc.Project({'code': 'admin', 'name': 'Admin'})
        project.get_all_search_types([{
            'code': 'admin/item', 'title': 'Admin Items', 'color': '#e35062',
            'table_name': 'item', 'column_info': {},
        }], [], '', [])
        login = SimpleNamespace(check_security=lambda **_: 'allow')
        self.scene(640, 600)
        drawer = self.item('testDrawer')
        model = NavigationModel(NavigationModel.build_project_entries(project, login))
        model.setParent(self.window)
        drawer.setProperty('model', model)
        selected = QSignalSpy(drawer.selected)

        for width in (640, 1200):
            self.window.resize(width, 600)
            drawer.open()
            frame(self.window)
            row = next(item for item in self.descendants(drawer)
                       if item.property("rowType") is not None and item.isVisible()
                       and item.property('title') == 'Admin Items')
            self.assertTrue(row.property('interactive'))
            if width == 640:
                self.click(row)
            else:
                row.forceActiveFocus()
                QTest.keyClick(self.window, Qt.Key_Return)
                frame(self.window)
            self.assertEqual(selected.at(selected.count() - 1), [
                'admin/item@admin/item', 'Admin Items', 'open_sidebar_item',
            ])
            self.assertFalse(drawer.property('opened'))

    def test_add_separator_uses_its_own_icon_and_can_be_selected(self):
        self.scene()
        button = self.item("sidebarAdd_separator")
        self.assertEqual(QQmlProperty.read(button, "icon.name"), "sidebar-separator")
        self.click(button)
        self.assertEqual(self.controller.selectedEntry["entryType"], "separator")
        separator = self.item("sidebarEditorEntry_" + str(self.controller.selectedRow))
        row_id = separator.objectName()
        self.controller.select_entry(0)
        frame(self.window)
        self.click(self.item(row_id))
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
        preset = self.item("sidebarSearchPreset")
        position = button.mapToItem(viewport, QPointF(0, 0))
        viewport.setProperty(
            "contentY",
            max(0, viewport.property("contentY") + position.y() - 12),
        )
        frame(self.window)
        position = button.mapToItem(viewport, QPointF(0, 0))
        self.assertGreaterEqual(position.y(), 0)
        self.assertLessEqual(position.y() + button.height(), viewport.height())
        self.click(button)
        self.assertEqual(events, [
            ("create", "demo/assets@my_tasks"),
            ("show", "sidebar_search_preview", "administration"),
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
