"""Real feed input and queued controller completion, without a live server."""

from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ["WINDIR"]) / "Fonts"))

from PySide6.QtCore import (
    QCoreApplication, QEvent, QObject, QPoint, QPointF, Signal, Qt, QTimer,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib import environment
from thlib.ui.communication_feed import ActivityFeedController
from tests import test_activity_feed_qml as activity_feed_qml
from tests import test_search_pagination_qml as search_pagination_qml
from tests.test_topbar_activity import _Application


class _Worker(QObject):
    result = Signal(object)
    error = Signal(object)

    def __init__(self, function, args):
        super().__init__()
        self.function = function
        self.args = args
        self.cancelled = False

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True


class _Pool:
    is_stopped = False

    def __init__(self):
        self.workers = []

    def add_task(self, function, *args):
        worker = _Worker(function, args)
        self.workers.append(worker)
        return worker


def _page(offset, count, day="2026-08-22"):
    return {"records": [
        activity_feed_qml._activity_record(
            f"event-{index}", day, "Artist", f"Shot {index}"
        )
        for index in range(offset, offset + count)
    ]}


class ActivityFeedLoadingTests(unittest.TestCase):
    _create_view = activity_feed_qml.ActivityFeedQmlTests._create_view
    _visual_item = staticmethod(
        activity_feed_qml.ActivityFeedQmlTests._visual_item
    )
    wait_frame = search_pagination_qml.SearchPaginationQmlTests.wait_frame

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(environment.env_mode, "current_path", directory))
        self.pool = _Pool()
        self.enterContext(patch.object(environment.env_inst, "server_pool", self.pool))
        self.warnings = []
        previous = qInstallMessageHandler(
            lambda _kind, _context, message: self.warnings.append(message)
        )
        self.addCleanup(qInstallMessageHandler, previous)

    @contextmanager
    def scene(self, animated=False, width=640, height=520):
        application = _Application()
        controller = ActivityFeedController(application)
        objects = self._create_view(controller, controller.model)
        engine, _, _, theme, _, _, _, _, view = objects
        theme.setProperty("fadeAnimationsEnabled", animated)
        theme.setProperty("clickAnimationsEnabled", animated)
        theme.setProperty("hoverAnimationsEnabled", animated)
        window = QQuickWindow()
        window.resize(width, height)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        controller.set_visible(True)
        try:
            feed = view.findChild(QQuickItem, "activityFeedList")
            self.wait_frame(window)
            yield controller, view, feed, window
            self.assertEqual(self.warnings, [])
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()

    def wheel(self, feed, window, *, pixels=0, angle=-12000):
        position = feed.mapToScene(QPointF(feed.width() / 2, feed.height() / 2))
        QTest.mouseMove(window, position.toPoint())
        event = QWheelEvent(
            position, QPointF(window.mapToGlobal(position.toPoint())),
            QPoint(0, pixels), QPoint(0, 0 if pixels else angle),
            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
        )
        self.app.sendEvent(window, event)

    def complete(self, window, payload, worker=None):
        worker = worker or self.pool.workers[-1]
        worker.result.emit(payload)
        self.app.processEvents()
        self.wait_frame(window)
        self.wait_frame(window)

    def test_wheel_pages_until_exhausted_without_resetting_position(self):
        for animated in (False, True):
            with self.subTest(animated=animated), self.scene(animated) as (
                controller, _view, feed, window,
            ):
                self.complete(window, _page(0, 26))
                self.assertEqual(controller.model.count(), 25)
                for offset in (25, 50):
                    requests = len(self.pool.workers)
                    self.wheel(feed, window)
                    self.wait_frame(window, lambda: controller.busy)
                    self.assertEqual(len(self.pool.workers), requests + 1)
                    self.assertEqual(self.pool.workers[-1].args[2], offset)
                    self.wait_frame(
                        window, lambda: not feed.property("interactionMoving"),
                    )
                    position = feed.property("contentY")
                    self.complete(window, _page(offset, 26 if offset == 25 else 5))
                    self.assertGreaterEqual(feed.property("contentY"), position - 1)
                self.assertFalse(controller.hasMore)
                requests = len(self.pool.workers)
                self.wheel(feed, window)
                self.wait_frame(window, lambda: not feed.property("interactionMoving"))
                self.assertEqual(len(self.pool.workers), requests)
                self.assertEqual(controller.model.count(), 55)

    def test_overlapping_pages_merge_by_event_identity(self):
        with self.scene() as (controller, _view, _feed, window):
            self.complete(window, _page(0, 26))
            controller.load_more()
            self.assertTrue(controller.busy)
            self.assertEqual(self.pool.workers[-1].args[2], 25)

            # A new server event can shift the offset window while the user
            # scrolls, leaving the last retained event at the next boundary.
            self.complete(window, _page(24, 26))

            event_ids = [
                record["eventId"] for record in controller.model.records()
            ]
            self.assertEqual(len(event_ids), 49)
            self.assertEqual(len(event_ids), len(set(event_ids)))
            self.assertEqual(controller._offset, 50)
            self.assertTrue(controller.hasMore)

    def test_live_checkin_reloads_enriched_feed_without_raw_cards(self):
        with self.scene() as (controller, _view, _feed, window):
            self.complete(window, _page(0, 26))
            original_ids = [
                record["eventId"] for record in controller.model.records()
            ]

            controller.apply_server_batch({
                "activity": [
                    {
                        "__kind__": "publication",
                        "code": "SNAPSHOT001",
                        "search_code": "ASSET001",
                        "timestamp": "2026-08-29 12:00:00",
                    },
                    {
                        "__kind__": "change",
                        "code": "CHANGE001",
                        "search_type": "sthpw/change_timestamp",
                        "search_code": "ASSET001",
                        "timestamp": "2026-08-29 12:00:00",
                    },
                ],
            })

            self.assertEqual(len(self.pool.workers), 2)
            self.assertTrue(controller.busy)
            self.assertTrue(self.pool.workers[-1].args[9])
            self.assertEqual(
                [record["eventId"] for record in controller.model.records()],
                original_ids,
            )

            enriched = activity_feed_qml._activity_record(
                "publication:SNAPSHOT001",
                "2026-08-29",
                "Artist",
                "Bathroom",
            )
            enriched.update({
                "itemTitle": "bathroom_render_v003.exr",
                "process": "render",
                "context": "render/final",
                "version": "3",
            })
            self.complete(window, {"records": [enriched]})

            self.assertEqual(controller.model.count(), 1)
            record = controller.model.get(0)
            self.assertEqual(record["eventId"], "publication:SNAPSHOT001")
            self.assertEqual(record["targetTitle"], "Bathroom")
            self.assertEqual(record["itemTitle"], "bathroom_render_v003.exr")
            self.assertNotEqual(record["detail"], "Object updated")
            self.assertFalse(controller._live_refresh_pending)

    def test_live_activity_waits_for_visible_idle_feed_and_coalesces(self):
        with self.scene() as (controller, _view, _feed, window):
            controller.apply_server_batch({
                "activity": [{
                    "__kind__": "publication",
                    "code": "SNAPSHOT001",
                    "timestamp": "2026-08-29 12:00:00",
                }],
            })
            controller.apply_server_batch({
                "activity": [{
                    "__kind__": "change",
                    "code": "CHANGE001",
                    "timestamp": "2026-08-29 12:00:01",
                }],
            })
            self.assertEqual(len(self.pool.workers), 1)
            self.assertTrue(controller._live_refresh_pending)

            self.complete(window, _page(0, 26))
            self.assertEqual(len(self.pool.workers), 2)
            self.assertTrue(self.pool.workers[-1].args[9])
            self.assertFalse(controller._live_refresh_pending)

            controller.set_visible(False)
            self.complete(window, _page(0, 1))
            controller.apply_server_batch({
                "activity": [{
                    "__kind__": "note",
                    "code": "NOTE001",
                    "timestamp": "2026-08-29 12:00:02",
                }],
            })
            self.assertEqual(len(self.pool.workers), 2)
            self.assertTrue(controller._live_refresh_pending)

            controller.set_visible(True)
            self.assertEqual(len(self.pool.workers), 3)
            self.assertTrue(self.pool.workers[-1].args[9])

    def test_wheel_at_existing_end_loads_without_at_y_end_transition(self):
        with self.scene() as (controller, _view, feed, window):
            self.complete(window, _page(0, 26))
            feed.setProperty("contentY", feed.property("maximumContentY"))
            self.wait_frame(window)
            self.assertTrue(feed.property("atYEnd"))
            self.assertFalse(controller.busy)
            self.wheel(feed, window, pixels=-60)
            self.wait_frame(window, lambda: controller.busy)
            self.assertEqual(self.pool.workers[-1].args[2], 25)

    def test_underfilled_filtered_pages_continue_after_busy_clears(self):
        with self.scene() as (controller, _view, _feed, window):
            controller.set_search_text("needle")
            self.complete(window, _page(0, 26))
            self.wait_frame(window, lambda: len(self.pool.workers) == 2)
            self.assertEqual(controller.model.count(), 0)
            self.assertEqual(self.pool.workers[-1].args[2], 25)
            self.complete(window, _page(25, 26))
            self.wait_frame(window, lambda: len(self.pool.workers) == 3)
            self.complete(window, _page(50, 0))
            self.assertFalse(controller.hasMore)
            self.assertFalse(controller.busy)
            self.assertEqual(len(self.pool.workers), 3)

    def test_wheeling_up_from_end_does_not_load_another_page(self):
        with self.scene(animated=True) as (controller, _view, feed, window):
            self.complete(window, _page(0, 26))
            feed.positionViewAtEnd()
            self.wait_frame(window)
            self.assertTrue(feed.property("atYEnd"))
            self.wheel(feed, window, angle=120)
            self.wait_frame(
                window, lambda: not feed.property("interactionMoving"),
            )
            self.assertFalse(controller.busy)
            self.assertEqual(len(self.pool.workers), 1)

    def test_failed_or_hidden_feed_does_not_automatically_retry(self):
        with self.scene() as (controller, view, _feed, window):
            controller.set_search_text("needle")
            view.setVisible(False)
            self.complete(window, _page(0, 26))
            self.assertEqual(len(self.pool.workers), 1)
            view.setVisible(True)
            self.wait_frame(window, lambda: len(self.pool.workers) == 2)
            self.pool.workers[-1].error.emit((RuntimeError("offline"), "trace"))
            self.wait_frame(window, lambda: not controller.busy)
            self.wait_frame(window)
            self.assertEqual(len(self.pool.workers), 2)

    def open_calendar(self, view, window):
        button = view.findChild(QQuickItem, "activityFeedCalendarButton")
        self.click(button, window)
        calendar = view.findChild(QObject, "activityCalendarPopup")
        self.wait_frame(window, lambda: calendar.property("opened"))
        return calendar

    def close_calendar(self, calendar, window):
        calendar.close()
        self.wait_frame(window, lambda: not calendar.property("visible"))
        # A second physical click is allowed after the shared duplicate-input
        # guard; do not disable that policy just to reopen faster in the test.
        guard = QTimer()
        guard.setSingleShot(True)
        elapsed = QSignalSpy(guard.timeout)
        duration = int(calendar.property("sameSourceToggleWindow")) + 1
        guard.start(duration)
        self.assertTrue(elapsed.wait(duration + 1000))

    def test_open_calendar_refreshes_full_history_after_invalidation(self):
        with self.scene() as (controller, view, _feed, window):
            self.complete(window, _page(0, 26))
            calendar = self.open_calendar(view, window)
            self.assertEqual(len(self.pool.workers), 2)
            calendar_worker = self.pool.workers[-1]
            self.assertTrue(calendar_worker.args[5])  # include_day_counts
            self.assertTrue(calendar_worker.args[7])  # counts_only
            self.assertEqual(calendar_worker.args[8], "")
            with patch("thlib.tactic_classes.get_user_recent_activity", return_value={
                "records": [], "dayCounts": [
                    {"dateKey": "2026-08-22", "count": 100},
                    {"dateKey": "2026-07-18", "count": 40},
                    {"dateKey": "2024-03-12", "count": 42},
                ],
            }) as query:
                payload = calendar_worker.function(*calendar_worker.args)
            self.assertTrue(query.call_args.kwargs["counts_only"])
            self.complete(window, payload, calendar_worker)
            self.assertEqual(controller.calendarCounts["2024-03-12"], 42)
            controller.apply_cache_invalidation({"demo": ["activity"]})
            self.assertEqual(controller.calendarCounts["2024-03-12"], 42)
            self.wait_frame(window, lambda: len(self.pool.workers) == 3)
            self.assertEqual(self.pool.workers[-1].args[8], "")
            self.complete(window, {"records": [], "dayCounts": [
                {"dateKey": "2026-07-18", "count": 40},
                {"dateKey": "2024-03-12", "count": 43},
            ]})
            self.assertEqual(controller.calendarCounts["2024-03-12"], 43)
            self.assertEqual(controller.model.count(), 25)
            previous = calendar.findChild(QQuickItem, "activityCalendarPreviousMonth")
            popup_window = previous.window()
            self.click(previous, popup_window)
            self.wait_frame(popup_window)
            day = self._visual_item(
                popup_window.contentItem(), "activityCalendarDay_2026-07-18",
            )
            self.assertIsNotNone(day)
            self.assertEqual(day.property("eventCount"), 40)
            self.click(day, popup_window)
            self.wait_frame(window, lambda: controller.selectedDay == "2026-07-18")
            self.assertEqual(self.pool.workers[-1].args[2], 0)
            self.assertEqual(self.pool.workers[-1].args[4], "2026-07-18")
            self.complete(window, _page(0, 26, "2026-07-18"))
            feed = view.findChild(QQuickItem, "activityFeedList")
            self.wheel(feed, window)
            self.wait_frame(window, lambda: controller.busy)
            self.assertEqual(self.pool.workers[-1].args[2], 25)
            self.assertEqual(self.pool.workers[-1].args[4], "2026-07-18")

    def test_calendar_opens_with_stale_full_history_before_feed_scroll(self):
        cached_calendar = {
            "completeHistory": True,
            "dayCounts": {
                "2026-08-22": 100,
                "2026-07-18": 40,
            },
        }
        with (
            patch("thlib.server_cache.read_entry", return_value=None),
            patch(
                "thlib.server_cache.read_stale_entry",
                side_effect=(cached_calendar, {}, {}),
            ),
            self.scene() as (controller, view, _feed, window),
        ):
            self.complete(window, _page(0, 26))
            self.assertEqual(controller.calendarCounts["2026-07-18"], 40)

            calendar = self.open_calendar(view, window)
            self.assertEqual(self.pool.workers[-1].args[8], "")
            previous = calendar.findChild(
                QQuickItem, "activityCalendarPreviousMonth"
            )
            popup_window = previous.window()
            self.click(previous, popup_window)
            self.wait_frame(popup_window)
            day = self._visual_item(
                popup_window.contentItem(),
                "activityCalendarDay_2026-07-18",
            )
            self.assertIsNotNone(day)
            self.assertEqual(day.property("eventCount"), 40)

    @staticmethod
    def click(item, window):
        QTest.mouseClick(
            window, Qt.LeftButton, Qt.NoModifier,
            item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint(),
        )

    def test_calendar_invalidation_during_query_recounts_once_and_keeps_history(self):
        with self.scene() as (controller, view, _feed, window):
            self.complete(window, _page(0, 26))
            calendar = self.open_calendar(view, window)
            worker = self.pool.workers[-1]
            controller.apply_cache_invalidation({"demo": ["activity"]})
            controller.apply_cache_invalidation({"demo": ["activity"]})
            self.assertEqual(len(self.pool.workers), 2)
            with patch.object(controller, "_save_calendar_counts") as save:
                self.complete(window, {"dayCounts": [
                    {"dateKey": "2024-03-12", "count": 42},
                ]}, worker)
                save.assert_not_called()
            self.assertEqual(controller.calendarCounts["2024-03-12"], 42)
            self.assertEqual(len(self.pool.workers), 3)
            self.assertEqual(self.pool.workers[-1].args[8], "")
            self.pool.workers[-1].error.emit({"exception": "offline"})
            self.wait_frame(window, lambda: not controller.calendarBusy)
            self.wait_frame(window)
            self.assertEqual(len(self.pool.workers), 3)
            self.assertEqual(controller.calendarCounts["2024-03-12"], 42)
            self.close_calendar(calendar, window)
            controller.apply_cache_invalidation({"demo": ["activity"]})
            self.wait_frame(window)
            self.assertEqual(len(self.pool.workers), 3)
            controller.apply_cache_invalidation({"all": True})
            self.assertNotIn("2024-03-12", controller.calendarCounts)
            self.assertEqual(len(self.pool.workers), 3)

    def test_refresh_recounts_whole_calendar_and_rejects_old_completion(self):
        with self.scene(width=1100, height=720) as (controller, view, _feed, window):
            self.complete(window, _page(0, 26))
            calendar = self.open_calendar(view, window)
            old_worker = self.pool.workers[-1]
            controller._calendar_counts = {"2024-03-12": 42}
            controller._calendar_cache_complete = True
            controller.refresh()
            self.assertTrue(old_worker.cancelled)
            self.assertEqual(len(self.pool.workers), 4)
            refresh_worker, calendar_worker = self.pool.workers[-2:]
            self.assertTrue(refresh_worker.args[9])
            self.assertTrue(calendar_worker.args[9])
            self.assertEqual(calendar_worker.args[8], "")
            self.complete(window, {"dayCounts": [
                {"dateKey": "2024-03-12", "count": 999},
            ]}, old_worker)
            self.assertEqual(controller.calendarCounts["2024-03-12"], 42)
            self.complete(window, {"dayCounts": [
                {"dateKey": "2024-03-12", "count": 43},
            ]}, calendar_worker)
            self.assertEqual(controller.calendarCounts["2024-03-12"], 43)
            self.assertTrue(controller._calendar_cache_complete)
            self.assertFalse(controller._calendar_bypass_cache)
            calendar.close()

    def test_calendar_scope_change_ignores_previous_user_counts(self):
        with self.scene() as (controller, view, _feed, window):
            self.complete(window, _page(0, 26))
            calendar = self.open_calendar(view, window)
            old_worker = self.pool.workers[-1]
            self.close_calendar(calendar, window)
            controller.set_users(["reviewer"])
            self.complete(window, _page(0, 1))
            self.complete(window, {"dayCounts": [
                {"dateKey": "2024-03-12", "count": 999},
            ]}, old_worker)
            self.assertNotIn("2024-03-12", controller.calendarCounts)
            calendar = self.open_calendar(view, window)
            self.assertEqual(self.pool.workers[-1].args[6], ["reviewer"])
            self.assertEqual(self.pool.workers[-1].args[8], "")
            calendar.close()


if __name__ == "__main__":
    unittest.main()
