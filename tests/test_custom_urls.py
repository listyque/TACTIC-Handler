"""Native URL capture never forwards a session to another origin."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from thlib.ui.search_links import parse_custom_page_link


class CustomUrls(unittest.TestCase):
    def test_same_origin_project_pattern_and_legacy_hash(self):
        self.assertEqual(parse_custom_page_link('http://local:8081/projects/demo/review/CAR?q=1','local:8081'),
            dict(project='demo',path='/review/CAR',parameters={'q':'1'}))
        self.assertEqual(parse_custom_page_link('http://local:8081/tactic/demo/#/review/CAR?q=2','local:8081')['parameters'],{'q':'2'})
        for value in ('http://foreign:8081/projects/demo/review/CAR','https://local:8081/projects/demo/review/CAR',
                      'http://user:password@local:8081/projects/demo/review/CAR','http://local:8081/admin/',
                      'http://local:8081/projects/demo/'):
            self.assertIsNone(parse_custom_page_link(value,'local:8081'))

    def test_native_layout_entry_and_stale_project_result(self):
        from thlib.ui.custom_urls import open_custom_url
        app=Mock();app._current_project_code='demo';app._custom_url_generation=0
        app._bootstrap_cache_identity.return_value='captured-server'
        app._table_services=Mock()
        target=dict(layoutView='dashboard.review',title='Review',options={},
                    project='demo',search_type='sthpw/project')
        layout=dict(targetSearchKey='sthpw/project?code=demo',layoutRecord={},layoutNodes=[])
        server=Mock();server.execute_cmd.side_effect=[dict(info=target),dict(info=layout)]
        with (patch('thlib.ui.custom_urls.env_server') as settings,
              patch('thlib.ui.custom_urls.env_inst',projects={'demo':Mock()}),
              patch('thlib.tactic_classes.server_start',return_value=server)):
            settings.get_server.return_value='local:8081'
            self.assertTrue(open_custom_url(app,'http://local:8081/projects/demo/dashboard/review'))
            operation,accept=app._table_services._run.call_args.args
            result=operation()
            accept(result)
            app._table_services.customLayout.open_result.assert_called_once_with(layout,'Review','custom-url:http://local:8081/projects/demo/dashboard/review')
            app._current_project_code='other'
            accept(result)
            self.assertEqual(app._table_services.customLayout.open_result.call_count,1)
