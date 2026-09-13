from __future__ import annotations

import os
from pathlib import Path
import re
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    QPointF,
    Property,
    QMetaObject,
    QUrl,
    Signal,
    Slot,
    Qt,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application


ROOT = Path(__file__).parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _SuggestionModel(QAbstractListModel):
    TitleRole = Qt.UserRole + 1
    DescriptionRole = Qt.UserRole + 2
    KeywordRole = Qt.UserRole + 3
    CodeRole = Qt.UserRole + 4
    SelectedRole = Qt.UserRole + 5

    def __init__(self):
        super().__init__()
        self._records = [{
            "title": "Alpha",
            "description": "First result",
            "keyword": "alpha",
            "code": "alpha",
            "selected": False,
        }]

    def roleNames(self):
        return {
            self.TitleRole: b"title",
            self.DescriptionRole: b"description",
            self.KeywordRole: b"keyword",
            self.CodeRole: b"code",
            self.SelectedRole: b"selected",
        }

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        record = self._records[index.row()]
        return {
            self.TitleRole: record["title"],
            self.DescriptionRole: record["description"],
            self.KeywordRole: record["keyword"],
            self.CodeRole: record["code"],
            self.SelectedRole: record["selected"],
        }.get(role)

    @Slot(result=int)
    def count(self):
        return len(self._records)

    @Slot(int)
    def select_row(self, _index):
        pass

    def clear(self):
        self.beginResetModel()
        self._records.clear()
        self.endResetModel()


class _SearchController(QObject):
    search_text_changed = Signal()

    def __init__(self, suggestions):
        super().__init__()
        self._suggestions = suggestions
        self.opened_suggestions = []

    @Property(str, notify=search_text_changed)
    def current_search_text(self):
        return ""

    @Slot(str)
    def update_search_text(self, _text):
        pass

    @Slot(str)
    def request_search_suggestions(self, _text):
        pass

    @Slot()
    def clear_search_suggestions(self):
        self._suggestions.clear()

    @Slot(int)
    def accept_search_suggestion(self, _index):
        self._suggestions.clear()

    @Slot(int)
    def open_search_suggestion_in_new_tab(self, index):
        self.opened_suggestions.append(index)

    @Slot(str)
    def search(self, _text):
        pass


class ThemeControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_shared_search_clear_mouse_keyboard_and_read_only(self):
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    width: 420; height: 100; visible: true
    Theme { id: palette; dark: true }
    Controls.SearchField {
        objectName: "search"; theme: palette; width: parent.width; height: 44
    }
}''', QUrl.fromLocalFile(str(QML / "_SharedSearchTest.qml")))
        owner = component.create()
        self.assertIsNotNone(owner, "\n".join(error.toString() for error in component.errors()))
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(owner))
            search = owner.findChild(QQuickItem, "search")
            clear = owner.findChild(QQuickItem, "searchFieldClear")
            clear.setProperty("duplicateWindow", 0)
            edits = []
            search.searchEdited.connect(edits.append)
            for width in (220, 420):
                owner.setWidth(width)
                search.setProperty("text", "needle")
                self.app.processEvents()
                edits.clear()
                point = clear.mapToScene(QPointF(clear.width() / 2, clear.height() / 2)).toPoint()
                QTest.mouseClick(owner, Qt.LeftButton, Qt.NoModifier, point)
                self.assertEqual(search.property("text"), "")
                self.assertEqual(edits, [""])
            search.setProperty("text", "needle")
            search.forceActiveFocus()
            QTest.keyClick(owner, Qt.Key_Escape)
            self.assertEqual(search.property("text"), "")
            search.setProperty("text", "locked")
            search.setProperty("readOnly", True)
            edits.clear()
            QTest.keyClick(owner, Qt.Key_Escape)
            QMetaObject.invokeMethod(search, "clearSearch")
            self.assertFalse(clear.property("enabled"))
            self.assertEqual(search.property("text"), "locked")
            self.assertEqual(edits, [])
        finally:
            owner.close()
            owner.deleteLater()
            self.app.processEvents()

    def test_project_image_picker_uses_controller_state_and_undo(self):
        from tempfile import TemporaryDirectory
        from PySide6.QtGui import QImage
        from thlib.tactic_classes import Project
        from thlib.ui.project_editor import ProjectEditorController

        with TemporaryDirectory() as directory:
            image_path = str(Path(directory) / "preview.png")
            image = QImage(20, 20, QImage.Format_RGB32)
            image.fill(Qt.red)
            self.assertTrue(image.save(image_path))
            controller = ProjectEditorController(
                lambda: {"project": Project({"code": "demo", "name": "Demo"})}, None)
            controller.begin_session()
            engine = QQmlEngine()
            engine.rootContext().setContextProperty("projectEditorController", controller)
            component = QQmlComponent(engine)
            component.setData(b'''import QtQuick
import QtQuick.Window
Window {
    width: 1000; height: 900; visible: true
    Theme { id: palette; dark: true }
    ProjectEditorView { anchors.fill: parent; theme: palette }
}''', QUrl.fromLocalFile(str(QML / "_ProjectImageTest.qml")))
            owner = component.create()
            self.assertIsNotNone(owner, "\n".join(error.toString() for error in component.errors()))
            try:
                dialog = owner.findChild(QObject, "projectPreviewDialog")
                preview = owner.findChild(QQuickItem, "projectPreview")
                undo = owner.findChild(QQuickItem, "projectCancelPreview")
                for width in (520, 1000):
                    owner.setWidth(width)
                    dialog.setProperty("selectedFile", QUrl.fromLocalFile(image_path))
                    self.assertTrue(QMetaObject.invokeMethod(dialog, "accepted"))
                    self.app.processEvents()
                    self.assertEqual(Path(controller.previewPath), Path(image_path))
                    self.assertEqual(preview.property("source"), QUrl.fromLocalFile(image_path))
                    point = undo.mapToScene(QPointF(undo.width() / 2, undo.height() / 2)).toPoint()
                    self.assertTrue(owner.contentItem().contains(point))
                    QTest.mouseClick(owner, Qt.LeftButton, Qt.NoModifier, point)
                    self.app.processEvents()
                    self.assertEqual(controller.previewPath, "")
                    self.assertEqual(preview.property("source"), QUrl())
                    self.assertFalse(undo.property("visible"))
            finally:
                owner.close()
                owner.deleteLater()
                self.app.processEvents()

    def test_qml_colors_are_centralized_in_theme(self):
        color_literal = re.compile(r"#[0-9a-fA-F]{3,8}")
        offenders = []
        for path in QML.rglob("*.qml"):
            if path.name == "Theme.qml":
                continue
            if color_literal.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

        icon = (QML / "controls" / "MaterialIcon.qml").read_text(
            encoding="utf-8"
        )
        ripple = (QML / "controls" / "MaterialRipple.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("required property color color", icon)
        self.assertIn("required property color color", ripple)
        self.assertIn("required property var theme", ripple)
        self.assertIn("theme.clickAnimationsEnabled", ripple)

    def test_button_ignores_a_transient_missing_theme_during_teardown(self):
        messages = []

        def capture_message(_message_type, _context, message):
            messages.append(str(message or ""))

        previous_handler = qInstallMessageHandler(capture_message)
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 160; height: 80; visible: true
    property var liveTheme: palette
    Theme { id: palette; dark: true }
    Controls.Button {
        anchors.centerIn: parent
        theme: window.liveTheme
        tonal: true
        text: "Test"
    }
    function releaseTheme() { liveTheme = undefined }
}''',
            QUrl.fromLocalFile(str(QML / "_ButtonThemeTeardownTest.qml")),
        )
        owner = None
        try:
            owner = component.create()
            self.assertIsNotNone(
                owner,
                "\n".join(error.toString() for error in component.errors()),
            )
            self.assertTrue(QMetaObject.invokeMethod(owner, "releaseTheme"))
            self.app.processEvents()
        finally:
            if owner is not None:
                owner.close()
                owner.deleteLater()
            engine.deleteLater()
            self.app.processEvents()
            qInstallMessageHandler(previous_handler)

        self.assertFalse(
            any("TypeError" in message for message in messages),
            messages,
        )

    def test_busy_indicator_skips_zero_sized_paint_devices(self):
        messages = []

        def capture_message(_message_type, _context, message):
            messages.append(str(message or ""))

        previous_handler = qInstallMessageHandler(capture_message)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    width: 80
    height: 80
    visible: true
    Theme { id: theme; dark: true }
    Controls.BusyIndicator {
        objectName: "testedBusyIndicator"
        anchors.centerIn: parent
        width: 0
        height: 0
        uiTheme: theme
        running: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_BusyIndicatorTest.qml")),
        )
        owner = None
        try:
            owner = component.create()
            self.assertIsNotNone(
                owner,
                "\n".join(error.toString() for error in component.errors()),
            )
            QTest.qWait(30)
            indicator = owner.findChild(QQuickItem, "testedBusyIndicator")
            arc = owner.findChild(QQuickItem, "busyIndicatorArc")
            self.assertIsNotNone(indicator)
            self.assertIsNotNone(arc)
            self.assertFalse(arc.property("visible"))

            indicator.setProperty("width", 24)
            indicator.setProperty("height", 24)
            QTest.qWait(30)
            self.assertTrue(arc.property("visible"))

            indicator.setProperty("running", False)
            QTest.qWait(10)
            self.assertFalse(arc.property("visible"))
        finally:
            if owner is not None:
                owner.close()
                owner.deleteLater()
            self.app.processEvents()
            qInstallMessageHandler(previous_handler)

        painter_errors = [
            message for message in messages
            if message.startswith("QPainter::")
        ]
        self.assertEqual(painter_errors, [])

    def test_material_ripple_has_no_idle_effect_or_animation_graph(self):
        messages = []

        def capture_message(_message_type, _context, message):
            messages.append(str(message or ""))

        previous_handler = qInstallMessageHandler(capture_message)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    width: 80
    height: 80
    visible: true
    Theme { id: theme; objectName: "testedTheme"; dark: true }
    function triggerRipple() { ripple.burst(20, 20) }
    function disableClickAnimations() { theme.clickAnimationsEnabled = false }
    function enableClickAnimations() { theme.clickAnimationsEnabled = true }
    function hideWhileAnimating() { visible = false }
    function showAgain() { visible = true }
    Controls.MaterialRipple {
        id: ripple
        objectName: "testedRipple"
        anchors.fill: parent
        theme: theme
        color: theme.rippleStrong
        shapeRadius: 12
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_MaterialRippleTest.qml")),
        )
        owner = None
        try:
            owner = component.create()
            self.assertIsNotNone(
                owner,
                "\n".join(
                    error.toString() for error in component.errors()
                ),
            )
            loader = owner.findChild(
                QQuickItem, "materialRippleVisualLoader"
            )
            self.assertIsNotNone(loader)
            self.assertFalse(loader.property("active"))
            self.assertIsNone(loader.property("item"))

            self.assertTrue(QMetaObject.invokeMethod(owner, "triggerRipple"))
            self.app.processEvents()
            self.assertTrue(loader.property("active"))
            self.assertIsNotNone(loader.property("item"))

            self.assertTrue(
                QMetaObject.invokeMethod(owner, "hideWhileAnimating")
            )
            QTest.qWait(20)
            self.assertTrue(loader.property("active"))
            self.assertTrue(QMetaObject.invokeMethod(owner, "showAgain"))

            for _index in range(5):
                self.assertTrue(
                    QMetaObject.invokeMethod(owner, "triggerRipple")
                )
                QTest.qWait(5)
            self.assertTrue(
                QMetaObject.invokeMethod(owner, "disableClickAnimations")
            )
            QTest.qWait(20)
            self.assertFalse(loader.property("active"))
            self.assertIsNone(loader.property("item"))

            self.assertTrue(
                QMetaObject.invokeMethod(owner, "enableClickAnimations")
            )
            self.assertTrue(QMetaObject.invokeMethod(owner, "triggerRipple"))
            QTest.qWait(450)
            self.assertFalse(loader.property("active"))
            self.assertIsNone(loader.property("item"))
        finally:
            if owner is not None:
                owner.close()
                owner.deleteLater()
            self.app.processEvents()
            qInstallMessageHandler(previous_handler)

        animation_driver_warnings = [
            message for message in messages
            if "QUnifiedTimer::stopAnimationDriver" in message
        ]
        self.assertEqual(animation_driver_warnings, [])

    def test_tooltip_popup_is_created_only_for_a_visible_invocation(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 120
    height: 80
    visible: true
    property bool showTip: false
    Theme { id: theme; dark: true }
    Controls.ToolTip {
        objectName: "testedLazyToolTip"
        theme: theme
        visible: window.showTip
        delay: 0
        text: "Details"
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_LazyToolTipTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        tooltip = owner.findChild(QQuickItem, "testedLazyToolTip")
        self.assertIsNotNone(tooltip)
        self.assertFalse(tooltip.property("active"))
        self.assertIsNone(tooltip.property("item"))

        owner.setProperty("showTip", True)
        self.app.processEvents()
        self.assertTrue(tooltip.property("active"))
        self.assertIsNotNone(tooltip.property("item"))

        owner.setProperty("showTip", False)
        self.app.processEvents()
        self.assertFalse(tooltip.property("active"))
        self.assertIsNone(tooltip.property("item"))

        owner.close()
        owner.deleteLater()
        self.app.processEvents()

    def test_shared_scrollbar_tracks_actual_content_overflow(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    width: 180
    height: 140
    visible: true
    property real itemContentHeight: 260

    Theme { id: theme; dark: true }
    Flickable {
        id: viewport
        anchors.fill: parent
        contentWidth: width
        contentHeight: itemContentHeight
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: "overflowBar"
            theme: theme
            flickableTarget: viewport
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ScrollBarOverflowTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            scrollbar = owner.findChild(QObject, "overflowBar")
            self.assertIsNotNone(scrollbar)
            self.assertTrue(scrollbar.property("visible"))
            self.assertTrue(scrollbar.property("enabled"))

            owner.setProperty("itemContentHeight", 80)
            QTest.qWait(30)
            self.assertFalse(scrollbar.property("visible"))
            self.assertFalse(scrollbar.property("enabled"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_shared_scrollbar_uses_canonical_viewport_edges(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    width: 220
    height: 160
    visible: true
    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true

    Theme { id: theme; dark: true }
    Flickable {
        id: viewport
        objectName: "edgeViewport"
        anchors.fill: parent
        contentWidth: 420
        contentHeight: 360
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: "edgeVerticalBar"
            theme: theme
            flickableTarget: viewport
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            objectName: "edgeHorizontalBar"
            theme: theme
            flickableTarget: viewport
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ScrollBarEdgeTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            viewport = owner.findChild(QQuickItem, "edgeViewport")
            vertical = owner.findChild(QQuickItem, "edgeVerticalBar")
            horizontal = owner.findChild(QQuickItem, "edgeHorizontalBar")

            self.assertIsNotNone(viewport)
            self.assertIsNotNone(vertical)
            self.assertIsNotNone(horizontal)
            self.assertAlmostEqual(
                vertical.x() + vertical.width(), viewport.width(), delta=0.5
            )
            self.assertAlmostEqual(vertical.y(), 0.0, delta=0.5)
            self.assertAlmostEqual(
                horizontal.y() + horizontal.height(),
                viewport.height(),
                delta=0.5,
            )
            self.assertAlmostEqual(horizontal.x(), 0.0, delta=0.5)
        finally:
            owner.close()
            owner.deleteLater()

    def test_shared_scrollbar_leaves_scroll_position_to_qt(self):
        source = (QML / "controls" / "ScrollBar.qml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("flickableTarget.contentY =", source)
        self.assertNotIn("flickableTarget.contentX =", source)
        self.assertIn("flickableTarget.cancelWheelScroll()", source)
        self.assertIn("function takePaginationPermit", source)
        self.assertIn("readonly property real reservedExtent", source)
        self.assertEqual(
            source.count(
                "enabled: !root.theme.suppressTransientMotion"
            ),
            7,
        )

    def test_shared_scrollbar_keeps_track_geometry_stable_on_hover(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls
Window {
    width: 180
    height: 140
    visible: true
    Theme { id: theme; dark: true }
    Flickable {
        id: viewport
        anchors.fill: parent
        contentWidth: width
        contentHeight: 400
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: "stableBar"
            theme: theme
            flickableTarget: viewport
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_StableScrollBarTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            scrollbar = owner.findChild(QQuickItem, "stableBar")
            width = scrollbar.property("width")
            self.assertEqual(width, scrollbar.property("reservedExtent"))
            point = scrollbar.mapToScene(QPointF(
                scrollbar.width() / 2, scrollbar.height() / 2
            )).toPoint()
            QTest.mouseMove(owner, point)
            QTest.qWait(30)
            self.assertTrue(scrollbar.property("hovered"))
            self.assertEqual(scrollbar.property("width"), width)
        finally:
            owner.close()
            owner.deleteLater()

    def test_common_search_uses_live_theme_roles(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    width: 480
    height: 160
    visible: true
    property alias darkMode: theme.dark
    property color expectedSurface: theme.surfaceContainerHigh
    property color expectedAction: theme.action
    property color expectedText: theme.primaryText
    property color expectedSecondaryText: theme.secondaryText
    property color expectedSelectedText: theme.selectedText

    Theme {
        id: theme
        dark: true
        baseColor: "#314154"
        accentColor: "#d67b32"
    }
    QtObject {
        id: suggestions
        signal contentReplaced()
        function count() { return 0 }
        function select_row(index) {}
    }
    QtObject {
        id: controller
        property string current_search_text: ""
        signal search_text_changed()
        function update_search_text(text) {}
        function request_search_suggestions(text) {}
        function clear_search_suggestions() {}
        function accept_search_suggestion(index) {}
        function search(text) {}
    }
    TacticSearchField {
        objectName: "commonSearch"
        anchors.centerIn: parent
        width: 360
        theme: theme
        suggestionModel: suggestions
        controller: controller
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ThemeSearchTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            rendered = owner.screen().grabWindow(owner.winId())
            self.assertFalse(rendered.isNull())
            self.assertEqual((rendered.width(), rendered.height()), (480, 160))
            background = owner.findChild(QObject, "tacticSearchBackground")
            icon = owner.findChild(QObject, "tacticSearchIcon")
            search_input = owner.findChild(QObject, "tacticSearchInput")
            self.assertIsNotNone(background)
            self.assertIsNotNone(icon)
            self.assertIsNotNone(search_input)

            self.assertEqual(
                background.property("color"), owner.property("expectedSurface")
            )
            self.assertEqual(
                icon.property("color"), owner.property("expectedSecondaryText")
            )
            self.assertEqual(
                search_input.property("color"), owner.property("expectedText")
            )
            self.assertEqual(
                search_input.property("selectionColor"),
                owner.property("expectedAction"),
            )
            self.assertEqual(
                search_input.property("selectedTextColor"),
                owner.property("expectedSelectedText"),
            )
            self.assertEqual(
                search_input.property("placeholderTextColor").toRgb().rgba(),
                owner.property("expectedSecondaryText").toRgb().rgba(),
            )

            previous_surface = background.property("color")
            owner.setProperty("darkMode", False)
            QTest.qWait(180)
            self.assertEqual(
                background.property("color").toRgb().rgba(),
                owner.property("expectedSurface").toRgb().rgba(),
            )
            self.assertNotEqual(background.property("color"), previous_surface)
        finally:
            owner.close()
            owner.deleteLater()

    def test_search_suggestion_can_clear_its_model_during_acceptance(self):
        messages = []

        def capture_message(_message_type, _context, message):
            messages.append(str(message or ""))

        previous_handler = qInstallMessageHandler(capture_message)
        suggestions = _SuggestionModel()
        controller = _SearchController(suggestions)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty(
            "regressionSuggestionModel", suggestions
        )
        engine.rootContext().setContextProperty(
            "regressionSearchController", controller
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    width: 480
    height: 180
    visible: true
    function acceptFirstSuggestion() {
        searchField.acceptSuggestion(0, "Alpha")
    }
    Theme { id: theme; dark: true }
    TacticSearchField {
        id: searchField
        objectName: "regressionSearchField"
        anchors.centerIn: parent
        width: 360
        theme: theme
        suggestionModel: regressionSuggestionModel
        controller: regressionSearchController
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_SearchAcceptanceTest.qml")),
        )
        owner = None
        try:
            owner = component.create()
            self.assertIsNotNone(
                owner,
                "\n".join(error.toString() for error in component.errors()),
            )
            search_field = owner.findChild(QObject, "regressionSearchField")
            self.assertIsNotNone(search_field)
            self.assertTrue(QMetaObject.invokeMethod(
                owner, "acceptFirstSuggestion"
            ))
            QTest.qWait(30)

            self.assertEqual(suggestions.count(), 0)
            self.assertEqual(search_field.property("text"), "Alpha")
            self.assertFalse(any(
                "searchInput is not defined" in message
                or "ReferenceError" in message
                for message in messages
            ), "\n".join(messages))
        finally:
            if owner is not None:
                owner.close()
                owner.deleteLater()
            self.app.processEvents()
            qInstallMessageHandler(previous_handler)

    def test_middle_click_on_search_suggestion_requests_a_new_tab(self):
        suggestions = _SuggestionModel()
        controller = _SearchController(suggestions)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty(
            "regressionSuggestionModel", suggestions
        )
        engine.rootContext().setContextProperty(
            "regressionSearchController", controller
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    width: 480
    height: 180
    visible: true
    Theme { id: theme; dark: true }
    TacticSearchField {
        id: searchField
        objectName: "middleClickSearchField"
        anchors.centerIn: parent
        width: 360
        theme: theme
        suggestionModel: regressionSuggestionModel
        controller: regressionSearchController
        openSuggestionsInNewTab: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_SearchMiddleClickTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            search_field = owner.findChild(QObject, "middleClickSearchField")
            self.assertTrue(QMetaObject.invokeMethod(
                search_field, "positionPopup"
            ))
            popup = owner.findChild(QObject, "tacticSearchSuggestionsPopup")
            self.assertIsNotNone(popup)
            self.assertTrue(QMetaObject.invokeMethod(popup, "open"))
            QTest.qWait(30)
            suggestion_list = owner.findChild(
                QQuickItem, "tacticSearchSuggestionList"
            )
            self.assertIsNotNone(suggestion_list)
            self.assertEqual(suggestion_list.property("count"), 1)
            self.assertTrue(popup.property("visible"))
            descendants = list(suggestion_list.childItems())
            suggestion = None
            while descendants:
                item = descendants.pop()
                if item.objectName() == "tacticSearchSuggestionRow_0":
                    suggestion = item
                    break
                descendants.extend(item.childItems())
            self.assertIsNotNone(suggestion)
            point = suggestion.mapToScene(QPointF(
                suggestion.width() / 2, suggestion.height() / 2
            )).toPoint()

            QTest.mouseClick(owner, Qt.MiddleButton, pos=point)
            QTest.qWait(30)

            self.assertEqual(controller.opened_suggestions, [0])
            self.assertEqual(suggestions.count(), 1)
        finally:
            owner.close()
            owner.deleteLater()
            self.app.processEvents()

    def test_button_family_uses_only_pointing_hand_cursor(self):
        button_sources = (
            QML / "controls" / "Button.qml",
            QML / "controls" / "CompactIconButton.qml",
            QML / "controls" / "FilledActionButton.qml",
            QML / "controls" / "PreviewNavigationButton.qml",
            QML / "controls" / "SegmentedButton.qml",
            QML / "controls" / "TabButton.qml",
            QML / "controls" / "PopupAction.qml",
            QML / "MessageReactionChip.qml",
        )
        for path in button_sources:
            source = path.read_text(encoding="utf-8")
            self.assertIn("Qt.PointingHandCursor", source, path.name)
            self.assertNotIn("Qt.OpenHandCursor", source, path.name)
            self.assertNotIn("Qt.ClosedHandCursor", source, path.name)

        activation = (
            QML / "controls" / "ActivationHandler.qml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "property int cursorShape: Qt.PointingHandCursor",
            activation,
        )


if __name__ == "__main__":
    unittest.main()
