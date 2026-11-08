"""Stream task reads use fixed commands; Legacy keeps its server procedure."""
from unittest import TestCase
from unittest.mock import Mock, patch

from thlib import tactic_classes as tc
from thlib.ui.task_workspace.field_catalog import load_task_field_catalog


class StaffTaskTransport(TestCase):
    def test_stream_page_does_not_execute_server_python(self):
        server = Mock()
        server.execute_cmd.return_value = dict(info=dict(tasks=[], parents=[], total=0))
        with patch('thlib.environment.get_server_api', return_value='stream'), \
                patch.object(tc, 'server_start', return_value=server), \
                patch.object(tc, 'execute_procedure_serverside') as python:
            result = tc.get_task_workspace_page([('assigned', 'artist')], ['timestamp desc'], 'demo')
        self.assertEqual(result['total'], 0)
        python.assert_not_called()
        self.assertEqual(server.execute_cmd.call_args.args, ('tactic.ui.table.task_workspace.TaskWorkspaceCmd',))
        self.assertEqual(server.execute_cmd.call_args.kwargs['args']['action'], 'page')

    def test_legacy_page_preserves_native_procedure(self):
        with patch('thlib.environment.get_server_api', return_value='legacy'), \
                patch.object(tc, 'execute_procedure_serverside', return_value={'total': 0}) as python:
            tc.get_task_workspace_page([], [], 'demo')
        self.assertIs(python.call_args.args[0], tc.tq.query_task_workspace_page)

    def test_stream_catalog_retains_permissions_and_choices(self):
        server = Mock()
        server.execute_cmd.return_value = dict(info=dict(priorityChoices=[{'value': 'high'}],
            milestoneChoices=[], permissions=dict(create=False, edit=False, delete=False)))
        with patch('thlib.environment.get_server_api', return_value='stream'), \
                patch.object(tc, 'server_start', return_value=server), \
                patch.object(tc, 'execute_procedure_serverside') as python:
            result = load_task_field_catalog('demo')
        python.assert_not_called()
        self.assertFalse(result['permissions']['edit'])
        self.assertEqual(result['priorityChoices'], [{'value': 'high'}])
