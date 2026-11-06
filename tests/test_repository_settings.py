"""Local repository setup must stay native, responsive and persistent."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QElapsedTimer, Qt, QUrl, QCoreApplication, QEvent
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtQml import QQmlEngine, QQmlComponent
from thlib.ui.icon_font import qml_icon_bindings
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from thlib.environment import (
    env_inst, env_mode, env_tactic, env_server, env_read_config, local_repository_path,
)
from thlib.pool import ThreadsPool
from thlib.tactic_classes import File as NativeFile
from thlib.ui.repository_editor import RepositoryEditorController, _empty_base_dirs
from thlib.ui.models import ProjectModel
from thlib.ui.controllers.connection import ConnectionMixin
from thlib.ui.repository_sync import RepositorySyncController
from tests.test_repository_waiting import File


class RepositorySettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.pool = ThreadsPool(1, parent=self.app)
        self.pool.start()
        self.addCleanup(self.pool.exit)
        self.native = 'windowsPath' if env_mode.get_platform() == 'Windows' else 'linuxPath'
        for mock in [
            patch.object(env_mode, 'current_path', str(self.root / 'profile')),
            patch.object(env_inst, 'local_pool', self.pool),
            patch.object(env_server, 'get_cur_srv_preset', return_value='fixture'),
            patch.object(env_tactic, 'base_dirs', _empty_base_dirs()),
            patch.object(env_tactic, 'default_base_dirs', {}),
            patch.object(env_tactic, 'custom_dirs', {}),
            patch.object(env_tactic, 'get_custom_dirs', return_value={}),
            patch('thlib.environment.cfg_controls.get_checkin', return_value={}),
            patch.object(RepositoryEditorController, '_set_checkin_default'),
        ]:
            mock.start()
            self.addCleanup(mock.stop)
        self.editor = RepositoryEditorController(parent=self.app)
        self.editor.model.setParent(self.editor)
        self.editor.begin_edit()
        self.saved = []
        self.editor.saved.connect(lambda: self.saved.append(True))

    def wait(self, condition):
        timer = QElapsedTimer(); timer.start()
        while not condition() and timer.elapsed() < 2000:
            QTest.qWait(5)
        self.assertTrue(condition())

    def test_server_linux_path_is_not_a_windows_repository(self):
        self.assertEqual(local_repository_path('/opt/tactic/assets', 'Windows'), '')
        self.assertEqual(local_repository_path('C:/work/repo', 'Windows'), 'C:/work/repo')
        self.assertEqual(local_repository_path('//nas/assets/repo', 'Windows'), '//nas/assets/repo')
        self.assertEqual(local_repository_path('/mnt/repo', 'Linux'), '/mnt/repo')
        self.assertEqual(local_repository_path('C:/work/repo', 'Linux'), '')

    def test_first_load_does_not_copy_posix_server_default_into_windows_mapping(self):
        defaults = {key: '' for key in _empty_base_dirs()}
        defaults['asset_base_dir'] = '/opt/tactic/assets'
        with patch.object(env_mode, 'platform', 'Windows'), patch.object(
            env_tactic, 'base_dirs', None
        ), patch.object(env_tactic, 'get_default_base_dirs', return_value=defaults), patch.object(
            env_tactic, 'save_base_dirs'
        ), patch('thlib.environment.env_read_config', return_value=None):
            actual = env_tactic.get_base_dirs()
        self.assertEqual(actual['asset_base_dir'][0], '')
        self.assertEqual(defaults['asset_base_dir'], '/opt/tactic/assets')

    def test_invalid_native_root_does_not_turn_into_a_network_file(self):
        snapshot = SimpleNamespace(get_snapshot=lambda: {'repo': 'base'})
        file = NativeFile({'file_name': 'preview.jpg', 'relative_dir': 'icons', 'metadata': ''}, snapshot)
        with patch.object(env_mode, 'platform', 'Windows'):
            env_tactic.base_dirs['asset_base_dir'][0] = '/opt/tactic/assets'
            self.assertEqual(file.get_repo_path(), '')
            self.assertEqual(file.get_abs_path(), '')
            self.assertEqual(file.get_full_abs_path(), '')

    def test_switching_default_back_to_first_row_keeps_the_clicked_row(self):
        self.editor.model.set_value(2, 'active', True)
        self.editor.model.set_value(2, 'isDefault', True)
        self.assertTrue(self.editor.model.get(2)['isDefault'])
        self.editor.model.set_value(0, 'isDefault', True)
        self.assertTrue(self.editor.model.get(0)['isDefault'])
        self.assertFalse(self.editor.model.get(2)['isDefault'])

    def test_save_creates_folder_in_worker_and_survives_forced_reload(self):
        target = self.root / 'new' / 'repository'
        self.editor.model.set_value(0, self.native, str(target))
        self.assertTrue(self.editor.save())
        self.assertTrue(self.editor.busy)
        self.wait(lambda: not self.editor.busy)
        self.assertEqual(self.saved, [True])
        self.assertTrue(target.is_dir())
        self.assertFalse(self.editor.dirty)
        stored = env_read_config(
            filename='tactic_dirs_fixture',
            unique_id=f'{env_mode.node}/environment_config/server_presets',
            sub_id='TACTIC_BASE_DIRS',
        )
        self.assertEqual(stored['asset_base_dir'][0], str(target))
        self.assertEqual(env_tactic.get_base_dirs(force=True)['asset_base_dir'][0], str(target))

    def test_blank_or_relative_paths_are_rejected_before_filesystem_work(self):
        for path in ['', '.', 'relative/repo']:
            self.editor.model.set_value(0, self.native, path)
            with patch.object(self.pool, 'add_task') as start:
                self.assertFalse(self.editor.save())
                start.assert_not_called()
        self.assertEqual(self.saved, [])
        self.assertIn('absolute', self.editor.message)

    def test_failed_creation_preserves_the_previous_mapping(self):
        blocker = self.root / 'file'
        blocker.write_text('keep', encoding='utf-8')
        self.editor.model.set_value(0, self.native, str(blocker / 'repo'))
        self.assertTrue(self.editor.save())
        self.wait(lambda: not self.editor.busy)
        self.assertEqual(self.saved, [])
        self.assertEqual(env_tactic.base_dirs['asset_base_dir'][0], '')
        self.assertTrue(self.editor.dirty)
        self.assertIn('Could not create', self.editor.message)
        self.assertEqual(blocker.read_text(), 'keep')

    def test_real_editor_commits_a_typed_path_without_manual_check(self):
        from tests.test_frame_help import Windows
        from tests.test_sidebar_editor_qml import SidebarEditorQmlTests
        from tests.profile_ui_responsiveness import frame
        root = Path(__file__).resolve().parents[1]
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        windows = Windows()
        context = engine.rootContext()
        for name, value in dict(qml_icon_bindings(root, self.app),
                                repositoryEditorController=self.editor,
                                repositoryEditorModel=self.editor.model,
                                windowModel=windows).items():
            context.setContextProperty(name, value)
        component = QQmlComponent(engine)
        qml = ('import QtQuick\nimport QtQuick.Controls\nimport "' +
               (root / 'thlib/ui/qml').as_uri() + '" as TH\n'
               'ApplicationWindow { visible:true; width:1000; height:740; '
               'TH.Theme {id:theme; dark:true} '
               'TH.RepositoryEditorView {theme:theme; anchors.fill:parent} }')
        component.setData(qml.encode(), QUrl())
        self.assertTrue(component.isReady(), [error.toString() for error in component.errors()])
        window = component.create()
        self.assertIsNotNone(window)
        try:
            frame(window)
            def item(name):
                return next(value for value in SidebarEditorQmlTests.descendants(window.contentItem())
                            if value.objectName() == name)
            field = item('setting_' + self.native)
            field.forceActiveFocus()
            target = self.root / 'typed' / 'repository'
            event = QInputMethodEvent()
            event.setCommitString(str(target))
            QCoreApplication.sendEvent(field, event)
            frame(window)
            self.assertEqual(self.editor.model.get(0)[self.native], str(target))
            save = item('repositorySave')
            self.assertTrue(save.isEnabled())
            save.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Space)
            self.wait(lambda: bool(self.saved))
            self.assertEqual(env_tactic.base_dirs['asset_base_dir'][0], str(target))
            self.assertTrue(target.is_dir())
            self.assertEqual(warnings, [])
        finally:
            window.close(); window.deleteLater(); engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_project_fallback_notifies_header_to_stop_loading(self):
        model = ProjectModel()
        model.setParent(self.app)
        owner = SimpleNamespace(_current_project_code='PROJECT',
                                _current_project_preview='pending-preview:test',
                                project_state_changed=SimpleNamespace(emit=lambda: None))
        model.preview_ready.connect(lambda code, url: ConnectionMixin._project_preview_ready(owner, code, url))
        model._preview_cache['PROJECT'] = owner._current_project_preview
        model.fail_preview('test')
        self.assertEqual(owner._current_project_preview, '')
        self.assertEqual(model._preview_cache['PROJECT'], '')

    def test_empty_native_destination_keeps_explicit_transfer_waiting(self):
        queue = RepositorySyncController(parent=self.app)
        self.addCleanup(queue.shutdown)
        file = File(self.root / 'missing')
        file.get_repo_path = lambda: ''
        file.get_full_abs_path = lambda: ''
        handle = queue.schedule_file_object(file, auto_start=True)
        self.wait(lambda: queue._active == 0)
        self.assertEqual(queue.status(handle.task_id), 'waiting_repository')
        self.assertEqual(queue.model.record(handle.task_id)['error'], '')

    def test_deferred_previews_finish_loading_even_when_root_is_already_blocked(self):
        queue = RepositorySyncController(parent=self.app)
        self.addCleanup(queue.shutdown)
        model = ProjectModel()
        model.setParent(self.app)
        queue.preview_deferred.connect(model.fail_preview, Qt.ConnectionType.QueuedConnection)
        failures = []
        queue.task_failed.connect(failures.append)
        for filename in ['first.jpg', 'second.jpg']:
            handle = queue.schedule_file_object(File(self.root / 'missing', filename),
                                                auto_start=True, is_ui_preview=True)
            model._preview_cache['PROJECT'] = 'pending-preview:' + handle.task_id
            self.wait(lambda: model._preview_cache['PROJECT'] == '')
        self.assertEqual(failures, [])
        self.assertFalse((self.root / 'missing').exists())


if __name__ == '__main__':
    unittest.main()
