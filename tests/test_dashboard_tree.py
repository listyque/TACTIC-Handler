"""Real native input for the portable lazy hierarchy; no production connection."""
from unittest.mock import Mock, patch
import unittest
from types import SimpleNamespace
from tests import test_workspace_page as pages
from tests.test_columns_table_view import _TableController, _TableColumns, _visual_items
from tests import test_frame_table as frames


class DashboardTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=frames.gui_test_application()
    owner = pages.WorkspacePageTests.owner
    create = pages.WorkspacePageTests.create
    close = pages.WorkspacePageTests.close
    click = pages.WorkspacePageTests.click

    def test_house_controls_remain_readable_without_pill_geometry(self):
        for name in ('Button','TextField'):
            window,control=self.create('controls/'+name+'.qml',{},width=240,height=32)
            self.assertLessEqual(control.property('implicitHeight'),34)
            self.assertLessEqual(control.property('background').property('radius'),6)
            self.assertGreaterEqual(control.property('font').pixelSize(),12)

    def tree_owner(self):
        app,services=self.owner()
        app.open_rich_link=Mock()
        tree=dict(search_type='demo/project',branches=[dict(search_type='demo/todo',title='Assignments',branches=[dict(search_type='sthpw/task',title='Tasks',branches=[])])])
        requests=[]
        with patch('thlib.ui.table.dashboard_tree.DashboardTreeController.read',lambda owner,request:requests.append((owner,request))):
            services.workspaceLayout.open_result(dict(title='Review',targetSearchKey='sthpw/project?code=demo',layoutRecord={},layoutView='dashboard.review',layoutNodes=[dict(kind='tree',text='Projects',tree=tree,height=560)]),'Review',app.tab.tab_id)
        reader,request=requests[0]
        self.complete(reader,request,[dict(key='demo/project?project=demo&code=P',title='StudyDesk',detail='Active',icon='folder')])
        return app,services,reader,requests

    def complete(self,reader,request,items,has_next=False,error=''):
        reader._model=reader.call('accept',reader.model,request,dict(items=items,offset=request['offset'],has_next=has_next),error)
        reader.changed.emit()

    def text_item(self,view,text):
        return next(item for item in _visual_items(view) if item.objectName()=='dashboardTreeTitleLabel' and item.property('text')==text)

    def test_tree_lazy_expansion_pagination_and_native_object_open(self):
        app,services,reader,requests=self.tree_owner()
        window,view=self.create('features/table/WorkspacePage.qml',dict(services=services,controller=_TableController(),columnsController=_TableColumns(),users=None,administration=None),width=1000,height=700)
        self.assertEqual(len(requests),1)
        with patch.object(reader,'read',side_effect=lambda request:requests.append((reader,request))):
            self.click(window,self.text_item(view,'Assignments'))
            self.assertEqual(requests[-1][1]['branch_path'],[0])
            self.complete(reader,requests[-1][1],[dict(key='demo/todo?project=demo&code=T',title='Build application',detail='In Progress',icon='task')],has_next=True)
            frames.frame(window)
            self.click(window,self.text_item(view,'Load more'))
            self.assertEqual(requests[-1][1]['offset'],1)
            self.complete(reader,requests[-1][1],[dict(key='demo/todo?project=demo&code=T2',title='Test application',detail='Ready',icon='task')])
            frames.frame(window)
            self.click(window,self.text_item(view,'Build application'))
        app.open_rich_link.assert_called_once_with('skey://demo/todo?project=demo&code=T')
        self.assertEqual(len(requests),3)
        app.open_window.assert_not_called()
        view.setWidth(400);window.resize(400,700);frames.frame(window)
        self.assertLessEqual(self.text_item(view,'Build application').width(),400)

    def test_refresh_ignores_old_reply_and_error_can_be_retried(self):
        _,_,reader,requests=self.tree_owner()
        with patch.object(reader,'read',side_effect=lambda request:requests.append((reader,request))):
            reader.activate(dict(type='refresh'));old=requests[-1][1]
            reader.activate(dict(type='refresh'));current=requests[-1][1]
            self.complete(reader,old,[dict(key='old',title='Stale')])
            self.assertTrue(reader.model['nodes']['root']['busy'])
            self.complete(reader,current,[],error='Connection failed')
            self.assertFalse(reader.model['nodes']['root']['busy'])
            reader.activate(dict(type='load',id='root'))
            self.complete(reader,requests[-1][1],[dict(key='new',title='New')])
        titles=[item.get('title') for item in reader.model['nodes'].values()]
        self.assertIn('New',titles);self.assertNotIn('Stale',titles)

    def test_native_error_keeps_retry_state_and_complete_debug_details(self):
        from thlib.environment import env_inst
        app,_,reader,_=self.tree_owner()
        app.debug_log=Mock()
        worker=Mock();pool=SimpleNamespace(is_stopped=False,add_task=lambda read:worker)
        with patch('thlib.tactic_classes.server_start',return_value=Mock()),patch.object(env_inst,'server_pool',pool):
            reader.activate(dict(type='refresh'))
        failed=worker.error.connect.call_args.args[0]
        failed([dict(exception='Read failed',stacktrace='Complete native traceback')])
        self.assertFalse(reader.model['nodes']['root']['busy'])
        self.assertEqual(reader.model['nodes']['root']['error'],'Read failed')
        app.debug_log.raise_error.assert_called_once_with('Read failed',stacktrace='Complete native traceback',group='dashboard/tree')
        reader.shutdown()
        failed([dict(exception='Stale failure',stacktrace='Stale traceback')])
        self.assertEqual(app.debug_log.raise_error.call_count,1)
