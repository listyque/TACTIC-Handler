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


def page_menu(fixture, command):
    from PySide6.QtCore import QObject
    from tests.profile_ui_responsiveness import frame
    from tests.test_columns_table_view import _visual_items
    fixture.click('pageEditorToolsButton')
    button=fixture.item('pageEditorToolsButton')
    menu=button.parentItem().property('menu')
    assert menu is not None and menu.property('visible'), (command, menu)
    if menu.property('openingInputGuardActive'):
        guard=QSignalSpy(menu.openingInputGuardActiveChanged)
        assert guard.wait(1500), 'Native popup opening guard did not settle'
    content=menu.property('contentItem')
    rows=[]
    for item in _visual_items(content):
        value=item.property('modelData')
        if hasattr(value,'toVariant'):
            value=value.toVariant()
        if isinstance(value,dict) and value.get('command')==command:
            rows.append(item)
    assert len(rows)==1, command
    target=next(item for item in _visual_items(rows[0]) if item.objectName()=='actionMenuPrimaryTarget')
    window=target.window()
    spy=QSignalSpy(menu.triggered)
    point=target.mapToScene(QPointF(target.width()/2,target.height()/2)).toPoint()
    QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,point)
    if not spy.count():
        assert spy.wait(1500), command
    frame(fixture.window)


class PageOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.pool = Pool()
        self.host = DashboardEditor(
            SimpleNamespace(is_stream_server=True, can_manage_tools=True, debug_log=None)
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

    def test_latest_readonly_detail_preview_runs_after_a_stale_reply(self):
        from PySide6.QtCore import QCoreApplication
        self.enterContext(patch('thlib.tactic_classes.server_start',return_value=object()))
        self.host._document=copy.deepcopy(DOCUMENT)
        self.host._original=copy.deepcopy(DOCUMENT)
        self.host._preview_owner=SimpleNamespace(items=SimpleNamespace(model={}),shutdown=lambda:None)
        for outcome,changed_context in [('result',False),('error',False),('result',True),('error',True)]:
            with self.subTest(outcome=outcome,changed_context=changed_context):
                self.host._metadata['compiled']=dict(layoutHasDetails=True)
                self.host._detail_key='demo/asset?code=A'
                self.host._preview()
                old=self.pool.workers[-1]
                if changed_context:
                    self.host._generation+=1
                self.host._preview_owner.items.model=dict(sampleItems=[dict(record={'__search_key__':'demo/asset?code=B'})])
                self.host._samples_changed()
                self.host._timer.stop()
                self.host._preview()
                self.assertIs(self.host._preview_worker,old)
                if outcome=='result':
                    old.result.emit(dict(model=dict(layoutHasDetails=True),xml='<config/>'))
                else:
                    old.error.emit((dict(exception=ValueError('Old preview failed')),old))
                QCoreApplication.processEvents()
                self.assertTrue(self.host._timer.isActive(),'Latest preview must run even when the document is unchanged')
                self.assertFalse(self.host.dirty)
                self.host._timer.stop()
                self.host._preview()
                self.pool.workers[-1].result.emit(dict(model=dict(layoutHasDetails=True,layoutDetail={'searchKey':'demo/asset?code=B'}),xml='<config/>'))
                QCoreApplication.processEvents()
                self.assertEqual(self.host.metadata['compiled']['layoutDetail']['searchKey'],'demo/asset?code=B')
                self.assertFalse(self.host.error)


class PageChromeTests(unittest.TestCase):
    from tests.test_frame_table import FrameTableTests
    create = FrameTableTests.create
    close = FrameTableTests.close
    item = FrameTableTests.item
    click = FrameTableTests.click

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_empty_catalog_has_direct_creation_and_no_irrelevant_canvas_tools(self):
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtGui import QInputMethodEvent
        from tests.profile_ui_responsiveness import frame
        from tests.test_columns_table_view import _visual_items
        host = DashboardEditor(SimpleNamespace(is_stream_server=True, can_manage_tools=True, debug_log=None))
        self.addCleanup(host.shutdown)
        pool = Pool()
        self.enterContext(patch.object(env_inst, 'server_pool', pool))
        host._project = 'demo'
        host._can_write = host._loaded = True
        host._metadata = dict(revision='R1')
        window, view = self.create('features/administration/layouts/PageLayoutEditorView.qml', dict(controller=host), width=1100, height=740)
        self.assertIsNotNone(self.item(view, 'pageEmptyHint'))
        self.assertFalse(any(item.objectName() == 'pageCanvasSize' for item in _visual_items(view)))
        self.assertEqual(self.item(view, 'pageNew').property('text'), 'New page')
        for name in ['pageNew']:
            button = self.item(view, name)
            label = next(item for item in _visual_items(button) if item.objectName() == 'buttonLabel')
            self.assertFalse(label.property('truncated'), (name, label.width(), label.property('implicitWidth')))
        self.click(window, self.item(view, 'pageNew'))
        for name, value in [('pageLayoutName', 'new_page'), ('pageLayoutTitle', 'New page title')]:
            field = self.item(view, name)
            field.forceActiveFocus()
            frame(window)
            event = QInputMethodEvent()
            event.setCommitString(value)
            QCoreApplication.sendEvent(window.activeFocusItem(), event)
        self.click(window, self.item(view, 'pageLayoutCreate'))
        host._timer.stop()
        frame(window)
        self.assertEqual(host.document, dict(name='new_page', title='New page title', blocks=[]))
        self.assertTrue(host.dirty)
        self.assertEqual(self.item(view, 'pageLayoutChoice').property('displayText'), 'New page title')
        self.assertIsNone(host._pending_save)
        self.assertEqual(pool.workers, [])
        self.assertEqual(self.item(view, 'pageEditorToolsButton').property('text'), 'Actions')
        self.assertIsNotNone(self.item(view, 'pagePreviewToggle'))
        for language in ['en', 'ru']:
            view.setProperty('language', language)
            frame(window)
            for name in ['pageNew', 'pagePreviewToggle', 'pageSourceXml']:
                button = self.item(view, name)
                label = next(item for item in _visual_items(button) if item.objectName() == 'buttonLabel')
                self.assertFalse(label.property('truncated'), (language, name, label.width(), label.property('implicitWidth')))

    def test_item_preview_initializes_the_result_surface(self):
        from tests.test_workspace_result_item import _WorkspaceAppController
        from thlib.ui.layout_editor import LayoutEditorHost
        application=_WorkspaceAppController()
        application.is_stream_server=True
        application.can_manage_tools=True
        application.debug_log=None
        host=LayoutEditorHost(application)
        self.addCleanup(host.shutdown)
        window,view=self.create('features/table/DashboardItems.qml',dict(controller=application,
            owner=None,columnsController=None,users=[],surfacesModel=None,versionsModel=None,previewItems=host),
            width=400,height=600,context=dict(appController=application))
        self.assertIsNotNone(self.item(view,'searchResultsListView'))

    def test_tree_splitters_collapsed_panels_and_source_xml_do_not_edit(self):
        from tests.profile_ui_responsiveness import frame
        from tests.test_columns_table_view import _visual_items
        from PySide6.QtCore import QPoint
        host = DashboardEditor(SimpleNamespace(is_stream_server=True, can_manage_tools=True, debug_log=None))
        self.addCleanup(host.shutdown)
        host._document = copy.deepcopy(DOCUMENT)
        host._original = copy.deepcopy(DOCUMENT)
        host._identity = 'review'
        host._can_write = host._loaded = True
        host._checked_document = copy.deepcopy(DOCUMENT)
        host._metadata = dict(checkedDocument=copy.deepcopy(DOCUMENT), sourceXml='<config><view name="dashboard.review"/></config>')
        host._catalog = [dict(identity='review',label='Review')]
        window,view = self.create('features/administration/layouts/PageLayoutEditorView.qml',dict(controller=host),width=1400,height=900)
        self.assertEqual(self.item(view,'pageLayersPanel').width(),180)
        self.assertGreater(self.item(view,'pageLayersPanel').mapToItem(view,QPointF()).y(),self.item(view,'pageCanvasTools').height())
        self.assertTrue(any(item.objectName()=='pageBlock_0.0' for item in _visual_items(view)))
        self.click(window,self.item(view,'pageTreeToggle_0'))
        self.assertFalse(any(item.objectName()=='pageBlock_0.0' and item.isVisible() for item in _visual_items(view)))
        row=self.item(view,'pageBlock_0')
        row.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(window,Qt.Key_Right)
        frame(window)
        self.assertIsNotNone(self.item(view,'pageBlock_0.0'))
        for name,delta in [('pageLayersSplitter',QPoint(60,0)),('pagePropertiesSplitter',QPoint(-40,0))]:
            handle=self.item(view,name)
            point=handle.mapToScene(QPointF(handle.width()/2,handle.height()/2)).toPoint()
            QTest.mousePress(window,Qt.LeftButton,Qt.NoModifier,point)
            QTest.mouseMove(window,point+delta,20)
            QTest.mouseRelease(window,Qt.LeftButton,Qt.NoModifier,point+delta)
            frame(window)
        self.assertEqual(self.item(view,'pageLayersPanel').width(),240)
        self.assertEqual(self.item(view,'pagePropertiesPanel').width(),320)
        for prefix,expanded in [('Layers',240),('Properties',320)]:
            self.click(window,self.item(view,'page'+prefix+'Toggle'))
            self.assertEqual(self.item(view,'page'+prefix+'Panel').width(),32)
            self.click(window,self.item(view,'page'+prefix+'Toggle'))
            self.assertEqual(self.item(view,'page'+prefix+'Panel').width(),expanded)
        self.click(window,self.item(view,'pageSourceXml'))
        self.assertIsNotNone(self.item(view,'pageXmlSource'))
        self.click(window,self.item(view,'pageSourceXml'))
        self.assertEqual(self.item(view,'pageLayersPanel').width(),240)
        self.assertEqual(host.document,DOCUMENT)
        self.assertFalse(host.dirty)
        self.assertIsNone(host._pending_save)


class PageCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_administration_qml import AdministrationQmlTests

        AdministrationQmlTests.setUpClass()

    def test_multiple_selection_alignment_marquee_guides_and_style(self):
        from tests.test_administration_qml import AdministrationQmlTests
        from tests.profile_ui_responsiveness import frame
        from PySide6.QtCore import QPoint

        fixture = AdministrationQmlTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.window.resize(1800, 1000)
        editor = fixture.admin.dashboardEditor
        children = [
            dict(kind="text", text=name, width=120, height=50) for name in ("A", "B", "C")
        ]
        document = dict(
            name="selection",
            title="Selection",
            blocks=[dict(kind="column", height=400, children=children)],
        )
        nodes = [
            dict(
                kind="text",
                text=name,
                width="120px",
                height=50,
                editorPath=[0, index],
                offsetX=index * 140,
            )
            for index, name in enumerate(("A", "B", "C"))
        ]
        fixture.seed(
            editor,
            "selection",
            document,
            dict(
                revision="R1",
                checkedDocument=copy.deepcopy(document),
                searchTypes=[],
                compiled=dict(
                    targetSearchKey="sthpw/project?code=demo",
                    layoutNodes=[
                        dict(kind="group", height=400, editorPath=[0], children=nodes)
                    ],
                ),
            ),
        )
        fixture.admin.select_section("dashboards")
        frame(fixture.window)

        def center(key):
            target = fixture.item("canvasTarget_" + key)
            return target.mapToScene(
                QPointF(target.width() / 2, target.height() / 2)
            ).toPoint()

        QTest.mouseClick(fixture.window, Qt.LeftButton, Qt.NoModifier, center("0.0"))
        QTest.mouseClick(fixture.window, Qt.LeftButton, Qt.ControlModifier, center("0.1"))
        frame(fixture.window)
        self.assertTrue(
            fixture.item("pageSelectionCount").property("text").startswith("2 ")
        )
        self.assertFalse(editor.dirty)
        QTest.keyClick(fixture.window, Qt.Key_Right, Qt.ShiftModifier)
        frame(fixture.window)
        self.assertEqual(
            [row.get("offset_x") for row in editor.document["blocks"][0]["children"][:2]],
            [10, 10],
        )
        fixture.click("pageAction_undo")
        self.assertEqual(editor.document, document)
        fixture.item("pageAlign").forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_Down)
        frame(fixture.window)
        self.assertEqual(editor.document["blocks"][0]["children"][1]["offset_x"], -140)
        fixture.click("pageAction_undo")
        # Style uses the same selected group and the ordinary document history.
        field = fixture.item("pageAppearance_shadow")
        scroll = fixture.item("pageProperties")
        position = field.mapToItem(scroll, QPointF()).y()
        scroll.setProperty("contentY", max(0, position - 40))
        frame(fixture.window)
        field = fixture.item("pageAppearance_shadow")
        self.assertTrue(field.isEnabled())
        field.forceActiveFocus(Qt.TabFocusReason)
        frame(fixture.window)
        point = field.mapToScene(QPointF(10, field.height() / 2)).toPoint()
        QTest.mouseClick(fixture.window, Qt.LeftButton, Qt.NoModifier, point)
        frame(fixture.window)
        self.assertTrue(
            all(
                row["appearance"]["shadow"]
                for row in editor.document["blocks"][0]["children"][:2]
            )
        )
        fixture.click("pageAction_undo")
        self.assertEqual(editor.document, document)
        scroll.setProperty("contentY", 0)
        # Shift drag over the existing canvas chooses children, not their container.
        area = fixture.item("canvasMarqueeArea")
        first = fixture.item("canvasTarget_0.0").mapToItem(area, QPointF())
        second = fixture.item("canvasTarget_0.1")
        end = second.mapToItem(area, QPointF(second.width() + 2, second.height() + 2))
        start = area.mapToScene(first - QPointF(2, 2)).toPoint()
        finish = area.mapToScene(end).toPoint()
        QTest.mousePress(fixture.window, Qt.LeftButton, Qt.ShiftModifier, start)
        QTest.mouseMove(fixture.window, finish, 30)
        QTest.mouseRelease(fixture.window, Qt.LeftButton, Qt.ShiftModifier, finish)
        frame(fixture.window)
        self.assertTrue(
            fixture.item("pageSelectionCount").property("text").startswith("2 ")
        )
        point = center("0.0")
        QTest.mousePress(fixture.window, Qt.LeftButton, Qt.NoModifier, point)
        QTest.mouseMove(fixture.window, point + QPoint(18, 1), 30)
        frame(fixture.window)
        self.assertIsNotNone(fixture.item("canvasGuide_x"))
        QTest.keyClick(fixture.window, Qt.Key_Escape)
        QTest.mouseRelease(
            fixture.window, Qt.LeftButton, Qt.NoModifier, point + QPoint(18, 1)
        )
        self.assertEqual(editor.document, document)
        self.assertEqual(fixture.fixture.warnings, [])


    def test_canvas_viewport_keeps_logical_resize_and_read_scopes(self):
        from tests.test_administration_qml import AdministrationQmlTests
        from tests.profile_ui_responsiveness import frame
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QWheelEvent
        fixture = AdministrationQmlTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.window.resize(1700, 950)
        editor = fixture.admin.dashboardEditor
        fixture.seed(editor, 'review', DOCUMENT, dict(
            revision='R1', compiled=COMPILED,
            checkedDocument=copy.deepcopy(DOCUMENT), searchTypes=[]))
        fixture.admin.select_section('dashboards')
        frame(fixture.window)
        serial, source = editor._preview_serial, editor._source_serial
        page_menu(fixture, 'canvasSettings')
        field = fixture.item('pageCanvasPixels')
        field.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(fixture.window, Qt.Key_A, Qt.ControlModifier)
        for key in (Qt.Key_8, Qt.Key_0, Qt.Key_0):
            QTest.keyClick(fixture.window, key)
        QTest.keyClick(fixture.window, Qt.Key_Tab)
        frame(fixture.window)
        fixture.choose_page('pageCanvasZoom', '50')
        frame(fixture.window)
        paper = fixture.item('pageViewportPaper')
        self.assertEqual(paper.width(), 800)
        self.assertAlmostEqual(paper.mapRectToScene(paper.boundingRect()).width(), 400)
        self.assertFalse(editor.dirty)
        self.assertEqual(editor._preview_serial, serial)
        self.assertEqual(editor._source_serial, source)
        fixture.click('canvasTarget_0.0')
        frame(fixture.window)
        handle = fixture.item('canvasHandle_se')
        self.assertAlmostEqual(handle.mapRectToScene(handle.boundingRect()).width(), 14)
        point = handle.mapToScene(QPointF(handle.width() / 2, handle.height() / 2)).toPoint()
        QTest.mousePress(fixture.window, Qt.LeftButton, Qt.NoModifier, point)
        QTest.mouseMove(fixture.window, point + QPoint(20, 20), 30)
        QTest.mouseRelease(fixture.window, Qt.LeftButton, Qt.NoModifier, point + QPoint(20, 20))
        frame(fixture.window)
        self.assertEqual(editor.document['blocks'][0]['children'][0]['height'], 100)
        fixture.click('pageAction_undo')
        self.assertEqual(editor.document, DOCUMENT)
        fixture.choose_page('pageCanvasSize', '1280')
        fixture.choose_page('pageCanvasZoom', '200')
        frame(fixture.window)
        scroll = fixture.item('pageViewportScroll')
        for modifiers, axis in [(Qt.NoModifier, 'contentY'), (Qt.ShiftModifier, 'contentX')]:
            point = scroll.mapToScene(QPointF(30, 50))
            event = QWheelEvent(
                point, QPointF(fixture.window.mapToGlobal(point.toPoint())),
                QPoint(), QPoint(0, -120), Qt.NoButton, modifiers, Qt.NoScrollPhase, False)
            gui_test_application().sendEvent(fixture.window, event)
            frame(fixture.window)
            self.assertGreater(scroll.property(axis), 0)
        fixture.choose_page('pageCanvasSize', 'auto')
        fixture.choose_page('pageCanvasZoom', 'fit')
        self.assertFalse(editor.dirty)
        self.assertEqual(fixture.fixture.warnings, [], '\n'.join(fixture.fixture.warnings))

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
        page_menu(fixture, 'moveUp')
        for _ in range(4):
            fixture.click('pageAction_undo')
        self.assertEqual(editor.document, DOCUMENT)
        fixture.click('pageBlock_0')
        self.assertIsNotNone(fixture.item('pageProperty_gap'))
        fixture.click('pageBlock_page')
        with self.assertRaises(StopIteration):
            fixture.item('pageParent')
        fixture.click('pageBlock_0.0')
        page_menu(fixture, 'duplicate')
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
        fixture.click('pagePreviewToggle')
        with self.assertRaises(StopIteration):
            fixture.item("canvasTarget_0.0")
        with self.assertRaises(StopIteration):
            fixture.item("pageLayersPanel")
        self.assertFalse(editor.dirty)
        fixture.click('pagePreviewToggle')
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
