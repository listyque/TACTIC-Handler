"""Actual QML input and captured native connection commands."""
from types import SimpleNamespace
import threading
import time
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
import tests.test_table_service_workflows as fixtures
from thlib.pool import ThreadsPool
from thlib.ui.table.services import TableServicesController


class Ports(fixtures.Ports):
    @Slot(str, 'QVariantMap')
    def request_connection_removal(self, node_id, cell):
        self.calls.append(('remove', node_id, dict(cell)))


class TableConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def cell(self, count=1):
        return dict(targetSearchKey='demo/asset?project=demo&code=P', direction='dst', iconSize=60,
            connectionRows=[dict(connectionKey='sthpw/connection?code=C%s' % index,
                expectedRevision='revision-%s' % index, available=True,
                searchKey='demo/asset?project=demo&code=A%s' % index, code='A%s' % index,
                name='Connected object %s' % index, description='Description', keywords='tag',
                retired=False, preview={}) for index in range(count)])

    def wait(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertTrue(condition())

    def test_first_click_captures_the_connection_and_both_endpoints(self):
        ports, controller = Ports(), frames._TableController()
        cell = self.cell()
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=controller,
            nodeId='P', services=ports, administration=None, cell=cell), width=360, height=100)
        self.click(window, self.item(view, 'tableConnectionRemove'))
        self.assertEqual(len(ports.calls), 1)
        operation, node, payload = ports.calls[0]
        self.assertEqual((operation, node), ('remove', 'P'))
        self.assertEqual(payload['targetSearchKey'], cell['targetSearchKey'])
        self.assertEqual(payload['connectionKey'], 'sthpw/connection?code=C0')
        self.assertEqual(payload['expectedRevision'], 'revision-0')
        self.click(window, self.item(view, 'tableConnectionPreviewAction'))
        self.assertEqual(controller.table_widget_actions[0][0:2], ('sobject_detail', 'P'))
        self.assertEqual(controller.table_widget_actions[0][2]['targetSearchKey'], cell['connectionRows'][0]['searchKey'])

    def test_filename_link_keeps_its_full_label_and_uses_existing_url_port(self):
        ports = Ports()
        cell = self.cell()
        name = 'Reference image with a long name.png'
        href = 'https://example.invalid/reference.png'
        cell['connectionRows'][0]['preview'] = dict(filename=name, text=href)
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=frames._TableController(),
            nodeId='P', services=ports, administration=None, cell=cell), width=420, height=110)
        action = self.item(view, 'tableConnectionFile')
        caption = self.item(view, 'tableConnectionFilename')
        self.assertGreater(action.width(), 360)
        labels = [item for item in frames._visual_items(caption) if item.property('text') == name
            and item.metaObject().indexOfProperty('truncated') >= 0]
        self.assertTrue(labels)
        self.assertTrue(all(not item.property('truncated') for item in labels))
        self.click(window, action)
        self.assertEqual(ports.calls, [('url', href)])

    def test_readonly_keeps_details_available_and_virtualizes_a_long_connection_list(self):
        ports, controller = Ports(), frames._TableController()
        window, view = self.create('features/table/ServiceCell.qml', dict(controller=controller,
            nodeId='P', services=ports, administration=None, cell=self.cell(100), editable=False), width=360, height=120)
        controls = [item for item in frames._visual_items(view) if item.objectName() == 'tableConnectionRemove']
        self.assertLess(len(controls), 10)
        self.assertTrue(controls)
        self.assertTrue(all(not control.property('enabled') for control in controls))
        scrollbar = self.item(view, 'tableConnectionsScrollBar')
        self.assertIsNotNone(scrollbar)
        self.assertTrue(scrollbar.property('visible'))
        self.assertGreater(scrollbar.property('width'), 0)
        preview = self.item(view, 'tableConnectionPreviewAction')
        preview.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return)
        frames.frame(window)
        self.assertEqual(len(controller.table_widget_actions), 1)
        self.assertEqual(ports.calls, [])

    def prepare_owner(self):
        from thlib import tactic_classes as tc
        application = fixtures.Application()
        application.debug_log = None
        owner = TableServicesController(application)
        server = SimpleNamespace(get_project=lambda: 'demo')
        self.enterContext(patch.object(tc, 'server_start', return_value=server))
        self.addCleanup(owner.shutdown)
        return application, owner, server

    def test_confirmation_cancel_and_changed_tab_never_write(self):
        application, owner, _server = self.prepare_owner()
        cell = dict(self.cell(), connectionKey='sthpw/connection?code=C0', expectedRevision='old')
        opened = []
        owner.connectionRemovalOpened.connect(lambda: opened.append(True))
        with patch.object(owner, '_run') as run:
            owner.request_connection_removal('P', cell)
            owner.confirm_connection_removal(False)
            run.assert_not_called()
            owner.request_connection_removal('P', cell)
            application.tab = object()
            owner.confirm_connection_removal(True)
            run.assert_not_called()
        self.assertEqual(len(opened), 2)
        application._notify.assert_called_once()

    def test_actual_worker_captures_context_and_refreshes_after_success_or_unknown_result(self):
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        application, owner, server = self.prepare_owner()
        pool = ThreadsPool()
        self.enterContext(patch.object(env_inst, 'server_pool', pool))
        self.addCleanup(pool.exit)
        self.addCleanup(owner.shutdown)
        completed = []
        owner.completed.connect(completed.append)
        cell = dict(self.cell(), connectionKey='sthpw/connection?code=C0', expectedRevision='old')
        gui_thread = threading.get_ident()
        calls = []
        def execute(function, values, project, server):
            self.assertNotEqual(threading.get_ident(), gui_thread)
            calls.append((function.__name__, dict(values), project, server))
            if len(calls) == 2:
                raise ConnectionError('Response lost')
            return dict(state='removed')
        with patch.object(tc, 'execute_procedure_serverside', side_effect=execute):
            for _ in range(2):
                owner.request_connection_removal('P', cell)
                owner.confirm_connection_removal(True)
                self.wait(lambda: not owner.busy)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], ('remove_connection', dict(parent_key=cell['targetSearchKey'],
            connection_key=cell['connectionKey'], expected_revision='old', direction='dst'), 'demo', server))
        self.assertEqual(completed, [cell['targetSearchKey']] * 2)
        self.assertIn('Response lost', owner.error)

    def test_context_teardown_closes_the_actual_confirmation(self):
        _application, owner, _server = self.prepare_owner()
        window, view = self.create('features/table/ServiceDialogs.qml', dict(controller=owner), width=700, height=500)
        cell = dict(self.cell(), connectionKey='sthpw/connection?code=C0', expectedRevision='old')
        owner.request_connection_removal('P', cell)
        frames.frame(window)
        confirmation = view.findChild(QObject, 'tableConfirmation_connectionConfirm')
        self.assertTrue(confirmation.property('opened'))
        QTest.keyClick(window, Qt.Key_Escape)
        frames.frame(window)
        self.assertIsNone(owner._connection_removal)
        owner.request_connection_removal('P', cell)
        frames.frame(window)
        owner.shutdown()
        frames.frame(window)
        self.assertFalse(confirmation.property('visible'))
