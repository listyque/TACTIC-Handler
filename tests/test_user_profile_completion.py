import inspect
import json
import sys
import unittest
from datetime import datetime, timezone
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from thlib import tactic_query


class UserProfileCompletionTests(unittest.TestCase):
    def test_profile_counts_native_status_behavior_not_percentage(self):
        tasks = []
        processes = []
        today = datetime.now(timezone.utc).date().isoformat()
        for status, mapping, xml_mapping, completion, deadline in (
            ('Оплачен', 'Complete', '', 0, '2000-01-01'),
            ('Оплачен', 'Approved', '', 0, today),
            ('Принят', '', 'complete', 0, '2000-01-01'),
            ('Complete', '', '', 0, '2000-01-01'),
            ('Approved', '', '', 0, today),
            ('Назначен', 'Pending', '', 100, '2000-01-01'),
            ('Complete', 'In Progress', '', 100, today),
            ('Оплачен', '', '', 100, today),
        ):
            node = SimpleNamespace(get_attribute=lambda key, value=xml_mapping: value)
            pipeline = SimpleNamespace(
                get_process=lambda name, value=node: value,
                get_process_sobject=lambda name: None,
            )
            pipeline_code = str(len(tasks))
            if mapping:
                workflow = {'default': {'mapping': mapping}} if mapping == 'Approved' else {'mapping': mapping}
                processes.append(SimpleNamespace(
                    get_value=lambda key, code=pipeline_code, name=status: {
                        'pipeline_code': code, 'process': name,
                    }[key],
                    get_json_value=lambda *args, value=workflow: value,
                ))
            data = dict(status=status, completion=completion, bid_end_date=deadline,
                        pipeline_code=pipeline_code, project_code='demo')
            tasks.append(SimpleNamespace(
                get_data=lambda value=data: value,
                get_pipeline=lambda value=pipeline: value,
            ))
        tasks.append(SimpleNamespace(
            get_data=lambda: {
                'status': 'Foreign', 'process': 'foreign',
                'project_code': 'other',
            },
            get_pipeline=lambda: None,
        ))
        searches = []

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []
                searches.append(self)

            def add_filter(self, *args, **kwargs):
                self.filters.append(args)

            def add_filters(self, *args, **kwargs):
                self.filters.append(args)

            def add_order_by(self, *args, **kwargs):
                pass

            def get_sobjects(self):
                if self.search_type == 'config/process?project=demo':
                    return processes
                if self.search_type != 'sthpw/task':
                    return []
                project = next((
                    value for field, value in self.filters
                    if field == 'project_code'
                ), None)
                return [
                    task for task in tasks
                    if task.get_data().get('project_code') == project
                ]

        search_module = ModuleType('pyasm.search')
        search_module.Search = Search
        search_module.SearchType = SimpleNamespace(
            build_search_type=lambda name, project: name + '?project=' + project)
        namespace = {'server': SimpleNamespace(get_login=lambda: 'admin')}
        exec(inspect.getsource(tactic_query.query_user_profile_data), namespace)
        with patch.dict(sys.modules, {'pyasm': ModuleType('pyasm'), 'pyasm.search': search_module}):
            result = json.loads(namespace['query_user_profile_data']('artist', 'demo'))
        self.assertEqual(result['taskSummary'], {
            'total': 8, 'incomplete': 3, 'overdue': 1, 'dueThisWeek': 2,
        })
        self.assertEqual(sum(item['count'] for item in result['statusSummary']), 8)
        self.assertEqual(sum(item['count'] for item in result['processSummary']), 8)
        self.assertEqual(result['processSummary'][0]['process'], '')
        self.assertIn(('project_code', 'demo'), searches[0].filters)
        self.assertEqual(searches[1].search_type, 'config/process?project=demo')
        with patch.dict(sys.modules, {'pyasm': ModuleType('pyasm'), 'pyasm.search': search_module}):
            self.assertEqual(json.loads(namespace['query_user_profile_data']('artist')), {})


if __name__ == '__main__':
    unittest.main()
