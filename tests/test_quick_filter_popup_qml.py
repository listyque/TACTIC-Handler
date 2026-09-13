"""Cached quick facets -> real Search button -> first populated popup frame."""

import json
import os
import statistics
import sys
import time
import unittest
from unittest.mock import patch
import shiboken6

from tests import test_process_menu_latency as menus
from tests.test_quick_filters import _Record, _Stype

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtQml import qmlContext
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.localization import CatalogTranslator
from thlib.ui.quick_filters import QuickFilterCatalog


class _FacetType(_Stype):
    def get_code(self):
        return "demo/asset"

    def get_columns_info(self):
        return {f"facet{index}": {"data_type": "varchar"} for index in range(5)}


class QuickFilterPopupQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_text_render_type = QQuickWindow.textRenderType()
        QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
        menus.ProcessMenuLatencyTests.setUpClass()
        cls.app = menus.ProcessMenuLatencyTests.app

    @classmethod
    def tearDownClass(cls):
        QQuickWindow.setTextRenderType(cls.previous_text_render_type)

    def setUp(self):
        self.workspace = menus.ProcessMenuLatencyTests()
        self.workspace.setUp()
        self.addCleanup(self.workspace.doCleanups)
        self.controller = self.workspace.controller
        self.controller._active_stype = lambda: _FacetType()
        self.groups_times = []
        self.cache_times = []
        groups = self.controller._quick_filters.groups
        cache = self.controller._cached_quick_filter_catalog

        def measured_groups(*args, **kwargs):
            started = time.perf_counter()
            result = groups(*args, **kwargs)
            self.groups_times.append((time.perf_counter() - started) * 1000)
            return result

        def measured_cache(key):
            started = time.perf_counter()
            result = cache(key)
            self.cache_times.append((time.perf_counter() - started) * 1000)
            return result

        self.enterContext(patch.object(self.controller._quick_filters, "groups", measured_groups))
        self.enterContext(patch.object(self.controller, "_cached_quick_filter_catalog", measured_cache))
        self.set_catalog(60)

    def set_catalog(self, count):
        self.records = [{
            "key": f"column:facet{group}", "column": f"facet{group}",
            "title": f"Категория {group}", "source": "column", "accent": "#28a96b",
            "options": [{
                "key": f"value-{index}", "title": f"Вариант {index}", "count": 1,
                "accent": "#28a96b", "showAccentMarker": False,
            } for index in range(group, count, 5)],
        } for group in range(5)]
        key = self.controller._quick_filter_catalog_cache_key("demo", "demo/asset")
        self.controller._quick_filter_runtime.cache[key] = {
            "loadedAt": time.time(), "records": self.records,
            "facetColumns": self.controller._quick_filters.facet_columns(_FacetType()),
        }

    def set_loaded_objects(self, count):
        tab = self.controller._current_tab()
        tab.sobjects = [_Record(f"ASSET{index:04d}") for index in range(count)]
        tab.quick_filter_tasks = {
            record.get_code(): [{"process": process, "status": "Assigned", "assigned": "artist"}
                                for process in ("publish", "storyboard")]
            for record in tab.sobjects
        }
        tab.quick_filter_task_codes = set(tab.quick_filter_tasks)
        tab.quick_filter_task_loaded_at = time.monotonic()

    def chips(self, popup):
        return [item for item in menus.visual_items(popup.property("contentItem"))
                if item.objectName() == "quickFilterOption"]

    def live_window(self, window):
        if not shiboken6.isValid(window):
            address = shiboken6.getCppPointer(window)[0]
            window = next(item for item in self.app.allWindows()
                          if shiboken6.isValid(item) and shiboken6.getCppPointer(item)[0] == address)
        return window

    def settle(self, window):
        window = self.live_window(window)
        presented = QSignalSpy(window.frameSwapped)
        window.update()
        if not presented.count():
            self.assertTrue(presented.wait(1000))

    def visible_chips(self, popup):
        viewport = popup.property("contentItem")
        return [chip for chip in self.chips(popup) if chip.isVisible()
                and 0 <= chip.mapToItem(viewport, QPointF()).y()
                and chip.mapToItem(viewport, QPointF()).y() + chip.height() <= viewport.height() + .5]

    def click(self, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(item.window(), Qt.LeftButton, Qt.NoModifier, point)
        self.settle(item.window())

    def wheel(self, viewport, angle):
        position = viewport.mapToScene(QPointF(viewport.width() / 2, viewport.height() / 2))
        QTest.mouseMove(viewport.window(), position.toPoint())
        stopped = QSignalSpy(viewport.movementEnded)
        event = QWheelEvent(
            position, viewport.window().mapToGlobal(position), QPoint(), QPoint(0, angle),
            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
        )
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        self.app.sendEvent(viewport.window(), event)
        if viewport.property("moving"):
            self.assertTrue(stopped.wait(2000))
        self.settle(viewport.window())

    def measure_open(self, window, view):
        editor = qmlContext(view).contextProperty("quickFilterEditorController")
        editor._context_key = ("demo", "demo/asset", "demo/asset")
        editor._loaded[editor._context_key] = {}
        button = view.findChild(QQuickItem, "searchQuickFilterButton")
        button.findChild(QObject, "compactIconButtonCursorArea").setProperty("lastActivationAt", -1000.)
        popup = view.findChild(QObject, "searchQuickFilterPopup")
        popup.setProperty("sameSourceToggleWindow", -1)
        position = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        probe = menus._PopupFrameProbe(
            popup.findChild(QObject, "quickFilterGroups"), window, popup.property("usePopupWindow"),
        )
        self.app.installEventFilter(probe)
        guard = QTimer()
        guard.setSingleShot(True)
        guard.timeout.connect(probe.loop.quit)
        opened = QSignalSpy(popup.opened)
        self.groups_times.clear()
        try:
            for kind, buttons in (
                (QEvent.MouseButtonPress, Qt.LeftButton),
                (QEvent.MouseButtonRelease, Qt.NoButton),
            ):
                QCoreApplication.postEvent(window, QMouseEvent(
                    kind, position, window.mapToGlobal(position), Qt.LeftButton, buttons, Qt.NoModifier,
                ))
            QCoreApplication.postEvent(probe, QEvent(QEvent.User))
            guard.start(5000)
            probe.loop.exec()
            self.assertIsNotNone(probe.dispatch_ms, "Quick-filter button did not handle input")
            self.assertIsNotNone(probe.content_frame, "Quick filters did not render content")
            ready_on_frame = popup.property("opened")
            if not ready_on_frame:
                self.assertTrue(opened.wait(1000))
            ready_ms = (time.perf_counter() - probe.activated) * 1000
        finally:
            guard.stop()
            self.app.removeEventFilter(probe)
            probe.detach()
        return popup, {
            "cacheMs": round(sum(self.cache_times[-1:]), 3),
            "groupsMs": round(sum(self.groups_times), 3),
            "groupReads": len(self.groups_times),
            "dispatchMs": round(probe.dispatch_ms, 3),
            "contentFrameMs": round(probe.content_frame, 3),
            "readyMs": round(ready_ms, 3), "readyOnFrame": ready_on_frame,
            "chipsCreated": len(self.chips(popup)),
        }

    def test_cached_popup_is_ready_on_first_content_frame(self):
        self.set_catalog(320)
        for width in (360, 1400):
            with self.subTest(width=width), self.workspace.scene(width, animated=True) as (window, view):
                popup, sample = self.measure_open(window, view)
                self.assertTrue(sample["readyOnFrame"], sample)
                self.assertEqual(popup.property("opacity"), 1)
                self.assertEqual(popup.property("scale"), 1)
                self.assertLess(sample["chipsCreated"], 40)
                self.assertEqual(self.controller._quick_filter_runtime.workers, {})
                self.workspace.close_menu(popup)

    def test_reopen_keeps_existing_chips_and_ignores_hidden_updates(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            chip = next(item for item in self.chips(popup) if item.property("text") == "Вариант 0")
            self.workspace.close_menu(popup)
            self.groups_times.clear()
            self.controller.quick_filters_changed.emit()
            self.assertEqual(self.groups_times, [])
            popup, _sample = self.measure_open(window, view)
            self.assertIn(chip, self.chips(popup))
            self.workspace.close_menu(popup)

    def test_selection_updates_advanced_search_without_recreating_visible_chips(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            chip = next(item for item in self.visible_chips(popup) if item.property("text") == "Вариант 0")
            viewport = popup.property("contentItem")
            extent = viewport.property("contentHeight")
            with patch.object(self.controller, "_load_tab") as query:
                self.click(chip)
                query.assert_called_once()
            tab = self.controller._current_tab()
            self.assertEqual(tab.quick_filters, {"column:facet0": {"value-0"}})
            self.assertTrue(any(record.get("column") == "facet0" for record in tab.filter_records))
            self.assertIn(chip, self.chips(popup))
            self.assertTrue(chip.property("checked"))
            self.assertEqual(viewport.property("contentHeight"), extent)
            with patch.object(self.controller, "_load_tab") as query:
                self.click(popup.findChild(QQuickItem, "resetSearchQuickFiltersButton"))
                query.assert_called_once()
            self.assertFalse(tab.quick_filters)
            self.assertFalse(chip.property("checked"))
            self.workspace.close_menu(popup)

    def test_text_facets_are_clickable_local_filters_not_shared_edits(self):
        stype = _FacetType()
        stype.get_columns_info = lambda: {
            "duration": {"data_type": "text"},
            "storyboard": {"data_type": "text"},
        }
        self.controller._active_stype = lambda: stype
        tab = self.controller._current_tab()
        tab.stype = stype
        columns = QuickFilterCatalog.facet_columns(stype)
        records = QuickFilterCatalog.discover_facets(stype, [
            {"duration": "1 Minute", "storyboard": "(No Storyboard)"},
            {"duration": "2 Minutes", "storyboard": None},
        ])
        key = self.controller._quick_filter_catalog_cache_key("demo", "demo/asset")
        self.controller._quick_filter_runtime.cache[key] = {
            "records": records, "facetColumns": columns,
        }
        with self.workspace.scene(animated=False) as (window, view):
            editor = qmlContext(view).contextProperty("quickFilterEditorController")
            with patch.object(editor, "save") as save:
                popup, _sample = self.measure_open(window, view)
                self.assertEqual(popup.findChild(QQuickItem, "editQuickFiltersButton").property("text"), "Edit")
                self.assertIsNone(popup.findChild(QQuickItem, "personalQuickFilterScope"))
                for text in ("2 Minutes", "(No Storyboard)"):
                    chip = next(item for item in self.visible_chips(popup) if item.property("text") == text)
                    with patch.object(self.controller, "_load_tab") as query:
                        self.click(chip)
                        query.assert_called_once()
                    self.assertTrue(chip.property("checked"))
                save.assert_not_called()
                self.assertFalse(editor.dirty)
            self.assertEqual(tab.quick_filters, {
                "column:duration": {"2 Minutes"},
                "column:storyboard": {"(No Storyboard)"},
            })
            self.assertTrue(tab.quick_filter_personalized)
            self.assertEqual(
                [(record["column"], record["relation"], record["value"])
                 for record in tab.filter_records if record.get("generatedFilterKind")],
                [("duration", "=", "2 Minutes"), ("storyboard", "=", "(No Storyboard)")],
            )
            self.assertFalse(self.controller._quick_filters.configuration("demo/asset"))
            self.workspace.close_menu(popup)

    def test_scroll_and_thumb_reach_users_without_changing_extent(self):
        self.set_catalog(320)
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            viewport = popup.property("contentItem")
            bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
            extent = viewport.property("contentHeight")
            self.wheel(viewport, -120000)
            self.assertTrue(viewport.property("atYEnd"))
            self.assertIn("SELECT USERS", [chip.property("text") for chip in self.visible_chips(popup)])
            self.assertLess(len(self.chips(popup)), 40)
            self.assertEqual(viewport.property("contentHeight"), extent)
            self.wheel(viewport, 120000)
            self.assertTrue(viewport.property("atYBeginning"))
            start = bar.mapToScene(QPointF(bar.width() / 2, 6)).toPoint()
            end = bar.mapToScene(QPointF(bar.width() / 2, bar.height() - 3)).toPoint()
            owner = bar.window()
            QTest.mousePress(owner, Qt.LeftButton, Qt.NoModifier, start)
            QTest.mouseMove(owner, end)
            QTest.mouseRelease(owner, Qt.LeftButton, Qt.NoModifier, end)
            self.settle(owner)
            self.assertTrue(viewport.property("atYEnd"))
            self.assertEqual(viewport.property("contentHeight"), extent)
            self.assertEqual(len(self.cache_times), 1)
            self.workspace.close_menu(popup)

    def test_keyboard_crosses_groups_and_touch_toggles_once(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            first = self.visible_chips(popup)[0]
            first.forceActiveFocus()
            owner = first.window()
            # Each field has ALL and twelve options: cross two field groups.
            for _ in range(30):
                QTest.keyClick(self.live_window(owner), Qt.Key_Tab)
            self.settle(owner)
            focused = self.live_window(owner).activeFocusItem()
            self.assertEqual(focused.objectName(), "quickFilterOption")
            self.assertEqual(focused.property("text"), "Вариант 17")
            with patch.object(self.controller, "_load_tab") as query:
                QTest.keyClick(self.live_window(owner), Qt.Key_Space)
                self.settle(owner)
                query.assert_called_once()
            self.assertTrue(focused.property("checked"))
            device = QTest.createTouchDevice()
            position = focused.mapToScene(QPointF(focused.width() / 2, focused.height() / 2)).toPoint()
            with patch.object(self.controller, "_load_tab") as query:
                owner = self.live_window(owner)
                tap = QTest.touchEvent(owner, device, autoCommit=False)
                tap.press(0, position, owner).commit()
                tap.release(0, position, owner).commit()
                self.settle(owner)
                query.assert_called_once()
            self.assertFalse(self.controller._current_tab().quick_filters)
            QTest.keyClick(self.live_window(owner), Qt.Key_Escape)
            self.assertFalse(popup.property("visible"))

    def test_hidden_catalog_changes_and_narrow_russian_layout(self):
        translator = CatalogTranslator(menus.QML.parent / "translations/ru.json")
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        with self.workspace.scene(width=1400, animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            old_chips = self.chips(popup)
            self.workspace.close_menu(popup)
            self.set_catalog(10)
            self.records[0]["options"][0]["title"] = "Очень длинное название настроенного на сервере фильтра"
            self.groups_times.clear()
            self.controller.quick_filters_changed.emit()
            self.assertFalse(self.groups_times)
            self.assertEqual(self.chips(popup), old_chips)
            view.setWidth(360)
            window.resize(360, 400)
            self.settle(window)
            popup, _sample = self.measure_open(window, view)
            viewport = popup.property("contentItem")
            bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
            self.assertTrue(bar.isVisible())
            self.assertLessEqual(popup.property("height"), window.height())
            for chip in self.visible_chips(popup):
                point = chip.mapToItem(viewport, QPointF())
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x() + chip.width(), viewport.width() - bar.width())
                self.assertAlmostEqual(chip.width(), min(popup.property("rowWidth"), chip.implicitWidth()), delta=1)
            self.assertEqual(self.visible_chips(popup)[0].property("text"), "ВСЕ")
            self.workspace.close_menu(popup)

    def test_edit_entry_fits_narrow_russian_popup_for_regular_user(self):
        translator = CatalogTranslator(menus.QML.parent / "translations/ru.json")
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        with self.workspace.scene(width=900, animated=False) as (window, view):
            editor = qmlContext(view).contextProperty("quickFilterEditorController")
            editor._users = type("Artist", (), {"canManageUsers": False})()
            editor.stateChanged.emit()
            for width in (900, 360):
                window.resize(width, 550)
                view.setWidth(width)
                self.settle(window)
                popup, _sample = self.measure_open(window, view)
                viewport = popup.property("contentItem")
                bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
                self.assertIsNone(popup.findChild(QQuickItem, "personalQuickFilterExplanation"))
                for name in ("editQuickFiltersButton",):
                    item = popup.findChild(QQuickItem, name)
                    self.assertTrue(item.isVisible())
                    point = item.mapToItem(viewport, QPointF())
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertLessEqual(point.x() + item.width(), viewport.width() - bar.width())
                    self.assertLessEqual(point.y() + item.height(), viewport.height())
                button = popup.findChild(QQuickItem, "editQuickFiltersButton")
                self.assertEqual(button.property("text"), "Редактировать")
                if width == 360:
                    screenshot = os.environ.get("QUICK_FILTER_POPUP_SCREENSHOT")
                    if screenshot:
                        self.assertTrue(self.live_window(button.window()).grabWindow().save(screenshot))
                    requested = QSignalSpy(popup.editRequested)
                    position = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
                    QTest.mouseClick(button.window(), Qt.LeftButton, pos=position)
                    self.settle(window)
                    self.assertEqual(requested.count(), 1)
                    self.assertFalse(popup.property("visible"))
                else:
                    self.workspace.close_menu(popup)

    def test_cached_task_facets_do_not_request_tasks_again(self):
        self.set_loaded_objects(300)
        with self.workspace.scene(animated=False) as (window, view):
            popup, sample = self.measure_open(window, view)
            self.assertEqual(sample["groupReads"], 1)
            self.assertLess(sample["chipsCreated"], 40)
            self.workspace.close_menu(popup)

    def test_shared_policy_can_hide_groups_in_open_popup(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            configuration = {"groups": [
                {"key": group["key"], "enabled": False}
                for group in self.controller.quick_filter_groups
            ], "defaultSelections": {}}
            self.controller._quick_filters.set_configuration("demo/asset", configuration)
            self.controller.quick_filters_changed.emit()
            self.settle(popup.property("contentItem").window())
            self.assertEqual(popup.findChild(QObject, "quickFilterGroups").property("count"), 0)
            self.assertFalse(self.chips(popup))
            self.assertFalse(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
            self.workspace.close_menu(popup)

    def test_keyboard_wraps_and_user_picker_stays_on_existing_route(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            first = self.visible_chips(popup)[0]
            first.forceActiveFocus()
            owner = first.window()
            QTest.keyClick(self.live_window(owner), Qt.Key_Backtab)
            self.settle(owner)
            focused = self.live_window(owner).activeFocusItem()
            self.assertEqual(focused.property("text"), "Edit")
            QTest.keyClick(self.live_window(owner), Qt.Key_Tab)
            self.settle(owner)
            self.assertEqual(self.live_window(owner).activeFocusItem().property("text"), "ALL")
            self.assertTrue(popup.property("contentItem").property("atYBeginning"))
            self.wheel(popup.property("contentItem"), -120000)
            users = next(chip for chip in self.visible_chips(popup) if chip.property("text") == "SELECT USERS")
            requested = QSignalSpy(popup.assigneesRequested)
            picker = view.findChild(QObject, "searchAssigneeFilterPopup")
            opened = QSignalSpy(picker.opened)
            position = users.mapToScene(QPointF(users.width() / 2, users.height() / 2)).toPoint()
            QTest.mouseClick(users.window(), Qt.LeftButton, Qt.NoModifier, position)
            if not picker.property("opened"):
                self.assertTrue(opened.wait(1000))
            self.assertEqual(requested.count(), 1)
            self.assertFalse(popup.property("visible"))
            self.assertTrue(picker.property("visible"))
            self.workspace.close_menu(picker)


def benchmark():
    QuickFilterPopupQmlTests.setUpClass()
    try:
        for count, loaded in ((60, 0), (320, 0), (60, 300)):
            case = QuickFilterPopupQmlTests()
            case.setUp()
            try:
                case.set_catalog(count)
                case.set_loaded_objects(loaded)
                with case.workspace.scene(animated=True) as (window, view):
                    samples = []
                    for _ in range(4):
                        popup, sample = case.measure_open(window, view)
                        samples.append(sample)
                        case.workspace.close_menu(popup)
                    print(json.dumps({
                        "options": count, "loadedObjects": loaded,
                        "cold": samples[0], "warmMedian": {
                            key: statistics.median(row[key] for row in samples[1:])
                            for key in samples[0]
                        },
                    }, ensure_ascii=False), flush=True)
            finally:
                case.doCleanups()
    finally:
        QuickFilterPopupQmlTests.tearDownClass()


if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        benchmark()
    else:
        unittest.main()
