"""Native input, composition geometry, retained scopes and report pagination."""

import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtPrintSupport import QPrinter
from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns, _visual_items
from tests.test_table_nested import Scope
from thlib.ui.table.report import document


class Services(QObject):
    documentChanged = Signal()
    nestedChanged = Signal()

    def __init__(self, model):
        super().__init__()
        self.state, self.events = model, []
        self.scopes = {key: Scope() for key in ('customLayout_0_0', 'customLayout_0_1')}
        self._report_models = {}
        self.document_data = model
        from thlib.ui.table.custom_layout import CustomLayoutController
        CustomLayoutController._open_reports(self)

    @Property('QVariantMap', notify=documentChanged)
    def document(self):
        return self.state

    @Property(QObject, constant=True)
    def customLayout(self):
        return self

    @Property(int, notify=nestedChanged)
    def nestedRevision(self):
        return 0

    @Property('QVariantMap', notify=nestedChanged)
    def tableModels(self):
        return {**{key: scope.model for key, scope in self.scopes.items()},**self._report_models}

    @Slot(str, int, result=QObject)
    def table(self, key, revision=0):
        return self.scopes.get(key)

    @Slot('QVariantMap')
    def activate(self, value):
        self.events.append(dict(value))

    @Slot(QObject, 'QVariantMap')
    def format_document(self, document, style):
        from thlib.ui.rich_text_document import format_readonly_document
        format_readonly_document(document, style)

    @Slot('QVariantMap')
    def set_state(self, state):
        self.state['layoutState'] = dict(state)
        self.documentChanged.emit()

    @Slot(str)
    def select_page(self, key):
        self.events.append(dict(type='tab', key=key))

    @Slot(str)
    def close_page(self, key):
        self.events.append(dict(type='close-tab', key=key))

    @Slot('QVariantMap')
    def apply_filters(self, values):
        self.events.append(dict(type='filters',values=values))

    @Slot(str)
    def filter_error(self, message):
        self.events.append(dict(type='filter-error',message=message))

    @Slot(str, 'QVariantMap', 'QVariantList')
    def open_links(self, node, cell, keys):
        self.events.append(dict(type='links', node=node, keys=list(keys)))


class CustomLayouts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item

    def test_page_regions_keep_header_footer_and_scroll_content_independently(self):
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtTest import QTest

        services = Services(dict(layoutView='dashboard.regions', layoutFilters=[
            dict(name='filter'+str(i), title='Filter '+str(i), value='value', enabled=True, relation='=', dataType='text')
            for i in range(4)], layoutNodes=[
                dict(kind='text', text='Header instructions', region='header', editorPath=[0]),
                dict(kind='metric', text='Scrollable report', value=25, height=1000, editorPath=[1]),
                dict(kind='button', text='Open project', href='https://example.com/project', region='footer', editorPath=[2])]))
        window, view = self.create('features/table/CustomLayoutView.qml', dict(
            services=services, controller=_TableController(), columnsController=_TableColumns(),
            users=None, administration=None), width=1000, height=650)
        footer_button = self.item(view, 'customLayout_2')
        for width, height in ((1000,650),(360,500),(700,800)):
            window.resize(width,height);view.setWidth(width);view.setHeight(height);frames.frame(window)
            header = self.item(view,'customLayoutHeader')
            body = self.item(view,'customLayoutScroll')
            footer = self.item(view,'customLayoutFooter')
            self.assertAlmostEqual(body.mapToItem(view,QPointF()).y(), header.mapToItem(view,QPointF()).y()+header.height())
            self.assertAlmostEqual(body.mapToItem(view,QPointF()).y()+body.height(), footer.mapToItem(view,QPointF()).y())
            self.assertAlmostEqual(footer.mapToItem(view,QPointF()).y()+footer.height(),height)
            self.assertEqual(self.item(view,'customLayout_2'), footer_button)
            point = body.mapToScene(QPointF(body.width()/2,body.height()/2))
            event = QWheelEvent(point, QPointF(window.mapToGlobal(point.toPoint())), QPoint(), QPoint(0,-1200), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            self.app.sendEvent(window,event);QTest.qWait(150)
            self.assertGreater(body.property('contentY'),0)
            self.assertAlmostEqual(footer.mapToItem(view,QPointF()).y()+footer.height(),height)
            self.click(window,footer_button)
            self.assertEqual(services.events[-1]['name'],'layout-link')
            footer_button.forceActiveFocus(); QTest.keyClick(window,Qt.Key_Space)
            self.assertEqual(services.events[-1]['name'],'layout-link')
            if width == 360:
                scroll = self.item(view,'customLayoutHeaderScroll')
                self.assertGreater(scroll.property('contentHeight'),scroll.height())
                self.assertTrue(self.item(view,'customLayoutHeaderScrollBar').isVisible())

    def test_markdown_close_drops_queued_formatting(self):
        window, pane = self.create(
            'controls/DocumentPane.qml', dict(text='Original', summary='Summary'),
            width=500, height=300)
        pane.setProperty('text', 'Changed before closing')
        pane.setProperty('summary', 'Changed summary before closing')
        # Cleanup destroys the pane before processing its queued format callbacks.

    def test_dashboard_grid_spans_content_size_and_native_button(self):
        from PySide6.QtCore import QPointF
        import os
        from PySide6.QtGui import QFontDatabase

        # Offscreen runs need the same explicit text fonts as the paired capture.
        for name in ("segoeui.ttf", "seguisb.ttf"):
            path = Path(os.environ.get("WINDIR", "")) / "Fonts" / name
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
        services = Services(
            dict(
                targetSearchKey="sthpw/project?code=demo",
                layoutNodes=[
                    dict(
                        kind="grid",
                        editorPath=[0],
                        columns=3,
                        min_cell_width=200,
                        row_height=100,
                        gap=10,
                        children=[
                            dict(
                                kind="text",
                                text="Overview",
                                textRole="heading",
                                textWeight=600,
                                editorPath=[0, 0],
                                columnSpan=2,
                            ),
                            dict(
                                kind="icon", icon="folder", iconSize=32, editorPath=[0, 1]
                            ),
                            dict(
                                kind="button",
                                text="Open project",
                                href="https://example.com/project",
                                buttonStyle="primary",
                                editorPath=[0, 2],
                                sizing=dict(width_mode="content", height_mode="content"),
                            ),
                            dict(kind="spacer", editorPath=[0, 3]),
                        ],
                    )
                ],
            )
        )
        window, view = self.create(
            "features/table/CustomLayoutView.qml",
            dict(
                services=services,
                controller=_TableController(),
                columnsController=_TableColumns(),
                users=None,
                administration=None,
            ),
            width=1000,
            height=600,
        )
        first = self.item(view, "customLayout_0_0_block")
        second = self.item(view, "customLayout_0_1_block")
        self.assertEqual(self.item(view, "customLayout_0_block").width(), 1000)
        self.assertGreater(first.width(), second.width() * 1.8)
        button = self.item(view, "customLayout_0_2")
        self.assertGreater(button.width(), 100)
        self.click(window, button)
        self.assertEqual(services.events[-1]["name"], "layout-link")
        self.assertEqual(services.events[-1]["href"], "https://example.com/project")
        window.resize(420, 600)
        view.setWidth(420)
        frames.frame(window)
        one = self.item(view, "customLayout_0_1_block").mapToScene(QPointF())
        two = self.item(view, "customLayout_0_2_block").mapToScene(QPointF())
        self.assertGreater(two.x(), one.x())
        self.assertAlmostEqual(one.y(), two.y())
        window.resize(390, 600)
        view.setWidth(390)
        frames.frame(window)
        one = self.item(view, "customLayout_0_1_block").mapToScene(QPointF())
        two = self.item(view, "customLayout_0_2_block").mapToScene(QPointF())
        self.assertAlmostEqual(one.x(), two.x())
        self.assertGreater(two.y(), one.y())
        self.assertIsNotNone(self.item(view, "customLayout_0_3_block"))

    def test_page_filters_apply_typed_values_and_report_grid_is_native(self):
        from PySide6.QtCore import QCoreApplication
        report=dict(columns=[dict(key='group_0',title='Status',kind='group'),dict(key='count',title='Count',kind='measure')],
                    rows=[dict(group_0='ready',count=0)],measure='count',truncated=False)
        services=Services(dict(layoutView='dashboard.report',layoutFilters=[dict(name='amount',title='Amount',
            value=0,enabled=False,relation='>=',dataType='numeric')],
            layoutNodes=[dict(kind='summary',text='Report',height=250,report=report),dict(kind='metric',text='Empty sum',value=None)]))
        window,view=self.create('features/table/CustomLayoutView.qml',dict(services=services,controller=_TableController(),
            columnsController=_TableColumns(),users=None,administration=None),width=1000,height=600)
        self.click(window,self.item(view,'pageRuntime_amount_enabled'))
        self.click(window,self.item(view,'pageRuntimeApply'))
        self.assertEqual(services.events[-1],dict(type='filters',values=dict(amount=dict(enabled=True,value=0))))
        services.documentChanged.emit();frames.frame(window)
        window.resize(850,600);view.setWidth(850);frames.frame(window)
        self.assertTrue(self.item(view,'pageRuntime_amount_enabled').property('checked'))
        self.assertEqual(self.item(view,'customLayout_0_grid_cell_0_1').property('text'),'0')
        self.assertEqual(self.item(view,'customLayout_1_value').property('text'),'—')
        self.click(window,self.item(view,'pageRuntimeReset'))
        self.assertEqual(services.events[-1],dict(type='filters',values={}))
        view.setProperty('editing',True);frames.frame(window)
        self.assertFalse(self.item(view,'pageRuntimeApply').isEnabled())

    def test_russian_page_filter_buttons_show_complete_captions(self):
        import os
        from PySide6.QtGui import QFontDatabase
        for name in ('segoeui.ttf', 'segoeuib.ttf'):
            path = Path(os.environ.get('WINDIR', '')) / 'Fonts' / name
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
        services = Services(dict(layoutView='dashboard.report', layoutNodes=[], layoutFilters=[
            dict(name='name', title='Название', value='%', enabled=False, relation='like', dataType='text')]))
        window, view = self.create('features/table/CustomLayoutView.qml', dict(services=services,
            controller=_TableController(), columnsController=_TableColumns(), users=None,
            administration=None, language='ru'), width=1000, height=300)
        for key in ('pageRuntimeApply', 'pageRuntimeReset'):
            captions = [item for item in _visual_items(self.item(view, key))
                        if item.property('text') in ('Применить фильтры', 'Сбросить фильтры')
                        and item.metaObject().indexOfProperty('truncated') >= 0]
            self.assertTrue(captions, key)
            self.assertFalse(any(item.property('truncated') for item in captions),
                             (key, self.item(view, key).width(),
                              [(item.width(), item.implicitWidth()) for item in captions]))

    def test_planner_embeds_two_live_tables_and_reflows_without_clipping(self):
        model = dict(
            layoutNodes=[
                dict(
                    kind='row',
                    children=[
                        dict(kind='table', text='Assets', table={}),
                        dict(kind='table', text='Shots', table={}),
                    ],
                )
            ]
        )
        services = Services(model)
        controller = _TableController()
        window, view = self.create(
            'features/table/CustomLayoutView.qml',
            dict(
                services=services,
                controller=controller,
                columnsController=_TableColumns(),
                users=None,
                administration=None,
            ),
            width=1000,
            height=520,
        )
        selections = [
            item for item in _visual_items(view) if item.objectName() == 'nestedSelect'
        ]
        self.assertEqual(len(selections), 2)
        from PySide6.QtCore import QPointF

        self.click(
            window, min(selections, key=lambda item: item.mapToScene(QPointF(0, 0)).x())
        )
        self.assertEqual(services.scopes['customLayout_0_0'].state['selected'], ['A'])
        self.assertEqual(services.scopes['customLayout_0_1'].state['selected'], [])
        self.assertEqual(controller.selections, [])
        view.setProperty('editing', True)
        frames.frame(window)
        self.assertTrue(all(not item.isEnabled() for item in selections))
        view.setProperty('editing', False)
        frames.frame(window)
        view.setWidth(400)
        window.resize(400, 520)
        frames.frame(window)
        scene = view.property('scene').toVariant()
        tables = [
            node for node in scene['nodes'][-1]['children'] if node['kind'] == 'View'
        ]
        self.assertEqual(tables[0]['x'], tables[1]['x'])
        self.assertGreater(tables[1]['y'], tables[0]['y'] + tables[0]['height'])
        self.assertIsNotNone(self.item(view, 'customLayoutScrollBar'))

    def test_review_choice_keyboard_and_submit_use_the_current_value(self):
        choice = dict(
            kind='choice',
            selector='review',
            name='review',
            options=[dict(value='A', text='Daily'), dict(value='B', text='Client')],
        )
        services = Services(
            dict(
                layoutNodes=[
                    choice,
                    dict(
                        kind='action',
                        text='Submit',
                        selector='submit',
                        javascript='submit()',
                    ),
                ],
                layoutState=dict(root={}, controls=[choice]),
            )
        )
        window, view = self.create(
            'features/table/CustomLayoutView.qml',
            dict(
                services=services,
                controller=_TableController(),
                columnsController=_TableColumns(),
                users=None,
                administration=None,
            ),
            width=400,
            height=200,
        )
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        control = self.item(view, 'customLayout_0')
        control.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Down)
        frames.frame(window)
        self.assertEqual(
            services.state['layoutState']['controls'][0]['selectedValue'], 'B'
        )
        self.click(window, self.item(view, 'customLayout_1'))
        self.assertEqual(services.events[-1]['selector'], 'submit')

    def test_planner_native_drag_reaches_the_existing_link_owner(self):
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtTest import QTest

        services = Services(
            dict(
                layoutNodes=[
                    dict(
                        kind='row',
                        children=[
                            dict(kind='table', text='Assets', table={}),
                            dict(kind='table', text='Shots', table={}),
                        ],
                    )
                ]
            )
        )
        asset = services.scopes['customLayout_0_0']
        asset.state['searchType'] = 'vfx/asset'
        asset.state['rows'][0]['key'] = 'vfx/asset?code=A'
        shot = services.scopes['customLayout_0_1']
        shot.state['searchType'] = 'vfx/shot'
        shot.state['columns'] = [
            dict(name='assets', title='Assets', width=180, cell=dict(kind='commands'))
        ]
        shot.state['rows'][0]['cells'] = dict(
            assets=dict(
                text='',
                links=[],
                acceptedType='vfx/asset',
                available=True,
                columnName='assets',
            )
        )
        window, view = self.create(
            'features/table/CustomLayoutView.qml',
            dict(
                services=services,
                controller=_TableController(),
                columnsController=_TableColumns(),
                users=None,
                administration=None,
            ),
            width=1000,
            height=520,
        )
        handles = [
            item for item in _visual_items(view) if item.objectName() == 'nestedDrag'
        ]
        handle = min(handles, key=lambda item: item.mapToScene(QPointF(0, 0)).x())
        target = self.item(view, 'dropSurface')
        start = handle.mapToScene(
            QPointF(handle.width() / 2, handle.height() / 2)
        ).toPoint()
        end = target.mapToScene(
            QPointF(target.width() / 2, target.height() / 2)
        ).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start + frames.QPointF(20, 0).toPoint(), 20)
        QTest.mouseMove(window, end, 20)
        frames.frame(window)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
        frames.frame(window)
        self.assertEqual(services.events[-1]['keys'], ['vfx/asset?code=A'])

    def test_details_ignore_stale_selection_without_reopening_tree(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from tests.test_table_service_workflows import Application
        from thlib.ui.table.services import TableServicesController
        application=Application()
        application.tab.layout_view='dashboard.work'
        application.selected_node_id='A'
        application.workspace_model=Mock()
        application.workspace_model.node_for.side_effect=lambda key:SimpleNamespace(node_type='sobject',search_key='demo/asset?project=demo&code='+key)
        services=TableServicesController(application)
        self.addCleanup(services.shutdown)
        owner=services.workspaceLayout
        owner.tab=application.tab
        owner.current='work'
        owner.context=dict(project='demo')
        owner.document_data=dict(layoutView='dashboard.work',targetSearchKey='sthpw/project?code=demo',layoutItems=dict(searchType='demo/asset'),layoutNodes=[dict(kind='details')])
        callbacks=[]
        with patch.object(services,'_run',side_effect=lambda operation,loaded,**kw:callbacks.append(loaded)),patch('thlib.tactic_classes.server_start'),patch.object(owner,'show_items') as tree_reload:
            application.selected_node_changed.emit()
            application.selected_node_id='B'
            application.selected_node_changed.emit()
            callbacks[0](dict(info=dict(title='stale',layoutNodes=[])))
            self.assertTrue(owner.document_data['layoutDetail']['busy'])
            callbacks[1](dict(info=dict(title='Current item',targetSearchKey='demo/asset?project=demo&code=B',layoutNodes=[])))
            self.assertEqual(owner.document_data['layoutDetail']['title'],'Current item')
            tree_reload.assert_not_called()

    def test_retained_layout_tabs_keep_selection_and_dispose_closed_scopes(self):
        from unittest.mock import patch
        from tests.test_table_service_workflows import Application
        from thlib.ui.table.services import TableServicesController

        application = Application()
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        context = dict(project='demo', searchKey=application.node.search_key)

        def model(title):
            return dict(
                title=title,
                nodeId='A',
                layoutNodes=[
                    dict(
                        kind='table',
                        text='Assets',
                        table=dict(
                            searchType='demo/asset',
                            parentKey=application.node.search_key,
                        ),
                    )
                ],
            )

        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            owner._document = model('First')
            owner.customLayout.open(application.tab, context, 'first')
            first = owner.customLayout.scopes['customLayout_0']
            first._model['selected'] = ['A']
            owner._document = model('Second')
            owner.customLayout.open(application.tab, context, 'second')
            self.assertFalse(first.open)
            owner.customLayout.select_page('first')
            self.assertEqual(first.model['selected'], ['A'])
            self.assertTrue(first.open)
            self.assertEqual(owner.document['title'], 'First')
            owner.customLayout.close_page('second')
            self.assertEqual(list(owner.customLayout.pages), ['first'])
            self.assertEqual(len(owner._nested_scopes), 1)
            application._sessions = {}
            owner._prune_nested()
            self.assertEqual(owner.document, {})
            self.assertEqual(owner.customLayout.pages, {})
            self.assertFalse(owner._nested_scopes)

    def test_inline_composition_opens_the_complete_document_owner(self):
        from unittest.mock import patch
        from tests.test_table_service_workflows import Application
        from thlib.ui.table.services import TableServicesController

        application = Application()
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        cell = dict(
            layoutView='planner',
            targetSearchKey=application.node.search_key,
            layoutNodes=[
                dict(
                    kind='table',
                    text='Assets',
                    table=dict(
                        searchType='demo/asset', parentKey=application.node.search_key
                    ),
                )
            ],
        )
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            window, view = self.create(
                'features/table/ServiceCell.qml',
                dict(
                    controller=_TableController(),
                    services=owner,
                    administration=None,
                    nodeId='A',
                    cell=cell,
                ),
                width=220,
                height=58,
            )
            self.click(window, self.item(view, 'tableLayoutDocument'))
            self.assertEqual(owner.document['layoutNodes'], cell['layoutNodes'])
            self.assertEqual(len(owner.customLayout.scopes), 1)
            application.open_window.assert_called_once_with('table_document')
            with patch(
                'thlib.tactic_classes.server_start',
                side_effect=PermissionError('Sign in again'),
            ):
                owner.customLayout.print_report()
            self.assertEqual(owner.document['layoutError'], 'Sign in again')
            from unittest.mock import Mock

            with (
                patch.object(owner, '_run'),
                patch('thlib.tactic_classes.server_start', return_value=Mock()),
                patch('thlib.ui.table.scripts.TableScriptRunner') as runner,
            ):
                owner.customLayout.run('alert(bvr.search_key)')
            self.assertEqual(runner.call_args.args[1]['searchType'], 'demo/asset')

    def test_native_report_keeps_table_rows_and_paginates_pdf(self):
        report = dict(
            blocks=[
                dict(kind='text', text='SH010 Shot Sheet'),
                dict(
                    kind='table',
                    title='Tasks',
                    columns=['Code', 'Description'],
                    rows=[[str(index), 'Animation'] for index in range(150)],
                ),
            ]
        )
        text = document(report)
        self.assertIn('149', text.toPlainText())
        directory = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(directory) / 'report.pdf'
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(path))
        text.print_(printer)
        self.assertTrue(path.read_bytes().startswith(b'%PDF'))
        import re

        self.assertGreater(len(re.findall(rb'/Type /Page\b', path.read_bytes())), 1)
