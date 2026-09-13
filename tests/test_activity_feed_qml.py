from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


ACTIVITY_ROLES = (
    "eventId", "kind", "title", "detail", "actor", "timestamp",
    "timestampPretty", "timestampFull", "actorLabel", "actorAvatar",
    "actorInitials", "actorColor", "itemCode", "itemTitle", "searchKey",
    "itemType", "itemTypeTitle", "itemTypeColor", "relationAction",
    "targetSearchKey", "targetTitle", "targetType", "targetTypeTitle",
    "pipelineCode",
    "typeColor", "processColor", "project", "process", "context",
    "version", "statusBefore", "statusAfter", "statusBeforeColor",
    "statusAfterColor", "changes", "taskCode", "serverGenerated",
    "hours", "workDay", "workDayPretty", "workHourAction",
    "workHourCategory", "workHourStatus", "workHourOwner",
    "canOpen", "dayKey",
)

USER_ROLES = (
    "login", "displayName", "initials", "avatarUrl", "avatarColor", "groups",
    "primaryGroup", "current",
)


class _LocalizationController(QObject):
    stateChanged = Signal()

    @Property(str, notify=stateChanged)
    def current_language(self):
        return "ru"


class _ActivityFeedController(QObject):
    stateChanged = Signal()
    calendarInvalidated = Signal()
    notificationsEnabledChanged = Signal()

    def __init__(self):
        super().__init__()
        self._busy = False
        self._error = ""
        self._filter = "all"
        self._selected_day = ""
        self._selected_users = []
        self._search_text = ""
        self._exclude_own_activity = False
        self._notifications_enabled = True
        self._calendar_counts = {
            "2026-08-22": 20,
            "2026-08-21": 53,
            "2026-08-15": 29,
        }
        self._has_more = False
        self.visible_calls = []
        self.refresh_calls = 0
        self.load_more_calls = 0

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def currentFilter(self):
        return self._filter

    @Property(bool, notify=stateChanged)
    def excludeOwnActivity(self):
        return self._exclude_own_activity

    @Property(bool, notify=notificationsEnabledChanged)
    def notificationsEnabled(self):
        return self._notifications_enabled

    @Property(str, notify=stateChanged)
    def selectedDay(self):
        return self._selected_day

    @Property("QVariantList", notify=stateChanged)
    def selectedUsers(self):
        return list(self._selected_users)

    @Property(str, notify=stateChanged)
    def searchText(self):
        return self._search_text

    @Property("QVariantMap", notify=stateChanged)
    def calendarCounts(self):
        return dict(self._calendar_counts)

    @Property(bool, notify=stateChanged)
    def calendarBusy(self):
        return False

    @Property(bool, notify=stateChanged)
    def hasMore(self):
        return self._has_more

    @Slot(bool)
    def set_visible(self, value):
        self.visible_calls.append(bool(value))

    @Slot()
    def refresh(self):
        self.refresh_calls += 1

    @Slot()
    def ensure_calendar_counts(self):
        pass

    @Slot()
    def load_more(self):
        self.load_more_calls += 1

    @Slot(str)
    def set_filter(self, value):
        self._filter = str(value)
        self.stateChanged.emit()

    @Slot(bool)
    def set_exclude_own_activity(self, value):
        self._exclude_own_activity = bool(value)
        self.stateChanged.emit()

    @Slot(bool)
    def set_notifications_enabled(self, value):
        self._notifications_enabled = bool(value)
        self.notificationsEnabledChanged.emit()

    @Slot(str)
    def select_day(self, value):
        self._selected_day = str(value)
        self.stateChanged.emit()

    @Slot(str)
    def set_search_text(self, value):
        self._search_text = str(value)
        self.stateChanged.emit()

    @Slot("QVariantList")
    def set_users(self, values):
        self._selected_users = list(values or [])
        self.stateChanged.emit()

    @Slot(int)
    def open_item(self, _row):
        pass

    @Slot(int)
    def open_target(self, _row):
        pass


def _activity_record(event_id, day_key, actor, target):
    record = {role: "" for role in ACTIVITY_ROLES}
    record["hours"] = 0.0
    record.update({
        "eventId": event_id,
        "kind": "publication",
        "actor": actor,
        "actorLabel": actor,
        "actorInitials": actor[:2].upper(),
        "actorColor": "#78909c",
        "timestamp": day_key + " 12:00:00",
        "timestampPretty": day_key,
        "timestampFull": day_key + " 12:00:00",
        "targetTitle": target,
        "targetType": "demo/asset",
        "typeColor": "#5c8ee6",
        "processColor": "#42a86b",
        "process": "publish",
        "detail": "Preview published",
        "canOpen": False,
        "dayKey": day_key,
    })
    return record


class ActivityFeedQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def _create_view(self, controller=None, model=None):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        controller = controller if controller is not None else _ActivityFeedController()
        model = model if model is not None else RecordListModel(ACTIVITY_ROLES, [
            _activity_record("one", "2026-08-22", "Admin", "Episode 79"),
            _activity_record("two", "2026-08-22", "Artist", "Shot 1"),
            _activity_record("three", "2026-08-21", "Artist", "Shot 2"),
        ])
        engine.rootContext().setContextProperty(
            "activityFeedController", controller
        )
        engine.rootContext().setContextProperty("activityFeedModel", model)
        users = RecordListModel(USER_ROLES, [{
            "login": "artist",
            "displayName": "Ada Artist",
            "initials": "AA",
            "avatarUrl": "",
            "avatarColor": "#5c6bc0",
            "groups": ["artists"],
            "primaryGroup": "artists",
            "current": False,
        }])
        localization = _LocalizationController()
        engine.rootContext().setContextProperty("userListModel", users)
        engine.rootContext().setContextProperty(
            "localizationController", localization
        )

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "ActivityFeedView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        return (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        )

    @staticmethod
    def _assert_inside(item, owner):
        position = item.mapToItem(owner, QPointF(0, 0))
        assert position.x() >= -0.5
        assert position.y() >= -0.5
        assert position.x() + item.width() <= owner.width() + 0.5
        assert position.y() + item.height() <= owner.height() + 0.5

    @staticmethod
    def _visual_item(owner, object_name):
        pending = list(owner.childItems())
        while pending:
            item = pending.pop()
            if item.objectName() == object_name:
                return item
            pending.extend(item.childItems())
        return None

    def test_feed_reflows_without_losing_search_calendar_or_refresh(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(1200, 720)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            segments = view.findChild(
                QQuickItem, "activityFeedFilterSegments"
            )
            search = view.findChild(QQuickItem, "activityFeedSearchBox")
            calendar = view.findChild(
                QQuickItem, "activityFeedCalendarButton"
            )
            refresh = view.findChild(
                QQuickItem, "activityFeedRefreshButton"
            )
            exclude_own = view.findChild(
                QQuickItem, "activityFeedExcludeOwnActivity"
            )
            activity_notifications = view.findChild(
                QQuickItem, "activityFeedNotificationsEnabled"
            )
            feed = view.findChild(QQuickItem, "activityFeedList")
            for item in (
                    segments, search, calendar, refresh, exclude_own,
                    activity_notifications, feed):
                self.assertIsNotNone(item)

            self.assertTrue(segments.property("visible"))
            self.assertFalse(segments.property("iconOnly"))
            filters = view.property("feedFilters").toVariant()
            self.assertIn("notes", [record["value"] for record in filters])
            self.assertNotIn(
                "messages", [record["value"] for record in filters]
            )
            self.assertEqual(controller.refresh_calls, 0)
            # Window presentation is owned by application_composition. A
            # retained QML page must not compete with that lifecycle owner.
            self.assertEqual(controller.visible_calls, [])
            self.assertFalse(exclude_own.property("checked"))
            self.assertTrue(activity_notifications.property("checked"))
            notification_center = activity_notifications.mapToScene(QPointF(
                activity_notifications.width() / 2,
                activity_notifications.height() / 2,
            )).toPoint()
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, notification_center,
            )
            QTest.qWait(40)
            self.assertFalse(controller.notificationsEnabled)
            exclude_center = exclude_own.mapToScene(QPointF(
                exclude_own.width() / 2, exclude_own.height() / 2
            )).toPoint()
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, exclude_center,
            )
            QTest.qWait(40)
            self.assertTrue(controller.excludeOwnActivity)
            self.assertLessEqual(search.width(), 250.5)
            self.assertGreater(segments.width(), 500)
            controller.select_day("2026-08-22")
            QTest.qWait(40)
            self.assertAlmostEqual(
                calendar.width(), min(230, calendar.implicitWidth()), delta=0.5
            )
            compact_users = view.findChild(
                QQuickItem, "activityFeedCompactUserFilterButton"
            )
            for item in (calendar, compact_users, refresh):
                self._assert_inside(item, view)
            self.assertFalse(window.grabWindow().isNull())

            for narrow_width in (900, 740, 520, 360):
                window.resize(narrow_width, 640)
                view.setSize(window.size())
                QTest.qWait(60)
                self.assertTrue(segments.property("visible"))
                self.assertTrue(segments.property("iconOnly"))
                for item in (
                        segments, search, calendar, refresh,
                        exclude_own, activity_notifications, feed):
                    self._assert_inside(item, view)
                for value in (
                        "all", "my_tasks", "my_objects", "notes",
                        "publications"):
                    segment = self._visual_item(
                        segments, "segmentedButtonSegment_" + value
                    )
                    self.assertIsNotNone(segment)
                    self.assertTrue(segment.property("visible"))
                    self._assert_inside(segment, segments)
                self.assertLessEqual(calendar.width(), 44.5)
            self.assertFalse(window.grabWindow().isNull())
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_activity_text_supports_selection_and_copy_context_menu(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(900, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            sentence = self._visual_item(view, "activitySentence")
            self.assertIsNotNone(sentence)
            self.assertTrue(sentence.property("readOnly"))
            self.assertTrue(sentence.property("selectByMouse"))

            context_point = sentence.mapToScene(QPointF(12, 8)).toPoint()
            QTest.mouseClick(
                window,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
                context_point,
            )
            QTest.qWait(80)
            context_menu = sentence.findChild(
                QObject, "selectableTextContextMenu"
            )
            self.assertIsNotNone(context_menu)
            self.assertTrue(context_menu.property("visible"))
            context_menu.close()
            QTest.qWait(30)

            copy_expression = QQmlExpression(
                engine.rootContext(),
                sentence,
                "(function() { forceActiveFocus(); selectAll(); copy(); })()",
            )
            copy_expression.evaluate()
            self.assertFalse(copy_expression.hasError())
            QGuiApplication.processEvents()
            copied_text = QGuiApplication.clipboard().text()
            self.assertIn("Committed snapshot", copied_text)
            self.assertIn("publish", copied_text)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_calendar_opens_as_shared_native_popup(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(900, 680)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            calendar_button = view.findChild(
                QQuickItem, "activityFeedCalendarButton"
            )
            calendar_popup = view.findChild(
                QObject, "activityCalendarPopup"
            )
            self.assertIsNotNone(calendar_button)
            self.assertIsNotNone(calendar_popup)

            center = calendar_button.mapToScene(QPointF(
                calendar_button.width() / 2,
                calendar_button.height() / 2,
            )).toPoint()
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, center,
            )
            QTest.qWait(80)
            self.assertTrue(calendar_popup.property("visible"))
            self.assertTrue(calendar_popup.property("usePopupWindow"))
            scrim = self._visual_item(
                window.contentItem(), "activityCalendarScrim"
            )
            self.assertIsNotNone(scrim)
            self.assertEqual(scrim.property("color"), theme.property("scrim"))
            month_label = calendar_popup.findChild(
                QQuickItem, "activityCalendarMonthLabel"
            )
            self.assertIsNotNone(month_label)
            popup_window = month_label.window()
            day = self._visual_item(
                popup_window.contentItem(),
                "activityCalendarDay_2026-08-22",
            )
            self.assertIsNotNone(day)
            self.assertIn("август", str(month_label.property("text")).lower())

            center = day.mapToScene(QPointF(
                day.width() / 2, day.height() / 2
            )).toPoint()
            QTest.mouseClick(
                popup_window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, center,
            )
            QTest.qWait(80)
            self.assertEqual(controller.selectedDay, "2026-08-22")
            self.assertFalse(calendar_popup.property("visible"))
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_overflowing_feed_shows_shared_scrollbar_with_gutter(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        model.replace([
            _activity_record(
                "event-{0}".format(index), "2026-08-22", "Artist",
                "Shot {0}".format(index),
            )
            for index in range(30)
        ])
        window = QQuickWindow()
        window.resize(640, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(100)
            feed = view.findChild(QQuickItem, "activityFeedList")
            scroll_bar = view.findChild(
                QQuickItem, "activityFeedScrollBar"
            )
            self.assertIsNotNone(feed)
            self.assertIsNotNone(scroll_bar)
            self.assertGreater(feed.property("contentHeight"), feed.height())
            self.assertTrue(scroll_bar.property("visible"))
            self.assertGreaterEqual(scroll_bar.width(), 5)
            self._assert_inside(scroll_bar, feed)
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_scrollbar_drag_does_not_request_another_page(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        model.replace([
            _activity_record(
                "event-{0}".format(index), "2026-08-22", "Artist",
                "Shot {0}".format(index),
            )
            for index in range(30)
        ])
        window = QQuickWindow()
        window.resize(640, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(100)
            feed = view.findChild(QQuickItem, "activityFeedList")
            scroll_bar = view.findChild(
                QQuickItem, "activityFeedScrollBar"
            )
            self.assertIsNotNone(feed)
            self.assertIsNotNone(scroll_bar)
            self.assertGreater(feed.property("contentHeight"), feed.height())
            controller._has_more = True
            controller.stateChanged.emit()
            QTest.qWait(20)
            controller.load_more_calls = 0

            start = scroll_bar.mapToScene(QPointF(
                scroll_bar.width() / 2,
                max(4, scroll_bar.height() * 0.06),
            )).toPoint()
            end = scroll_bar.mapToScene(QPointF(
                scroll_bar.width() / 2,
                scroll_bar.height() * 0.92,
            )).toPoint()
            QTest.mousePress(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, start,
            )
            QTest.mouseMove(window, end, 80)
            self.assertTrue(scroll_bar.property("paginationBlocked"))
            self.assertEqual(controller.load_more_calls, 0)
            QTest.mouseRelease(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, end,
            )
            QTest.qWait(30)
            self.assertEqual(controller.load_more_calls, 0)

            maximum_y = max(
                float(feed.property("originY") or 0),
                float(feed.property("originY") or 0)
                + float(feed.property("contentHeight") or 0)
                - feed.height(),
            )
            feed.setProperty("contentY", maximum_y - 30)
            scroll_bar.armPagination()
            feed.setProperty("contentY", maximum_y)
            QTest.qWait(20)
            self.assertEqual(controller.load_more_calls, 1)
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_work_hour_event_renders_hours_date_and_task_context(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        record = _activity_record(
            "work-hour-one", "2026-08-25", "Listy", "Bathroom"
        )
        record.update({
            "kind": "work_hour",
            "hours": 6.5,
            "workDay": "2026-08-25 00:00:00",
            "workDayPretty": "25 August 2026",
            "workHourAction": "create",
            "workHourCategory": "regular",
            "workHourStatus": "approved",
            "workHourOwner": "artist",
            "process": "model",
            "detail": "Retopology",
        })
        model.replace([record])
        window = QQuickWindow()
        window.resize(760, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(100)
            sentence = self._visual_item(view, "activitySentence")
            self.assertIsNotNone(sentence)
            text = str(sentence.property("text"))
            self.assertIn("6", text)
            self.assertIn("Bathroom", text)
            self.assertIn("model", text)
            self.assertIn("artist", text)
            self.assertIn("Retopology", text)
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_server_task_card_uses_parent_context_without_task_code(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        task = _activity_record(
            "task:TASK0003", "2026-08-25", "", "Bathroom"
        )
        task.update({
            "kind": "task",
            "itemCode": "TASK0003",
            "itemTitle": "model/review",
            "process": "model",
            "context": "model/review",
            "statusAfter": "In Progress",
            "taskCode": "TASK0003",
            "serverGenerated": True,
            "canOpen": True,
        })
        model.replace([task])
        window = QQuickWindow()
        window.resize(900, 420)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            sentence = self._visual_item(view, "activitySentence")
            actor_label = self._visual_item(view, "activityActorLabel")
            self.assertIsNotNone(sentence)
            self.assertIsNotNone(actor_label)
            self.assertIn("Bathroom", str(sentence.property("text")))
            self.assertIn("model/review", str(sentence.property("text")))
            self.assertNotIn("TASK0003", str(sentence.property("text")))
            self.assertNotEqual(
                str(actor_label.property("text")), "Unknown user"
            )
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_instance_relation_names_both_objects_without_connector_details(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        relation = _activity_record(
            "audit:TX0017:0", "2026-08-25", "Artist", "Episode 79"
        )
        relation.update({
            "kind": "create",
            "relationAction": "link",
            "searchKey": "skey://demo/asset?code=ASSET001",
            "itemTitle": "Baby Shark",
            "itemType": "demo/asset",
            "itemTypeTitle": "Assets",
            "itemTypeColor": "#ef5350",
            "targetSearchKey": "skey://demo/scene?code=SCENE001",
            "targetTitle": "Episode 79",
            "targetType": "demo/scene",
            "targetTypeTitle": "Scenes",
            "itemCode": "",
            "detail": "",
            "changes": [],
            "canOpen": True,
        })
        model.replace([relation])
        window = QQuickWindow()
        window.resize(900, 420)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            sentence = self._visual_item(view, "activitySentence")
            changes = self._visual_item(view, "activityChangeList")
            self.assertIsNotNone(sentence)
            self.assertIsNotNone(changes)
            text = str(sentence.property("text"))
            self.assertIn("Baby Shark", text)
            self.assertIn("Episode 79", text)
            self.assertIn("Assets", text)
            self.assertIn("Scenes", text)
            self.assertIn('href="activity"', text)
            self.assertIn('href="target"', text)
            self.assertNotIn("LINK001", text)
            self.assertNotIn("asset_in_scene", text)
            self.assertFalse(changes.property("visible"))
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_child_lifecycle_names_the_child_and_owning_object(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        child = _activity_record(
            "audit:TX_CHILD:0", "2026-08-25", "Artist", "Bathroom"
        )
        child.update({
            "kind": "create",
            "searchKey": "skey://demo/shot?code=SHOT001",
            "itemCode": "SHOT001",
            "itemTitle": "Shot 001",
            "itemType": "demo/shot",
            "itemTypeTitle": "Shots",
            "itemTypeColor": "#8e6ccf",
            "targetSearchKey": "skey://demo/asset?code=ASSET001",
            "targetTitle": "Bathroom",
            "targetType": "demo/asset",
            "changes": [],
            "canOpen": True,
        })
        model.replace([child])
        window = QQuickWindow()
        window.resize(900, 420)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            sentence = self._visual_item(view, "activitySentence")
            self.assertIsNotNone(sentence)
            text = str(sentence.property("text"))
            self.assertIn("Shot 001", text)
            self.assertIn("Shots", text)
            self.assertIn("Bathroom", text)
            self.assertNotIn("SHOT001", text)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_object_update_renders_readable_change_rows(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        update = _activity_record(
            "audit:TX0007:0", "2026-08-25", "Artist", "Bathroom"
        )
        update.update({
            "kind": "change",
            "targetType": "demo/asset",
            "changes": [
                {
                    "field": "assigned",
                    "before": "admin",
                    "after": "artist",
                },
                {
                    "field": "description",
                    "before": "",
                    "after": "",
                    "valuesKnown": False,
                },
            ],
        })
        model.replace([update])
        window = QQuickWindow()
        window.resize(900, 420)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            sentence = self._visual_item(view, "activitySentence")
            changes = self._visual_item(view, "activityChangeList")
            self.assertIsNotNone(sentence)
            self.assertIsNotNone(changes)
            self.assertTrue(changes.property("visible"))
            self.assertIn("Bathroom", str(sentence.property("text")))
            self.assertNotIn("TX0007", str(sentence.property("text")))
            self.assertGreater(changes.height(), 40)
            self.assertFalse(window.grabWindow().isNull())

            window.resize(380, 420)
            view.setSize(window.size())
            QTest.qWait(80)
            self._assert_inside(changes, view)
            self.assertFalse(window.grabWindow().isNull())
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_user_filter_selects_user_through_shared_picker(self):
        (
            engine, theme_component, component, theme,
            controller, model, users, localization, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(1200, 720)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            button = view.findChild(
                QQuickItem, "activityFeedCompactUserFilterButton"
            )
            popup = view.findChild(
                QObject, "activityFeedUserFilterPopup"
            )
            self.assertIsNotNone(button)
            self.assertIsNotNone(popup)
            self.assertTrue(button.property("visible"))
            self.assertEqual(button.property("iconName"), "groups")

            center = button.mapToScene(QPointF(
                button.width() / 2, button.height() / 2
            )).toPoint()
            QTest.mouseClick(
                window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, center,
            )
            QTest.qWait(80)
            self.assertTrue(popup.property("visible"))

            picker = popup.findChild(QQuickItem, "activityFeedUserPicker")
            self.assertIsNotNone(picker)
            self.assertGreaterEqual(popup.property("height"), 360)
            self.assertGreater(picker.height(), 200)
            selection_expression = QQmlExpression(
                engine.rootContext(), picker, "toggle('artist')"
            )
            selection_expression.evaluate()
            self.assertFalse(selection_expression.hasError())
            selected = picker.property("selectedLogins")
            self.assertEqual(selected.toVariant(), ["artist"])

            apply_button = popup.findChild(
                QQuickItem, "activityFeedApplyUserFilterButton"
            )
            self.assertIsNotNone(apply_button)
            apply_expression = QQmlExpression(
                engine.rootContext(), apply_button, "clicked()"
            )
            apply_expression.evaluate()
            self.assertFalse(apply_expression.hasError())
            QTest.qWait(80)
            self.assertEqual(controller.selectedUsers, ["artist"])
            self.assertFalse(popup.property("visible"))
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
