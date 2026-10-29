"""Idle task values reuse geometry and do not allocate empty image subtrees."""

from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QSignalSpy, QTest

from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableColumns, _TableController, _visual_items
from tests.qt_application import gui_test_application
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _MutableColumns(_TableColumns):
    def __init__(self):
        super().__init__()
        self.reads = 0
        self.payload = {"name": {"text": "First", "kind": "text"}}
        self._columns = [dict(row=0, name="name", label="Name", width=220,
                              kind="text", dataType="varchar", hideOrder=0)]

    @Slot(str, int, result="QVariantMap")
    def row_cells(self, search_key, revision):
        self.reads += 1
        return self.payload


class TaskDisplayCostTests(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def wait_for(self, condition):
        deadline = time.monotonic() + 2
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(condition())

    def test_text_and_paint_changes_reuse_geometry_and_font(self):
        model = dict(text="Ready", enabled=True, hovered=False,
                     actionField=True, showAccent=True, accent="#427da9",
                     fontRole="caption")
        window, view = self.create(
            "features/tasks/TaskCellDisplay.qml", dict(model=model),
            width=150, height=29,
        )
        layout = view.property("layout")
        self.assertIsNotNone(layout)
        label = self.item(view, "taskTableCellDisplayLabel")
        surface = self.item(view, "taskTableCellSurface")
        accent = self.item(view, "taskTableCellAccent")
        theme = view.property("theme")
        font = label.property("font")
        for patch in (
            dict(text="Done"), dict(hovered=True), dict(enabled=False),
            dict(accent="#cb684f"), dict(text="Changed again", hovered=False),
        ):
            model.update(patch)
            view.setProperty("model", model)
            self.app.processEvents()
            self.assertTrue(layout.strictlyEquals(view.property("layout")))
            self.assertEqual(label.property("font"), font)
            self.assertEqual(label.property("text"), model["text"])
            self.assertEqual(label.property("color").rgba(), theme.property(
                "primaryText" if model["enabled"] else "disabledText"
            ).rgba())
            self.assertEqual(surface.property("color").rgba(), theme.property(
                "surfaceContainerHigh" if model["enabled"] and model["hovered"]
                else "surfaceContainerLow"
            ).rgba())
            self.assertEqual(accent.property("color"), QColor(model["accent"]))
        model.update(avatar=True)
        view.setProperty("model", model)
        self.app.processEvents()
        self.assertFalse(layout.strictlyEquals(view.property("layout")))
        self.assertGreater(label.x(), layout.property("label").property("x").toNumber())

    def test_fallback_and_pending_previews_have_no_decoder_or_mask(self):
        window, view = self.create(
            "controls/ItemPreview.qml", dict(fallbackText="AR"),
            width=24, height=24,
        )
        for source in ("", "pending-preview:avatar", "file:///document.txt"):
            view.setProperty("source", QUrl(source))
            self.app.processEvents()
            self.assertIsNone(view.findChild(QObject, "previewSourceImage"))
            self.assertIsNone(view.findChild(QObject, "previewMaskLoader"))
            self.assertFalse(view.property("previewReady"))
            self.assertEqual(view.property("sourcePixelWidth"), 0)

    def test_late_avatar_arrival_releases_and_recreates_only_the_image_subtree(self):
        with TemporaryDirectory() as directory:
            picture = QImage(24, 24, QImage.Format_RGB32)
            picture.fill(QColor("#5378b1"))
            path = Path(directory) / "avatar.png"
            self.assertTrue(picture.save(str(path)))
            users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
            window, view = self.create(
                "UserAvatar.qml", dict(userModel=users, login="artist"),
                width=24, height=24,
            )
            ready = QSignalSpy(view.imageReady)
            self.assertIsNone(view.findChild(QObject, "previewSourceImage"))
            users.replace([dict(login="artist", initials="AR", displayName="Artist",
                                avatarUrl=QUrl.fromLocalFile(str(path)).toString())])
            self.wait_for(lambda: bool(view.property("previewReady")))
            self.assertEqual(ready.count(), 1)
            image = view.findChild(QObject, "previewSourceImage")
            self.assertIsNotNone(image)
            self.assertGreater(view.property("sourcePixelWidth"), 0)
            view.setWidth(30)
            view.setHeight(30)
            self.app.processEvents()
            self.assertIs(view.findChild(QObject, "previewSourceImage"), image)
            view.setProperty("active", False)
            self.wait_for(lambda: view.findChild(QObject, "previewSourceImage") is None)
            self.assertEqual(view.property("sourcePixelWidth"), 0)
            view.setProperty("active", True)
            self.wait_for(lambda: bool(view.property("previewReady")))
            self.assertEqual(ready.count(), 2)
            self.assertEqual(view.property("fallbackText"), "AR")

    def test_loaded_preview_resize_keeps_decoder_mask_and_pixels(self):
        with TemporaryDirectory() as directory:
            picture = QImage(96, 64, QImage.Format_RGB32)
            picture.fill(QColor("#d06020"))
            path = Path(directory) / "preview.png"
            self.assertTrue(picture.save(str(path)))
            window, view = self.create(
                "controls/ItemPreview.qml",
                dict(source=QUrl.fromLocalFile(str(path)), round=True,
                     decodeAtItemSize=False, animateAppearance=False),
                width=64, height=64,
            )
            self.wait_for(lambda: bool(view.property("previewReady")))
            image = view.findChild(QObject, "previewSourceImage")
            mask = view.findChild(QObject, "previewMaskLoader")
            self.wait_for(lambda: bool(mask.property("item")))
            loaded_mask = mask.property("item")
            decoded = image.property("sourceSize")
            ready = QSignalSpy(view.imageReady)
            for size in (90, 40, 100):
                window.resize(size, size)
                view.setWidth(size)
                view.setHeight(size)
                grab = view.grabToImage()
                self.wait_for(lambda: not grab.image().isNull())
                pixels = grab.image()
                self.assertEqual(
                    pixels.pixelColor(pixels.width() // 2, pixels.height() // 2),
                    QColor("#d06020"),
                )
                self.assertIs(view.findChild(QObject, "previewSourceImage"), image)
                self.assertIs(mask.property("item"), loaded_mask)
                self.assertEqual(image.property("sourceSize"), decoded)
                self.assertEqual(ready.count(), 0)

    def test_table_cell_snapshot_updates_on_revision_without_extra_row_reads(self):
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id="asset", node_type="sobject", search_key="asset",
            code="ASSET001", title="Asset",
        )])
        columns, controller = _MutableColumns(), _TableController()
        users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
        window, view = self.create(
            "SearchResultTable.qml",
            dict(controller=controller, columnsController=columns,
                 resultModel=model, userModel=users, presentationActive=True),
            width=500, height=160, context=dict(appController=controller),
        )
        label = next(item for item in _visual_items(view)
                     if item.metaObject().indexOfProperty("text") >= 0
                     and item.property("text") == "First")
        reads = columns.reads
        columns.payload["name"]["text"] = "Second"
        controller.selected_node_changed.emit()
        self.app.processEvents()
        self.assertEqual(label.property("text"), "First")
        self.assertEqual(columns.reads, reads)
        columns._cell_revision += 1
        columns.cellRevisionChanged.emit()
        self.app.processEvents()
        self.assertEqual(label.property("text"), "Second")
        self.assertEqual(columns.reads, reads + 1)


if __name__ == "__main__":
    unittest.main()
