"""Runner denials, inherited groups and the cached Maya entry point."""
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from thlib.script_access import query_runner_access
from tests import test_admin_security_matrix as matrix_fixture
from tests import test_script_editor as editor_fixture
from tactic_handler_api.objects import Project
from tactic_handler_dcc.runtime import DccRuntime, ScriptJob

PATH = 'stream/tools/runners/cache_checkin_runner'


class RunnerPolicyTests(unittest.TestCase):
    def policy(self, groups, admin=False, project='demo'):
        security = SimpleNamespace(is_admin=lambda: admin, get_groups=lambda: [
            SimpleNamespace(get_value=lambda name, no_exception=True, row=row: row.get(name))
            for row in groups
        ])
        with patch.dict(sys.modules, {
            'pyasm.common': SimpleNamespace(Environment=SimpleNamespace(get_security=lambda: security)),
            'pyasm.biz': SimpleNamespace(Project=SimpleNamespace(get_project_code=lambda: project)),
        }):
            return json.loads(query_runner_access('demo'))

    def test_denial_wins_and_other_projects_are_ignored(self):
        rule = '<rules><rule group="script_runner" key="%s" project="demo" access="deny"/></rules>' % PATH
        allowed = '<rules><rule group="script_runner" key="%s" project="demo" access="allow"/></rules>' % PATH
        self.assertEqual(self.policy([{'access_rules': allowed}, {'access_rules': rule}])['denied'], [PATH])
        self.assertEqual(self.policy([{'access_rules': rule, 'project_code': 'other'}])['denied'], [])
        self.assertEqual(self.policy([{'access_rules': rule}], admin=True)['denied'], [])
        self.assertEqual(self.policy([])['denied'], [])
        with self.assertRaises(ValueError):
            self.policy([], project='other')

    def test_maya_cached_runner_checks_before_touching_the_file(self):
        runtime = object.__new__(DccRuntime)
        runtime.wait_until_connected = lambda timeout: True
        runtime.startup_timeout = 1
        runtime.application_title = 'Maya'
        runtime._notify = Mock()
        check = Mock(side_effect=PermissionError('denied'))
        runtime._api = SimpleNamespace(project=lambda project: SimpleNamespace(require_script_access=check))
        job = ScriptJob('Maya')
        runtime._run_custom_script(job, PATH, 'demo', {}, False)
        check.assert_called_once_with(PATH)
        self.assertIsInstance(job.error, PermissionError)
        self.assertTrue(job._done.is_set())

    def test_project_api_uses_authenticated_server_policy(self):
        core = Mock()
        core.execute_procedure_serverside.return_value = {'project': 'demo', 'denied': [PATH]}
        api = SimpleNamespace(_check=Mock(), _core=core)
        project = Project(api, SimpleNamespace(get_info=lambda: {'code': 'demo'}))
        with self.assertRaises(PermissionError):
            project.require_script_access(PATH)
        self.assertTrue(project.require_script_access('stream/tools/runners/save_similar_runner'))


class RunnerMatrixTests(unittest.TestCase):
    def setUp(self):
        fixture = matrix_fixture.SecurityMatrixTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.editor = fixture.editor
        self.editor._metadata['targets']['script_runner'] = [
            {'label': path, 'attributes': {'key': path, 'project': 'demo'}} for path in ('*', PATH)
        ]
        self.editor.matrix.filter('script_runner', '', '')

    def test_default_deny_and_restore_preserve_other_rules(self):
        editor = self.editor
        original = editor.document['groups']['G0']['xml']
        self.assertTrue(editor.matrix.cell_at(1, 0)['checked'])
        editor.matrix.set_allowed(1, 0, False)
        self.assertFalse(editor.matrix.cell_at(1, 0)['checked'])
        self.assertTrue(editor.dirty)
        self.assertIn('studio_custom', editor.document['groups']['G0']['xml'])
        editor.matrix.set_allowed(1, 0, True)
        self.assertEqual(editor.document['groups']['G0']['xml'], original)

    def test_inherited_and_all_runner_denials_cannot_be_overridden(self):
        editor = self.editor
        editor.matrix.set_allowed(0, 0, False)
        self.assertTrue(editor.matrix.cell_at(1, 0)['locked'])
        editor.select_group('G1')
        editor.set_group_field('subGroups', 'Artists 0')
        self.assertFalse(editor.matrix.cell_at(1, 1)['checked'])
        self.assertTrue(editor.matrix.cell_at(1, 1)['locked'])
        editor.matrix.set_allowed(1, 1, True)
        self.assertFalse(editor.matrix.cell_at(1, 1)['checked'])


class RunnerExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        editor_fixture.ScriptEditorTests.setUpClass()

    def test_saved_invocations_and_hook_definitions_are_denied(self):
        fixture = editor_fixture.ScriptEditorTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        editor = fixture.controller
        path = 'pipeline/tools/First'
        editor._denied_runners = {path}
        self.assertFalse(editor.run_saved_script(path))
        self.assertEqual(editor.saved_script_definition(path), {})
        self.assertNotIn(path, [row['value'] for row in editor.shelfScriptOptions])
        with self.assertRaises(PermissionError):
            editor.require_saved_script_access(path)
        with self.assertRaises(PermissionError):
            editor.require_saved_script_access(path.replace('/', '\\'))
        editor._access_ready = False
        self.assertFalse(editor.script_allowed('unconfigured/runner'))

    def test_old_session_worker_cannot_restore_old_permissions(self):
        fixture = editor_fixture.ScriptEditorTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        editor = fixture.controller
        worker = Mock()
        pool = SimpleNamespace(is_stopped=False, add_task=lambda *args: worker)
        with patch.object(editor, '_request_context', side_effect=['old-session', 'new-session']), \
                patch.object(editor, '_access_context_changed') as invalidate, \
                patch.object(editor, '_done') as apply:
            editor._start(pool, lambda: None)
            callback = worker.result.connect.call_args.args[0]
            callback({'kind': 'load', 'runnerAccess': {'denied': []}})
            apply.assert_not_called()
            invalidate.assert_called_once()
            self.assertFalse(editor.busy)
