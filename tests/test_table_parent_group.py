"""Parent picker exercises the real QML presenter and house input controls."""
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt, QPoint
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtTest import QTest

import tests.test_frame_table as frames


class ParentResponses(QObject):
    seedChanged = Signal()
    openChanged = Signal()
    received = Signal(str, 'QVariantMap', str, bool)

    def __init__(self, count=2, uncertain=False):
        super().__init__()
        self.calls = []
        self.finished = []
        self.uncertain = uncertain
        self._open = True
        self._rows = [dict(searchKey='contract/entity?project=demo&code=' + str(index),
            code=str(index), title='Parent ' + str(index), revision='r' + str(index)) for index in range(count)]

    @Property('QVariantMap', notify=seedChanged)
    def seed(self):
        return dict(targetSearchKey='sthpw/note?code=N1', sourceId='1', projectCode='demo',
            tableView='table', columnName='parent', sourceRevision='source', sourceTitle='Review note')

    @Property(bool, notify=openChanged)
    def isOpen(self):
        return self._open

    @Slot('QVariantMap')
    def request(self, request):
        self.calls.append(dict(request))
        operation = request['action']
        if operation == 'prepare':
            result = dict(sourceId='1', sourceTitle='Review note', expectedRevision='captured',
                currentParentKey=self._rows[0]['searchKey'], currentParent=self._rows[0],
                parentType='contract/entity', parentTypes=[dict(value='contract/entity', label='Entities')])
        elif operation == 'candidates':
            offset = request.get('offset', 0)
            result = dict(rows=self._rows[offset:offset + 50], hasNext=len(self._rows) > offset + 50)
        elif operation == 'save' and self.uncertain:
            self.received.emit(operation, {}, 'Unable to reach the server.', True)
            return
        else:
            result = dict(state='saved')
        self.received.emit(operation, result, '', False)

    @Slot(bool)
    def finish(self, saved):
        self.finished.append(saved)
        self._open = False
        self.openChanged.emit()


class TableParentGroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    def setUp(self):
        from thlib.environment import env_mode
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.enterContext(patch.object(env_mode, 'current_path', directory.name))

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def test_pointer_selection_and_space_save_capture_exact_target(self):
        ports = ParentResponses()
        window, view = self.create('features/table/ParentGroupView.qml', dict(owner=ports), width=380, height=480)
        self.assertEqual(len(ports.calls), 2)
        self.click(window, self.item(view, 'parentCandidate:' + ports._rows[1]['searchKey']))
        save = self.item(view, 'parentSave')
        self.assertTrue(save.isEnabled())
        save.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        frames.frame(window)
        self.assertEqual(ports.finished, [True])
        request = ports.calls[-1]
        self.assertEqual(request['parent_key'], ports._rows[1]['searchKey'])
        self.assertEqual(request['parent_revision'], 'r1')
        self.assertEqual(request['source_id'], '1')
        self.assertEqual(request['expected_revision'], 'captured')

    def test_uncertain_write_checks_before_retry_and_cancel_preserves_draft(self):
        ports = ParentResponses(uncertain=True)
        window, view = self.create('features/table/ParentGroupView.qml', dict(owner=ports), width=320, height=480)
        self.click(window, self.item(view, 'parentCandidate:' + ports._rows[1]['searchKey']))
        self.click(window, self.item(view, 'parentCancel'))
        self.assertEqual(ports.finished, [])
        self.click(window, self.item(view, 'confirmationReject'))
        self.assertTrue(self.item(view, 'parentSave').isEnabled())
        self.click(window, self.item(view, 'parentSave'))
        self.assertEqual(ports.calls[-1]['action'], 'save')
        self.assertEqual(ports.finished, [])
        self.click(window, self.item(view, 'parentSave'))
        self.assertEqual(ports.calls[-1]['action'], 'check')
        self.assertEqual(ports.finished, [True])

    def test_ime_query_and_virtualized_long_list_keep_shared_scrollbar(self):
        ports = ParentResponses(count=200)
        window, view = self.create('features/table/ParentGroupView.qml', dict(owner=ports), width=320, height=480)
        field = self.item(view, 'parentQuery')
        self.click(window, field)
        event = QInputMethodEvent()
        event.setCommitString('Родитель')
        QGuiApplication.sendEvent(field, event)
        QTest.keyClick(window, Qt.Key_Return)
        frames.frame(window)
        self.assertEqual(ports.calls[-1]['query'], 'Родитель')
        for _ in range(3):
            self.click(window, self.item(view, 'parentMore'))
        bar = self.item(view, 'parentScrollBar')
        self.assertTrue(bar.isVisible())
        self.assertGreater(bar.width(), 0)
        labels = [item for item in frames._visual_items(view) if item.objectName().startswith('parentCandidateTitle:')]
        self.assertLess(len(labels), 40)


class ParentDragPorts(QObject):
    @Property(int, constant=True)
    def nestedRevision(self):
        return 0

    @Slot(str, int, result=QObject)
    def nested_row(self, node_id, revision):
        return None

    def __init__(self):
        super().__init__()
        self.calls = []

    @Property(QObject, constant=True)
    def parentGroups(self):
        return self

    @Slot(QObject, str, 'QVariantMap', str)
    def open(self, anchor, node, cell, key):
        self.calls.append(('parent', node, dict(cell), key))

    @Slot('QVariantMap')
    def create_child(self, cell):
        self.calls.append(('create', dict(cell)))

    @Slot(str, 'QVariantMap', 'QVariantList')
    def open_links(self, node, cell, keys):
        self.calls.append(('links', node, dict(cell), list(keys)))

    @Slot(str)
    def report_error(self, message):
        self.calls.append(('error', message))


class TableParentGroupingTests(TableParentGroupTests):
    def test_actual_drag_delivers_value_to_parent_and_existing_link_adapter(self):
        from pathlib import Path
        fixture = str(Path(__file__).parent / 'fixtures/frame_table_parent_drag.qml')
        key = 'contract/entity?project=demo&code=B'
        cells = [dict(parentGrouping=False, parentEditable=True, targetSearchKey='sthpw/note?code=N1', text='A'),
            dict(kind='commands', acceptedType='contract/entity', links=[], available=True)]
        for kind, cell in zip(('parent', 'links'), cells):
            ports = ParentDragPorts()
            window, view = self.create(fixture, dict(controller=frames._TableController(), services=ports, cell=cell), width=400, height=120)
            QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(40, 45))
            for x in (60, 80, 110, 160, 220):
                QTest.mouseMove(window, QPoint(x, 45), 20)
            QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(220, 45))
            frames.frame(window)
            self.assertEqual(len(ports.calls), 1, ports.calls)
            self.assertEqual(ports.calls[0][0], kind)
            self.assertEqual(ports.calls[0][3], key if kind == 'parent' else [key])

    def test_actual_table_header_toggle_and_add_use_existing_owners(self):
        from tests.test_result_organization import _node
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        class Controller(frames._TableController):
            @Property(bool, constant=True)
            def can_manage_tools(self):
                return True
            @Property(str, constant=True)
            def server_url(self):
                return ''
        model, controller, ports = WorkspaceItemModel(), Controller(), ParentDragPorts()
        cell = dict(groupKey='contract/entity?project=demo&code=A', text='A', parent=dict(
            searchKey='contract/entity?project=demo&code=A', code='A', name='Parent', description='Description', preview={}))
        node = _node('1', 'First')
        node.values.update(parent='A', __tableParentGroups={'parent': cell})
        model.set_organization(group_mode='column:parent')
        model.replace_nodes([node])
        window, view = self.create('SearchResultTable.qml', dict(controller=controller,
            resultModel=model, columnsController=frames._TableColumns(), tableServices=ports), width=700, height=200)
        header = self.item(view, 'searchResultTableParentGroup')
        self.assertEqual(header.height(), 64)
        self.click(window, self.item(header, 'parentGroupToggle'))
        self.assertEqual(controller.toggled_nodes, [model._root_groups[0].node_id])
        self.click(window, self.item(header, 'parentGroupCreate'))
        self.assertEqual(ports.calls, [('create', cell)])

    def test_missing_parent_groups_follow_the_same_canonical_order_as_the_browser(self):
        from tests.test_result_organization import _node
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        model = WorkspaceItemModel()
        keys = ['sthpw/login?code=A', 'missing:contract/missing?code=A', 'no-parent']
        nodes = []
        for index, key in enumerate(keys):
            node = _node(str(index), 'Row ' + str(index))
            cell = dict(groupKey=key, text='A' if index == 0 else '')
            if index == 1:
                cell['missingParentKey'] = 'contract/missing?code=A'
            node.values.update(parent=cell['text'], __tableParentGroups={'parent': cell})
            nodes.append(node)
        model.set_organization(group_mode='column:parent')
        model.replace_nodes(nodes)
        self.assertEqual([group.values['groupKey'] for group in model._root_groups], sorted(keys))
        self.assertEqual([group.title for group in model._root_groups], ['Parent unavailable', 'No parent', 'A'])

    def test_same_parent_code_groups_by_identity_and_preserves_collapse(self):
        from tests.test_result_organization import _node
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        model = WorkspaceItemModel()
        nodes = [_node('1', 'First'), _node('2', 'Second'), _node('3', 'Third')]
        for index, node in enumerate(nodes):
            key = 'contract/' + ('asset' if index != 1 else 'scene') + '?project=demo&code=SAME'
            node.values.update(parent='SAME', __tableParentGroups={'parent': dict(groupKey=key, text='SAME')})
        model.set_organization(group_mode='column:parent')
        model.replace_nodes(nodes)
        groups = model._root_groups
        self.assertEqual(len(groups), 2)
        self.assertEqual([g.child_count for g in groups], [2, 1])
        self.assertEqual(groups[0].title, groups[1].title)
        model.toggle_node(groups[0].node_id)
        model._rebuild_organized_rows()
        self.assertFalse(model._root_groups[0].expanded)
        from thlib import tactic_table_widgets
        widget = tactic_table_widgets.create_widget(dict(resolvedClass='tactic.ui.table.expression_element_wdg.ExpressionElementWdg',
            actionClass='tactic.ui.table.ParentGroupAction'))
        self.assertEqual(widget.get_cell_kind(), 'commands')
        self.assertEqual(widget.map_cell(dict(text='Computed', parentGrouping=False))['text'], 'Computed')


class NativeParentOwnerTests(TableParentGroupTests):
    def test_real_worker_is_off_gui_and_close_project_and_tab_reject_late_results(self):
        import threading
        import time
        from types import SimpleNamespace
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        from thlib.pool import ThreadsPool
        from thlib.ui.table.services import TableServicesController
        from tests.test_table_service_workflows import Application
        application = Application()
        application.node.title = 'Source'
        application._sessions = {}
        application.debug_log = None
        owner = TableServicesController(application)
        pool = ThreadsPool()
        self.enterContext(patch.object(env_inst, 'server_pool', pool))
        self.addCleanup(pool.exit)
        self.addCleanup(owner.shutdown)
        parent = owner.parentGroups
        received = []
        parent.received.connect(lambda *args: received.append(args))
        gui = threading.get_ident()
        cell = dict(targetSearchKey=application.node.search_key, projectCode='source', parentEditable=True,
            sourceId='7', sourceRevision='revision', tableView='table', columnName='parent')
        request = dict(search_key=cell['targetSearchKey'], view='table', column='parent', action='prepare', source_id='7')
        def wait(condition):
            deadline = time.monotonic()+3
            while not condition() and time.monotonic()<deadline:
                self.app.processEvents()
                QTest.qWait(5)
            self.assertTrue(condition())
        def switch_tab():
            application.tab = SimpleNamespace(table_view='table')
            application.results_view_changed.emit()
        with patch.object(tc, 'server_start', return_value=object()) as start:
            for close in (parent.shutdown, application.project_changed.emit, switch_tab):
                began, release = threading.Event(), threading.Event()
                def execute(*args, **kwargs):
                    self.assertNotEqual(threading.get_ident(), gui)
                    self.assertEqual(kwargs['project'], 'source')
                    began.set()
                    if not release.wait(3):
                        raise TimeoutError('Test did not release worker')
                    return dict(sourceId='7', expectedRevision='revision')
                with patch.object(tc, 'execute_procedure_serverside', side_effect=execute):
                    parent.open(QObject(), 'A', cell)
                    self.assertEqual(parent.seed['projectCode'], 'source')
                    parent.request(request)
                    try:
                        wait(began.is_set)
                        close()
                    finally:
                        release.set()
                    wait(lambda: not parent._workers)
                self.assertFalse(parent.isOpen)
            self.assertEqual(start.call_args.kwargs['project'], 'source')
        self.assertEqual(received, [])

    def test_actual_popup_anchors_and_closes_with_its_context(self):
        from thlib.ui.table.services import TableServicesController
        from tests.test_table_service_workflows import Application
        application = Application()
        application.node.title = 'Source'
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        parent = owner.parentGroups
        cell = dict(targetSearchKey=application.node.search_key, parentEditable=True,
            sourceId='7', sourceRevision='revision', tableView='table', columnName='parent')
        window, view = self.create('features/table/ServiceDialogs.qml', dict(controller=owner), width=700, height=600)
        with patch.object(parent, 'request'):
            parent.open(view, 'A', cell)
            frames.frame(window)
            popup = view.findChild(QObject, 'tableParentGroupPopup')
            self.assertTrue(popup.property('visible'))
            self.assertFalse(popup.property('modal'))
            self.assertEqual(popup.property('surfaceWidth'), 380)
            application.project_changed.emit()
            self.assertFalse(parent.isOpen)
            from PySide6.QtCore import QDeadlineTimer
            deadline = QDeadlineTimer(2000)
            while popup.property('visible') and not deadline.hasExpired():
                QTest.qWait(5)
            self.assertFalse(popup.property('visible'))

    def test_create_child_uses_existing_insert_form_and_captured_parent_project(self):
        from thlib.ui.table.services import TableServicesController
        from thlib.environment import env_inst
        from tests.test_table_service_workflows import Application
        application = Application()
        owner = TableServicesController(application)
        self.addCleanup(owner.shutdown)
        parent = dict(searchKey='contract/entity?project=source&code=A', record=dict(code='A', __search_key__='contract/entity?project=source&code=A'))
        cell = dict(targetSearchKey='sthpw/note?code=N1', projectCode='source', parent=parent)
        with patch.object(env_inst, 'get_stype_by_code', return_value=object()) as lookup:
            owner.parentGroups.create_child(cell)
            self.assertEqual(lookup.call_args.kwargs['project_code'], 'source')
            request = application._sobject_editor_request
            self.assertEqual((request['mode'], request['view']), ('insert', 'insert'))
            self.assertEqual(request['parent_sobject'].get_info()['code'], 'A')
            application.open_window.assert_called_once_with('add_sobject')
            parent['retired'] = True
            owner.parentGroups.create_child(cell)
            self.assertEqual(application.open_window.call_count, 1)
