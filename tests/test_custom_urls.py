"""Native URL capture never forwards a session to another origin."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from thlib.ui.search_links import parse_custom_page_link


class CustomUrls(unittest.TestCase):
    def test_dashboard_button_routes_to_native_page_without_opening_browser(self):
        from thlib.ui.controllers.rich_text_links import RichTextLinksMixin
        from thlib.ui.table.custom_layout import CustomLayoutController
        app=Mock(); app._current_project_code='demo'; app._custom_url_generation=0
        app._bootstrap_cache_identity.return_value='captured-server'
        app.open_rich_link=lambda value: RichTextLinksMixin.open_rich_link(app,value)
        owner=SimpleNamespace(services=SimpleNamespace(_application=app))
        server=Mock()
        with (patch('thlib.ui.custom_urls.env_server') as settings,
              patch('thlib.ui.custom_urls.env_inst',projects={'demo':Mock()}),
              patch('thlib.tactic_classes.server_start',return_value=server),
              patch('thlib.ui.controllers.rich_text_links.QDesktopServices.openUrl') as external):
            settings.get_server.return_value='local:8081'
            for name in ('work','tasks','analytics'):
                href='http://local:8081/projects/demo/dashboard/'+name
                server.execute_cmd.return_value=dict(info=dict(layoutView='dashboard.'+name,
                    title=name,options={},search_type='demo/project',view='table'))
                CustomLayoutController.activate(owner,dict(name='layout-link',href=href))
                operation,accept=app._table_services._run.call_args.args
                accept(operation())
                self.assertEqual(server.execute_cmd.call_args.args[1]['path'],'/dashboard/'+name)
                self.assertEqual(app._activate_saved_search_preset.call_args.args[0]['layout_view'],'dashboard.'+name)
            self.assertEqual(app._activate_saved_search_preset.call_count,3)
            external.assert_not_called()

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
                    project='demo',search_type='sthpw/project',view='table',filterField='',filterValue='')
        server=Mock();server.execute_cmd.return_value=dict(info=target)
        with (patch('thlib.ui.custom_urls.env_server') as settings,
              patch('thlib.ui.custom_urls.env_inst',projects={'demo':Mock()}),
              patch('thlib.tactic_classes.server_start',return_value=server)):
            settings.get_server.return_value='local:8081'
            self.assertTrue(open_custom_url(app,'http://local:8081/projects/demo/dashboard/review'))
            operation,accept=app._table_services._run.call_args.args
            result=operation()
            accept(result)
            app._activate_saved_search_preset.assert_called_once_with(dict(search_type='sthpw/project',
                view='custom-url:http://local:8081/projects/demo/dashboard/review',table_view='table',view_mode='table',
                layout_view='dashboard.review',layout_target=''),dict(title='Review',records=[]))
            app._table_services.customLayout.open_result.assert_not_called()
            app._current_project_code='other'
            accept(result)
            self.assertEqual(app._activate_saved_search_preset.call_count,1)
