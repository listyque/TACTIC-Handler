import unittest
from unittest.mock import patch

from thlib.ui.theme_catalog import read_project_theme


class PluginThemeTests(unittest.TestCase):
    def test_only_owned_active_valid_theme_overrides_personal_colors(self):
        class Server:
            selection='{"view":"studio.theme","plugin":"studio"}'
            active=True
            config='<config><studio.theme><theme style="fluent"><light base="#ffffff" accent="#123456"/><dark base="#202020" accent="#abcdef"/></theme></studio.theme></config>'
            def query(self,stype,filters=None):
                if stype=='config/prod_setting':return [dict(value=self.selection)]
                if stype=='config/widget_config':return [dict(code='THEME',config=self.config)]
                if stype=='config/plugin':return [dict(code='studio')] if self.active else []
        server=Server()
        with patch('thlib.tactic_classes.server_start',return_value=server):
            palette=read_project_theme('one')
            self.assertEqual('#abcdef',palette['dark']['accent'])
            self.assertEqual('fluent',palette['style'])
            server.active=False
            self.assertIsNone(read_project_theme('one'))
            server.active=True
            self.assertEqual('fluent',read_project_theme('one')['style'])
            server.config=server.config.replace('#abcdef','invalid')
            self.assertIsNone(read_project_theme('one'))
            server.config='<broken'
            self.assertIsNone(read_project_theme('one'))

    def test_system_project_never_fetches_theme(self):
        with patch('thlib.tactic_classes.server_start') as start:
            self.assertIsNone(read_project_theme('admin'))
            start.assert_not_called()
