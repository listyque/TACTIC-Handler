from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest

from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class UserComboBoxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QGuiApplication.instance() is None:
            QQuickStyle.setStyle("Basic")
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.transient_windows = []
        self.profiles = RecordListModel(
            (
                "login", "displayName", "initials", "email",
                "avatarUrl", "avatarColor", "primaryGroup",
            ),
            [
                {
                    "login": "alice",
                    "displayName": "Alice Smith",
                    "initials": "AS",
                    "email": "alice@test",
                    "avatarUrl": "",
                    "avatarColor": "#ef5350",
                    "primaryGroup": "Artists",
                },
                {
                    "login": "bob",
                    "displayName": "Bob Jones",
                    "initials": "BJ",
                    "email": "bob@test",
                    "avatarUrl": "",
                    "avatarColor": "#42a5f5",
                    "primaryGroup": "Artists",
                },
                {
                    "login": "carl",
                    "displayName": "Carl Lead",
                    "initials": "CL",
                    "email": "carl@test",
                    "avatarUrl": "",
                    "avatarColor": "#66bb6a",
                    "primaryGroup": "Supervisors",
                },
            ],
        )
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(QML))
        self.engine.rootContext().setContextProperty(
            "testUserProfiles", self.profiles
        )
        self.component = QQmlComponent(self.engine)
        self.component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window

Window {
    width: 420
    height: 320
    visible: true
    property int activatedIndex: -1
    property string activatedValue: ""
    property bool popupOpened: chooser.popup.opened
    property bool popupUsesWindow: chooser.popup.popupType === Popup.Window

    function openChooser() {
        chooser.popup.open()
    }
    function searchUsers(value) {
        chooser.searchText = value
        chooser.rebuildPopupOptions()
    }
    function activateRow(index) {
        chooser.activatePopupRow(index)
    }
    function selectedValue() {
        return String(chooser.currentValue || "")
    }
    function addGeneratedUsers(amount) {
        for (let index = 0; index < amount; ++index) {
            choices.append({
                "label": "Generated User " + index,
                "value": "generated_" + index,
                "avatarUrl": ""
            })
        }
    }

    Theme {
        id: theme
        dark: true
        popupAnimationsEnabled: false
    }
    ListModel {
        id: choices
        ListElement {
            label: "Not assigned"
            value: ""
            avatarUrl: ""
        }
        ListElement {
            label: "Bob Jones"
            value: "bob"
            avatarUrl: ""
        }
        ListElement {
            label: "Alice Smith"
            value: "alice"
            avatarUrl: ""
        }
        ListElement {
            label: "Carl Lead"
            value: "carl"
            avatarUrl: ""
        }
        ListElement {
            label: "Duplicate Bob"
            value: "bob"
            avatarUrl: ""
        }
    }
    UserComboBox {
        id: chooser
        objectName: "testedUserCombo"
        x: 40
        y: 40
        width: 220
        theme: theme
        userModel: testUserProfiles
        model: choices
        textRole: "label"
        valueRole: "value"
        currentIndex: 0
        onActivated: function(index) {
            activatedIndex = index
            activatedValue = String(currentValue || "")
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_UserComboBoxTest.qml")),
        )
        self.owner = self.component.create()
        self.assertIsNotNone(
            self.owner,
            "\n".join(
                error.toString() for error in self.component.errors()
            ),
        )
        QTest.qWait(20)
        self.popup_model = self.owner.findChild(
            QObject, "userComboBoxPopupModel"
        )
        self.assertIsNotNone(self.popup_model)

    def tearDown(self):
        self.owner.close()
        self.owner.deleteLater()
        self.transient_windows = []
        self.engine.deleteLater()

    def test_mouse_click_opens_populated_popup_and_outside_closes_it(self):
        runtime_warnings = []
        self.engine.warnings.connect(
            lambda errors: runtime_warnings.extend(
                error.toString() for error in errors
            )
        )
        QTest.mouseClick(
            self.owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, QPoint(100, 55),
        )
        QTest.qWait(50)

        self.assertTrue(self.owner.property("popupOpened"))
        self.assertEqual(self.popup_model.property("count"), 4)
        self.assertFalse(
            runtime_warnings,
            "\n".join(runtime_warnings),
        )

        QTest.qWait(180)
        QTest.mouseClick(
            self.owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, QPoint(390, 300),
        )
        QTest.qWait(20)
        self.assertFalse(self.owner.property("popupOpened"))

    def test_pointer_press_prepares_users_before_popup_creation(self):
        chooser = self.owner.findChild(QQuickItem, "testedUserCombo")
        self.assertEqual(self.popup_model.property("count"), 0)

        chooser.setProperty("activationPressed", True)

        self.assertEqual(self.popup_model.property("count"), 4)
        chooser.setProperty("activationPressed", False)

    def test_user_popup_is_a_transient_window_not_an_owner_overlay(self):
        QTest.mouseClick(
            self.owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, QPoint(100, 55),
        )
        QTest.qWait(80)

        self.assertTrue(self.owner.property("popupOpened"))
        self.assertTrue(self.owner.property("popupUsesWindow"))
        popup_windows = [
            window
            for window in QGuiApplication.allWindows()
            if window is not self.owner
            and window.isVisible()
            and window.transientParent() is self.owner
        ]
        self.assertEqual(len(popup_windows), 1)
        self.transient_windows = popup_windows
        popup_window = popup_windows[0]
        self.assertGreater(
            popup_window.y() + popup_window.height(),
            self.owner.y() + self.owner.height(),
        )
        QTest.qWait(180)
        QTest.mouseClick(
            self.owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, QPoint(390, 300),
        )
        QTest.qWait(20)

    def test_user_combo_scrollbar_drag_scrolls_popup_list(self):
        self.owner.addGeneratedUsers(24)
        self.owner.openChooser()
        QTest.qWait(80)
        user_list = self.owner.findChild(
            QQuickItem, "userComboBoxPopupList"
        )
        scroll_bar = self.owner.findChild(
            QQuickItem, "userComboBoxScrollBar"
        )
        self.assertIsNotNone(user_list)
        self.assertIsNotNone(scroll_bar)
        self.assertGreater(user_list.property("contentHeight"), user_list.height())
        self.assertTrue(scroll_bar.property("visible"))
        popup_window = scroll_bar.window()
        self.assertIsNotNone(popup_window)
        self.assertIsNot(popup_window, self.owner)

        start = scroll_bar.mapToScene(QPointF(
            scroll_bar.width() / 2,
            max(4, scroll_bar.height() * 0.08),
        )).toPoint()
        end = scroll_bar.mapToScene(QPointF(
            scroll_bar.width() / 2,
            scroll_bar.height() * 0.75,
        )).toPoint()
        before = float(user_list.property("contentY"))
        QTest.mousePress(
            popup_window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, start,
        )
        QTest.mouseMove(popup_window, end, 80)
        QTest.mouseRelease(
            popup_window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, end,
        )
        QTest.qWait(30)
        self.assertGreater(float(user_list.property("contentY")), before + 10)

        user_list.setProperty("contentY", 0)
        QTest.qWait(10)
        touch_device = QTest.createTouchDevice()
        QTest.touchEvent(popup_window, touch_device).press(
            0, start, popup_window
        ).commit()
        QTest.touchEvent(popup_window, touch_device).move(
            0, end, popup_window
        ).commit()
        QTest.touchEvent(popup_window, touch_device).release(
            0, end, popup_window
        ).commit()
        QTest.qWait(30)
        self.assertGreater(float(user_list.property("contentY")), 10)

    def test_fast_selection_does_not_reopen_the_combo_popup(self):
        QTest.mouseClick(
            self.owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, QPoint(100, 55),
        )
        QTest.qWait(50)
        self.assertTrue(self.owner.property("popupOpened"))

        self.owner.activateRow(1)
        QTest.qWait(400)
        self.assertFalse(self.owner.property("popupOpened"))
        self.assertEqual(self.owner.selectedValue(), "alice")

    def test_popup_normalizes_groups_and_preserves_source_index(self):
        self.owner.openChooser()
        QTest.qWait(20)

        self.assertTrue(self.owner.property("popupOpened"))
        self.assertEqual(self.popup_model.property("count"), 4)

        # The normalized popup is grouped, so Alice precedes Bob even though
        # the task-specific choices arrive in the opposite order.
        self.owner.activateRow(1)
        QTest.qWait(10)
        self.assertEqual(self.owner.property("activatedIndex"), 2)
        self.assertEqual(self.owner.property("activatedValue"), "alice")
        self.assertEqual(self.owner.selectedValue(), "alice")

    def test_combo_uses_identity_color_for_current_and_popup_avatar(self):
        chooser = self.owner.findChild(QQuickItem, "testedUserCombo")
        chooser.setProperty("currentIndex", 1)
        QTest.qWait(20)
        current_avatar = self.owner.findChild(
            QQuickItem, "userComboBoxCurrentAvatar"
        )
        self.assertEqual(
            current_avatar.property("accent"), QColor("#42a5f5")
        )

        self.owner.openChooser()
        QTest.qWait(30)
        popup_record = self.popup_model.get(2).toVariant()
        self.assertEqual(
            popup_record.property("avatarColor"), "#42a5f5"
        )

    def test_escape_closes_popup_from_keyboard(self):
        self.owner.openChooser()
        QTest.qWait(40)
        self.assertTrue(self.owner.property("popupOpened"))

        QTest.keyClick(self.owner, Qt.Key_Escape)
        QTest.qWait(30)
        self.assertFalse(self.owner.property("popupOpened"))

    def test_popup_list_accepts_arrows_and_space(self):
        self.owner.openChooser()
        QTest.qWait(20)
        user_list = self.owner.findChild(
            QQuickItem, "userComboBoxPopupList"
        )
        search = self.owner.findChild(
            QQuickItem, "userComboBoxSearchField"
        )
        popup_window = user_list.window()

        search.forceActiveFocus()
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Space)
        QTest.qWait(20)

        self.assertEqual(self.owner.selectedValue(), "alice")
        self.assertFalse(self.owner.property("popupOpened"))

    def test_search_filters_profiles_without_losing_choice_index(self):
        self.owner.openChooser()
        QTest.qWait(20)
        self.owner.searchUsers("bob@test")
        QTest.qWait(10)

        self.assertEqual(self.popup_model.property("count"), 1)
        self.owner.activateRow(0)
        QTest.qWait(10)
        self.assertEqual(self.owner.property("activatedIndex"), 1)
        self.assertEqual(self.owner.property("activatedValue"), "bob")
        self.assertEqual(self.owner.selectedValue(), "bob")

    def test_shared_record_model_populates_the_open_popup(self):
        chooser = self.owner.findChild(QQuickItem, "testedUserCombo")
        chooser.setProperty("model", self.profiles)
        chooser.setProperty("textRole", "displayName")
        chooser.setProperty("valueRole", "login")

        self.owner.openChooser()
        QTest.qWait(30)

        self.assertEqual(self.popup_model.property("count"), 3)
        first_record = self.popup_model.get(0).toVariant()
        self.assertEqual(first_record.property("login"), "alice")

    def test_bulk_assignee_reuses_the_shared_user_selector(self):
        source = (QML / "TaskBulkBar.qml").read_text(encoding="utf-8")
        start = source.index("id: assigneeCombo")
        block = source[max(0, start - 80):source.index(
            "Controls.CompactIconButton", start
        )]
        self.assertIn("UserComboBox {", block)
        self.assertIn("userModel: userListModel", block)
        self.assertNotIn("Controls.ComboBox {", block)

    def test_shared_control_has_no_parallel_delegate_model_filter(self):
        source = (QML / "UserComboBox.qml").read_text(encoding="utf-8")
        self.assertIn("sourceIndex", source)
        self.assertIn("popupUsers", source)
        self.assertIn("seen[identity]", source)
        self.assertNotIn("model: control.delegateModel", source)
        self.assertNotIn("groupHasMatches", source)
        self.assertNotIn("matchesSearch", source)


class UserPickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QGuiApplication.instance() is None:
            QQuickStyle.setStyle("Basic")
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_current_user_remains_visible_but_cannot_be_selected(self):
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl", "avatarColor", "groups",
            "primaryGroup", "current",
        ), [
            {
                "login": "alice",
                "displayName": "Alice Smith",
                "initials": "AS",
                "avatarUrl": "",
                "avatarColor": "#ef5350",
                "groups": ["Solo Group"],
                "primaryGroup": "Solo Group",
                "current": True,
            },
            {
                "login": "bob",
                "displayName": "Bob Jones",
                "initials": "BJ",
                "avatarUrl": "",
                "avatarColor": "#42a5f5",
                "groups": ["Artists"],
                "primaryGroup": "Artists",
                "current": False,
            },
        ])
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty("userListModel", users)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window

Window {
    width: 420
    height: 360
    visible: true
    property int selectionCount: picker.selectedLogins.length
    Theme { id: theme; dark: true }
    UserPicker {
        id: picker
        anchors.fill: parent
        anchors.margins: 12
        theme: theme
        includeCurrent: false
    }
}
''', QUrl.fromLocalFile(str(QML / "_UserPickerTest.qml")))
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        QTest.qWait(50)

        visual_items = [owner.contentItem()]
        for item in visual_items:
            if isinstance(item, QQuickItem):
                visual_items.extend(item.childItems())
        current_row = next((
            item for item in visual_items
            if item.property("login") == "alice"
        ), None)
        current_group = next((
            item for item in visual_items
            if item.objectName() == "userPickerSection_Solo Group"
        ), None)
        marker = next((
            item for item in visual_items
            if item.objectName() == "userPickerCurrentMarker"
            and item.property("visible")
        ), None)
        self.assertIsNotNone(current_row)
        self.assertIsNotNone(current_group)
        self.assertIsNotNone(marker)
        self.assertTrue(current_row.property("visible"))
        self.assertFalse(current_row.property("selectable"))
        self.assertTrue(current_group.property("visible"))
        self.assertTrue(marker.property("visible"))

        center = current_row.mapToScene(QPointF(
            current_row.width() / 2, current_row.height() / 2
        ))
        QTest.mouseClick(
            owner, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        QTest.qWait(10)
        self.assertEqual(owner.property("selectionCount"), 0)

        owner.close()
        owner.deleteLater()
        engine.deleteLater()

    def test_scrollbar_drag_scrolls_the_user_list(self):
        users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl", "avatarColor",
            "groups", "primaryGroup", "current",
        ), [
            {
                "login": f"artist_{index:02d}",
                "displayName": f"Artist {index:02d}",
                "initials": "AR",
                "avatarUrl": "",
                "avatarColor": "#42a5f5",
                "groups": ["Artists"],
                "primaryGroup": "Artists",
                "current": False,
            }
            for index in range(24)
        ])
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty("userListModel", users)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls

Window {
    width: 360
    height: 320
    visible: true
    Theme { id: theme; dark: true }
    Rectangle { id: anchor; width: 32; height: 32 }
    Controls.Popup {
        id: popup
        theme: theme
        width: 340
        height: 280
        padding: 12
        contentItem: UserPicker { theme: theme }
        Component.onCompleted: {
            preparePositionAtItem(anchor, 0, anchor.height)
            open()
        }
    }
}
''', QUrl.fromLocalFile(str(QML / "_UserPickerScrollTest.qml")))
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        QTest.qWait(80)
        user_list = owner.findChild(QQuickItem, "userPickerList")
        scroll_bar = owner.findChild(QQuickItem, "userPickerScrollBar")
        self.assertIsNotNone(user_list)
        self.assertIsNotNone(scroll_bar)
        self.assertGreater(user_list.property("contentHeight"), user_list.height())
        self.assertTrue(scroll_bar.property("visible"))
        popup_window = scroll_bar.window()
        self.assertIsNotNone(popup_window)
        self.assertIsNot(popup_window, owner)

        start = scroll_bar.mapToScene(QPointF(
            scroll_bar.width() / 2,
            max(4, scroll_bar.height() * 0.08),
        )).toPoint()
        end = scroll_bar.mapToScene(QPointF(
            scroll_bar.width() / 2,
            scroll_bar.height() * 0.75,
        )).toPoint()
        before = float(user_list.property("contentY"))
        QTest.mousePress(
            popup_window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, start,
        )
        QTest.mouseMove(popup_window, end, 80)
        QTest.mouseRelease(
            popup_window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, end,
        )
        QTest.qWait(30)
        self.assertGreater(float(user_list.property("contentY")), before + 10)

        owner.close()
        owner.deleteLater()
        engine.deleteLater()


if __name__ == "__main__":
    unittest.main()

