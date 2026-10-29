"""Note image resize must rescale one loaded image, without loading it again."""

from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, QUrl
from PySide6.QtGui import QImage, QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_columns_table_view import _visual_items


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class NoteImageResizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_note_image_keeps_decode_mask_and_aspect_while_resizing(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import "."
import "features/objects" as Objects
Window {
    id: window
    width: 900; height: 800; visible: true
    property url previewSource: ""
    Theme { id: palette; dark: true; fadeAnimationsEnabled: false }
    QtObject { id: commands; function attachment_action(token, action) {} }
    Objects.NoteBody {
        width: parent.width - 40
        x: 20; y: 20
        height: implicitHeight
        theme: palette
        controller: commands
        model: ({entryType:"note", displayHtml:"", body:"", skeyPreviews:[], attachments:[{
            token:"resize-image", title:"Resize image", extension:"JPG", local:true,
            previewUrl:String(window.previewSource)
        }]})
    }
}''', QUrl.fromLocalFile(str(QML / "_NoteImageResizeTest.qml")))
        window = component.create()
        self.assertIsNotNone(window, [e.toString() for e in component.errors()])
        directory = TemporaryDirectory(prefix="note-resize-")
        try:
            for width, height in ((1200, 1800), (1800, 800)):
                path = Path(directory.name) / f"{width}x{height}.jpg"
                image = QImage(width, height, QImage.Format_RGB32)
                image.fill(QColor("#d06020"))
                self.assertTrue(image.save(str(path)))
                window.setProperty("previewSource", QUrl.fromLocalFile(str(path)))
                deadline = time.monotonic() + 3
                preview = None
                while time.monotonic() < deadline:
                    preview = next((item for item in _visual_items(window.contentItem())
                                    if item.objectName() == "attachmentImagePreview"), None)
                    if preview and preview.property("sourcePixelWidth") > 0:
                        break
                    QTest.qWait(10)
                self.assertIsNotNone(preview)
                self.assertGreater(preview.property("sourcePixelWidth"), 0)
                frame(window)
                source = preview.findChild(QQuickItem, "previewSourceImage")
                self.assertIsNotNone(source)
                decoded_size = source.property("sourceSize")
                size_changes = QSignalSpy(source.sourceSizeChanged)
                loads = QSignalSpy(preview.imageReady)
                mask_loader = preview.findChild(QObject, "previewMaskLoader")
                mask = mask_loader.property("item")
                for extent in (*range(900, 319, -20), *range(320, 901, 20)):
                    window.resize(extent, 800)
                    # Capture asynchronously; grabWindow can wait on Python render callbacks.
                    grab = window.contentItem().grabToImage()
                    deadline = time.monotonic() + 2
                    while grab.image().isNull() and time.monotonic() < deadline:
                        QTest.qWait(5)
                    rendered = grab.image()
                    self.assertFalse(rendered.isNull())
                    self.assertIs(preview.findChild(QQuickItem, "previewSourceImage"), source)
                    self.assertEqual(size_changes.count(), 0, "Resize changed the decoder request")
                    self.assertEqual(loads.count(), 0, "Resize reloaded the image")
                    self.assertEqual(source.property("sourceSize"), decoded_size)
                    self.assertGreater(preview.property("sourcePixelWidth"), 0)
                    self.assertIs(mask_loader.property("item"), mask)
                    center = preview.mapToScene(QPointF(preview.width() / 2, preview.height() / 2))
                    pixel = rendered.pixelColor(int(center.x() * rendered.width() / window.width()),
                                                int(center.y() * rendered.height() / window.height()))
                    self.assertGreater(pixel.red(), 150, "Image flashed to its fallback surface")
                    self.assertLess(pixel.blue(), 100, "Image flashed to its fallback surface")
                    card = next(item for item in _visual_items(window.contentItem())
                                if item.metaObject().className().startswith("AttachmentCard"))
                    self.assertAlmostEqual(card.property("imageHeight"),
                                           min(360, (card.width() - 16) * height / width), delta=1)
            self.assertEqual(warnings, [])
        finally:
            window.setProperty("previewSource", QUrl())
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            directory.cleanup()
