"""Render the real bubble contour, including its selected outline and tail."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest


class MessageBubbleRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_contour_is_continuous_and_mirrored_with_consistent_corners(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(
            error.toString() for error in errors
        ))
        component = QQmlComponent(engine)
        qml_dir = Path(__file__).parents[1] / "thlib/ui/qml"
        component.setData(b'''
import QtQuick
import QtQuick.Controls
import "."
Window {
    width: 700; height: 420; visible: true; color: appTheme.workspace
    Theme { id: appTheme; dark: true; fadeAnimationsEnabled: false }
    Column {
        anchors.fill: parent; anchors.margins: 24; spacing: 12
        Repeater {
            model: 4
            MessageTimelineFrame {
                required property int index
                objectName: "bubbleFrame" + index
                width: parent.width
                theme: appTheme
                outgoing: index % 2 === 1
                groupFirst: index < 2
                groupLast: index < 2
                current: true
                initials: "AA"
                Label { text: "Alexey"; color: appTheme.action }
                Label { text: "Hello! How are you?"; color: appTheme.primaryText }
            }
        }
    }
}
''', QUrl.fromLocalFile(str(qml_dir / "BubbleRenderHarness.qml")))
        window = component.create()
        self.assertIsNotNone(window, [e.toString() for e in component.errors()])
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            pending = [window.contentItem()]
            frames = {}
            while pending:
                item = pending.pop()
                if item.objectName().startswith("bubbleFrame"):
                    frames[item.objectName()] = item
                pending.extend(item.childItems())
            images = []
            for index in range(4):
                frame = frames["bubbleFrame" + str(index)]
                grab = frame.grabToImage()
                ready = QSignalSpy(grab.ready)
                self.assertTrue(ready.wait(2000))
                image = grab.image()
                self.assertFalse(image.isNull())
                images.append(image)
            if os.environ.get("TH_BUBBLE_PREVIEW"):
                self.assertTrue(window.grabWindow().save(os.environ["TH_BUBBLE_PREVIEW"]))
            # Opposite directions must be exact mirrors of the same contour.
            for first, second in ((images[0], images[1]), (images[2], images[3])):
                self.assertEqual(first.size(), second.size())
                for y in range(first.height()):
                    for x in range(first.width()):
                        self.assertLessEqual(abs(
                            first.pixelColor(x, y).alpha()
                            - second.pixelColor(first.width() - 1 - x, y).alpha()
                        ), 3)
            # Every filled scanline through the lower corner/tail is contiguous.
            grab = frames["bubbleFrame0"].findChild(
                QQuickItem, "messageTimelineOutline"
            ).grabToImage()
            ready = QSignalSpy(grab.ready)
            self.assertTrue(ready.wait(2000))
            image = grab.image()
            for y in range(image.height() // 2, image.height() - 2):
                occupied = [x for x in range(image.width())
                            if image.pixelColor(x, y).alpha() > 200]
                self.assertTrue(occupied)
                self.assertEqual(len(occupied), occupied[-1] - occupied[0] + 1)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_wide_attachment_uses_bubble_width_and_image_aspect_ratio(self):
        with TemporaryDirectory() as directory:
            image_path = Path(directory) / "wide.png"
            self.assertTrue(QImage(640, 120, QImage.Format_RGB32).save(str(image_path)))
            small_path = Path(directory) / "small.png"
            self.assertTrue(QImage(180, 60, QImage.Format_RGB32).save(str(small_path)))
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(
                error.toString() for error in errors
            ))
            component = QQmlComponent(engine)
            qml_dir = Path(__file__).parents[1] / "thlib/ui/qml"
            component.setData(b'''
import QtQuick
import QtQuick.Layouts
import "."
Window {
    id: window
    width: 800; height: 500; visible: true
    property url previewSource: ""
    Theme { id: appTheme; dark: true; fadeAnimationsEnabled: false }
    MessageTimelineFrame {
        id: frame
        objectName: "mediaFrame"
        width: parent.width
        theme: appTheme
        mediaAttachments: true
        AttachmentCard {
            objectName: "wideAttachment"
            Layout.fillWidth: true
            theme: appTheme
            title: "wide.png"
            extension: "PNG"
            previewUrl: String(window.previewSource)
            webPreview: true
        }
    }
}
''', QUrl.fromLocalFile(str(qml_dir / "MediaBubbleHarness.qml")))
            window = component.create()
            self.assertIsNotNone(window, [e.toString() for e in component.errors()])
            try:
                window.setProperty("previewSource", QUrl.fromLocalFile(str(image_path)))
                self.assertTrue(QTest.qWaitForWindowExposed(window))
                frame = window.findChild(QQuickItem, "mediaFrame")
                card = window.findChild(QQuickItem, "wideAttachment")
                preview = window.findChild(QQuickItem, "attachmentImagePreview")
                deadline = monotonic() + 2
                while preview.property("sourcePixelWidth") == 0 and monotonic() < deadline:
                    QTest.qWait(10)
                self.assertGreater(preview.property("sourcePixelWidth"), 0)
                QTest.qWait(20)
                self.assertAlmostEqual(frame.property("bubbleExtent"), 560, delta=1)
                self.assertGreater(card.width(), 500)
                self.assertLess(card.height(), 180, (
                    preview.property("sourcePixelWidth"),
                    preview.property("sourcePixelHeight"),
                    card.property("imageHeight"),
                ))
                if os.environ.get("TH_MEDIA_PREVIEW"):
                    self.assertTrue(window.grabWindow().save(os.environ["TH_MEDIA_PREVIEW"]))
                frame.setWidth(320)
                QTest.qWait(20)
                self.assertAlmostEqual(frame.property("bubbleExtent"), 224, delta=1)
                self.assertLessEqual(card.width(), 224)
                frame.setWidth(800)
                window.setProperty("previewSource", QUrl.fromLocalFile(str(small_path)))
                deadline = monotonic() + 2
                while preview.property("sourcePixelWidth") != 180 and monotonic() < deadline:
                    QTest.qWait(10)
                self.assertEqual(preview.property("sourcePixelWidth"), 180)
                QTest.qWait(20)
                self.assertLessEqual(preview.width(), 180)
                self.assertLess(card.height(), 130)
                self.assertEqual(warnings, [])
            finally:
                window.close()
                window.deleteLater()
                engine.deleteLater()
