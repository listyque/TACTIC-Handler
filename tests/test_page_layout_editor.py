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

    def test_source_reads_coalesce_and_ignore_late_or_closed_replies(self):
        from PySide6.QtCore import QCoreApplication
        self.host.load_source('demo/asset')
        first=self.pool.workers[-1]
        self.host.load_source('demo/shot')
        self.assertEqual(len(self.pool.workers),1)
        first.result.emit(dict(searchType='demo/asset',fields=[dict(value='old')]))
        QCoreApplication.processEvents()
        self.assertEqual(len(self.pool.workers),2)
        self.assertNotEqual(self.host.metadata.get('dataSource',{}).get('searchType'),'demo/asset')
        second=self.pool.workers[-1]
        second.result.emit(dict(searchType='demo/shot',fields=[dict(value='name')]))
        QCoreApplication.processEvents()
        self.assertEqual(self.host.metadata['dataSource']['searchType'],'demo/shot')
        self.host.load_source('demo/asset')
        last=self.pool.workers[-1]
        self.host.shutdown()
        last.result.emit(dict(searchType='demo/asset'))
        QCoreApplication.processEvents()
        self.assertEqual(self.host.metadata['dataSource']['searchType'],'demo/shot')

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

    def test_structure_history_and_shortcuts_are_local(self):
        from tests.test_administration_qml import AdministrationQmlTests
        from tests.profile_ui_responsiveness import frame
        fixture = AdministrationQmlTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        editor = fixture.admin.dashboardEditor
        fixture.seed(editor, 'review', DOCUMENT, dict(revision='R1', compiled=COMPILED,
            checkedDocument=copy.deepcopy(DOCUMENT), searchTypes=[]))
        fixture.admin.select_section('dashboards')
        frame(fixture.window)
        fixture.window.resize(1700,950)
        frame(fixture.window)
        fixture.click('pageBlock_0.0')
        QTest.keyClick(fixture.window, Qt.Key_D, Qt.ControlModifier)
        frame(fixture.window)
        self.assertEqual(len(editor.document['blocks'][0]['children']), 2)
        fixture.item('pageAction_undo').forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_Z, Qt.ControlModifier)
        frame(fixture.window)
        self.assertEqual(editor.document, DOCUMENT)
        fixture.item('pageAction_redo').forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier)
        frame(fixture.window)
        self.assertEqual(len(editor.document['blocks'][0]['children']), 2)
        fixture.item('pageParent').forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_Up)
        frame(fixture.window)
        self.assertEqual(len(editor.document['blocks']), 2)
        fixture.item('pageParent').forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_Down)
        frame(fixture.window)
        self.assertEqual(len(editor.document['blocks']), 1)
        fixture.click('pageAction_reorder-1')
        for _ in range(4):
            fixture.click('pageAction_undo')
        self.assertEqual(editor.document, DOCUMENT)
        fixture.click('pageAncestor_0')
        self.assertIsNotNone(fixture.item('pageProperty_gap'))
        fixture.click('pageAncestor_page')
        with self.assertRaises(StopIteration):
            fixture.item('pageParent')
        fixture.click('pageBlock_0.0')
        fixture.click('pageAction_duplicate')
        field = fixture.item('pageProperty_title')
        field.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_X)
        QTest.keyClick(fixture.window, Qt.Key_Z, Qt.ControlModifier)
        frame(fixture.window)
        self.assertEqual(len(editor.document['blocks'][0]['children']), 2,
                         'Text Undo must not undo the duplicated widget')
        fixture.click('adminDiscardDocument')
        fixture.click('adminConfirmSave')
        self.assertEqual(editor.document, DOCUMENT)
        self.assertFalse(fixture.item('pageAction_undo').isEnabled())
        self.assertFalse(editor.busy)
        self.assertIsNone(editor._pending_save)
        self.assertEqual(fixture.fixture.warnings, [], '\n'.join(fixture.fixture.warnings))

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
        fixture.click("pagePreviewMode")
        with self.assertRaises(StopIteration):
            fixture.item("canvasTarget_0.0")
        with self.assertRaises(StopIteration):
            fixture.item("pageLayersPanel")
        self.assertFalse(editor.dirty)
        fixture.click("pagePreviewMode")
        target = fixture.item("canvasTarget_0.0")
        fixture.fixture.click(fixture.window, target)
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

    def test_native_data_controls_keep_typed_values_without_geometry_reads(self):
        from tests.test_administration_qml import AdministrationQmlTests
        from tests.profile_ui_responsiveness import frame
        from PySide6.QtCore import QCoreApplication

        fixture=AdministrationQmlTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.window.resize(1700,950)
        pool=Pool();self.enterContext(patch.object(env_inst,'server_pool',pool))
        editor=fixture.admin.dashboardEditor
        document=dict(name='data_controls',title='Data',blocks=[dict(kind='metric',title='Assets',search_type='demo/asset',filters=[])])
        compiled=dict(title='Data',targetSearchKey='sthpw/project?code=demo',layoutNodes=[dict(kind='metric',text='Assets',value=4,editorPath=[0])])
        fixture.seed(editor,'data_controls',document,dict(revision='R1',checkedDocument=copy.deepcopy(document),compiled=compiled,
            searchTypes=[dict(value='demo/asset',label='Assets',projectOwned=True)]))
        fixture.admin.select_section('dashboards');frame(fixture.window)
        fixture.click('pageBlock_0');frame(fixture.window)
        metadata=dict(searchType='demo/asset',fields=[dict(value='code',label='Code',dataType='varchar'),
            dict(value='amount',label='Amount',dataType='integer'),dict(value='active',label='Active',dataType='boolean')],
            tableViews=[],itemViews=[],records=[])
        self.assertIsNotNone(editor._source_worker)
        editor._source_worker.result.emit(metadata);QCoreApplication.processEvents();frame(fixture.window)
        def visible(name):
            item=fixture.item(name);scroll=fixture.item('pageProperties')
            y=item.mapToItem(scroll,QPointF()).y()
            if y<0 or y+item.height()>scroll.height():
                scroll.setProperty('contentY',max(0,min(scroll.property('contentHeight')-scroll.height(),scroll.property('contentY')+y-16)))
                frame(fixture.window)
            return item
        def click(name):
            fixture.fixture.click(fixture.window,visible(name))
        def choose(name,value):
            item=visible(name);rows=item.property('model')
            rows=rows.toVariant() if hasattr(rows,'toVariant') else rows
            index=next(index for index,row in enumerate(rows) if row['value']==value)
            current=item.property('currentIndex')
            for _ in range(abs(index-current)):
                item=visible(name)
                item.forceActiveFocus(Qt.TabFocusReason)
                QTest.keyClick(fixture.window,Qt.Key_Down if index>current else Qt.Key_Up)
                frame(fixture.window)
            self.assertEqual(fixture.item(name).property('currentValue'),value)
        click('pageFilterAdd')
        choose('pageFilter_0_column','amount')
        self.assertEqual(editor.document['blocks'][0]['filters'][0]['value'],0)
        choose('pageFilter_0_relation','notEmpty')
        self.assertIsNone(editor.document['blocks'][0]['filters'][0]['value'])
        handle=fixture.item('canvasHandle_se')
        start=handle.mapToScene(QPointF(handle.width()/2,handle.height()/2)).toPoint()
        QTest.mousePress(fixture.window,Qt.LeftButton,Qt.NoModifier,start)
        QTest.mouseMove(fixture.window,start+QPointF(20,20).toPoint(),30)
        QTest.mouseRelease(fixture.window,Qt.LeftButton,Qt.NoModifier,start+QPointF(20,20).toPoint())
        frame(fixture.window)
        self.assertIn('value',editor.document['blocks'][0]['filters'][0])
        self.assertIsNone(editor.document['blocks'][0]['filters'][0]['value'])
        choose('pageFilter_0_column','active')
        self.assertIs(editor.document['blocks'][0]['filters'][0]['value'],False)
        serial=editor._source_serial
        fixture.window.resize(1500,850);frame(fixture.window)
        self.assertEqual(editor._source_serial,serial)
        self.assertEqual(fixture.fixture.warnings,[])


class ItemCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    from tests.test_frame_table import FrameTableTests

    create = FrameTableTests.create
    close = FrameTableTests.close
    click = FrameTableTests.click
    item = FrameTableTests.item

    def test_flow_children_select_and_alt_click_reaches_the_container(self):
        from tests.profile_ui_responsiveness import frame

        common = dict(row=1, column=1, span=12, rows=1, height=60, options={}, variant="all")
        layout = dict(flow="grid", collection="tree", columns=12, elements=[
            dict(common, name="group", kind="group", title="Header", parent="", flow="row", columns=12),
            dict(common, name="title", kind="title", title="Title", parent="group")])
        window, view = self.create("features/search/ConfiguredItem.qml", dict(
            layout=layout, record=dict(kind="object", title="Asset", record={}),
            controller={}, nodeId="A", editing=True, selectedElement="title"), 600, 160)
        selected = QSignalSpy(view.elementSelected)
        changed = QSignalSpy(view.geometryEdited)
        target = self.item(view, "canvasTarget_title")
        position = target.mapToScene(QPointF(target.width()/2, target.height()/2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position)
        self.assertEqual(selected.at(selected.count()-1)[0], "title")
        with self.assertRaises(StopIteration):
            self.item(view, "canvasHandle_se")
        QTest.mouseClick(window, Qt.LeftButton, Qt.AltModifier, position)
        self.assertEqual(selected.at(selected.count()-1)[0], "group")
        self.assertEqual(changed.count(), 0)
        view.setProperty("editing", False)
        view.setProperty("selectedElement", "")
        frame(window)
        with self.assertRaises(StopIteration):
            self.item(view, "canvasTarget_title")

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
