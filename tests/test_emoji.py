from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from thlib.ui.emoji import EmojiCatalog


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class EmojiCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.catalog = EmojiCatalog(ROOT)

    def test_catalog_uses_vendored_unicode_data_and_noto_font(self):
        data = (
            ROOT / "thlib" / "side" / "unicode_emoji" / "emoji-test.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("# Version: 17.0", data[:1000])
        self.assertEqual(self.catalog.fontFamily, "Noto Color Emoji")
        self.assertEqual(self.catalog.totalCount, 3944)
        self.assertTrue(
            ROOT.joinpath(
                "thlib", "side", "noto_emoji",
                "NotoColorEmoji_WindowsCompatible.ttf",
            ).is_file()
        )
        self.assertTrue(
            ROOT.joinpath("thlib", "side", "noto_emoji", "LICENSE").is_file()
        )
        self.assertTrue(
            ROOT.joinpath("thlib", "side", "unicode_emoji", "LICENSE").is_file()
        )

    def test_catalog_filters_categories_and_names(self):
        self.catalog.set_filter(self.catalog.defaultCategory, "")
        self.assertGreater(self.catalog.count, 100)

        self.catalog.set_filter("Flags", "Ukraine")

        self.assertEqual(self.catalog.count, 1)
        index = self.catalog.index(0)
        self.assertEqual(
            self.catalog.data(index, EmojiCatalog.EmojiRole), "🇺🇦"
        )
        self.assertEqual(
            self.catalog.data(index, EmojiCatalog.NameRole), "flag: Ukraine"
        )

    def test_picker_creates_only_visible_delegates_and_activates_by_keyboard(self):
        engine = QQmlEngine()
        engine.rootContext().setContextProperty("emojiCatalog", self.catalog)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    id: window
    objectName: "emojiTestWindow"
    width: 520
    height: 560
    visible: true
    property string selectedEmoji: ""
    Theme { id: theme; dark: true }
    Rectangle {
        id: anchor
        width: 32
        height: 32
        anchors.bottom: parent.bottom
        anchors.right: parent.right
    }
    EmojiPicker {
        id: picker
        objectName: "emojiTestPicker"
        theme: theme
        catalog: emojiCatalog
        usePopupWindow: false
        onEmojiSelected: emoji => {
            window.selectedEmoji = emoji
            picker.close()
        }
    }
    Component.onCompleted: picker.openFor(anchor)
}
''',
            QUrl.fromLocalFile(str(QML / "_EmojiPickerTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(100)
            picker = window.findChild(QObject, "emojiTestPicker")
            self.assertIsNotNone(picker)
            self.assertTrue(picker.property("opened"))
            self.assertGreater(self.catalog.count, 100)

            grid = window.findChild(QQuickItem, "emojiPickerGrid")
            pending = list(grid.childItems())
            delegates = []
            while pending:
                child = pending.pop()
                pending.extend(child.childItems())
                if child.objectName() == "emojiPickerCell":
                    delegates.append(child)
            self.assertGreater(len(delegates), 0)
            self.assertLess(len(delegates), self.catalog.count)

            first = delegates[0]
            first.forceActiveFocus()
            QTest.keyClick(window, Qt.Key.Key_Return)
            QTest.qWait(20)
            self.assertTrue(window.property("selectedEmoji"))
            self.assertFalse(picker.property("opened"))
        finally:
            window.close()
            window.deleteLater()

    def test_composer_picker_is_created_on_click_and_released_on_close(self):
        engine = QQmlEngine()
        engine.rootContext().setContextProperty("emojiCatalog", self.catalog)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    id: window
    width: 420
    height: 120
    visible: true
    QtObject {
        id: attachments
        function clipboard_has_text() { return false }
        function clipboard_has_image() { return false }
        function add_clipboard_image() {}
    }
    Theme { id: theme; dark: true }
    MessageComposerField {
        id: composer
        objectName: "emojiTestComposer"
        anchors.fill: parent
        theme: theme
        emojiCatalogModel: emojiCatalog
        attachmentController: attachments
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_EmojiComposerTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(50)
            loader = window.findChild(QObject, "messageComposerEmojiPickerLoader")
            button = window.findChild(QQuickItem, "messageComposerEmojiButton")
            self.assertIsNotNone(loader)
            self.assertIsNotNone(button)
            self.assertFalse(loader.property("active"))
            self.assertIsNone(loader.property("item"))

            point = button.mapToScene(
                QPointF(
                    button.property("width") / 2,
                    button.property("height") / 2,
                )
            )
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                point.toPoint(),
            )
            QTest.qWait(100)

            picker = loader.property("item")
            self.assertIsNotNone(picker)
            self.assertTrue(loader.property("active"))
            self.assertTrue(picker.property("opened"))

            picker.close()
            QTest.qWait(50)
            self.assertFalse(loader.property("active"))
            self.assertIsNone(loader.property("item"))
        finally:
            window.close()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
