import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.workspace_models.records import RecordListModel


class UserProfileQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    @staticmethod
    def _fake_controllers(engine):
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
Item {
    QtObject {
        objectName: "fakeUserController"
        property bool directoryVisible: true
        property bool canManageUsers: false
        property bool editingBusy: false
        property bool busy: false
        property bool tasksBusy: false
        property bool canEdit: false
        property string editingError: ""
        property string error: ""
        property string activityError: ""
        property string login: ""
        property bool canViewWorkHours: false
        property var profile: ({"login": "", "groups": [], "roles": []})
        property var taskSummary: ({"total": 0, "incomplete": 0,
            "overdue": 0, "dueThisWeek": 0})
        property var workHourSummary: ({"loggedHours": 0,
            "approvedHours": 0, "pendingHours": 0,
            "periodStart": "", "periodEnd": ""})
        property var taskStatusSummary: []
        property var taskProcessSummary: []
        function select_profile(login) {}
        function refresh() {}
        function logout() {}
        function open_activity(key) {}
        function open_activity_target(key) {}
        function open_full_activity() {}
        function create_user(values) {}
        function queue_avatar(path) {}
        function save_group_settings(values) {}
        function save_profile(values) {}
    }
    QtObject {
        objectName: "fakeAppController"
        property string server_state: "online"
    }
    QtObject {
        objectName: "fakeMessagesController"
        property bool busy: false
        function open_direct_conversation(login) {}
    }
    QtObject {
        objectName: "fakeTasksController"
        function open_for_user(login) {}
        property string lastProfileFilter: ""
        function open_for_user_filter(login, field, value) {
            lastProfileFilter = login + "|" + field + "|" + value
        }
    }
}
''', QUrl("inline:UserProfileFakes.qml"))
        for _ in range(20):
            if component.status() != QQmlComponent.Status.Loading:
                break
            QTest.qWait(10)
        root = component.create()
        if root is None:
            raise AssertionError("\n".join(
                error.toString() for error in component.errors()
            ))
        return component, root

    @staticmethod
    def _first_user_row(user_list):
        items = [user_list]
        for item in items:
            if isinstance(item, QQuickItem):
                items.extend(item.childItems())
        return next((
            item for item in items
            if item.property("login") == "user0"
        ), None)

    @staticmethod
    def _visual_item(root, name):
        items = [root]
        for item in items:
            if item.objectName() == name:
                return item
            items.extend(item.childItems())
        return None

    def test_user_directory_reserves_scrollbar_gutter(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        fake_component, fakes = self._fake_controllers(engine)
        for context_name, object_name in (
            ("userController", "fakeUserController"),
            ("appController", "fakeAppController"),
            ("messagesController", "fakeMessagesController"),
            ("tasksController", "fakeTasksController"),
        ):
            engine.rootContext().setContextProperty(
                context_name, fakes.findChild(QObject, object_name)
            )

        users = RecordListModel((
            "login", "displayName", "initials", "email", "avatarUrl",
            "avatarColor",
            "groups", "primaryGroup", "current", "selected",
            "presenceKnown", "online", "lastSeen",
        ))
        users.replace([{
            "login": f"user{index}",
            "displayName": f"User {index}",
            "initials": "US",
            "email": "",
            "avatarUrl": "",
            "avatarColor": "#5c6bc0",
            "groups": ["Artists"],
            "primaryGroup": "Artists",
            "current": False,
            "selected": index == 0,
            "presenceKnown": True,
            "online": index % 2 == 0,
            "lastSeen": "",
        } for index in range(20)])
        empty_model = RecordListModel(("value",))
        engine.rootContext().setContextProperty("userListModel", users)
        engine.rootContext().setContextProperty(
            "userActivityModel", empty_model
        )
        engine.rootContext().setContextProperty("userGroupModel", empty_model)

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "UserProfileView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(900, 620)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QTest.qWait(80)

        user_list = view.findChild(QQuickItem, "userDirectoryList")
        scroll_bar = view.findChild(QQuickItem, "userDirectoryScrollBar")
        self.assertIsNotNone(user_list)
        self.assertIsNotNone(scroll_bar)
        row = self._first_user_row(user_list)
        self.assertIsNotNone(row)
        self.assertTrue(scroll_bar.property("visible"))
        work_hours = view.findChild(
            QQuickItem, "profileWorkHoursSection"
        )
        self.assertIsNotNone(work_hours)
        fake_user = fakes.findChild(QObject, "fakeUserController")
        self.assertFalse(
            work_hours.property("visible"),
            "work-hours visible=%r, permission=%r, owner=%r"
            % (
                work_hours.property("visible"),
                fake_user.property("canViewWorkHours"),
                work_hours.parent().property("userController"),
            ),
        )
        fake_user.setProperty("canViewWorkHours", True)
        QTest.qWait(20)
        self.assertTrue(work_hours.property("visible"))
        gutter = float(user_list.width() - row.width())
        self.assertEqual(gutter, 16.0)
        self.assertGreaterEqual(gutter, float(scroll_bar.width()) + 4.0)

        scroll_center = scroll_bar.mapToScene(QPointF(
            scroll_bar.width() / 2, scroll_bar.height() / 2
        ))
        QTest.mouseMove(window, QPoint(
            round(scroll_center.x()), round(scroll_center.y())
        ))
        QTest.qWait(180)
        self.assertGreaterEqual(gutter, float(scroll_bar.width()) + 4.0)

        fake_user.setProperty("profile", {
            "displayName": "Administrator", "login": "admin",
            "project": "Demo Project", "email": "listy@live.ru",
            "contact": "479912061", "address": "Moscow",
            "department": "Uber",
            "server": "http://192.168.2.144", "groups": [], "roles": [],
        })
        card = view.findChild(QQuickItem, "profileSummaryCard")
        server_row = view.findChild(QQuickItem, "profileServerInfo")
        info_grid = view.findChild(QQuickItem, "profileInfoGrid")
        self.assertIsNotNone(card)
        self.assertIsNotNone(server_row)
        self.assertIsNotNone(info_grid)
        # Simulate taller profile fields at a larger UI/text scale.
        info_grid.setProperty("rowSpacing", 32)
        for width in (900, 640):
            window.resize(width, 620)
            view.setSize(window.size())
            QTest.qWait(30)
            server_bottom = server_row.mapToItem(
                card, QPointF(0, server_row.height())).y()
            self.assertLessEqual(server_bottom, card.height() - 12)

        window.resize(640, 620)
        view.setSize(window.size())
        QTest.qWait(30)
        self.assertEqual(
            float(user_list.width() - row.width()), 16.0
        )

        view.setProperty("userSearch", "User 1")
        QGuiApplication.processEvents()
        self.assertEqual(user_list.property("count"), 11)
        view.setProperty("userSearch", "absent user")
        QGuiApplication.processEvents()
        self.assertEqual(user_list.property("count"), 0)
        view.setProperty("userSearch", "Artists")
        QGuiApplication.processEvents()
        self.assertEqual(user_list.property("count"), 20)

        window.close()
        # The native filter calls QML functions: release its view before the
        # engine and source models leave Python scope, not in the next test.
        view.setParentItem(None)
        view.deleteLater()
        QGuiApplication.sendPostedEvents(view, QEvent.DeferredDelete)
        window.deleteLater()
        theme.deleteLater()
        fakes.deleteLater()
        engine.deleteLater()
        QGuiApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        del fake_component

    def test_task_manager_targets_the_viewed_profile(self):
        source = (Path(__file__).parents[1] / "thlib" / "ui" / "qml"
                  / "UserWorkSummary.qml").read_text(encoding="utf-8")
        marker = 'text: qsTr("OPEN TASK MANAGER")'
        block = source[source.index(marker):source.index(marker) + 500]

        self.assertIn(
            "root.tasksController.open_for_user(\n"
            "                root.userController.profile.login",
            block,
        )
        self.assertNotIn("root.userController.login", block)

    def test_work_summary_counts_and_badges_in_narrow_and_wide_views(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        fake_component, fakes = self._fake_controllers(engine)
        fake_user = fakes.findChild(QObject, "fakeUserController")
        fake_tasks = fakes.findChild(QObject, "fakeTasksController")
        fake_user.setProperty("profile", {"login": "artist"})
        fake_user.setProperty("taskSummary", {
            "total": 32, "incomplete": 16,
            "overdue": 7, "dueThisWeek": 0,
        })
        fake_user.setProperty("taskStatusSummary", [{
            "label": "Оплачен", "value": "Оплачен",
            "count": 16, "color": "#00aa44",
        }])
        fake_user.setProperty("taskProcessSummary", [{
            "label": "animation", "value": "animation",
            "count": 27, "color": "#00aa44",
        }])
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "UserWorkSummary.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme, "userController": fake_user,
            "tasksController": fake_tasks,
        })
        self.assertIsNotNone(
            view, "\n".join(error.toString() for error in component.errors())
        )
        window = QQuickWindow()
        window.resize(640, 520)
        view.setParentItem(window.contentItem())
        window.show()

        for width in (640, 420):
            window.resize(width, 520)
            view.setWidth(width)
            QGuiApplication.processEvents()
            for key, expected in (
                ("total", "32"), ("completed", "16"),
                ("incomplete", "16"), ("overdue", "7"),
                ("dueThisWeek", "0"),
            ):
                metric = self._visual_item(view, "profileTaskMetric_" + key)
                self.assertIsNotNone(metric)
                labels = [child for child in metric.childItems()
                          if child.property("text") is not None]
                self.assertIn(expected, [str(label.property("text"))
                                         for label in labels])
                self.assertLessEqual(metric.x() + metric.width(), width)

        for chip_name, expected in (
            ("profileStatusChip", "artist|status|Оплачен"),
            ("profileProcessChip", "artist|process|animation"),
        ):
            chip = self._visual_item(view, chip_name)
            self.assertIsNotNone(chip)
            center = chip.mapToScene(QPointF(
                chip.width() / 2, chip.height() / 2
            ))
            QTest.mouseClick(window, Qt.LeftButton, pos=center.toPoint())
            QGuiApplication.processEvents()
            self.assertEqual(fake_tasks.property("lastProfileFilter"), expected)

        status_chip = self._visual_item(view, "profileStatusChip")
        status_action = self._visual_item(status_chip, "summaryChipAction")
        status_action.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return)
        QGuiApplication.processEvents()
        self.assertEqual(
            fake_tasks.property("lastProfileFilter"),
            "artist|status|Оплачен",
        )

        window.close()
        view.setParentItem(None)
        view.deleteLater()
        QGuiApplication.sendPostedEvents(view, QEvent.DeferredDelete)
        window.deleteLater()
        theme.deleteLater()
        fakes.deleteLater()
        engine.deleteLater()
        QGuiApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        del fake_component

    def test_profile_editor_preserves_the_address_field(self):
        source = (Path(__file__).parents[1] / "thlib" / "ui" / "qml"
                  / "UserProfileEditorDialog.qml").read_text(encoding="utf-8")

        self.assertIn('id: addressField', source)
        self.assertIn('"address": addressField.text', source)

    def test_profile_summary_has_no_legacy_supervisor_or_workload_card(self):
        source = (Path(__file__).parents[1] / "thlib" / "ui" / "qml"
                  / "UserWorkSummary.qml").read_text(encoding="utf-8")

        self.assertNotIn("SUPERVISOR SUMMARY", source)
        self.assertNotIn("workloadPercent", source)
        self.assertIn("root.userController.canViewWorkHours", source)
        self.assertIn('qsTr("THIS WEEK")', source)


if __name__ == "__main__":
    unittest.main()
