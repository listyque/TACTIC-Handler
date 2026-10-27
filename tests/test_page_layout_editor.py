"""Page drafts and real native canvas input without writes to a server."""

import copy
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QSG_RENDER_LOOP", "basic")
from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtTest import QSignalSpy
from tests.test_layout_editor import Pool
from tests.qt_application import gui_test_application
from thlib.environment import env_inst
from thlib.ui.admin.dashboard import DashboardEditor

DOCUMENT = dict(
    name="review",
    title="Review",
    blocks=[
        dict(
            kind="column",
            height=240,
            children=[dict(kind="text", text="Project status", height=60)],
        )
    ],
)
COMPILED = dict(
    title="Review",
    targetSearchKey="sthpw/project?code=demo",
    layoutNodes=[
        dict(
            kind="group",
            height=240,
            editorPath=[0],
            children=[
                dict(kind="text", text="Project status", height=60, editorPath=[0, 0])
            ],
        )
    ],
)


class PageOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.pool = Pool()
        self.host = DashboardEditor(
            SimpleNamespace(can_manage_tools=True, debug_log=None)
        )
        self.addCleanup(self.host.shutdown)
        self.enterContext(patch.object(env_inst, "server_pool", self.pool))
        self.host._project = "demo"
        self.host._can_write = self.host._loaded = True
        self.host._metadata = dict(revision="R1")
        self.host._revision = "R1"

    def test_create_is_only_a_draft_and_checks_boundary(self):
        self.host.create("../bad", "Bad")
        self.assertFalse(self.host.document)
        self.host.create("review", "Review")
        self.assertTrue(self.host.dirty)
        self.assertFalse(self.host.checked)
        self.assertEqual(self.host.document["blocks"], [])
        self.assertEqual(self.pool.workers, [])

    def test_write_is_explicit_and_receipt_is_reused(self):
        self.host._identity = "review"
        self.host._document = copy.deepcopy(DOCUMENT)
        self.host._checked_document = copy.deepcopy(DOCUMENT)
        self.host.save()
        pending = copy.deepcopy(self.host._pending_save)
        self.assertTrue(self.host.busy)
        self.host._release(cancel=True)
        self.host.save()
        self.assertEqual(self.host._pending_save, pending)
        self.host._release(cancel=True)
        self.host._write_uncertain = True
        count = len(self.pool.workers)
        self.host.save()
        self.assertEqual(len(self.pool.workers), count)

    def test_detail_sample_uses_private_records_without_changing_the_draft(self):
        key = "demo/asset?project=demo&code=A"
        self.host._preview_owner = SimpleNamespace(
            items=SimpleNamespace(
                model=dict(sampleItems=[dict(record={"__search_key__": key})])
            ),
            shutdown=lambda: None,
        )
        self.host._metadata["compiled"] = dict(layoutHasDetails=True)
        before = copy.deepcopy(self.host.document)
        self.host._samples_changed()
        self.assertEqual(self.host._detail_key, key)
        self.assertEqual(self.host.document, before)
        serial = self.host._preview_serial
        self.host._metadata["compiled"]["layoutDetail"] = dict(targetSearchKey=key)
        self.host._samples_changed()
        self.assertEqual(self.host._preview_serial, serial)


class PageCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_administration_qml import AdministrationQmlTests

        AdministrationQmlTests.setUpClass()

    def test_page_canvas_resizes_without_saving_and_keeps_working_document(self):
        from tests.test_administration_qml import AdministrationQmlTests
        from tests.profile_ui_responsiveness import frame

        fixture = AdministrationQmlTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.window.resize(1700, 950)
        editor = fixture.admin.dashboardEditor
        from thlib.ui.table.services import TableServicesController

        working = TableServicesController(
            fixture.fixture.application, document_window=""
        )
        self.addCleanup(working.shutdown)
        working._document = dict(title="Working document", layoutNodes=[])
        previous = copy.deepcopy(working.customLayout.document)
        fixture.seed(
            editor,
            "review",
            DOCUMENT,
            dict(
                revision="R1",
                compiled=COMPILED,
                checkedDocument=copy.deepcopy(DOCUMENT),
                searchTypes=[],
            ),
        )
        fixture.admin.select_section("dashboards")
        frame(fixture.window)
        self.assertEqual(fixture.fixture.warnings, [])
        self.assertIsNotNone(editor._preview_owner)
        self.assertEqual(
            editor._preview_owner.owner.document.get("layoutNodes"),
            COMPILED["layoutNodes"],
        )
        if os.environ.get("TACTIC_CANVAS_CAPTURE"):
            fixture.window.grabWindow().save(
                str(
                    Path(os.environ["TACTIC_CANVAS_CAPTURE"]) / "native-page-before.png"
                )
            )
        target = fixture.item("canvasTarget_0.0")
        fixture.fixture.click(fixture.window, target)
        frame(fixture.window)
        handle = fixture.item("canvasHandle_se")
        start = handle.mapToScene(
            QPointF(handle.width() / 2, handle.height() / 2)
        ).toPoint()
        QTest.mousePress(fixture.window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(fixture.window, start + QPointF(20, 20).toPoint(), 30)
        QTest.keyClick(fixture.window, Qt.Key_Escape)
        QTest.mouseRelease(
            fixture.window,
            Qt.LeftButton,
            Qt.NoModifier,
            start + QPointF(20, 20).toPoint(),
        )
        self.assertFalse(editor.dirty)
        QTest.mousePress(fixture.window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(fixture.window, start + QPointF(40, 30).toPoint(), 30)
        QTest.mouseRelease(
            fixture.window,
            Qt.LeftButton,
            Qt.NoModifier,
            start + QPointF(40, 30).toPoint(),
        )
        frame(fixture.window)
        changed = editor.document["blocks"][0]["children"][0]
        self.assertEqual(changed["height"], 90)
        self.assertTrue(editor.dirty)
        self.assertFalse(editor.checked)
        self.assertEqual(working.customLayout.document, previous)
        for width in (850, 1700):
            fixture.window.resize(width, 950)
            frame(fixture.window)
            self.assertGreater(fixture.item("pageCanvasPanel").width(), 250)
        self.assertEqual(fixture.fixture.warnings, [])
        output = os.environ.get("TACTIC_CANVAS_CAPTURE")
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.assertTrue(
                fixture.window.grabWindow().save(
                    str(Path(output) / "native-page-editor.png")
                )
            )


class ItemCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    from tests.test_frame_table import FrameTableTests

    create = FrameTableTests.create
    close = FrameTableTests.close
    click = FrameTableTests.click
    item = FrameTableTests.item

    def test_existing_item_renderer_exposes_resize_and_escape(self):
        from tests.profile_ui_responsiveness import frame

        layout = dict(
            flow="grid",
            collection="tree",
            columns=12,
            elements=[
                dict(
                    name="title",
                    kind="title",
                    title="Title",
                    parent="",
                    row=1,
                    column=1,
                    span=6,
                    rows=1,
                    height=40,
                    options={},
                    variant="all",
                )
            ],
        )
        window, view = self.create(
            "features/search/ConfiguredItem.qml",
            dict(
                layout=layout,
                record=dict(kind="object", title="Asset", record={}),
                controller={},
                nodeId="A",
                editing=True,
                selectedElement="title",
            ),
            600,
            160,
        )
        changed = QSignalSpy(view.geometryEdited)
        handle = self.item(view, "canvasHandle_se")
        start = handle.mapToScene(
            QPointF(handle.width() / 2, handle.height() / 2)
        ).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start + QPointF(25, 20).toPoint(), 30)
        QTest.keyClick(window, Qt.Key_Escape)
        QTest.mouseRelease(
            window, Qt.LeftButton, Qt.NoModifier, start + QPointF(25, 20).toPoint()
        )
        self.assertEqual(changed.count(), 0)
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start + QPointF(25, 20).toPoint(), 30)
        QTest.mouseRelease(
            window, Qt.LeftButton, Qt.NoModifier, start + QPointF(25, 20).toPoint()
        )
        frame(window)
        self.assertEqual(changed.count(), 1)
        value = changed.at(0)[0].toVariant()
        self.assertEqual(value["key"], "title")
        self.assertEqual(value["after"]["height"] - value["before"]["height"], 20)
