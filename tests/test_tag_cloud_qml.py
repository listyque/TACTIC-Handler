"""Cached tag catalog -> real Search button -> rendered popup, without TACTIC."""

import json
import os
import statistics
import sys
import time
import unittest
from unittest.mock import patch
import shiboken6

from tests import test_process_menu_latency as menus
from tests.test_tag_catalog import _DeferredPool, _SearchType

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QInputMethodEvent, QMouseEvent, QWheelEvent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_inst
from thlib.ui.localization import CatalogTranslator


class TagCloudQmlTests(unittest.TestCase):
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
        # Reuse the real, isolated Search workspace and its font/controller
        # bindings; no parallel simplified tag-controller implementation.
        self.workspace = menus.ProcessMenuLatencyTests()
        self.workspace.setUp()
        self.addCleanup(self.workspace.doCleanups)
        self.controller = self.workspace.controller
        self.controller._active_stype = lambda: _SearchType()
        self.cache_times = []
        read_cache = self.controller._cached_tag_catalog

        def measured_cache(key):
            started = time.perf_counter()
            result = read_cache(key)
            self.cache_times.append((time.perf_counter() - started) * 1000)
            return result

        self.enterContext(patch.object(self.controller, "_cached_tag_catalog", measured_cache))
        self.set_catalog(1000)

    def set_catalog(self, count):
        labels = ("trees", "Characters", "very-long-production-tag-name", "шарики", "water")
        self.records = [{
            "tag": f"{labels[index % len(labels)]}-{index:04d}",
            "weight": 1 - index / max(1, count), "count": count - index,
            "column": "keywords",
        } for index in range(count)]
        key = self.controller._tag_catalog_cache_key("demo", "demo/asset", "keywords")
        self.controller._tag_catalog_cache[key] = {
            "records": self.records, "loadedAt": time.time(),
        }

    def chips(self, popup):
        return [item for item in menus.visual_items(popup.property("contentItem"))
                if item.objectName() == "tagCloudChip"]

    def visible_chips(self, popup):
        view = popup.findChild(QQuickItem, "scrollablePopupViewport")
        return [chip for chip in self.chips(popup) if chip.isVisible()
                and 0 <= chip.mapToItem(view, QPointF()).y()
                and chip.mapToItem(view, QPointF()).y() + chip.height() <= view.height() + .5]

    def live_window(self, window):
        # Qt's private QQuickPopupWindow can receive a new Python wrapper
        # after QML's Window attached property was read. Match the live native
        # window instead of retaining that invalidated borrowed wrapper.
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

    def click(self, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(item.window(), Qt.LeftButton, Qt.NoModifier, point)
        self.settle(item.window())

    def wheel(self, view, angle):
        position = view.mapToScene(QPointF(view.width() / 2, view.height() / 2))
        QTest.mouseMove(view.window(), position.toPoint())
        stopped = QSignalSpy(view.movementEnded)
        event = QWheelEvent(
            position, view.window().mapToGlobal(position), QPoint(), QPoint(0, angle),
            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
        )
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        self.app.sendEvent(view.window(), event)
        if view.property("moving"):
            self.assertTrue(stopped.wait(2000))
        self.settle(view.window())

    def measure_open(self, window, view):
        button = view.findChild(QQuickItem, "searchTagButton")
        button.findChild(QObject, "compactIconButtonCursorArea").setProperty("lastActivationAt", -1000.)
        popup = view.findChild(QObject, "searchTagCloudPopup")
        popup.setProperty("sameSourceToggleWindow", 0)
        position = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        probe = menus._PopupFrameProbe(
            popup.findChild(QObject, "tagCloudRows"), window, popup.property("usePopupWindow"),
        )
        self.app.installEventFilter(probe)
        guard = QTimer()
        guard.setSingleShot(True)
        guard.timeout.connect(probe.loop.quit)
        opened = QSignalSpy(popup.opened)
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
            self.assertIsNotNone(probe.dispatch_ms, "Tag button did not handle input")
            self.assertIsNotNone(probe.content_frame, "Tag popup did not render content")
            if not popup.property("opened"):
                self.assertTrue(opened.wait(1000))
        finally:
            guard.stop()
            self.app.removeEventFilter(probe)
            probe.detach()
        return popup, {
            "cacheMs": round(self.cache_times[-1], 3),
            "dispatchMs": round(probe.dispatch_ms, 3),
            "contentFrameMs": round(probe.content_frame, 3),
            "chipsCreated": len(self.chips(popup)),
        }

    def test_cached_tags_create_only_viewport_chips(self):
        for width in (360, 1400):
            with self.subTest(width=width), self.workspace.scene(width, animated=False) as (window, view):
                popup, sample = self.measure_open(window, view)
                self.assertGreater(sample["chipsCreated"], 0)
                self.assertLess(sample["chipsCreated"], 80, sample)
                self.assertEqual(self.controller._tag_workers, {})
                self.assertTrue(popup.property("opened"))
                self.assertEqual(popup.property("scale"), 1)
                self.assertEqual(popup.property("opacity"), 1)
                self.workspace.close_menu(popup)

    def test_search_filters_cached_tags_without_changing_selection(self):
        for width in (360, 1400):
            with self.subTest(width=width), self.workspace.scene(width, animated=False) as (window, view):
                popup, _sample = self.measure_open(window, view)
                field = popup.findChild(QQuickItem, "tagCloudSearchField")
                self.assertIsNotNone(field)
                height = popup.property("height")
                with patch.object(self.controller, "apply_search_filters"):
                    self.controller.toggle_tag(self.records[0]["tag"])
                with patch.object(self.controller, "apply_search_filters") as apply:
                    self.click(field)
                    for character in " WATER-0999 ":
                        QTest.keyClick(self.live_window(field.window()), character)
                    self.settle(field.window())
                    apply.assert_not_called()
                self.assertEqual(
                    [chip.property("text") for chip in self.visible_chips(popup)],
                    ["ALL", self.records[999]["tag"]],
                )
                self.assertEqual(self.controller._current_tab().selected_tags, {self.records[0]["tag"]})
                self.assertEqual(popup.property("height"), height)
                self.assertFalse(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
                with patch.object(self.controller, "apply_search_filters") as apply:
                    self.click(self.visible_chips(popup)[1])
                    apply.assert_called_once()
                self.assertTrue(self.visible_chips(popup)[1].property("checked"))
                with patch.object(self.controller, "apply_search_filters") as apply:
                    self.click(popup.findChild(QQuickItem, "clearTagSearchButton"))
                    apply.assert_not_called()
                self.assertEqual(field.property("text"), "")
                self.assertEqual(set(self.controller._current_tab().selected_tags),
                                 {self.records[0]["tag"], self.records[999]["tag"]})
                self.assertEqual(popup.property("height"), height)
                self.assertTrue(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
                self.assertLess(len(self.chips(popup)), 80)
                self.assertEqual(len(self.cache_times), 1)
                self.assertEqual(self.controller._tag_workers, {})
                with patch.object(self.controller, "apply_search_filters"):
                    self.controller.toggle_tag("")
                self.workspace.close_menu(popup)
                self.cache_times.clear()

    def test_search_empty_state_and_filtered_keyboard_and_touch_navigation(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            field = popup.findChild(QQuickItem, "tagCloudSearchField")
            self.assertTrue(field.hasActiveFocus())
            owner = self.live_window(field.window())
            height = popup.property("height")
            for character in "absent-tag":
                QTest.keyClick(owner, character)
            self.settle(owner)
            self.assertFalse(self.visible_chips(popup))
            self.assertEqual(popup.findChild(QQuickItem, "tagCloudStatusLabel").property("text"),
                             "No matching tags")
            self.assertFalse(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
            QTest.keyClick(owner, Qt.Key_A, Qt.ControlModifier)
            QTest.keyClick(owner, Qt.Key_Backspace)
            commit = QInputMethodEvent()
            commit.setCommitString("ШАРИКИ")
            self.app.sendEvent(field, commit)
            self.settle(owner)
            self.assertTrue(all(chip.property("text") == "ALL"
                                or "шарики" in chip.property("text")
                                for chip in self.visible_chips(popup)))
            QTest.keyClick(owner, Qt.Key_Down)
            self.assertEqual(owner.activeFocusItem().property("text"), self.records[3]["tag"])
            for _ in range(34):
                QTest.keyClick(owner, Qt.Key_Tab)
            self.settle(owner)
            focused = owner.activeFocusItem()
            self.assertEqual(focused.property("text"), self.records[173]["tag"])
            with patch.object(self.controller, "apply_search_filters") as apply:
                QTest.keyClick(owner, Qt.Key_Space)
                self.settle(owner)
                apply.assert_called_once()
            self.assertEqual(self.controller._current_tab().selected_tags, {self.records[173]["tag"]})
            self.assertTrue(focused.property("checked"))
            device = QTest.createTouchDevice()
            position = focused.mapToScene(QPointF(focused.width() / 2, focused.height() / 2)).toPoint()
            with patch.object(self.controller, "apply_search_filters") as apply:
                tap = QTest.touchEvent(owner, device, autoCommit=False)
                tap.press(0, position, owner).commit()
                tap.release(0, position, owner).commit()
                self.settle(owner)
                apply.assert_called_once()
            self.assertFalse(self.controller._current_tab().selected_tags)
            self.assertEqual(popup.property("height"), height)
            self.assertLess(len(self.chips(popup)), 80)
            self.assertEqual(self.controller._tag_workers, {})
            QTest.keyClick(owner, Qt.Key_Escape)
            self.assertFalse(popup.property("visible"))

    def test_search_survives_catalog_refresh_and_resets_on_reopen(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            field = popup.findChild(QQuickItem, "tagCloudSearchField")
            for character in "water":
                QTest.keyClick(self.live_window(field.window()), character)
            self.settle(field.window())
            pool = _DeferredPool()
            with patch.object(env_inst, "server_pool", pool):
                self.click(popup.findChild(QQuickItem, "reloadSearchTagsButton"))
            self.set_catalog(20)
            self.controller._tag_cloud_result((self.records, pool.worker.metadata))
            self.settle(field.window())
            self.assertEqual(field.property("text"), "water")
            self.assertEqual([chip.property("text") for chip in self.chips(popup) if chip.isVisible()],
                             ["ALL"] + [record["tag"] for record in self.records if "water" in record["tag"]])
            self.workspace.close_menu(popup)
            popup, _sample = self.measure_open(window, view)
            self.assertEqual(field.property("text"), "")
            self.assertEqual(self.visible_chips(popup)[1].property("text"), self.records[0]["tag"])
            self.assertTrue(field.hasActiveFocus())
            self.workspace.close_menu(popup)

    def test_scroll_to_last_cached_tag_keeps_extent_and_selection(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            tag_list = popup.findChild(QQuickItem, "scrollablePopupViewport")
            bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
            popup_window = tag_list.window()
            self.assertTrue(bar.isVisible())
            height = tag_list.property("contentHeight")
            self.wheel(tag_list, -1200000)
            self.assertTrue(tag_list.property("atYEnd"))
            last = next(chip for chip in self.visible_chips(popup)
                        if chip.property("text") == self.records[-1]["tag"])
            original_y = tag_list.property("contentY")
            # Keep the production tag -> Advanced Search transformation, only
            # isolate the subsequent query of matching sObjects.
            with patch.object(self.controller, "apply_search_filters") as apply:
                self.click(last)
                apply.assert_called_once()
            self.assertIn(self.records[-1]["tag"], self.controller._current_tab().selected_tags)
            self.assertTrue(last.property("checked"))
            self.assertAlmostEqual(tag_list.property("contentY"), original_y, delta=.5)
            self.assertEqual(tag_list.property("contentHeight"), height)
            self.assertLess(len(self.chips(popup)), 80)
            last.forceActiveFocus()
            QTest.keyClick(self.live_window(last.window()), Qt.Key_Tab)
            self.settle(popup_window)
            self.assertTrue(tag_list.property("atYBeginning"))
            self.wheel(tag_list, -1200000)
            self.wheel(tag_list, 1200000)
            self.assertTrue(tag_list.property("atYBeginning"), {
                key: tag_list.property(key) for key in ("contentY", "contentHeight", "moving", "flicking")
            })
            self.assertEqual(tag_list.property("contentHeight"), height)
            with patch.object(self.controller, "apply_search_filters"):
                self.click(popup.findChild(QQuickItem, "resetSearchTagsButton"))
            self.assertFalse(self.controller._current_tab().selected_tags)
            self.workspace.close_menu(popup)

    def test_scrollbar_drag_navigates_cached_tail_without_gaps_or_requests(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            tag_list = popup.findChild(QQuickItem, "scrollablePopupViewport")
            bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
            owner = bar.window()
            start = bar.mapToScene(QPointF(bar.width() / 2, 6)).toPoint()
            end = bar.mapToScene(QPointF(bar.width() / 2, bar.height() - 3)).toPoint()
            QTest.mousePress(owner, Qt.LeftButton, Qt.NoModifier, start)
            QTest.mouseMove(owner, end)
            QTest.mouseRelease(owner, Qt.LeftButton, Qt.NoModifier, end)
            self.settle(owner)
            self.assertTrue(tag_list.property("atYEnd"))
            self.assertIn(self.records[-1]["tag"], [c.property("text") for c in self.visible_chips(popup)])
            self.assertEqual(len(self.cache_times), 1)
            self.assertEqual(self.controller._tag_workers, {})
            self.workspace.close_menu(popup)

    def test_keyboard_can_cross_virtual_rows_and_touch_selects_once(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            chip = self.visible_chips(popup)[0]
            chip.forceActiveFocus()
            owner = chip.window()
            for _ in range(35):
                QTest.keyClick(owner, Qt.Key_Tab)
            self.settle(owner)
            focused = owner.activeFocusItem()
            self.assertEqual(focused.objectName(), "tagCloudChip")
            tag = focused.property("text")
            self.assertEqual(tag, self.records[34]["tag"])
            with patch.object(self.controller, "apply_search_filters") as apply:
                QTest.keyClick(owner, Qt.Key_Space)
                self.settle(owner)
                apply.assert_called_once()
            self.assertTrue(focused.property("checked"))
            device = QTest.createTouchDevice()
            position = focused.mapToScene(QPointF(focused.width() / 2, focused.height() / 2)).toPoint()
            with patch.object(self.controller, "apply_search_filters") as apply:
                tap = QTest.touchEvent(owner, device, autoCommit=False)
                tap.press(0, position, owner).commit()
                tap.release(0, position, owner).commit()
                self.settle(owner)
                apply.assert_called_once()
            self.assertNotIn(tag, self.controller._current_tab().selected_tags)
            self.workspace.close_menu(popup)

    def test_refresh_keeps_height_and_uses_worker_and_hidden_popup_does_no_layout(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            height = popup.property("height")
            popup_window = popup.property("contentItem").window()
            pool = _DeferredPool()
            with patch.object(env_inst, "server_pool", pool):
                self.click(popup.findChild(QQuickItem, "reloadSearchTagsButton"))
            self.assertTrue(pool.worker.started)
            self.assertTrue(self.controller.tag_cloud_loading)
            self.assertTrue(self.visible_chips(popup))
            self.set_catalog(1)
            self.controller._tag_cloud_result((self.records, pool.worker.metadata))
            self.settle(popup_window)
            self.assertEqual(popup.property("height"), height)
            self.assertFalse(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
            self.assertEqual(len(self.chips(popup)), 2)
            self.workspace.close_menu(popup)
            retained = self.chips(popup)
            self.assertTrue(all(not chip.isVisible() for chip in retained))
            self.controller._tag_records = []
            self.controller.tag_cloud_changed.emit()
            self.settle(window)
            self.assertEqual(self.chips(popup), retained)

    def test_russian_layout_reserves_scrollbar_and_chip_geometry(self):
        translator = CatalogTranslator(menus.QML.parent / "translations/ru.json")
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        with self.workspace.scene(width=360, animated=False, height=400) as (window, view):
            popup, _sample = self.measure_open(window, view)
            tag_list = popup.findChild(QQuickItem, "scrollablePopupViewport")
            bar = popup.findChild(QQuickItem, "scrollablePopupScrollBar")
            content = popup.property("contentItem")
            field = popup.findChild(QQuickItem, "tagCloudSearchField")
            self.assertEqual(field.property("placeholderText"), "Поиск тегов")
            point = field.mapToItem(tag_list, QPointF())
            self.assertGreaterEqual(point.x(), 0)
            self.assertLessEqual(point.x() + field.width(), tag_list.width() - bar.width())
            self.assertLessEqual(point.y() + field.height(), tag_list.height())
            self.assertTrue(bar.isVisible())
            self.assertLessEqual(popup.property("height"), window.height())
            self.assertGreater(len(self.visible_chips(popup)), 2)
            for chip in self.visible_chips(popup):
                point = chip.mapToItem(tag_list, QPointF())
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x() + chip.width(), tag_list.width() - bar.width() + .5)
                self.assertLessEqual(chip.mapToItem(content, QPointF()).y() + chip.height(), content.height())
                self.assertAlmostEqual(chip.width(), min(260, popup.property("rowWidth"), chip.implicitWidth()), delta=1)
            self.assertEqual(self.visible_chips(popup)[0].property("text"), "ВСЕ")
            self.workspace.close_menu(popup)

    def test_reopening_reuses_layout_but_hidden_changes_and_resize_refresh_it(self):
        with self.workspace.scene(animated=False) as (window, view):
            popup, _sample = self.measure_open(window, view)
            geometry = popup.property("rows")
            self.workspace.close_menu(popup)
            popup, _sample = self.measure_open(window, view)
            self.assertTrue(geometry.strictlyEquals(popup.property("rows")))
            self.workspace.close_menu(popup)
            self.set_catalog(20)
            for record in self.records:
                record["tag"] = "Changed " + record["tag"]
            self.controller.tag_cloud_changed.emit()
            self.assertTrue(geometry.strictlyEquals(popup.property("rows")))
            self.assertTrue(all(not chip.isVisible() for chip in self.chips(popup)))
            popup, _sample = self.measure_open(window, view)
            self.assertFalse(geometry.strictlyEquals(popup.property("rows")))
            self.assertEqual(self.visible_chips(popup)[1].property("text"), self.records[0]["tag"])
            geometry = popup.property("rows")
            self.workspace.close_menu(popup)
            view.setWidth(360)
            window.resize(360, window.height())
            self.settle(window)
            popup, _sample = self.measure_open(window, view)
            self.assertFalse(geometry.strictlyEquals(popup.property("rows")))
            self.workspace.close_menu(popup)

    def test_empty_cache_has_no_tag_widgets_and_dismisses_with_escape(self):
        self.set_catalog(0)
        with self.workspace.scene(animated=False) as (window, view):
            self.click(view.findChild(QQuickItem, "searchTagButton"))
            popup = view.findChild(QObject, "searchTagCloudPopup")
            self.assertTrue(popup.property("opened"))
            self.assertFalse(self.chips(popup))
            self.assertEqual(popup.findChild(QQuickItem, "tagCloudStatusLabel").property("text"), "No tags found.")
            self.assertFalse(popup.findChild(QQuickItem, "scrollablePopupScrollBar").isVisible())
            owner = self.live_window(popup.property("contentItem").window())
            QTest.keyClick(owner, Qt.Key_Escape)
            self.assertFalse(popup.property("visible"))


def benchmark():
    from thlib.ui.rendering import apply_render_backend

    apply_render_backend("automatic", environment=os.environ)
    QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
    TagCloudQmlTests.setUpClass()
    for count in (100, 1000):
        test = TagCloudQmlTests()
        test.setUp()
        test.set_catalog(count)
        try:
            with test.workspace.scene() as (window, view):
                samples = []
                for _ in range(4):
                    popup, sample = test.measure_open(window, view)
                    samples.append(sample)
                    test.workspace.close_menu(popup)
                    presented = QSignalSpy(window.frameSwapped)
                    window.update()
                    if not presented.count():
                        test.assertTrue(presented.wait(1000))
                print(json.dumps({
                    "tags": count, "backend": str(window.rendererInterface().graphicsApi()),
                    "style": QQuickStyle.name(), "cold": samples[0],
                    "warmMedian": {key: statistics.median(row[key] for row in samples[1:])
                                   for key in samples[0]},
                }, indent=2))
        finally:
            test.doCleanups()


if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        benchmark()
    else:
        unittest.main()
