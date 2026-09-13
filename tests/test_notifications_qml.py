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

from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"
HISTORY_ROLES = (
    "notificationId", "kind", "group", "message", "detail",
    "timestamp", "timestampPretty", "timestampFull",
)
TOAST_ROLES = (
    "notificationId", "kind", "message", "detail", "progress",
    "dismissible", "action", "actionData", "dedupeKey",
    "sourceType", "sourceTitle", "previewUrl", "avatarText",
    "avatarColor", "sourceIcon",
)


class _NotificationController(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._history_group = "all"
        self.clear_calls = 0
        self.dismiss_calls = []
        self.activate_calls = []

    @Property(int, notify=changed)
    def count(self):
        return 1

    @Property(str, notify=changed)
    def historyGroup(self):
        return self._history_group

    @Slot(str)
    def set_history_group(self, value):
        self._history_group = str(value)
        self.changed.emit()

    @Slot()
    def clear_history(self):
        self.clear_calls += 1

    @Slot(int)
    def dismiss(self, index):
        self.dismiss_calls.append(index)

    @Slot(int)
    def activate(self, index):
        self.activate_calls.append(index)


def _history_record(index):
    return {
        "notificationId": f"event-{index}",
        "kind": "complete" if index % 2 else "info",
        "group": "repository" if index % 2 else "client",
        "message": f"Repository download completed {index}",
        "detail": "The local cache now contains the current files.",
        "timestamp": "2026-08-25T15:00:06",
        "timestampPretty": "Just now",
        "timestampFull": "25 August 2026, 15:00:06",
    }


class NotificationsQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def _create_view(self, record_count=18):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        controller = _NotificationController()
        model = RecordListModel(
            HISTORY_ROLES,
            [_history_record(index) for index in range(record_count)],
        )
        engine.rootContext().setContextProperty(
            "notificationController", controller
        )
        engine.rootContext().setContextProperty(
            "notificationHistoryModel", model
        )
        engine.rootContext().setContextProperty(
            "notificationGroupedHistoryModel", model
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "NotificationsView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        return engine, theme_component, component, theme, controller, model, view

    @staticmethod
    def _inside(item, container):
        top_left = item.mapToItem(container, QPointF(0, 0))
        bottom_right = item.mapToItem(
            container, QPointF(item.width(), item.height())
        )
        return (
            top_left.x() >= -0.5
            and top_left.y() >= -0.5
            and bottom_right.x() <= container.width() + 0.5
            and bottom_right.y() <= container.height() + 0.5
        )

    @staticmethod
    def _visual_item(owner, object_name):
        pending = list(owner.childItems())
        while pending:
            item = pending.pop()
            if item.objectName() == object_name:
                return item
            pending.extend(item.childItems())
        return None

    @staticmethod
    def _visible_visual_item(owner, object_name):
        pending = list(owner.childItems())
        while pending:
            item = pending.pop()
            pending.extend(item.childItems())
            if item.objectName() != object_name or not item.isVisible():
                continue
            position = item.mapToItem(owner, QPointF(0, 0))
            if (
                    position.y() + item.height() >= 0
                    and position.y() <= owner.height()):
                return item
        return None

    def test_history_uses_shared_surface_scrollbar_and_selectable_text(self):
        (
            engine, theme_component, component, theme,
            controller, model, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(900, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(320)
            panel = view.findChild(QQuickItem, "notificationsPanel")
            toolbar = view.findChild(QQuickItem, "notificationsToolbar")
            history = view.findChild(QQuickItem, "notificationHistoryList")
            scroll_bar = view.findChild(
                QQuickItem, "notificationHistoryScrollBar"
            )
            message = self._visible_visual_item(
                view, "notificationMessageText"
            )
            timestamp = self._visible_visual_item(
                view, "notificationTimestampText"
            )
            filters = view.findChild(
                QQuickItem, "notificationHistoryFilters"
            )

            self.assertIsNotNone(panel)
            self.assertIsNotNone(toolbar)
            self.assertIsNotNone(history)
            self.assertIsNotNone(scroll_bar)
            self.assertIsNotNone(message, {
                "count": history.property("count"),
                "historyWidth": history.width(),
                "historyHeight": history.height(),
                "contentHeight": history.property("contentHeight"),
                "toolbarHeight": toolbar.height(),
                "viewSize": (view.width(), view.height()),
                "namedChildren": [
                    (child.metaObject().className(), child.objectName())
                    for child in history.findChildren(QObject)
                    if child.objectName()
                ][:80],
            })
            self.assertIsNotNone(timestamp)
            self.assertIsNotNone(filters)
            self.assertTrue(self._inside(panel, view))
            self.assertTrue(scroll_bar.property("visible"))
            self.assertTrue(message.property("readOnly"))
            self.assertTrue(message.property("selectByMouse"))
            self.assertEqual(timestamp.property("text"), "Just now")
            self.assertNotIn("T", timestamp.property("text"))

            context_point = message.mapToScene(QPointF(10, 8)).toPoint()
            QTest.mouseClick(
                window,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
                context_point,
            )
            QTest.qWait(80)
            context_menu = message.findChild(
                QObject, "selectableTextContextMenu"
            )
            self.assertIsNotNone(context_menu)
            self.assertTrue(context_menu.property("visible"))
            context_menu.close()
            QTest.qWait(30)

            copy_expression = QQmlExpression(
                engine.rootContext(),
                message,
                "(function() { forceActiveFocus(); selectAll(); copy(); })()",
            )
            copy_expression.evaluate()
            self.assertFalse(copy_expression.hasError())
            QGuiApplication.processEvents()
            self.assertIn(
                "Repository download completed",
                QGuiApplication.clipboard().text(),
            )

            view.setProperty("width", 440)
            view.setProperty("height", 520)
            QTest.qWait(80)
            self.assertTrue(filters.property("iconOnly"))
            self.assertTrue(self._inside(toolbar, view))
            self.assertTrue(self._inside(history, view))
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_empty_state_keeps_readable_width_in_wide_and_narrow_views(self):
        (
            engine, theme_component, component, theme,
            controller, model, view,
        ) = self._create_view(record_count=0)
        window = QQuickWindow()
        window.resize(900, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(80)
            empty_state = view.findChild(
                QQuickItem, "notificationsEmptyState"
            )
            title = view.findChild(QQuickItem, "emptyStateTitle")
            self.assertIsNotNone(empty_state)
            self.assertIsNotNone(title)
            self.assertTrue(empty_state.isVisible())
            self.assertGreaterEqual(empty_state.width(), 240)
            self.assertLessEqual(empty_state.width(), 440)
            self.assertGreaterEqual(title.width(), 240)
            self.assertLessEqual(title.property("lineCount"), 2)

            window.resize(360, 520)
            view.setSize(window.size())
            QTest.qWait(80)
            self.assertGreaterEqual(empty_state.width(), 240)
            self.assertLessEqual(empty_state.width(), 320)
            self.assertGreaterEqual(title.width(), 240)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_custom_toast_shows_message_source_avatar_and_excerpt(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        controller = _NotificationController()
        model = RecordListModel(TOAST_ROLES, [{
            "notificationId": "message-1",
            "kind": "info",
            "message": "Sam Supervisor",
            "detail": "The lighting render is ready for review.",
            "progress": -1.0,
            "dismissible": True,
            "action": "messages",
            "actionData": "conversation-7",
            "dedupeKey": "message-1",
            "sourceType": "message",
            "sourceTitle": "Lighting",
            "previewUrl": "",
            "avatarText": "SS",
            "avatarColor": "#78909c",
            "sourceIcon": "comments",
        }])
        engine.rootContext().setContextProperty(
            "notificationController", controller
        )
        engine.rootContext().setContextProperty("notificationModel", model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(QML / "NotificationToastWindow.qml")),
        )
        toast = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "notifications": model,
        })
        self.assertIsNotNone(
            toast,
            "\n".join(error.toString() for error in component.errors()),
        )

        try:
            QTest.qWait(120)
            content_item = toast.contentItem()
            source = self._visual_item(
                content_item, "notificationSource"
            )
            sender = self._visual_item(
                content_item, "notificationMessage"
            )
            detail = self._visual_item(
                content_item, "notificationDetail"
            )
            avatar = self._visual_item(
                content_item, "notificationAvatarText"
            )

            self.assertTrue(toast.isVisible())
            self.assertTrue(
                toast.flags() & Qt.WindowType.FramelessWindowHint
            )
            self.assertTrue(
                toast.flags() & Qt.WindowType.WindowStaysOnTopHint
            )
            available = toast.screen().availableGeometry()
            self.assertAlmostEqual(
                toast.x(), available.x() + available.width()
                    - toast.width() - 18,
                delta=2,
            )
            self.assertAlmostEqual(
                toast.y(), available.y() + available.height()
                    - toast.height() - 18,
                delta=2,
            )
            self.assertIsNotNone(source)
            self.assertIsNotNone(sender)
            self.assertIsNotNone(detail)
            self.assertIsNotNone(avatar)
            self.assertEqual(source.property("text"), "Message · Lighting")
            self.assertEqual(sender.property("text"), "Sam Supervisor")
            self.assertEqual(
                detail.property("text"),
                "The lighting render is ready for review.",
            )
            self.assertEqual(avatar.property("text"), "SS")

            model.replace([{
                "notificationId": "activity-1",
                "kind": "info",
                "message": "Ada Artist",
                "detail": "Published Robot in process render.",
                "progress": -1.0,
                "dismissible": True,
                "action": "activity",
                "actionData": "publication:SNAPSHOT001",
                "dedupeKey": "activity-1",
                "sourceType": "activity",
                "sourceTitle": "New publication",
                "previewUrl": "",
                "avatarText": "AA",
                "avatarColor": "#5c6bc0",
                "sourceIcon": "snapshot",
            }])
            QTest.qWait(80)
            self.assertEqual(
                source.property("text"),
                "Activity Feed · New publication",
            )
            self.assertEqual(sender.property("text"), "Ada Artist")
            self.assertEqual(
                detail.property("text"),
                "Published Robot in process render.",
            )
            self.assertEqual(avatar.property("text"), "AA")
            available = toast.screen().availableGeometry()
            self.assertAlmostEqual(
                toast.x(), available.x() + available.width()
                    - toast.width() - 18,
                delta=2,
            )
            self.assertAlmostEqual(
                toast.y(), available.y() + available.height()
                    - toast.height() - 18,
                delta=2,
            )

            point = sender.mapToScene(
                QPointF(sender.width() / 2, sender.height() / 2)
            ).toPoint()
            QTest.mouseClick(
                toast,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                point,
            )
            QTest.qWait(30)
            self.assertEqual(controller.activate_calls, [0])
        finally:
            toast.close()
            toast.deleteLater()
            theme.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
