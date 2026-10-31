"""Worker controls belong to Configuration and retain async draft protection."""
from types import SimpleNamespace
import unittest

from PySide6.QtTest import QSignalSpy

from tests.frame_configuration_fixture import Surface
from thlib.ui.configuration_server import ServerControlEditor


class ConfigurationServerControlTests(unittest.TestCase):
    def surface(self):
        backend = ServerControlEditor(SimpleNamespace(
            can_manage_tools=True, debug_log=None, server_url='fixture', server_user='admin'))
        backend._project = 'admin'
        backend._loaded = True
        backend._identity = 'server'
        backend._can_write = True
        backend._document = {'workers': '2'}
        backend._original = {'workers': '2'}
        backend._metadata = {'runtime': {'available': True, 'state': 'running', 'web_workers': 2}}
        surface = Surface('configuration', width=1100, height=800, language='en', server_control=backend)
        self.addCleanup(surface.close)
        self.addCleanup(backend.shutdown)
        return surface, backend

    def test_server_page_contains_worker_card_and_connection_fields(self):
        surface, backend = self.surface()
        self.assertGreater(surface.item('serverWorkerCount').width(), 0)
        self.assertGreater(surface.item('setting_serverUrl').height(), 0)
        surface.case.config.select_page('appearance')
        surface.settle()
        with self.assertRaises(AssertionError):
            surface.item('serverWorkerCount')
        self.assertFalse(surface.warnings)

    def test_save_and_close_waits_for_remote_commit(self):
        surface, backend = self.surface()
        config = surface.case.config
        confirmations, closed = QSignalSpy(config.confirmationRequested), QSignalSpy(config.closeAllowed)
        backend.set_field('workers', '3')
        self.assertIn('server', config.dirty_pages)
        config.request_close()
        self.assertEqual(confirmations.count(), 1)
        # Hold the real async boundary open; no local setting or live server writes.
        requests = []
        backend.save = lambda: requests.append('save')
        config.save_and_close()
        self.assertEqual(requests, ['save'])
        self.assertEqual(closed.count(), 0)
        backend._original = dict(backend._document)
        backend.stateChanged.emit()
        backend.committed.emit()
        self.assertEqual(closed.count(), 1)
        self.assertFalse(config.dirty)

    def test_failed_write_stays_open_and_role_revocation_clears_remote_draft(self):
        surface, backend = self.surface()
        config = surface.case.config
        closed = QSignalSpy(config.closeAllowed)
        backend.set_field('workers', '3')
        backend.save = lambda: None
        config.save_and_close()
        backend._write_uncertain = True
        backend.fail('Connection lost')
        config.save_and_close()
        self.assertEqual(closed.count(), 0)
        self.assertTrue(config.dirty)
        backend._application.can_manage_tools = False
        backend._session_changed()
        self.assertFalse(config.dirty)
        self.assertFalse(backend.managementAvailable)
        backend.committed.emit()
        self.assertEqual(closed.count(), 0, 'Revoked session cannot resume an old close request')
