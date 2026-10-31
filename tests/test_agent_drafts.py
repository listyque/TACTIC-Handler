"""Real native review controls and guards; no candidate source executes."""
import unittest
from unittest.mock import Mock, patch

from PySide6.QtQuick import QQuickWindow

from tests import test_frame_script_tools as native_fixture
from thlib.ui.agent_drafts import AgentDraftsController
from thlib.ui.script_editor import ScriptEditorController


class AgentDraftTests(unittest.TestCase):
    def setUp(self):
        self.surface = native_fixture.ScriptToolsTests()
        self.surface.setUpClass()
        self.surface.setUp()
        self.addCleanup(self.surface.doCleanups)
        with patch('thlib.ui.script_editor.env_read_config', return_value={}), patch('thlib.ui.script_editor.env_write_config'):
            self.editor = ScriptEditorController(None, Mock())
        self.editor._write_settings = lambda: None
        self.editor._application = type('Application', (), {'is_stream_server': True})()
        self.review = self.editor.agentDrafts
        self.review._request = Mock()

    def test_real_review_checkbox_confirmation_stale_state_and_generation(self):
        self.review._model.update(selected='draft', drafts=[dict(draft_id='draft', title='Reviewed action')],
            draft=dict(draft_id='draft', ready=True, activated=False, revision='source', dependency_revision='deps',
                       document=dict(title='Reviewed action', kind='shelf', source='raise RuntimeError("Must not execute")'), trial_ids=['passed'], trials=[]))
        surface = self.surface
        view = surface.create(native_fixture.QML/'features/scripts/AgentDraftsView.qml',
            dict(theme=surface.theme, controller=self.review, width=1000, height=700))
        window = QQuickWindow()
        window.resize(1000, 700)
        surface.windows.append(window)
        view.setParentItem(window.contentItem())
        window.show()
        from tests.profile_ui_responsiveness import frame
        frame(window)
        activate = surface.item(view, 'agentDraftActivate')
        self.assertFalse(activate.isEnabled())
        surface.click(window, surface.item(view, 'agentDraftReviewed'))
        self.assertTrue(self.review.model['reviewed'])
        self.assertTrue(surface.item(view, 'agentDraftActivate').isEnabled())
        surface.click(window, surface.item(view, 'agentDraftActivate'))
        self.assertTrue(self.review.model['confirming'])
        self.review._request.reset_mock()
        surface.click(window, surface.item(view, 'agentDraftActivate'))
        self.review._request.assert_called_once_with('activate')
        operation = dict(self.review._pending)
        self.review.handle('activate', '')
        self.assertEqual(self.review._pending, operation)
        self.review._model['draft'].update(dependency_revision='new-deps', trial_ids=['new-proof'])
        self.review.handle('activate', '')
        self.assertNotEqual(self.review._pending['operation_id'], operation['operation_id'])
        self.assertEqual(self.review._pending['expected_revision'], 'new-deps')
        self.review._model['error'] = 'Read failed'
        self.review.changed.emit()
        frame(window)
        self.assertFalse(surface.item(view, 'agentDraftActivate').isEnabled())
        self.review._model['error'] = ''
        self.review._model['draft']['ready'] = False
        self.review.changed.emit()
        frame(window)
        self.assertFalse(surface.item(view, 'agentDraftActivate').isEnabled())
        self.review.handle('select', 'another-draft')
        self.assertEqual(self.review.model['draft'], {})
        self.review.reset()
        self.review._done(dict(generation=self.review._generation-1, drafts=[dict(title='wrong login')]))
        self.assertEqual(self.review.model['drafts'], [])
        self.assertEqual(surface.warnings, [])

    def test_reset_ignores_old_result_and_preserves_explicit_execution_owner(self):
        before = self.review._generation
        self.review.reset()
        self.review._done(dict(generation=before, error='old session'))
        self.assertEqual(self.review.model['error'], '')
        server = Mock()
        server.execute_cmd.return_value = dict(status='OK', info=dict(drafts=[]))
        response = AgentDraftsController._load(server, 'one', 'refresh', '', None, self.review._generation)
        self.assertEqual(response['drafts'], [])
        self.assertEqual(server.execute_cmd.call_args.args[1]['project_code'], 'one')


if __name__ == '__main__':
    unittest.main()
