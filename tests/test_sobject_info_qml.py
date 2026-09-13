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


def _activity_record(index: int) -> dict:
    return {
        "searchKey": "",
        "targetSearchKey": "skey://demo/assets?code=ASSET001",
        "targetTitle": "Bathroom",
        "targetType": "demo/assets",
        "targetTypeTitle": "Assets",
        "kind": "change",
        "title": "Updated object",
        "detail": "Description changed on activity row {0}".format(index),
        "actor": "artist",
        "actorLabel": "Ada Artist",
        "actorAvatar": "",
        "actorInitials": "AA",
        "actorColor": "#4e7fa5",
        "timestamp": "2026-08-25 12:00:00",
        "timestampPretty": "yesterday",
        "timestampFull": "25 August 2026, 12:00:00",
        "itemCode": "",
        "itemTitle": "",
        "itemType": "",
        "itemTypeTitle": "",
        "itemTypeColor": "",
        "relationAction": "",
        "hours": 0.0,
        "workDay": "",
        "workDayPretty": "",
        "workHourAction": "",
        "workHourCategory": "",
        "workHourStatus": "",
        "workHourOwner": "",
        "typeColor": "#ef5350",
        "processColor": "",
        "project": "demo",
        "process": "",
        "context": "",
        "version": "",
        "statusBefore": "",
        "statusAfter": "",
        "statusBeforeColor": "",
        "statusAfterColor": "",
        "changes": [],
        "taskCode": "",
        "serverGenerated": False,
        "canOpen": True,
    }


class _SObjectInfoController(QObject):
    changed = Signal()

    @Slot(int)
    def set_page(self, page):
        self.page = page

    def __init__(self):
        super().__init__()
        self._activity_has_more = False
        self._activity_loading_more = False
        self.load_more_calls = 0
        self.opened_note_rows = []

    @Property("QVariantMap", notify=changed)
    def summary(self):
        return {
            "title": "Baby_Shark.Default",
            "typeTitle": "Assets",
            "description": "Test asset",
            "code": "ASSETS00283",
            "searchType": "dolly3d/assets?project=niki_friends",
            "project": "Niki Friends",
            "pipeline": "niki_friends/assets",
            "searchKey": "skey://dolly3d/assets?code=ASSETS00283",
            "accent": "#ef5350",
        }

    @Property("QVariantMap", notify=changed)
    def metrics(self):
        return {
            "tasks": 3,
            "notes": 0,
            "children": 0,
            "childTypes": 0,
            "participants": 1,
            "workHours": 0,
            "files": 12,
            "snapshots": 6,
            "totalSize": "25.8 MB",
        }

    @Property(bool, notify=changed)
    def busy(self):
        return False

    @Property(bool, notify=changed)
    def activityHasMore(self):
        return self._activity_has_more

    @Property(bool, notify=changed)
    def activityLoadingMore(self):
        return self._activity_loading_more

    @Property(bool, notify=changed)
    def hasObject(self):
        return True

    @Property(str, notify=changed)
    def error(self):
        return ""

    @Slot()
    def refresh(self):
        pass

    @Slot()
    def load_more_activity(self):
        self.load_more_calls += 1

    @Slot(str)
    def open_search_key(self, _search_key):
        pass

    @Slot(str)
    def open_participant(self, _login):
        pass

    @Slot(int)
    def open_note(self, index):
        self.opened_note_rows.append(index)

    @Slot(str, str)
    def open_task(self, _task_code, _process):
        pass

    @Slot(str, str)
    def open_tasks_filter(self, _field, _value):
        pass

    @Slot(int)
    def open_activity(self, _index):
        pass


class SObjectInfoQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def _create_view(
            self, child_records=None, activity_records=None,
            note_records=None):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        controller = _SObjectInfoController()
        empty_model = RecordListModel(())
        child_model = RecordListModel((
            "searchKey", "title", "subtitle", "typeTitle", "typeCode",
            "relationship", "status", "accent", "previewUrl",
        ), child_records or [])
        activity_model = RecordListModel((
            "searchKey", "targetSearchKey", "targetTitle", "targetType",
            "targetTypeTitle", "kind", "title", "detail", "actor",
            "actorLabel", "actorAvatar", "actorInitials", "actorColor",
            "timestamp", "timestampPretty", "timestampFull", "itemCode",
            "itemTitle", "itemType", "itemTypeTitle", "itemTypeColor",
            "relationAction", "hours", "workDay", "workDayPretty",
            "workHourAction", "workHourCategory", "workHourStatus",
            "workHourOwner", "typeColor", "processColor", "project",
            "process", "context", "version", "statusBefore",
            "statusAfter", "statusBeforeColor", "statusAfterColor",
            "changes", "taskCode", "serverGenerated", "canOpen",
        ), activity_records or [])
        note_model = RecordListModel((
            "searchKey", "body", "author", "authorLabel", "avatarUrl",
            "initials", "authorColor", "timestamp", "timestampPretty",
            "timestampFull", "process", "taskCode", "taskTitle",
            "isTaskNote",
        ), note_records or [])
        engine.rootContext().setContextProperty(
            "sobjectInfoController", controller
        )
        for name in (
            "sobjectTaskStatusModel", "sobjectTaskProcessModel",
            "sobjectTaskModel", "sobjectParticipantModel",
            "sobjectChildTypeModel",
            "sobjectSnapshotProcessModel",
        ):
            engine.rootContext().setContextProperty(name, empty_model)
        engine.rootContext().setContextProperty("sobjectChildModel", child_model)
        engine.rootContext().setContextProperty("sobjectNoteModel", note_model)
        engine.rootContext().setContextProperty(
            "sobjectActivityModel", activity_model
        )

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SObjectInfoView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        return (
            engine, theme_component, component, theme,
            controller,
            (empty_model, child_model, activity_model, note_model), view,
        )

    def test_report_pages_are_created_only_after_first_activation(self):
        (
            engine, theme_component, component, theme,
            controller, models, view,
        ) = self._create_view()
        try:
            self.app.processEvents()
            self.assertIsNotNone(
                view.findChild(QQuickItem, "sobjectTasksPageHost")
            )
            self.assertIsNone(
                view.findChild(QObject, "sobjectNoteRepeater")
            )
            self.assertIsNone(
                view.findChild(QQuickItem, "sobjectChildrenPage")
            )

            tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
            tabs.setProperty("currentIndex", 1)
            self.app.processEvents()
            self.assertIsNotNone(
                view.findChild(QObject, "sobjectNoteRepeater")
            )

            tabs.setProperty("currentIndex", 2)
            self.app.processEvents()
            self.assertIsNotNone(
                view.findChild(QQuickItem, "sobjectChildrenPage")
            )
            self.assertIsNotNone(
                view.findChild(QObject, "sobjectNoteRepeater")
            )
        finally:
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_note_row_click_invokes_the_note_navigation_command(self):
        note = {
            "searchKey": "skey://sthpw/note?code=NOTE001",
            "body": "Review this render",
            "author": "artist",
            "authorLabel": "Ada Artist",
            "avatarUrl": "",
            "initials": "AA",
            "authorColor": "#4caf50",
            "timestamp": "2026-08-26 12:00:00",
            "timestampPretty": "today",
            "timestampFull": "26 August 2026, 12:00",
            "process": "model",
            "taskCode": "TASK001",
            "taskTitle": "Model",
            "isTaskNote": True,
        }
        (
            engine, theme_component, component, theme,
            controller, models, view,
        ) = self._create_view(note_records=[note])
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
        tabs.setProperty("currentIndex", 1)
        window.show()
        try:
            QTest.qWait(100)
            repeater = view.findChild(QObject, "sobjectNoteRepeater")
            self.assertIsNotNone(repeater)
            context = QQmlEngine.contextForObject(repeater)
            row, undefined = QQmlExpression(
                context, repeater, "itemAt(0)"
            ).evaluate()
            self.assertFalse(undefined)
            self.assertIsNotNone(row)
            self.assertEqual(row.objectName(), "sobjectNoteRow0")
            point = row.mapToScene(
                QPointF(row.width() / 2, row.height() / 2)
            ).toPoint()
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, point
            )
            QTest.qWait(30)
            self.assertEqual(controller.opened_note_rows, [0])
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_children_empty_state_stays_centered_and_readable(self):
        (
            engine, theme_component, component, theme,
            controller, empty_model, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(1200, 900)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
        tabs.setProperty("currentIndex", 2)
        window.show()
        try:
            QTest.qWait(100)
            empty_state = view.findChild(
                QQuickItem, "sobjectChildrenEmptyState"
            )
            self.assertIsNotNone(empty_state)
            message = empty_state.findChild(QQuickItem, "emptyStateMessage")
            page = view.findChild(QQuickItem, "sobjectChildrenPage")
            panel = view.findChild(QQuickItem, "sobjectChildrenListPanel")
            rows = view.findChild(QQuickItem, "sobjectChildrenRows")
            self.assertIsNotNone(message)
            self.assertTrue(empty_state.isVisible())
            self.assertGreaterEqual(empty_state.width(), 900, {
                "view": view.width(),
                "page": page.width(),
                "panel": panel.width(),
                "rowsParent": rows.parent().width(),
                "rows": rows.width(),
                "empty": empty_state.width(),
                "emptyImplicit": empty_state.implicitWidth(),
                "maximumContentWidth": empty_state.property(
                    "maximumContentWidth"
                ),
                "message": message.width(),
            })
            self.assertGreaterEqual(message.width(), 240)
            self.assertLessEqual(message.property("lineCount"), 2)

            message_center = message.mapToItem(
                view, QPointF(message.width() / 2, 0)
            ).x()
            self.assertAlmostEqual(
                message_center, view.width() / 2, delta=24
            )

            window.resize(560, 760)
            view.setSize(window.size())
            QTest.qWait(80)
            self.assertGreaterEqual(empty_state.width(), 400)
            self.assertGreaterEqual(message.width(), 240)
            self.assertLessEqual(message.property("lineCount"), 2)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_children_page_renders_loaded_child_records(self):
        child = {
            "searchKey": "skey://demo/shot?code=SHOT010",
            "title": "Shot 010",
            "subtitle": "Linked shot",
            "typeTitle": "Shots",
            "typeCode": "demo/shot",
            "relationship": "code",
            "status": "In Progress",
            "accent": "#8e6ccf",
            "previewUrl": "",
        }
        (
            engine, theme_component, component, theme,
            controller, models, view,
        ) = self._create_view([child])
        window = QQuickWindow()
        window.resize(900, 700)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
        tabs.setProperty("currentIndex", 2)
        window.show()
        try:
            QTest.qWait(100)
            repeater = view.findChild(QObject, "sobjectChildrenRepeater")
            empty_state = view.findChild(
                QQuickItem, "sobjectChildrenEmptyState"
            )
            rows = view.findChild(QQuickItem, "sobjectChildrenRows")
            self.assertIsNotNone(repeater)
            self.assertEqual(repeater.property("count"), 1)
            self.assertFalse(empty_state.isVisible())
            self.assertGreaterEqual(rows.implicitHeight(), 68)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_small_overflow_scrolls_the_full_header_without_compacting(self):
        (
            engine, theme_component, component, theme,
            controller, empty_model, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(1200, 320)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
        tabs.setProperty("currentIndex", 2)
        window.show()
        try:
            QTest.qWait(100)
            report_scroll = view.findChild(
                QQuickItem, "sobjectInfoReportScroll"
            )
            scroll_bar = view.findChild(
                QQuickItem, "sobjectInfoReportScrollBar"
            )
            header = view.findChild(
                QQuickItem, "sobjectInfoPresentationHeader"
            )
            self.assertIsNotNone(report_scroll)
            self.assertIsNotNone(scroll_bar)
            self.assertIsNotNone(header)

            natural_height = float(report_scroll.property("contentHeight"))
            self.assertGreater(natural_height, 320)
            window.resize(1200, max(320, int(natural_height - 20)))
            view.setSize(window.size())
            QTest.qWait(80)

            overflow = (
                float(report_scroll.property("contentHeight"))
                - report_scroll.height()
            )
            self.assertGreater(overflow, 0)
            self.assertLessEqual(overflow, 24)
            self.assertTrue(scroll_bar.isVisible())
            header_height = header.height()
            header_before = header.mapToItem(view, QPointF(0, 0)).y()

            report_scroll.setProperty("contentY", overflow)
            QTest.qWait(30)

            header_after = header.mapToItem(view, QPointF(0, 0)).y()
            self.assertAlmostEqual(header.height(), header_height, delta=0.5)
            self.assertAlmostEqual(
                header_before - header_after, overflow, delta=1.0
            )
            self.assertIsNone(
                view.findChild(QQuickItem, "sobjectInfoCompactHeader")
            )
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_activity_requests_next_page_at_scroll_end(self):
        (
            engine, theme_component, component, theme,
            controller, models, view,
        ) = self._create_view(
            activity_records=[_activity_record(index) for index in range(20)]
        )
        window = QQuickWindow()
        window.resize(720, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
        tabs.setProperty("currentIndex", 4)
        window.show()
        try:
            QTest.qWait(120)
            report_scroll = view.findChild(
                QQuickItem, "sobjectInfoReportScroll"
            )
            scroll_bar = view.findChild(
                QQuickItem, "sobjectInfoReportScrollBar"
            )
            self.assertIsNotNone(report_scroll)
            self.assertIsNotNone(scroll_bar)
            maximum_y = max(
                0.0,
                float(report_scroll.property("contentHeight") or 0)
                - report_scroll.height(),
            )
            self.assertGreater(maximum_y, 40)
            controller._activity_has_more = True
            controller.changed.emit()
            QTest.qWait(20)
            controller.load_more_calls = 0

            report_scroll.setProperty("contentY", maximum_y - 30)
            scroll_bar.armPagination()
            report_scroll.setProperty("contentY", maximum_y)
            QTest.qWait(30)

            self.assertEqual(controller.load_more_calls, 1)
            report_scroll.setProperty("contentY", maximum_y - 10)
            report_scroll.setProperty("contentY", maximum_y)
            QTest.qWait(20)
            self.assertEqual(controller.load_more_calls, 1)
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_report_sections_use_labelled_activity_feed_segments(self):
        (
            engine, theme_component, component, theme,
            controller, empty_model, view,
        ) = self._create_view()
        window = QQuickWindow()
        window.resize(720, 420)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        try:
            QTest.qWait(100)
            tabs = view.findChild(QQuickItem, "sobjectInfoTabs")
            pages = view.findChild(QQuickItem, "sobjectInfoReportPages")
            self.assertIsNotNone(tabs)
            self.assertIsNotNone(pages)
            self.assertFalse(tabs.property("iconOnly"))
            section_model = tabs.property("model")
            if hasattr(section_model, "toVariant"):
                section_model = section_model.toVariant()
            self.assertEqual(
                [section["value"] for section in section_model],
                ["tasks", "notes", "children", "snapshots", "activity"],
            )
            self.assertEqual(
                [section["icon"] for section in section_model],
                [
                    "task", "notes", "account-tree", "snapshot",
                    "activity-feed",
                ],
            )
            self.assertTrue(all(section["label"] for section in section_model))
            self.assertGreaterEqual(tabs.width(), 680)

            report_scroll = view.findChild(
                QQuickItem, "sobjectInfoReportScroll"
            )
            report_scroll.setProperty("contentY", 20)
            QTest.qWait(20)
            tabs.setProperty("currentIndex", 4)
            QTest.qWait(30)
            self.assertEqual(pages.property("currentIndex"), 4)
            self.assertEqual(tabs.property("currentValue"), "activity")
            self.assertAlmostEqual(
                float(report_scroll.property("contentY")), 20, delta=1
            )
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
