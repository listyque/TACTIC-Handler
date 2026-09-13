from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (
    QMetaObject, QObject, QPoint, QPointF, Qt, QUrl, Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from thlib.ui.pointer import PointerController
from tests.qt_application import gui_test_application

class _TestPointerController(QObject):
    position = {"x": 0.0, "y": 0.0}

    @Slot(result="QVariantMap")
    def global_position(self):
        return self.position

    available_area = {}

    @Slot(float, float, result="QVariantMap")
    def available_geometry_at(self, _x, _y):
        return self.available_area


class PopupWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_pointer_service_returns_available_geometry_for_point(self):
        screen = QGuiApplication.primaryScreen()
        self.assertIsNotNone(screen)
        geometry = screen.availableGeometry()
        center = geometry.center()
        area = PointerController().available_geometry_at(
            center.x(), center.y()
        )

        self.assertEqual(area["x"], float(geometry.x()))
        self.assertEqual(area["y"], float(geometry.y()))
        self.assertEqual(area["width"], float(geometry.width()))
        self.assertEqual(area["height"], float(geometry.height()))

    def test_qml_has_single_native_popup_and_combo_implementation(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        popup_owners = []
        menu_owners = []
        combo_owners = []
        popup_action_owners = []
        for path in qml_dir.rglob("*.qml"):
            source = path.read_text(encoding="utf-8")
            if "QtControls.Popup {" in source:
                popup_owners.append(path.relative_to(qml_dir).as_posix())
            if "QtControls.Menu {" in source:
                menu_owners.append(path.relative_to(qml_dir).as_posix())
            if "QtControls.ComboBox {" in source:
                combo_owners.append(path.relative_to(qml_dir).as_posix())
            if "QtControls.AbstractButton {" in source:
                popup_action_owners.append(
                    path.relative_to(qml_dir).as_posix()
                )

        self.assertEqual(popup_owners, ["controls/Popup.qml"])
        self.assertEqual(menu_owners, ["controls/Menu.qml"])
        self.assertEqual(combo_owners, ["controls/ComboBox.qml"])
        self.assertEqual(
            popup_action_owners, ["controls/PopupAction.qml"]
        )

    def test_popup_content_uses_active_actions_and_shared_scrollbars(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        passive_actions = ("MouseArea {", "ActivationHandler {", "TapHandler {")
        overflow_views = ("ListView {", "GridView {", "Flickable {")
        violations = []

        for path in qml_dir.rglob("*.qml"):
            source = path.read_text(encoding="utf-8")
            for marker in ("Controls.Popup {", "Controls.Menu {", "Controls.ScrollablePopup {"):
                search_from = 0
                while True:
                    start = source.find(marker, search_from)
                    if start < 0:
                        break
                    depth = 0
                    end = start
                    entered = False
                    while end < len(source):
                        character = source[end]
                        if character == "{":
                            depth += 1
                            entered = True
                        elif character == "}":
                            depth -= 1
                            if entered and depth == 0:
                                end += 1
                                break
                        end += 1
                    block = source[start:end]
                    relative = path.relative_to(qml_dir).as_posix()
                    for passive in passive_actions:
                        if passive in block:
                            violations.append(
                                f"{relative}: passive popup action {passive}"
                            )
                    if any(view in block for view in overflow_views):
                        if "Controls.ScrollBar" not in block:
                            violations.append(
                                f"{relative}: popup overflow without shared scrollbar"
                            )
                    search_from = max(end, start + len(marker))

        self.assertEqual(violations, [])

    def test_action_menu_uses_native_popup_grab_without_disabling_its_owner(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 320
    height: 220
    visible: true
    property bool menuUsesWindow:
        actionMenu.popupType === Popup.Window
    property bool menuIsModal: actionMenu.modal
    property bool menuIsDimmed: actionMenu.dim
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: anchor
        x: window.width - 12
        y: window.height - 12
        width: 10
        height: 10
    }
    ActionMenu {
        id: actionMenu
        objectName: "windowedActionMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Open", "icon": "open_in_new", "command": "open"}
        ]
    }
    Component.onCompleted:
        actionMenu.openAt(anchor, anchor.width, anchor.height)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupWindowTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            menu = owner.findChild(QObject, "windowedActionMenu")
            self.assertIsNotNone(menu)
            self.assertTrue(menu.property("opened"))
            self.assertTrue(owner.property("menuUsesWindow"))
            self.assertFalse(owner.property("menuIsModal"))
            self.assertFalse(owner.property("menuIsDimmed"))
            shadow_margin = float(menu.property("effectiveShadowMargin"))
            self.assertGreater(shadow_margin, 0.0)
            surface = owner.findChild(QObject, "popupSurface")
            self.assertIsNotNone(surface)
            self.assertEqual(float(surface.property("x")), shadow_margin)
            self.assertEqual(float(surface.property("y")), shadow_margin)
            self.assertEqual(
                float(surface.property("width")),
                float(menu.property("preferredWidth")),
            )
            self.assertGreater(
                float(menu.property("x")) + float(menu.property("width")),
                float(owner.width()),
            )
            popup_windows = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertTrue(popup_windows)
            popup_image = popup_windows[0].grabWindow()
            self.assertFalse(popup_image.isNull())
            scale = popup_image.width() / popup_windows[0].width()
            surface_pixel = int((shadow_margin + 4) * scale)
            surface_alpha = popup_image.pixelColor(
                popup_image.width() // 2, surface_pixel).alpha()
            self.assertGreater(surface_alpha, 0)
            outer_pixel = int(4 * scale)
            outer_alpha = popup_image.pixelColor(outer_pixel, outer_pixel).alpha()
            self.assertLess(outer_alpha, surface_alpha)
            self.assertTrue(any(
                bool(window.flags() & Qt.WindowType.Popup)
                for window in popup_windows
            ))
            self.assertTrue(all(
                window.modality() == Qt.WindowModality.NonModal
                for window in popup_windows
            ))
            menu.close()
            QTest.qWait(20)
            self.assertTrue(all(
                window.modality() == Qt.WindowModality.NonModal
                for window in popup_windows
            ))
        finally:
            owner.close()
            owner.deleteLater()

    def test_popup_window_is_raised_after_the_opening_input_turn(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import "controls/PopupLogic.js" as PopupLogic
QtObject {
    id: control
    property bool usePopupWindow: true
    property var contentItem: ({})
    property var _popupWindow: null
    property bool _nativeModalityApplied: false
    property bool modal: false
    property bool opened: true
    property bool focus: true
    property int raiseCount: 0
    property QtObject popupWindowProbe: QtObject {
        function raise() { control.raiseCount += 1 }
    }
    Component.onCompleted: PopupLogic.opened(control, popupWindowProbe)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupActivationTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(20)
            self.assertEqual(owner.property("raiseCount"), 1)
        finally:
            owner.deleteLater()

    def test_windowed_action_menu_keeps_its_width_with_a_narrow_parent(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 420
    height: 260
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Item { id: narrowOverlay; width: 1; height: 1 }
    Rectangle {
        id: anchor
        x: 40
        y: 40
        width: 180
        height: 80
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: mouse => menu.openAt(anchor, mouse.x, mouse.y)
        }
    }
    ActionMenu {
        id: menu
        objectName: "narrowParentActionMenu"
        parent: narrowOverlay
        theme: theme
        preferredWidth: 244
        actions: [{
            "title": "Open in Maya", "command": "open",
            "secondaryCommand": "dcc_options:open", "secondaryIcon": "edit"
        }]
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_NarrowParentMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.mouseClick(
                owner, Qt.RightButton, Qt.NoModifier, QPoint(80, 70)
            )
            QTest.qWait(60)
            menu = owner.findChild(QObject, "narrowParentActionMenu")
            self.assertTrue(menu.property("opened"))
            self.assertEqual(
                float(menu.property("width")),
                float(menu.property("preferredWidth"))
                + 2 * float(menu.property("effectiveShadowMargin")),
            )
            popup_window = next(
                window for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            )
            self.assertGreaterEqual(
                popup_window.width(), menu.property("preferredWidth")
            )
        finally:
            owner.close()
            owner.deleteLater()

    def test_process_count_menu_has_anchor_and_zero_publish_badge(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 520
    height: 360
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: anchor
        x: 430
        y: 44
        width: 28
        height: 28
    }
    ActionMenu {
        id: actionMenu
        objectName: "processCountActionMenu"
        parent: window.contentItem
        theme: theme
        usePopupWindow: false
        preferredWidth: 212
        processPickerStyle: true
        alignBelowRight: true
        belowRightOverhang: 12
        anchorPointerVisible: true
        actions: [
            {"title": "Messages", "header": true},
            {
                "title": "Publish", "command": "publish",
                "accent": "#78909c", "badgeCount": 0,
                "showZeroBadge": true, "badgeUpdated": false
            },
            {
                "title": "Model", "command": "model",
                "accent": "#ef5350", "badgeCount": 2,
                "badgeUpdated": true
            }
        ]
    }
    Component.onCompleted: actionMenu.openBelow(anchor)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_ProcessCountMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(60)
            menu = owner.findChild(QObject, "processCountActionMenu")
            self.assertIsNotNone(menu)
            self.assertTrue(menu.property("opened"))
            pointer = owner.findChild(QObject, "popupAnchorPointer")
            self.assertIsNotNone(pointer)
            self.assertTrue(pointer.property("visible"))
            self.assertGreater(
                float(pointer.property("width")),
                float(pointer.property("height")) * 2,
            )
            self.assertLess(float(pointer.property("height")), 8)
            self.assertGreater(
                float(menu.property("anchorPointerCenter")),
                float(menu.property("width")) * 0.7,
            )
            flickable = owner.findChild(QObject, "actionMenuFlickable")
            scroll_bar = owner.findChild(QObject, "actionMenuScrollBar")
            self.assertIsNotNone(flickable)
            self.assertIsNotNone(scroll_bar)
            self.assertLessEqual(
                float(flickable.property("contentHeight")),
                float(flickable.property("height")) + 0.5,
            )
            self.assertFalse(scroll_bar.property("visible"))
            self.assertFalse(flickable.property("interactive"))
            def visual_descendants(item):
                result = []
                for child in item.childItems():
                    result.append(child)
                    result.extend(visual_descendants(child))
                return result

            content_item = menu.property("contentItem")
            badges = [
                item for item in visual_descendants(content_item)
                if item.objectName() == "actionMenuBadge"
                and item.property("visible")
            ]
            self.assertEqual(
                sorted(int(badge.property("countValue")) for badge in badges),
                [0, 2],
            )
            self.assertTrue(all(
                int(badge.property("height")) == 20 for badge in badges
            ))
            row_surfaces = [
                item for item in visual_descendants(content_item)
                if item.objectName() == "actionMenuRowSurface"
                and item.property("visible")
            ]
            self.assertEqual(len(row_surfaces), 2)
            self.assertTrue(all(
                int(surface.property("height")) == 32
                for surface in row_surfaces
            ))
        finally:
            owner.close()
            owner.deleteLater()

    def test_compact_entity_action_uses_its_icon_and_accent(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    width: 360
    height: 240
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    ActionMenu {
        id: actionMenu
        objectName: "entityActionMenu"
        parent: Overlay.overlay
        theme: theme
        usePopupWindow: false
        preferredWidth: 212
        processPickerStyle: true
        actions: [{
            "title": "Episode", "command": "episode",
            "icon": "film", "accent": "#42a5f5",
            "accentIcon": true, "translate": false
        }]
    }
    Component.onCompleted: actionMenu.open()
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_EntityActionMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(40)
            repeater = owner.findChild(QObject, "actionMenuRepeater")
            self.assertIsNotNone(repeater)
            self.assertEqual(repeater.property("count"), 1)
            row_expression = QQmlExpression(
                engine.rootContext(), repeater, "itemAt(0)"
            )
            row, undefined = row_expression.evaluate()
            self.assertFalse(row_expression.hasError())
            self.assertFalse(undefined)
            self.assertIsNotNone(row)
            icon = row.findChild(QObject, "actionMenuIcon")
            marker = row.findChild(QObject, "actionMenuAccentMarker")
            self.assertIsNotNone(icon)
            self.assertIsNotNone(marker)
            self.assertTrue(icon.property("visible"))
            self.assertEqual(icon.property("name"), "film")
            self.assertEqual(icon.property("color").name(), "#42a5f5")
            self.assertFalse(marker.property("visible"))
            action_menu = owner.findChild(QObject, "entityActionMenu")
            action_menu.close()
            self.assertFalse(action_menu.property("visible"))
            self.assertEqual(repeater.property("count"), 1)
            self.assertFalse(row.isVisible())
        finally:
            owner.close()
            owner.deleteLater()

    def test_action_menu_is_clamped_to_anchor_screen_available_area(self):
        engine = QQmlEngine()
        pointer_controller = _TestPointerController()
        pointer_controller.position = {"x": 350.0, "y": 250.0}
        pointer_controller.available_area = {
            "x": 100.0, "y": 80.0, "width": 260.0, "height": 180.0,
        }
        engine.rootContext().setContextProperty(
            "pointerController", pointer_controller
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    x: 100
    y: 80
    width: 260
    height: 180
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: anchor
        x: window.width - 10
        y: window.height - 10
        width: 8
        height: 8
    }
    ActionMenu {
        id: actionMenu
        objectName: "edgeActionMenu"
        parent: window.contentItem
        theme: theme
        preferredWidth: 160
        actions: [
            {"title": "Open", "icon": "open_in_new", "command": "open"},
            {"title": "Edit", "icon": "edit", "command": "edit"},
            {"title": "Delete", "icon": "delete", "command": "delete"}
        ]
    }
    function openAtEdge() {
        actionMenu.openAt(anchor, anchor.width, anchor.height)
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupScreenEdgeTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertTrue(QMetaObject.invokeMethod(owner, "openAtEdge"))
            QTest.qWait(100)
            menu = owner.findChild(QObject, "edgeActionMenu")
            self.assertTrue(menu.property("opened"))
            popup = next(
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            )
            area = pointer_controller.available_area
            margin = 4
            self.assertGreaterEqual(popup.x(), area["x"] + margin)
            self.assertGreaterEqual(popup.y(), area["y"] + margin)
            self.assertLessEqual(
                popup.x() + popup.width(),
                area["x"] + area["width"] - margin,
            )
            self.assertLessEqual(
                popup.y() + popup.height(),
                area["y"] + area["height"] - margin,
            )
        finally:
            owner.close()
            owner.deleteLater()
    def test_long_action_menu_is_limited_to_screen_and_scrollable(self):
        engine = QQmlEngine()
        pointer_controller = _TestPointerController()
        pointer_controller.position = {"x": 220.0, "y": 150.0}
        pointer_controller.available_area = {
            "x": 100.0, "y": 80.0, "width": 260.0, "height": 180.0,
        }
        engine.rootContext().setContextProperty(
            "pointerController", pointer_controller
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    x: 100
    y: 80
    width: 260
    height: 180
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle { id: anchor; x: 120; y: 80; width: 8; height: 8 }
    ActionMenu {
        id: actionMenu
        objectName: "longActionMenu"
        parent: window.contentItem
        theme: theme
        preferredWidth: 180
        actions: [
            {"title": "One", "command": "1"},
            {"title": "Two", "command": "2"},
            {"title": "Three", "command": "3"},
            {"title": "Four", "command": "4"},
            {"title": "Five", "command": "5"},
            {"title": "Six", "command": "6"},
            {"title": "Seven", "command": "7"},
            {"title": "Eight", "command": "8"},
            {"title": "Nine", "command": "9"},
            {"title": "Ten", "command": "10"}
        ]
    }
    Component.onCompleted: actionMenu.openAt(anchor, 0, 0)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_LongPopupMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(100)
            menu = owner.findChild(QObject, "longActionMenu")
            flickable = owner.findChild(QObject, "actionMenuFlickable")
            scroll_bar = owner.findChild(QObject, "actionMenuScrollBar")
            self.assertIsNotNone(menu)
            self.assertIsNotNone(flickable)
            self.assertIsNotNone(scroll_bar)
            self.assertLessEqual(
                float(menu.property("height")),
                pointer_controller.available_area["height"] - 8,
            )
            self.assertGreater(
                float(flickable.property("contentHeight")),
                float(flickable.property("height")),
            )
            self.assertTrue(scroll_bar.property("visible"))
            self.assertTrue(flickable.property("interactive"))
            popup = next(
                window for window in QGuiApplication.allWindows()
                if window is not owner and window.isVisible()
                and window.transientParent() is owner
            )
            self.assertLessEqual(
                popup.y() + popup.height(),
                pointer_controller.available_area["y"]
                + pointer_controller.available_area["height"] - 4,
            )
        finally:
            owner.close()
            owner.deleteLater()

    def test_windowed_action_menu_uses_available_screen_before_scrolling(self):
        engine = QQmlEngine()
        pointer_controller = _TestPointerController()
        pointer_controller.position = {"x": 220.0, "y": 50.0}
        pointer_controller.available_area = {
            "x": 0.0, "y": 0.0, "width": 1000.0, "height": 720.0,
        }
        engine.rootContext().setContextProperty(
            "pointerController", pointer_controller
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 500
    height: 620
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle { id: anchor; x: 210; y: 40; width: 20; height: 20 }
    ActionMenu {
        id: actionMenu
        objectName: "screenHeightActionMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "One", "command": "1"},
            {"title": "Two", "command": "2"},
            {"title": "Three", "command": "3"},
            {"title": "Four", "command": "4"},
            {"title": "Five", "command": "5"},
            {"title": "Six", "command": "6"},
            {"title": "Seven", "command": "7"},
            {"separator": true},
            {"title": "Eight", "command": "8"},
            {"title": "Nine", "command": "9"},
            {"title": "Ten", "command": "10"},
            {"title": "Eleven", "command": "11"},
            {"title": "Twelve", "command": "12"},
            {"title": "Thirteen", "command": "13"},
            {"title": "Fourteen", "command": "14"},
            {"separator": true},
            {"title": "Fifteen", "command": "15"}
        ]
    }
    Component.onCompleted: actionMenu.openAt(anchor, 0, 0)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_ScreenHeightMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(100)
            menu = owner.findChild(QObject, "screenHeightActionMenu")
            flickable = owner.findChild(QObject, "actionMenuFlickable")
            scroll_bar = owner.findChild(QObject, "actionMenuScrollBar")
            self.assertIsNotNone(menu)
            self.assertIsNotNone(flickable)
            self.assertIsNotNone(scroll_bar)
            self.assertGreater(float(menu.property("height")), 612.0)
            self.assertLessEqual(
                float(flickable.property("contentHeight")),
                float(flickable.property("height")) + 0.5,
            )
            self.assertFalse(scroll_bar.property("visible"))
            self.assertFalse(flickable.property("interactive"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_reopening_an_open_menu_uses_the_new_anchor_position(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 520
    height: 260
    x: 310
    y: 170
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: firstAnchor
        objectName: "firstAnchor"
        x: 32
        y: 42
        width: 10
        height: 10
    }
    Rectangle {
        id: secondAnchor
        objectName: "secondAnchor"
        x: 224
        y: 142
        width: 10
        height: 10
    }
    ActionMenu {
        id: actionMenu
        objectName: "repositionedActionMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Open", "icon": "open_in_new", "command": "open"}
        ]
    }
    function openSecond() {
        actionMenu.openAt(secondAnchor, 0, 0)
    }
    Component.onCompleted:
        actionMenu.openAt(firstAnchor, 0, 0)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupRepositionTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            menu = owner.findChild(QObject, "repositionedActionMenu")
            self.assertIsNotNone(menu)
            first_windows = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertEqual(len(first_windows), 1)
            first_x = first_windows[0].x()
            first_y = first_windows[0].y()
            self.assertTrue(QMetaObject.invokeMethod(owner, "openSecond"))
            QTest.qWait(100)
            second_windows = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertEqual(len(second_windows), 1)
            self.assertTrue(menu.property("opened"))
            self.assertGreater(second_windows[0].x(), first_x + 100)
            self.assertGreater(second_windows[0].y(), first_y + 50)
            self.assertAlmostEqual(
                float(menu.property("x")),
                224.0 - float(menu.property("effectiveShadowMargin")),
                delta=2.0,
            )
            self.assertAlmostEqual(
                float(menu.property("y")),
                142.0 - float(menu.property("effectiveShadowMargin")),
                delta=2.0,
            )
            self.assertAlmostEqual(
                float(second_windows[0].x()),
                float(owner.x()) + 224.0
                    - float(menu.property("effectiveShadowMargin")),
                delta=3.0,
            )
            self.assertAlmostEqual(
                float(second_windows[0].y()),
                float(owner.y()) + 142.0
                    - float(menu.property("effectiveShadowMargin")),
                delta=3.0,
            )
            menu.close()
        finally:
            owner.close()
            owner.deleteLater()

    def test_second_right_click_moves_shared_menu_to_the_new_item(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    x: 180
    y: 120
    width: 520
    height: 300
    visible: true
    function openSobjectMenu() {
        actionMenu.actions = [
            {"title": "Open", "icon": "open_in_new", "command": "open"},
            {"separator": true},
            {"title": "Advanced", "icon": "edit", "command": "advanced",
             "advanced": true}
        ]
        actionMenu.openAt(firstItem, 32, 24, false)
    }
    function openSnapshotMenu() {
        actionMenu.actions = [
            {"title": "Open scene", "icon": "deployed_code", "command": "open",
             "secondaryCommand": "open_options", "secondaryIcon": "edit"},
            {"title": "Open folder", "icon": "folder", "command": "folder"}
        ]
        actionMenu.openAt(secondItem, 32, 24, false)
    }

    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: firstItem
        x: 28
        y: 36
        width: 170
        height: 54
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: mouse =>
                actionMenu.openAt(firstItem, mouse.x, mouse.y)
        }
    }
    Rectangle {
        id: secondItem
        x: 248
        y: 156
        width: 170
        height: 54
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: mouse =>
                actionMenu.openAt(secondItem, mouse.x, mouse.y)
        }
    }
    ActionMenu {
        id: actionMenu
        objectName: "rightClickActionMenu"
        parent: window.contentItem
        theme: theme
        actions: []
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupRightClickTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )

        def menu_geometry(title):
            menu = owner.findChild(QObject, "rightClickActionMenu")
            def visual_children(item):
                for child in item.childItems():
                    yield child
                    yield from visual_children(child)

            label = next(
                item for item in visual_children(menu.property("contentItem"))
                if item.objectName() == "actionMenuTitleLabel"
                and item.property("text") == title
            )
            row = label.parentItem().parentItem().parentItem()
            text_x = label.mapToItem(
                menu.property("contentItem"), QPointF()
            ).x()
            return menu.property("padding"), row.height(), text_x

        try:
            self.assertTrue(QMetaObject.invokeMethod(owner, "openSobjectMenu"))
            QTest.qWait(60)
            menu = owner.findChild(QObject, "rightClickActionMenu")
            self.assertTrue(menu.property("opened"))
            sobject_geometry = menu_geometry("Open")
            popup = next(
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            )
            first_position = QPoint(popup.x(), popup.y())

            menu.close()
            QTest.qWait(80)
            self.assertFalse(menu.property("opened"))

            self.assertTrue(QMetaObject.invokeMethod(owner, "openSnapshotMenu"))
            QTest.qWait(80)
            visible_popups = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertEqual(len(visible_popups), 1)
            self.assertTrue(menu.property("opened"))
            self.assertEqual(
                float(menu.property("width")),
                float(menu.property("preferredWidth"))
                + 2 * float(menu.property("effectiveShadowMargin")),
            )
            self.assertGreaterEqual(
                float(visible_popups[0].width()),
                float(menu.property("preferredWidth")),
            )
            self.assertEqual(
                menu_geometry("Open scene"), sobject_geometry
            )
            self.assertGreater(
                visible_popups[0].x(), first_position.x() + 150
            )
            self.assertGreater(
                visible_popups[0].y(), first_position.y() + 70
            )
            menu.close()
            QTest.qWait(20)
        finally:
            owner.close()
            owner.deleteLater()

    def test_reopening_never_exposes_two_transient_popup_windows(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
Window {
    id: window
    width: 520
    height: 260
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle { id: firstAnchor; x: 32; y: 42; width: 10; height: 10 }
    Rectangle { id: secondAnchor; x: 224; y: 142; width: 10; height: 10 }
    ActionMenu {
        id: actionMenu
        objectName: "firstRaceMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Open", "icon": "open_in_new", "command": "open"}
        ]
    }
    ActionMenu {
        id: secondMenu
        objectName: "secondRaceMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Edit", "icon": "edit", "command": "edit"}
        ]
    }
    function openFirst() { actionMenu.openAt(firstAnchor, 0, 0) }
    function openRace() {
        actionMenu.openAt(secondAnchor, 0, 0)
        secondMenu.openAt(secondAnchor, 0, 0)
    }
    Component.onCompleted: openFirst()
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupNoDuplicateTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(50)
            first_menu = owner.findChild(QObject, "firstRaceMenu")
            second_menu = owner.findChild(QObject, "secondRaceMenu")
            self.assertIsNotNone(first_menu)
            self.assertIsNotNone(second_menu)
            for _ in range(6):
                self.assertTrue(QMetaObject.invokeMethod(owner, "openRace"))
                for wait_ms in (0, 1, 4, 12):
                    QTest.qWait(wait_ms)
                    visible_popups = [
                        window
                        for window in QGuiApplication.allWindows()
                        if window is not owner
                        and window.isVisible()
                        and window.transientParent() is owner
                    ]
                    self.assertLessEqual(len(visible_popups), 1)
                self.assertFalse(first_menu.property("opened"))
                self.assertTrue(second_menu.property("opened"))
                self.assertTrue(QMetaObject.invokeMethod(owner, "openFirst"))
                QTest.qWait(4)
        finally:
            owner.close()
            owner.deleteLater()

    def test_combo_box_popup_is_a_transient_window_beyond_owner_bounds(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    x: 100
    y: 100
    width: 360
    height: 220
    visible: true
    property bool popupOpened: combo.popup.opened
    property bool popupUsesWindow: combo.popup.popupType === Popup.Window
    property bool popupVisible: combo.popup.visible
    property real popupWidth: combo.popup.width
    property real popupHeight: combo.popup.height
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.ComboBox {
        id: combo
        objectName: "nativeComboBox"
        x: 40
        y: 180
        width: 180
        theme: theme
        model: [
            "Local Python", "DCC Python", "Server Python", "JavaScript",
            "Server JS", "Expression", "XML"
        ]
    }
    Component.onCompleted: combo.popup.open()
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_ComboPopupWindowTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            self.assertTrue(owner.property("popupOpened"))
            self.assertTrue(owner.property("popupUsesWindow"))
            self.assertTrue(owner.property("popupVisible"))
            self.assertGreaterEqual(float(owner.property("popupWidth")), 180.0)
            self.assertGreater(float(owner.property("popupHeight")), 8.0)
            options = owner.findChild(QObject, "comboBoxPopupList")
            self.assertIsNotNone(options)
            self.assertEqual(int(options.property("count")), 7)
            self.assertGreater(float(options.property("height")), 0.0)
            self.assertGreater(float(options.property("contentHeight")), 0.0)
            self.assertGreaterEqual(
                float(options.property("height")),
                float(options.property("contentHeight")),
            )
            popup_windows = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertEqual(len(popup_windows), 1)
            popup_window = popup_windows[0]
            self.assertGreater(
                popup_window.y() + popup_window.height(),
                owner.y() + owner.height(),
            )
            surface = owner.findChild(QObject, "popupSurface")
            self.assertIsNotNone(surface)
            self.assertEqual(float(surface.property("x")), 12.0)
            self.assertEqual(float(surface.property("y")), 12.0)
            self.assertEqual(
                float(surface.property("width")),
                float(owner.property("popupWidth")) - 24,
            )
        finally:
            owner.close()
            owner.deleteLater()

    def test_clicking_neighbor_combo_keeps_new_popup_open(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 520
    height: 240
    visible: true
    property bool firstOpened: first.popup.opened
    property bool secondOpened: second.popup.opened
    property int firstOpenCount: 0
    property int secondOpenCount: 0
    property int firstCloseCount: 0
    property int secondCloseCount: 0
    function openFirst() { first.popup.open() }
    function closeSecond() { second.popup.close() }
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.ComboBox {
        id: first
        x: 40
        y: 30
        width: 180
        theme: theme
        model: ["One", "Two"]
        popup.onOpened: window.firstOpenCount += 1
        popup.onClosed: window.firstCloseCount += 1
    }
    Controls.ComboBox {
        id: second
        x: 280
        y: 30
        width: 180
        theme: theme
        model: ["Alpha", "Beta"]
        popup.onOpened: window.secondOpenCount += 1
        popup.onClosed: window.secondCloseCount += 1
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_NeighborComboTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertTrue(QMetaObject.invokeMethod(owner, "openFirst"))
            QTest.qWait(50)
            self.assertTrue(owner.property("firstOpened"))

            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(340, 50)
            )
            QTest.qWait(80)

            self.assertFalse(owner.property("firstOpened"))
            self.assertTrue(owner.property("secondOpened"))
            QTest.qWait(400)
            self.assertFalse(owner.property("firstOpened"))
            self.assertTrue(owner.property("secondOpened"))
            self.assertEqual(owner.property("firstOpenCount"), 1)
            self.assertEqual(owner.property("secondCloseCount"), 0)
            self.assertEqual(owner.property("secondOpenCount"), 1)

            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(100, 50)
            )
            QTest.qWait(400)
            self.assertTrue(owner.property("firstOpened"))
            self.assertFalse(owner.property("secondOpened"))
            self.assertEqual(owner.property("firstOpenCount"), 2)
            self.assertEqual(owner.property("secondOpenCount"), 1)
            self.assertEqual(owner.property("firstCloseCount"), 1)

            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(340, 50)
            )
            QTest.qWait(400)
            self.assertFalse(owner.property("firstOpened"))
            self.assertTrue(owner.property("secondOpened"))
            self.assertEqual(owner.property("firstOpenCount"), 2)
            self.assertEqual(owner.property("secondOpenCount"), 2)
            self.assertEqual(owner.property("secondCloseCount"), 1)

            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(340, 50)
            )
            QTest.qWait(250)
            self.assertFalse(owner.property("secondOpened"))

        finally:
            owner.close()
            owner.deleteLater()

    def test_quick_filter_chip_activates_inside_native_popup_window(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 420
    height: 300
    visible: true
    property int filterActivations: 0
    property int underlyingActivations: 0
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: anchor
        x: 30
        y: 30
        width: 40
        height: 36
    }
    MouseArea {
        anchors.fill: parent
        onClicked: window.underlyingActivations += 1
    }
    Controls.ScrollablePopup {
        id: popup
        objectName: "quickFilterProbePopup"
        parent: window.contentItem
        theme: theme
        preferredSurfaceWidth: 320
        maximumSurfaceHeight: 160
        QuickFilterChip {
            id: chip
            objectName: "nativePopupQuickFilterChip"
            width: 180
            height: 32
            theme: theme
            text: "Lighting"
            onClicked: window.filterActivations += 1
        }
        Repeater {
            model: 12
            delegate: Rectangle {
                required property int index
                width: parent.width
                height: 30
                color: index % 2 ? theme.surfaceContainerHigh
                    : theme.surfaceContainer
            }
        }
    }
    Component.onCompleted: popup.openBelowItem(anchor, false, 6)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_QuickFilterPopupTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            popup = owner.findChild(QObject, "quickFilterProbePopup")
            chip = owner.findChild(QQuickItem, "nativePopupQuickFilterChip")
            self.assertIsNotNone(popup)
            self.assertIsNotNone(chip)
            self.assertTrue(popup.property("opened"))
            viewport = owner.findChild(QObject, "scrollablePopupViewport")
            scroll_bar = owner.findChild(
                QObject, "scrollablePopupScrollBar"
            )
            content_column = owner.findChild(
                QObject, "scrollablePopupContent"
            )
            self.assertIsNotNone(viewport)
            self.assertIsNotNone(scroll_bar)
            self.assertIsNotNone(content_column)
            self.assertLessEqual(float(popup.property("surfaceHeight")), 160.0)
            self.assertGreater(
                float(viewport.property("contentHeight")),
                float(viewport.property("height")),
            )
            self.assertTrue(scroll_bar.property("visible"))
            self.assertLess(
                float(content_column.property("width")),
                float(viewport.property("width")),
            )
            popup_window = chip.window()
            self.assertIsNotNone(popup_window)
            self.assertIsNot(popup_window, owner)
            click_point = chip.mapToScene(QPointF(
                chip.width() / 2, chip.height() / 2
            )).toPoint()

            QTest.mouseClick(
                popup_window, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, click_point,
            )
            QTest.qWait(30)

            self.assertEqual(owner.property("filterActivations"), 1)
            self.assertEqual(owner.property("underlyingActivations"), 0)
            self.assertTrue(popup.property("opened"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_popup_toggle_does_not_reopen_from_same_pointer_release(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 360
    height: 220
    visible: true
    property bool popupOpened: popup.opened
    property int popupOpenCount: 0
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Button {
        id: sourceButton
        objectName: "unguardedPopupButton"
        x: 40
        y: 30
        width: 150
        height: 40
        text: "Filters"
        onClicked: popup.toggleBelowItem(sourceButton, false, 6)
    }
    Controls.Popup {
        id: popup
        parent: window.contentItem
        theme: theme
        width: 220
        height: 120
        onOpened: window.popupOpenCount += 1
    }
    Component.onCompleted: popup.openBelowItem(sourceButton, false, 6)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_PopupSameSourceTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            self.assertTrue(owner.property("popupOpened"))
            self.assertEqual(owner.property("popupOpenCount"), 1)

            QTest.mouseClick(
                owner, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier, QPoint(110, 50),
            )
            QTest.qWait(250)

            self.assertFalse(owner.property("popupOpened"))
            self.assertEqual(owner.property("popupOpenCount"), 1)
        finally:
            owner.close()
            owner.deleteLater()

    def test_scrollable_popup_clamps_to_a_narrow_owner(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 250
    height: 230
    visible: true
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle { id: anchor; x: 190; y: 20; width: 40; height: 36 }
    Controls.ScrollablePopup {
        id: popup
        objectName: "narrowScrollablePopup"
        parent: window.contentItem
        theme: theme
        preferredSurfaceWidth: 440
        minimumSurfaceWidth: 280
        maximumSurfaceHeight: 150
        Repeater {
            model: 20
            delegate: Rectangle {
                required property int index
                width: parent.width
                height: 28
                color: index % 2 ? theme.row : theme.panelRaised
            }
        }
    }
    Component.onCompleted: popup.openBelowItem(anchor, true, 6)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_NarrowPopupTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            popup = owner.findChild(QObject, "narrowScrollablePopup")
            viewport = owner.findChild(QObject, "scrollablePopupViewport")
            content_column = owner.findChild(
                QObject, "scrollablePopupContent"
            )
            self.assertIsNotNone(popup)
            self.assertTrue(popup.property("opened"))
            self.assertLessEqual(float(popup.property("width")), 242.0)
            self.assertLessEqual(float(popup.property("surfaceHeight")), 150.0)
            self.assertGreater(float(content_column.property("width")), 0.0)
            self.assertLess(
                float(content_column.property("width")),
                float(viewport.property("width")),
            )
        finally:
            owner.close()
            owner.deleteLater()

    def test_fixed_height_popup_does_not_grow_after_model_update(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 640
    height: 520
    visible: true
    property int tagCount: 0
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle { id: anchor; x: 40; y: 30; width: 40; height: 36 }
    Controls.ScrollablePopup {
        id: popup
        objectName: "dynamicFixedPopup"
        parent: window.contentItem
        theme: theme
        preferredSurfaceWidth: 360
        fixedSurfaceHeight: 180
        Repeater {
            model: window.tagCount
            delegate: Rectangle {
                required property int index
                width: parent.width
                height: 30
                color: index % 2 ? theme.row : theme.panelRaised
            }
        }
    }
    Component.onCompleted: popup.openBelowItem(anchor, false, 6)
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_FixedPopupTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            popup = owner.findChild(QObject, "dynamicFixedPopup")
            viewport = owner.findChild(QObject, "scrollablePopupViewport")
            self.assertIsNotNone(popup)
            self.assertEqual(float(popup.property("surfaceHeight")), 180.0)

            owner.setProperty("tagCount", 120)
            QTest.qWait(120)

            self.assertEqual(float(popup.property("surfaceHeight")), 180.0)
            self.assertGreater(
                float(viewport.property("contentHeight")),
                float(viewport.property("height")),
            )
        finally:
            owner.close()
            owner.deleteLater()

    def test_nested_combo_replaces_sibling_without_closing_parent_popup(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 620
    height: 360
    visible: true
    property bool outerOpened: outer.opened
    property bool firstOpened: first.popup.opened
    property bool secondOpened: second.popup.opened
    property bool outsideOpened: outside.popup.opened
    function openOuter() { outer.openCenteredIn(window.contentItem) }
    function openFirst() { first.popup.open() }
    function openSecond() { second.popup.open() }
    function openOutside() { outside.popup.open() }
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.ComboBox {
        id: outside
        x: 30
        y: 20
        width: 180
        theme: theme
        model: ["Outside one", "Outside two"]
    }
    Controls.Popup {
        id: outer
        parent: window.contentItem
        theme: theme
        width: 430
        height: 190
        contentItem: Item {
            Controls.ComboBox {
                id: first
                x: 24
                y: 30
                width: 175
                theme: window.theme
                model: ["One", "Two"]
            }
            Controls.ComboBox {
                id: second
                x: 225
                y: 30
                width: 175
                theme: window.theme
                model: ["Alpha", "Beta"]
            }
        }
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_NestedPopupBranchTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertTrue(QMetaObject.invokeMethod(owner, "openOuter"))
            QTest.qWait(50)
            self.assertTrue(owner.property("outerOpened"))

            self.assertTrue(QMetaObject.invokeMethod(owner, "openFirst"))
            QTest.qWait(80)
            self.assertTrue(owner.property("outerOpened"))
            self.assertTrue(owner.property("firstOpened"))

            self.assertTrue(QMetaObject.invokeMethod(owner, "openSecond"))
            QTest.qWait(100)
            self.assertTrue(owner.property("outerOpened"))
            self.assertFalse(owner.property("firstOpened"))
            self.assertTrue(owner.property("secondOpened"))

            self.assertTrue(QMetaObject.invokeMethod(owner, "openOutside"))
            QTest.qWait(100)
            self.assertFalse(owner.property("outerOpened"))
            self.assertFalse(owner.property("secondOpened"))
            self.assertTrue(owner.property("outsideOpened"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_combo_popup_closes_neighbors_on_press_not_release(self):
        combo = (
            Path(__file__).parents[1]
            / "thlib" / "ui" / "qml" / "controls" / "ComboBox.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("settledClosePolicy: QtControls.Popup.CloseOnEscape", combo)
        self.assertIn("QtControls.Popup.CloseOnPressOutside", combo)
        self.assertNotIn("CloseOnReleaseOutside", combo)
        self.assertNotIn("popupOpeningReleaseProtected", combo)
        self.assertNotIn("QtControls.Popup.NoAutoClose", combo)

    def test_shared_popup_window_default_and_shadow_margin(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        action_menu = (qml_dir / "ActionMenu.qml").read_text(
            encoding="utf-8"
        )
        dock_menu = (qml_dir / "DockMenu.qml").read_text(
            encoding="utf-8"
        )
        text_menu = (
            qml_dir / "controls" / "TextContextMenu.qml"
        ).read_text(encoding="utf-8")
        popup = (qml_dir / "controls" / "Popup.qml").read_text(
            encoding="utf-8"
        )
        combo = (qml_dir / "controls" / "ComboBox.qml").read_text(
            encoding="utf-8"
        )
        background = (qml_dir / "controls" / "PopupBackground.qml").read_text(
            encoding="utf-8"
        )
        menu = (qml_dir / "controls" / "Menu.qml").read_text(encoding="utf-8")

        self.assertIn("property bool usePopupWindow: true", popup)
        self.assertIn("QtControls.Popup.Window", popup)
        self.assertIn("property real shadowMargin: 12", popup)
        self.assertIn(
            "anchors.leftMargin: popup.effectiveShadowMargin", background
        )
        self.assertIn(
            "anchors.topMargin: popup.effectiveShadowMargin", background
        )
        self.assertIn("property bool anchorPointerVisible: false", popup)
        self.assertIn("function prepareGlobalPosition", popup)
        self.assertIn("function openBelowItem", popup)
        self.assertNotIn("popupWindow.x =", popup)
        self.assertNotIn("popupWindow.y =", popup)
        self.assertNotIn("function applyWindowPosition", popup)
        self.assertNotIn("function scheduleWindowPlacement", popup)
        self.assertIn("ActionMenu {", dock_menu)
        self.assertIn("Controls.Menu {", action_menu)
        self.assertIn("modal: false", action_menu)
        self.assertIn("modal: false", menu)
        for source in (popup, menu):
            self.assertIn("PopupLogic.aboutToShow(control)", source)
            self.assertIn("Controls.PopupBackground { popup: control }", source)
        for source in (action_menu, text_menu):
            self.assertIn("usePopupWindow: true", source)
            self.assertIn("dim: false", source)
        self.assertIn("usePopupWindow: true", combo)
        self.assertIn("coordinateGlobally: true", combo)
        self.assertIn("preparePositionAtItem", combo)
        self.assertIn("cancelOpeningRecovery", combo)
        self.assertNotIn("restorePopupAfterDuplicateClose", combo)
        self.assertNotIn("_touchOpenGuardUntil", combo)

    def test_right_click_inside_text_selection_preserves_selection(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        for control_name, control_height, click_y in (
                ("TextField", 44, 42), ("TextArea", 88, 38)):
            with self.subTest(control=control_name):
                engine = QQmlEngine()
                engine.addImportPath(str(qml_dir))
                component = QQmlComponent(engine)
                source = '''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 340
    height: 150
    visible: true
    property string currentSelection: editor.selectedText
    function selectWord() { editor.select(0, 5) }
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.%s {
        id: editor
        objectName: "selectionEditor"
        x: 20
        y: 20
        width: 300
        height: %d
        theme: theme
        text: "alpha beta gamma"
    }
}
''' % (control_name, control_height)
                component.setData(
                    source.encode("utf-8"),
                    QUrl.fromLocalFile(str(qml_dir / "_TextSelectionTest.qml")),
                )
                window = component.create()
                self.assertIsNotNone(
                    window,
                    "\n".join(
                        error.toString() for error in component.errors()
                    ),
                )
                try:
                    editor = window.findChild(QObject, "selectionEditor")
                    self.assertIsNotNone(editor)
                    self.assertTrue(editor.property("persistentSelection"))
                    self.assertTrue(
                        QMetaObject.invokeMethod(window, "selectWord")
                    )
                    self.assertEqual(window.property("currentSelection"), "alpha")

                    QTest.mouseClick(
                        window,
                        Qt.RightButton,
                        Qt.NoModifier,
                        QPoint(44, click_y),
                    )
                    QTest.qWait(50)

                    self.assertEqual(
                        window.property("currentSelection"), "alpha"
                    )
                finally:
                    window.close()
                    window.deleteLater()
                    QTest.qWait(10)


    def test_right_click_action_menu_dispatches_mouse_selection(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    id: window
    width: 420
    height: 260
    visible: true
    property string triggeredCommand: ""
    property bool menuOpenWhenTriggered: true
    property int underlyingClicks: 0
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Rectangle {
        id: item
        x: 40
        y: 40
        width: 180
        height: 80
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton)
                    menu.openAt(item, mouse.x, mouse.y)
                else
                    window.underlyingClicks += 1
            }
        }
    }
    ActionMenu {
        id: menu
        objectName: "sobjectContextMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Save snapshot", "icon": "save", "command": "save"}
        ]
        onTriggered: function(command) {
            window.menuOpenWhenTriggered = menu.opened
            window.triggeredCommand = command
        }
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_SObjectContextMouseTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(40)
            QTest.mouseClick(
                owner, Qt.RightButton, Qt.NoModifier, QPoint(80, 70)
            )
            QTest.qWait(80)
            menu = owner.findChild(QObject, "sobjectContextMenu")
            self.assertTrue(menu.property("opened"))
            popup_window = next(
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            )
            QTest.mouseClick(
                popup_window,
                Qt.LeftButton,
                Qt.NoModifier,
                QPoint(popup_window.width() // 2, popup_window.height() // 2),
            )
            QTest.qWait(80)
            self.assertEqual(owner.property("triggeredCommand"), "save")
            self.assertEqual(owner.property("underlyingClicks"), 0)
            self.assertFalse(owner.property("menuOpenWhenTriggered"))
            self.assertFalse(menu.property("opened"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_task_editor_moves_directly_from_assignee_to_status_popup(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 560
    height: 180
    visible: true
    property bool assigneeOpened: false
    property bool statusOpened: false
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    ListModel {
        id: users
        ListElement { login: "listy"; displayName: "Listy";
            initials: "L"; email: ""; avatarUrl: "";
            primaryGroup: "Artists" }
    }
    ListModel {
        id: choices
        ListElement { label: "Listy"; value: "listy" }
    }
    TaskEditorReleaseCoordinator {
        id: releaseCoordinator
        theme: theme
    }
    TaskTableEditorCell {
        id: assigneeCell
        x: 30
        y: 50
        width: 220
        height: 32
        theme: theme
        releaseCoordinator: releaseCoordinator
        displayText: "Listy"
        editorComponent: Component {
            UserComboBox {
                theme: window.theme
                userModel: users
                model: choices
                textRole: "label"
                valueRole: "value"
                Component.onCompleted:
                    popup.objectName = "taskAssigneePopupProbe"
                popup.onOpened: window.assigneeOpened = true
                popup.onClosed: window.assigneeOpened = false
            }
        }
    }
    TaskTableEditorCell {
        id: statusCell
        x: 310
        y: 50
        width: 220
        height: 32
        theme: theme
        releaseCoordinator: releaseCoordinator
        displayText: "In Progress"
        editorComponent: Component {
            Controls.ComboBox {
                theme: window.theme
                model: ["In Progress", "Done"]
                Component.onCompleted:
                    popup.objectName = "taskStatusPopupProbe"
                popup.onOpened: window.statusOpened = true
                popup.onClosed: window.statusOpened = false
            }
        }
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_TaskPopupHandoffTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(120, 66)
            )
            QTest.qWait(80)
            assignee_popup = owner.findChild(
                QObject, "taskAssigneePopupProbe"
            )
            self.assertIsNotNone(assignee_popup)
            self.assertTrue(owner.property("assigneeOpened"))

            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(400, 66)
            )
            QTest.qWait(120)
            status_popup = owner.findChild(QObject, "taskStatusPopupProbe")
            self.assertIsNotNone(status_popup)
            self.assertFalse(owner.property("assigneeOpened"))
            self.assertTrue(owner.property("statusOpened"))
            QTest.qWait(500)
            self.assertFalse(owner.property("assigneeOpened"))
            self.assertTrue(owner.property("statusOpened"))
        finally:
            owner.close()
            owner.deleteLater()


if __name__ == "__main__":
    unittest.main()
