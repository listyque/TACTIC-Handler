"""Real modal editor inputs -> controller draft -> widget_config round trip."""

from __future__ import annotations

from copy import deepcopy
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_mode
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.workspace_models.windows import FloatingWindowModel, VisibleFloatingWindowModel
from tests.profile_ui_responsiveness import frame
from tests.test_quick_filter_editor import _Application, _Pool, _RuntimeServer, _Users


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class QuickFilterEditorQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.icon_bindings = qml_icon_bindings(ROOT, cls.app)

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.application = _Application()
        self.application.window_model = FloatingWindowModel({})
        self.controller = QuickFilterEditorController(self.application, _Users())
        self.key = ("demo", "demo/asset", "demo/asset@assets")
        self.controller._loaded[self.key] = {}
        self.controller.begin_session()
        self.server = _RuntimeServer()
        self.enterContext(patch("thlib.tactic_classes.server_start", return_value=self.server))
        runtime = type("Runtime", (), {"server_pool": _Pool()})()
        self.enterContext(patch("thlib.environment.env_inst", runtime))

    def scene(self, width=620, height=520, russian=False):
        if russian:
            translator = CatalogTranslator(QML.parent / "translations/ru.json")
            self.app.installTranslator(translator)
            self.addCleanup(self.app.removeTranslator, translator)
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(QML))
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        for name, value in self.icon_bindings.items():
            self.engine.rootContext().setContextProperty(name, value)
        self.engine.rootContext().setContextProperty("editorController", self.controller)
        self.engine.rootContext().setContextProperty("quickFilterEditorController", self.controller)
        self.windows = self.application.window_model
        self.visible_windows = VisibleFloatingWindowModel(self.windows)
        self.engine.rootContext().setContextProperty("windowModel", self.windows)
        self.engine.rootContext().setContextProperty("visibleWindowModel", self.visible_windows)
        self.component = QQmlComponent(self.engine)
        self.component.setData(b'''
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "." as App

ApplicationWindow {
    id: owner
    width: 1024; height: 900; visible: true
    App.Theme {
        id: theme
        dark: true
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    QtObject {
        id: windowAppearanceController
        function apply(window, dark, background, foreground) {}
    }
    QtObject {
        id: configurationController
        signal closeAllowed()
    }
    App.WindowHost {
        ownerWindow: owner
        theme: theme
        workspaceEnabled: true
    }
}
''', QUrl.fromLocalFile(str(QML / "_QuickFilterEditorLayoutTest.qml")))
        self.owner = self.component.create()
        self.assertIsNotNone(self.owner, "\n".join(e.toString() for e in self.component.errors()))
        self.windows.show_window("quick_filter_editor")
        self.window = next(window for window in self.app.allWindows()
                           if window.property("kind") == "quick_filter_editor")
        self.window.resize(width, height)
        self.window.requestActivate()
        frame(self.window)
        self.addCleanup(self.close_scene)

    def close_scene(self):
        self.window.close()
        self.owner.close()
        self.owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])

    def item(self, name):
        def find(parent):
            if parent.objectName() == name:
                return parent
            for child in parent.childItems():
                found = find(child)
                if found is not None:
                    return found
            return None

        item = find(self.window.contentItem())
        self.assertIsNotNone(item, name)
        return item

    def click(self, name):
        item = self.item(name)
        self.assertTrue(item.isVisible(), name)
        center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=center.toPoint())
        frame(self.window)

    def test_standard_save_reload_and_reopen_through_native_modal_inputs(self):
        self.controller.discard()
        self.controller._groups = []
        self.scene()
        self.assertTrue(self.controller._session_open)
        self.assertEqual(len(self.controller.groups), 1)
        self.assertIs(self.window.transientParent(), self.owner)
        self.assertEqual(self.window.modality(), Qt.WindowModal)
        self.assertEqual(self.item("saveQuickFilterDefaultsButton").property("text"),
                         "Save as defaults on server")
        self.assertEqual(self.item("saveQuickFilterEditorButton").property("text"), "SAVE")
        self.assertTrue(self.item("saveQuickFilterEditorButton").isEnabled())
        self.click("useCurrentQuickFiltersAsStandardButton")
        self.assertEqual(self.controller.standardSelectionCount, 1)
        self.assertEqual(self.server.insert_calls, [])
        self.click("saveQuickFilterDefaultsButton")
        self.assertFalse(self.controller.dirty)
        self.assertFalse(self.controller.error)
        self.controller.apply_server_batch({"cacheChanges": [{
            "searchType": "config/widget_config", "projectCode": "demo",
        }]})
        self.controller.discard()
        self.controller.begin_session()
        self.assertEqual(self.controller._loaded[self.key]["defaultSelections"], {
            "column:category": ["props"],
        })
        self.assertEqual(self.controller.standardSelectionCount, 1)
        self.assertEqual(len(self.server.insert_calls), 1)
        saved = self.server.insert_calls[0][1]
        self.assertEqual(saved["login"], "")
        self.assertEqual(saved["search_type"], "demo/asset")
        self.assertIn("server for all users", self.application.notifications[-1])

    def test_chip_selection_stays_visible_and_group_checkbox_still_hides(self):
        self.scene()
        option_name = "quickFilterOption:column:category:props"
        self.click(option_name)
        self.assertTrue(self.item(option_name).isVisible())
        self.assertFalse(self.item(option_name).property("checked"))
        self.assertEqual(self.controller.standardSelectionCount, 0)
        option = self.item(option_name)
        option.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertTrue(self.item(option_name).property("checked"))
        self.assertEqual(self.controller.standardSelectionCount, 1)
        option = self.item(option_name)
        center = option.mapToScene(QPointF(option.width() / 2, option.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(self.window, device).press(0, center, self.window).commit()
        QTest.touchEvent(self.window, device).release(0, center, self.window).commit()
        frame(self.window)
        self.assertTrue(self.item(option_name).isVisible())
        self.assertFalse(self.item(option_name).property("checked"))
        self.assertEqual(self.controller.standardSelectionCount, 0)
        self.click("quickFilterGroupToggle:column:category")
        self.assertFalse(self.item("quickFilterGroup:column:category").isVisible())
        self.click("showHiddenQuickFilters")
        toggle = self.item("quickFilterGroupToggle:column:category")
        center = toggle.mapToScene(QPointF(toggle.width() / 2, toggle.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(self.window, device).press(0, center, self.window).commit()
        QTest.touchEvent(self.window, device).release(0, center, self.window).commit()
        frame(self.window)
        self.assertTrue(self.controller.groups[0]["enabled"])

    def test_selecting_a_chip_updates_both_saves_and_reopens_selected(self):
        self.scene()
        name = "quickFilterOption:column:category:characters"
        self.assertFalse(self.item(name).property("checked"))
        self.click(name)
        self.assertTrue(self.item(name).isVisible())
        self.assertTrue(self.item(name).property("checked"))
        self.assertEqual(self.controller.standardSelectionCount, 2)
        self.click("saveQuickFilterEditorButton")
        saved = self.application.local_saves[-1][1]
        self.assertEqual(saved["defaultSelections"]["column:category"], ["characters", "props"])
        self.assertNotIn("options", saved["groups"][0])
        self.click("saveQuickFilterDefaultsButton")
        record = self.server.records[0]
        self.assertEqual(self.controller._configuration_from_xml(record["config"], record["view"]), saved)
        self.controller.discard()
        self.controller.begin_session()
        frame(self.window)
        self.assertTrue(self.item(name).isVisible())
        self.assertTrue(self.item(name).property("checked"))

    def test_individual_starting_filter_removal_is_saved_and_can_be_cleared(self):
        self.application.context["selections"] = {
            "column:category": ["props", "characters"],
        }
        self.scene()
        self.click("useCurrentQuickFiltersAsStandardButton")
        self.click("saveQuickFilterDefaultsButton")
        self.click("removeStandardFilter:column:category:props")
        self.assertEqual(self.controller.standardSelectionCount, 1)
        self.click("saveQuickFilterDefaultsButton")
        self.click("saveQuickFilterEditorButton")
        self.controller.discard()
        self.controller.begin_session()
        self.assertEqual(self.controller._standard_selections, {
            "column:category": ["characters"],
        })
        self.click("removeStandardFilter:column:category:characters")
        self.assertEqual(self.controller.standardSelectionCount, 0)
        self.click("saveQuickFilterDefaultsButton")
        record = self.server.records[0]
        saved = self.controller._configuration_from_xml(record["config"], record["view"])
        self.assertEqual(saved["defaultSelections"], {})

    def test_hidden_group_survives_save_poll_and_reopen(self):
        self.scene()
        self.click("useCurrentQuickFiltersAsStandardButton")
        self.click("quickFilterGroupToggle:column:category")
        self.assertEqual(self.controller.standardSelectionCount, 0)
        self.click("saveQuickFilterDefaultsButton")
        self.controller.apply_server_batch({"cacheChanges": [{
            "searchType": "config/widget_config", "projectCode": "demo",
        }]})
        self.controller.discard()
        self.controller.begin_session()
        frame(self.window)
        self.assertFalse(self.item("quickFilterGroup:column:category").isVisible())
        self.assertFalse(self.controller.groups[0]["enabled"])
        self.assertFalse(self.controller.dirty)

    def test_russian_narrow_and_wide_scroll_and_footer_layout(self):
        groups = []
        for index in range(12):
            groups.append({
                "key": f"column:field{index}", "title": f"Server field {index}",
                "enabled": True, "options": [{
                    "key": f"value{value}", "title": "Long server label " * 3 + str(value),
                    "enabled": True,
                } for value in range(3)],
            })
        self.application.catalog_groups = deepcopy(groups)
        self.application.context["groups"] = groups
        self.controller._rebuild(self.controller._context())
        self.scene(russian=True)
        self.assertEqual(self.item("saveQuickFilterDefaultsButton").property("text"),
                         "Сохранить как дефолты на сервере")
        for width, height in [(620, 520), (1000, 800)]:
            self.window.resize(width, height)
            frame(self.window)
            flick = self.item("quickFilterEditorScroll")
            content = self.item("quickFilterEditorContent")
            bar = self.item("quickFilterEditorScrollBar")
            self.assertGreater(flick.property("contentHeight"), flick.height())
            self.assertTrue(bar.isVisible())
            self.assertLessEqual(content.width() + 8, flick.width() - bar.property("reservedExtent"))
            for name in ("saveQuickFilterEditorButton", "saveQuickFilterDefaultsButton", "cancelQuickFilterEditorButton"):
                button = self.item(name)
                top = button.mapToScene(QPointF())
                self.assertGreaterEqual(top.x(), 0)
                self.assertGreaterEqual(top.y(), 0)
                self.assertLessEqual(top.x() + button.width(), width)
                self.assertLessEqual(top.y() + button.height(), height)
            center = flick.mapToScene(QPointF(flick.width() / 2, flick.height() / 2))
            QTest.mouseMove(self.window, center.toPoint())
            wheel = QWheelEvent(center, self.window.mapToGlobal(center.toPoint()),
                                QPoint(), QPoint(0, -360), Qt.NoButton, Qt.NoModifier,
                                Qt.NoScrollPhase, False)
            wheel.setTimestamp(time.monotonic_ns() // 1_000_000)
            changed = QSignalSpy(flick.contentYChanged)
            QGuiApplication.sendEvent(self.window, wheel)
            if flick.property("contentY") <= 0:
                changed.wait(500)
            self.assertGreater(flick.property("contentY"), 0)
            flick.cancelFlick()
            flick.setProperty("contentY", 0)
            screenshot = os.environ.get("QUICK_FILTER_EDITOR_SCREENSHOT")
            if screenshot:
                path = Path(screenshot)
                path = path.with_stem(path.stem + f"-{width}")
                self.assertTrue(self.window.grabWindow().save(str(path)))

    def test_regular_user_can_edit_and_save_but_cannot_reveal_shared_hidden_values(self):
        configuration = {"groups": [{
            "key": "column:category", "enabled": True, "options": ["props"],
        }], "defaultSelections": {}}
        self.application.apply_quick_filter_configuration("demo/asset", configuration)
        self.controller._users.canManageUsers = False
        self.controller._loaded[self.key] = configuration
        self.controller.begin_session()
        self.scene(russian=True)
        self.assertEqual(self.item("saveQuickFilterEditorButton").property("text"), "СОХРАНИТЬ")
        self.assertFalse(self.item("saveQuickFilterDefaultsButton").isVisible())
        self.click("showHiddenQuickFilters")
        self.assertEqual([option["key"] for option in self.controller.groups[0]["options"]], ["props"])
        self.click("quickFilterGroupToggle:column:category")
        self.click("saveQuickFilterEditorButton")
        self.assertEqual(self.server.insert_calls, [])
        self.assertEqual(len(self.application.local_saves), 1)
        self.controller.discard()
        self.controller.begin_session()
        frame(self.window)
        self.assertFalse(self.item("quickFilterGroupToggle:column:category").property("checked"))
        self.assertEqual(len(self.controller.groups[0]["options"]), 1)

    def test_empty_editor_receives_catalog_while_its_window_stays_open(self):
        groups = deepcopy(self.application.catalog_groups)
        self.application.catalog_groups = []
        self.application.context.update(groups=[], loading=True)
        self.controller.begin_session()
        self.scene()
        self.assertTrue(self.item("quickFilterEditorLoading").isVisible())
        self.assertFalse(self.item("saveQuickFilterEditorButton").isEnabled())
        self.application.context.update(groups=groups, loading=False)
        self.application.quick_filters_changed.emit()
        frame(self.window)
        self.assertFalse(self.item("quickFilterEditorLoading").isVisible())
        self.click("quickFilterOption:column:category:props")
        self.assertTrue(self.controller.dirty)

    def test_native_host_with_application_catalog_displays_editable_rows(self):
        from tests.test_quick_filter_personal_layout import QuickFilterPersonalLayoutTests
        fixture = QuickFilterPersonalLayoutTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.application = fixture.controller
        self.enterContext(patch.object(self.application, "_request_quick_filter_tasks"))
        runtime = self.application._quick_filter_runtime
        runtime.cache[runtime.context_key] = {
            "records": deepcopy(runtime.records),
            "facetColumns": self.application._quick_filters.facet_columns(fixture.tab.stype),
        }
        self.controller = QuickFilterEditorController(self.application, _Users())
        self.scene()
        self.assertTrue(self.controller.groups)
        group = self.item("quickFilterGroupToggle:column:category")
        self.assertTrue(group.isVisible())
        self.assertGreater(group.height(), 20)
        self.assertGreater(group.width(), 100)
        self.click("quickFilterOption:column:category:props")
        self.assertTrue(self.controller.dirty)
        self.click("saveQuickFilterEditorButton")
        self.assertEqual(fixture.tab.quick_filters, {"column:category": {"props"}})
        self.assertTrue(any(record.get("column") == "category" and record.get("value") == "props"
                            for record in fixture.tab.filter_records))

    def test_reopening_retained_native_window_receives_late_catalog(self):
        groups = deepcopy(self.application.catalog_groups)
        self.application.context["groups"] = []
        self.scene()
        button = self.item("cancelQuickFilterEditorButton")
        position = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=position.toPoint())
        self.windows.show_window("quick_filter_editor")
        self.application.context["groups"] = groups
        self.application.quick_filters_changed.emit()
        frame(self.window)
        self.assertTrue(self.controller._session_open)
        self.assertTrue(self.item("quickFilterGroupToggle:column:category").isVisible())


if __name__ == "__main__":
    unittest.main()
