"""Configured navigation projects the existing tree; ordinary views stay complete."""
from types import SimpleNamespace, ModuleType
import sys
import unittest
from unittest.mock import patch
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class NavigationTests(unittest.TestCase):
    def test_metadata_resolves_explicit_shared_types_on_their_own_database(self):
        from thlib import tactic_query
        from unittest.mock import Mock
        class ReachedColumns(Exception): pass
        project = Mock()
        project.get_search_types.return_value = []
        project.has_table.side_effect = AssertionError('Shared types do not live in the business database')
        task = Mock()
        task.get_data.return_value = {'code':'sthpw/task'}
        task.get_column_info.side_effect = ReachedColumns
        types = Mock()
        types.get.return_value = task
        types.get_sql_by_search_type.return_value.table_exists.return_value = True
        biz = ModuleType('pyasm.biz');biz.Project=SimpleNamespace(get_by_code=lambda _:project);biz.Pipeline=Mock()
        search = ModuleType('pyasm.search');search.Search=Mock();search.SearchKey=Mock();search.WidgetDbConfig=Mock();search.SearchType=types
        widget = ModuleType('pyasm.widget');widget.WidgetConfigView=Mock()
        server = Mock();server.query.return_value=[{'schema':'<schema><search_type name="demo/chat"/><search_type name="sthpw/task"/></schema>'}]
        with patch.dict(sys.modules,{'pyasm':ModuleType('pyasm'),'pyasm.biz':biz,'pyasm.search':search,'pyasm.widget':widget}), patch.object(tactic_query,'server',server,create=True):
            with self.assertRaises(ReachedColumns): tactic_query.query_search_types_extended('demo')
        types.get.assert_called_once_with('sthpw/task')
        types.get_sql_by_search_type.assert_called_once_with('sthpw/task')

    def test_allowed_children_empty_leaf_and_unconfigured_view(self):
        from tests.test_workspace_process_count_menu import _Source, _SearchType

        class Child:
            info = {}
            def get_pretty_name(self): return 'Fallback'
            def get_stype_color(self, fmt='hex'): return '#607d8b'

        class Type(_SearchType):
            def get_schema(self):
                return SimpleNamespace(children=[{'from':name, 'title':title} for name,title in [('demo/chat','Chats'),('demo/run','Runs')]])
            def get_project(self):
                return SimpleNamespace(stypes={'demo/chat':Child(), 'demo/run':Child()})

        source = _Source()
        source.get_stype = lambda: Type(source.pipeline)
        source.get_process = lambda _name: None
        node = WorkspaceNode(node_id='project', node_type='sobject', code='P', title='Project', search_key='skey://demo/project?code=P', source=source)
        model = WorkspaceItemModel()
        model.replace_nodes([node])
        with patch.object(model, '_snapshot_nodes', return_value=[]), patch('thlib.tactic_classes.get_notes_count', return_value={}):
            model.set_item_layout({'navigation':{'demo/project':['demo/chat']}})
            model._load_root(node)
            self.assertEqual([(n.code,n.title) for n in node.children], [('demo/chat','Chats')])
            model.set_item_layout({'navigation':{'demo/project':[]}})
            model._load_root(node)
            self.assertEqual(node.children, [])
            model.set_item_layout({})
            model._load_root(node)
            self.assertEqual([n.code for n in node.children if n.node_type=='relation'], ['demo/chat','demo/run'])
            self.assertTrue(any(n.node_type=='process' for n in node.children))


if __name__ == '__main__': unittest.main()
