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
        return {key: scope.model for key, scope in self.scopes.items()}

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
